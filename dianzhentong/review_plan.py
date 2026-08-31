"""把现有学习记录整理为一份可立即执行的10分钟复习任务。"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

from .diagram_learning import DIAGRAM_CASES
from .engine import KnowledgeBase
from .learning import EXPERIMENT_CARD_ORDER, KNOWLEDGE_CARDS
from .quiz import QUESTION_MAP, card_id_for_question

@dataclass(frozen=True)
class ReviewTask:
    kind: str
    title: str
    reason: str
    minutes: int
    experiment_id: str | None = None
    reference_id: str | None = None

def _weak_fault(repository: Any) -> ReviewTask | None:
    candidates = []
    for experiment_id, experiment in KnowledgeBase.catalog().items():
        knowledge = KnowledgeBase(experiment_id)
        for scenario_id, item in repository.fault_stats(knowledge.scenario_ids, experiment_id).items():
            attempts = int(item["attempts"])
            if not attempts or (attempts >= 2 and item["accuracy"] is not None and float(item["accuracy"]) >= .60):
                continue
            candidates.append((float(item["accuracy"] or 0), attempts, experiment_id, scenario_id, experiment["name"], knowledge.results[scenario_id]["cause"]))
    if not candidates: return None
    accuracy, attempts, experiment_id, scenario_id, experiment_name, cause = min(candidates)
    return ReviewTask("fault", f"再练一次：{cause}", f"{experiment_name}已练{attempts}次，诊断正确率{accuracy:.0%}", 4, experiment_id, scenario_id)

def _wrong_question(repository: Any) -> ReviewTask | None:
    wrong_ids = repository.wrong_question_ids()
    if not wrong_ids: return None
    question = QUESTION_MAP[wrong_ids[0]]
    card_id = card_id_for_question(question.id)
    return ReviewTask("quiz", f"复习题：{question.knowledge_point}", f"最近记录中该知识点仍有错误判断；先看解析，再做一道同类题", 3, reference_id=question.id)

def _weak_diagram(repository: Any) -> ReviewTask | None:
    step_id = repository.diagram_summary()["weakest_step"]
    if not step_id: return None
    for case_id, case in DIAGRAM_CASES.items():
        step = next((item for item in case["steps"] if item["id"] == step_id), None)
        if step:
            return ReviewTask("diagram", f"识图训练：{case['title']}", f"最常出错的逻辑点：{step['prompt']}", 3, reference_id=case_id)
    return None

def _starter_task(repository: Any) -> ReviewTask:
    options = []
    for experiment_id, cards in EXPERIMENT_CARD_ORDER.items():
        learned = repository.learned_cards(experiment_id)
        missing = next((card_id for card_id in cards if card_id not in learned), None)
        if missing: options.append((len(learned), experiment_id, missing))
    if options:
        _, experiment_id, card_id = min(options)
        return ReviewTask("knowledge", f"知识卡：{KNOWLEDGE_CARDS[card_id]['title']}", "先补齐一个尚未学习的基础知识点", 3, experiment_id, card_id)
    return ReviewTask("knowledge", "复习控制路径追踪", "当前没有明显错题，巩固从公共条件到执行元件的判断顺序", 3, "motor_dol_no_start", "control_power")

def build_review_plan(repository: Any) -> tuple[ReviewTask, ...]:
    """按错题、薄弱识图和薄弱故障生成任务；无记录时给出起步任务。"""
    tasks = [item for item in (_wrong_question(repository), _weak_diagram(repository), _weak_fault(repository)) if item]
    if not tasks: tasks = [_starter_task(repository)]
    return tuple(tasks[:3])
