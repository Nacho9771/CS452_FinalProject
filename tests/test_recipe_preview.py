from copy import deepcopy
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from cs_452_finalproject.api import create_app
from cs_452_finalproject.models import PreviewRequest
from cs_452_finalproject.recipes import preview_recipe


@pytest.fixture
def payload():
    return {
        "recipe": {
            "title": "Family recipe",
            "servings": 2,
            "ingredients": [
                {
                    "name": "flour",
                    "original_text": "1 cup sifted flour",
                    "quantity": "1",
                    "unit": "cup",
                },
                {"name": "salt", "original_text": "Salt to taste"},
            ],
            "steps": ["Keep this instruction exactly."],
            "prep_minutes": 10,
            "cook_minutes": 25,
        },
        "target_servings": 4,
    }


def test_scale_preserves_source_and_instructions(payload):
    request = PreviewRequest.model_validate(payload)
    original = request.model_dump()
    result = preview_recipe(request)
    assert result.ingredients[0].quantity == 2
    assert result.ingredients[0].original_text == "1 cup sifted flour"
    assert result.ingredients[1].quantity is None
    assert result.ingredients[1].warning
    assert result.steps == payload["recipe"]["steps"]
    assert (result.prep_minutes, result.cook_minutes) == (10, 25)
    assert request.model_dump() == original


@pytest.mark.parametrize(
    "source,target,quantity,density,expected,expected_unit",
    [
        ("cup", "tbsp", "1", None, "16", "tbsp"),
        ("kg", "g", "0.5", None, "500", "g"),
        ("cup", "g", "1", None, "1", "cup"),
        ("ml", "g", "100", "0.5", "50", "g"),
        ("g", "ml", "50", "0.5", "100", "ml"),
        ("count", "g", "2", "1", "2", "count"),
    ],
)
def test_unit_conversion_or_source_fallback(
    payload, source, target, quantity, density, expected, expected_unit
):
    payload["target_servings"] = 2
    ingredient = payload["recipe"]["ingredients"][0]
    ingredient.update(unit=source, quantity=quantity, density_g_per_ml=density)
    payload["target_units"] = {"0": target}
    result = preview_recipe(PreviewRequest.model_validate(payload)).ingredients[0]
    assert result.quantity == Decimal(expected)
    assert result.unit == expected_unit
    assert bool(result.warning) == (expected_unit != target)


def test_http_contract_and_health(payload):
    with TestClient(create_app()) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert set(health.json()["integrations"].values()) == {"not_connected"}
        response = client.post("/api/v1/recipes/preview", json=payload)
        assert response.status_code == 200
        assert response.json()["ingredients"][0]["quantity"] == "2"
        assert client.get("/openapi.json").status_code == 200


@pytest.mark.parametrize("invalid", [0, -1, 1.5, True, "4"])
def test_reject_invalid_servings(payload, invalid):
    payload["target_servings"] = invalid
    with TestClient(create_app()) as client:
        assert client.post("/api/v1/recipes/preview", json=payload).status_code == 422


def test_reject_unknown_fields_and_bad_conversion_index(payload):
    with TestClient(create_app()) as client:
        unknown = deepcopy(payload)
        unknown["recipe"]["servngs"] = 3
        assert client.post("/api/v1/recipes/preview", json=unknown).status_code == 422
        for index in (-1, 20):
            payload["target_units"] = {str(index): "g"}
            assert client.post("/api/v1/recipes/preview", json=payload).status_code == 422
