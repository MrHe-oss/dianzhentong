from pathlib import Path
from streamlit.testing.v1 import AppTest
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.storage import PracticeRepository
from dianzhentong.textbook_discovery import build_textbook_index, search_textbooks

BOOK = "electrical_control_plc_s71200_tong"


def test_search_has_readable_topic_titles():
    entries = build_textbook_index([BOOK])
    for entry in entries:
        if entry["kind"] == "知识点":
            assert entry["title"] != entry["topic_id"]
            assert entry in search_textbooks(entries, entry["title"], limit=100)


def test_home_search_and_lesson_navigation(tmp_path, monkeypatch):
    db = tmp_path / "learning.db"
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(db))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.text_input(key="home_search").set_value("PLC").run()
    assert not app.exception and any(b.key and b.key.startswith("home_result_") for b in app.button)
    unit = BOOK_EDITION_MAPPINGS[BOOK]["chapters"][4]
    app.session_state["stage"] = 24
    app.session_state["textbook_context"] = {"book_id": BOOK, "chapter_index": 4, "topic_id": unit["topic_ids"][0]}
    app.run()
    next(b for b in app.button if b.label == "下一个知识点").click().run()
    repo = PracticeRepository(db)
    assert repo.recent_textbook_visits(1)[0]["topic_id"] == unit["topic_ids"][1]
    app.button(key=f"lesson_directory_{unit['topic_ids'][-1]}").click().run()
    assert not app.exception
    assert app.button(key="lesson_unit_assessment")
    assert app.button(key="lesson_lab_logic")
    next(b for b in app.button if b.label == "返回本单元").click().run()
    assert not app.exception
    assert app.session_state["selected_textbook_chapter"] == 4
