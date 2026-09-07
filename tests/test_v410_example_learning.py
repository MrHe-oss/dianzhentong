from pathlib import Path
from streamlit.testing.v1 import AppTest
from dianzhentong.textbook_examples import example_for_unit

BOOK = "electrical_control_plc_s71200_tong"


def test_example_requires_explicit_reveal_and_does_not_complete_learning(tmp_path, monkeypatch):
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "learning.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == "进入教材学习").click().run()
    app.selectbox(key="selected_textbook_chapter").set_value(3).run()
    example = example_for_unit(3, BOOK)
    assert not app.exception
    assert not any(example["answer"] in message.value for message in app.success)
    assert any("6 道题库练习" in message.value for message in app.caption)
    assert any("待完成" == m.value for m in app.metric if m.label == "例题练习 · 20%")
    app.checkbox(key=f"unit_reasoning_{BOOK}_3_hint").check().run()
    assert any(example["thinking_hint"] in message.value for message in app.info)
    app.checkbox(key=f"unit_reasoning_{BOOK}_3_solution").check().run()
    assert any(example["answer"] in message.value for message in app.success)
    assert any("待完成" == m.value for m in app.metric if m.label == "例题练习 · 20%")
    app.button(key="book_topic_plc_cpu").click().run()
    assert not any(example["answer"] in message.value for message in app.success)
    app.checkbox(key=f"lesson_reasoning_{BOOK}_3_plc_cpu_solution").check().run()
    assert any(example["answer"] in message.value for message in app.success)
    assert not app.exception
