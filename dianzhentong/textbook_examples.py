"""教材原创公式与例题兼容接口；实际内容来自结构化教材文件。"""
from __future__ import annotations

from typing import Any

from .content_loader import load_textbook_content


_UNITS = load_textbook_content("electrical_control_plc_s71200_tong")["project"]["units"]
LOGIC_FORMULAS: dict[str, tuple[dict[str, Any], ...]] = {
    topic["id"]: tuple(topic.get("formulas", []))
    for unit in _UNITS for topic in unit["topics"] if topic.get("formulas")
}
UNIT_EXAMPLES: dict[int, dict[str, Any]] = {
    index: unit["worked_example"] for index, unit in enumerate(_UNITS)
}


def formulas_for_topic(topic_id: str) -> tuple[dict[str, Any], ...]:
    return LOGIC_FORMULAS.get(topic_id, tuple())


def example_for_unit(unit_index: int) -> dict[str, Any]:
    return UNIT_EXAMPLES[unit_index]
