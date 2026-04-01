import httpx

from app.core.config import Settings
from app.schemas.inference import InferenceResponse, Usage
from app.services.context import RequestContext

MAMAVNAV_SYSTEM_PROMPT = (
    "You are MamaNav AI, a compassionate and knowledgeable pregnancy and parenting companion. "
    "Provide empathetic, clinically-aware guidance on topics like pregnancy, newborn care, "
    "breastfeeding, postpartum recovery, child development, and local resources. "
    "Always recommend consulting a qualified healthcare provider for medical decisions. "
    "Keep responses concise, warm, and supportive. Use emojis sparingly. 💛"
)


class GeminiProvider:
    name = "gemini"
    # Gemini exposes an OpenAI-compatible endpoint
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def infer(self, context: RequestContext) -> InferenceResponse:
        if not self.settings.gemini_api_key:
            raise RuntimeError(
                "gemini provider is configured without GEMINI_API_KEY — "
                "set it in .env and restart the server"
            )

        messages = [{"role": "system", "content": MAMAVNAV_SYSTEM_PROMPT}]
        messages += [m.model_dump() for m in context.payload.messages]

        async with httpx.AsyncClient(base_url=self.BASE_URL, timeout=30.0) as client:
            response = await client.post(
                "chat/completions",
                headers={"Authorization": f"Bearer {self.settings.gemini_api_key}"},
                json={
                    "model": context.payload.model,
                    "messages": messages,
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
