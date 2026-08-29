from __future__ import annotations

import pytest

from dianzhentong.engine import DiagnosticSession, KnowledgeBase, SessionError
from dianzhentong.report import build_report


SCENARIOS = [
    ("cause_control_power", 0),
    ("cause_fuse", 1),
    ("cause_thermal", 2),
    ("cause_stop", 3),
    ("cause_start", 4),
    ("cause_coil", 5),
]


@pytest.mark.parametrize(("scenario_id", "normal_count"), SCENARIOS)
def test_six_practice_scenarios_can_be_solved(scenario_id, normal_count):
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id=scenario_id)
    for _ in range(normal_count):
        assert session.expected_answer == "正常"
        assert session.scenario_observation
        session.answer("正常")
    assert session.expected_answer == "异常"
    session.answer("异常")
    assert session.result_id == scenario_id
    assert session.score == (normal_count + 1, normal_count + 1)


def test_wrong_practice_answer_is_scored_and_never_relabels_scenario():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    session.answer("异常")
    assert session.result_id == "cause_control_power"
    assert session.scenario_id == "cause_fuse"
    assert session.score == (0, 1)


def test_uncertain_is_recorded_but_not_scored():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_control_power")
    session.answer("不确定")
    assert session.current_node_id == "control_power"
    assert session.score == (0, 0)
    session.answer("异常")
    assert session.score == (1, 1)


def test_back_preserves_hidden_scenario_and_recalculates_score():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_thermal")
    session.answer("正常")
    session.answer("正常")
    assert session.score == (2, 2)
    session.go_back()
    assert session.scenario_id == "cause_thermal"
    assert session.score == (1, 1)
    assert session.current_node_id == "fuse"


def test_practice_report_includes_answer_and_score():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_control_power")
    session.answer("异常")
    report = build_report(session)
    assert "练习预设故障：模拟控制电源缺失" in report
    assert "诊断是否匹配：是" in report
    assert "有效判断得分：1/1" in report


def test_invalid_scenario_is_rejected():
    session = DiagnosticSession(KnowledgeBase())
    with pytest.raises(SessionError):
        session.start(True, scenario_id="unknown")

