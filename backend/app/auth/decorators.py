from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User
from app.services.errors import ForbiddenError, NotFoundError


def get_current_user() -> User:
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    if user is None or not user.active:
        raise NotFoundError("Authenticated user not found or inactive.")
    return user


def require_role(*roles):
    """Restrict a route to one or more roles. Always used alongside jwt_required — authorization
    is enforced here in the backend, never assumed from what the frontend chooses to show."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if roles and user.role not in roles:
                allowed = ", ".join(r.value for r in roles)
                raise ForbiddenError(f"This action requires one of the following roles: {allowed}.")
            return fn(*args, **kwargs)

        return wrapper

    return decorator
