from datetime import datetime, timezone

from flask import Blueprint, request

from app.api.response import api_response
from app.auth.decorators import get_current_user, require_role
from app.extensions import db
from app.models.collaboration import Notification
from app.services.errors import NotFoundError

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@require_role()
def list_notifications():
    user = get_current_user()
    query = Notification.query.filter(Notification.user_id == user.id)

    unread_only = request.args.get("unread_only")
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))

    notifications = query.order_by(Notification.created_at.desc()).limit(50).all()
    return api_response(data=[n.to_dict() for n in notifications])


@notifications_bp.patch("/<int:notification_id>/read")
@require_role()
def mark_read(notification_id: int):
    user = get_current_user()
    notification = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if notification is None:
        raise NotFoundError("Notification not found.")

    notification.read_at = datetime.now(timezone.utc)
    db.session.commit()
    return api_response(data=notification.to_dict())
