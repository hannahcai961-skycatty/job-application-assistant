import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ..config import REPORTS_DIR, ROOT_DIR
from .storage import load_collection, save_collection


class Generation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    job_id: str | None = None
    type: str
    input_summary: str = ""
    output: dict | str
    report_path: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text.strip().lower())
    return cleaned.strip("-") or "unknown"


def save_generation(
    gen_type: str,
    output: dict | str,
    job_id: str | None = None,
    input_summary: str = "",
    report_path: str | None = None,
) -> Generation:
    items = load_collection(Generation, "generations")
    record = Generation(
        type=gen_type,
        output=output,
        job_id=job_id,
        input_summary=input_summary,
        report_path=report_path,
    )
    items.append(record)
    save_collection("generations", items)
    return record


def save_report(
    report_type: str,
    content: str,
    company: str = "job",
) -> str:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{ts}-{_slug(company)}-{report_type}.md"
    path = REPORTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return str(path.relative_to(ROOT_DIR)).replace("\\", "/")


def format_match_report(result: dict, jd_preview: str) -> str:
    blocks = result.get("blocks", {})
    lines = [
        f"# 匹配度报告",
        "",
        f"- **分数**: {result.get('score')}",
        f"- **建议**: {result.get('recommendation')} — {result.get('recommendation_message', '')}",
        "",
        f"## 摘要",
        result.get("summary", ""),
        "",
    ]
    for key, title in [
        ("a_role_summary", "A. 岗位要求"),
        ("b_cv_match", "B. 简历匹配"),
        ("c_level_fit", "C. 职级匹配"),
        ("d_key_gaps", "D. 主要差距"),
        ("e_personalization", "E. 定制方向"),
        ("f_interview_angles", "F. 面试角度"),
    ]:
        val = blocks.get(key, "")
        lines.extend([f"## {title}", str(val), ""])
    lines.extend([
        "## JD 预览",
        jd_preview[:500],
    ])
    return "\n".join(lines)
