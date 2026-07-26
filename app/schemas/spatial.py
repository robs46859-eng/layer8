"""
Pydantic models for the PawsMemories BO-4 Thermal Cascade spatial contract.

These models are a deliberate 1:1 mirror of the zod schemas in
PawsMemories' server/spatial-generator/schemas.ts (SpatialObserveOutputSchema,
SpatialPlanSchema / NormalizedPrimitiveSchema, SpatialVerifyOutputSchema).
Field names, nesting, and value constraints must stay in sync by hand --
there is no shared schema generator between the two repos. If PawsMemories'
schemas.ts changes, update this file to match in the same PR.

Layer8 is advisory only: it proposes observations/plans/verification scores,
never touches deterministic math or geometry. PawsMemories treats every
field here as untrusted model output and re-validates on receipt.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Axis = Literal["x", "y", "z"]


def sha256_hex_of(payload: dict) -> str:
    """Canonical-JSON sha256 hash, matching PawsMemories' own hash convention
    (see gent-scoring.ts computeReportHash: JSON.stringify + sha256 hex)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ScaleAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")
    axis: Axis
    millimeters: float = Field(gt=0)
    label: str = Field(min_length=1, max_length=64)


class EnvelopeMm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float = Field(gt=0, le=5000)
    y: float = Field(gt=0, le=5000)
    z: float = Field(gt=0, le=5000)


