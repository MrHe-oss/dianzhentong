from pathlib import Path

from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.textbook_learning import ALL_LESSON_TOPIC_IDS, TEXTBOOK_LESSONS


def test_all_three_textbook_units_have_complete_lessons():
    book = next(iter(BOOK_EDITION_MAPPINGS.values()))
    mapped_ids = {topic_id for unit in book["chapters"] for topic_id in unit["topic_ids"]}
    assert mapped_ids == set(ALL_LESSON_TOPIC_IDS) == set(TEXTBOOK_LESSONS)
    assert len(TEXTBOOK_LESSONS) == 30
    for unit in book["chapters"]:
        assert sum(TEXTBOOK_LESSONS[item]["minutes"] for item in unit["topic_ids"]) >= 12


def test_v36_shows_unit_progress_and_project_summary():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.4"' in config and 'UI_STATE_VERSION = "4.4"' in app
    for phrase in ("教材项目学习进度", "教材知识学习", "当前上线教材项目的知识小课已完成", "selected_textbook_chapter"):
        assert phrase in app
