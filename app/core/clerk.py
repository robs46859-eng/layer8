"""Organization claims from an already verified Clerk session token."""

from collections.abc import Mapping


def clerk_organization_id(claims: Mapping[str, object]) -> str | None:
    """Read v2 ``o.id`` or legacy ``org_id`` after JWT verification.

    A malformed or conflicting claim must never fall back to the other format.
    This function does not verify a token or grant organization membership.
    """
    organization_ids: list[str] = []
    if "o" in claims:
        organization = claims["o"]
        if not isinstance(organization, dict) or "id" not in organization:
            raise ValueError("invalid Clerk organization claim")
        organization_ids.append(_organization_id(organization["id"]))
    if "org_id" in claims:
        organization_ids.append(_organization_id(claims["org_id"]))
    if len(set(organization_ids)) > 1:
        raise ValueError("conflicting Clerk organization claims")
    return organization_ids[0] if organization_ids else None


def _organization_id(value: object) -> str:
    if (not isinstance(value, str) or not 0 < len(value) <= 64
            or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError("invalid Clerk organization ID")
    return value
