"""Real Firebase and MongoDB adapters, initialized only when an account route is used."""

import os
from datetime import UTC, datetime
from threading import Lock
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import firebase_admin
from fastapi import HTTPException
from firebase_admin import auth, credentials
from firebase_admin.exceptions import FirebaseError
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import DuplicateKeyError, PyMongoError
from requests.exceptions import RequestException

from .accounts import Account, Kitchen, Profile


class FirebaseIdentity:
    def __init__(self):
        self.app = None
        self.lock = Lock()

    def verify(self, token: str) -> str:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        if not project_id or os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
            raise HTTPException(503, "Firebase is not configured for verified sign-in.")
        with self.lock:
            if self.app is None:
                try:
                    self.app = firebase_admin.initialize_app(
                        credentials.ApplicationDefault(),
                        {"projectId": project_id, "httpTimeout": 10},
                        name=f"my-kitchen-{uuid4()}",
                    )
                except ValueError, OSError, DefaultCredentialsError:
                    raise HTTPException(503, "Firebase credentials are unavailable.") from None
        try:
            claims = auth.verify_id_token(token, app=self.app, check_revoked=True)
        except (
            auth.InvalidIdTokenError,
            auth.RevokedIdTokenError,
            auth.UserDisabledError,
            auth.UserNotFoundError,
            ValueError,
        ):
            raise HTTPException(
                401, "Sign in again with Google.", headers={"WWW-Authenticate": "Bearer"}
            ) from None
        except FirebaseError, GoogleAuthError, RequestException, OSError:
            # Transport/credential/certificate failures must not masquerade as bad passwords.
            raise HTTPException(503, "Firebase verification is temporarily unavailable.") from None
        if claims.get("firebase", {}).get("sign_in_provider") != "google.com":
            raise HTTPException(403, "Use Google sign-in for My Kitchen.")
        uid = claims.get("uid")
        if not isinstance(uid, str) or not uid:
            raise HTTPException(401, "Invalid sign-in identity.")
        return uid

    def close(self):
        if self.app is not None:
            firebase_admin.delete_app(self.app)
            self.app = None


class MongoAccounts:
    def __init__(self):
        self.client = None
        self.lock = Lock()

    def collection(self):
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise HTTPException(503, "MongoDB is not configured.")
        with self.lock:
            if self.client is None:
                try:
                    self.client = MongoClient(
                        **mongo_connection_options(uri),
                        appname="my-kitchen-api",
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=5000,
                        tz_aware=True,
                    )
                except PyMongoError, ValueError:
                    raise HTTPException(503, "MongoDB configuration is invalid.") from None
        return self.client[os.getenv("MONGODB_DATABASE", "my_kitchen")].accounts

    @staticmethod
    def decode(document):
        if document is None:
            raise HTTPException(404, "Create your account first with POST /api/v1/account.")
        data = dict(document)
        data["uid"] = data.pop("_id")
        return Account.model_validate(data)

    def read(self, uid: str) -> Account:
        try:
            return self.decode(self.collection().find_one({"_id": uid}))
        except PyMongoError:
            raise HTTPException(503, "Account storage is temporarily unavailable.") from None

    def create(self, uid: str) -> Account:
        now = datetime.now(UTC)
        document = {
            "_id": uid,
            "revision": 0,
            "created_at": now,
            "updated_at": now,
            "profile": Profile().model_dump(),
            "kitchen": Kitchen().model_dump(),
        }
        try:
            collection = self.collection()
            try:
                result = collection.find_one_and_update(
                    {"_id": uid},
                    {"$setOnInsert": document},
                    upsert=True,
                    return_document=ReturnDocument.AFTER,
                )
            except DuplicateKeyError:
                # Another device may have created the same UID concurrently.
                result = collection.find_one({"_id": uid})
            return self.decode(result)
        except PyMongoError:
            raise HTTPException(503, "Account storage is temporarily unavailable.") from None

    def update(self, uid: str, revision: int, section: str, value: dict) -> Account:
        if section not in ("profile", "kitchen"):
            raise ValueError("Unknown account section")
        try:
            collection = self.collection()
            result = collection.find_one_and_update(
                {"_id": uid, "revision": revision},
                {
                    "$set": {section: value, "updated_at": datetime.now(UTC)},
                    "$inc": {"revision": 1},
                },
                return_document=ReturnDocument.AFTER,
            )
            if result is None:
                if collection.find_one({"_id": uid}, {"_id": 1}) is None:
                    raise HTTPException(404, "Account not found.")
                raise HTTPException(409, "Account changed on another device. Reload before saving.")
            return self.decode(result)
        except PyMongoError:
            raise HTTPException(503, "Account storage is temporarily unavailable.") from None

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None


def mongo_connection_options(uri: str) -> dict:
    """Support either a complete URI or separate credentials, without URI escaping.

    PyMongo accepts username/password arguments directly. Removing the URI's
    placeholder user-info keeps credentials out of the connection string.
    """
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    if username is not None or password is not None:
        if not username or not password:
            raise ValueError("Both MongoDB credential settings are required")
        parts = urlsplit(uri)
        if parts.scheme not in ("mongodb", "mongodb+srv"):
            raise ValueError("Unsupported MongoDB URI scheme")
        uri = urlunsplit(parts._replace(netloc=parts.netloc.rsplit("@", 1)[-1]))
        options = {"host": uri, "username": username, "password": password}
    else:
        options = {"host": uri}
    if "<" in uri or ">" in uri:
        raise ValueError("MongoDB URI still contains placeholders")
    return options
