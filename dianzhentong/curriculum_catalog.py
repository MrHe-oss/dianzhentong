"""学习平台的课程、统一知识点与教材版本映射结构。"""
from __future__ import annotations

from typing import Any

from .course import COURSE_CHAPTERS, COURSES
from .content_loader import load_textbook_projects
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


# 教材映射来自结构化内容文件；不收录教材正文、插图或课后题。
_TEXTBOOK_PROJECTS = load_textbook_projects("electrical_control_plc_s71200_tong")
_TEXTBOOK_CONTENT = _TEXTBOOK_PROJECTS[0]
_BOOK = _TEXTBOOK_CONTENT["book"]
BOOK_EDITION_MAPPINGS: dict[str, dict[str, Any]] = {
    _BOOK["id"]: {
        **_BOOK,
        "course_ids": tuple(_BOOK["course_ids"]),
        "projects": tuple({"id": item["project"]["id"], "title": item["project"]["title"]}
                          for item in _TEXTBOOK_PROJECTS),
        "chapters": tuple({
            **{key: tuple(value) if key in {"topic_ids", "case_ids", "experiment_ids", "quiz_chapter_ids"} else value
               for key, value in unit.items() if key not in {"id", "topics"}},
            "project_id": content["project"]["id"], "project_title": content["project"]["title"],
        } for content in _TEXTBOOK_PROJECTS for unit in content["project"]["units"]),
    }
}


def books_for_course(course_id: str) -> tuple[dict[str, Any], ...]:
    return tuple(book for book in BOOK_EDITION_MAPPINGS.values() if course_id in book["course_ids"])


def topics_for_book_chapter(book_id: str, chapter_index: int) -> tuple[dict[str, Any], ...]:
    book = BOOK_EDITION_MAPPINGS[book_id]
    chapter = book["chapters"][chapter_index]
    return tuple(KNOWLEDGE_TOPICS[topic_id] for topic_id in chapter["topic_ids"])


def validate_curriculum_catalog() -> None:
    course_ids = {course["id"] for course in COURSES}
    for book_id, book in BOOK_EDITION_MAPPINGS.items():
        if not set(book["course_ids"]) <= course_ids or not book["chapters"]:
            raise ValueError(f"教材映射课程无效：{book_id}")
        if not all(book.get(field) for field in ("title", "edition", "author", "publisher", "isbn", "source_url", "notice")):
            raise ValueError(f"教材元数据不完整：{book_id}")
        topic_ids = [topic_id for chapter in book["chapters"] for topic_id in chapter["topic_ids"]]
        if len(topic_ids) != len(set(topic_ids)) or not set(topic_ids) <= set(KNOWLEDGE_TOPICS):
            raise ValueError(f"教材映射知识点无效：{book_id}")
        if any(not all(chapter.get(field) for field in ("source_title", "title", "goal", "topic_ids"))
               for chapter in book["chapters"]):
            raise ValueError(f"教材章节映射不完整：{book_id}")


validate_curriculum_catalog()
