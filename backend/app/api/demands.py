from flask import Blueprint, request

from app.api.response import api_response, paginated_response
from app.auth.decorators import get_current_user, require_role
from app.extensions import db
from app.models.demand import Demand, DemandReview
from app.models.enums import DemandStatus, Role
from app.models.project import Project
from app.schemas.demand import DemandCreateSchema, DemandReviewSchema, DemandUpdateSchema
from app.services.audit import log_action
from app.services.errors import ForbiddenError, NotFoundError, WorkflowError
from app.services.notifications import notify, notify_many
from app.services.workflow import assert_demand_can_convert, assert_demand_transition

demands_bp = Blueprint("demands", __name__)

create_schema = DemandCreateSchema()
update_schema = DemandUpdateSchema()
review_schema = DemandReviewSchema()

# Transitions a requestor may trigger themselves via PATCH (submitting a draft, or responding to
# a clarification request). Everything else goes through the PM/management-only /review endpoint.
OWNER_TRANSITIONS = {
    DemandStatus.DRAFT: DemandStatus.SUBMITTED,
    DemandStatus.CLARIFICATION_REQUIRED: DemandStatus.UNDER_REVIEW,
}

REVIEWER_ROLES = (Role.PROJECT_MANAGER, Role.MANAGEMENT, Role.ADMIN)


def _get_demand_or_404(demand_id: int) -> Demand:
    demand = db.session.get(Demand, demand_id)
    if demand is None:
        raise NotFoundError("Demand not found.")
    return demand


@demands_bp.post("")
@require_role()
def create_demand():
    user = get_current_user()
    payload = create_schema.load(request.get_json(force=True) or {})

    demand = Demand(
        title=payload["title"],
        business_function_id=payload["business_function_id"],
        requestor_id=user.id,
        problem_statement=payload["problem_statement"],
        business_need=payload.get("business_need"),
        support_required=payload.get("support_required"),
        request_type=payload["request_type"],
        priority=payload["priority"],
        expected_timeline=payload.get("expected_timeline"),
        additional_details=payload.get("additional_details"),
        status=DemandStatus.DRAFT,
    )
    db.session.add(demand)
    db.session.flush()

    log_action(user, "created demand", "demand", demand.id, new_value=demand.status.value)
    db.session.commit()
    return api_response(data=demand.to_dict(), status=201)


@demands_bp.get("")
@require_role()
def list_demands():
    user = get_current_user()
    query = Demand.query

    if user.role == Role.REQUESTOR:
        query = query.filter(Demand.requestor_id == user.id)

    status = request.args.get("status")
    if status:
        query = query.filter(Demand.status == status)
    business_function_id = request.args.get("business_function_id", type=int)
    if business_function_id:
        query = query.filter(Demand.business_function_id == business_function_id)
    priority = request.args.get("priority")
    if priority:
        query = query.filter(Demand.priority == priority)
    requestor_id = request.args.get("requestor_id", type=int)
    if requestor_id:
        query = query.filter(Demand.requestor_id == requestor_id)
    search = request.args.get("search")
    if search:
        query = query.filter(Demand.title.ilike(f"%{search}%"))

    query = query.order_by(Demand.created_at.desc())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return paginated_response(query, lambda d: d.to_dict(), page, per_page)


@demands_bp.get("/<int:demand_id>")
@require_role()
def get_demand(demand_id: int):
    user = get_current_user()
    demand = _get_demand_or_404(demand_id)
    if user.role == Role.REQUESTOR and demand.requestor_id != user.id:
        raise ForbiddenError("You can only view your own demands.")
    return api_response(data=demand.to_dict(include_reviews=True))


@demands_bp.patch("/<int:demand_id>")
@require_role()
def update_demand(demand_id: int):
    user = get_current_user()
    demand = _get_demand_or_404(demand_id)
    if demand.requestor_id != user.id and user.role != Role.ADMIN:
        raise ForbiddenError("Only the requestor (or an admin) can edit this demand.")

    payload = update_schema.load(request.get_json(force=True) or {})
    target_status = payload.pop("status", None)

    old_value = demand.status.value
    for field, value in payload.items():
        setattr(demand, field, value)

    if target_status:
        target = DemandStatus(target_status)
        if OWNER_TRANSITIONS.get(demand.status) != target:
            raise WorkflowError(
                f"As the requestor you can only submit a Draft or respond to a Clarification "
                f"Required demand. Use the review endpoint for other transitions."
            )
        assert_demand_transition(demand.status, target)
        demand.status = target

    db.session.flush()
    log_action(user, "updated demand", "demand", demand.id, old_value=old_value, new_value=demand.status.value)
    db.session.commit()
    return api_response(data=demand.to_dict())


@demands_bp.post("/<int:demand_id>/review")
@require_role(*REVIEWER_ROLES)
def review_demand(demand_id: int):
    user = get_current_user()
    demand = _get_demand_or_404(demand_id)
    payload = review_schema.load(request.get_json(force=True) or {})

    target = DemandStatus(payload["action"])
    old_value = demand.status.value
    assert_demand_transition(demand.status, target)
    demand.status = target

    review = DemandReview(demand_id=demand.id, reviewer_id=user.id, action=target.value, comments=payload.get("comments"))
    db.session.add(review)

    log_action(
        user, "reviewed demand", "demand", demand.id, old_value=old_value, new_value=target.value, comments=payload.get("comments")
    )
    notify(demand.requestor, "demand_status_changed", f"Your demand '{demand.title}' is now {target.value}.")
    db.session.commit()
    return api_response(data=demand.to_dict(include_reviews=True))


@demands_bp.post("/<int:demand_id>/convert")
@require_role(Role.PROJECT_MANAGER, Role.ADMIN)
def convert_demand(demand_id: int):
    user = get_current_user()
    demand = _get_demand_or_404(demand_id)
    assert_demand_can_convert(demand)

    project = Project(demand_id=demand.id, name=demand.title, business_objective=demand.business_need)
    db.session.add(project)
    db.session.flush()

    log_action(user, "converted demand to project", "demand", demand.id, new_value=f"project:{project.id}")
    notify_many(
        [demand.requestor],
        "demand_converted",
        f"Your demand '{demand.title}' has been converted to a portfolio project.",
    )
    db.session.commit()
    return api_response(data=project.to_dict(include_details=True), status=201)
