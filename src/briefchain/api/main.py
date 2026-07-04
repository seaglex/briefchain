"""FastAPI application factory and route registration."""

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from briefchain.api.exceptions import (
    APIError,
    api_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from briefchain.api.routes import (
    auth,
    brief_transfers,
    brief_versions,
    briefs,
    chains,
    feedbacks,
    invites,
    kanban,
    tasks,
    users,
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="BriefChain API",
        description="API for BriefChain user authentication and profile management.",
        version="0.1.0",
    )

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(briefs.router, prefix="/api/v1")
    app.include_router(brief_versions.router, prefix="/api/v1")
    app.include_router(brief_transfers.router, prefix="/api/v1")
    app.include_router(feedbacks.brief_router, prefix="/api/v1")
    app.include_router(feedbacks.feedback_router, prefix="/api/v1")
    app.include_router(chains.router, prefix="/api/v1")
    app.include_router(invites.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(tasks.comments_router, prefix="/api/v1")
    app.include_router(kanban.board_router, prefix="/api/v1")
    app.include_router(kanban.kanban_router, prefix="/api/v1")
    app.include_router(kanban.template_router, prefix="/api/v1")

    @app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
    def health_check() -> dict:
        """Return API health status."""
        return {"status": "ok"}

    return app


app = create_app()
