"""In-memory assessment state representation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FINAL_STATUSES = frozenset({"COMPLETED", "STOPPED", "TIMEOUT", "FAILED"})
RUNNING_STATUSES = frozenset({
    "STARTING",
    "VERIFYING_TARGET",
    "DISCOVERING",
    "PASSIVE_SCANNING",
    "AWAITING_DURATION",
    "ACTIVE_SCANNING",
    "ANALYZING_FINDINGS",
})

STAGE_LABELS = {
    "IDLE": "Idle",
    "STARTING": "Target Verification",
    "VERIFYING_TARGET": "Target Verification",
    "DISCOVERING": "Website Discovery",
    "PASSIVE_SCANNING": "Passive Analysis",
    "AWAITING_DURATION": "Active Security Testing",
    "ACTIVE_SCANNING": "Active Security Testing",
    "ANALYZING_FINDINGS": "Findings Analysis",
    "COMPLETED": "Report",
    "STOPPED": "Report",
    "TIMEOUT": "Report",
    "FAILED": "Target Verification",
}

STATUS_MESSAGES = {
    "STARTING": "Starting assessment...",
    "VERIFYING_TARGET": "Checking whether the target is reachable...",
    "DISCOVERING": "Discovering application pages...",
    "PASSIVE_SCANNING": "Analyzing discovered traffic...",
    "AWAITING_DURATION": "Passive security analysis completed. Select active scan duration.",
    "ACTIVE_SCANNING": "Testing application for vulnerabilities...",
    "ANALYZING_FINDINGS": "Analyzing security findings...",
    "COMPLETED": "Security assessment completed.",
    "STOPPED": "Active scan stopped. Available findings will now be analyzed.",
    "TIMEOUT": "Active scan reached the configured time limit. Available findings will now be analyzed.",
    "FAILED": "Assessment failed.",
}


@dataclass
class AssessmentState:
    """Application-level assessment state (separate from ZAP scan IDs)."""

    application_scan_id: str
    target_url: str
    status: str = "IDLE"
    current_stage: str = "IDLE"
    scan_completion: str | None = None

    spider_scan_id: str | None = None
    spider_progress: int = 0
    discovered_url_count: int = 0
    discovered_urls: list[str] = field(default_factory=list)

    passive_records_to_scan: int | None = None

    active_scan_id: str | None = None
    active_scan_progress: int = 0
    active_scan_duration: int | None = None

    alert_summary: dict[str, int] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    top_findings: list[dict[str, Any]] = field(default_factory=list)

    html_report_path: str | None = None
    json_report_path: str | None = None

    error_message: str | None = None

    def is_running(self) -> bool:
        return self.status in RUNNING_STATUSES

    def is_final(self) -> bool:
        return self.status in FINAL_STATUSES

    def get_progress(self) -> int:
        if self.status == "DISCOVERING":
            return self.spider_progress
        if self.status == "ACTIVE_SCANNING":
            return self.active_scan_progress
        if self.status in {"COMPLETED", "STOPPED", "TIMEOUT"}:
            return 100
        return 0

    def get_stage_label(self) -> str:
        return STAGE_LABELS.get(self.status, self.current_stage)

    def get_status_message(self) -> str:
        if self.error_message and self.status == "FAILED":
            return self.error_message
        return STATUS_MESSAGES.get(self.status, "")

    def to_public_dict(self) -> dict[str, Any]:
        """Return state safe for frontend display (no ZAP scan IDs)."""
        return {
            "application_scan_id": self.application_scan_id,
            "target_url": self.target_url,
            "status": self.status,
            "stage": self.get_stage_label(),
            "current_stage": self.current_stage,
            "scan_completion": self.scan_completion,
            "progress": self.get_progress(),
            "spider_progress": self.spider_progress,
            "discovered_url_count": self.discovered_url_count,
            "active_scan_progress": self.active_scan_progress,
            "active_scan_duration": self.active_scan_duration,
            "alert_summary": self.alert_summary,
            "top_findings": self.top_findings,
            "findings_count": len(self.findings),
            "status_message": self.get_status_message(),
            "error_message": self.error_message,
            "awaiting_duration": self.status == "AWAITING_DURATION",
            "can_stop": self.status == "ACTIVE_SCANNING",
            "has_results": self.status in {"COMPLETED", "STOPPED", "TIMEOUT"},
            "is_final": self.is_final(),
        }
