import json
import sys
from typing import Any

from .config import (
    DATA_DIR,
    FRONTEND_DIR,
    PROMPTS_DIR,
    REPORTS_DIR,
    ROOT_DIR,
    STATES_FILE,
    settings,
)
from .services.storage import load_settings


def run_doctor() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    ok = True

    py_version = sys.version_info
    py_ok = py_version >= (3, 11)
    checks.append({
        "name": "python_version",
        "ok": py_ok,
        "detail": f"{py_version.major}.{py_version.minor}.{py_version.micro}",
        "message": "需要 Python 3.11+" if not py_ok else "OK",
    })
    ok &= py_ok

    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        probe = DATA_DIR / ".doctor_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        data_ok = True
        data_msg = "data/ 可写"
    except OSError as exc:
        data_ok = False
        data_msg = str(exc)
    checks.append({"name": "data_writable", "ok": data_ok, "detail": str(DATA_DIR), "message": data_msg})
    ok &= data_ok

    key_set = bool(load_settings().get("deepseek_api_key") or settings.deepseek_api_key)
    checks.append({
        "name": "deepseek_api_key",
        "ok": key_set,
        "detail": "settings.json or .env",
        "message": "已配置" if key_set else "未配置（AI 功能不可用）",
    })

    for path, label in [
        (STATES_FILE, "templates/states.yml"),
        (PROMPTS_DIR / "match-analysis.md", "match-analysis prompt"),
        (FRONTEND_DIR / "index.html", "frontend"),
    ]:
        exists = path.exists()
        checks.append({"name": f"file_{label}", "ok": exists, "detail": str(path), "message": "存在" if exists else "缺失"})
        ok &= exists

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    for name in ("experiences", "resumes", "jobs", "generations"):
        p = DATA_DIR / f"{name}.json"
        if p.exists():
            try:
                json.loads(p.read_text(encoding="utf-8"))
                valid = True
                msg = "JSON 合法"
            except json.JSONDecodeError as exc:
                valid = False
                msg = str(exc)
            checks.append({"name": f"json_{name}", "ok": valid, "detail": str(p), "message": msg})
            ok &= valid

    return {"status": "ok" if ok else "degraded", "checks": checks, "root": str(ROOT_DIR)}


def main() -> None:
    result = run_doctor()
    for c in result["checks"]:
        mark = "✓" if c["ok"] else "✗"
        print(f"{mark} {c['name']}: {c['message']}")
    print(f"\nOverall: {result['status']}")
    sys.exit(0 if result["status"] == "ok" else 1)
