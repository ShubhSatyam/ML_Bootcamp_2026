from datetime import datetime, timezone
from enum import Enum

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class MeetingStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"


Minute = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class MeetingMinutes(BaseModel):
    """Validated, ordered discussion points for one meeting."""

    model_config = ConfigDict(extra="forbid")

    entries: list[Minute] = Field(default_factory=list)


class ActionItem(BaseModel):
    """An explicitly stated follow-up, with no inferred metadata."""

    model_config = ConfigDict(extra="forbid")

    task: Minute
    owner: str = "Unspecified"
    deadline: str = "Unspecified"

    @field_validator("owner", "deadline", mode="before")
    @classmethod
    def normalize_missing_values(cls, value: str | None) -> str:
        return value.strip() if isinstance(value, str) and value.strip() else "Unspecified"


# Retained as a public alias because the API and frontend expose `tasks`.
Task = ActionItem


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: Minute
    evidence: Minute


class MeetingDocumentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: Minute
    minutes: list[Minute] = Field(default_factory=list)
    decisions: list[Decision]
    tasks: list[ActionItem]

    @field_validator("minutes")
    @classmethod
    def validate_minutes(cls, value: list[Minute]) -> list[Minute]:
        return MeetingMinutes(entries=value).entries


class Meeting(BaseModel):
    id: str
    filename: str
    status: MeetingStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_transcript: str | None = None
    refined_transcript: str | None = None
    summary: str | None = None
    minutes: list[Minute] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    tasks: list[ActionItem] = Field(default_factory=list)
    error: str | None = None
    current_stage: str | None = None
    progress: int = 0
