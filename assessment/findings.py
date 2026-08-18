"""Finding normalization and prioritization."""

from __future__ import annotations

from typing import Any

RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3, "Info": 3}
CONFIDENCE_ORDER = {"High": 0, "Medium": 1, "Low": 2, "False Positive": 3}


def normalize_finding(alert: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": alert.get("alert") or alert.get("name") or "Unknown",
        "risk": alert.get("risk") or "Informational",
        "confidence": alert.get("confidence") or "Low",
        "url": alert.get("url") or "",
        "param": alert.get("param") or "",
        "description": alert.get("description") or "",
        "solution": alert.get("solution") or "",
        "reference": alert.get("reference") or "",
    }


def prioritize_findings(findings: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    def sort_key(finding: dict[str, Any]) -> tuple[int, int]:
        risk = RISK_ORDER.get(finding.get("risk", ""), 99)
        confidence = CONFIDENCE_ORDER.get(finding.get("confidence", ""), 99)
        return (risk, confidence)

    return sorted(findings, key=sort_key)[:limit]
