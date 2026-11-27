import pytest

from cs_452_finalproject.services import mongo_connection_options


@pytest.fixture(autouse=True)
def clean_credentials(monkeypatch):
    monkeypatch.delenv("MONGODB_USERNAME", raising=False)
    monkeypatch.delenv("MONGODB_PASSWORD", raising=False)


def test_separate_credentials_preserve_special_characters_and_uri_options(monkeypatch):
    monkeypatch.setenv("MONGODB_USERNAME", "test-user")
    monkeypatch.setenv("MONGODB_PASSWORD", "password@:/?#%+")
    options = mongo_connection_options(
        "mongodb+srv://<db_username>:<db_password>@example.invalid/?retryWrites=true&authSource=admin"
    )
    assert options == {
        "host": "mongodb+srv://example.invalid/?retryWrites=true&authSource=admin",
        "username": "test-user",
        "password": "password@:/?#%+",
    }


def test_complete_uri_still_works():
    uri = "mongodb+srv://test-user:encoded%40password@example.invalid/"
    assert mongo_connection_options(uri) == {"host": uri}


def test_partial_credentials_and_remaining_placeholders_fail_closed(monkeypatch):
    with pytest.raises(ValueError):
        mongo_connection_options("mongodb+srv://user:<db_password>@example.invalid/")
    monkeypatch.setenv("MONGODB_USERNAME", "test-user")
    with pytest.raises(ValueError):
        mongo_connection_options("mongodb+srv://example.invalid/")
    monkeypatch.setenv("MONGODB_PASSWORD", "test-password")
    with pytest.raises(ValueError):
        mongo_connection_options("mongodb+srv://<cluster-host>/")
