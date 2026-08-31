from pathlib import Path


def test_v29_has_dashboard_navigation_and_responsive_visual_system():
    app = Path("app.py").read_text(encoding="utf-8")
    for phrase in (
        "今天继续学一点", "今日任务", "连续学习", "待复习",
        "📖 学习", "🧠 知识", "✍️ 练习", "🧰 实训", "📊 我的学习",
        "dzt-dashboard", "dzt-brandbar", "dzt-section-label",
    ):
        assert phrase in app
    assert "max-width:1040px" in app
    assert "@media(max-width:640px)" in app
    assert "st.columns(len(COURSES))" not in app
    assert "st.dataframe" not in app and "st.table" not in app


def test_v29_keeps_storage_schema_and_learning_content_unchanged():
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    backup = Path("dianzhentong/backup.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "3.0"' in config
    assert 'SCHEMA_VERSION = 3' in backup
