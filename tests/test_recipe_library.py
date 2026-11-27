"""Exercise production recipe repository/routes against a small Mongo collection test double."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pymongo.errors import AutoReconnect, DuplicateKeyError

from cs_452_finalproject.api import create_app
from cs_452_finalproject.recipe_library import MongoRecipes


class Identity:
    def verify(self, token):
        if token not in ("alice", "bob"):
            raise HTTPException(401, "Invalid test identity")
        return token

    def close(self):
        pass


class Cursor:
    def __init__(self, rows):
        self.rows = rows

    def sort(self, keys):
        for key, direction in reversed(keys):
            self.rows.sort(key=lambda row: row[key], reverse=direction == -1)
        return self

    def skip(self, offset):
        self.rows = self.rows[offset:]
        return self

    def limit(self, count):
        return self.rows[:count]


class Collection:
    """No production fallback: test only, with recorded filters for ownership checks."""

    def __init__(self):
        self.rows = {}
        self.queries = []

    def create_index(self, *args, **kwargs):
        pass

    def insert_one(self, row):
        if row["_id"] in self.rows:
            raise DuplicateKeyError("Duplicate test ID")
        self.rows[row["_id"]] = deepcopy(row)

    def find(self, query):
        self.queries.append(query)
        return Cursor(
            [
                deepcopy(row)
                for row in self.rows.values()
                if all(row.get(key) == value for key, value in query.items())
            ]
        )

    def find_one(self, query, projection=None):
        return next(iter(self.find(query).rows), None)

    def find_one_and_update(self, query, update, **kwargs):
        row = self.find_one(query)
        if row is None:
            return None
        row.update(update["$set"])
        row["revision"] += update["$inc"]["revision"]
        self.rows[row["_id"]] = deepcopy(row)
        return row


@pytest.fixture
def library():
    collection = Collection()
    accounts = MagicMock()
    accounts.collection.return_value = SimpleNamespace(database=SimpleNamespace(recipes=collection))
    repository = MongoRecipes(accounts)
    with TestClient(
        create_app(identity=Identity(), accounts=accounts, recipes=repository)
    ) as client:
        yield client, collection


@pytest.fixture
def body():
    return {
        "client_request_id": str(uuid4()),
        "recipe": {
            "title": "Original family rice",
            "servings": 2,
            "ingredients": [
                {
                    "name": "rice",
                    "original_text": "1 cup uncooked rice",
                    "quantity": "1.25",
                    "unit": "cup",
                },
                {"name": "salt", "original_text": "Salt to taste"},
            ],
            "steps": ["Keep this original instruction."],
            "prep_minutes": 5,
            "cook_minutes": 20,
            "source_url": "https://example.com/original-recipe",
            "estimated_cost": "3.50",
        },
    }


def auth(uid="alice"):
    return {"Authorization": f"Bearer {uid}"}


def test_create_retry_list_and_persistence_across_app_instances(library, body):
    client, collection = library
    first = client.post("/api/v1/recipes", headers=auth(), json=body)
    assert first.status_code == 201
    saved = first.json()
    assert saved["recipe"]["visibility"] == "private"
    assert saved["recipe"]["ingredients"][0]["quantity"] == "1.25"
    assert saved["recipe"]["steps"] == body["recipe"]["steps"]
    assert "owner_uid" not in saved and "creation_hash" not in saved
    assert client.post("/api/v1/recipes", headers=auth(), json=body).json() == saved
    assert len(collection.rows) == 1
    # A new API/repository instance still reads the collection, not route-local memory.
    accounts = MagicMock()
    accounts.collection.return_value = SimpleNamespace(database=SimpleNamespace(recipes=collection))
    with TestClient(create_app(identity=Identity(), accounts=accounts)) as restarted:
        assert restarted.get(f"/api/v1/recipes/{saved['id']}", headers=auth()).json() == saved
    assert client.get("/api/v1/recipes", headers=auth()).json()["items"] == [saved]


def test_other_users_cannot_read_edit_list_or_export_recipe(library, body):
    client, collection = library
    saved = client.post("/api/v1/recipes", headers=auth(), json=body).json()
    path = f"/api/v1/recipes/{saved['id']}"
    assert client.get(path, headers=auth("bob")).status_code == 404
    assert client.get(path + "/schema", headers=auth("bob")).status_code == 404
    assert (
        client.put(
            path, headers=auth("bob"), json={"expected_revision": 0, "recipe": body["recipe"]}
        ).status_code
        == 404
    )
    assert client.get("/api/v1/recipes", headers=auth("bob")).json()["items"] == []
    assert all("owner_uid" in query for query in collection.queries)


def test_conflicting_edits_and_reused_creation_ids_do_not_overwrite(library, body):
    client, _ = library
    saved = client.post("/api/v1/recipes", headers=auth(), json=body).json()
    path = f"/api/v1/recipes/{saved['id']}"
    changed = deepcopy(body)
    changed["recipe"]["title"] = "Edited family rice"
    assert client.post("/api/v1/recipes", headers=auth(), json=changed).status_code == 409
    update = {"expected_revision": 0, "recipe": changed["recipe"]}
    response = client.put(path, headers=auth(), json=update)
    assert response.status_code == 200 and response.json()["revision"] == 1
    assert client.put(path, headers=auth(), json=update).status_code == 409
    assert client.get(path, headers=auth()).json()["recipe"]["title"] == "Edited family rice"


def test_jsonld_export_preserves_original_text_and_excludes_private_metadata(library, body):
    client, _ = library
    saved = client.post("/api/v1/recipes", headers=auth(), json=body).json()
    response = client.get(f"/api/v1/recipes/{saved['id']}/schema", headers=auth())
    data = response.json()
    assert data["@type"] == "Recipe"
    assert data["recipeIngredient"] == [
        item["original_text"] for item in body["recipe"]["ingredients"]
    ]
    assert data["recipeInstructions"][0]["text"] == body["recipe"]["steps"][0]
    assert data["prepTime"] == "PT5M"
    assert data["estimatedCost"]["value"] == "3.50"
    assert "alice" not in response.text and "creation_hash" not in response.text


def test_pagination_is_bounded_and_does_not_mix_owners(library, body):
    client, _ = library
    for _ in range(3):
        body["client_request_id"] = str(uuid4())
        client.post("/api/v1/recipes", headers=auth(), json=body)
    page = client.get("/api/v1/recipes?limit=2", headers=auth()).json()
    assert len(page["items"]) == 2 and page["next_offset"] == 2
    next_page = client.get("/api/v1/recipes?limit=2&offset=2", headers=auth()).json()
    assert len(next_page["items"]) == 1 and next_page["next_offset"] is None
    for query in ("limit=0", "limit=51", "offset=-1"):
        assert client.get("/api/v1/recipes?" + query, headers=auth()).status_code == 422


def test_invalid_publication_ownership_and_urls_are_rejected(library, body):
    client, _ = library
    for field, value in (
        ("visibility", "public"),
        ("owner_uid", "bob"),
        ("image_urls", ["javascript:alert(1)"]),
    ):
        invalid = deepcopy(body)
        invalid["recipe"][field] = value
        assert client.post("/api/v1/recipes", headers=auth(), json=invalid).status_code == 422
    assert client.post("/api/v1/recipes", json=body).status_code == 401
    assert client.get("/api/v1/recipes", headers=auth("invalid")).status_code == 401


def test_database_outage_does_not_expose_connection_details(library, body):
    client, _ = library
    repository = client.app.state.recipes
    repository.collection = MagicMock(side_effect=AutoReconnect("private-host:password"))
    response = client.post("/api/v1/recipes", headers=auth(), json=body)
    assert response.status_code == 503
    assert "private-host" not in response.text
