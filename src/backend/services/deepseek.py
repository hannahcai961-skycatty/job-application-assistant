import json
from typing import Any

import httpx

from ..config import settings
from .generations import format_match_report, save_generation, save_report
from .prompt_loader import load_prompt
from .states import apply_recommendation
from .storage import load_settings


class DeepSeekError(Exception):
    pass


def _resolve_api_key() -> str:
    local = load_settings().get("deepseek_api_key", "")
    return local or settings.deepseek_api_key


def _resolve_model() -> str:
    local = load_settings().get("deepseek_model", "")
    return local or settings.deepseek_model


async def chat_completion(
    prompt: str,
    temperature: float = 0.7,
    *,
    image_data_url: str | None = None,
) -> str:
    api_key = _resolve_api_key()
    if not api_key:
        raise DeepSeekError("未配置 DeepSeek API Key，请在设置页或 .env 中填写")

    url = f"{settings.deepseek_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if image_data_url:
        content: str | list[dict[str, Any]] = [
            {"type": "image_url", "image_url": {"url": image_data_url}},
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt
    payload = {
        "model": _resolve_model(),
        "messages": [{"role": "user", "content": content}],
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise DeepSeekError(f"DeepSeek 请求失败: {response.status_code} {response.text[:200]}")
        data = response.json()
        return data["choices"][0]["message"]["content"]


_OCR_PROMPT = """从这张招聘/岗位截图中提取信息。只根据图中可见文字，不要编造。
请按以下 JSON 输出（仅 JSON，无 markdown）：
{
  "company": "公司名，没有则空字符串",
  "position": "岗位名称，没有则空字符串",
  "url": "图中可见的投递或岗位链接，没有则空字符串",
  "jd_text": "岗位要求/职责/任职条件的完整转写",
  "raw_text": "图中主要文字的转写"
}"""


async def extract_ocr(image_b64: str, mime: str) -> dict[str, Any]:
    data_url = f"data:{mime};base64,{image_b64}"
    raw = await chat_completion(_OCR_PROMPT, temperature=0.1, image_data_url=data_url)
    return _parse_json(raw)


def _format_bullets(experiences: list[dict]) -> str:
    if not experiences:
        return "（暂无经历素材）"
    lines = []
    for exp in experiences:
        title = exp.get("title", "")
        bullets = exp.get("bullets") or []
        content = exp.get("content", "")
        block = f"- {title}"
        if bullets:
            block += "\n  " + "\n  ".join(f"• {b}" for b in bullets)
        elif content:
            block += f"\n  {content[:300]}"
        lines.append(block)
    return "\n".join(lines)


def _prompt(name: str, jd_text: str, resume_content: str, experiences: list[dict], **extra: str) -> str:
    return load_prompt(
        name,
        jd_text=jd_text,
        resume_content=resume_content,
        experience_bullets=_format_bullets(experiences),
        **extra,
    )


async def analyze_match(
    jd_text: str,
    resume_content: str,
    experiences: list[dict],
    *,
    job_id: str | None = None,
    company: str = "job",
    persist: bool = True,
) -> dict[str, Any]:
    prompt = _prompt("match-analysis", jd_text, resume_content, experiences)
    raw = await chat_completion(prompt, temperature=0.3)
    result = apply_recommendation(_parse_json(raw))
    if persist:
        report = format_match_report(result, jd_text)
        report_path = save_report("match", report, company)
        save_generation(
            "match",
            result,
            job_id=job_id,
            input_summary=jd_text[:200],
            report_path=report_path,
        )
    return result


async def tune_resume(
    jd_text: str,
    resume_content: str,
    experiences: list[dict],
    *,
    job_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    prompt = _prompt("resume-tune", jd_text, resume_content, experiences)
    raw = await chat_completion(prompt, temperature=0.5)
    result = _parse_json(raw)
    if persist:
        save_generation("tune", result, job_id=job_id, input_summary=jd_text[:200])
    return result


async def generate_boss_greeting(
    jd_text: str,
    resume_content: str,
    experiences: list[dict],
    *,
    job_id: str | None = None,
    persist: bool = True,
) -> str:
    prompt = _prompt("boss-greeting", jd_text, resume_content, experiences)
    text = (await chat_completion(prompt, temperature=0.7)).strip()
    if persist:
        save_generation("boss", text, job_id=job_id, input_summary=jd_text[:200])
    return text


async def generate_email_draft(
    jd_text: str,
    resume_content: str,
    experiences: list[dict],
    recipient_name: str | None = None,
    *,
    job_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    prompt = _prompt(
        "email-draft",
        jd_text,
        resume_content,
        experiences,
        recipient_name=recipient_name or "招聘负责人",
    )
    raw = await chat_completion(prompt, temperature=0.6)
    result = _parse_json(raw)
    if persist:
        save_generation("email", result, job_id=job_id, input_summary=jd_text[:200])
    return result


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as exc:
        raise DeepSeekError("AI 返回格式解析失败，请重试") from exc
