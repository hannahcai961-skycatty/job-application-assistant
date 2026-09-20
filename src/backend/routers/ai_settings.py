import base64
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..doctor import run_doctor
from ..models.schemas import (
    AIGenerateRequest,
    AIMatchRequest,
    OcrResult,
    SettingsUpdate,
    SettingsView,
)
from ..models.schemas import Job
from ..services.deepseek import (
    DeepSeekError,
    analyze_match,
    extract_ocr,
    generate_email_draft,
)
from ..config import DATA_DIR
from ..services.documents import extract_document
from ..services.pipeline import resolve_company_name
from ..services.states import load_states_config
from ..services.storage import load_collection, load_settings, save_settings

router = APIRouter(prefix="/api", tags=["ai", "settings", "meta", "ingest"])


def _profile_text() -> str:
    extracted = DATA_DIR / "profile" / "extracted.txt"
    text = ""
    if extracted.exists():
        text = extracted.read_text(encoding="utf-8").strip()
    if not text:
        text = (load_settings().get("profile_text") or "").strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="请先在「设置」中上传简历或简介文档（PDF / Word / Markdown / TXT）",
        )
    return text


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
    data = load_settings()
    preview = (data.get("profile_text") or "").strip()
    return SettingsView(
        deepseek_api_key_set=bool(data.get("deepseek_api_key")),
        deepseek_model=data.get("deepseek_model", "deepseek-chat"),
        profile_filename=data.get("profile_filename", ""),
        profile_preview=preview[:800],
    )


@router.put("/settings", response_model=SettingsView)
def update_settings(payload: SettingsUpdate) -> SettingsView:
    data = load_settings()
    if payload.deepseek_api_key is not None:
        data["deepseek_api_key"] = payload.deepseek_api_key
    if payload.deepseek_model is not None:
        data["deepseek_model"] = payload.deepseek_model
    save_settings(data)
    return get_settings()


@router.post("/profile/upload", response_model=SettingsView)
async def upload_profile(file: UploadFile = File(...)) -> SettingsView:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空文件")
    if len(raw) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文档请小于 15MB")
    name = file.filename or "profile.txt"
    try:
        text = extract_document(name, raw).strip()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法读取该文档：{exc}") from exc
    if not text:
        raise HTTPException(
            status_code=400,
            detail="没有提取到文字。扫描版 PDF 请换成可复制文本的 PDF 或 Word。",
        )

    folder = DATA_DIR / "profile"
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(name).suffix.lower() or ".bin"
    (folder / f"source{suffix}").write_bytes(raw)
    (folder / "extracted.txt").write_text(text, encoding="utf-8")

    data = load_settings()
    data["profile_text"] = text
    data["profile_filename"] = name
    save_settings(data)
    return get_settings()


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
