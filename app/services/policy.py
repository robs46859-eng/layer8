from app.services.context import RequestContext


class PolicyService:
    async def evaluate(self, context: RequestContext) -> None:
        if "inference:invoke" not in context.api_key_scopes:
            raise PermissionError("missing scope inference:invoke")
        if context.payload.model not in context.allowed_models:
            raise PermissionError("requested model is not allowed")
        context.policy_snapshot = {
            "tenant_id": context.tenant_id,
            "allowed_models": sorted(context.allowed_models),
            "plugin_allowlist": list(context.payload.plugin_set),
        }
