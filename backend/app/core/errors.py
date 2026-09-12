"""Application error type + consistent JSON error envelope handlers.

Every error returned to a client has the shape:
    {"success": false, "error": {"code": "...", "message": "...", "details": ...}}
Internal stack traces are never exposed.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("worktrack")


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


# ---- Convenience factories ----
def bad_request(message: str, code: str = "VALIDATION_ERROR", details: Any = None) -> AppError:
    return AppError(code, message, 400, details)


def unauthorized(
    message: str = "Not authenticated.", code: str = "NOT_AUTHENTICATED", details: Any = None
) -> AppError:
    return AppError(code, message, 401, details)


def forbidden(
    message: str = "You do not have access to this resource.",
    code: str = "FORBIDDEN",
    details: Any = None,
) -> AppError:
    return AppError(code, message, 403, details)


def not_found(
    message: str = "Resource not found.", code: str = "NOT_FOUND", details: Any = None
) -> AppError:
    return AppError(code, message, 404, details)


def conflict(message: str, code: str = "CONFLICT", details: Any = None) -> AppError:
    return AppError(code, message, 409, details)


def unprocessable(message: str, code: str = "VALIDATION_ERROR", details: Any = None) -> AppError:
    return AppError(code, message, 422, details)


def _envelope(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    err: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return JSONResponse(status_code=status_code, content={"success": False, "error": err})


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        details = [
            {"loc": list(e.get("loc", [])), "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]
        return _envelope(422, "VALIDATION_ERROR", "Request validation failed.", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        code_map = {
            401: "NOT_AUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMITED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _envelope(exc.status_code, code, message)

    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError):  # noqa: ARG001
        return _envelope(409, "CONFLICT", "This action conflicts with existing data.")

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):  # noqa: ARG001
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _envelope(500, "INTERNAL_ERROR", "An unexpected error occurred.")
