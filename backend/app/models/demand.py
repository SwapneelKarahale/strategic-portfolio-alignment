from datetime import datetime, timezone

from app.extensions import db
from app.models.enums import DemandStatus, Priority, RequestType


class Demand(db.Model):
    __tablename__ = "demands"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    business_function_id = db.Column(db.Integer, db.ForeignKey("business_functions.id"), nullable=False)
    requestor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    problem_statement = db.Column(db.Text, nullable=False)
    business_need = db.Column(db.Text, nullable=True)
    support_required = db.Column(db.Text, nullable=True)
    request_type = db.Column(db.Enum(RequestType, name="request_type"), nullable=False, default=RequestType.OTHER)
    priority = db.Column(db.Enum(Priority, name="priority"), nullable=False, default=Priority.MEDIUM)
    expected_timeline = db.Column(db.String(120), nullable=True)
    additional_details = db.Column(db.Text, nullable=True)

    status = db.Column(db.Enum(DemandStatus, name="demand_status"), nullable=False, default=DemandStatus.DRAFT, index=True)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    business_function = db.relationship("BusinessFunction", back_populates="demands")
    requestor = db.relationship("User", foreign_keys=[requestor_id])
    reviews = db.relationship("DemandReview", back_populates="demand", order_by="DemandReview.created_at")
    project = db.relationship("Project", back_populates="demand", uselist=False)

    def to_dict(self, include_reviews: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "business_function_id": self.business_function_id,
            "business_function": self.business_function.name if self.business_function else None,
            "requestor_id": self.requestor_id,
            "requestor": self.requestor.name if self.requestor else None,
            "problem_statement": self.problem_statement,
            "business_need": self.business_need,
            "support_required": self.support_required,
            "request_type": self.request_type.value if self.request_type else None,
            "priority": self.priority.value if self.priority else None,
            "expected_timeline": self.expected_timeline,
            "additional_details": self.additional_details,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "has_project": self.project is not None,
        }
        if include_reviews:
            data["reviews"] = [review.to_dict() for review in self.reviews]
        return data


class DemandReview(db.Model):
    __tablename__ = "demand_reviews"

    id = db.Column(db.Integer, primary_key=True)
    demand_id = db.Column(db.Integer, db.ForeignKey("demands.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(60), nullable=False)  # e.g. "moved to Under Review", "requested clarification"
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    demand = db.relationship("Demand", back_populates="reviews")
    reviewer = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "demand_id": self.demand_id,
            "reviewer_id": self.reviewer_id,
            "reviewer": self.reviewer.name if self.reviewer else None,
            "action": self.action,
            "comments": self.comments,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
