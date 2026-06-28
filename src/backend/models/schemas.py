from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid4())


class ExperienceBase(BaseModel):
    title: str
    category: Literal["internship", "project", "competition", "other"] = "project"
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)


class ExperienceCreate(ExperienceBase):
    pass


class Experience(ExperienceBase):
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ResumeBase(BaseModel):
    name: str
    description: str = ""
    content: str = ""
    experience_ids: list[str] = Field(default_factory=list)
    is_default: bool = False


class ResumeCreate(ResumeBase):
    pass


class Resume(ResumeBase):
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class JobBase(BaseModel):
    company: str
    position: str
    jd_text: str = ""
    source: Literal["boss", "email", "other"] = "boss"
    status: Literal["pending", "greeted", "emailed", "replied", "dropped"] = "pending"
    resume_id: str | None = None
    notes: str = ""


class JobCreate(JobBase):
    pass


class Job(JobBase):
    id: str = Field(default_factory=new_id)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SettingsUpdate(BaseModel):
    deepseek_api_key: str | None = None
    deepseek_model: str | None = None
    default_resume_id: str | None = None


class SettingsView(BaseModel):
    deepseek_api_key_set: bool
    deepseek_model: str
    default_resume_id: str | None = None


class AIMatchRequest(BaseModel):
    job_id: str | None = None
    jd_text: str
    resume_id: str


class AIGenerateRequest(BaseModel):
    job_id: str | None = None
    jd_text: str
    resume_id: str
    recipient_name: str | None = None


class AutoPipelineRequest(BaseModel):
    job_id: str | None = None
    jd_text: str
    resume_id: str
    channel: Literal["boss", "email"] = "boss"
    include_tune: bool = True
    recipient_name: str | None = None
