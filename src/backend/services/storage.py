import json
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ..config import DATA_DIR

T = TypeVar("T", bound=BaseModel)


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _collection_path(name: str) -> Path:
    return DATA_DIR / f"{name}.json"


def load_collection(model: type[T], name: str) -> list[T]:
    _ensure_data_dir()
    path = _collection_path(name)
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("items", [])
    return [model.model_validate(item) for item in items]


def save_collection(name: str, items: list[BaseModel]) -> None:
    _ensure_data_dir()
    path = _collection_path(name)
    payload = {"items": [item.model_dump() for item in items]}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings() -> dict:
    _ensure_data_dir()
    path = DATA_DIR / "settings.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_settings(data: dict) -> None:
    _ensure_data_dir()
    path = DATA_DIR / "settings.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
