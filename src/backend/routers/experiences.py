from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.schemas import (
    Experience,
    ExperienceCreate,
    Job,
    JobCreate,
    Resume,
    ResumeCreate,
)
from ..services.storage import load_collection, save_collection

router = APIRouter(prefix="/api/experiences", tags=["experiences"])


@router.get("", response_model=list[Experience])
def list_experiences() -> list[Experience]:
    return load_collection(Experience, "experiences")


@router.post("", response_model=Experience)
def create_experience(payload: ExperienceCreate) -> Experience:
    items = load_collection(Experience, "experiences")
    item = Experience(**payload.model_dump())
    items.append(item)
    save_collection("experiences", items)
    return item


@router.put("/{item_id}", response_model=Experience)
def update_experience(item_id: str, payload: ExperienceCreate) -> Experience:
    items = load_collection(Experience, "experiences")
    for idx, item in enumerate(items):
        if item.id == item_id:
            updated = Experience(
                **payload.model_dump(),
                id=item.id,
                created_at=item.created_at,
                updated_at=datetime.now().isoformat(),
            )
            items[idx] = updated
            save_collection("experiences", items)
            return updated
    raise HTTPException(status_code=404, detail="经历不存在")


@router.delete("/{item_id}")
def delete_experience(item_id: str) -> dict[str, str]:
    items = load_collection(Experience, "experiences")
    filtered = [item for item in items if item.id != item_id]
    if len(filtered) == len(items):
        raise HTTPException(status_code=404, detail="经历不存在")
    save_collection("experiences", filtered)
    return {"status": "ok"}
