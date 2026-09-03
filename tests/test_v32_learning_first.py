from pathlib import Path


def test_v32_makes_textbook_learning_the_primary_entry():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.5"' in config
    assert 'UI_STATE_VERSION = "4.5"' in app
    for phrase in (
        "从教材开始学习", "进入教材目录", "教材知识点进度",
        "配套课程与知识路线", "实训与诊断为辅助学习工具",
        "电气专业教材学习平台",
    ):
        assert phrase in app


def test_v32_preserves_training_and_diagnosis_as_supporting_tools():
    app = Path("app.py").read_text(encoding="utf-8")
    assert "虚拟实训中心" in app
    assert "故障诊断模拟" in app
    assert "诊断功能是虚拟实训的一部分，不是平台的主学习入口" in app
    assert "st.dataframe" not in app and "st.table" not in app
