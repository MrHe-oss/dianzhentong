"""教材原创公式与例题兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from typing import Any

from .content_loader import load_textbook_projects, TEXTBOOK_IDS, all_textbook_projects


_UNITS = tuple(unit for content in load_textbook_projects("electrical_control_plc_s71200_tong")
               for unit in content["project"]["units"])
LOGIC_FORMULAS: dict[str, tuple[dict[str, Any], ...]] = {
    topic["id"]: tuple(topic.get("formulas", []))
    for content in all_textbook_projects() for unit in content["project"]["units"]
    for topic in unit["topics"] if topic.get("formulas")
}
UNIT_EXAMPLES: dict[int, dict[str, Any]] = {
    index: unit["worked_example"] for index, unit in enumerate(_UNITS)
}


def formulas_for_topic(topic_id: str) -> tuple[dict[str, Any], ...]:
    return LOGIC_FORMULAS.get(topic_id, tuple())


BOOK_EXAMPLES = {
    book_id: tuple(unit["worked_example"] for content in load_textbook_projects(book_id)
                   for unit in content["project"]["units"])
    for book_id in TEXTBOOK_IDS
}


def example_for_unit(unit_index: int, book_id: str = "electrical_control_plc_s71200_tong") -> dict[str, Any]:
    return BOOK_EXAMPLES[book_id][unit_index]
