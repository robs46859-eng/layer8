"""Strict, versioned VirtuaPet contracts; no caller-selected identity or policy overrides."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

BoundedText = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=256)]


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LinkProofRequest(StrictContract):
    subject: UUID
    tenantId: UUID
    challengeId: UUID
    nonce: UUID


class LinkProofResponse(StrictContract):
    proofToken: str


class PolicyRequest(StrictContract):
    protocol: Literal["virtuapet.layer8.policy.v1"]
    requestId: UUID
    subject: UUID
    tenantId: UUID
    correlationId: UUID
    action: BoundedText
    resource: BoundedText
    purpose: BoundedText
    requiredEntitlements: list[BoundedText] = Field(max_length=32)
    identityProof: str = Field(strict=True, min_length=1, max_length=15000)

    @field_validator("action", "resource", "purpose")
    @classmethod
    def canonical_text(cls, value: str) -> str:
        if value != value.strip() or any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("noncanonical text")
        return value

    @field_validator("requiredEntitlements")
    @classmethod
    def canonical_entitlements(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError("duplicate entitlements")
        for value in values:
            cls.canonical_text(value)
        return values


class PolicyResponse(StrictContract):
    decisionToken: str
