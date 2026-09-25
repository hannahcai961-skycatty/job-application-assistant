from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ..config import DATA_DIR
from ..models.schemas import ProfileDocView
from .storage import load_collection, load_settings, save_collection, save_settings


class ProfileDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    filename: str
    content: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProfileUpdate(BaseModel):
    topic: str | None = None


def _folder() -> Path:
    path = DATA_DIR / "profiles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_profiles() -> list[ProfileDoc]:
    _migrate_legacy_if_needed()
    return load_collection(ProfileDoc, "profiles")


def get_profile(item_id: str) -> ProfileDoc | None:
    return next((p for p in list_profiles() if p.id == item_id), None)


def add_profile(*, topic: str, filename: str, content: str, raw: bytes | None = None) -> ProfileDoc:
    items = list_profiles()
    topic = (topic or "").strip() or _topic_from_filename(filename)
    item = ProfileDoc(topic=topic, filename=filename, content=content)
    items.append(item)
    save_collection("profiles", items)
    if raw is not None:
        suffix = Path(filename).suffix.lower() or ".bin"
        (_folder() / f"{item.id}{suffix}").write_bytes(raw)
    (_folder() / f"{item.id}.txt").write_text(content, encoding="utf-8")
    return item


def update_profile(item_id: str, *, topic: str | None = None) -> ProfileDoc | None:
    items = list_profiles()
    for idx, item in enumerate(items):
        if item.id != item_id:
            continue
        updated = item.model_copy(
            update={
                "topic": (topic or item.topic).strip() or item.topic,
                "updated_at": datetime.now().isoformat(),
            }
        )
        items[idx] = updated
        save_collection("profiles", items)
        return updated
    return None


def delete_profile(item_id: str) -> bool:
    items = list_profiles()
    filtered = [p for p in items if p.id != item_id]
    if len(filtered) == len(items):
        return False
    save_collection("profiles", filtered)
    folder = _folder()
    for path in folder.glob(f"{item_id}.*"):
        path.unlink(missing_ok=True)
    return True


def format_profiles_for_prompt(docs: list[ProfileDoc] | None = None) -> str:
    docs = docs if docs is not None else list_profiles()
    if not docs:
        return ""
    blocks = []
    for i, doc in enumerate(docs, start=1):
        blocks.append(
            "\n".join(
                [
                    f"===== 材料 {i} | 主题：{doc.topic} | 文件：{doc.filename} =====",
                    "（以下内容仅属于该主题，评估时勿与其他材料主题混淆）",
                    doc.content.strip(),
                    f"===== 材料 {i} 结束 =====",
                ]
            )
        )
    return "\n\n".join(blocks)


def to_views(docs: list[ProfileDoc] | None = None) -> list[ProfileDocView]:
    docs = docs if docs is not None else list_profiles()
    return [
        ProfileDocView(
            id=d.id,
            topic=d.topic,
            filename=d.filename,
            preview=(d.content or "").strip()[:400],
            created_at=d.created_at,
        )
        for d in docs
    ]


def _topic_from_filename(filename: str) -> str:
    stem = Path(filename or "未命名").stem.strip()
    return stem or "未命名材料"


def _migrate_legacy_if_needed() -> None:
    """把旧版单文件 profile 迁到多文档库（只做一次）。"""
    existing = load_collection(ProfileDoc, "profiles")
    if existing:
        return

    settings = load_settings()
    text = (settings.get("profile_text") or "").strip()
    filename = settings.get("profile_filename") or "legacy-profile.txt"
    extracted = DATA_DIR / "profile" / "extracted.txt"
    if not text and extracted.exists():
        text = extracted.read_text(encoding="utf-8").strip()
    if not text:
        return

    item = ProfileDoc(
        topic=_topic_from_filename(filename),
        filename=filename,
        content=text,
    )
    save_collection("profiles", [item])
    (_folder() / f"{item.id}.txt").write_text(text, encoding="utf-8")
    settings.pop("profile_text", None)
    settings.pop("profile_filename", None)
    save_settings(settings)
