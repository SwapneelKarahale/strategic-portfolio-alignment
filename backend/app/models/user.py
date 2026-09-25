from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.enums import Role


class BusinessFunction(db.Model):
    __tablename__ = "business_functions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    users = db.relationship("User", back_populates="business_function")
    demands = db.relationship("Demand", back_populates="business_function")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role, name="role"), nullable=False)
    business_function_id = db.Column(db.Integer, db.ForeignKey("business_functions.id"), nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    business_function = db.relationship("BusinessFunction", back_populates="users")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value,
            "business_function_id": self.business_function_id,
            "business_function": self.business_function.name if self.business_function else None,
            "active": self.active,
        }
