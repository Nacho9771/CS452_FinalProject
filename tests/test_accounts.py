"""HTTP security tests plus Mongo query-contract tests; no live cloud credentials."""

from copy import deepcopy
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from firebase_admin import auth
from pymongo.errors import AutoReconnect, DuplicateKeyError

from cs_452_finalproject.accounts import Account, Kitchen, Profile
from cs_452_finalproject.api import create_app
from cs_452_finalproject.services import FirebaseIdentity, MongoAccounts


def document(uid="alice"):
    now = datetime.now(UTC)
    return {
        "_id": uid,
        "revision": 0,
        "created_at": now,
        "updated_at": now,
        "profile": Profile().model_dump(),
        "kitchen": Kitchen().model_dump(),
    }


class TestIdentity:
    __test__ = False

    def verify(self, token):
        if token not in ("alice", "bob"):
            raise HTTPException(401, "Invalid test token")
        return token

    def close(self):
        pass


class MemoryAccounts:
    """Test double only: production code never falls back to memory storage."""

    def __init__(self):
        self.records = {}

    def create(self, uid):
        if uid not in self.records:
            self.records[uid] = MongoAccounts.decode(document(uid))
        return self.read(uid)

    def read(self, uid):
        if uid not in self.records:
            raise HTTPException(404, "Account not found")
        return self.records[uid].model_copy(deep=True)

    def update(self, uid, revision, section, value):
        record = self.read(uid)
        if revision != record.revision:
            raise HTTPException(409, "Stale revision")
        data = record.model_dump()
        data[section] = value
        data["revision"] += 1
        self.records[uid] = Account.model_validate(data)
        return self.read(uid)

    def close(self):
        pass


@pytest.fixture
def client():
    with TestClient(create_app(identity=TestIdentity(), accounts=MemoryAccounts())) as result:
        yield result


def headers(uid="alice"):
    return {"Authorization": f"Bearer {uid}"}


def test_account_creation_is_idempotent_and_users_are_isolated(client):
    assert client.get("/api/v1/account").status_code == 401
    assert client.get("/api/v1/account", headers=headers("bad")).status_code == 401
    assert client.get("/api/v1/account", headers=headers()).status_code == 404
    original = client.post("/api/v1/account", headers=headers()).json()
    updated = client.put(
        "/api/v1/account/profile",
        headers=headers(),
        json={"expected_revision": 0, "profile": {"first_name": "Alice", "household_size": 4}},
    )
    assert updated.status_code == 200
    assert updated.json()["revision"] == 1
    assert client.post("/api/v1/account", headers=headers()).json() == updated.json()
    bob = client.post("/api/v1/account", headers=headers("bob")).json()
    assert bob["uid"] == "bob"
    assert bob["profile"]["first_name"] == ""
    assert original["uid"] == "alice"
    # A query string cannot select another account, and a path ID isn't a route.
    assert client.get("/api/v1/account?uid=alice", headers=headers("bob")).json() == bob
    assert client.get("/api/v1/account/alice", headers=headers("bob")).status_code == 404


def test_stale_device_cannot_overwrite_kitchen_and_unknown_is_distinct(client):
    client.post("/api/v1/account", headers=headers())
    body = {
        "expected_revision": 0,
        "kitchen": {
            "appliances": {"skillet": True, "oven": False},
            "spices": ["ginger"],
            "spice_setup": "provided",
        },
    }
    first = client.put("/api/v1/account/kitchen", headers=headers(), json=body)
    assert first.status_code == 200
    stale = deepcopy(body)
    stale["kitchen"]["spices"] = ["pepper"]
    assert client.put("/api/v1/account/kitchen", headers=headers(), json=stale).status_code == 409
    saved = client.get("/api/v1/account", headers=headers()).json()
    assert saved["kitchen"]["spices"] == ["ginger"]
    assert saved["kitchen"]["appliances"]["oven"] is False
    assert "blender" not in saved["kitchen"]["appliances"]
    assert saved["profile"]["household_size"] == 1


@pytest.mark.parametrize(
    "profile",
    [
        {"uid": "someone-else"},
        {"household_size": 0},
        {"household_size": True},
        {
            "stores": [
                {"provider": "example", "location_id": str(i), "name": "Store"} for i in range(4)
            ]
        },
    ],
)
def test_invalid_profiles_cannot_be_saved(client, profile):
    client.post("/api/v1/account", headers=headers())
    assert (
        client.put(
            "/api/v1/account/profile",
            headers=headers(),
            json={"expected_revision": 0, "profile": profile},
        ).status_code
        == 422
    )


def test_missing_services_fail_closed(monkeypatch):
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
    monkeypatch.delenv("MONGODB_URI", raising=False)
    with TestClient(create_app()) as client:
        assert client.post("/api/v1/account").status_code == 401
        assert client.post("/api/v1/account", headers=headers()).status_code == 503
        assert client.get("/health").status_code == 200


def test_firebase_verification_checks_revocation_and_google_provider(monkeypatch):
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "test-project")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    identity = FirebaseIdentity()
    identity.app = object()  # Avoid creating any real Firebase app in this unit test.
    verify = MagicMock(
        return_value={"uid": "alice", "firebase": {"sign_in_provider": "google.com"}}
    )
    monkeypatch.setattr(auth, "verify_id_token", verify)
    assert identity.verify("signed-token") == "alice"
    verify.assert_called_once_with("signed-token", app=identity.app, check_revoked=True)
    verify.return_value["firebase"]["sign_in_provider"] = "password"
    with pytest.raises(HTTPException) as denied:
        identity.verify("signed-token")
    assert denied.value.status_code == 403
    verify.side_effect = auth.InvalidIdTokenError("Invalid token")
    with pytest.raises(HTTPException) as invalid:
        identity.verify("bad-token")
    assert invalid.value.status_code == 401
    verify.side_effect = ConnectionError("Do not expose connection details")
    with pytest.raises(HTTPException) as unavailable:
        identity.verify("signed-token")
    assert unavailable.value.status_code == 503
    assert "connection details" not in unavailable.value.detail


def test_mongo_update_filter_enforces_ownership_and_revision():
    repository = MongoAccounts()
    collection = MagicMock()
    repository.collection = MagicMock(return_value=collection)
    saved = document()
    saved["revision"] = 3
    collection.find_one_and_update.return_value = saved
    assert repository.update("alice", 2, "kitchen", Kitchen().model_dump()).revision == 3
    args, kwargs = collection.find_one_and_update.call_args
    assert args[0] == {"_id": "alice", "revision": 2}
    assert args[1]["$inc"] == {"revision": 1}
    assert "kitchen" in args[1]["$set"]
    assert "upsert" not in kwargs
    collection.find_one_and_update.return_value = None
    collection.find_one.return_value = {"_id": "alice"}
    with pytest.raises(HTTPException) as stale:
        repository.update("alice", 2, "kitchen", {})
    assert stale.value.status_code == 409
    collection.find_one.return_value = None
    with pytest.raises(HTTPException) as missing:
        repository.update("alice", 2, "kitchen", {})
    assert missing.value.status_code == 404


def test_mongo_creation_race_and_storage_outage_are_handled():
    repository = MongoAccounts()
    collection = MagicMock()
    repository.collection = MagicMock(return_value=collection)
    collection.find_one_and_update.side_effect = DuplicateKeyError("Concurrent signup")
    collection.find_one.return_value = document()
    assert repository.create("alice").uid == "alice"
    collection.find_one.side_effect = AutoReconnect("private host details")
    with pytest.raises(HTTPException) as failure:
        repository.read("alice")
    assert failure.value.status_code == 503
    assert "private host" not in failure.value.detail
