from flask import Flask
from marshmallow import ValidationError

from app.api.response import api_response
from app.services.errors import ApiError


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return api_response(error=err.message, status=err.status_code)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return api_response(error=err.messages, status=422)

    @app.errorhandler(404)
    def handle_not_found(err):
        return api_response(error="Resource not found.", status=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(err):
        return api_response(error="Method not allowed.", status=405)

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        app.logger.exception("Unhandled exception")
        return api_response(error="An unexpected error occurred.", status=500)
