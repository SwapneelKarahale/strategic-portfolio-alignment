from marshmallow import Schema, fields, validate


class RoadmapScheduleSchema(Schema):
    project_id = fields.Integer(required=True)
    quarter = fields.String(required=True, validate=validate.Regexp(r"^\d{4}-Q[1-4]$", error="quarter must look like '2026-Q1'"))
    sequence = fields.Integer(load_default=0)
    planned_start = fields.Date(required=True)
    planned_end = fields.Date(required=True)
