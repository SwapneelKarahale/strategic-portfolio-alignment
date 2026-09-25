from datetime import datetime, timezone

from app.extensions import db
from app.models.enums import Priority, ProjectHealth, ProjectStatus


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    demand_id = db.Column(db.Integer, db.ForeignKey("demands.id"), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    business_objective = db.Column(db.Text, nullable=True)
    project_manager_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    status = db.Column(db.Enum(ProjectStatus, name="project_status"), nullable=False, default=ProjectStatus.PORTFOLIO, index=True)
    priority = db.Column(db.Enum(Priority, name="project_priority"), nullable=False, default=Priority.MEDIUM)
    health = db.Column(db.Enum(ProjectHealth, name="project_health"), nullable=False, default=ProjectHealth.ON_TRACK)

    estimated_effort = db.Column(db.String(120), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    target_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    demand = db.relationship("Demand", back_populates="project")
    project_manager = db.relationship("User")
    requirements = db.relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    project_capabilities = db.relationship("ProjectCapability", back_populates="project", cascade="all, delete-orphan")
    roadmap_item = db.relationship("RoadmapItem", back_populates="project", uselist=False, cascade="all, delete-orphan")
    milestones = db.relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    dependencies = db.relationship(
        "Dependency", back_populates="project", foreign_keys="Dependency.project_id", cascade="all, delete-orphan"
    )

    def to_dict(self, include_details: bool = False) -> dict:
        data = {
            "id": self.id,
            "demand_id": self.demand_id,
            "name": self.name,
            "description": self.description,
            "business_objective": self.business_objective,
            "project_manager_id": self.project_manager_id,
            "project_manager": self.project_manager.name if self.project_manager else None,
            "status": self.status.value,
            "priority": self.priority.value,
            "health": self.health.value,
            "estimated_effort": self.estimated_effort,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "business_function": self.demand.business_function.name if self.demand and self.demand.business_function else None,
            "on_roadmap": self.roadmap_item is not None,
        }
        if include_details:
            data["requirements"] = [r.to_dict() for r in self.requirements]
            data["capabilities"] = [pc.to_dict() for pc in self.project_capabilities]
            data["milestones"] = [m.to_dict() for m in self.milestones]
            data["dependencies"] = [d.to_dict() for d in self.dependencies]
            data["roadmap_item"] = self.roadmap_item.to_dict() if self.roadmap_item else None
        return data


class Requirement(db.Model):
    __tablename__ = "requirements"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    requirement_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(60), nullable=False, default="Open")

    project = db.relationship("Project", back_populates="requirements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "requirement_text": self.requirement_text,
            "category": self.category,
            "status": self.status,
        }


class Capability(db.Model):
    __tablename__ = "capabilities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    project_capabilities = db.relationship("ProjectCapability", back_populates="capability")


class ProjectCapability(db.Model):
    __tablename__ = "project_capabilities"

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), primary_key=True)
    capability_id = db.Column(db.Integer, db.ForeignKey("capabilities.id"), primary_key=True)
    effort_estimate = db.Column(db.String(120), nullable=True)

    project = db.relationship("Project", back_populates="project_capabilities")
    capability = db.relationship("Capability", back_populates="project_capabilities")

    def to_dict(self) -> dict:
        return {
            "capability_id": self.capability_id,
            "capability": self.capability.name if self.capability else None,
            "effort_estimate": self.effort_estimate,
        }


class RoadmapItem(db.Model):
    __tablename__ = "roadmap_items"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), unique=True, nullable=False)
    quarter = db.Column(db.String(20), nullable=False)  # e.g. "2026-Q1"
    sequence = db.Column(db.Integer, nullable=False, default=0)
    planned_start = db.Column(db.Date, nullable=False)
    planned_end = db.Column(db.Date, nullable=False)

    project = db.relationship("Project", back_populates="roadmap_item")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "quarter": self.quarter,
            "sequence": self.sequence,
            "planned_start": self.planned_start.isoformat() if self.planned_start else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "status": self.project.status.value if self.project else None,
            "business_function": (
                self.project.demand.business_function.name
                if self.project and self.project.demand and self.project.demand.business_function
                else None
            ),
            "project_manager": self.project.project_manager.name if self.project and self.project.project_manager else None,
        }


class Milestone(db.Model):
    __tablename__ = "milestones"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(60), nullable=False, default="Planned")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    project = db.relationship("Project", back_populates="milestones")
    owner = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "owner_id": self.owner_id,
            "owner": self.owner.name if self.owner else None,
        }


class Dependency(db.Model):
    __tablename__ = "dependencies"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    depends_on_project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(60), nullable=False, default="Open")

    project = db.relationship("Project", back_populates="dependencies", foreign_keys=[project_id])
    depends_on_project = db.relationship("Project", foreign_keys=[depends_on_project_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "depends_on_project_id": self.depends_on_project_id,
            "depends_on_project_name": self.depends_on_project.name if self.depends_on_project else None,
            "description": self.description,
            "status": self.status,
        }
