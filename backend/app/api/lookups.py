from flask import Blueprint, request

from app.api.response import api_response
from app.auth.decorators import require_role
from app.models.enums import Role
from app.models.project import Capability
from app.models.user import BusinessFunction, User

lookups_bp = Blueprint("lookups", __name__)


@lookups_bp.get("/business-functions")
@require_role()
def list_business_functions():
    items = BusinessFunction.query.order_by(BusinessFunction.name).all()
    return api_response(data=[{"id": bf.id, "name": bf.name} for bf in items])


@lookups_bp.get("/capabilities")
@require_role()
def list_capabilities():
    items = Capability.query.order_by(Capability.name).all()
    return api_response(data=[{"id": c.id, "name": c.name} for c in items])


@lookups_bp.get("/users")
@require_role()
def list_users():
    query = User.query.filter(User.active.is_(True))
    role = request.args.get("role")
    if role:
        query = query.filter(User.role == role)
    items = query.order_by(User.name).all()
    return api_response(data=[u.to_dict() for u in items])
