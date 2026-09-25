from marshmallow import Schema, fields, validate

from app.models.enums import Priority, RequestType


class DemandCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=3, max=200))
    business_function_id = fields.Integer(required=True)
    problem_statement = fields.String(required=True, validate=validate.Length(min=10))
    business_need = fields.String(load_default=None)
    support_required = fields.String(load_default=None)
    request_type = fields.String(load_default=RequestType.OTHER.value, validate=validate.OneOf([t.value for t in RequestType]))
    priority = fields.String(load_default=Priority.MEDIUM.value, validate=validate.OneOf([p.value for p in Priority]))
    expected_timeline = fields.String(load_default=None)
    additional_details = fields.String(load_default=None)


class DemandUpdateSchema(Schema):
    title = fields.String(validate=validate.Length(min=3, max=200))
    business_function_id = fields.Integer()
    problem_statement = fields.String(validate=validate.Length(min=10))
    business_need = fields.String(allow_none=True)
    support_required = fields.String(allow_none=True)
    request_type = fields.String(validate=validate.OneOf([t.value for t in RequestType]))
    priority = fields.String(validate=validate.OneOf([p.value for p in Priority]))
    expected_timeline = fields.String(allow_none=True)
    additional_details = fields.String(allow_none=True)
    status = fields.String()  # submission (Draft -> Submitted) goes through this; validated against the state machine


class DemandReviewSchema(Schema):
    action = fields.String(
        required=True,
        validate=validate.OneOf(["Under Review", "Clarification Required", "Validated", "Approved", "Rejected"]),
    )
    comments = fields.String(load_default=None)
