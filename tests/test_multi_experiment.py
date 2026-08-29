from __future__ import annotations

import sqlite3

import pytest

from dianzhentong.engine import (
    DEFAULT_EXPERIMENT_ID,
    DiagnosticSession,
    KnowledgeBase,
    SessionError,
)
from dianzhentong.report import build_report
from dianzhentong.storage import PracticeRepository


REVERSE_CASES = [
    "fr_cause_fuse",
    "fr_cause_thermal",
    "fr_cause_stop",
    "fr_cause_forward_button",
    "fr_cause_reverse_button",
    "fr_cause_forward_coil",
    "fr_cause_reverse_coil",
    "fr_cause_interlock",
]


def solve_scenario(knowledge: KnowledgeBase, scenario_id: str) -> DiagnosticSession:
    session = DiagnosticSession(knowledge)
    session.start(True, scenario_id=scenario_id)
    while not session.is_complete:
        session.answer(session.expected_answer or "不确定")
    return session


def test_catalog_contains_two_experiments():
    catalog = KnowledgeBase.catalog()
    assert set(catalog) == {"motor_dol_no_start", "motor_forward_reverse"}


@pytest.mark.parametrize("scenario_id", REVERSE_CASES)
def test_all_forward_reverse_scenarios_have_unique_solvable_paths(scenario_id):
    knowledge = KnowledgeBase("motor_forward_reverse")
    session = solve_scenario(knowledge, scenario_id)
    assert session.result_id == scenario_id
    assert session.scenario_result["symptom_id"] == session.symptom_id
    assert all(item["is_correct"] is True for item in session.history)
    path = session.recommended_path()
    assert path is not None
    assert path["result_id"] == scenario_id
    assert [step["node_id"] for step in path["steps"]] == [
        item["node_id"] for item in session.history
    ]


@pytest.mark.parametrize("scenario_id", REVERSE_CASES)
def test_forward_reverse_uncertain_can_resume(scenario_id):
    knowledge = KnowledgeBase("motor_forward_reverse")
    session = DiagnosticSession(knowledge)
    session.start(True, scenario_id=scenario_id)
    first_node = session.current_node_id
    session.answer("不确定")
    assert session.current_node_id == first_node
    while not session.is_complete:
        session.answer(session.expected_answer or "不确定")
    assert session.result_id == scenario_id
    assert session.uncertain_count == 1


def test_direction_specific_paths_skip_unrelated_branch():
    knowledge = KnowledgeBase("motor_forward_reverse")
    forward = solve_scenario(knowledge, "fr_cause_forward_coil")
    reverse = solve_scenario(knowledge, "fr_cause_reverse_coil")
    forward_nodes = {item["node_id"] for item in forward.history}
    reverse_nodes = {item["node_id"] for item in reverse.history}
    assert "fr_reverse_button" not in forward_nodes
    assert "fr_reverse_coil" not in forward_nodes
    assert "fr_forward_button" not in reverse_nodes
    assert "fr_forward_coil" not in reverse_nodes
    assert "fr_interlock" not in reverse_nodes


@pytest.mark.parametrize(
    ("scenario_id", "expected_symptom"),
    [
        ("fr_cause_fuse", "正转和反转两个方向均不能启动"),
        ("fr_cause_forward_button", "正转不能启动，反转功能正常"),
        ("fr_cause_reverse_button", "反转不能启动，正转功能正常"),
    ],
)
def test_scenario_selects_correct_symptom(scenario_id, expected_symptom):
    session = DiagnosticSession(KnowledgeBase("motor_forward_reverse"))
    session.start(True, scenario_id=scenario_id)
    assert session.symptom == expected_symptom


def test_free_reverse_diagnosis_uses_selected_symptom_and_ends_safely():
    session = DiagnosticSession(KnowledgeBase("motor_forward_reverse"))
    session.start(True, symptom_id="reverse_no_start")
    while not session.is_complete:
        session.answer("正常")
    assert session.result_id == "fr_inconsistent"
    assert {item["node_id"] for item in session.history} == {
        "fr_fuse", "fr_thermal", "fr_stop", "fr_reverse_button", "fr_reverse_coil"
    }


def test_session_state_records_experiment_and_rejects_wrong_loader():
    state = DiagnosticSession(KnowledgeBase("motor_forward_reverse"))
    state.start(True, scenario_id="fr_cause_fuse")
    payload = state.to_dict()
    assert payload["experiment_id"] == "motor_forward_reverse"
    with pytest.raises(SessionError):
        DiagnosticSession.from_dict(KnowledgeBase(), payload)


def test_legacy_session_defaults_to_direct_start():
    knowledge = KnowledgeBase()
    original = DiagnosticSession(knowledge)
    original.start(True)
    payload = original.to_dict()
    payload.pop("experiment_id")
    payload.pop("symptom_id")
    restored = DiagnosticSession.from_dict(knowledge, payload)
    assert restored.experiment_id == DEFAULT_EXPERIMENT_ID
    assert restored.symptom_id == "no_start"


def test_report_names_experiment_and_scenario_symptom():
    session = solve_scenario(KnowledgeBase("motor_forward_reverse"), "fr_cause_forward_button")
    report = build_report(session)
    assert "实验：三相异步电动机正反转控制" in report
    assert "故障现象：正转不能启动，反转功能正常" in report


def test_legacy_database_migration_preserves_rows_and_is_repeatable(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE practice_records (
                practice_id TEXT PRIMARY KEY, completed_at TEXT NOT NULL,
                scenario_id TEXT NOT NULL, result_id TEXT NOT NULL,
                matched INTEGER NOT NULL, correct_judgments INTEGER NOT NULL,
                total_judgments INTEGER NOT NULL, wrong_nodes TEXT NOT NULL,
                uncertain_count INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO practice_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("legacy", "2026-01-01T00:00:00", "cause_fuse", "cause_fuse", 1, 2, 2, "[]", 0),
        )
    first = PracticeRepository(path)
    second = PracticeRepository(path)
    assert first.summary()["attempts"] == 1
    assert second.summary(experiment_id=DEFAULT_EXPERIMENT_ID)["attempts"] == 1
    assert second.recent(10)[0]["experiment_id"] == DEFAULT_EXPERIMENT_ID


def test_statistics_are_isolated_by_experiment(tmp_path):
    repository = PracticeRepository(tmp_path / "stats.db")
    direct = solve_scenario(KnowledgeBase(), "cause_fuse").to_practice_record("2026-01-01T00:00:00")
    reverse = solve_scenario(
        KnowledgeBase("motor_forward_reverse"), "fr_cause_fuse"
    ).to_practice_record("2026-01-02T00:00:00")
    repository.save(direct)
    repository.save(reverse)
    assert repository.summary()["attempts"] == 2
    assert repository.summary(experiment_id=DEFAULT_EXPERIMENT_ID)["attempts"] == 1
    assert repository.summary(experiment_id="motor_forward_reverse")["attempts"] == 1
