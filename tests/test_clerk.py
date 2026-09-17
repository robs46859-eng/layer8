import pytest

from app.core.clerk import clerk_organization_id


@pytest.mark.parametrize("claims", [
    {"org_id": "org_alpha"},
    {"v": 2, "o": {"id": "org_alpha", "rol": "member"}},
    {"o": {"id": "org_alpha"}, "org_id": "org_alpha"},
])
def test_organization_formats_resolve_the_same_identity(claims):
    assert clerk_organization_id(claims) == "org_alpha"


def test_absent_organization_does_not_invent_identity():
    assert clerk_organization_id({"sub": "user_alpha", "v": 2}) is None


@pytest.mark.parametrize("value", [None, False, 12, [], {}, "", " org_alpha", "org alpha",
                                        "org_alpha\n", "org_\x00alpha", "org_\x7falpha", "x" * 65])
@pytest.mark.parametrize("shape", ["legacy", "v2"])
def test_invalid_organization_ids_fail_closed(value, shape):
    claims = {"org_id": value} if shape == "legacy" else {"v": 2, "o": {"id": value}}
    with pytest.raises(ValueError):
        clerk_organization_id(claims)


@pytest.mark.parametrize("claims", [
    {"o": None}, {"o": "org_alpha"}, {"o": []}, {"o": {}},
    {"o": {"id": "org_beta"}, "org_id": "org_alpha"},
    {"o": {"id": "org_alpha"}, "org_id": None},
    {"o": {"id": None}, "org_id": "org_alpha"},
    {"o": {}, "org_id": "org_alpha"},
])
def test_malformed_or_conflicting_claims_never_fall_back(claims):
    with pytest.raises(ValueError):
        clerk_organization_id(claims)
