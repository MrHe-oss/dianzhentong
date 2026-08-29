"""本地练习记录、统计和薄弱项选择。"""

from __future__ import annotations

import json
import os
import secrets
import sqlite3
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Sequence
from zoneinfo import ZoneInfo


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "practice.db"
BEIJING_TZ = ZoneInfo("Asia/Shanghai")
ACTIVITY_TYPES = {"knowledge_card", "guided_session"}


@dataclass(frozen=True)
class PracticeRecord:
    practice_id: str
    completed_at: str
    experiment_id: str
    scenario_id: str
    result_id: str
    matched: bool
    correct_judgments: int
    total_judgments: int
    wrong_nodes: tuple[str, ...]
    uncertain_count: int

    def as_row(self) -> dict[str, Any]:
        row = asdict(self)
        row["matched"] = int(self.matched)
        row["wrong_nodes"] = json.dumps(self.wrong_nodes, ensure_ascii=False)
        return row


@dataclass(frozen=True)
class LearningActivity:
    activity_id: str
    occurred_at: str
    local_date: str
    experiment_id: str
    activity_type: str
    reference_id: str

    def __post_init__(self) -> None:
        if self.activity_type not in ACTIVITY_TYPES:
            raise ValueError(f"未知学习活动类型：{self.activity_type}")

    def as_row(self) -> dict[str, str]:
        return asdict(self)


def beijing_now() -> datetime:
    return datetime.now(BEIJING_TZ)


def beijing_date_from_iso(value: str) -> date:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(BEIJING_TZ).date()


def make_learning_activity(
    experiment_id: str,
    activity_type: str,
    reference_id: str,
    occurred_at: datetime | None = None,
) -> LearningActivity:
    moment = (occurred_at or beijing_now()).astimezone(BEIJING_TZ)
    if activity_type == "knowledge_card":
        activity_id = f"knowledge:{experiment_id}:{reference_id}"
    elif activity_type == "guided_session":
        activity_id = f"guided:{reference_id}"
    else:
        raise ValueError(f"未知学习活动类型：{activity_type}")
    return LearningActivity(
        activity_id=activity_id,
        occurred_at=moment.isoformat(timespec="seconds"),
        local_date=moment.date().isoformat(),
        experiment_id=experiment_id,
        activity_type=activity_type,
        reference_id=reference_id,
    )


def resolve_db_path(path: Path | str | None = None) -> Path:
    if path is not None:
        return Path(path)
    configured = os.getenv("DIANZHENTONG_DB_PATH")
    return Path(configured) if configured else DEFAULT_DB_PATH


