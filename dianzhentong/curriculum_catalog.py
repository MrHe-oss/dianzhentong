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


# 教材只用于公开目录与平台原创内容之间的索引；不收录教材正文、插图或课后题。
BOOK_EDITION_MAPPINGS: dict[str, dict[str, Any]] = {
    "electrical_control_plc_s71200_tong": {
        "id": "electrical_control_plc_s71200_tong",
        "title": "电气控制与PLC应用技术（S7-1200）",
        "edition": "第1版",
        "author": "童克波",
        "publisher": "机械工业出版社",
        "isbn": "978-7-111-73129-0",
        "published_at": "2023-07-24",
        "source_url": "https://www.cmpedu.com/books/book/5606823.htm",
        "official": False,
        "notice": "本学习映射由电诊通独立开发，属于非出版社官方配套内容，不是机械工业出版社或教材作者提供的资源。",
        "course_ids": (
            "low_voltage_control_basics",
            "relay_contactor_control",
            "electrical_diagram_reading",
            "star_delta_starting",
            "time_relay_sequence_control",
        ),
        "chapters": (
            {
                "source_title": "项目1·任务1 实现电动机的单向旋转",
                "title": "电动机单向旋转控制",
                "goal": "识别公共条件、操作请求、执行角色及点动和连续运行关系。",
                "topic_ids": ("control_power", "fuse", "thermal_relay", "button_contacts", "contactor_coil", "jog_control", "self_hold", "series_logic"),
                "case_ids": ("dol_roles", "jog_roles", "dol_series", "hold_parallel"),
                "experiment_ids": ("motor_dol_no_start", "motor_jog_continuous"),
                "quiz_chapter_ids": ("components", "direct_start", "jog_continuous_basics"),
            },
            {
                "source_title": "项目1·任务2 实现电动机的正反转控制",
                "title": "电动机正反转控制",
                "goal": "理解方向支路、公共条件和电气互锁的逻辑关系。",
                "topic_ids": ("forward_reverse", "electrical_interlock", "parallel_logic", "logic_tracing"),
                "case_ids": ("reverse_common", "reverse_branch"),
                "experiment_ids": ("motor_forward_reverse",),
                "quiz_chapter_ids": ("forward_reverse", "control_path_tracing"),
            },
            {
                "source_title": "项目1·任务3 实现电动机星—三角减压启动控制",
                "title": "星—三角减压启动控制",
                "goal": "理解启动目的、三个接触器角色、时间转换和互锁约束。",
                "topic_ids": ("star_delta_principle", "star_delta_components", "star_delta_timing", "star_delta_interlock", "timer_role", "on_delay"),
                "case_ids": ("sd_purpose", "sd_suitability", "sd_roles", "sd_timer", "sd_sequence", "sd_interlock"),
                "experiment_ids": tuple(),
                "quiz_chapter_ids": ("star_delta_principles", "star_delta_components", "star_delta_sequence"),
            },
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
        if not all(book.get(field) for field in ("title", "edition", "author", "publisher", "isbn", "source_url", "notice")):
            raise ValueError(f"教材元数据不完整：{book_id}")
        topic_ids = [topic_id for chapter in book["chapters"] for topic_id in chapter["topic_ids"]]
        if len(topic_ids) != len(set(topic_ids)) or not set(topic_ids) <= set(KNOWLEDGE_TOPICS):
            raise ValueError(f"教材映射知识点无效：{book_id}")
        if any(not all(chapter.get(field) for field in ("source_title", "title", "goal", "topic_ids", "case_ids", "quiz_chapter_ids"))
               for chapter in book["chapters"]):
            raise ValueError(f"教材章节映射不完整：{book_id}")


validate_curriculum_catalog()
