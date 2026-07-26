"""
Advisory AI reasoning for PawsMemories' BO-4 Thermal Cascade.

Replaces the old MamaNav chat pipeline for these three calls. This is a
separate code path from InferencePipeline/InferenceRequest on purpose --
observe/verify need multi-image vision input and strict structured JSON
output, neither of which the chat-completions pipeline models. Deterministic
math, geometry, and final authority stay on PawsMemories' side; Layer8 only
ever proposes.
"""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.schemas.spatial import (
    ImageRef,
    ScaleAnchor,
    SpatialObserveOutput,
    SpatialObserveOutputDraft,
    SpatialPlanOutput,
    SpatialPlanOutputDraft,
    SpatialVerifyOutput,
    SpatialVerifyOutputDraft,
    sha256_hex_of,
)

logger = logging.getLogger(__name__)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.0-flash"
MAX_SCHEMA_REPAIR_ATTEMPTS = 1  # one repair retry, matching PawsMemories' own retry budget


class SpatialReasoningError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


OBSERVE_SYSTEM_PROMPT = (
    "You are the observation stage of a deterministic 3D manufacturing cascade. "
    "You are given 1-4 reference photographs of a physical object (an accessory or "
    "hard-surface item for a pet, e.g. a collar, tag, or attachment part). "
    "Identify the subject class, a short factual summary, distinguishable geometric "
    "features with normalized bounding boxes (0-1 range, relative to image frame), "
    "and any occluded regions you cannot assess. Do not invent dimensions -- report "
    "scale uncertainty honestly. Respond with ONLY a single JSON object matching the "
    "provided schema. No prose, no markdown fences."
)

PLAN_SYSTEM_PROMPT = (
    "You are the planning stage of a deterministic 3D manufacturing cascade. Given an "
    "observation report and a target envelope size in millimeters, propose a set of "
    "normalized geometric primitives (box, cylinder, uv_sphere, cone, torus, capsule) "
    "with additive/subtractive roles that approximate the observed subject. Positions "
    "and sizes are normalized to the target envelope (position range -0.5..0.5, size "
    "range 0..1). All primitives must respect the given minimum wall thickness. You are "
    "proposing a plan for a downstream deterministic math solver to resolve into exact "
    "millimeter dimensions -- your numbers are a starting point, not final geometry. "
    "Respond with ONLY a single JSON object matching the provided schema. No prose, no "
    "markdown fences."
)

VERIFY_SYSTEM_PROMPT = (
    "You are the verification stage of a deterministic 3D manufacturing cascade. You are "
    "given the original observation and 1-5 rendered views of a draft 3D model built from "
    "that observation. Score how well the draft matches the observed subject on four axes "
    "(silhouette, proportion, featurePresence, viewConsistency, each 0-1) and list any "
    "critical issues per view with a confidence and short detail. Be conservative: only set "
    "automatedPass=true if there are no critical issues and all four scores are reasonably "
    "high. Respond with ONLY a single JSON object matching the provided schema. No prose, no "
    "markdown fences."
)

T = TypeVar("T", bound=BaseModel)


def _image_content_parts(images: list[ImageRef]) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    for img in images:
        parts.append({"type": "image_url", "image_url": {"url": img.url}})
    return parts


