import asyncio
import logging

from app.plugins.base import AuditTagPlugin, PromptMetadataPlugin
from app.schemas.inference import InferenceResponse
from app.services.context import RequestContext

logger = logging.getLogger(__name__)


class PluginRuntime:
    def __init__(self, timeout_ms: int) -> None:
        self.timeout_seconds = timeout_ms / 1000
        self.before_plugins = {"prompt-metadata": PromptMetadataPlugin()}
        self.after_plugins = {"audit-tag": AuditTagPlugin()}

    async def run_before(self, context: RequestContext) -> RequestContext:
        context.stage_trace.append("plugins_before")
        for plugin_name in context.payload.plugin_set:
            plugin = self.before_plugins.get(plugin_name)
            if plugin is None:
                raise RuntimeError(f"unknown before plugin {plugin_name}")
            context.plugin_bindings.append(plugin.name)
            result = await self._run_with_timeout(plugin.run(context), plugin.blocking)
            if result is not None:
                context = result
        return context

    async def run_after(
        self, context: RequestContext, response: InferenceResponse
    ) -> InferenceResponse:
        context.stage_trace.append("plugins_after")
        for plugin_name, plugin in self.after_plugins.items():
            context.plugin_bindings.append(plugin_name)
            result = await self._run_with_timeout(plugin.run(context, response), plugin.blocking)
            if result is not None:
                response = result
        return response

    async def _run_with_timeout(self, coro, blocking: bool):
        try:
            return await asyncio.wait_for(coro, timeout=self.timeout_seconds)
        except Exception:
            if blocking:
                raise
            logger.exception("non-blocking plugin failed")
            return None
