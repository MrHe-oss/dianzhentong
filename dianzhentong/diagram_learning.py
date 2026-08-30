"""安全的抽象控制逻辑识读案例与纯规则训练引擎。"""
from __future__ import annotations
import secrets
from dataclasses import dataclass, field
from typing import Any

SAFETY_NOTICE = "仅用于抽象控制逻辑学习，不包含端子号、电压、真实导线、接线或带电操作指导。"

def _step(step_id: str, prompt: str, options: tuple[str, ...], answer: str, explanation: str) -> dict[str, Any]:
    return {"id": step_id, "prompt": prompt, "options": options, "answer": answer, "explanation": explanation}

DIAGRAM_CASES: dict[str, dict[str, Any]] = {
    "dol_roles": {"chapter_id":"diagram_symbols_roles","title":"直接启动：识别元件角色","phenomenon":"按下启动按钮后，模拟执行元件没有形成动作条件。","nodes":("保护条件","停止条件","启动请求","执行元件"),"card_ids":("diagram_symbols","button_contacts","contactor_coil"),"steps":(
        _step("dol_roles_scope","第一步应先识别哪类上游角色？",("保护条件","执行元件","无关分支"),"保护条件","保护条件位于公共路径上游。"),
        _step("dol_roles_signal","保护条件正常后，哪个角色表达启动意图？",("启动请求","停止条件","执行元件"),"启动请求","启动按钮的抽象角色是提供启动请求。"),
        _step("dol_roles_end","逻辑链末端应关注哪个角色？",("执行元件","保护条件","启动请求"),"执行元件","前序条件满足后才判断执行元件。"))},
    "jog_roles": {"chapter_id":"diagram_symbols_roles","title":"点动与连续：区分共享角色","phenomenon":"点动和连续运行两种方式均不能形成模拟动作条件。","nodes":("公共条件","方式选择","保持分支","执行元件"),"card_ids":("diagram_symbols","jog_control"),"steps":(
        _step("jog_roles_scope","两种方式共同异常时先看哪一类？",("公共条件","只看点动分支","只看保持分支"),"公共条件","共同异常优先指向共享的上游条件。"),
        _step("jog_roles_branch","公共条件正常后，区分运行方式需要观察什么？",("方式选择","真实导线长度","设备安装位置"),"方式选择","点动与连续使用不同的请求或保持逻辑。"),
        _step("jog_roles_end","两个方式最后共同到达哪类角色？",("执行元件","保持分支","方式按钮"),"执行元件","不同方式最终共享同一抽象执行角色。"))},
    "dol_series": {"chapter_id":"series_parallel_logic","title":"直接启动：追踪串联中断","phenomenon":"模拟资料显示公共电源正常，但保护触点条件未满足。","nodes":("控制电源","保护触点","停止条件","启动请求","执行元件"),"card_ids":("series_logic","thermal_relay"),"steps":(
        _step("dol_series_start","控制电源正常后沿串联路径检查哪里？",("保护触点","直接跳到执行元件","并联保持分支"),"保护触点","串联路径应按上游到下游逐项确认。"),
        _step("dol_series_state","保护触点条件未满足时，路径状态是？",("在此中断","仍然完整","自动转入其他分支"),"在此中断","串联条件任一不满足都会阻断后续逻辑。"),
        _step("dol_series_result","此时是否应继续确定启动按钮故障？",("不应，当前证据已定位上游中断","应直接确定","应真实送电验证"),"不应，当前证据已定位上游中断","无需越过已确认的上游中断猜测下游故障。"))},
    "hold_parallel": {"chapter_id":"series_parallel_logic","title":"连续运行：理解保持分支","phenomenon":"启动请求能够短暂形成，但请求消失后模拟运行条件不能维持。","nodes":("公共条件","启动请求","保持分支","执行元件"),"card_ids":("parallel_logic","self_hold"),"steps":(
        _step("hold_parallel_scope","短暂启动说明哪部分曾经满足？",("公共条件与启动请求","保持分支一定正常","执行元件一定损坏"),"公共条件与启动请求","能够短暂形成说明初始启动路径曾有效。"),
        _step("hold_parallel_branch","请求消失后应由哪条可选路径维持？",("保持分支","停止条件","无关方式分支"),"保持分支","连续运行依靠并联的保持条件延续逻辑。"),
        _step("hold_parallel_break","不能维持时最相关的逻辑中断点是？",("保持分支","公共电源必然缺失","点动按钮"),"保持分支","现象直接对应保持路径不能形成。"))},
    "reverse_common": {"chapter_id":"control_path_tracing","title":"正反转：追踪公共路径","phenomenon":"正转和反转两个方向均不能形成模拟启动条件。","nodes":("公共条件","方向选择","互锁条件","方向执行元件"),"card_ids":("logic_tracing","forward_reverse"),"steps":(
        _step("reverse_common_scope","两个方向共同异常，先选择哪条范围？",("公共路径","只选正转分支","只选反转分支"),"公共路径","两个方向共享公共条件。"),
        _step("reverse_common_order","公共路径中应采用什么顺序？",("从上游条件逐项向下游","从结果随机猜测","先检查无关方向"),"从上游条件逐项向下游","顺序追踪能减少无依据结论。"),
        _step("reverse_common_break","公共条件已显示异常，下一步结论应是？",("公共路径在该条件中断","两个方向线圈都损坏","继续检查方向按钮"),"公共路径在该条件中断","当前证据已解释两个方向共同异常。"))},
    "reverse_branch": {"chapter_id":"control_path_tracing","title":"正反转：进入相关方向分支","phenomenon":"公共条件正常，反转可以形成条件，但正转不能形成启动条件。","nodes":("公共条件","正转分支","正转互锁","正转执行元件"),"card_ids":("logic_tracing","electrical_interlock"),"steps":(
        _step("reverse_branch_scope","根据现象应进入哪个局部分支？",("正转分支","反转分支","所有公共条件"),"正转分支","单一方向异常应进入对应方向分支。"),
        _step("reverse_branch_order","正转请求正常后应检查哪个逻辑条件？",("正转互锁条件","反转执行元件","云端记录"),"正转互锁条件","方向请求后应沿对应互锁条件继续追踪。"),
        _step("reverse_branch_break","互锁条件模拟状态异常时，中断点在哪里？",("正转互锁条件","公共电源","反转按钮"),"正转互锁条件","模拟证据把中断点限定在正转分支的互锁条件。"))},
}

