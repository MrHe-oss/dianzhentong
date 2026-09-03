from pathlib import Path

from dianzhentong.textbook_learning import SAMPLE_UNIT_TOPIC_IDS, TEXTBOOK_LESSONS, lesson_for_topic


def test_sample_unit_has_eight_complete_micro_lessons():
    assert set(SAMPLE_UNIT_TOPIC_IDS) <= set(TEXTBOOK_LESSONS)
    assert sum(TEXTBOOK_LESSONS[item]["minutes"] for item in SAMPLE_UNIT_TOPIC_IDS) >= 25
    for topic_id in SAMPLE_UNIT_TOPIC_IDS:
        lesson = lesson_for_topic(topic_id)
        assert lesson and len(lesson["points"]) >= 3
        assert len(lesson["options"]) == 3 and lesson["answer"] in lesson["options"]


def test_sample_unit_ui_has_orientation_checks_and_continuous_navigation():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.4.1"' in config and 'UI_STATE_VERSION = "4.4"' in app
    for phrase in ("预计学习", "开始本单元学习", "继续本单元学习", "本节要点", "即时检查", "下一个知识点"):
        assert phrase in app
    assert "完成即时检查后即可记录本节进度" in app
