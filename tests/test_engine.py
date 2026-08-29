from __future__ import annotations

import pytest

from dianzhentong.engine import DiagnosticSession, KnowledgeBase, SessionError


@pytest.fixture(scope="module")
def knowledge() -> KnowledgeBase:
    return KnowledgeBase()


FAULT_CASES = [
    (0, "cause_control_power"),
    (1, "cause_fuse"),
    (2, "cause_thermal"),
    (3, "cause_stop"),
    (4, "cause_start"),
    (5, "cause_coil"),
]


def run_answers(knowledge: KnowledgeBase, answers: list[str]) -> DiagnosticSession:
    session = DiagnosticSession(knowledge)
    session.start(True)
    for answer in answers:
        session.answer(answer)
    return session


@pytest.mark.parametrize(("normal_count", "expected_result"), FAULT_CASES)
def test_six_standard_paths(knowledge, normal_count, expected_result):
    session = run_answers(knowledge, ["正常"] * normal_count + ["异常"])
    assert session.result_id == expected_result
    assert len(session.history) == normal_count + 1


@pytest.mark.parametrize(("normal_count", "expected_result"), FAULT_CASES)
def test_six_uncertain_then_resolved_paths(knowledge, normal_count, expected_result):
    session = run_answers(knowledge, ["正常"] * normal_count + ["不确定", "异常"])
    assert session.result_id == expected_result
    assert session.history[-2]["node_id"] == session.history[-1]["node_id"]
    assert session.history[-2]["answer"] == "不确定"


@pytest.mark.parametrize("normal_count", range(6))
def test_six_contradictory_paths_end_without_false_diagnosis(knowledge, normal_count):
    # 在目标节点先给出“不确定”，随后把所有限定检查都记为正常。
    answers = ["正常"] * normal_count + ["不确定"] + ["正常"] * (6 - normal_count)
    session = run_answers(knowledge, answers)
    assert session.result_id == "inconsistent"
    assert "不确定" in [item["answer"] for item in session.history]


def test_safety_confirmation_is_required(knowledge):
    session = DiagnosticSession(knowledge)
    with pytest.raises(SessionError):
        session.start(False)
    assert session.current_node is None


def test_back_replays_state_without_mixing_history(knowledge):
    session = run_answers(knowledge, ["正常", "正常", "不确定"])
    assert session.current_node_id == "thermal_relay"
    assert session.go_back() is True
    assert session.current_node_id == "thermal_relay"
    assert len(session.history) == 2
    assert session.eliminated == [
        "控制电源状态（模拟）",
        "控制回路熔断器（模拟）",
    ]


def test_session_round_trip(knowledge):
    original = run_answers(knowledge, ["正常", "不确定"])
    restored = DiagnosticSession.from_dict(knowledge, original.to_dict())
    assert restored.to_dict() == original.to_dict()

