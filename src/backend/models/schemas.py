from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid4())


class JobBase(BaseModel):
    company: str = ""
    position: str = ""
    jd_text: str = ""
    url: str = ""
    source: Literal["fair", "official", "platform"] = "platform"
    status: Literal[
        "pending",
        "applied",
        "interview_pending",
        "interviewing",
        "rejected",
    ] = "pending"
    applied_at: str = ""
    interview_round: str = ""
    notes: str = ""
    match_score: int | None = None
    match_reason: str = ""


class JobCreate(JobBase):
    pass


class Job(JobBase):
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SettingsUpdate(BaseModel):
    deepseek_api_key: str | None = None
    deepseek_model: str | None = None
    deepseek_base_url: str | None = None


class ProfileDocView(BaseModel):
    id: str
    topic: str
    filename: str
    preview: str
    created_at: str


class ProfileUpdate(BaseModel):
    topic: str


class SettingsView(BaseModel):
    deepseek_api_key_set: bool
    deepseek_model: str
    deepseek_base_url: str
    profiles: list[ProfileDocView] = Field(default_factory=list)


class AIMatchRequest(BaseModel):
    job_id: str | None = None
    jd_text: str = ""


class AIGenerateRequest(BaseModel):
    job_id: str | None = None
    jd_text: str = ""
    recipient_name: str | None = None


class OcrResult(BaseModel):
    company: str = ""
    position: str = ""
    url: str = ""
    jd_text: str = ""
    raw_text: str = ""