async def _call_gemini_json(
    settings: Settings,
    system_prompt: str,
    user_text: str,
    images: list[ImageRef],
    schema: type[T],
) -> T:
    if not settings.gemini_api_key:
        raise SpatialReasoningError(
            "NOT_CONFIGURED",
            "gemini provider is configured without GEMINI_API_KEY -- set it in .env",
        )

    user_content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    user_content.extend(_image_content_parts(images))

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    last_error: str | None = None
    async with httpx.AsyncClient(base_url=GEMINI_BASE_URL, timeout=60.0) as client:
        for attempt in range(MAX_SCHEMA_REPAIR_ATTEMPTS + 1):
            request_messages = list(messages)
            if last_error is not None:
                request_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response failed schema validation with this "
                            f"error: {last_error}\nRespond again with ONLY a corrected JSON "
                            "object matching the schema."
                        ),
                    }
                )

            response = await client.post(
                "chat/completions",
                headers={"Authorization": f"Bearer {settings.gemini_api_key}"},
                json={
                    "model": GEMINI_MODEL,
                    "messages": request_messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "stream": False,
                },
            )
            if response.status_code >= 500:
                raise SpatialReasoningError(
                    "UPSTREAM_ERROR", f"Gemini upstream error: {response.status_code}"
                )
            response.raise_for_status()
            data = response.json()
            raw_text = data["choices"][0]["message"]["content"]

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                last_error = f"response was not valid JSON: {exc}"
                logger.warning({"event": "spatial_schema_repair", "reason": "invalid_json", "attempt": attempt})
                continue

            try:
                return schema.model_validate(parsed)
            except ValidationError as exc:
                last_error = str(exc)
                logger.warning(
                    {"event": "spatial_schema_repair", "reason": "validation_error", "attempt": attempt}
                )
                continue

    raise SpatialReasoningError(
        "INVALID_MODEL_OUTPUT",
        f"Gemini output failed schema validation after {MAX_SCHEMA_REPAIR_ATTEMPTS + 1} attempt(s): {last_error}",
    )


async def run_observe(
    settings: Settings,
    reference_images: list[ImageRef],
    scale_anchor: ScaleAnchor | None,
) -> SpatialObserveOutput:
    if not reference_images:
        raise SpatialReasoningError(
            "NO_REFERENCE_IMAGES", "observe requires at least one reference image"
        )

    anchor_text = (
        f"A scale anchor is provided: {scale_anchor.millimeters}mm along the "
        f"{scale_anchor.axis} axis, labeled '{scale_anchor.label}'."
        if scale_anchor
        else "No scale anchor was provided -- report scaleEvidence.hasAnchor=false and a "
        "correspondingly higher uncertainty."
    )
    user_text = (
        f"{len(reference_images)} reference image(s) follow. {anchor_text} "
        "Set viewCount and viewLabels to match the number and order of images provided."
    )

    draft = await _call_gemini_json(
        settings, OBSERVE_SYSTEM_PROMPT, user_text, reference_images, SpatialObserveOutputDraft
    )
    payload = draft.model_dump()
    observation_hash = sha256_hex_of(payload)
    return SpatialObserveOutput(**payload, observationHash=observation_hash)


async def run_plan(
    settings: Settings,
    observation: SpatialObserveOutput,
    user_prompt: str,
    target_envelope_mm: dict[str, float],
    scale_anchor: ScaleAnchor | None,
    attachment_interface: dict[str, Any] | None,
) -> SpatialPlanOutput:
    user_text = (
        "Observation report:\n"
        f"{observation.model_dump_json()}\n\n"
        f"User prompt: {user_prompt}\n"
        f"Target envelope (mm): {json.dumps(target_envelope_mm)}\n"
        f"Scale anchor: {scale_anchor.model_dump_json() if scale_anchor else 'none'}\n"
        f"Attachment interface: {json.dumps(attachment_interface) if attachment_interface else 'none'}\n"
        "Propose normalized primitives now."
    )

    draft = await _call_gemini_json(settings, PLAN_SYSTEM_PROMPT, user_text, [], SpatialPlanOutputDraft)
    payload = draft.model_dump()
    plan_hash = sha256_hex_of(payload)
    return SpatialPlanOutput(**payload, planHash=plan_hash)


async def run_verify(
    settings: Settings,
    observation: SpatialObserveOutput,
    draft_images: list[ImageRef],
    attempt_hash: str,
) -> SpatialVerifyOutput:
    if not draft_images:
        raise SpatialReasoningError(
            "NO_DRAFT_IMAGES", "verify requires at least one draft render image"
        )

    user_text = (
        "Original observation report:\n"
        f"{observation.model_dump_json()}\n\n"
        f"{len(draft_images)} draft render view(s) follow. attemptHash={attempt_hash}. "
        "Score the match between the draft renders and the observed subject."
    )

    draft = await _call_gemini_json(
        settings, VERIFY_SYSTEM_PROMPT, user_text, draft_images, SpatialVerifyOutputDraft
    )
    payload = draft.model_dump()
    report_hash = sha256_hex_of(payload)
    return SpatialVerifyOutput(**payload, reportHash=report_hash)
