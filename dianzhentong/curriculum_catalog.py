"""学习平台的课程、统一知识点与教材版本映射结构。"""
from __future__ import annotations

from typing import Any

from .course import COURSE_CHAPTERS, COURSES
from .learning import KNOWLEDGE_CARDS


LEARNING_DOMAINS = (
    {"id": "foundation", "title": "电气基础", "description": "电路、低压电器、电机和安全基础。"},
    {"id": "control", "title": "控制与自动化", "description": "继电器控制、PLC、自动控制和运动控制。"},
    {"id": "power", "title": "电力系统", "description": "发输配电、供配电、继电保护与新能源。"},
    {"id": "practice", "title": "识图与实训", "description": "读图、逻辑分析、虚拟实验和故障排查。"},
)


KNOWLEDGE_TOPICS: dict[str, dict[str, Any]] = {
    card_id: {
        "id": card_id,
        "title": card["title"],
        "summary": card["principle"],
        "prerequisites": tuple(),
        "course_ids": tuple(
            course["id"] for course in COURSES
            if any(card_id in chapter["card_ids"] for chapter in COURSE_CHAPTERS[course["id"]])
        ),
    }
    for card_id, card in KNOWLEDGE_CARDS.items()
}


# 首版采用平台原创的通用章节结构。字段已经支持后续接入用户指定的书名、版次和ISBN；
# 在未取得出版社授权前，不收录教材正文、插图或课后题。
BOOK_EDITION_MAPPINGS: dict[str, dict[str, Any]] = {
    "electrical_control_general_v1": {
        "id": "electrical_control_general_v1",
        "title": "电气控制与PLC基础",
        "edition": "通用教材学习路线 v1",
        "publisher": "电诊通原创映射",
        "isbn": None,
        "official": False,
        "notice": "非出版社官方配套内容；仅按常见教材知识顺序组织原创讲解与训练。",
        "course_ids": (
            "low_voltage_control_basics",
            "relay_contactor_control",
            "electrical_diagram_reading",
            "time_relay_sequence_control",
        ),
        "chapters": (
            {"title": "低压电器与控制角色", "topic_ids": ("control_power", "fuse", "thermal_relay", "button_contacts", "contactor_coil")},
            {"title": "基本控制电路", "topic_ids": ("jog_control", "self_hold", "forward_reverse", "electrical_interlock")},
            {"title": "控制图与逻辑追踪", "topic_ids": ("diagram_symbols", "series_logic", "parallel_logic", "logic_tracing")},
            {"title": "时间与顺序控制", "topic_ids": ("timer_role", "on_delay", "off_delay", "sequence_control")},
        ),
    },
}


def books_for_course(course_id: str) -> tuple[dict[str, Any], ...]:
    return tuple(book for book in BOOK_EDITION_MAPPINGS.values() if course_id in book["course_ids"])


def topics_for_book_chapter(book_id: str, chapter_index: int) -> tuple[dict[str, Any], ...]:
    book = BOOK_EDITION_MAPPINGS[book_id]
    chapter = book["chapters"][chapter_index]
    return tuple(KNOWLEDGE_TOPICS[topic_id] for topic_id in chapter["topic_ids"])


def validate_curriculum_catalog() -> None:
    course_ids = {course["id"] for course in COURSES}
    if any(not topic["course_ids"] for topic in KNOWLEDGE_TOPICS.values()):
        raise ValueError("存在未关联课程的统一知识点")
    for book_id, book in BOOK_EDITION_MAPPINGS.items():
        if not set(book["course_ids"]) <= course_ids or not book["chapters"]:
            raise ValueError(f"教材映射课程无效：{book_id}")
        topic_ids = [topic_id for chapter in book["chapters"] for topic_id in chapter["topic_ids"]]
        if len(topic_ids) != len(set(topic_ids)) or not set(topic_ids) <= set(KNOWLEDGE_TOPICS):
            raise ValueError(f"教材映射知识点无效：{book_id}")


validate_curriculum_catalog()
