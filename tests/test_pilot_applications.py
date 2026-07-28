import os
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base
from app.db.models import PilotApplication
from app.db.session import get_engine, get_session_factory
from app.main import create_app


def _reset_settings() -> None:
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


def _build_client(db_path: Path) -> TestClient:
    os.environ["BACKEND_MODE"] = "memory"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ADMIN_API_TOKEN"] = "test-admin-token"
    _reset_settings()
    engine = create_engine(
        f"sqlite:///{db_path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return TestClient(create_app())


def _application_payload(**overrides) -> dict:
    payload = {
        "contact_name": "Ada Lovelace",
        "work_email": "ADA@Example.com",
        "company": "Analytical Engines",
        "role": "Platform lead",
        "use_case": "Govern model failover for a production agent workflow.",
        "timeline": "30_days",
        "source": "website-pilot",
        "consent_to_contact": True,
        "website": "",
    }
    payload.update(overrides)
    return payload


def _admin_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-admin-token"}


def test_public_application_is_normalized_stored_and_admin_listed(tmp_path):
    db_path = tmp_path / "pilot.sqlite3"
    client = _build_client(db_path)

    response = client.post(
        "/v1/pilot-applications",
        json=_application_payload(
            contact_name="  Ada Lovelace  ",
            company="  Analytical Engines  ",
        ),
    )

    assert response.status_code == 202
    assert response.json() == {
        "accepted": True,
        "message": "Thanks. SALTI8 will review your pilot request.",
    }
    assert "ADA@Example.com" not in response.text

    listing = client.get(
        "/admin/pilot-applications?status=new&source=website-pilot",
        headers=_admin_headers(),
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    application = listing.json()[0]
    assert application["id"].startswith("pilot_")
    assert application["contact_name"] == "Ada Lovelace"
    assert application["work_email"] == "ada@example.com"
    assert application["company"] == "Analytical Engines"
    assert application["status"] == "new"
    assert application["consent_to_contact"] is True
    assert application["consented_at"]
    assert application["created_at"]
    assert application["updated_at"]

    with Session(create_engine(f"sqlite:///{db_path}", future=True)) as session:
        stored = session.scalar(select(PilotApplication))
        assert stored is not None
        assert stored.work_email == "ada@example.com"


def test_honeypot_submission_is_accepted_without_storage(tmp_path):
    client = _build_client(tmp_path / "honeypot.sqlite3")

    response = client.post(
        "/v1/pilot-applications",
        json=_application_payload(website="https://spam.example"),
    )

    assert response.status_code == 202
    listing = client.get(
        "/admin/pilot-applications",
        headers=_admin_headers(),
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_public_application_rejects_invalid_or_excessive_fields(tmp_path):
    client = _build_client(tmp_path / "validation.sqlite3")

    invalid_email = client.post(
        "/v1/pilot-applications",
        json=_application_payload(work_email="not-an-email"),
    )
    assert invalid_email.status_code == 422

    missing_consent = client.post(
        "/v1/pilot-applications",
        json=_application_payload(consent_to_contact=False),
    )
    assert missing_consent.status_code == 422

    short_use_case = client.post(
        "/v1/pilot-applications",
        json=_application_payload(use_case="Too short"),
    )
    assert short_use_case.status_code == 422

    oversized_company = client.post(
        "/v1/pilot-applications",
        json=_application_payload(company="x" * 161),
    )
    assert oversized_company.status_code == 422

    unexpected_data = client.post(
        "/v1/pilot-applications",
        json={**_application_payload(), "phone": "555-0100"},
    )
    assert unexpected_data.status_code == 422


def test_admin_listing_requires_auth_and_enforces_pagination(tmp_path):
    client = _build_client(tmp_path / "admin-list.sqlite3")
    for index in range(2):
        response = client.post(
            "/v1/pilot-applications",
            json=_application_payload(
                work_email=f"person{index}@example.com",
                source="homepage" if index == 0 else "website-pilot",
            ),
        )
        assert response.status_code == 202

    missing_auth = client.get("/admin/pilot-applications")
    assert missing_auth.status_code == 401

    wrong_auth = client.get(
        "/admin/pilot-applications",
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert wrong_auth.status_code == 403

    first_page = client.get(
        "/admin/pilot-applications?limit=1&offset=0",
        headers=_admin_headers(),
    )
    assert first_page.status_code == 200
    assert len(first_page.json()) == 1

    filtered = client.get(
        "/admin/pilot-applications?source=homepage",
        headers=_admin_headers(),
    )
    assert filtered.status_code == 200
    assert [item["source"] for item in filtered.json()] == ["homepage"]

    invalid_limit = client.get(
        "/admin/pilot-applications?limit=201",
        headers=_admin_headers(),
    )
    assert invalid_limit.status_code == 422
