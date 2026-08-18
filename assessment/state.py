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
    "ACTIVE_SCANNING",
})


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

    passive_records_to_scan: int | None = None

    active_scan_id: str | None = None
    active_scan_progress: int = 0
    active_scan_duration: int | None = None

    alert_summary: dict[str, int] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)

    html_report_path: str | None = None
    json_report_path: str | None = None

    error_message: str | None = None

    def is_running(self) -> bool:
        return self.status in RUNNING_STATUSES

    def to_public_dict(self) -> dict[str, Any]:
        """Return state safe for frontend display (no ZAP scan IDs)."""
        return {
            "application_scan_id": self.application_scan_id,
            "target_url": self.target_url,
            "status": self.status,
            "current_stage": self.current_stage,
            "scan_completion": self.scan_completion,
            "spider_progress": self.spider_progress,
            "discovered_url_count": self.discovered_url_count,
            "active_scan_progress": self.active_scan_progress,
            "active_scan_duration": self.active_scan_duration,
            "alert_summary": self.alert_summary,
            "findings_count": len(self.findings),
            "error_message": self.error_message,
        }
