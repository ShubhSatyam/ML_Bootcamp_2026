from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeetingStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Task(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=1)
    owner: str = "Unspecified"
    deadline: str = "Unspecified"

    @field_validator("owner", "deadline", mode="before")
    @classmethod
    def normalize_missing_values(cls, value: str | None) -> str:
        return value.strip() if isinstance(value, str) and value.strip() else "Unspecified"


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class MeetingDocumentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    minutes: list[str]
    decisions: list[Decision]
    tasks: list[Task]


class Meeting(BaseModel):
    id: str
    filename: str
    status: MeetingStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_transcript: str | None = None
    refined_transcript: str | None = None
    summary: str | None = None
    minutes: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    error: str | None = None
    current_stage: str | None = None
    progress: int = 0
