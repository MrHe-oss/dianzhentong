"""教材项目1的原创逻辑公式、例题和变式练习。不得冒充教材原题。"""
from __future__ import annotations

from typing import Any


LOGIC_FORMULAS: dict[str, tuple[dict[str, Any], ...]] = {
    "series_logic": ({
        "title": "串联条件的逻辑表达", "expression": r"Y=A\land B\land C",
        "symbols": ("Y：输出条件", "A、B、C：串联的各个必要条件"),
        "meaning": "只有A、B、C全部成立时，输出Y才成立。",
    },),
    "parallel_logic": ({
        "title": "并联分支的逻辑表达", "expression": r"Y=A\lor B",
        "symbols": ("Y：输出条件", "A、B：两条可选分支"),
        "meaning": "A或B任一分支成立，就能为输出Y提供逻辑路径。",
    },),
    "self_hold": ({
        "title": "自锁保持的抽象表达", "expression": r"KM=C\land(SB\lor KM_a)",
        "symbols": ("KM：接触器动作条件", "C：公共条件", "SB：启动请求", "KMₐ：保持辅助触点"),
        "meaning": "公共条件成立时，启动请求或保持分支任一成立，都可维持KM条件。",
    },),
    "electrical_interlock": ({
        "title": "正转支路的互锁表达", "expression": r"K_F=C\land S_F\land\lnot K_R",
        "symbols": ("K_F：正转条件", "C：公共条件", "S_F：正转请求", "K_R：反转状态"),
        "meaning": "正转请求成立且反转未动作时，正转支路才允许建立。",
    },),
    "star_delta_interlock": ({
        "title": "星形与三角的互斥约束", "expression": r"K_Y\land K_\Delta=0",
        "symbols": ("Kᵧ：星形阶段状态", "KΔ：三角阶段状态", "0：不允许同时成立"),
        "meaning": "星形与三角两个互斥阶段不能同时有效。",
    },),
}


UNIT_EXAMPLES: dict[int, dict[str, Any]] = {
    0: {
        "title": "原创例题：直接启动公共条件分析",
        "scenario": "抽象状态卡显示：控制电源、熔断器和热继电器条件成立，停止条件成立，但启动请求尚未出现。判断接触器动作条件是否成立。",
        "steps": (
            "写出抽象关系：KM=公共条件∧(启动请求∨保持条件)。",
            "公共条件均成立，但当前既没有启动请求，也没有已建立的保持条件。",
            "括号内逻辑或为假，因此KM动作条件不成立。",
        ),
        "answer": "接触器动作条件暂不成立；这是缺少启动请求的正常逻辑状态，不等同于元件故障。",
        "practice": "若公共条件成立且启动请求出现，KM动作条件应如何变化？",
        "options": ("成立", "必然保持不成立", "无法讨论任何逻辑"), "practice_answer": "成立",
        "practice_explanation": "公共条件与启动请求同时成立，满足首次动作所需的逻辑条件。",
    },
    1: {
        "title": "原创例题：正反转方向分支分析",
        "scenario": "正转能够建立，反转不能建立；抽象资料显示反转请求存在，但正转接触器仍处于动作状态。判断反转支路为何被限制。",
        "steps": (
            "正转能够建立，为公共条件成立提供了证据。",
            "反转表达式包含“正转未动作”这一互锁条件。",
            "当前正转仍动作，因此互锁条件不成立，反转支路被正常抑制。",
        ),
        "answer": "反转不能同时建立是互锁逻辑的预期结果，不能据此直接判定反转元件故障。",
        "practice": "正转状态退出后，分析反转请求时下一步最应确认什么？",
        "options": ("反转支路条件", "设备颜色", "重新假定公共条件全部故障"), "practice_answer": "反转支路条件",
        "practice_explanation": "公共条件已有正常证据，应继续检查反转请求、互锁和执行条件。",
    },
    2: {
        "title": "原创例题：星—三角阶段转换分析",
        "scenario": "抽象时序显示计时条件已满足，但星形阶段仍未退出。此时是否允许三角阶段建立？",
        "steps": (
            "识别互斥约束：星形与三角不能同时有效。",
            "计时完成只提供转换条件，不能替代阶段退出和互锁条件。",
            "星形仍有效时，三角阶段应继续被限制。",
        ),
        "answer": "不允许建立三角阶段；应先满足星形退出条件，再进入三角阶段。",
        "practice": "正确的抽象转换顺序是哪一项？",
        "options": ("星形退出→三角进入", "星形与三角同时进入", "三角进入→星形退出"), "practice_answer": "星形退出→三角进入",
        "practice_explanation": "先退出星形再进入三角，才能满足阶段互斥约束。",
    },
}


def formulas_for_topic(topic_id: str) -> tuple[dict[str, Any], ...]:
    return LOGIC_FORMULAS.get(topic_id, tuple())


def example_for_unit(unit_index: int) -> dict[str, Any]:
    return UNIT_EXAMPLES[unit_index]


def validate_examples() -> None:
    for example in UNIT_EXAMPLES.values():
        if example["practice_answer"] not in example["options"] or len(example["steps"]) < 3:
            raise ValueError("原创例题结构无效")


validate_examples()
