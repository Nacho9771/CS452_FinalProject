"""Opt-in, loopback-only client for testing real Google sign-in and account saves."""

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

ASSETS = Path(__file__).parent / "dev_web"


def local_development_only(request: Request):
    if (
        os.getenv("ENABLE_DEV_SIGNIN") != "1"
        or request.client is None
        or request.client.host not in ("127.0.0.1", "::1")
        or request.url.hostname not in ("localhost", "127.0.0.1", "::1")
    ):
        raise HTTPException(404, "Not found")


router = APIRouter(
    prefix="/dev", dependencies=[Depends(local_development_only)], include_in_schema=False
)
HEADERS = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}


@router.get("/sign-in")
def sign_in_page():
    return FileResponse(ASSETS / "sign-in.html", headers=HEADERS)


@router.get("/sign-in.js")
def sign_in_script():
    return FileResponse(ASSETS / "sign-in.js", media_type="text/javascript", headers=HEADERS)


@router.get("/sign-in.css")
def sign_in_styles():
    return FileResponse(ASSETS / "sign-in.css", media_type="text/css", headers=HEADERS)


@router.get("/firebase-config")
def public_firebase_config():
    # Explicit allowlist. Never serialize the process environment or Admin credentials.
    config = {
        "apiKey": os.getenv("FIREBASE_WEB_API_KEY"),
        "appId": os.getenv("FIREBASE_WEB_APP_ID"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    }
    if not all(config.values()):
        raise HTTPException(
            503, "Firebase web client configuration is incomplete. See docs/DEV_SIGNIN.md."
        )
    return JSONResponse(config, headers=HEADERS)
