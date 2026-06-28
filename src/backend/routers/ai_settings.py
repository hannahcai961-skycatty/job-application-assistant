from fastapi import APIRouter, HTTPException

from ..doctor import run_doctor
from ..models.schemas import (
    AIGenerateRequest,
    AIMatchRequest,
    AutoPipelineRequest,
    SettingsUpdate,
    SettingsView,
)
from ..models.schemas import Experience, Job, Resume
from ..services.deepseek import (
    DeepSeekError,
    analyze_match,
    generate_boss_greeting,
    generate_email_draft,
    tune_resume,
)
from ..services.pipeline import resolve_company_name, run_auto_pipeline
from ..services.states import load_states_config
from ..services.storage import load_collection, load_settings, save_settings

router = APIRouter(prefix="/api", tags=["ai", "settings", "meta"])


def _get_resume_context(resume_id: str) -> tuple[str, list[dict]]:
    resumes = load_collection(Resume, "resumes")
    resume = next((r for r in resumes if r.id == resume_id), None)
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    experiences = load_collection(Experience, "experiences")
    linked = [e for e in experiences if e.id in resume.experience_ids]
    exp_dicts = [e.model_dump() for e in linked] or [
        e.model_dump() for e in experiences
    ]
    return resume.content, exp_dicts


def _resolve_jd(job_id: str | None, jd_text: str) -> str:
    if jd_text.strip():
        return jd_text
    if job_id:
        jobs = load_collection(Job, "jobs")
        job = next((j for j in jobs if j.id == job_id), None)
        if job and job.jd_text:
            return job.jd_text
    raise HTTPException(status_code=400, detail="请提供 JD 文本或有效岗位 ID")


@router.get("/doctor")
def doctor() -> dict:
    return run_doctor()


@router.get("/states")
def get_states() -> dict:
    return load_states_config()


@router.get("/settings", response_model=SettingsView)
def get_settings() -> SettingsView:
    data = load_settings()
    return SettingsView(
        deepseek_api_key_set=bool(data.get("deepseek_api_key")),
        deepseek_model=data.get("deepseek_model", "deepseek-chat"),
        default_resume_id=data.get("default_resume_id"),
    )


@router.put("/settings", response_model=SettingsView)
def update_settings(payload: SettingsUpdate) -> SettingsView:
    data = load_settings()
    if payload.deepseek_api_key is not None:
        data["deepseek_api_key"] = payload.deepseek_api_key
    if payload.deepseek_model is not None:
        data["deepseek_model"] = payload.deepseek_model
    if payload.default_resume_id is not None:
        data["default_resume_id"] = payload.default_resume_id
    save_settings(data)
    return get_settings()


@router.post("/ai/match")
async def ai_match(payload: AIMatchRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    content, exps = _get_resume_context(payload.resume_id)
    company = resolve_company_name(payload.job_id)
    try:
        return await analyze_match(
            jd, content, exps, job_id=payload.job_id, company=company
        )
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ai/tune-resume")
async def ai_tune(payload: AIMatchRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    content, exps = _get_resume_context(payload.resume_id)
    try:
        return await tune_resume(jd, content, exps, job_id=payload.job_id)
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ai/boss-greeting")
async def ai_boss(payload: AIGenerateRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    content, exps = _get_resume_context(payload.resume_id)
    try:
        text = await generate_boss_greeting(
            jd, content, exps, job_id=payload.job_id
        )
        return {"greeting": text}
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ai/email-draft")
async def ai_email(payload: AIGenerateRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    content, exps = _get_resume_context(payload.resume_id)
    try:
        return await generate_email_draft(
            jd, content, exps, payload.recipient_name, job_id=payload.job_id
        )
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ai/auto-pipeline")
async def ai_auto_pipeline(payload: AutoPipelineRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    content, exps = _get_resume_context(payload.resume_id)
    company = resolve_company_name(payload.job_id)
    try:
        return await run_auto_pipeline(
            jd,
            payload.resume_id,
            content,
            exps,
            channel=payload.channel,
            job_id=payload.job_id,
            company=company,
            include_tune=payload.include_tune,
            recipient_name=payload.recipient_name,
        )
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
