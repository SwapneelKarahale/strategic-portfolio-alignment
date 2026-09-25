from marshmallow import Schema, fields, validate

from app.models.enums import Priority, ProjectStatus


class ProjectUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=3, max=200))
    description = fields.String(allow_none=True)
    business_objective = fields.String(allow_none=True)
    project_manager_id = fields.Integer(allow_none=True)
    priority = fields.String(validate=validate.OneOf([p.value for p in Priority]))
    estimated_effort = fields.String(allow_none=True)
    start_date = fields.Date(allow_none=True)
    target_date = fields.Date(allow_none=True)


class ProjectStatusUpdateSchema(Schema):
    status = fields.String(required=True, validate=validate.OneOf([s.value for s in ProjectStatus]))
    health = fields.String(load_default=None)
    comments = fields.String(load_default=None)


class RequirementCreateSchema(Schema):
    requirement_text = fields.String(required=True, validate=validate.Length(min=3))
    category = fields.String(load_default=None)


class CapabilityAssignSchema(Schema):
    capability_id = fields.Integer(required=True)
    effort_estimate = fields.String(load_default=None)


class MilestoneCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=3, max=200))
    due_date = fields.Date(required=True)
    owner_id = fields.Integer(load_default=None)


class MilestoneUpdateSchema(Schema):
    status = fields.String(validate=validate.OneOf(["Planned", "In Progress", "At Risk", "Overdue", "Completed"]))
    due_date = fields.Date()
    name = fields.String(validate=validate.Length(min=3, max=200))
