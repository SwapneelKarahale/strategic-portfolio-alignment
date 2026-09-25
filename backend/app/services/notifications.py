from app.extensions import db
from app.models.collaboration import Notification


def notify(user, type_: str, message: str) -> Notification | None:
    """Create an in-app notification for a user. No-op if the user is unknown (e.g. unassigned PM)."""
    if user is None:
        return None
    notification = Notification(user_id=user.id, type=type_, message=message)
    db.session.add(notification)
    return notification


def notify_many(users, type_: str, message: str) -> None:
    for user in users:
        notify(user, type_, message)
