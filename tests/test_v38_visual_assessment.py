from pathlib import Path

from dianzhentong.quiz import QuizAnswer, make_quiz_record
from dianzhentong.textbook_learning import SAMPLE_UNIT_TOPIC_IDS
from dianzhentong.textbook_visuals import SELF_HOLD_STATES, TOPIC_VISUALS, visual_for_topic


def test_sample_unit_has_safe_abstract_visuals_and_state_demo():
    assert set(TOPIC_VISUALS) == set(SAMPLE_UNIT_TOPIC_IDS)
    assert len(SELF_HOLD_STATES) == 5
    for topic_id in SAMPLE_UNIT_TOPIC_IDS:
        visual = visual_for_topic(topic_id)
        assert visual and len(visual["nodes"]) >= 3 and visual["caption"]


def test_textbook_unit_assessment_uses_seventy_percent_threshold():
    answers = tuple(QuizAnswer(f"q{i}", "A", "A", i < 3, False) for i in range(5))
    assert make_quiz_record("direct_start", answers, "textbook_unit_assessment").passed is False
    answers = tuple(QuizAnswer(f"q{i}", "A", "A", i < 4, False) for i in range(5))
    assert make_quiz_record("direct_start", answers, "textbook_unit_assessment").passed is True


def test_v38_ui_has_visuals_assessment_and_mastery_states():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.2"' in config and 'UI_STATE_VERSION = "4.2"' in app
    for phrase in ("原理图解", "查看自锁状态变化演示", "开始学后评测", "单元评测报告", "基本掌握", "待识图巩固"):
        assert phrase in app
    assert "图中只表达抽象关系，不是接线图" in app


def test_opening_topic_does_not_mutate_instantiated_chapter_widget():
    app = Path("app.py").read_text(encoding="utf-8")
    helper = app.split("def open_textbook_topic", 1)[1].split("def progress_map", 1)[0]
    assert "selected_textbook_chapter" not in helper
