"""教材抽象图解兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from .content_loader import load_textbook_content


_CONTENT = load_textbook_content("electrical_control_plc_s71200_tong")
TOPIC_VISUALS = {
    topic["id"]: topic["visual"]
    for unit in _CONTENT["project"]["units"] for topic in unit["topics"] if topic.get("visual")
}
SELF_HOLD_STATES = tuple(
    tuple(item) for item in _CONTENT.get("shared_state_demos", {}).get("self_hold", [])
)


def visual_for_topic(topic_id: str):
    return TOPIC_VISUALS.get(topic_id)
