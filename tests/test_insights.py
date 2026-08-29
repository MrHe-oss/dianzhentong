from __future__ import annotations

from pathlib import Path

from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.insights import RESULT_INSIGHTS, insight_for_result, validate_result_insights
from dianzhentong.report import build_report


def expected_fault_results() -> set[str]:
    result_ids: set[str] = set()
    for experiment_id in ("motor_dol_no_start", "motor_forward_reverse"):
        knowledge = KnowledgeBase(experiment_id)
        result_ids.update(knowledge.scenario_ids)
    return result_ids


def test_all_fourteen_faults_have_complete_learning_insights():
    expected = expected_fault_results()
    assert len(expected) == 14
    validate_result_insights(expected)
    assert set(RESULT_INSIGHTS) == expected


def test_insight_does_not_cover_inconclusive_result():
    assert insight_for_result("inconsistent") is None
    assert insight_for_result("fr_inconsistent") is None
    assert insight_for_result(None) is None


def test_download_report_contains_explanation_confusion_and_memory_tip():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    session.answer("正常")
    session.answer("异常")
    report = build_report(session)
    assert "为什么这样判断" in report
    assert "容易混淆" in report
    assert "记忆提示" in report


def test_ui_displays_learning_explanation_without_changing_fault_tree():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "学会这个故障" in source
    assert "insight_for_result(session.result_id)" in source
