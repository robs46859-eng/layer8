from types import SimpleNamespace

import pytest

from app.services.startup import run_startup_checks


class StubReadinessService:
    def __init__(self, result):
        self.result = result

    def check(self):
        return self.result


def test_run_startup_checks_returns_result():
    settings = SimpleNamespace(
        app_name="layer8",
        environment="test",
        backend_mode="memory",
        startup_checks_strict=False,
    )
    result = run_startup_checks(
        settings,
        StubReadinessService(
            {"status": "ok", "checks": {"app": {"status": "ok"}}, "backend_mode": "memory"}
        ),
    )
    assert result["status"] == "ok"


def test_run_startup_checks_raises_when_strict():
    settings = SimpleNamespace(
        app_name="layer8",
        environment="test",
        backend_mode="self_hosted",
        startup_checks_strict=True,
    )
    with pytest.raises(RuntimeError, match="startup dependency checks failed"):
        run_startup_checks(
            settings,
            StubReadinessService(
                {
                    "status": "error",
                    "checks": {"postgres": {"status": "error", "detail": "unreachable"}},
                    "backend_mode": "self_hosted",
                }
            ),
        )
