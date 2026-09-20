from ..models.schemas import Job
from ..services.storage import load_collection


def resolve_company_name(job_id: str | None) -> str:
    if not job_id:
        return "job"
    jobs = load_collection(Job, "jobs")
    job = next((j for j in jobs if j.id == job_id), None)
    return job.company if job else "job"
