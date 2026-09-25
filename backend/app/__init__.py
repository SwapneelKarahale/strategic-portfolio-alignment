from flask import Flask

from config import Config
from app.extensions import cors, db, jwt, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from app import models  # noqa: F401  (register models with SQLAlchemy metadata)
    from app.api.errors import register_error_handlers
    from app.api.auth import auth_bp
    from app.api.demands import demands_bp
    from app.api.projects import projects_bp
    from app.api.roadmap import roadmap_bp
    from app.api.dashboard import dashboard_bp
    from app.api.audit import audit_bp
    from app.api.notifications import notifications_bp
    from app.api.lookups import lookups_bp

    register_error_handlers(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(demands_bp, url_prefix="/api/demands")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(roadmap_bp, url_prefix="/api/roadmap")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(audit_bp, url_prefix="/api/audit-logs")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(lookups_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"success": True, "data": {"status": "ok"}, "error": None}

    @app.cli.command("seed")
    def seed_command():
        """Populate the database with demo data: flask --app wsgi seed"""
        from app.seed import run_seed

        run_seed()

    return app
