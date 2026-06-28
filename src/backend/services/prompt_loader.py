from pathlib import Path

from ..config import PROMPTS_DIR, VOICE_DNA_FILE


def load_voice_dna() -> str:
    if VOICE_DNA_FILE.exists():
        content = VOICE_DNA_FILE.read_text(encoding="utf-8").strip()
        if content:
            return f"【写作风格约束】\n{content}\n"
    return ""


def load_prompt(name: str, **kwargs: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt 模板不存在: {path}")
    template = path.read_text(encoding="utf-8")
    kwargs.setdefault("voice_dna", load_voice_dna())
    return template.format(**kwargs)
