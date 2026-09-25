import enum


class Role(str, enum.Enum):
    REQUESTOR = "requestor"
    PROJECT_MANAGER = "project_manager"
    MANAGEMENT = "management"
    ADMIN = "admin"


class DemandStatus(str, enum.Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    CLARIFICATION_REQUIRED = "Clarification Required"
    VALIDATED = "Validated"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ProjectStatus(str, enum.Enum):
    PORTFOLIO = "Portfolio"
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    AT_RISK = "At Risk"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"


class ProjectHealth(str, enum.Enum):
    ON_TRACK = "On Track"
    AT_RISK = "At Risk"
    BLOCKED = "Blocked"


class Priority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RequestType(str, enum.Enum):
    TASK = "Task"
    AUTOMATION = "Automation"
    APPLICATION = "Application"
    ANALYTICS_REPORTING = "Analytics/Reporting"
    REPLICATION = "Replication"
    DATA_SOLUTION = "Data Solution"
    OTHER = "Other"


class MilestoneStatus(str, enum.Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "In Progress"
    AT_RISK = "At Risk"
    OVERDUE = "Overdue"
    COMPLETED = "Completed"


# Valid forward transitions for a demand. Rejection/clarification can happen from most active states.
DEMAND_TRANSITIONS = {
    DemandStatus.DRAFT: {DemandStatus.SUBMITTED},
    DemandStatus.SUBMITTED: {DemandStatus.UNDER_REVIEW},
    DemandStatus.UNDER_REVIEW: {
        DemandStatus.CLARIFICATION_REQUIRED,
        DemandStatus.VALIDATED,
        DemandStatus.REJECTED,
    },
    DemandStatus.CLARIFICATION_REQUIRED: {DemandStatus.UNDER_REVIEW, DemandStatus.REJECTED},
    DemandStatus.VALIDATED: {DemandStatus.APPROVED, DemandStatus.REJECTED},
    DemandStatus.APPROVED: set(),
    DemandStatus.REJECTED: set(),
}

# Valid forward transitions for a project's execution status.
PROJECT_TRANSITIONS = {
    ProjectStatus.PORTFOLIO: {ProjectStatus.PLANNED},
    ProjectStatus.PLANNED: {ProjectStatus.IN_PROGRESS},
    ProjectStatus.IN_PROGRESS: {ProjectStatus.AT_RISK, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED},
    ProjectStatus.AT_RISK: {ProjectStatus.IN_PROGRESS, ProjectStatus.BLOCKED, ProjectStatus.COMPLETED},
    ProjectStatus.BLOCKED: {ProjectStatus.IN_PROGRESS, ProjectStatus.AT_RISK},
    ProjectStatus.COMPLETED: set(),
}
