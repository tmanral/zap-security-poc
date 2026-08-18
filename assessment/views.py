import json
import logging
import os

from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from assessment.services import (
    AssessmentInProgressError,
    AssessmentService,
    ZapClient,
    ZapClientError,
)
from assessment.services.assessment_service import AssessmentValidationError

logger = logging.getLogger(__name__)


def _get_zap_status() -> dict:
    try:
        client = ZapClient()
        version = client.check_connectivity()
        return {"available": True, "version": version, "error": None}
    except ZapClientError as exc:
        logger.warning("ZAP connectivity check failed: %s", exc)
        return {"available": False, "version": None, "error": exc.user_message}


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


@require_http_methods(["GET"])
def landing(request):
    return render(request, "landing.html")


@require_http_methods(["GET"])
def assessment_dashboard(request):
    context = {
        "zap_status": _get_zap_status(),
    }
    return render(request, "assessment.html", context)


@require_http_methods(["POST"])
def api_start(request):
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _json_error("Invalid request body.")

    target_url = body.get("target_url", "")
    try:
        state = AssessmentService.start_assessment(target_url)
        return JsonResponse(state.to_public_dict())
    except AssessmentValidationError as exc:
        return _json_error(exc.user_message)
    except AssessmentInProgressError as exc:
        return _json_error(exc.user_message, status=409)


@require_http_methods(["GET"])
def api_status(request):
    return JsonResponse(AssessmentService.get_public_status())


@require_http_methods(["POST"])
def api_stop(request):
    AssessmentService.stop_active_scan()
    return JsonResponse({"ok": True})


@require_http_methods(["POST"])
def api_duration(request):
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _json_error("Invalid request body.")

    try:
        minutes = int(body.get("duration", 0))
    except (TypeError, ValueError):
        return _json_error("Please select a valid scan duration.")

    try:
        AssessmentService.set_active_scan_duration(minutes)
        return JsonResponse(AssessmentService.get_public_status())
    except AssessmentValidationError as exc:
        return _json_error(exc.user_message)


@require_http_methods(["GET"])
def api_results(request):
    results = AssessmentService.get_results()
    if not results:
        return _json_error("No assessment results available.", status=404)
    return JsonResponse(results)


@require_http_methods(["GET"])
def api_findings(request):
    findings = AssessmentService.get_all_findings()
    return JsonResponse({"findings": findings})


@require_http_methods(["GET"])
def api_report(request, report_format: str):
    if report_format not in ("html", "json"):
        return _json_error("Invalid report format.")

    try:
        path = AssessmentService.generate_report(report_format)
    except AssessmentValidationError as exc:
        return _json_error(exc.user_message)
    except ZapClientError as exc:
        return _json_error(exc.user_message, status=500)

    content_type = "text/html" if report_format == "html" else "application/json"
    filename = os.path.basename(path)
    return FileResponse(
        open(path, "rb"),
        content_type=content_type,
        as_attachment=True,
        filename=filename,
    )