class PracticeRepository:
    def __init__(self, path: Path | str | None = None):
        self.path = resolve_db_path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS practice_records (
                    practice_id TEXT PRIMARY KEY,
                    completed_at TEXT NOT NULL,
                    experiment_id TEXT NOT NULL DEFAULT 'motor_dol_no_start',
                    scenario_id TEXT NOT NULL,
                    result_id TEXT NOT NULL,
                    matched INTEGER NOT NULL CHECK (matched IN (0, 1)),
                    correct_judgments INTEGER NOT NULL CHECK (correct_judgments >= 0),
                    total_judgments INTEGER NOT NULL CHECK (total_judgments >= 0),
                    wrong_nodes TEXT NOT NULL,
                    uncertain_count INTEGER NOT NULL CHECK (uncertain_count >= 0)
                )
                """
            )
            columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(practice_records)")
            }
            if "experiment_id" not in columns:
                connection.execute(
                    "ALTER TABLE practice_records ADD COLUMN experiment_id "
                    "TEXT NOT NULL DEFAULT 'motor_dol_no_start'"
                )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_activities (
                    activity_id TEXT PRIMARY KEY,
                    occurred_at TEXT NOT NULL,
                    local_date TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL CHECK (
                        activity_type IN ('knowledge_card', 'guided_session')
                    ),
                    reference_id TEXT NOT NULL
                )
                """
            )

    def save(self, record: PracticeRecord) -> bool:
        row = record.as_row()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO practice_records (
                    practice_id, completed_at, experiment_id, scenario_id, result_id, matched,
                    correct_judgments, total_judgments, wrong_nodes, uncertain_count
                ) VALUES (
                    :practice_id, :completed_at, :experiment_id, :scenario_id, :result_id, :matched,
                    :correct_judgments, :total_judgments, :wrong_nodes, :uncertain_count
                )
                """,
                row,
            )
        return cursor.rowcount == 1

    def summary(self, experiment_id: str | None = None) -> dict[str, int | float | None]:
        where = "WHERE experiment_id = ?" if experiment_id else ""
        params = (experiment_id,) if experiment_id else ()
        with self.connect() as connection:
            aggregate = connection.execute(
                f"""
                SELECT COUNT(*) AS attempts,
                       COALESCE(SUM(matched), 0) AS matched_count,
                       COALESCE(SUM(correct_judgments), 0) AS correct_judgments,
                       COALESCE(SUM(total_judgments), 0) AS total_judgments
                FROM practice_records {where}
                """,
                params,
            ).fetchone()
            outcomes = connection.execute(
                f"SELECT matched FROM practice_records {where} "
                "ORDER BY completed_at DESC, rowid DESC",
                params,
            ).fetchall()
        attempts = int(aggregate["attempts"])
        matched_count = int(aggregate["matched_count"])
        correct = int(aggregate["correct_judgments"])
        total = int(aggregate["total_judgments"])
        streak = 0
        for outcome in outcomes:
            if not outcome["matched"]:
                break
            streak += 1
        return {
            "attempts": attempts,
            "matched_count": matched_count,
            "diagnosis_accuracy": matched_count / attempts if attempts else None,
            "correct_judgments": correct,
            "total_judgments": total,
            "judgment_accuracy": correct / total if total else None,
            "current_streak": streak,
        }

    def fault_stats(
        self, scenario_ids: Sequence[str], experiment_id: str | None = None
    ) -> dict[str, dict[str, int | float | None]]:
        stats = {
            scenario_id: {"attempts": 0, "correct": 0, "accuracy": None}
            for scenario_id in scenario_ids
        }
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT scenario_id, COUNT(*) AS attempts, SUM(matched) AS correct
                FROM practice_records
                WHERE (? IS NULL OR experiment_id = ?)
                GROUP BY scenario_id
                """,
                (experiment_id, experiment_id),
            ).fetchall()
        for row in rows:
            if row["scenario_id"] not in stats:
                continue
            attempts = int(row["attempts"])
            correct = int(row["correct"] or 0)
            stats[row["scenario_id"]] = {
                "attempts": attempts,
                "correct": correct,
                "accuracy": correct / attempts if attempts else None,
            }
        return stats

    def recent(self, limit: int = 10, experiment_id: str | None = None) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 100))
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM practice_records
                WHERE (? IS NULL OR experiment_id = ?)
                ORDER BY completed_at DESC, rowid DESC LIMIT ?
                """,
                (experiment_id, experiment_id, bounded_limit),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["matched"] = bool(item["matched"])
            item["wrong_nodes"] = json.loads(item["wrong_nodes"])
            result.append(item)
        return result

    def save_activity(self, activity: LearningActivity) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO learning_activities (
                    activity_id, occurred_at, local_date, experiment_id,
                    activity_type, reference_id
                ) VALUES (
                    :activity_id, :occurred_at, :local_date, :experiment_id,
                    :activity_type, :reference_id
                )
                """,
                activity.as_row(),
            )
        return cursor.rowcount == 1

    def activities(self, experiment_id: str | None = None) -> list[dict[str, str]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM learning_activities
                WHERE (? IS NULL OR experiment_id = ?)
                ORDER BY occurred_at DESC, rowid DESC
                """,
                (experiment_id, experiment_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def learned_cards(self, experiment_id: str) -> set[str]:
        return {
            item["reference_id"] for item in self.activities(experiment_id)
            if item["activity_type"] == "knowledge_card"
        }

    def active_dates(self) -> set[date]:
        dates = {date.fromisoformat(item["local_date"]) for item in self.activities()}
        with self.connect() as connection:
            rows = connection.execute("SELECT completed_at FROM practice_records").fetchall()
        dates.update(beijing_date_from_iso(row["completed_at"]) for row in rows)
        return dates

    def today_progress(self, today: date | None = None) -> dict[str, int]:
        current = today or beijing_now().date()
        day_text = current.isoformat()
        activities = [item for item in self.activities() if item["local_date"] == day_text]
        with self.connect() as connection:
            rows = connection.execute("SELECT completed_at FROM practice_records").fetchall()
        return {
            "knowledge_cards": sum(item["activity_type"] == "knowledge_card" for item in activities),
            "guided_sessions": sum(item["activity_type"] == "guided_session" for item in activities),
            "random_practices": sum(
                beijing_date_from_iso(row["completed_at"]) == current for row in rows
            ),
        }

    def clear(self, confirmed: bool = False) -> int:
        if not confirmed:
            return 0
        with self.connect() as connection:
            practice_cursor = connection.execute("DELETE FROM practice_records")
            activity_cursor = connection.execute("DELETE FROM learning_activities")
        return practice_cursor.rowcount + activity_cursor.rowcount


class MemoryPracticeRepository:
    """SQLite不可用时的会话级降级存储。"""

    def __init__(self):
        self.records: dict[str, PracticeRecord] = {}
        self.learning_records: dict[str, LearningActivity] = {}

    def save(self, record: PracticeRecord) -> bool:
        if record.practice_id in self.records:
            return False
        self.records[record.practice_id] = record
        return True

    def _selected(self, experiment_id: str | None = None) -> list[PracticeRecord]:
        records = list(self.records.values())
        if experiment_id:
            records = [item for item in records if item.experiment_id == experiment_id]
        return sorted(records, key=lambda item: item.completed_at, reverse=True)

    def summary(self, experiment_id: str | None = None) -> dict[str, int | float | None]:
        records = self._selected(experiment_id)
        attempts = len(records)
        matched = sum(item.matched for item in records)
        correct = sum(item.correct_judgments for item in records)
        total = sum(item.total_judgments for item in records)
        streak = 0
        for item in records:
            if not item.matched:
                break
            streak += 1
        return {
            "attempts": attempts,
            "matched_count": matched,
            "diagnosis_accuracy": matched / attempts if attempts else None,
            "correct_judgments": correct,
            "total_judgments": total,
            "judgment_accuracy": correct / total if total else None,
            "current_streak": streak,
        }

    def fault_stats(
        self, scenario_ids: Sequence[str], experiment_id: str | None = None
    ) -> dict[str, dict[str, int | float | None]]:
        records = self._selected(experiment_id)
        result: dict[str, dict[str, int | float | None]] = {}
        for scenario_id in scenario_ids:
            selected = [item for item in records if item.scenario_id == scenario_id]
            attempts = len(selected)
            correct = sum(item.matched for item in selected)
            result[scenario_id] = {
                "attempts": attempts,
                "correct": correct,
                "accuracy": correct / attempts if attempts else None,
            }
        return result

    def recent(self, limit: int = 10, experiment_id: str | None = None) -> list[dict[str, Any]]:
        return [
            {
                **record.as_row(),
                "matched": record.matched,
                "wrong_nodes": list(record.wrong_nodes),
            }
            for record in self._selected(experiment_id)[: max(1, min(int(limit), 100))]
        ]

    def save_activity(self, activity: LearningActivity) -> bool:
        if activity.activity_id in self.learning_records:
            return False
        self.learning_records[activity.activity_id] = activity
        return True

    def activities(self, experiment_id: str | None = None) -> list[dict[str, str]]:
        records = list(self.learning_records.values())
        if experiment_id:
            records = [item for item in records if item.experiment_id == experiment_id]
        return [item.as_row() for item in sorted(records, key=lambda item: item.occurred_at, reverse=True)]

    def learned_cards(self, experiment_id: str) -> set[str]:
        return {
            item.reference_id for item in self.learning_records.values()
            if item.experiment_id == experiment_id and item.activity_type == "knowledge_card"
        }

    def active_dates(self) -> set[date]:
        dates = {date.fromisoformat(item.local_date) for item in self.learning_records.values()}
        dates.update(beijing_date_from_iso(item.completed_at) for item in self.records.values())
        return dates

    def today_progress(self, today: date | None = None) -> dict[str, int]:
        current = today or beijing_now().date()
        activities = [
            item for item in self.learning_records.values()
            if date.fromisoformat(item.local_date) == current
        ]
        return {
            "knowledge_cards": sum(item.activity_type == "knowledge_card" for item in activities),
            "guided_sessions": sum(item.activity_type == "guided_session" for item in activities),
            "random_practices": sum(
                beijing_date_from_iso(item.completed_at) == current for item in self.records.values()
            ),
        }

    def clear(self, confirmed: bool = False) -> int:
        if not confirmed:
            return 0
        count = len(self.records)
        self.records.clear()
        count += len(self.learning_records)
        self.learning_records.clear()
        return count


class ResilientPracticeRepository:
    """优先使用SQLite，失败时自动切换到内存。"""

    def __init__(self, path: Path | str | None = None):
        self.persistent = True
        self.error: str | None = None
        try:
            self.backend: PracticeRepository | MemoryPracticeRepository = PracticeRepository(path)
        except (OSError, sqlite3.Error) as exc:
            self.backend = MemoryPracticeRepository()
            self.persistent = False
            self.error = str(exc)

    def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        try:
            return getattr(self.backend, method)(*args, **kwargs)
        except (OSError, sqlite3.Error) as exc:
            self.backend = MemoryPracticeRepository()
            self.persistent = False
            self.error = str(exc)
            return getattr(self.backend, method)(*args, **kwargs)

    def save(self, record: PracticeRecord) -> bool:
        return bool(self._call("save", record))

    def summary(self, experiment_id: str | None = None) -> dict[str, int | float | None]:
        return self._call("summary", experiment_id)

    def fault_stats(
        self, scenario_ids: Sequence[str], experiment_id: str | None = None
    ) -> dict[str, dict[str, int | float | None]]:
        return self._call("fault_stats", scenario_ids, experiment_id)

    def recent(self, limit: int = 10, experiment_id: str | None = None) -> list[dict[str, Any]]:
        return self._call("recent", limit, experiment_id)

    def save_activity(self, activity: LearningActivity) -> bool:
        return bool(self._call("save_activity", activity))

    def activities(self, experiment_id: str | None = None) -> list[dict[str, str]]:
        return self._call("activities", experiment_id)

    def learned_cards(self, experiment_id: str) -> set[str]:
        return self._call("learned_cards", experiment_id)

    def active_dates(self) -> set[date]:
        return self._call("active_dates")

    def today_progress(self, today: date | None = None) -> dict[str, int]:
        return self._call("today_progress", today)

    def clear(self, confirmed: bool = False) -> int:
        return int(self._call("clear", confirmed))


def choose_weak_scenario(
    stats: dict[str, dict[str, int | float | None]],
    scenario_ids: Sequence[str],
    chooser: Callable[[Sequence[str]], str] = secrets.choice,
) -> str:
    candidates = list(scenario_ids)
    if not candidates:
        raise ValueError("至少需要一个练习场景")
    if not stats or all(int(stats.get(item, {}).get("attempts", 0) or 0) == 0 for item in candidates):
        return chooser(candidates)

    def priority(scenario_id: str) -> tuple[int, float, int]:
        item = stats.get(scenario_id, {})
        attempts = int(item.get("attempts", 0) or 0)
        correct = int(item.get("correct", 0) or 0)
        accuracy = float(item.get("accuracy") or 0.0)
        never_correct = 1 if correct == 0 else 0
        return never_correct, 1.0 - accuracy, -attempts

    best_priority = max(priority(item) for item in candidates)
    weakest = [item for item in candidates if priority(item) == best_priority]
    return chooser(weakest)


def learning_streak(active_dates: set[date], today: date | None = None) -> int:
    current = today or beijing_now().date()
    cursor = current if current in active_dates else current - timedelta(days=1)
    streak = 0
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
