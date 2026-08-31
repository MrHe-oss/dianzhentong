"""把历史记录转化为可完成的薄弱项与10分钟复习清单。"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from .diagram_learning import DIAGRAM_CASES
from .engine import KnowledgeBase
from .learning import EXPERIMENT_CARD_ORDER, KNOWLEDGE_CARDS
from .quiz import QUESTION_MAP

BEIJING_TZ = ZoneInfo("Asia/Shanghai")

@dataclass(frozen=True)
class ReviewMasteryStatus:
    kind: str
    reference_id: str
    error_count: int
    consecutive_correct: int
    last_activity_at: str
    last_error_at: str
    mastered: bool
    mastered_at: str | None
    attempts: int
    experiment_id: str | None = None
    case_id: str | None = None

@dataclass(frozen=True)
class ReviewTask:
    kind: str
    title: str
    reason: str
    minutes: int
    experiment_id: str | None = None
    reference_id: str | None = None

def _status(kind: str, reference_id: str, history: list[dict[str, Any]],
            experiment_id: str | None = None, case_id: str | None = None) -> ReviewMasteryStatus | None:
    if not history or not any(not item["is_correct"] for item in history): return None
    trailing = 0
    for item in reversed(history):
        if not item["is_correct"]: break
        trailing += 1
    mastered = trailing >= 2
    last_error_at = next(item["completed_at"] for item in reversed(history) if not item["is_correct"])
    mastery_index = len(history) - trailing + 1
    mastered_at = history[mastery_index]["completed_at"] if mastered else None
    return ReviewMasteryStatus(
        kind, reference_id, sum(not item["is_correct"] for item in history), trailing,
        history[-1]["completed_at"], last_error_at, mastered, mastered_at,
        len(history), experiment_id, case_id,
    )

def review_mastery_statuses(repository: Any) -> tuple[ReviewMasteryStatus, ...]:
    result: list[ReviewMasteryStatus] = []
    for question_id in repository.wrong_question_ids():
        item = _status("quiz", question_id, repository.question_answer_history(question_id))
        if item: result.append(item)
    seen_steps: set[str] = set()
    for case_id, case in DIAGRAM_CASES.items():
        for step in case["steps"]:
            step_id = step["id"]
            if step_id in seen_steps: continue
            seen_steps.add(step_id)
            item = _status("diagram", step_id, repository.diagram_step_history(case_id, step_id), case_id=case_id)
            if item: result.append(item)
    for experiment_id in KnowledgeBase.catalog():
        knowledge = KnowledgeBase(experiment_id)
        for scenario_id in knowledge.scenario_ids:
            history = [
                {"completed_at": item["completed_at"], "is_correct": bool(item["matched"])}
                for item in reversed(repository.recent(100, experiment_id))
                if item["scenario_id"] == scenario_id
            ]
            item = _status("fault", scenario_id, history, experiment_id=experiment_id)
            if item: result.append(item)
    return tuple(result)

def review_overview(repository: Any, today: date | None = None) -> dict[str, Any]:
    statuses = review_mastery_statuses(repository)
    current = today or datetime.now(BEIJING_TZ).date()
    cutoff = current - timedelta(days=6)
    recently_mastered = sum(
        item.mastered and item.mastered_at is not None
        and cutoff <= datetime.fromisoformat(item.mastered_at).astimezone(BEIJING_TZ).date() <= current
        for item in statuses
    )
    return {
        "statuses": statuses,
        "pending": tuple(item for item in statuses if not item.mastered),
        "mastered": tuple(item for item in statuses if item.mastered),
        "recently_mastered": recently_mastered,
    }

def _sort_pending(items: Iterable[ReviewMasteryStatus]) -> list[ReviewMasteryStatus]:
    return sorted(items, key=lambda item: (-item.error_count, -datetime.fromisoformat(item.last_error_at).timestamp(), item.attempts, item.kind, item.reference_id))

def _task(item: ReviewMasteryStatus) -> ReviewTask:
    progress = f"已连续正确 {item.consecutive_correct}/2 次；累计错误 {item.error_count} 次"
    if item.kind == "quiz":
        question = QUESTION_MAP[item.reference_id]
        return ReviewTask("quiz", f"复习题：{question.knowledge_point}", progress, 3, reference_id=item.reference_id)
    if item.kind == "diagram":
        case = DIAGRAM_CASES[item.case_id]
        step = next(step for step in case["steps"] if step["id"] == item.reference_id)
        return ReviewTask("diagram", f"识图训练：{case['title']}", f"{step['prompt']}；{progress}", 3, reference_id=item.case_id)
    knowledge = KnowledgeBase(item.experiment_id)
    return ReviewTask("fault", f"再练一次：{knowledge.results[item.reference_id]['cause']}", progress, 4, item.experiment_id, item.reference_id)

def _starter_task(repository: Any) -> ReviewTask:
    options = []
    for experiment_id, cards in EXPERIMENT_CARD_ORDER.items():
        learned = repository.learned_cards(experiment_id)
        missing = next((card_id for card_id in cards if card_id not in learned), None)
        if missing: options.append((len(learned), experiment_id, missing))
    if options:
        _, experiment_id, card_id = min(options)
        return ReviewTask("knowledge", f"知识卡：{KNOWLEDGE_CARDS[card_id]['title']}", "当前没有待处理薄弱项，补充一个尚未学习的基础知识点", 3, experiment_id, card_id)
    return ReviewTask("knowledge", "巩固控制路径追踪", "当前复习任务已完成，可自由巩固控制路径", 3, "motor_dol_no_start", "control_power")

def build_review_plan(repository: Any) -> tuple[ReviewTask, ...]:
    pending = _sort_pending(review_overview(repository)["pending"])
    tasks: list[ReviewTask] = []
    selected_kinds: set[str] = set()
    minutes = 0
    for item in pending:
        if item.kind in selected_kinds: continue
        task = _task(item)
        if len(tasks) == 3 or minutes + task.minutes > 10: break
        tasks.append(task); selected_kinds.add(item.kind); minutes += task.minutes
    return tuple(tasks or [_starter_task(repository)])
