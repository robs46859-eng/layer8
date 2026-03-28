import httpx

from app.core.config import Settings
from app.providers.base import EchoProvider
from app.schemas.inference import InferenceResponse, Usage
from app.services.context import RequestContext


class MockProvider(EchoProvider):
    pass


class OpenAIChatProvider:
    name = "openai"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def infer(self, context: RequestContext) -> InferenceResponse:
        if not self.settings.openai_api_key:
            raise RuntimeError("openai provider is configured without OPENAI_API_KEY")

        async with httpx.AsyncClient(base_url=self.settings.openai_base_url, timeout=30.0) as client:
            response = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json={
                    "model": context.payload.model,
                    "messages": [message.model_dump() for message in context.payload.messages],
                    "temperature": context.payload.temperature,
                    "max_tokens": context.payload.max_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
        choice = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return InferenceResponse(
            request_id=context.request_id,
            tenant_id=context.tenant_id or "unknown",
            provider=self.name,
            model=context.payload.model,
            output_text=choice,
            usage=Usage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            ),
        )
