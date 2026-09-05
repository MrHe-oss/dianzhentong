from pathlib import Path

from dianzhentong.quiz import QuizAnswer, make_quiz_record


def _answers(correct: int, total: int):
    return tuple(QuizAnswer(f"q{i}", "A", "A", i < correct, False) for i in range(total))


def test_pretest_is_saved_as_distinct_non_mastery_mode():
    record = make_quiz_record("components", _answers(1, 3), "textbook_unit_pretest")
    assert record.mode == "textbook_unit_pretest"
    post = make_quiz_record("components", _answers(4, 5), "textbook_unit_assessment")
    assert post.mode == "textbook_unit_assessment" and post.passed


def test_v39_has_pre_post_comparison_and_direct_textbook_review():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.7"' in config and 'UI_STATE_VERSION = "4.7"' in app
    for phrase in ("开始学前小测", "学前小测报告", "学习起点记录", "开始学后评测", "学习效果", "返回教材复习薄弱知识点"):
        assert phrase in app
    assert '"mode": "textbook_unit_pretest" if pretest else "textbook_unit_assessment"' in app
