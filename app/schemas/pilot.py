from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)

PilotTimeline = Literal["immediate", "30_days", "60_90_days", "exploring"]
PilotStatus = Literal["new", "contacted", "qualified", "closed"]


class PilotApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    contact_name: str = Field(min_length=2, max_length=120)
    work_email: EmailStr
    company: str = Field(min_length=2, max_length=160)
    role: str | None = Field(default=None, max_length=120)
    use_case: str = Field(min_length=20, max_length=2000)
    timeline: PilotTimeline | None = None
    source: str = Field(
        default="website-pilot",
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    )
    consent_to_contact: Literal[True]
    website: str | None = Field(
        default=None,
        max_length=512,
        description="Leave blank. This field is a bot-detection honeypot.",
        exclude=True,
    )

    @field_validator("work_email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("role", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class PilotApplicationAccepted(BaseModel):
    accepted: Literal[True] = True
    message: str = "Thanks. SALTI8 will review your pilot request."


class PilotApplicationAdminResponse(BaseModel):
    id: str
    contact_name: str
    work_email: str
    company: str
    role: str | None
    use_case: str
    timeline: PilotTimeline | None
    source: str
    status: PilotStatus
    consent_to_contact: bool
    consented_at: datetime
    created_at: datetime
    updated_at: datetime
