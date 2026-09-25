from datetime import datetime, timezone

from app.extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(40), nullable=False)  # "demand" | "project"
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "user": self.user.name if self.user else None,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(120), nullable=False)
    resource_type = db.Column(db.String(60), nullable=False, index=True)
    resource_id = db.Column(db.Integer, nullable=False, index=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    request_id = db.Column(db.String(64), nullable=True)
    comments = db.Column(db.Text, nullable=True)

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user": self.user.name if self.user else "System",
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "request_id": self.request_id,
            "comments": self.comments,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(60), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "message": self.message,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
