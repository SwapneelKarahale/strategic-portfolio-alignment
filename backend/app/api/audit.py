from flask import Blueprint, request

from app.api.response import paginated_response
from app.auth.decorators import require_role
from app.models.collaboration import AuditLog
from app.models.enums import Role

audit_bp = Blueprint("audit", __name__)


@audit_bp.get("")
@require_role(Role.PROJECT_MANAGER, Role.MANAGEMENT, Role.ADMIN)
def list_audit_logs():
    query = AuditLog.query

    resource_type = request.args.get("resource_type")
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    resource_id = request.args.get("resource_id", type=int)
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)

    query = query.order_by(AuditLog.timestamp.desc())
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    return paginated_response(query, lambda log: log.to_dict(), page, per_page)
