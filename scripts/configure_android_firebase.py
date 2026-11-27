"""Register/get the Android Firebase client and write only its public SDK config.

Requires the existing server Admin credential locally. Never copies that private
credential into the Android project. --sha1 registers a debug signing certificate.
"""

import argparse
import base64
import json
import os
import re
import time
from pathlib import Path

from firebase_admin import credentials
from google.auth.credentials import with_scopes_if_required
from google.auth.transport.requests import AuthorizedSession

from cs_452_finalproject.configuration import load_environment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sha1", help="Debug signing certificate SHA-1, with or without colons")
    args = parser.parse_args()
    fingerprint = re.sub(":", "", args.sha1).upper() if args.sha1 else None
    if fingerprint and not re.fullmatch(r"[0-9A-F]{40}", fingerprint):
        raise SystemExit("SHA-1 must contain exactly 40 hexadecimal characters.")
    load_environment()
    credential = with_scopes_if_required(
        credentials.ApplicationDefault().get_credential(),
        ["https://www.googleapis.com/auth/cloud-platform"],
    )
    session = AuthorizedSession(credential)
    base = "https://firebase.googleapis.com/v1beta1/"
    project = os.environ["FIREBASE_PROJECT_ID"]

    def request(method, resource, **kwargs):
        response = session.request(method, base + resource, timeout=30, **kwargs)
        if not response.ok:
            raise RuntimeError(f"Firebase Android setup returned HTTP {response.status_code}.")
        return response.json()

    listing = request("GET", f"projects/{project}/androidApps")
    app = next(
        (
            item
            for item in listing.get("apps", [])
            if item.get("packageName") == "com.mykitchen.app"
        ),
        None,
    )
    if app is None:
        operation = request(
            "POST",
            f"projects/{project}/androidApps",
            json={
                "displayName": "My Kitchen Android",
                "packageName": "com.mykitchen.app",
            },
        )
        for _ in range(30):
            if operation.get("done"):
                break
            time.sleep(1)
            operation = request("GET", operation["name"])
        if not operation.get("done") or operation.get("error"):
            raise RuntimeError("Android client registration did not complete.")
        app = operation["response"]
    if fingerprint:
        hashes = request("GET", app["name"] + "/sha").get("certificates", [])
        if not any(
            item.get("shaHash", "").replace(":", "").upper() == fingerprint for item in hashes
        ):
            request(
                "POST", app["name"] + "/sha", json={"shaHash": fingerprint, "certType": "SHA_1"}
            )
        print("Debug signing certificate registered.")
    result = request("GET", app["name"] + "/config")
    config = json.loads(base64.b64decode(result["configFileContents"]))
    destination = Path(__file__).resolve().parents[1] / "mobile" / "app" / "google-services.json"
    destination.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print("Android Firebase client registered; public google-services.json saved locally.")
    print(
        "Admin private credentials were not copied. Register debug SHA-1 before testing Google sign-in."
    )


if __name__ == "__main__":
    main()
