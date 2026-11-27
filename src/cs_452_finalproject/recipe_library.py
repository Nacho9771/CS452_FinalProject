"""Private recipe contracts, MongoDB persistence, and schema.org export."""

import hashlib
import json
from datetime import UTC, datetime
from threading import Lock
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import HTTPException
from pydantic import Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError

from .models import InputModel, Recipe


class PrivateRecipe(Recipe):
    # Publication needs its own deliberate workflow, not a forged creation flag.
    visibility: Literal["private"] = "private"


class RecipeCreate(InputModel):
    client_request_id: UUID
    recipe: PrivateRecipe


class RecipeUpdate(InputModel):
    expected_revision: int = Field(ge=0, strict=True)
    recipe: PrivateRecipe


class SavedRecipe(InputModel):
    id: UUID
    revision: int
    created_at: datetime
    updated_at: datetime
    recipe: PrivateRecipe


class RecipePage(InputModel):
    items: list[SavedRecipe]
    next_offset: int | None


class MongoRecipes:
    def __init__(self, accounts):
        # Reuse the account adapter's connection pool; recipes use a separate collection.
        self.accounts = accounts
        self.index_ready = False
        self.lock = Lock()

    def collection(self):
        collection = self.accounts.collection().database.recipes
        with self.lock:
            if not self.index_ready:
                collection.create_index(
                    [("owner_uid", 1), ("created_at", -1), ("_id", -1)],
                    name="recipes_by_owner",
                )
                self.index_ready = True
        return collection

    @staticmethod
    def decode(document):
        if document is None:
            raise HTTPException(404, "Recipe not found.")
        return SavedRecipe.model_validate(
            {
                "id": document["_id"],
                "revision": document["revision"],
                "created_at": document["created_at"],
                "updated_at": document["updated_at"],
                "recipe": document["recipe"],
            }
        )

    def create(self, uid: str, request: RecipeCreate) -> SavedRecipe:
        payload = request.recipe.model_dump(mode="json")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        recipe_id = str(uuid5(NAMESPACE_URL, f"my-kitchen:{uid}:{request.client_request_id}"))
        now = datetime.now(UTC)
        document = {
            "_id": recipe_id,
            "owner_uid": uid,
            "revision": 0,
            "created_at": now,
            "updated_at": now,
            "recipe": payload,
            "creation_hash": fingerprint,
        }
        try:
            collection = self.collection()
            try:
                collection.insert_one(document)
                return self.decode(document)
            except DuplicateKeyError:
                previous = collection.find_one({"_id": recipe_id, "owner_uid": uid})
                if previous is None or previous["creation_hash"] != fingerprint:
                    raise HTTPException(
                        409, "This creation request ID was already used for another recipe."
                    ) from None
                return self.decode(previous)
        except PyMongoError:
            raise HTTPException(503, "Recipe storage is temporarily unavailable.") from None

    def read(self, uid: str, recipe_id: UUID) -> SavedRecipe:
        try:
            return self.decode(
                self.collection().find_one({"_id": str(recipe_id), "owner_uid": uid})
            )
        except PyMongoError:
            raise HTTPException(503, "Recipe storage is temporarily unavailable.") from None

    def list(self, uid: str, offset: int, limit: int) -> RecipePage:
        try:
            rows = list(
                self.collection()
                .find({"owner_uid": uid})
                .sort([("created_at", -1), ("_id", -1)])
                .skip(offset)
                .limit(limit + 1)
            )
            return RecipePage(
                items=[self.decode(row) for row in rows[:limit]],
                next_offset=offset + limit if len(rows) > limit else None,
            )
        except PyMongoError:
            raise HTTPException(503, "Recipe storage is temporarily unavailable.") from None

    def update(self, uid: str, recipe_id: UUID, request: RecipeUpdate) -> SavedRecipe:
        query = {"_id": str(recipe_id), "owner_uid": uid}
        try:
            collection = self.collection()
            result = collection.find_one_and_update(
                {**query, "revision": request.expected_revision},
                {
                    "$set": {
                        "recipe": request.recipe.model_dump(mode="json"),
                        "updated_at": datetime.now(UTC),
                    },
                    "$inc": {"revision": 1},
                },
                return_document=ReturnDocument.AFTER,
            )
            if result is None:
                if collection.find_one(query, {"_id": 1}) is None:
                    raise HTTPException(404, "Recipe not found.")
                raise HTTPException(409, "Recipe changed on another device. Reload before saving.")
            return self.decode(result)
        except PyMongoError:
            raise HTTPException(503, "Recipe storage is temporarily unavailable.") from None


def schema_org(recipe: Recipe) -> dict:
    result = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipe.title,
        "description": recipe.description,
        "recipeYield": f"{recipe.servings} servings",
        "recipeIngredient": [item.original_text for item in recipe.ingredients],
        "recipeInstructions": [{"@type": "HowToStep", "text": step} for step in recipe.steps],
        "prepTime": f"PT{recipe.prep_minutes}M",
        "cookTime": f"PT{recipe.cook_minutes}M",
        "image": [str(url) for url in recipe.image_urls],
        "tool": [{"@type": "HowToTool", "name": tool} for tool in recipe.equipment],
    }
    if recipe.source_url:
        result["isBasedOn"] = str(recipe.source_url)
    if recipe.cuisine:
        result["recipeCuisine"] = recipe.cuisine
    if recipe.estimated_cost is not None:
        result["estimatedCost"] = {
            "@type": "MonetaryAmount",
            "currency": recipe.currency,
            "value": str(recipe.estimated_cost),
        }
    return result
