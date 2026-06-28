from __future__ import annotations

import yaml

from ..config import STATES_FILE


def load_states_config() -> dict:
    if not STATES_FILE.exists():
        return {"states": [], "match_thresholds": {"apply": 75, "consider": 60}}
    return yaml.safe_load(STATES_FILE.read_text(encoding="utf-8"))


def get_state_labels() -> dict[str, str]:
    data = load_states_config()
    return {s["id"]: s["label"] for s in data.get("states", [])}


def get_match_thresholds() -> dict[str, int]:
    data = load_states_config()
    return data.get("match_thresholds", {"apply": 75, "consider": 60})


def apply_recommendation(result: dict) -> dict:
    score = int(result.get("score", 0))
    thresholds = get_match_thresholds()
    apply_min = thresholds.get("apply", 75)
    consider_min = thresholds.get("consider", 60)
    if score >= apply_min:
        rec, msg = "apply", f"匹配度 {score}，建议花时间定制投递"
    elif score >= consider_min:
        rec, msg = "consider", f"匹配度 {score}，可权衡后决定是否投递"
    else:
        rec, msg = "skip", f"匹配度 {score}，不建议花时间深度定制"
    result["recommendation"] = rec
    result["recommendation_message"] = msg
    return result
