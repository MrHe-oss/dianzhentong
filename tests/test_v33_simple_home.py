from pathlib import Path


def test_v33_home_has_one_primary_and_three_clear_supporting_entries():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.2"' in config
    assert 'UI_STATE_VERSION = "4.2"' in app
    for phrase in (
        "今天想学什么？", "进入教材学习", "继续上次学习",
        "🗺️ 课程路线", "✍️ 练习复习", "🧰 实训诊断",
    ):
        assert phrase in app
    assert "elif stage == 23" in app


def test_diagnostic_step_progress_is_not_rendered_on_home():
    app = Path("app.py").read_text(encoding="utf-8")
    assert "if stage in {2, 3, 4}:" in app
    assert "if stage <= 4:" not in app
    assert "st.dataframe" not in app and "st.table" not in app
