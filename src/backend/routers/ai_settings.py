import base64
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..config import settings
from ..doctor import run_doctor
from ..models.schemas import (
    AIGenerateRequest,
    AIMatchRequest,
    Job,
    OcrResult,
    ProfileDocView,
    ProfileUpdate,
    SettingsUpdate,
    SettingsView,
)
from ..services.deepseek import (
    DeepSeekError,
    analyze_match,
    extract_ocr,
    generate_email_draft,
)
from ..services.documents import extract_document
from ..services.pipeline import resolve_company_name
from ..services import profiles as profile_store
from ..services.states import load_states_config
from ..services.storage import load_collection, load_settings, save_settings

router = APIRouter(prefix="/api", tags=["ai", "settings", "meta", "ingest"])


def _profile_text() -> str:
    text = profile_store.format_profiles_for_prompt().strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="请先在「设置」中上传至少一份个人材料，并为每份填写主题",
        )
    return text


def _settings_view() -> SettingsView:
    data = load_settings()
    return SettingsView(
        deepseek_api_key_set=bool(data.get("deepseek_api_key") or settings.deepseek_api_key),
        deepseek_model=data.get("deepseek_model") or settings.deepseek_model,
        deepseek_base_url=data.get("deepseek_base_url") or settings.deepseek_base_url,
        profiles=profile_store.to_views(),
    )


def _resolve_jd(job_id: str | None, jd_text: str) -> str:
    if jd_text and jd_text.strip():
        return jd_text.strip()
    if job_id:
        jobs = load_collection(Job, "jobs")
        job = next((j for j in jobs if j.id == job_id), None)
        if job and job.jd_text:
            return job.jd_text
    raise HTTPException(status_code=400, detail="请提供 JD 文本，或从投递表选择有 JD 的岗位")


@router.get("/doctor")
def doctor() -> dict:
    return run_doctor()


@router.get("/states")
def get_states() -> dict:
    return load_states_config()


@router.get("/settings", response_model=SettingsView)
def get_settings() -> SettingsView:
    return _settings_view()


@router.put("/settings", response_model=SettingsView)
def update_settings(payload: SettingsUpdate) -> SettingsView:
    data = load_settings()
    if payload.deepseek_api_key is not None:
        data["deepseek_api_key"] = payload.deepseek_api_key
    if payload.deepseek_model is not None:
        data["deepseek_model"] = payload.deepseek_model
    if payload.deepseek_base_url is not None:
        data["deepseek_base_url"] = payload.deepseek_base_url.strip().rstrip("/")
    save_settings(data)
    return _settings_view()


@router.get("/profiles")
def list_profiles() -> list[ProfileDocView]:
    return profile_store.to_views()


@router.post("/profiles/upload", response_model=SettingsView)
async def upload_profiles(
    files: list[UploadFile] = File(...),
    topic: str = Form(""),
) -> SettingsView:
    if not files:
        raise HTTPException(status_code=400, detail="请选择至少一个文件")

    shared_topic = (topic or "").strip()
    uploaded = 0
    for file in files:
        raw = await file.read()
        if not raw:
            continue
        if len(raw) > 15 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{file.filename} 超过 15MB")
        name = file.filename or "profile.txt"
        try:
            text = extract_document(name, raw).strip()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"{name}: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{name} 无法读取：{exc}") from exc
        if not text:
            raise HTTPException(
                status_code=400,
                detail=f"{name} 没有提取到文字。扫描版 PDF 请换成可复制文本的 PDF 或 Word。",
            )
        # 多文件时：有统一主题则「主题 · 文件名」区分；单文件用统一主题或文件名
        if shared_topic and len(files) > 1:
            doc_topic = f"{shared_topic} · {Path(name).stem}"
        elif shared_topic:
            doc_topic = shared_topic
        else:
            doc_topic = Path(name).stem or "未命名材料"
        profile_store.add_profile(topic=doc_topic, filename=name, content=text, raw=raw)
        uploaded += 1

    if not uploaded:
        raise HTTPException(status_code=400, detail="没有成功上传任何文件")
    return _settings_view()


@router.put("/profiles/{item_id}", response_model=SettingsView)
def update_profile(item_id: str, payload: ProfileUpdate) -> SettingsView:
    updated = profile_store.update_profile(item_id, topic=payload.topic)
    if not updated:
        raise HTTPException(status_code=404, detail="材料不存在")
    return _settings_view()


@router.delete("/profiles/{item_id}", response_model=SettingsView)
def delete_profile(item_id: str) -> SettingsView:
    if not profile_store.delete_profile(item_id):
        raise HTTPException(status_code=404, detail="材料不存在")
    return _settings_view()


@router.post("/ingest/ocr", response_model=OcrResult)
async def ingest_ocr(file: UploadFile = File(...)) -> OcrResult:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片请小于 8MB")
    mime = file.content_type or "image/png"
    if not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    b64 = base64.b64encode(raw).decode("ascii")
    try:
        data = await extract_ocr(b64, mime)
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return OcrResult(
        company=str(data.get("company") or ""),
        position=str(data.get("position") or ""),
        url=str(data.get("url") or ""),
        jd_text=str(data.get("jd_text") or ""),
        raw_text=str(data.get("raw_text") or ""),
    )


@router.post("/ai/match")
async def ai_match(payload: AIMatchRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    profile = _profile_text()
    company = resolve_company_name(payload.job_id)
    try:
        return await analyze_match(
            jd, profile, [], job_id=payload.job_id, company=company
        )
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/ai/email-draft")
async def ai_email(payload: AIGenerateRequest) -> dict:
    jd = _resolve_jd(payload.job_id, payload.jd_text)
    profile = _profile_text()
    try:
        return await generate_email_draft(
            jd, profile, [], payload.recipient_name, job_id=payload.job_id
        )
    except DeepSeekError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
