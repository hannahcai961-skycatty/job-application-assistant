from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..models.schemas import Job, JobCreate
from ..services.storage import load_collection, save_collection

jobs_router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@jobs_router.get("", response_model=list[Job])
def list_jobs() -> list[Job]:
    return load_collection(Job, "jobs")


@jobs_router.post("", response_model=Job)
def create_job(payload: JobCreate) -> Job:
    items = load_collection(Job, "jobs")
    item = Job(**payload.model_dump())
    items.append(item)
    save_collection("jobs", items)
    return item


@jobs_router.put("/{item_id}", response_model=Job)
def update_job(item_id: str, payload: JobCreate) -> Job:
    items = load_collection(Job, "jobs")
    for idx, item in enumerate(items):
        if item.id == item_id:
            updated = Job(
                **payload.model_dump(),
                id=item.id,
                created_at=item.created_at,
                updated_at=datetime.now().isoformat(),
            )
            items[idx] = updated
            save_collection("jobs", items)
            return updated
    raise HTTPException(status_code=404, detail="岗位不存在")


@jobs_router.delete("/{item_id}")
def delete_job(item_id: str) -> dict[str, str]:
    items = load_collection(Job, "jobs")
    filtered = [item for item in items if item.id != item_id]
    if len(filtered) == len(items):
        raise HTTPException(status_code=404, detail="岗位不存在")
    save_collection("jobs", filtered)
    return {"status": "ok"}
