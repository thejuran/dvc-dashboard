"""Structured error handling for the DVC Dashboard API.

All API errors return a consistent JSON structure:
    {"error": {"type": "...", "message": "...", "fields": [...]}}

Error types: VALIDATION_ERROR, NOT_FOUND, CONFLICT, SERVER_ERROR
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def error_response(
    status_code: int,
    error_type: str,
    message: str,
    fields: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """Build a structured error JSONResponse."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "type": error_type,
                "message": message,
                "fields": fields or [],
            }
        },
    )


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class AppError(Exception):
    """Base exception for all application errors."""

    status_code: int = 500
    error_type: str = "SERVER_ERROR"

    def __init__(self, message: str, fields: list[dict[str, str]] | None = None):
        self.message = message
        self.fields = fields or []
        super().__init__(message)


class ValidationError(AppError):
    """422 -- input validation failed."""

    status_code = 422
    error_type = "VALIDATION_ERROR"


class NotFoundError(AppError):
    """404 -- requested resource does not exist."""

    status_code = 404
    error_type = "NOT_FOUND"


class ConflictError(AppError):
    """409 -- resource conflict (e.g. duplicate)."""

    status_code = 409
    error_type = "CONFLICT"


class ServerError(AppError):
    """500 -- internal server error.

    The real message is logged server-side; clients always see
    "Something went wrong".
    """

    status_code = 500
    error_type = "SERVER_ERROR"


# ---------------------------------------------------------------------------
# Exception handlers (registered on the FastAPI app)
# ---------------------------------------------------------------------------

async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom AppError subclasses."""
    if isinstance(exc, ServerError):
        logger.exception("ServerError: %s", exc.message)
        return error_response(500, "SERVER_ERROR", "Something went wrong")
    return error_response(exc.status_code, exc.error_type, exc.message, exc.fields)


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle FastAPI/Starlette HTTPException (legacy raises)."""
    status_map: dict[int, str] = {
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        400: "VALIDATION_ERROR",
    }
    error_type = status_map.get(exc.status_code, "SERVER_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "Something went wrong"

    if error_type == "SERVER_ERROR":
        logger.exception("Unhandled HTTPException %s: %s", exc.status_code, message)
        message = "Something went wrong"

    return error_response(exc.status_code, error_type, message)


async def handle_pydantic_validation(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic request validation errors.

    Returns ALL invalid fields at once (not fail-on-first).
    """
    fields: list[dict[str, str]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        # Use last element of loc (the field name), skip "body" prefix
        field_name = str(loc[-1]) if loc else "unknown"
        fields.append({"field": field_name, "issue": err.get("msg", "Invalid value")})

    return error_response(
        422,
        "VALIDATION_ERROR",
        "Validation failed",
        fields,
    )


async def handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions.

    Logs the real error server-side; returns generic message to client.
    """
    logger.exception("Unhandled exception: %s", exc)
    return error_response(500, "SERVER_ERROR", "Something went wrong")
