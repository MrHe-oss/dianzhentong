"""课程章节、术语和实验学习记录。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from .diagram_learning import cases_for_chapter


COURSE = {
    "id": "low_voltage_control_basics",
    "title": "低压电器与电气控制基础",
    "description": "从元件与安全基础出发，通过模拟实验学习电动机控制逻辑和故障排查思路。",
}

SECOND_COURSE = {
    "id": "relay_contactor_control",
    "title": "继电器—接触器控制基础",
    "description": "从运行方式与保持逻辑出发，学习点动和连续运行的控制关系与模拟排查。",
}

THIRD_COURSE = {
    "id": "electrical_diagram_reading",
    "title": "电气控制图识读基础",
    "description": "用抽象逻辑图学习元件角色、串并联条件和控制路径追踪，不涉及真实接线。",
}

FOURTH_COURSE = {
    "id": "star_delta_starting",
    "title": "星—三角降压启动基础",
    "description": "理解星—三角启动的适用条件、三个接触器角色、定时转换和互锁逻辑，不涉及真实接线。",
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

SECOND_COURSE_CHAPTERS = (
    {
        "id": "jog_continuous_basics",
        "title": "1. 点动与连续运行方式",
        "goal": "区分点动请求、连续启动请求以及公共控制条件。",
        "points": ("点动运行特征", "连续运行特征", "共享条件与方式支路"),
        "card_ids": ("jog_control",),
        "experiment_id": "motor_jog_continuous",
        "reflection": "为什么只有一种运行方式异常时，不应直接判断公共控制条件异常？",
        "next": "自锁保持逻辑与模拟排查",
    },
    {
        "id": "jog_continuous_training",
        "title": "2. 自锁逻辑与综合训练",
        "goal": "理解连续运行保持条件，并完成点动与连续运行故障排查。",
        "points": ("自锁辅助触点", "现象分支", "公共条件到方式支路的排查顺序"),
        "card_ids": ("self_hold", "button_contacts", "contactor_coil"),
        "experiment_id": "motor_jog_continuous",
        "reflection": "连续运行能启动但不能保持时，为什么要关注自锁而不是点动按钮？",
        "next": "进入跨实验综合训练",
    },
)

THIRD_COURSE_CHAPTERS = (
    {
        "id": "diagram_symbols_roles",
        "title": "1. 图形符号与元件角色",
        "goal": "从功能角色理解保护条件、操作信号、辅助触点和执行元件。",
        "points": ("功能角色优先于外形记忆", "触点基准状态", "抽象图与真实接线的边界"),
        "card_ids": ("diagram_symbols",),
        "experiment_id": None,
        "reflection": "为什么识图时应先判断元件角色，而不是只记住图形外观？",
        "next": "串联条件与并联分支",
    },
    {
        "id": "series_parallel_logic",
        "title": "2. 串联条件与并联分支",
        "goal": "理解串联表示条件同时满足，并联表示可选路径。",
        "points": ("串联条件：逻辑与", "并联分支：逻辑或", "公共条件与局部分支"),
        "card_ids": ("series_logic", "parallel_logic"),
        "experiment_id": None,
        "reflection": "一个公共条件异常时，为什么多个并联支路都可能失效？",
        "next": "沿控制路径进行逻辑追踪",
    },
    {
        "id": "control_path_tracing",
        "title": "3. 控制路径追踪",
        "goal": "按公共条件、操作分支和执行元件的顺序阅读抽象控制逻辑。",
        "points": ("先公共后分支", "从现象缩小范围", "用证据形成完整逻辑链"),
        "card_ids": ("logic_tracing",),
        "experiment_id": None,
        "reflection": "单一分支异常时，怎样避免检查无关分支？",
        "next": "返回已有模拟实验，用识图思路复盘排查路径",
    },
)

FOURTH_COURSE_CHAPTERS = (
    {
        "id": "star_delta_principles",
        "title": "1. 启动目的与适用条件",
        "goal": "理解星—三角启动用于降低启动阶段电流与转矩，并明确其适用边界。",
        "points": ("降压启动目的", "启动电流与启动转矩均降低", "适合启动负载较轻且允许三角运行的电动机"),
        "card_ids": ("star_delta_principle",), "experiment_id": None,
        "reflection": "为什么星—三角启动不能只看启动电流降低，而忽略启动转矩和负载条件？",
        "next": "认识三个接触器与时间控制",
    },
    {
        "id": "star_delta_components",
        "title": "2. 三个接触器与时间控制",
        "goal": "区分主、星形和三角接触器的抽象角色，理解时间控制负责阶段转换。",
        "points": ("主接触器维持公共运行条件", "星形接触器服务启动阶段", "三角接触器服务稳定运行阶段", "时间控制触发转换"),
        "card_ids": ("star_delta_components", "star_delta_timing"), "experiment_id": None,
        "reflection": "为什么识读星—三角逻辑时必须先判断当前处于启动阶段还是运行阶段？",
        "next": "学习转换顺序与互锁",
    },
    {
        "id": "star_delta_sequence",
        "title": "3. 转换顺序与互锁逻辑",
        "goal": "按启动请求、星形阶段、转换条件和三角阶段追踪抽象路径，并理解互锁约束。",
        "points": ("先星形后三角", "转换过程不允许星形与三角同时有效", "互锁与阶段顺序共同约束"),
        "card_ids": ("star_delta_timing", "star_delta_interlock"), "experiment_id": None,
        "reflection": "为什么星形与三角接触器不能同时形成动作条件？",
        "next": "用互动识图复盘完整阶段路径",
    },
)

COURSES = (COURSE, SECOND_COURSE, THIRD_COURSE, FOURTH_COURSE)
COURSE_CHAPTERS = {
    COURSE["id"]: CHAPTERS,
    SECOND_COURSE["id"]: SECOND_COURSE_CHAPTERS,
    THIRD_COURSE["id"]: THIRD_COURSE_CHAPTERS,
    FOURTH_COURSE["id"]: FOURTH_COURSE_CHAPTERS,
}
ALL_CHAPTERS = CHAPTERS + SECOND_COURSE_CHAPTERS + THIRD_COURSE_CHAPTERS + FOURTH_COURSE_CHAPTERS

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
    "串联控制条件": "多个条件依次位于同一路径中；教学逻辑上通常需要同时满足。",
    "并联控制分支": "控制路径分成可选支路；教学逻辑上任一有效支路可形成后续条件。",
    "控制路径": "从公共条件经过操作或保护条件到执行元件的抽象逻辑关系，不代表真实导线走向。",
    "星—三角启动": "先以星形阶段降低启动影响，再转换到三角运行阶段的启动方式；本平台只讲抽象逻辑。",
    "时间控制": "在教学逻辑中用于触发星形启动阶段向三角运行阶段转换的条件。",
    "阶段互锁": "阻止星形与三角两个阶段同时形成动作条件的约束逻辑。",
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


@dataclass(frozen=True)
class LearningStep:
    name: str
    status: str
    detail: str


def chapter_by_id(chapter_id: str) -> dict[str, Any]:
    return next(chapter for chapter in ALL_CHAPTERS if chapter["id"] == chapter_id)


def course_is_unlocked(repository: Any, course_id: str) -> bool:
    """课程逐级解锁：通过前一门课程任一章节测验。"""
    if course_id == COURSE["id"]:
        return True
    if course_id == SECOND_COURSE["id"]:
        return any(repository.quiz_summary(item["id"])["passed_count"] for item in CHAPTERS)
    if course_id == THIRD_COURSE["id"]:
        return any(repository.quiz_summary(item["id"])["passed_count"] for item in SECOND_COURSE_CHAPTERS)
    if course_id == FOURTH_COURSE["id"]:
        return bool(repository.quiz_summary(THIRD_COURSE["id"])["passed_count"])
    return False


def course_unlock_requirement(course_id: str) -> str:
    if course_id == SECOND_COURSE["id"]:
        return "通过第一门课程任意一个章节测验（达到60%）"
    if course_id == THIRD_COURSE["id"]:
        return "通过第二门课程任意一个章节测验（达到60%）"
    if course_id == FOURTH_COURSE["id"]:
        return "完成第三门课程综合评测（达到70%）"
    return "已开放"


def chapter_learning_steps(repository: Any, chapter: dict[str, Any]) -> tuple[LearningStep, ...]:
    progress = chapter_progress(repository, chapter)
    diagram_cases = cases_for_chapter(chapter["id"])
    if diagram_cases:
        diagram = repository.diagram_summary(chapter["id"])
        return (
            LearningStep("学习知识卡", "已完成" if progress.learned_cards == progress.total_cards else "进行中", f"{progress.learned_cards}/{progress.total_cards}"),
            LearningStep("完成互动识图", "已完成" if diagram["attempts"] else "待完成", f"{diagram['completed_cases']}/{len(diagram_cases)} 个案例"),
            LearningStep("通过章节测验", "已完成" if progress.quiz_passed else "待完成", f"已测 {progress.quiz_attempts} 次"),
            LearningStep("完成本章总结", "已完成" if progress.status == "已完成" else "待完成", "复盘路径与错题"),
        )
    experiment_id = chapter["experiment_id"]
    summary = repository.summary(experiment_id) if experiment_id else {"attempts": 0}
    guided = sum(
        item["activity_type"] == "guided_session"
        for item in repository.activities(experiment_id)
    ) if experiment_id else 0
    cards_done = progress.learned_cards == progress.total_cards
    return (
        LearningStep("学习知识卡", "已完成" if cards_done else "进行中", f"{progress.learned_cards}/{progress.total_cards}"),
        LearningStep("通过章节测验", "已完成" if progress.quiz_passed else "待完成", f"已测 {progress.quiz_attempts} 次"),
        LearningStep("完成引导实验", "已完成" if guided else ("待完成" if experiment_id else "本章无独立实验"), f"{guided} 次"),
        LearningStep("完成随机练习", "已完成" if int(summary["attempts"]) else ("待完成" if experiment_id else "本章无独立实验"), f"{summary['attempts']} 次"),
        LearningStep("完成本章总结", "已完成" if progress.quiz_passed and (not experiment_id or int(summary["attempts"])) else "待完成", "复盘学习目标与错题"),
    )


def recommended_chapter_action(repository: Any, chapter: dict[str, Any]) -> str:
    for step in chapter_learning_steps(repository, chapter):
        if step.status in {"进行中", "待完成"}:
            return step.name
    return "本章已完成，可继续下一章"


def chapter_progress(repository: Any, chapter: dict[str, Any]) -> ChapterProgress:
    experiment_id = chapter["experiment_id"]
    card_ids = set(chapter["card_ids"])
    learned = repository.learned_cards(experiment_id) if experiment_id else set()
    if not experiment_id:
        learned = set().union(*(repository.learned_cards(item) for item in ("motor_dol_no_start", "motor_forward_reverse", "motor_jog_continuous")))
    learned_count = len(card_ids.intersection(learned))
    experiment_completed = False
    if experiment_id:
        experiment_completed = bool(repository.summary(experiment_id)["attempts"]) or any(
            item["activity_type"] == "guided_session" for item in repository.activities(experiment_id)
        )
    card_ratio = learned_count / len(card_ids) if card_ids else 1.0
    diagram_cases = cases_for_chapter(chapter["id"])
    if diagram_cases:
        diagram_completed = bool(repository.diagram_summary(chapter["id"])["attempts"])
        quiz = repository.quiz_summary(chapter["id"])
        quiz_passed = bool(quiz["passed_count"])
        completion = 0.4 * card_ratio + 0.3 * diagram_completed + 0.3 * quiz_passed
        all_complete = card_ratio == 1 and diagram_completed and quiz_passed
        status = "已完成" if all_complete else ("未开始" if completion == 0 else "学习中")
        return ChapterProgress(
            chapter["id"], learned_count, len(card_ids), diagram_completed,
            completion, status, int(quiz["attempts"]), quiz_passed,
        )
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
        "motor_jog_continuous": "区分点动、连续运行与公共条件，理解自锁保持的教学逻辑。",
    }
    return {
        "experiment": session.knowledge.experiment["name"],
        "purpose": purposes[experiment_id],
        "phenomenon": session.symptom,
        "steps": tuple(item["object"] for item in session.history),
        "result": session.result["cause"] if session.result else "未完成",
        "reflection": tuple(session.knowledge.data["reflection_questions"]),
    }
