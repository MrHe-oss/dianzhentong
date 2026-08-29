"""每日任务、学习连续性和实验掌握度计算。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Sequence
from zoneinfo import ZoneInfo



def learning_streak(active_dates: set[date], today: date) -> int:
    """计算连续活跃天数；当天尚未开始时允许从昨天延续。"""
    cursor = today if today in active_dates else today - timedelta(days=1)
    streak = 0
    while cursor in active_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def beijing_today() -> date:
    return datetime.now(ZoneInfo("Asia/Shanghai")).date()


@dataclass(frozen=True)
class ExperimentProgress:
    experiment_id: str
    learned_cards: int
    total_cards: int
    guided_sessions: int
    practice_attempts: int
    mastered_faults: int
    total_faults: int
    mastery: float
    status: str
    route_stage: str


def calculate_experiment_progress(
    repository: Any,
    experiment_id: str,
    scenario_ids: Sequence[str],
    card_ids: Sequence[str],
) -> ExperimentProgress:
    learned = repository.learned_cards(experiment_id)
    activities = repository.activities(experiment_id)
    guided = sum(item["activity_type"] == "guided_session" for item in activities)
    summary = repository.summary(experiment_id)
    stats = repository.fault_stats(scenario_ids, experiment_id)
    mastered = sum(
        int(item["attempts"]) >= 2
        and item["accuracy"] is not None
        and float(item["accuracy"]) >= 0.60
        for item in stats.values()
    )
    knowledge_ratio = len(learned.intersection(card_ids)) / len(card_ids) if card_ids else 1.0
    guided_ratio = 1.0 if guided else 0.0
    fault_ratio = mastered / len(scenario_ids) if scenario_ids else 1.0
    mastery = 0.30 * knowledge_ratio + 0.20 * guided_ratio + 0.50 * fault_ratio
    attempts = int(summary["attempts"])
    if not learned and not guided and not attempts:
        status = "未开始"
    elif mastery >= 0.80:
        status = "基本掌握"
    elif attempts:
        status = "练习中"
    else:
        status = "学习中"

    if len(learned.intersection(card_ids)) < len(card_ids):
        route_stage = "学习知识卡"
    elif guided < 1:
        route_stage = "完成引导学习"
    elif attempts < 3:
        route_stage = "完成3次随机练习"
    elif mastered < len(scenario_ids):
        route_stage = "掌握全部故障"
    else:
        route_stage = "路线已完成"
    return ExperimentProgress(
        experiment_id=experiment_id,
        learned_cards=len(learned.intersection(card_ids)),
        total_cards=len(card_ids),
        guided_sessions=guided,
        practice_attempts=attempts,
        mastered_faults=mastered,
        total_faults=len(scenario_ids),
        mastery=mastery,
        status=status,
        route_stage=route_stage,
    )


def daily_task_status(
    repository: Any,
    all_cards_learned: bool = False,
    today: date | None = None,
) -> dict[str, Any]:
    counts = repository.today_progress(today)
    completed = {
        "knowledge": counts["knowledge_cards"] >= 1 or all_cards_learned,
        "guided": counts["guided_sessions"] >= 1,
        "practice": counts["random_practices"] >= 2,
    }
    return {
        **counts,
        **completed,
        "completed_count": sum(completed.values()),
        "completion": sum(completed.values()) / 3,
    }


def learning_overview(
    repository: Any,
    progress_by_experiment: dict[str, ExperimentProgress],
    today: date | None = None,
) -> dict[str, Any]:
    all_cards_learned = all(
        item.learned_cards == item.total_cards for item in progress_by_experiment.values()
    )
    weakest = min(
        progress_by_experiment.values(),
        key=lambda item: (item.mastery, item.practice_attempts, item.experiment_id),
    )
    return {
        "tasks": daily_task_status(repository, all_cards_learned, today),
        "streak": learning_streak(repository.active_dates(), today or beijing_today()),
        "recommended_experiment_id": weakest.experiment_id,
    }
