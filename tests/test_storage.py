from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from dianzhentong.engine import DiagnosticSession, KnowledgeBase, SessionError
from dianzhentong.storage import PracticeRecord, PracticeRepository, choose_weak_scenario


@pytest.fixture
def repository(tmp_path) -> PracticeRepository:
    return PracticeRepository(tmp_path / "nested" / "practice.db")


def record(
    practice_id: str,
    scenario_id: str = "cause_fuse",
    *,
    matched: bool = True,
    correct: int = 2,
    total: int = 2,
    seconds: int = 0,
) -> PracticeRecord:
    moment = datetime(2026, 8, 29, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return PracticeRecord(
        practice_id=practice_id,
        completed_at=moment.isoformat(),
        experiment_id="motor_dol_no_start",
        scenario_id=scenario_id,
        result_id=scenario_id if matched else "cause_control_power",
        matched=matched,
        correct_judgments=correct,
        total_judgments=total,
        wrong_nodes=() if matched else ("control_power",),
        uncertain_count=0,
    )


def test_database_is_created_and_persists_across_repository_instances(tmp_path):
    path = tmp_path / "data" / "records.db"
    first = PracticeRepository(path)
    assert path.exists()
    assert first.save(record("one")) is True
    second = PracticeRepository(path)
    assert second.summary()["attempts"] == 1


def test_duplicate_practice_id_is_ignored(repository):
    item = record("same-id")
    assert repository.save(item) is True
    assert repository.save(item) is False
    assert repository.summary()["attempts"] == 1


def test_summary_uses_distinct_diagnosis_and_judgment_denominators(repository):
    repository.save(record("one", matched=True, correct=2, total=2, seconds=1))
    repository.save(record("two", matched=False, correct=1, total=3, seconds=2))
    repository.save(record("three", matched=True, correct=0, total=0, seconds=3))
    summary = repository.summary()
    assert summary["attempts"] == 3
    assert summary["diagnosis_accuracy"] == pytest.approx(2 / 3)
    assert summary["judgment_accuracy"] == pytest.approx(3 / 5)
    assert summary["current_streak"] == 1


def test_empty_summary_has_no_division_error(repository):
    summary = repository.summary()
    assert summary["attempts"] == 0
    assert summary["diagnosis_accuracy"] is None
    assert summary["judgment_accuracy"] is None
    assert summary["current_streak"] == 0


def test_fault_stats_include_unpracticed_scenarios(repository):
    repository.save(record("one", scenario_id="cause_fuse"))
    stats = repository.fault_stats(["cause_fuse", "cause_coil"])
    assert stats["cause_fuse"] == {"attempts": 1, "correct": 1, "accuracy": 1.0}
    assert stats["cause_coil"] == {"attempts": 0, "correct": 0, "accuracy": None}


def test_recent_is_reverse_chronological_and_limited(repository):
    for index in range(12):
        repository.save(record(str(index), seconds=index))
    recent = repository.recent(10)
    assert len(recent) == 10
    assert recent[0]["practice_id"] == "11"
    assert recent[-1]["practice_id"] == "2"


def test_clear_requires_confirmation(repository):
    repository.save(record("one"))
    assert repository.clear(confirmed=False) == 0
    assert repository.summary()["attempts"] == 1
    assert repository.clear(confirmed=True) == 1
    assert repository.summary()["attempts"] == 0


def test_no_data_uses_uniform_candidate_list():
    captured = []

    def choose(items):
        captured.extend(items)
        return items[-1]

    result = choose_weak_scenario({}, ["a", "b", "c"], chooser=choose)
    assert result == "c"
    assert captured == ["a", "b", "c"]


def test_weak_selector_prioritizes_never_correct_then_error_rate():
    stats = {
        "never": {"attempts": 2, "correct": 0, "accuracy": 0.0},
        "weak": {"attempts": 10, "correct": 2, "accuracy": 0.2},
        "strong": {"attempts": 10, "correct": 9, "accuracy": 0.9},
    }
    assert choose_weak_scenario(stats, list(stats), chooser=lambda items: items[0]) == "never"


def test_completed_practice_exports_full_record():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    practice_id = session.practice_id
    session.answer("正常")
    session.answer("不确定")
    session.answer("异常")
    exported = session.to_practice_record("2026-08-29T12:00:00+08:00")
    assert exported.practice_id == practice_id
    assert exported.matched is True
    assert exported.correct_judgments == 2
    assert exported.total_judgments == 2
    assert exported.uncertain_count == 1
    assert exported.wrong_nodes == ()


def test_free_diagnosis_cannot_export_or_enter_statistics():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True)
    session.answer("异常")
    with pytest.raises(SessionError):
        session.to_practice_record()


def test_wrong_nodes_are_exported():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    session.answer("异常")
    exported = session.to_practice_record("2026-08-29T12:00:00+08:00")
    assert exported.matched is False
    assert exported.wrong_nodes == ("control_power",)
