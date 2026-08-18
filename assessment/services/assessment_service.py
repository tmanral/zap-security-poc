"""Application-level assessment state management and workflow orchestration."""

from __future__ import annotations

import logging
import re
import threading
import time
from urllib.parse import urlparse

from assessment.findings import normalize_finding, prioritize_findings
from assessment.services.zap_client import ZapClient, ZapClientError
from assessment.state import AssessmentState, FINAL_STATUSES

logger = logging.getLogger(__name__)

POLL_INTERVAL = 3
VALID_DURATIONS = {5, 10, 15, 30}

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class AssessmentValidationError(Exception):
    """Raised when user input fails validation."""

    def __init__(self, message: str):
        super().__init__(message)
        self.user_message = message


class AssessmentInProgressError(Exception):
    """Raised when a second assessment is attempted while one is running."""

    def __init__(self):
        super().__init__("Assessment already in progress")
        self.user_message = (
            "An assessment is already in progress. "
            "Please wait for it to complete or stop the current assessment."
        )


class AssessmentService:
    """Manages a single in-memory assessment and orchestrates the ZAP workflow."""

    _id_counter: int = 1000
    _current: AssessmentState | None = None
    _lock = threading.Lock()
    _duration_event = threading.Event()
    _duration_minutes: int | None = None
    _stop_active_requested = False
    _workflow_thread: threading.Thread | None = None

    @classmethod
    def get_current(cls) -> AssessmentState | None:
        with cls._lock:
            return cls._current

    @classmethod
    def is_running(cls) -> bool:
        state = cls.get_current()
        return state is not None and state.is_running()

    @classmethod
    def validate_target_url(cls, target_url: str) -> str:
        target_url = (target_url or "").strip()
        if not target_url:
            raise AssessmentValidationError("Please enter a target URL.")
        if not _URL_PATTERN.match(target_url):
            raise AssessmentValidationError(
                "Please enter a valid HTTP or HTTPS URL."
            )
        parsed = urlparse(target_url)
        if not parsed.netloc:
            raise AssessmentValidationError(
                "Please enter a valid HTTP or HTTPS URL."
            )
        return target_url

    @classmethod
    def _next_scan_id(cls) -> str:
        cls._id_counter += 1
        return f"APP-{cls._id_counter}"

    @classmethod
    def _set_state(cls, state: AssessmentState) -> None:
        with cls._lock:
            cls._current = state

    @classmethod
    def _update_state(cls, **kwargs) -> None:
        with cls._lock:
            if cls._current is None:
                return
            for key, value in kwargs.items():
                setattr(cls._current, key, value)

    @classmethod
    def start_assessment(cls, target_url: str) -> AssessmentState:
        if cls.get_current() and not cls.get_current().is_final():
            raise AssessmentInProgressError()

        validated_url = cls.validate_target_url(target_url)
        cls._duration_event.clear()
        cls._duration_minutes = None
        cls._stop_active_requested = False

        state = AssessmentState(
            application_scan_id=cls._next_scan_id(),
            target_url=validated_url,
            status="STARTING",
            current_stage="VERIFYING_TARGET",
        )
        cls._set_state(state)

        thread = threading.Thread(target=cls._run_workflow, daemon=True)
        cls._workflow_thread = thread
        thread.start()
        return state

    @classmethod
    def set_active_scan_duration(cls, minutes: int) -> None:
        if minutes not in VALID_DURATIONS:
            raise AssessmentValidationError(
                "Please select a valid scan duration (5, 10, 15, or 30 minutes)."
            )
        state = cls.get_current()
        if not state or state.status != "AWAITING_DURATION":
            raise AssessmentValidationError(
                "Active scan duration can only be set when prompted."
            )
        cls._duration_minutes = minutes
        cls._update_state(active_scan_duration=minutes)
        cls._duration_event.set()

    @classmethod
    def stop_active_scan(cls) -> None:
        state = cls.get_current()
        if not state or state.status != "ACTIVE_SCANNING":
            return
        cls._stop_active_requested = True
        if state.active_scan_id:
            try:
                ZapClient().stop_active_scan(state.active_scan_id)
            except ZapClientError as exc:
                logger.warning("Stop active scan failed: %s", exc)

    @classmethod
    def get_public_status(cls) -> dict:
        state = cls.get_current()
        if not state:
            return {"status": "IDLE", "stage": "Idle", "progress": 0}
        return state.to_public_dict()

    @classmethod
    def get_results(cls) -> dict:
        state = cls.get_current()
        if not state:
            return {}
        return {
            "target_url": state.target_url,
            "status": state.status,
            "scan_completion": state.scan_completion,
            "alert_summary": state.alert_summary,
            "top_findings": state.top_findings,
            "findings_count": len(state.findings),
            "status_message": state.get_status_message(),
        }

    @classmethod
    def get_all_findings(cls) -> list[dict]:
        state = cls.get_current()
        if not state:
            return []
        return state.findings

    @classmethod
    def generate_report(cls, report_format: str) -> str:
        state = cls.get_current()
        if not state or state.status not in {"COMPLETED", "STOPPED", "TIMEOUT"}:
            raise AssessmentValidationError(
                "Reports are available after an assessment completes."
            )
        if report_format == "html":
            template = "traditional-html"
            filename = f"{state.application_scan_id}.html"
        elif report_format == "json":
            template = "traditional-json"
            filename = f"{state.application_scan_id}.json"
        else:
            raise AssessmentValidationError("Invalid report format.")

        title = f"Security Assessment — {state.application_scan_id}"
        zap = ZapClient()
        path = zap.generate_report(
            template=template,
            title=title,
            sites=state.target_url,
            report_filename=filename,
        )
        if report_format == "html":
            cls._update_state(html_report_path=path)
        else:
            cls._update_state(json_report_path=path)
        return path

    @classmethod
    def _fail_assessment(cls, message: str) -> None:
        cls._update_state(status="FAILED", error_message=message)

    @classmethod
    def _run_workflow(cls) -> None:
        zap = ZapClient()
        state = cls.get_current()
        if not state:
            return

        try:
            cls._stage_verify_target(zap, state)
            state = cls.get_current()
            if not state or state.status == "FAILED":
                return

            cls._stage_spider(zap, state)
            state = cls.get_current()
            if not state or state.status == "FAILED":
                return

            cls._stage_passive_scan(zap, state)
            state = cls.get_current()
            if not state or state.status == "FAILED":
                return

            cls._stage_await_duration()
            state = cls.get_current()
            if not state or state.status == "FAILED":
                return

            cls._stage_active_scan(zap, state)
            state = cls.get_current()
            if not state or state.status == "FAILED":
                return

            cls._stage_retrieve_findings(zap, state)
        except ZapClientError as exc:
            logger.exception("Workflow ZAP error")
            cls._fail_assessment(exc.user_message)
        except Exception as exc:
            logger.exception("Workflow unexpected error")
            cls._fail_assessment(
                "The security assessment could not be completed. Please try again."
            )

    @classmethod
    def _stage_verify_target(cls, zap: ZapClient, state: AssessmentState) -> None:
        cls._update_state(
            status="VERIFYING_TARGET",
            current_stage="VERIFYING_TARGET",
        )
        try:
            zap.verify_target(state.target_url)
        except ZapClientError as exc:
            cls._fail_assessment(exc.user_message)
            return
        cls._update_state(status="DISCOVERING", current_stage="DISCOVERING")

    @classmethod
    def _stage_spider(cls, zap: ZapClient, state: AssessmentState) -> None:
        try:
            spider_id = zap.start_spider(state.target_url)
        except ZapClientError as exc:
            cls._fail_assessment(exc.user_message)
            return

        cls._update_state(spider_scan_id=spider_id, spider_progress=0)

        while True:
            try:
                progress = zap.get_spider_status(spider_id)
            except ZapClientError as exc:
                cls._fail_assessment(exc.user_message)
                return
            cls._update_state(spider_progress=progress)
            if progress >= 100:
                break
            time.sleep(POLL_INTERVAL)

        try:
            results = zap.get_spider_results(spider_id)
        except ZapClientError as exc:
            cls._fail_assessment(exc.user_message)
            return

        cls._update_state(
            discovered_urls=results,
            discovered_url_count=len(results),
            status="PASSIVE_SCANNING",
            current_stage="PASSIVE_SCANNING",
        )

    @classmethod
    def _stage_passive_scan(cls, zap: ZapClient, state: AssessmentState) -> None:
        while True:
            try:
                records = zap.get_passive_scan_status()
            except ZapClientError as exc:
                cls._fail_assessment(exc.user_message)
                return
            cls._update_state(passive_records_to_scan=records)
            if records == 0:
                break
            time.sleep(POLL_INTERVAL)

        cls._update_state(
            status="AWAITING_DURATION",
            current_stage="AWAITING_DURATION",
        )

    @classmethod
    def _stage_await_duration(cls) -> None:
        cls._duration_event.clear()
        cls._duration_minutes = None
        cls._duration_event.wait()
        if cls._duration_minutes is None:
            cls._fail_assessment("Active scan duration was not set.")
            return

    @classmethod
    def _stage_active_scan(cls, zap: ZapClient, state: AssessmentState) -> None:
        minutes = cls._duration_minutes or state.active_scan_duration
        if not minutes:
            cls._fail_assessment("Active scan duration was not set.")
            return

        cls._stop_active_requested = False
        try:
            zap.set_active_scan_duration(minutes)
            active_id = zap.start_active_scan(state.target_url)
        except ZapClientError as exc:
            cls._fail_assessment(exc.user_message)
            return

        cls._update_state(
            active_scan_id=active_id,
            active_scan_progress=0,
            status="ACTIVE_SCANNING",
            current_stage="ACTIVE_SCANNING",
            active_scan_duration=minutes,
        )

        start_time = time.time()
        final_status = "COMPLETED"
        completion = "FULL"

        while True:
            if cls._stop_active_requested:
                final_status = "STOPPED"
                completion = "PARTIAL"
                break

            try:
                progress = zap.get_active_scan_status(active_id)
            except ZapClientError as exc:
                cls._fail_assessment(exc.user_message)
                return

            cls._update_state(active_scan_progress=progress)

            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes >= minutes and progress < 100:
                try:
                    zap.stop_active_scan(active_id)
                except ZapClientError:
                    pass
                final_status = "TIMEOUT"
                completion = "PARTIAL"
                break

            if progress >= 100:
                final_status = "COMPLETED"
                completion = "FULL"
                break

            time.sleep(POLL_INTERVAL)

        cls._update_state(
            status=final_status,
            scan_completion=completion,
            current_stage="ANALYZING_FINDINGS",
        )

    @classmethod
    def _stage_retrieve_findings(cls, zap: ZapClient, state: AssessmentState) -> None:
        prev_status = state.status
        cls._update_state(status="ANALYZING_FINDINGS", current_stage="ANALYZING_FINDINGS")
        try:
            raw_alerts = zap.get_alerts(state.target_url)
            summary = zap.get_alert_summary(state.target_url)
        except ZapClientError as exc:
            cls._fail_assessment(exc.user_message)
            return

        findings = [normalize_finding(a) for a in raw_alerts]
        top = prioritize_findings(findings)

        cls._update_state(
            findings=findings,
            top_findings=top,
            alert_summary=summary,
            status=prev_status,
            current_stage=prev_status,
        )
