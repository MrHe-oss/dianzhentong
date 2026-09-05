from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository
from dianzhentong.textbook_discovery import build_textbook_index, search_textbooks


BOOK_ID = "electrical_control_plc_s71200_tong"


def test_textbook_index_searches_units_topics_formulas_and_examples():
    index = build_textbook_index([BOOK_ID])
    assert {item["kind"] for item in index} >= {"教材", "单元", "知识点", "原创例题"}
    assert search_textbooks(index, "接触器")
    assert search_textbooks(index, "原创例题")
    assert search_textbooks(index, "不存在的电气词") == ()


def test_memory_bookmarks_toggle_and_recent_visits_are_deduplicated():
    repository = MemoryPracticeRepository()
    assert repository.toggle_textbook_bookmark(BOOK_ID, "control_power") is True
    assert repository.textbook_bookmarks()[0]["topic_id"] == "control_power"
    assert repository.toggle_textbook_bookmark(BOOK_ID, "control_power") is False
    assert repository.textbook_bookmarks() == []
    repository.record_textbook_visit(BOOK_ID, 0, "control_power")
    repository.record_textbook_visit(BOOK_ID, 1, "control_power")
    visits = repository.recent_textbook_visits()
    assert len(visits) == 1 and visits[0]["chapter_index"] == 1


def test_sqlite_bookmarks_and_visits_survive_restart(tmp_path):
    path = tmp_path / "practice.db"
    first = PracticeRepository(path)
    first.toggle_textbook_bookmark(BOOK_ID, "fuse")
    first.record_textbook_visit(BOOK_ID, 0, "fuse")
    second = PracticeRepository(path)
    assert second.textbook_bookmarks()[0]["topic_id"] == "fuse"
    assert second.recent_textbook_visits()[0]["topic_id"] == "fuse"


def test_v41_ui_has_bookshelf_search_bookmarks_and_recent_learning():
    app = open("app.py", encoding="utf-8").read()
    config = open("dianzhentong/config.py", encoding="utf-8").read()
    assert 'APP_VERSION = "4.7"' in config and 'UI_STATE_VERSION = "4.7"' in app
    for phrase in ("我的教材书架", "搜索学习内容", "我的收藏", "最近学习", "收藏知识点"):
        assert phrase in app
