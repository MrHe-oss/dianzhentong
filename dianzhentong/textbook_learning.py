"""教材知识小课兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from typing import Any

from .content_loader import load_textbook_projects


BOOK_ID = "electrical_control_plc_s71200_tong"
_CONTENTS = load_textbook_projects(BOOK_ID)
_UNITS = tuple(unit for content in _CONTENTS for unit in content["project"]["units"])

SAMPLE_UNIT_TOPIC_IDS = tuple(_UNITS[0]["topic_ids"])
ALL_LESSON_TOPIC_IDS = tuple(topic_id for unit in _UNITS for topic_id in unit["topic_ids"])
TEXTBOOK_LESSONS: dict[str, dict[str, Any]] = {
    topic["id"]: topic["lesson"] for unit in _UNITS for topic in unit["topics"]
}


def lesson_for_topic(topic_id: str) -> dict[str, Any] | None:
    return TEXTBOOK_LESSONS.get(topic_id)
