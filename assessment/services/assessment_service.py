"""Application-level assessment state management."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from assessment.state import AssessmentState, FINAL_STATUSES

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
    """Manages a single in-memory assessment (no persistence)."""

    _id_counter: int = 1000
    _current: AssessmentState | None = None

    @classmethod
    def get_current(cls) -> AssessmentState | None:
        return cls._current

    @classmethod
    def is_running(cls) -> bool:
        return cls._current is not None and cls._current.is_running()

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
    def start_assessment(cls, target_url: str) -> AssessmentState:
        """Initialize assessment state. Full workflow is implemented in Phase 2."""
        if cls.is_running():
            raise AssessmentInProgressError()

        validated_url = cls.validate_target_url(target_url)

        cls._current = AssessmentState(
            application_scan_id=cls._next_scan_id(),
            target_url=validated_url,
            status="STARTING",
            current_stage="VERIFYING_TARGET",
        )
        return cls._current

    @classmethod
    def reset(cls) -> None:
        """Clear assessment state after a final status (Phase 2 helper)."""
        if cls._current and cls._current.status in FINAL_STATUSES:
            cls._current = None
