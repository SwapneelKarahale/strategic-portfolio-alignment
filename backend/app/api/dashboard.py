from flask import Blueprint, request

from app.api.response import api_response
from app.auth.decorators import require_role
from app.services.analytics import get_analytics_provider

dashboard_bp = Blueprint("dashboard", __name__)


def _filters_from_request() -> dict:
    filters = {}
    for key in ("business_function_id", "project_manager_id", "capability_id"):
        value = request.args.get(key, type=int)
        if value:
            filters[key] = value
    for key in ("priority", "quarter"):
        value = request.args.get(key)
        if value:
            filters[key] = value
    return filters


@dashboard_bp.get("/summary")
@require_role()
def summary():
    provider = get_analytics_provider()
    filters = _filters_from_request()
    return api_response(data=provider.get_kpis(filters))


@dashboard_bp.get("/analytics")
@require_role()
def analytics():
    provider = get_analytics_provider()
    filters = _filters_from_request()
    data = {
        "funnel": provider.get_funnel_counts(filters),
        "by_business_function": provider.get_distribution_by("business_function", filters),
        "by_project_manager": provider.get_distribution_by("project_manager", filters),
        "by_priority": provider.get_distribution_by("priority", filters),
        "roadmap": provider.get_roadmap_view(filters),
        "upcoming_milestones": provider.get_upcoming_milestones(),
    }
    return api_response(data=data)
