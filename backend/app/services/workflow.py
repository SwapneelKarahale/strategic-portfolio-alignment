from app.models.enums import DEMAND_TRANSITIONS, PROJECT_TRANSITIONS, DemandStatus, ProjectStatus
from app.services.errors import WorkflowError


def assert_demand_transition(current: DemandStatus, target: DemandStatus) -> None:
    allowed = DEMAND_TRANSITIONS.get(current, set())
    if target not in allowed:
        allowed_names = ", ".join(s.value for s in allowed) or "(none — terminal state)"
        raise WorkflowError(
            f"Cannot move demand from '{current.value}' to '{target.value}'. Allowed next states: {allowed_names}."
        )


def assert_project_transition(current: ProjectStatus, target: ProjectStatus) -> None:
    allowed = PROJECT_TRANSITIONS.get(current, set())
    if target not in allowed:
        allowed_names = ", ".join(s.value for s in allowed) or "(none — terminal state)"
        raise WorkflowError(
            f"Cannot move project from '{current.value}' to '{target.value}'. Allowed next states: {allowed_names}."
        )


def assert_demand_can_convert(demand) -> None:
    if demand.status != DemandStatus.APPROVED:
        raise WorkflowError("Only an Approved demand can be converted to a portfolio project.")
    if demand.project is not None:
        raise WorkflowError("This demand has already been converted to a project.")


def assert_project_can_be_scheduled(project) -> None:
    if not project.requirements:
        raise WorkflowError("Add at least one requirement before scheduling this project on the roadmap.")
    if not project.project_capabilities:
        raise WorkflowError("Assign at least one required capability before scheduling this project on the roadmap.")


def assert_project_can_start(project) -> None:
    if project.roadmap_item is None:
        raise WorkflowError("Project must have a planned roadmap timeline before it can enter execution.")
