"""Dedicated ZAP API client — all ZAP communication goes through this layer."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class ZapClientError(Exception):
    """Raised when ZAP is unavailable or returns an error."""

    def __init__(self, message: str, user_message: str | None = None):
        super().__init__(message)
        self.user_message = user_message or (
            "OWASP ZAP is unavailable. Please make sure ZAP is running."
        )


class ZapClient:
    """Server-side client for OWASP ZAP JSON API."""

    def __init__(self) -> None:
        self.base_url = settings.ZAP_BASE_URL.rstrip("/")
        self.api_key = settings.ZAP_API_KEY

    def _build_url(self, component: str, view_or_action: str, operation: str) -> str:
        return f"{self.base_url}/JSON/{component}/{view_or_action}/{operation}/"

    def _request(
        self,
        component: str,
        view_or_action: str,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"apikey": self.api_key}
        if params:
            query.update(params)

        url = self._build_url(component, view_or_action, operation)
        try:
            response = requests.get(url, params=query, timeout=120)
            response.raise_for_status()
        except requests.ConnectionError as exc:
            logger.exception("ZAP connection failed")
            raise ZapClientError(str(exc)) from exc
        except requests.Timeout as exc:
            logger.exception("ZAP request timed out")
            raise ZapClientError(str(exc)) from exc
        except requests.HTTPError as exc:
            logger.exception("ZAP HTTP error: %s", exc)
            raise ZapClientError(str(exc)) from exc

        try:
            data = response.json()
        except ValueError as exc:
            logger.exception("Invalid JSON from ZAP")
            raise ZapClientError("Invalid response from ZAP") from exc

        if isinstance(data, dict) and "code" in data and "message" in data:
            logger.error("ZAP API error: %s", data.get("message"))
            raise ZapClientError(str(data.get("message", "ZAP API error")))

        return data

    def check_connectivity(self) -> str:
        """Verify ZAP is reachable via the version endpoint."""
        data = self._request("core", "view", "version")
        version = data.get("version")
        if not version:
            raise ZapClientError("Unexpected ZAP version response")
        return str(version)

    def verify_target(self, url: str) -> dict[str, Any]:
        data = self._request(
            "core",
            "action",
            "accessUrl",
            {"url": url, "followRedirects": "true"},
        )
        access = data.get("accessUrl")
        if not access:
            raise ZapClientError(
                "Target unreachable",
                "The target could not be reached. Please verify the target URL and try again.",
            )
        if isinstance(access, list):
            return access[0]
        return access

    def start_spider(self, url: str) -> str:
        data = self._request(
            "spider",
            "action",
            "scan",
            {"url": url, "recurse": "true"},
        )
        scan_id = data.get("scan")
        if scan_id is None:
            raise ZapClientError(
                "Spider start failed",
                "Website discovery could not be completed.",
            )
        return str(scan_id)

    def get_spider_status(self, scan_id: str) -> int:
        data = self._request("spider", "view", "status", {"scanId": scan_id})
        return int(data.get("status", 0))

    def get_spider_results(self, scan_id: str) -> list[str]:
        data = self._request("spider", "view", "results", {"scanId": scan_id})
        return list(data.get("results", []))

    def get_passive_scan_status(self) -> int:
        data = self._request("pscan", "view", "recordsToScan")
        return int(data.get("recordsToScan", 0))

    def set_active_scan_duration(self, minutes: int) -> None:
        self._request(
            "ascan",
            "action",
            "setOptionMaxScanDurationInMins",
            {"Integer": str(minutes)},
        )

    def start_active_scan(self, url: str) -> str:
        data = self._request(
            "ascan",
            "action",
            "scan",
            {"url": url, "recurse": "true"},
        )
        scan_id = data.get("scan")
        if scan_id is None:
            raise ZapClientError(
                "Active scan start failed",
                "Active security testing could not be completed.",
            )
        return str(scan_id)

    def get_active_scan_status(self, scan_id: str) -> int:
        data = self._request("ascan", "view", "status", {"scanId": scan_id})
        return int(data.get("status", 0))

    def stop_active_scan(self, scan_id: str) -> None:
        self._request("ascan", "action", "stop", {"scanId": scan_id})

    def get_alerts(
        self, baseurl: str, start: int = 0, count: int = 999
    ) -> list[dict[str, Any]]:
        data = self._request(
            "core",
            "view",
            "alerts",
            {"baseurl": baseurl, "start": str(start), "count": str(count)},
        )
        alerts = data.get("alerts", [])
        return alerts if isinstance(alerts, list) else []

    def get_alert_summary(self, baseurl: str) -> dict[str, int]:
        data = self._request(
            "core",
            "view",
            "alertsSummary",
            {"baseurl": baseurl},
        )
        raw = data.get("alertsSummary", data)
        if not isinstance(raw, dict):
            return {"high": 0, "medium": 0, "low": 0, "informational": 0}
        return {
            "high": int(raw.get("High", 0)),
            "medium": int(raw.get("Medium", 0)),
            "low": int(raw.get("Low", 0)),
            "informational": int(
                raw.get("Informational", raw.get("Info", 0))
            ),
        }

    def get_report_templates(self) -> list[str]:
        data = self._request("reports", "view", "templates")
        templates = data.get("templates", [])
        return list(templates) if isinstance(templates, list) else []

    def generate_report(
        self,
        template: str,
        title: str,
        sites: str,
        report_filename: str,
    ) -> str:
        self._request(
            "reports",
            "action",
            "generate",
            {
                "title": title,
                "template": template,
                "sites": sites,
                "reportDir": settings.ZAP_REPORT_DIR,
                "reportFileName": report_filename,
                "display": "false",
            },
        )
        report_path = os.path.join(settings.ZAP_REPORT_DIR, report_filename)
        if not os.path.isfile(report_path):
            raise ZapClientError(
                "Report not created",
                "The report could not be generated. Please try again.",
            )
        return report_path
