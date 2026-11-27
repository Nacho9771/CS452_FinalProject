"""Account contracts. Ownership/revision fields never come from editable profile data."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .models import InputModel

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Choice = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
ApplianceId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9_-]{1,80}$")]


class Store(InputModel):
    provider: Choice
    location_id: Choice
    name: Choice


class Profile(InputModel):
    # Empty fields let each onboarding screen save before setup is finished.
    first_name: ShortText = ""
    last_name: ShortText = ""
    address: Annotated[str, Field(max_length=1000)] = ""
    phone: ShortText = ""
    household_size: int = Field(default=1, ge=1, le=1000, strict=True)
    measurement_system: Literal["us", "metric"] = "us"
    default_cooking_minutes: int = Field(default=30, ge=1, le=1440, strict=True)
    stores: list[Store] = Field(default_factory=list, max_length=3)
    cuisine_preferences: list[Choice] = Field(default_factory=list, max_length=50)
    exclusive_cuisines: bool = Field(default=False, strict=True)
    dietary_restrictions: list[Choice] = Field(default_factory=list, max_length=50)
    apply_dietary_restrictions: bool = Field(default=True, strict=True)
    onboarding_step: Literal[
        "name", "contact", "stores", "preferences", "household", "appliances", "spices", "ready"
    ] = "name"


class Kitchen(InputModel):
    # Missing key = unanswered, false = explicitly not owned. Never confuse them.
    appliances: dict[ApplianceId, Annotated[bool, Field(strict=True)]] = Field(
        default_factory=dict, max_length=200
    )
    spices: list[Choice] = Field(default_factory=list, max_length=200)
    spice_setup: Literal["not_started", "skipped", "provided"] = "not_started"


class Account(InputModel):
    uid: str
    revision: int
    created_at: datetime
    updated_at: datetime
    profile: Profile
    kitchen: Kitchen


class ProfileUpdate(InputModel):
    expected_revision: int = Field(ge=0, strict=True)
    profile: Profile


class KitchenUpdate(InputModel):
    expected_revision: int = Field(ge=0, strict=True)
    kitchen: Kitchen