@dataclass
class DiagramTrainingSession:
    case_id: str
    training_id: str = field(default_factory=lambda: secrets.token_hex(12))
    index: int = 0
    first_answers: dict[str, str] = field(default_factory=dict)
    wrong_steps: list[str] = field(default_factory=list)
    step_solved: bool = False
    @property
    def case(self) -> dict[str, Any]: return DIAGRAM_CASES[self.case_id]
    @property
    def is_complete(self) -> bool: return self.index >= len(self.case["steps"])
    @property
    def current_step(self) -> dict[str, Any] | None: return None if self.is_complete else self.case["steps"][self.index]
    @property
    def correct_steps(self) -> int: return len(self.case["steps"]) - len(self.wrong_steps)
    def answer(self, selected: str) -> bool:
        step = self.current_step
        if step is None: raise ValueError("识图训练已经完成")
        if selected not in step["options"]: raise ValueError("答案不属于当前步骤选项")
        if step["id"] not in self.first_answers:
            self.first_answers[step["id"]] = selected
            if selected != step["answer"]: self.wrong_steps.append(step["id"])
        self.step_solved = selected == step["answer"]
        return self.step_solved
    def next_step(self) -> None:
        if not self.step_solved: raise ValueError("请先完成当前步骤")
        self.index += 1; self.step_solved = False
    def to_dict(self) -> dict[str, Any]:
        return {"case_id":self.case_id,"training_id":self.training_id,"index":self.index,"first_answers":dict(self.first_answers),"wrong_steps":list(self.wrong_steps),"step_solved":self.step_solved}
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DiagramTrainingSession":
        if data.get("case_id") not in DIAGRAM_CASES: raise ValueError("未知识图案例")
        return cls(data["case_id"],str(data["training_id"]),int(data["index"]),dict(data.get("first_answers",{})),list(data.get("wrong_steps",[])),bool(data.get("step_solved",False)))

def cases_for_chapter(chapter_id: str) -> tuple[dict[str, Any], ...]:
    return tuple({"id":case_id,**case} for case_id,case in DIAGRAM_CASES.items() if case["chapter_id"] == chapter_id)

def diagram_lesson_for_chapter(chapter_id: str) -> dict[str, object] | None:
    cases = cases_for_chapter(chapter_id)
    return None if not cases else {"title":"从功能角色到完整控制路径","flows":tuple(case["nodes"] for case in cases)}

def validate_diagram_cases() -> None:
    for case_id,case in DIAGRAM_CASES.items():
        ids=[step["id"] for step in case["steps"]]
        if not ids or len(ids)!=len(set(ids)): raise ValueError(f"识图案例步骤无效：{case_id}")
        for step in case["steps"]:
            if step["answer"] not in step["options"] or len(step["options"]) not in {2,3}: raise ValueError(f"识图案例选项无效：{case_id}")
validate_diagram_cases()
