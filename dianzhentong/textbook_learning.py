"""教材知识小课兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class TextbookUnitProgress:
    knowledge_completion: float
    example_completed: bool
    assessment_passed: bool
    completion: float
    status: str


def calculate_unit_progress(topic_ids: tuple[str, ...], learned_topic_ids: set[str],
                            quiz_history: list[dict[str, Any]]) -> TextbookUnitProgress:
    """按知识40%、例题20%、单元评测40%计算教材单元进度。"""
    knowledge = sum(item in learned_topic_ids for item in topic_ids) / len(topic_ids) if topic_ids else 0.0
    example_completed = any(item.get("mode") == "textbook_example" for item in quiz_history)
    assessment_passed = any(
        item.get("mode") == "textbook_unit_assessment" and item.get("passed")
        for item in quiz_history
    )
    completion = knowledge * 0.4 + float(example_completed) * 0.2 + float(assessment_passed) * 0.4
    if completion >= 1.0:
        status = "已完成"
    elif completion >= 0.7:
        status = "基本掌握"
    elif completion > 0:
        status = "学习中"
    else:
        status = "未开始"
    return TextbookUnitProgress(knowledge, example_completed, assessment_passed, completion, status)
