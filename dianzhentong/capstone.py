"""课程综合实训任务与纯规则会话引擎。"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from .course import COURSE_CHAPTERS
from .learning import KNOWLEDGE_CARDS


CAPSTONE_SAFETY = "仅使用网页给出的模拟情境完成学习判断，不包含真实设备选型、整定或操作指导。"


def _step(step_id: str, prompt: str, options: tuple[str, ...], answer: str,
          explanation: str, card_id: str) -> dict[str, Any]:
    return {"id": step_id, "prompt": prompt, "options": options, "answer": answer,
            "explanation": explanation, "card_id": card_id}


CAPSTONE_TASKS: dict[str, dict[str, Any]] = {
    "capstone_low_voltage": {
        "course_id": "low_voltage_control_basics", "title": "低压电器基础综合实训",
        "goal": "根据模拟现象识别控制角色、保护条件和安全边界。",
        "scenario": "模拟控制路径无法形成启动条件，需要按功能角色从上游向下游分析。",
        "steps": (
            _step("lv_scope", "本任务首先应关注哪类路径？", ("控制逻辑路径", "机械安装位置", "无关外观"), "控制逻辑路径", "题设描述的是控制条件，先确定控制逻辑范围。", "control_power"),
            _step("lv_power", "控制电源模拟条件不可用时应怎样判断？", ("公共路径在上游中断", "直接判断线圈异常", "忽略并继续"), "公共路径在上游中断", "控制电源是后续控制逻辑的前置条件。", "control_power"),
            _step("lv_protection", "公共电源正常后应继续确认哪类条件？", ("保护条件", "设备颜色", "运行声音"), "保护条件", "保护元件状态会影响后续控制条件。", "thermal_relay"),
            _step("lv_request", "保护条件正常后，哪个角色表达启动意图？", ("启动按钮触点", "熔断器", "过载保护"), "启动按钮触点", "操作触点用于表达启动请求。", "button_contacts"),
            _step("lv_safety", "模拟证据不足时应如何处理？", ("选择不确定并复核资料", "强行给出结论", "转向真实操作"), "选择不确定并复核资料", "证据不足时保留不确定，不能猜测或扩大操作范围。", "diagram_symbols"),
        ),
    },
    "capstone_relay_control": {
        "course_id": "relay_contactor_control", "title": "点动与连续控制综合实训",
        "goal": "区分公共条件、运行方式和自锁保持关系。",
        "scenario": "点动能够形成模拟动作，连续运行按住按钮时有效，但请求消失后不能保持。",
        "steps": (
            _step("rc_common", "点动能够形成动作说明什么？", ("公共条件和执行角色基本可用", "公共条件一定异常", "保持分支一定正常"), "公共条件和执行角色基本可用", "点动有效说明共享路径和执行角色已经形成。", "jog_control"),
            _step("rc_scope", "当前异常最应关注哪种运行方式？", ("连续运行方式", "点动方式", "所有方式"), "连续运行方式", "现象只发生在连续保持阶段。", "jog_control"),
            _step("rc_request", "按住连续启动按钮时能够运行说明什么？", ("启动请求路径有效", "停止条件异常", "公共电源缺失"), "启动请求路径有效", "短暂动作证明启动请求能够到达执行角色。", "button_contacts"),
            _step("rc_hold", "请求消失后本应由哪个角色维持？", ("自锁保持分支", "点动按钮", "保护条件"), "自锁保持分支", "连续运行依靠辅助触点形成保持逻辑。", "self_hold"),
            _step("rc_result", "最符合现象的抽象结论是？", ("保持分支未形成", "公共条件全部失效", "点动请求异常"), "保持分支未形成", "现象把范围限定在连续运行的保持逻辑。", "self_hold"),
        ),
    },
    "capstone_diagram_reading": {
        "course_id": "electrical_diagram_reading", "title": "控制路径识读综合实训",
        "goal": "从共同现象缩小范围，并定位抽象逻辑中断点。",
        "scenario": "正、反两个方向均不能形成模拟动作，公共电源正常但某个共享条件未满足。",
        "steps": (
            _step("dr_scope", "两个方向共同异常时应先追踪哪里？", ("公共路径", "只看正转分支", "只看反转分支"), "公共路径", "共同异常优先指向共享条件。", "logic_tracing"),
            _step("dr_order", "公共路径应按什么顺序阅读？", ("从上游向下游", "从结果随机倒猜", "同时检查所有分支"), "从上游向下游", "顺序追踪可以建立可解释的证据链。", "series_logic"),
            _step("dr_series", "串联条件中有一项不满足时会怎样？", ("后续路径被阻断", "自动切换到任意分支", "仍然完整"), "后续路径被阻断", "串联条件需要共同满足。", "series_logic"),
            _step("dr_branch", "已定位公共中断后是否继续判断方向支路？", ("不继续猜测无关支路", "直接判断两个线圈异常", "任选一个方向"), "不继续猜测无关支路", "当前证据已经解释两个方向共同异常。", "logic_tracing"),
            _step("dr_evidence", "完整识图结论应包含什么？", ("现象、路径、状态和依据", "只有元件名称", "只有最终答案"), "现象、路径、状态和依据", "可解释结论需要完整逻辑链。", "diagram_symbols"),
        ),
    },
    "capstone_star_delta": {
        "course_id": "star_delta_starting", "title": "星—三角启动综合实训",
        "goal": "判断适用条件、阶段角色、转换顺序和互锁约束。",
        "scenario": "题设允许较低启动转矩，启动请求形成后先进入星形阶段，随后满足转换条件。",
        "steps": (
            _step("sd_fit", "该方式的适用性首先取决于什么？", ("题设负载与电动机条件", "接触器外观", "任意电动机都适用"), "题设负载与电动机条件", "启动电流和启动转矩都会降低，必须先确认适用条件。", "star_delta_principle"),
            _step("sd_start", "启动阶段应由哪组角色形成？", ("主接触器与星形接触器", "主接触器与三角接触器", "星形与三角接触器"), "主接触器与星形接触器", "公共主角色与星形角色服务启动阶段。", "star_delta_components"),
            _step("sd_time", "时间条件在本任务中的作用是？", ("触发阶段转换", "替代保护条件", "允许两个阶段重叠"), "触发阶段转换", "时间控制表达从星形启动向三角运行转换的条件。", "star_delta_timing"),
            _step("sd_exit", "进入三角阶段前必须先发生什么？", ("星形角色退出", "星形角色继续保持", "公共角色永久退出"), "星形角色退出", "转换过程应先结束星形阶段。", "star_delta_interlock"),
            _step("sd_run", "转换完成后的有效角色是？", ("主接触器与三角接触器", "主接触器与星形接触器", "星形与三角接触器同时有效"), "主接触器与三角接触器", "运行阶段保留公共主角色并启用三角角色。", "star_delta_components"),
        ),
    },
    "capstone_time_sequence": {
        "course_id": "time_relay_sequence_control", "title": "时间继电器与顺序控制综合实训",
        "goal": "区分通电与断电延时，并按条件追踪顺序控制阶段。",
        "scenario": "模拟输入形成后先进入等待，条件到达后允许后续阶段；停止请求后按退出条件结束。",
        "steps": (
            _step("ts_input", "时间过程分析首先识别什么？", ("输入条件", "输出结果", "设备外观"), "输入条件", "时间继电器的过程由输入状态变化触发。", "timer_role"),
            _step("ts_on", "输入形成后等待、再改变输出属于哪类逻辑？", ("通电延时", "断电延时", "无时间关系"), "通电延时", "通电延时从输入形成开始等待。", "on_delay"),
            _step("ts_off", "输入消失后输出暂时保持属于哪类逻辑？", ("断电延时", "通电延时", "立即复位"), "断电延时", "断电延时从输入撤除开始等待，输出延后退出。", "off_delay"),
            _step("ts_sequence", "后续阶段何时允许进入？", ("前序与顺序条件满足后", "任意时刻", "早于第一阶段"), "前序与顺序条件满足后", "顺序控制由前序状态和转换条件共同限定。", "sequence_control"),
            _step("ts_safety", "模拟资料不足时应怎样处理？", ("保留不确定并复核", "照此操作真实设备", "猜测具体整定值"), "保留不确定并复核", "教学模型不提供真实设备整定或操作结论。", "timer_role"),
        ),
    },
}


@dataclass
class CapstoneTaskSession:
    task_id: str
    session_id: str = field(default_factory=lambda: secrets.token_hex(12))
    index: int = 0
    first_answers: dict[str, str] = field(default_factory=dict)
    wrong_steps: list[str] = field(default_factory=list)
    step_solved: bool = False
    reflection: str = ""

    @property
    def task(self) -> dict[str, Any]:
        return CAPSTONE_TASKS[self.task_id]

    @property
    def current_step(self) -> dict[str, Any] | None:
        return None if self.objective_complete else self.task["steps"][self.index]

    @property
    def objective_complete(self) -> bool:
        return self.index >= len(self.task["steps"])

    @property
    def correct_steps(self) -> int:
        return len(self.task["steps"]) - len(self.wrong_steps)

    @property
    def passed(self) -> bool:
        return self.objective_complete and self.correct_steps / len(self.task["steps"]) >= 0.7

    @property
    def reflection_valid(self) -> bool:
        return 20 <= len(self.reflection.strip()) <= 300

    @property
    def can_finalize(self) -> bool:
        return self.objective_complete and self.reflection_valid

    def answer(self, selected: str) -> bool:
        step = self.current_step
        if step is None:
            raise ValueError("综合实训客观步骤已经完成")
        if selected not in (*step["options"], "不确定"):
            raise ValueError("答案不属于当前步骤选项")
        if step["id"] not in self.first_answers:
            self.first_answers[step["id"]] = selected
            if selected != step["answer"]:
                self.wrong_steps.append(step["id"])
        self.step_solved = selected == step["answer"]
        return self.step_solved

    def next_step(self) -> None:
        if not self.step_solved:
            raise ValueError("请先完成当前步骤")
        self.index += 1
        self.step_solved = False

    def set_reflection(self, text: str) -> None:
        if len(text) > 300:
            raise ValueError("学习反思不能超过300字")
        self.reflection = text

    def to_dict(self) -> dict[str, Any]:
        return {"task_id": self.task_id, "session_id": self.session_id, "index": self.index,
                "first_answers": dict(self.first_answers), "wrong_steps": list(self.wrong_steps),
                "step_solved": self.step_solved, "reflection": self.reflection}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapstoneTaskSession":
        if data.get("task_id") not in CAPSTONE_TASKS:
            raise ValueError("未知综合实训任务")
        task_id = str(data["task_id"])
        task = CAPSTONE_TASKS[task_id]
        index = int(data.get("index", 0))
        first_answers = dict(data.get("first_answers", {}))
        wrong_steps = list(data.get("wrong_steps", []))
        step_map = {step["id"]: step for step in task["steps"]}
        if index < 0 or index > len(task["steps"]):
            raise ValueError("综合实训步骤位置无效")
        if any(step_id not in step_map or selected not in (*step_map[step_id]["options"], "不确定")
               for step_id, selected in first_answers.items()):
            raise ValueError("综合实训答案状态无效")
        expected_wrong = {step_id for step_id, selected in first_answers.items()
                          if selected != step_map[step_id]["answer"]}
        if set(wrong_steps) != expected_wrong or len(wrong_steps) != len(set(wrong_steps)):
            raise ValueError("综合实训得分状态无效")
        reflection = str(data.get("reflection", ""))
        if len(reflection) > 300:
            raise ValueError("综合实训反思状态无效")
        return cls(task_id, str(data["session_id"]), index, first_answers, wrong_steps,
                   bool(data.get("step_solved", False)), reflection)


def task_for_course(course_id: str) -> dict[str, Any]:
    return next({"id": task_id, **task} for task_id, task in CAPSTONE_TASKS.items()
                if task["course_id"] == course_id)


def task_is_unlocked(repository: Any, course_id: str) -> bool:
    return all(repository.quiz_summary(chapter["id"])["passed_count"]
               for chapter in COURSE_CHAPTERS[course_id])


def capstone_report_text(session: CapstoneTaskSession) -> str:
    if not session.can_finalize:
        raise ValueError("综合实训尚未完成")
    task = session.task
    lines = ["电诊通｜课程综合实训学习报告", task["title"], "", f"任务目标：{task['goal']}",
             f"模拟情境：{task['scenario']}",
             f"首次判断得分：{session.correct_steps}/{len(task['steps'])}（{session.correct_steps / len(task['steps']):.0%}）",
             f"完成状态：{'已完成' if session.passed else '尚未达到70%'}", "", "判断过程："]
    for index, step in enumerate(task["steps"], 1):
        selected = session.first_answers[step["id"]]
        lines.append(f"{index}. {step['prompt']}")
        lines.append(f"   首次判断：{selected}；正确判断：{step['answer']}")
        lines.append(f"   依据：{step['explanation']}")
    cards = tuple(dict.fromkeys(step["card_id"] for step in task["steps"]))
    lines.extend(("", "关联知识卡：" + "、".join(KNOWLEDGE_CARDS[item]["title"] for item in cards),
                  "", "学习反思：", session.reflection.strip()))
    if session.wrong_steps:
        weak_cards = tuple(dict.fromkeys(step["card_id"] for step in task["steps"]
                                         if step["id"] in session.wrong_steps))
        lines.extend(("", "复习建议：" + "、".join(KNOWLEDGE_CARDS[item]["title"] for item in weak_cards)))
    else:
        lines.extend(("", "复习建议：本次首次判断全部正确，可继续使用10分钟复习巩固。"))
    lines.extend(("", CAPSTONE_SAFETY, "本报告不是职业资格、实训考核或能力认证证书。"))
    return "\n".join(lines)


def validate_capstone_tasks() -> None:
    if {task["course_id"] for task in CAPSTONE_TASKS.values()} != set(COURSE_CHAPTERS):
        raise ValueError("综合实训未完整覆盖课程")
    for task_id, task in CAPSTONE_TASKS.items():
        if len(task["steps"]) != 5:
            raise ValueError(f"综合实训必须包含5个步骤：{task_id}")
        ids = [step["id"] for step in task["steps"]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"综合实训步骤编号重复：{task_id}")
        for step in task["steps"]:
            if step["answer"] not in step["options"] or len(step["options"]) != 3:
                raise ValueError(f"综合实训选项无效：{task_id}")
            if step["card_id"] not in KNOWLEDGE_CARDS:
                raise ValueError(f"综合实训引用未知知识卡：{task_id}")


validate_capstone_tasks()
