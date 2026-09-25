from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from app.api.response import api_response
from app.auth.decorators import get_current_user
from app.models.user import User
from app.schemas.auth import LoginSchema
from flask_jwt_extended import jwt_required

auth_bp = Blueprint("auth", __name__)

login_schema = LoginSchema()


@auth_bp.post("/login")
def login():
    payload = login_schema.load(request.get_json(force=True) or {})
    user = User.query.filter_by(email=payload["email"].lower()).first()
    if user is None or not user.active or not user.check_password(payload["password"]):
        return api_response(error="Invalid email or password.", status=401)

    token = create_access_token(identity=str(user.id))
    return api_response(data={"access_token": token, "user": user.to_dict()})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = get_current_user()
    return api_response(data=user.to_dict())
