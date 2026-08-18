"""Dedicated ZAP API client — all ZAP communication goes through this layer."""

from __future__ import annotations

import logging
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
            response = requests.get(url, params=query, timeout=30)
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

    # --- Workflow methods (stubs for Phase 2) ---

    def verify_target(self, url: str) -> dict[str, Any]:
        raise NotImplementedError("Implemented in Phase 2")

    def start_spider(self, url: str) -> str:
        raise NotImplementedError("Implemented in Phase 2")

    def get_spider_status(self, scan_id: str) -> int:
        raise NotImplementedError("Implemented in Phase 2")

    def get_spider_results(self, scan_id: str) -> list[str]:
        raise NotImplementedError("Implemented in Phase 2")

    def get_passive_scan_status(self) -> int:
        raise NotImplementedError("Implemented in Phase 2")

    def set_active_scan_duration(self, minutes: int) -> None:
        raise NotImplementedError("Implemented in Phase 2")

    def start_active_scan(self, url: str) -> str:
        raise NotImplementedError("Implemented in Phase 2")

    def get_active_scan_status(self, scan_id: str) -> int:
        raise NotImplementedError("Implemented in Phase 2")

    def stop_active_scan(self, scan_id: str) -> None:
        raise NotImplementedError("Implemented in Phase 2")

    def get_alerts(self, baseurl: str, start: int = 0, count: int = 999) -> list[dict]:
        raise NotImplementedError("Implemented in Phase 2")

    def get_alert_summary(self, baseurl: str) -> dict[str, int]:
        raise NotImplementedError("Implemented in Phase 2")

    def get_report_templates(self) -> list[str]:
        raise NotImplementedError("Implemented in Phase 2")

    def generate_report(
        self,
        template: str,
        title: str,
        sites: str,
        report_filename: str,
    ) -> str:
        raise NotImplementedError("Implemented in Phase 2")
