from pathlib import Path


def test_textbook_topic_opens_independent_lesson_not_experiment_center():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "3.6"' in config
    assert 'UI_STATE_VERSION = "3.6"' in app
    assert "open_textbook_topic(selected_book_id, chapter_index, topic[\"id\"])" in app
    assert "elif stage == 24" in app
    for phrase in ("核心原理", "理解这个知识点", "正确理解", "常见误区", "学习小结", "返回本单元"):
        assert phrase in app


def test_textbook_lesson_keeps_training_language_out_of_primary_heading():
    app = Path("app.py").read_text(encoding="utf-8")
    assert "本页属于教材知识学习，不是故障诊断或真实设备操作指导" in app
    assert "st.dataframe" not in app and "st.table" not in app
