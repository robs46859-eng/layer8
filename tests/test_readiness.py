from fastapi.testclient import TestClient

from app.main import app


class StubReadinessService:
    def __init__(self, result):
        self.result = result

    def check(self):
        return self.result


def test_readyz_ok(monkeypatch):
    from app.api import routes

    monkeypatch.setattr(
        routes,
        "readiness_service",
        StubReadinessService(
            {
                "status": "ok",
                "backend_mode": "memory",
                "checks": {"app": {"status": "ok"}},
            }
        ),
    )
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz_returns_503_on_failed_check(monkeypatch):
    from app.api import routes

    monkeypatch.setattr(
        routes,
        "readiness_service",
        StubReadinessService(
            {
                "status": "error",
                "backend_mode": "self_hosted",
                "checks": {"postgres": {"status": "error", "detail": "dial tcp failed"}},
            }
        ),
    )
    client = TestClient(app)
    response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "error"
