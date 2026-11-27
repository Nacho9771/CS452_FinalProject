from uuid import UUID

from fastapi.testclient import TestClient

from cs_452_finalproject.api import create_app


def test_requests_can_be_matched_to_logs_without_logging_inputs(caplog):
    with caplog.at_level("INFO", logger="uvicorn.error"), TestClient(create_app()) as client:
        response = client.get("/health?secret=private-value")
        request_id = response.headers["X-Request-ID"]
        assert str(UUID(request_id)) == request_id
        assert f"request_id={request_id}" in caplog.text
        assert "path=/health status=200" in caplog.text
        assert "private-value" not in caplog.text
        assert client.get("/health").headers["X-Request-ID"] != request_id


def test_validation_errors_and_missing_routes_also_have_request_ids():
    with TestClient(create_app()) as client:
        for response in (
            client.post("/api/v1/recipes/preview", json={}),
            client.get("/not-a-route"),
        ):
            assert response.status_code in (422, 404)
            assert response.headers["X-Request-ID"]
