import pytest
from fastapi.testclient import TestClient

from cs_452_finalproject.api import create_app

PATHS = ("/dev/sign-in", "/dev/sign-in.js", "/dev/sign-in.css", "/dev/firebase-config")


def local_client(**kwargs):
    return TestClient(
        create_app(), base_url="http://localhost", client=("127.0.0.1", 50000), **kwargs
    )


def test_dev_tools_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_DEV_SIGNIN", raising=False)
    with local_client() as client:
        for path in PATHS:
            assert client.get(path).status_code == 404


@pytest.mark.parametrize(
    "remote,host", [("203.0.113.10", "localhost"), ("127.0.0.1", "evil.example")]
)
def test_enabled_tools_still_require_loopback_client_and_host(monkeypatch, remote, host):
    monkeypatch.setenv("ENABLE_DEV_SIGNIN", "1")
    with TestClient(create_app(), base_url=f"http://{host}", client=(remote, 50000)) as client:
        for path in PATHS:
            assert client.get(path).status_code == 404


def test_public_config_is_allowlisted_and_assets_have_correct_types(monkeypatch):
    monkeypatch.setenv("ENABLE_DEV_SIGNIN", "1")
    for name, value in {
        "FIREBASE_WEB_API_KEY": "public-client-key",
        "FIREBASE_WEB_APP_ID": "public-client-id",
        "FIREBASE_PROJECT_ID": "test-project",
        "FIREBASE_AUTH_DOMAIN": "test-project.firebaseapp.com",
        "MONGODB_PASSWORD": "never-send-this",
        "GOOGLE_APPLICATION_CREDENTIALS": "C:/private/server-key.json",
    }.items():
        monkeypatch.setenv(name, value)
    with local_client() as client:
        response = client.get("/dev/firebase-config")
        assert response.status_code == 200
        assert set(response.json()) == {"apiKey", "appId", "projectId", "authDomain"}
        assert "never-send-this" not in response.text
        assert "server-key" not in response.text
        assert response.headers["cache-control"] == "no-store"
        assert "text/html" in client.get("/dev/sign-in").headers["content-type"]
        assert "text/javascript" in client.get("/dev/sign-in.js").headers["content-type"]
        assert "text/css" in client.get("/dev/sign-in.css").headers["content-type"]
        assert "/dev/sign-in" not in client.get("/openapi.json").json()["paths"]


def test_incomplete_config_gives_actionable_error(monkeypatch):
    monkeypatch.setenv("ENABLE_DEV_SIGNIN", "1")
    monkeypatch.delenv("FIREBASE_WEB_API_KEY", raising=False)
    with local_client() as client:
        assert client.get("/dev/firebase-config").status_code == 503
