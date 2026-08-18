import logging

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
    """Check ZAP connectivity; return status safe for templates."""
    try:
        client = ZapClient()
        version = client.check_connectivity()
        return {"available": True, "version": version, "error": None}
    except ZapClientError as exc:
        logger.warning("ZAP connectivity check failed: %s", exc)
        return {"available": False, "version": None, "error": exc.user_message}


@require_http_methods(["GET"])
def landing(request):
    return render(request, "landing.html")


@require_http_methods(["GET", "POST"])
def assessment_dashboard(request):
    zap_status = _get_zap_status()
    validation_error = None
    assessment = AssessmentService.get_current()

    if request.method == "POST":
        target_url = request.POST.get("target_url", "")
        try:
            assessment = AssessmentService.start_assessment(target_url)
        except AssessmentValidationError as exc:
            validation_error = exc.user_message
        except AssessmentInProgressError as exc:
            validation_error = exc.user_message

    context = {
        "zap_status": zap_status,
        "assessment": assessment,
        "validation_error": validation_error,
        "assessment_running": AssessmentService.is_running(),
    }
    return render(request, "assessment.html", context)
