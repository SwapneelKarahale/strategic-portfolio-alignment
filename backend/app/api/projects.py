from flask import Blueprint, request

from app.api.response import api_response, paginated_response
from app.auth.decorators import get_current_user, require_role
from app.extensions import db
from app.models.enums import ProjectHealth, ProjectStatus, Role
from app.models.project import Capability, Milestone, Project, ProjectCapability, Requirement
from app.schemas.project import (
    CapabilityAssignSchema,
    MilestoneCreateSchema,
    MilestoneUpdateSchema,
    ProjectStatusUpdateSchema,
    ProjectUpdateSchema,
    RequirementCreateSchema,
)
from app.services.audit import log_action
from app.services.errors import ForbiddenError, NotFoundError, WorkflowError
from app.services.notifications import notify
from app.services.workflow import assert_project_can_start, assert_project_transition

projects_bp = Blueprint("projects", __name__)

update_schema = ProjectUpdateSchema()
status_schema = ProjectStatusUpdateSchema()
requirement_schema = RequirementCreateSchema()
capability_schema = CapabilityAssignSchema()
milestone_schema = MilestoneCreateSchema()
milestone_update_schema = MilestoneUpdateSchema()

MANAGER_ROLES = (Role.PROJECT_MANAGER, Role.ADMIN)


def _get_project_or_404(project_id: int) -> Project:
    project = db.session.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found.")
    return project


def _ensure_manages(project: Project, user) -> None:
    if user.role == Role.ADMIN:
        return
    if user.role != Role.PROJECT_MANAGER or project.project_manager_id != user.id:
        raise ForbiddenError("Only the assigned project manager (or an admin) can manage this project.")


@projects_bp.get("")
@require_role()
def list_projects():
    user = get_current_user()
    query = Project.query

    if user.role == Role.PROJECT_MANAGER:
        pm_only = request.args.get("mine")
        if pm_only:
            query = query.filter(Project.project_manager_id == user.id)

    status = request.args.get("status")
    if status:
        query = query.filter(Project.status == status)
    priority = request.args.get("priority")
    if priority:
        query = query.filter(Project.priority == priority)
    project_manager_id = request.args.get("project_manager_id", type=int)
    if project_manager_id:
        query = query.filter(Project.project_manager_id == project_manager_id)
    search = request.args.get("search")
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))

    query = query.order_by(Project.created_at.desc())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    return paginated_response(query, lambda p: p.to_dict(), page, per_page)


@projects_bp.get("/<int:project_id>")
@require_role()
def get_project(project_id: int):
    project = _get_project_or_404(project_id)
    return api_response(data=project.to_dict(include_details=True))


@projects_bp.patch("/<int:project_id>")
@require_role(*MANAGER_ROLES)
def update_project(project_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    if user.role == Role.PROJECT_MANAGER and project.project_manager_id not in (None, user.id):
        raise ForbiddenError("Only the assigned project manager (or an admin) can manage this project.")

    payload = update_schema.load(request.get_json(force=True) or {})
    for field, value in payload.items():
        setattr(project, field, value)

    db.session.flush()
    log_action(user, "updated project", "project", project.id)
    db.session.commit()
    return api_response(data=project.to_dict(include_details=True))


@projects_bp.post("/<int:project_id>/requirements")
@require_role(*MANAGER_ROLES)
def add_requirement(project_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    _ensure_manages(project, user)

    payload = requirement_schema.load(request.get_json(force=True) or {})
    requirement = Requirement(project_id=project.id, requirement_text=payload["requirement_text"], category=payload.get("category"))
    db.session.add(requirement)
    db.session.flush()

    log_action(user, "added requirement", "project", project.id, new_value=requirement.requirement_text)
    db.session.commit()
    return api_response(data=requirement.to_dict(), status=201)


@projects_bp.post("/<int:project_id>/capabilities")
@require_role(*MANAGER_ROLES)
def add_capability(project_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    _ensure_manages(project, user)

    payload = capability_schema.load(request.get_json(force=True) or {})
    capability = db.session.get(Capability, payload["capability_id"])
    if capability is None:
        raise NotFoundError("Capability not found.")

    link = db.session.get(ProjectCapability, (project.id, capability.id))
    if link is None:
        link = ProjectCapability(project_id=project.id, capability_id=capability.id)
        db.session.add(link)
    link.effort_estimate = payload.get("effort_estimate")

    db.session.flush()
    log_action(user, "assigned capability", "project", project.id, new_value=capability.name)
    db.session.commit()
    return api_response(data=link.to_dict(), status=201)


@projects_bp.post("/<int:project_id>/milestones")
@require_role(*MANAGER_ROLES)
def add_milestone(project_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    _ensure_manages(project, user)

    payload = milestone_schema.load(request.get_json(force=True) or {})
    milestone = Milestone(
        project_id=project.id, name=payload["name"], due_date=payload["due_date"], owner_id=payload.get("owner_id")
    )
    db.session.add(milestone)
    db.session.flush()

    log_action(user, "added milestone", "project", project.id, new_value=milestone.name)
    db.session.commit()
    return api_response(data=milestone.to_dict(), status=201)


@projects_bp.patch("/<int:project_id>/milestones/<int:milestone_id>")
@require_role(*MANAGER_ROLES)
def update_milestone(project_id: int, milestone_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    _ensure_manages(project, user)

    milestone = Milestone.query.filter_by(id=milestone_id, project_id=project.id).first()
    if milestone is None:
        raise NotFoundError("Milestone not found.")

    payload = milestone_update_schema.load(request.get_json(force=True) or {})
    old_value = milestone.status
    for field, value in payload.items():
        setattr(milestone, field, value)

    db.session.flush()
    log_action(user, "updated milestone", "project", project.id, old_value=old_value, new_value=milestone.status)
    db.session.commit()
    return api_response(data=milestone.to_dict())


@projects_bp.patch("/<int:project_id>/status")
@require_role(*MANAGER_ROLES)
def update_status(project_id: int):
    user = get_current_user()
    project = _get_project_or_404(project_id)
    _ensure_manages(project, user)

    payload = status_schema.load(request.get_json(force=True) or {})
    target = ProjectStatus(payload["status"])

    if target == ProjectStatus.PLANNED:
        raise WorkflowError(
            "A project moves to Planned automatically when it is scheduled on the roadmap — use POST /api/roadmap."
        )
    if target == ProjectStatus.IN_PROGRESS and project.status == ProjectStatus.PLANNED:
        assert_project_can_start(project)

    old_value = project.status.value
    assert_project_transition(project.status, target)
    project.status = target
    if payload.get("health"):
        project.health = ProjectHealth(payload["health"])
    elif target == ProjectStatus.AT_RISK:
        project.health = ProjectHealth.AT_RISK
    elif target == ProjectStatus.BLOCKED:
        project.health = ProjectHealth.BLOCKED
    elif target == ProjectStatus.IN_PROGRESS:
        project.health = ProjectHealth.ON_TRACK

    db.session.flush()
    log_action(
        user, "changed project status", "project", project.id, old_value=old_value, new_value=target.value, comments=payload.get("comments")
    )
    if project.project_manager and target in (ProjectStatus.AT_RISK, ProjectStatus.BLOCKED):
        notify(project.project_manager, "project_at_risk", f"Project '{project.name}' was marked {target.value}.")
    db.session.commit()
    return api_response(data=project.to_dict(include_details=True))
