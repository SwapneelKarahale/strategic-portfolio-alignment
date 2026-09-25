import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from flask_jwt_extended import create_access_token

from app import create_app
from app.extensions import db as _db
from config import TestingConfig
from app.models.enums import Role
from app.models.project import Capability
from app.models.user import BusinessFunction, User


@pytest.fixture()
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def business_function(db):
    bf = BusinessFunction(name="Finance")
    db.session.add(bf)
    db.session.commit()
    return bf


@pytest.fixture()
def capability(db):
    cap = Capability(name="Data Engineering")
    db.session.add(cap)
    db.session.commit()
    return cap


def make_test_user(db, name, email, role, business_function=None):
    user = User(name=name, email=email, role=role, business_function_id=business_function.id if business_function else None)
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def requestor(db, business_function):
    return make_test_user(db, "Test Requestor", "requestor@test.example", Role.REQUESTOR, business_function)


@pytest.fixture()
def project_manager(db):
    return make_test_user(db, "Test PM", "pm@test.example", Role.PROJECT_MANAGER)


@pytest.fixture()
def management(db):
    return make_test_user(db, "Test Management", "management@test.example", Role.MANAGEMENT)


@pytest.fixture()
def admin(db):
    return make_test_user(db, "Test Admin", "admin@test.example", Role.ADMIN)


def auth_header(app, user):
    with app.app_context():
        token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}
