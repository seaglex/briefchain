"""Unified API error response handling."""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIError(Exception):
    """Application-specific API error."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def api_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, Any],
) -> JSONResponse:
    """Build a unified JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
            }
        },
    )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:  # noqa: ARG001
    """Handle application-specific API errors."""
    return api_error_response(
        exc.code,
        exc.message,
        exc.status_code,
        exc.details,
    )


async def http_exception_handler(
    request: Request,  # noqa: ARG001
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle FastAPI/starlette HTTP exceptions."""
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "")
        details = exc.detail
    else:
        message = str(exc.detail)
        details = {}

    status_code_map = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
    }
    code = status_code_map.get(exc.status_code, "HTTP_ERROR")

    return api_error_response(
        code=code,
        message=message,
        status_code=exc.status_code,
        details=details,
    )


async def validation_exception_handler(
    request: Request,  # noqa: ARG001
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    errors = exc.errors()
    simplified = [
        {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in errors
    ]
    return api_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        details={"errors": simplified},
    )


async def unhandled_exception_handler(
    request: Request,  # noqa: ARG001
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions in production."""
    return api_error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=500,
        details={"type": exc.__class__.__name__},
    )
