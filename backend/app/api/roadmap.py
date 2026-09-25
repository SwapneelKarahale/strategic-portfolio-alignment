from flask import Blueprint, request

from app.api.response import api_response
from app.auth.decorators import get_current_user, require_role
from app.extensions import db
from app.models.demand import Demand
from app.models.enums import ProjectStatus, Role
from app.models.project import Project, RoadmapItem
from app.schemas.roadmap import RoadmapScheduleSchema
from app.services.audit import log_action
from app.services.errors import NotFoundError
from app.services.workflow import assert_project_can_be_scheduled, assert_project_transition

roadmap_bp = Blueprint("roadmap", __name__)

schedule_schema = RoadmapScheduleSchema()


@roadmap_bp.get("")
@require_role()
def get_roadmap():
    query = RoadmapItem.query.join(Project, RoadmapItem.project_id == Project.id)

    quarter = request.args.get("quarter")
    if quarter:
        query = query.filter(RoadmapItem.quarter == quarter)
    project_manager_id = request.args.get("project_manager_id", type=int)
    if project_manager_id:
        query = query.filter(Project.project_manager_id == project_manager_id)
    business_function_id = request.args.get("business_function_id", type=int)
    if business_function_id:
        query = query.join(Demand, Project.demand_id == Demand.id).filter(
            Demand.business_function_id == business_function_id
        )
    status = request.args.get("status")
    if status:
        query = query.filter(Project.status == status)

    items = query.order_by(RoadmapItem.quarter.asc(), RoadmapItem.sequence.asc()).all()
    return api_response(data=[item.to_dict() for item in items])


@roadmap_bp.post("")
@require_role(Role.PROJECT_MANAGER, Role.ADMIN)
def schedule_project():
    user = get_current_user()
    payload = schedule_schema.load(request.get_json(force=True) or {})

    project = db.session.get(Project, payload["project_id"])
    if project is None:
        raise NotFoundError("Project not found.")

    assert_project_can_be_scheduled(project)
    assert_project_transition(project.status, ProjectStatus.PLANNED)

    roadmap_item = RoadmapItem(
        project_id=project.id,
        quarter=payload["quarter"],
        sequence=payload["sequence"],
        planned_start=payload["planned_start"],
        planned_end=payload["planned_end"],
    )
    db.session.add(roadmap_item)

    old_value = project.status.value
    project.status = ProjectStatus.PLANNED

    db.session.flush()
    log_action(user, "scheduled project on roadmap", "project", project.id, old_value=old_value, new_value=ProjectStatus.PLANNED.value)
    db.session.commit()
    return api_response(data=roadmap_item.to_dict(), status=201)
