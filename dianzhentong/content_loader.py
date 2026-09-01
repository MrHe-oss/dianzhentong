"""结构化教材内容的加载与完整性校验。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CONTENT_ROOT = Path(__file__).resolve().parent / "content" / "textbooks"
LESSON_FIELDS = {"minutes", "lead", "points", "example", "question", "options", "answer", "explanation"}
UNIT_FIELDS = {"id", "source_title", "title", "goal", "topic_ids", "case_ids", "experiment_ids", "quiz_chapter_ids", "topics", "worked_example"}


class ContentValidationError(ValueError):
    """教材内容文件不完整或引用关系无效。"""


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_textbook_content(data: dict[str, Any]) -> None:
    if data.get("schema_version") != 1:
        raise ContentValidationError("不支持的教材内容版本")
    book, project = data.get("book", {}), data.get("project", {})
    required_book = ("id", "title", "edition", "author", "publisher", "isbn", "published_at", "source_url", "notice")
    if not all(_nonempty(book.get(field)) for field in required_book):
        raise ContentValidationError("教材元数据不完整")
    source = urlparse(book["source_url"])
    if source.scheme != "https" or not source.netloc or source.username or source.password:
        raise ContentValidationError("教材来源链接必须是无账号信息的HTTPS地址")
    units = project.get("units")
    if not _nonempty(project.get("id")) or not _nonempty(project.get("title")) or not isinstance(units, list) or not units:
        raise ContentValidationError("教材项目或单元缺失")
    seen_topics: set[str] = set()
    for unit in units:
        if not UNIT_FIELDS <= set(unit) or not all(unit.get(field) for field in ("topic_ids", "case_ids", "quiz_chapter_ids")):
            raise ContentValidationError("教材单元结构不完整")
        topic_ids = unit["topic_ids"]
        topic_items = unit["topics"]
        if len(topic_ids) != len(set(topic_ids)) or [item.get("id") for item in topic_items] != topic_ids:
            raise ContentValidationError("单元知识点顺序或身份不一致")
        if seen_topics & set(topic_ids):
            raise ContentValidationError("知识点不能重复属于多个教材单元")
        seen_topics.update(topic_ids)
        for topic in topic_items:
            lesson = topic.get("lesson", {})
            if not LESSON_FIELDS <= set(lesson) or lesson.get("answer") not in lesson.get("options", []):
                raise ContentValidationError(f"知识小课结构无效：{topic.get('id', 'unknown')}")
            if len(lesson["points"]) < 3 or not 1 <= int(lesson["minutes"]) <= 20:
                raise ContentValidationError(f"知识小课时长或要点无效：{topic['id']}")
            for formula in topic.get("formulas", []):
                if not all(formula.get(field) for field in ("title", "expression", "symbols", "meaning")):
                    raise ContentValidationError(f"公式结构无效：{topic['id']}")
        example = unit["worked_example"]
        if example.get("practice_answer") not in example.get("options", []) or len(example.get("steps", [])) < 3:
            raise ContentValidationError(f"原创例题结构无效：{unit['id']}")


@lru_cache(maxsize=16)
def load_textbook_content(book_id: str) -> dict[str, Any]:
    if not book_id or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for character in book_id):
        raise ContentValidationError("教材ID格式无效")
    path = CONTENT_ROOT / book_id / "project1.json"
    if not path.is_file():
        raise ContentValidationError(f"教材内容不存在：{book_id}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentValidationError(f"教材内容无法读取：{book_id}") from error
    validate_textbook_content(data)
    return data
