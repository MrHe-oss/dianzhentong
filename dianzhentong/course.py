"""课程章节、术语和实验学习记录。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COURSE = {
    "id": "low_voltage_control_basics",
    "title": "低压电器与电气控制基础",
    "description": "从元件与安全基础出发，通过模拟实验学习电动机控制逻辑和故障排查思路。",
}

CHAPTERS = (
    {
        "id": "safety_and_circuits",
        "title": "1. 控制回路与安全基础",
        "goal": "区分主回路与控制回路，理解本平台的教学边界。",
        "points": ("主回路与控制回路", "模拟资料与真实测量的区别", "正常、异常与不确定"),
        "card_ids": ("control_power",),
        "experiment_id": None,
        "reflection": "为什么网页中的模拟状态不能替代现场验电和安全规程？",
        "next": "按钮、保护元件与接触器",
    },
    {
        "id": "components",
        "title": "2. 按钮、保护元件与接触器",
        "goal": "理解常用低压控制元件在模拟回路中的作用与状态。",
        "points": ("熔断器", "热继电器保护触点", "常开与常闭按钮触点", "接触器线圈"),
        "card_ids": ("fuse", "thermal_relay", "button_contacts", "contactor_coil"),
        "experiment_id": None,
        "reflection": "为什么判断按钮触点前必须先明确按钮是否被按下？",
        "next": "三相异步电动机直接启动",
    },
    {
        "id": "direct_start",
        "title": "3. 三相异步电动机直接启动",
        "goal": "按上游条件到下游元件的顺序，完成直接启动教学排查。",
        "points": ("直接启动控制逻辑", "自锁概念", "公共条件与顺序排查"),
        "card_ids": ("self_hold",),
        "experiment_id": "motor_dol_no_start",
        "reflection": "为什么不能只凭‘电动机不启动’就直接更换接触器？",
        "next": "三相异步电动机正反转控制",
    },
    {
        "id": "forward_reverse",
        "title": "4. 三相异步电动机正反转控制",
        "goal": "根据一个方向或两个方向的现象，区分公共条件与方向支路。",
        "points": ("正反转方向支路", "电气互锁", "现象分支与排查范围"),
        "card_ids": ("electrical_interlock", "forward_reverse"),
        "experiment_id": "motor_forward_reverse",
        "reflection": "为什么正反转两个方向都不能启动时，应先检查公共条件？",
        "next": "完成错题复习并巩固薄弱故障",
    },
)

GLOSSARY = {
    "主回路": "向电动机等负载传递主要电能的回路。本平台不提供真实主回路接线指导。",
    "控制回路": "由按钮、保护触点和接触器线圈等组成，用于表达启停与保护逻辑的回路。",
    "常开触点": "元件处于未动作基准状态时断开，动作后闭合的触点。",
    "常闭触点": "元件处于未动作基准状态时闭合，动作后断开的触点。",
    "接触器": "通过线圈产生电磁动作，带动主触点和辅助触点改变状态的控制电器。",
    "熔断器": "异常电流使熔体断开，从而限制故障影响的保护元件。",
    "热继电器": "用于反映过载状态的保护电器；其保护触点可中断控制条件。",
    "自锁": "利用接触器常开辅助触点，在启动信号消失后继续维持控制条件的逻辑。",
    "电气互锁": "利用另一方向接触器的常闭辅助触点，阻止两个方向同时形成动作条件。",
    "过载保护": "当负载状态超出规定范围时采取保护动作的机制，不等同于短路保护。",
    "直接启动": "教学中常见的电动机启动控制方式，本平台只模拟其控制逻辑与故障判断。",
}


@dataclass(frozen=True)
class ChapterProgress:
    chapter_id: str
    learned_cards: int
    total_cards: int
    experiment_completed: bool
    completion: float
    status: str
    quiz_attempts: int
    quiz_passed: bool


def chapter_by_id(chapter_id: str) -> dict[str, Any]:
    return next(chapter for chapter in CHAPTERS if chapter["id"] == chapter_id)


def chapter_progress(repository: Any, chapter: dict[str, Any]) -> ChapterProgress:
    experiment_id = chapter["experiment_id"]
    card_ids = set(chapter["card_ids"])
    learned = repository.learned_cards(experiment_id) if experiment_id else set()
    if not experiment_id:
        learned = set().union(*(repository.learned_cards(item) for item in ("motor_dol_no_start", "motor_forward_reverse")))
    learned_count = len(card_ids.intersection(learned))
    experiment_completed = False
    if experiment_id:
        experiment_completed = bool(repository.summary(experiment_id)["attempts"]) or any(
            item["activity_type"] == "guided_session" for item in repository.activities(experiment_id)
        )
    card_ratio = learned_count / len(card_ids) if card_ids else 1.0
    completion = card_ratio if not experiment_id else 0.5 * card_ratio + 0.5 * experiment_completed
    quiz = repository.quiz_summary(chapter["id"])
    quiz_passed = bool(quiz["passed_count"])
    prerequisites_complete = completion == 1
    if quiz_passed:
        status = "已完成"
    elif prerequisites_complete:
        status = "待测验"
        completion = 0.9
    else:
        status = "学习中" if completion else "未开始"
    return ChapterProgress(
        chapter["id"], learned_count, len(card_ids), experiment_completed,
        completion, status, int(quiz["attempts"]), quiz_passed,
    )


def experiment_learning_record(session: Any) -> dict[str, Any]:
    experiment_id = session.knowledge.experiment_id
    purposes = {
        "motor_dol_no_start": "理解直接启动控制逻辑，练习按上游到下游顺序排查。",
        "motor_forward_reverse": "区分正反转公共条件和方向支路，理解电气互锁的教学逻辑。",
    }
    return {
        "experiment": session.knowledge.experiment["name"],
        "purpose": purposes[experiment_id],
        "phenomenon": session.symptom,
        "steps": tuple(item["object"] for item in session.history),
        "result": session.result["cause"] if session.result else "未完成",
        "reflection": tuple(session.knowledge.data["reflection_questions"]),
    }
