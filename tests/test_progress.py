from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone

import pytest

from dianzhentong.progress import (
    calculate_experiment_progress,
    daily_task_status,
    learning_streak,
    learning_overview,
)
from dianzhentong.storage import (
    BEIJING_TZ,
    MemoryPracticeRepository,
    PracticeRecord,
    PracticeRepository,
    ResilientPracticeRepository,
    beijing_date_from_iso,
    make_learning_activity,
)


def practice(
    practice_id: str,
    scenario_id: str,
    matched: bool,
    moment: datetime,
    experiment_id: str = "motor_dol_no_start",
) -> PracticeRecord:
    return PracticeRecord(
        practice_id=practice_id,
        completed_at=moment.isoformat(),
        experiment_id=experiment_id,
        scenario_id=scenario_id,
        result_id=scenario_id if matched else "inconsistent",
        matched=matched,
        correct_judgments=int(matched),
        total_judgments=1,
        wrong_nodes=() if matched else ("fuse",),
        uncertain_count=0,
    )


def test_old_database_gets_activity_table_without_changing_practices(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE practice_records (
                practice_id TEXT PRIMARY KEY, completed_at TEXT NOT NULL,
                experiment_id TEXT NOT NULL, scenario_id TEXT NOT NULL,
                result_id TEXT NOT NULL, matched INTEGER NOT NULL,
                correct_judgments INTEGER NOT NULL, total_judgments INTEGER NOT NULL,
                wrong_nodes TEXT NOT NULL, uncertain_count INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            "INSERT INTO practice_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("old", "2026-08-29T00:00:00+08:00", "motor_dol_no_start", "cause_fuse", "cause_fuse", 1, 2, 2, "[]", 0),
        )
    first = PracticeRepository(path)
    second = PracticeRepository(path)
    assert first.summary()["attempts"] == second.summary()["attempts"] == 1
    with sqlite3.connect(path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "learning_activities" in tables


def test_learning_activity_ids_deduplicate_cards_and_guided_sessions(tmp_path):
    repository = PracticeRepository(tmp_path / "activity.db")
    card = make_learning_activity("motor_dol_no_start", "knowledge_card", "fuse")
    guided = make_learning_activity("motor_dol_no_start", "guided_session", "practice-1")
    assert repository.save_activity(card) is True
    assert repository.save_activity(card) is False
    assert repository.save_activity(guided) is True
    assert repository.save_activity(guided) is False
    assert repository.learned_cards("motor_dol_no_start") == {"fuse"}
    assert len(repository.activities("motor_dol_no_start")) == 2


def test_beijing_date_boundary_and_today_tasks(tmp_path):
    repository = PracticeRepository(tmp_path / "today.db")
    beijing_day = date(2026, 8, 30)
    # UTC 16:30 已是北京时间次日 00:30。
    moment = datetime(2026, 8, 29, 16, 30, tzinfo=timezone.utc)
    assert beijing_date_from_iso(moment.isoformat()) == beijing_day
    repository.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", "fuse", moment))
    repository.save_activity(make_learning_activity("motor_dol_no_start", "guided_session", "g1", moment))
    repository.save(practice("p1", "cause_fuse", True, moment))
    repository.save(practice("p2", "cause_fuse", False, moment + timedelta(minutes=1)))
    tasks = daily_task_status(repository, today=beijing_day)
    assert tasks["knowledge"] and tasks["guided"] and tasks["practice"]
    assert tasks["completed_count"] == 3
    assert tasks["completion"] == 1.0


def test_streak_uses_today_or_yesterday_grace():
    today = date(2026, 8, 30)
    assert learning_streak({today, today - timedelta(days=1)}, today) == 2
    assert learning_streak({today - timedelta(days=1), today - timedelta(days=2)}, today) == 2
    assert learning_streak({today - timedelta(days=2)}, today) == 0


def test_mastery_weights_status_and_beginner_route(tmp_path):
    repository = PracticeRepository(tmp_path / "mastery.db")
    experiment_id = "motor_dol_no_start"
    cards = ["control_power", "fuse"]
    scenarios = ["cause_control_power", "cause_fuse"]
    for card_id in cards:
        repository.save_activity(make_learning_activity(experiment_id, "knowledge_card", card_id))
    repository.save_activity(make_learning_activity(experiment_id, "guided_session", "guided-1"))
    moment = datetime(2026, 8, 29, tzinfo=BEIJING_TZ)
    for scenario_id in scenarios:
        repository.save(practice(f"{scenario_id}-1", scenario_id, True, moment))
        repository.save(practice(f"{scenario_id}-2", scenario_id, True, moment + timedelta(minutes=1)))
    progress = calculate_experiment_progress(repository, experiment_id, scenarios, cards)
    assert progress.mastery == pytest.approx(1.0)
    assert progress.status == "基本掌握"
    assert progress.route_stage == "路线已完成"
    assert progress.mastered_faults == 2


def test_zero_progress_and_global_recommendation_are_safe():
    repository = MemoryPracticeRepository()
    first = calculate_experiment_progress(repository, "a", ["f1"], ["c1"])
    second = calculate_experiment_progress(repository, "b", ["f2"], ["c2"])
    overview = learning_overview(repository, {"a": first, "b": second}, date(2026, 8, 29))
    assert first.mastery == 0
    assert first.status == "未开始"
    assert first.route_stage == "学习知识卡"
    assert overview["tasks"]["completed_count"] == 0
    assert overview["recommended_experiment_id"] == "a"


def test_all_cards_learned_completes_knowledge_task_without_duplicate_event():
    repository = MemoryPracticeRepository()
    tasks = daily_task_status(repository, all_cards_learned=True, today=date(2026, 8, 29))
    assert tasks["knowledge"] is True
    assert tasks["knowledge_cards"] == 0


def test_fault_requires_two_attempts_and_sixty_percent_accuracy(tmp_path):
    repository = PracticeRepository(tmp_path / "threshold.db")
    moment = datetime(2026, 8, 29, tzinfo=BEIJING_TZ)
    repository.save(practice("one", "fault", True, moment))
    first = calculate_experiment_progress(repository, "motor_dol_no_start", ["fault"], ["card"])
    assert first.mastered_faults == 0
    repository.save(practice("two", "fault", False, moment + timedelta(minutes=1)))
    second = calculate_experiment_progress(repository, "motor_dol_no_start", ["fault"], ["card"])
    assert second.mastered_faults == 0
    repository.save(practice("three", "fault", True, moment + timedelta(minutes=2)))
    third = calculate_experiment_progress(repository, "motor_dol_no_start", ["fault"], ["card"])
    assert third.mastered_faults == 1


def test_resilient_repository_keeps_learning_tasks_in_memory(tmp_path):
    invalid_path = tmp_path / "directory-not-database"
    invalid_path.mkdir()
    repository = ResilientPracticeRepository(invalid_path)
    assert repository.persistent is False
    activity = make_learning_activity("motor_dol_no_start", "knowledge_card", "fuse")
    assert repository.save_activity(activity) is True
    assert repository.learned_cards("motor_dol_no_start") == {"fuse"}
    assert repository.today_progress()["knowledge_cards"] == 1
