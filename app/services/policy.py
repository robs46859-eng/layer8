from app.services.context import RequestContext
from app.services.entitlements import enforce_entitlement


class PolicyService:
    async def evaluate(self, context: RequestContext) -> None:
        enforce_entitlement(
            subscription_status=context.billing_status,
            payment_grace_ends_at=context.payment_grace_ends_at,
            entitlements=context.billing_entitlements,
            required_entitlement="api_access",
        )
        if "inference:invoke" not in context.api_key_scopes:
            raise PermissionError("missing scope inference:invoke")
        if context.payload.model not in context.allowed_models:
            raise PermissionError("requested model is not allowed")
        context.policy_snapshot = {
            "tenant_id": context.tenant_id,
            "billing_status": context.billing_status,
            "billing_entitlements": sorted(context.billing_entitlements),
            "payment_grace_ends_at": (
                context.payment_grace_ends_at.isoformat()
                if context.payment_grace_ends_at
                else None
            ),
            "allowed_models": sorted(context.allowed_models),
            "plugin_allowlist": list(context.payload.plugin_set),
        }
