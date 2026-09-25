import uuid

from app.extensions import db
from app.models.collaboration import AuditLog


def log_action(
    user,
    action: str,
    resource_type: str,
    resource_id: int,
    old_value: str | None = None,
    new_value: str | None = None,
    comments: str | None = None,
    request_id: str | None = None,
) -> AuditLog:
    """Record a workflow action for the audit trail. Does not commit — caller commits as part of the
    same transaction as the action being audited, so a failed write never produces an orphan log entry."""
    entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        comments=comments,
        request_id=request_id or str(uuid.uuid4()),
    )
    db.session.add(entry)
    return entry
