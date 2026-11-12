from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_validation_error_uses_unified_shape() -> None:
    # /weather/current requires q; omit it to force a 422 from FastAPI
    r = client.get("/api/v1/weather/current")
    assert r.status_code == 422
    body = r.json()
    assert set(body["error"]) == {"code", "message", "details"}
    assert body["error"]["code"] == "VALIDATION_FAILED"


def test_404_uses_unified_shape() -> None:
    r = client.get("/api/v1/no-such-route")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "NOT_FOUND"