class AttachmentInterface(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targetAssetVersionId: int = Field(gt=0)
    clearanceMm: float = Field(ge=0, le=100)


class ImageRef(BaseModel):
    """Signed, short-lived URL for a reference or draft-render image.
    PawsMemories resolves asset version IDs to these before calling Layer8 --
    Layer8 has no MySQL/B2 credentials of its own."""

    model_config = ConfigDict(extra="forbid")
    versionId: int
    url: str


# --- Observe -----------------------------------------------------------

class SpatialObserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    referenceAssetVersionIds: list[int] = Field(default_factory=list)
    referenceImages: list[ImageRef] = Field(default_factory=list)
    scaleAnchor: ScaleAnchor | None = None


class ObserveFeatureBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")
    min: list[float] = Field(min_length=3, max_length=3)
    max: list[float] = Field(min_length=3, max_length=3)


class ObserveFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(max_length=128)
    confidence: float = Field(ge=0, le=1)
    normalizedBounds: ObserveFeatureBounds
    viewIndices: list[int] = Field(min_length=1, max_length=4)


class ScaleEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    hasAnchor: bool
    uncertainty: float = Field(ge=0, le=1)


class Occlusion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region: str = Field(max_length=128)
    description: str = Field(max_length=500)


class SpatialObserveOutput(BaseModel):
    """Mirrors SpatialObserveOutputSchema exactly."""

    model_config = ConfigDict(extra="forbid")
    subjectClass: str = Field(min_length=1, max_length=128)
    summary: str = Field(max_length=2000)
    viewCount: int = Field(ge=1, le=4)
    viewLabels: list[str] = Field(min_length=1, max_length=4)
    features: list[ObserveFeature] = Field(default_factory=list, max_length=50)
    scaleEvidence: ScaleEvidence
    occlusions: list[Occlusion] = Field(default_factory=list, max_length=20)
    observationHash: str = Field(pattern=r"^[a-f0-9]{64}$")


# --- Plan ----------------------------------------------------------------

class SpatialPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation: SpatialObserveOutput
    userPrompt: str = Field(min_length=3, max_length=2000)
    targetEnvelopeMm: EnvelopeMm
    scaleAnchor: ScaleAnchor | None = None
    attachmentInterface: AttachmentInterface | None = None


class Vec3(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: float
    y: float
    z: float


class Bevel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    width: float = Field(gt=0, le=100)
    segments: int = Field(gt=0, le=32)


class CurveSweep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controlPoints: list[list[float]] = Field(min_length=2, max_length=16)
    segments: int = Field(gt=0, le=128)


class PrimitiveArray(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: int = Field(gt=0, le=64)
    spacing: float = Field(gt=0, le=1000)
    axis: Axis


class PrimitiveConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minimumWallMm: float = Field(gt=0, le=100)
    clearanceMm: float | None = Field(default=None, ge=0, le=100)


class MaterialIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    roughness: float | None = Field(default=None, ge=0, le=1)
    metalness: float | None = Field(default=None, ge=0, le=1)


class NormalizedPrimitive(BaseModel):
    """Mirrors NormalizedPrimitiveSchema exactly."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=64)
    type: Literal["box", "cylinder", "uv_sphere", "cone", "torus", "capsule"]
    role: Literal["additive", "subtractive"]
    normalizedSize: Vec3
    normalizedPosition: Vec3
    rotationDeg: Vec3
    symmetryAxis: Axis | None = None
    bevel: Bevel | None = None
    curveSweep: CurveSweep | None = None
    array: PrimitiveArray | None = None
    constraints: PrimitiveConstraints
    materialIntent: MaterialIntent | None = None


class SpatialPlanOutput(BaseModel):
    """Mirrors SpatialPlanSchema exactly."""

    model_config = ConfigDict(extra="forbid")
    planHash: str = Field(pattern=r"^[a-f0-9]{64}$")
    targetEnvelopeMm: EnvelopeMm
    primitives: list[NormalizedPrimitive] = Field(min_length=1, max_length=40)
    manufacturingIntent: Literal["digital", "attachment", "print"] | None = None


# --- Verify ----------------------------------------------------------------

class SpatialVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observation: SpatialObserveOutput
    draftRenderAssetVersions: list[int] = Field(default_factory=list)
    draftImages: list[ImageRef] = Field(default_factory=list)
    attemptHash: str = Field(pattern=r"^[a-f0-9]{64}$")


class VerifyScores(BaseModel):
    model_config = ConfigDict(extra="forbid")
    silhouette: float = Field(ge=0, le=1)
    proportion: float = Field(ge=0, le=1)
    featurePresence: float = Field(ge=0, le=1)
    viewConsistency: float = Field(ge=0, le=1)


class CriticalIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(max_length=64)
    view: str = Field(max_length=64)
    confidence: float = Field(ge=0, le=1)
    detail: str = Field(max_length=500)


class SpatialVerifyOutput(BaseModel):
    """Mirrors SpatialVerifyOutputSchema exactly."""

    model_config = ConfigDict(extra="forbid")
    scores: VerifyScores
    criticalIssues: list[CriticalIssue] = Field(default_factory=list, max_length=20)
    automatedPass: bool
    reportHash: str = Field(pattern=r"^[a-f0-9]{64}$")


# --- Health ------------------------------------------------------------

class SpatialHealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    spatial_observe: Literal["healthy", "unhealthy"]
    spatial_plan: Literal["healthy", "unhealthy"]
    spatial_math: Literal["healthy", "unhealthy"]
    spatial_verify: Literal["healthy", "unhealthy"]


# --- "Draft" variants (model output before we compute the hash field) -----
# Gemini is asked to produce these -- we never trust a model to compute its
# own sha256 correctly, so the *Hash field is always calculated server-side
# from the validated draft and attached afterward.

class SpatialObserveOutputDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subjectClass: str = Field(min_length=1, max_length=128)
    summary: str = Field(max_length=2000)
    viewCount: int = Field(ge=1, le=4)
    viewLabels: list[str] = Field(min_length=1, max_length=4)
    features: list[ObserveFeature] = Field(default_factory=list, max_length=50)
    scaleEvidence: ScaleEvidence
    occlusions: list[Occlusion] = Field(default_factory=list, max_length=20)


class SpatialPlanOutputDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targetEnvelopeMm: EnvelopeMm
    primitives: list[NormalizedPrimitive] = Field(min_length=1, max_length=40)
    manufacturingIntent: Literal["digital", "attachment", "print"] | None = None


class SpatialVerifyOutputDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scores: VerifyScores
    criticalIssues: list[CriticalIssue] = Field(default_factory=list, max_length=20)
    automatedPass: bool
