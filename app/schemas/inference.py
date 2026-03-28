from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class InferenceRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = 0.0
    max_tokens: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    plugin_set: list[str] = Field(default_factory=list)
    provider_hint: str | None = None
    stream: bool = False


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class InferenceResponse(BaseModel):
    request_id: str
    tenant_id: str
    provider: str
    model: str
    output_text: str
    cached: bool = False
    usage: Usage = Field(default_factory=Usage)
    stage_trace: list[str] = Field(default_factory=list)
    audit_reference: str | None = None


class ErrorResponse(BaseModel):
    detail: str
