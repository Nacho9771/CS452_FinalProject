"""Authenticated manual recipe library. No public publishing or URL fetching yet."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from .account_api import Uid
from .recipe_library import RecipeCreate, RecipePage, RecipeUpdate, SavedRecipe, schema_org

router = APIRouter(prefix="/api/v1/recipes", tags=["Your Recipes"])


@router.post("", response_model=SavedRecipe, status_code=201)
def create_recipe(body: RecipeCreate, request: Request, uid: Uid):
    """Save privately. Reuse client_request_id when retrying the same creation."""
    return request.app.state.recipes.create(uid, body)


@router.get("", response_model=RecipePage)
def list_recipes(
    request: Request,
    uid: Uid,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return request.app.state.recipes.list(uid, offset, limit)


@router.get("/{recipe_id}", response_model=SavedRecipe)
def get_recipe(recipe_id: UUID, request: Request, uid: Uid):
    return request.app.state.recipes.read(uid, recipe_id)


@router.put("/{recipe_id}", response_model=SavedRecipe)
def put_recipe(recipe_id: UUID, body: RecipeUpdate, request: Request, uid: Uid):
    return request.app.state.recipes.update(uid, recipe_id, body)


@router.get("/{recipe_id}/schema")
def export_recipe(recipe_id: UUID, request: Request, uid: Uid):
    """Return schema.org Recipe JSON-LD; export remains owner-only."""
    return schema_org(request.app.state.recipes.read(uid, recipe_id).recipe)
