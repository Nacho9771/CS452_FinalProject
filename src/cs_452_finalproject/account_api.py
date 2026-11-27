"""Only /account routes: the verified Firebase UID always determines ownership."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .accounts import Account, KitchenUpdate, ProfileUpdate

router = APIRouter(prefix="/api/v1/account", tags=["Account and kitchen"])
bearer = HTTPBearer(auto_error=False)


def current_uid(
    request: Request,
    credential: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credential is None:
        raise HTTPException(401, "Google sign-in required.", headers={"WWW-Authenticate": "Bearer"})
    return request.app.state.identity.verify(credential.credentials)


Uid = Annotated[str, Depends(current_uid)]


@router.post("", response_model=Account)
def create_account(request: Request, uid: Uid):
    """Create once after Google sign-in; repeated calls preserve all saved data."""
    return request.app.state.accounts.create(uid)


@router.get("", response_model=Account)
def get_account(request: Request, uid: Uid):
    """Retrieve your profile and kitchen; there is no caller-selected user ID."""
    return request.app.state.accounts.read(uid)


@router.put("/profile", response_model=Account)
def put_profile(update: ProfileUpdate, request: Request, uid: Uid):
    """Replace your profile section using its last-read account revision."""
    return request.app.state.accounts.update(
        uid, update.expected_revision, "profile", update.profile.model_dump()
    )


@router.put("/kitchen", response_model=Account)
def put_kitchen(update: KitchenUpdate, request: Request, uid: Uid):
    """Replace your kitchen section; false appliance values mean explicitly not owned."""
    return request.app.state.accounts.update(
        uid, update.expected_revision, "kitchen", update.kitchen.model_dump()
    )
