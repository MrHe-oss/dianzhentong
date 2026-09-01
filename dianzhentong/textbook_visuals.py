"""教材抽象图解兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from .content_loader import load_textbook_projects


_CONTENTS = load_textbook_projects("electrical_control_plc_s71200_tong")
TOPIC_VISUALS = {
    topic["id"]: topic["visual"]
    for content in _CONTENTS for unit in content["project"]["units"]
    for topic in unit["topics"] if topic.get("visual")
}
SELF_HOLD_STATES = tuple(
    tuple(item) for item in _CONTENTS[0].get("shared_state_demos", {}).get("self_hold", [])
)


def visual_for_topic(topic_id: str):
    return TOPIC_VISUALS.get(topic_id)
