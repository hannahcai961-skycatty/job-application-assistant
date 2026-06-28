from typing import Any, Literal

from ..models.schemas import Job
from ..services.storage import load_collection
from .deepseek import (
    DeepSeekError,
    analyze_match,
    generate_boss_greeting,
    generate_email_draft,
    tune_resume,
)
from .generations import save_generation, save_report
from .states import get_match_thresholds


async def run_auto_pipeline(
    jd_text: str,
    resume_id: str,
    resume_content: str,
    experiences: list[dict],
    channel: Literal["boss", "email"],
    job_id: str | None = None,
    company: str = "job",
    include_tune: bool = True,
    recipient_name: str | None = None,
) -> dict[str, Any]:
    match_result = await analyze_match(
        jd_text,
        resume_content,
        experiences,
        job_id=job_id,
        company=company,
        persist=True,
    )

    tune_result = None
    consider_min = get_match_thresholds().get("consider", 60)
    if include_tune and match_result.get("score", 0) >= consider_min:
        tune_result = await tune_resume(
            jd_text,
            resume_content,
            experiences,
            job_id=job_id,
            persist=True,
        )

    if channel == "boss":
        greeting = await generate_boss_greeting(
            jd_text,
            resume_content,
            experiences,
            job_id=job_id,
            persist=True,
        )
        channel_output: dict | str = {"greeting": greeting}
    else:
        channel_output = await generate_email_draft(
            jd_text,
            resume_content,
            experiences,
            recipient_name,
            job_id=job_id,
            persist=True,
        )

    pipeline_payload = {
        "match": match_result,
        "tune": tune_result,
        "channel": channel,
        "output": channel_output,
    }
    report_lines = [
        "# Auto-Pipeline 报告",
        "",
        f"- 渠道: {channel}",
        f"- 匹配分: {match_result.get('score')}",
        f"- 建议: {match_result.get('recommendation')} — {match_result.get('recommendation_message', '')}",
        "",
        "## 匹配摘要",
        match_result.get("summary", ""),
        "",
        "## 渠道输出",
        str(channel_output),
    ]
    report_path = save_report("pipeline", "\n".join(report_lines), company)
    save_generation(
        "pipeline",
        pipeline_payload,
        job_id=job_id,
        input_summary=jd_text[:200],
        report_path=report_path,
    )

    return {
        **pipeline_payload,
        "report_path": report_path,
    }


def resolve_company_name(job_id: str | None) -> str:
    if not job_id:
        return "job"
    jobs = load_collection(Job, "jobs")
    job = next((j for j in jobs if j.id == job_id), None)
    return job.company if job else "job"
