from datetime import UTC, datetime


class BillingAccessError(PermissionError):
    """The tenant does not currently have billable execution access."""


class EntitlementAccessError(PermissionError):
    """The tenant's active plan does not include the requested capability."""


def has_billing_access(
    subscription_status: str,
    payment_grace_ends_at: datetime | None,
    *,
    now: datetime | None = None,
) -> bool:
    if subscription_status in {"active", "trialing"}:
        return True
    if subscription_status != "past_due" or payment_grace_ends_at is None:
        return False
    current = now or datetime.now(UTC).replace(tzinfo=None)
    if current.tzinfo is not None:
        current = current.astimezone(UTC).replace(tzinfo=None)
    grace_end = payment_grace_ends_at
    if grace_end.tzinfo is not None:
        grace_end = grace_end.astimezone(UTC).replace(tzinfo=None)
    return current <= grace_end


def enforce_entitlement(
    *,
    subscription_status: str,
    payment_grace_ends_at: datetime | None,
    entitlements: set[str],
    required_entitlement: str,
) -> None:
    if not has_billing_access(subscription_status, payment_grace_ends_at):
        raise BillingAccessError("an active subscription is required")
    if required_entitlement not in entitlements:
        raise EntitlementAccessError(
            f"the active plan does not include {required_entitlement}"
        )
