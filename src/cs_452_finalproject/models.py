"""Validated recipe input/output shared by the HTTP routes and recipe logic.

These are internal models inspired by schema.org/Recipe, not a JSON-LD importer.
Keep original ingredient text alongside structured values so parsing never has to
guess away an instruction such as 'sifted' or 'divided'.
"""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveQuantity = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]


class InputModel(BaseModel):
    # Catch misspelled fields instead of silently throwing the user's data away.
    model_config = ConfigDict(extra="forbid")


class Unit(StrEnum):
    GRAM = "g"
    KILOGRAM = "kg"
    OUNCE = "oz"
    POUND = "lb"
    MILLILITER = "ml"
    LITER = "l"
    US_TEASPOON = "tsp"
    US_TABLESPOON = "tbsp"
    US_CUP = "cup"
    COUNT = "count"


class Ingredient(InputModel):
    name: NonEmptyText
    original_text: NonEmptyText
    # Both are optional for ingredients like 'salt to taste'.
    quantity: PositiveQuantity | None = None
    unit: Unit | None = None
    # Only supply an ingredient-specific known value; never assume water density.
    density_g_per_ml: PositiveQuantity | None = None


class Recipe(InputModel):
    title: NonEmptyText
    description: str = Field(default="", max_length=4000)
    servings: int = Field(ge=1, le=1000, strict=True)
    ingredients: list[Ingredient] = Field(min_length=1, max_length=200)
    steps: list[NonEmptyText] = Field(min_length=1, max_length=200)
    prep_minutes: int = Field(ge=0, strict=True)
    cook_minutes: int = Field(ge=0, strict=True)
    source_url: HttpUrl | None = None
    image_urls: list[HttpUrl] = Field(default_factory=list, max_length=10)
    cuisine: str = Field(default="", max_length=100)
    estimated_cost: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)] | None = None
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    equipment: list[NonEmptyText] = Field(default_factory=list)
    # Recipe creation will default to private when persistence is connected.
    visibility: str = Field(default="private", pattern="^(private|public)$")


class PreviewRequest(InputModel):
    recipe: Recipe
    target_servings: int = Field(ge=1, le=1000, strict=True)
    # Keys are zero-based ingredient positions; unspecified items keep source units.
    target_units: dict[int, Unit] = Field(default_factory=dict)


class PreviewIngredient(InputModel):
    name: str
    original_text: str
    quantity: Decimal | None
    unit: Unit | None
    warning: str | None = None


class RecipePreview(InputModel):
    title: str
    original_servings: int
    servings: int
    ingredients: list[PreviewIngredient]
    steps: list[str]
    prep_minutes: int
    cook_minutes: int
    source_url: HttpUrl | None
