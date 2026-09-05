from pathlib import Path

from dianzhentong.course import COURSES
from dianzhentong.curriculum_catalog import (
    BOOK_EDITION_MAPPINGS, KNOWLEDGE_TOPICS, LEARNING_DOMAINS,
    books_for_course, topics_for_book_chapter,
)
from dianzhentong.learning import KNOWLEDGE_CARDS


def test_learning_platform_has_courses_topics_and_safe_book_mapping():
    assert len(LEARNING_DOMAINS) == 4
    assert set(KNOWLEDGE_TOPICS) == set(KNOWLEDGE_CARDS)
    assert BOOK_EDITION_MAPPINGS
    course_ids = {course["id"] for course in COURSES}
    for book in BOOK_EDITION_MAPPINGS.values():
        assert set(book["course_ids"]) <= course_ids
        assert book["official"] is False
        assert "非出版社官方" in book["notice"]
        assert not book["isbn"] if book.get("kind") == "original" else book["isbn"]
        for index, chapter in enumerate(book["chapters"]):
            topics = topics_for_book_chapter(book["id"], index)
            assert topics and {item["id"] for item in topics} == set(chapter["topic_ids"])
    assert books_for_course("relay_contactor_control")


def test_v30_navigation_separates_learning_practice_and_training():
    app = Path("app.py").read_text(encoding="utf-8")
    for phrase in (
        "按教材学习", "练习中心", "虚拟实训中心",
        "故障诊断是实训方式之一", "诊断功能是虚拟实训的一部分",
        "🏠 学习首页", "📚 教材中心", "🧠 知识", "✍️ 练习", "🧰 实训", "📊 我的学习",
    ):
        assert phrase in app
    assert "BOOK_EDITION_MAPPINGS" in app and "topics_for_book_chapter" in app
    assert "stage == 20" in app and "stage == 21" in app and "stage == 22" in app
    assert "st.dataframe" not in app and "st.table" not in app


def test_v30_does_not_change_archive_schema_or_add_identity_collection():
    backup = Path("dianzhentong/backup.py").read_text(encoding="utf-8")
    catalog = Path("dianzhentong/curriculum_catalog.py").read_text(encoding="utf-8")
    assert "SCHEMA_VERSION = 3" in backup
    for forbidden in ("教材正文", "扫描图片", "课后题"):
        assert forbidden not in str(BOOK_EDITION_MAPPINGS)
    assert "身份证" not in catalog and "手机号" not in catalog
