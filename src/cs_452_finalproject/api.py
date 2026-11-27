"""HTTP entry point: validate input, call recipe logic, serialize the result.

Recipe previews are stateless. Account routes use Firebase and MongoDB when
configured; AI and external recipe services are not connected.
"""

import logging
import os
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

from .account_api import router as account_router
from .models import PreviewRequest, RecipePreview
from .recipes import preview_recipe
from .services import FirebaseIdentity, MongoAccounts

logger = logging.getLogger("uvicorn.error")


def create_app(*, identity=None, accounts=None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(application):
        yield
        application.state.identity.close()
        application.state.accounts.close()

    application = FastAPI(
        title="My Kitchen API",
        version="0.2.0",
        description=(
            "Recipe previews and Firebase-protected account/kitchen storage. "
            "Account routes require Firebase and MongoDB configuration."
        ),
        lifespan=lifespan,
    )
    application.state.identity = identity if identity is not None else FirebaseIdentity()
    application.state.accounts = accounts if accounts is not None else MongoAccounts()
    application.include_router(account_router)

    @application.middleware("http")
    async def trace_request(request: Request, call_next):
        """Connect a response to its server log without recording private inputs."""
        request_id = str(uuid4())
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_id=%s action=request_failed", request_id)
            raise
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s service=my-kitchen-api method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            (perf_counter() - started) * 1000,
        )
        return response

    @application.get("/health", tags=["Development"])
    def health() -> dict:
        """Liveness only: a running API does not imply working cloud integrations."""
        integrations = {
            name: "not_connected"
            for name in ("firebase", "mongodb", "redis", "ollama", "recipes", "store_prices")
        }
        if os.getenv("FIREBASE_PROJECT_ID"):
            integrations["firebase"] = "configured_not_verified"
        if os.getenv("MONGODB_URI"):
            integrations["mongodb"] = "configured_not_verified"
        return {
            "status": "ok",
            "service": "my-kitchen-api",
            "milestone": "account-kitchen",
            "integrations": integrations,
        }

    @application.post("/api/v1/recipes/preview", response_model=RecipePreview, tags=["Recipes"])
    def preview(request: PreviewRequest) -> RecipePreview:
        """Preview only. This does not save, publish, or claim ownership of a recipe."""
        try:
            return preview_recipe(request)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    return application


app = create_app()
