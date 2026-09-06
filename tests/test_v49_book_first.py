from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_book_scoped_search_and_supplement_navigation(tmp_path, monkeypatch):
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "book.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    assert len(app.selectbox(key="home_book_selection").options) == 1
    app.text_input(key="home_search").set_value("欧姆定律").run()
    assert not any(b.key and b.key.startswith("home_result_") for b in app.button)
    app.button(key="supplement_circuit_foundations").click().run()
    app.text_input(key="textbook_search_query").set_value("欧姆定律").run()
    assert any(b.key and b.key.startswith("search_open_") for b in app.button)
    app.selectbox(key="selected_textbook_id").set_value("electrical_control_plc_s71200_tong").run()
    assert not app.exception
    assert not any(b.key and b.key.startswith("search_open_") for b in app.button)
    app.text_input(key="textbook_search_query").set_value("").run()
    app.selectbox(key="selected_textbook_chapter").set_value(4).run()
    next(b for b in app.button if b.label == "开始本单元学习").click().run()
    assert app.session_state["textbook_context"]["chapter_index"] == 4
    next(b for b in app.button if b.label == "返回本单元").click().run()
    assert not app.exception
    assert app.session_state["selected_textbook_chapter"] == 4
