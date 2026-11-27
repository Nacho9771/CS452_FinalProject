"""Read-only connection checks; never prints credentials or writes user records."""

import os

import firebase_admin
from firebase_admin import credentials

from cs_452_finalproject.configuration import load_environment
from cs_452_finalproject.services import FirebaseIdentity, MongoAccounts


def main():
    load_environment()
    success = True
    app = None
    database = MongoAccounts()
    try:
        if not os.getenv("FIREBASE_PROJECT_ID"):
            print("Firebase: project ID missing")
            success = False
        elif os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
            print("Firebase: emulator configuration is not accepted by this backend")
            success = False
        else:
            try:
                credential = credentials.ApplicationDefault()
                app = firebase_admin.initialize_app(
                    credential,
                    {"projectId": os.environ["FIREBASE_PROJECT_ID"]},
                    name="my-kitchen-connection-check",
                )
                credential.get_access_token()
                print("Firebase: Admin credentials accepted (not a user sign-in test)")
            except Exception as error:  # noqa: BLE001 -- CLI reports safe type, not secret-bearing details
                print(f"Firebase: unavailable ({type(error).__name__})")
                success = False
        try:
            collection = database.collection()
            collection.database.command("ping")
            print("MongoDB: ping succeeded (no records written)")
        except Exception as error:  # noqa: BLE001 -- do not expose a URI/password in error text
            print(f"MongoDB: unavailable ({type(error).__name__})")
            success = False
        token = os.getenv("FIREBASE_ID_TOKEN")
        if token:
            identity = FirebaseIdentity()
            try:
                identity.verify(token)
                print("Firebase: Google user ID token verified, including revocation check")
            except Exception as error:  # noqa: BLE001
                print(f"Firebase user token: unavailable ({type(error).__name__})")
                success = False
            finally:
                identity.close()
        else:
            print("Firebase user sign-in: not tested (no FIREBASE_ID_TOKEN)")
    finally:
        database.close()
        if app is not None:
            firebase_admin.delete_app(app)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
