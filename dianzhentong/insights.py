"""诊断结论的学习解释；只补充教学内容，不参与故障树转移。"""

from __future__ import annotations


RESULT_INSIGHTS: dict[str, dict[str, str]] = {
    "cause_control_power": {
        "why": "控制电源是整条控制回路的上游条件。它缺失时，按钮、保护触点和接触器线圈即使正常，也不能形成完整的控制条件。",
        "confusion": "容易与熔断器断路混淆：两者都可影响后续元件，但应分别依据控制电源状态卡和熔断器通断卡判断。",
        "memory": "先电源，后元件；上游不成立，下游先不猜。",
    },
    "cause_fuse": {
        "why": "控制电源条件正常，但熔断器模拟为不导通，说明控制路径在熔断器处中断。",
        "confusion": "容易与控制电源缺失混淆：前者是通路元件的模拟通断异常，后者是整体电源条件不成立。",
        "memory": "电源有条件，熔断器还要有通路。",
    },
    "cause_thermal": {
        "why": "热继电器动作后，常闭保护触点断开，控制路径因此不能继续形成。",
        "confusion": "容易与停止按钮常闭触点断路混淆：两者都是公共常闭条件，需根据各自的模拟状态卡定位。",
        "memory": "保护一动作，常闭就断开；先查原因，不盲目复位。",
    },
    "cause_stop": {
        "why": "停止按钮未按下时，其常闭触点应保持导通；模拟结果不导通，会截断后续控制路径。",
        "confusion": "容易把未按下误判为触点应断开。停止按钮检查的是常闭触点，未动作时应闭合。",
        "memory": "停止用常闭：不按是通，按下才断。",
    },
    "cause_start": {
        "why": "启动按钮按下后，常开触点应闭合；模拟结果仍不导通，启动信号无法向后传递。",
        "confusion": "容易与接触器线圈断路混淆：按钮异常是启动信号没有形成，线圈异常是前序信号正常后的下游问题。",
        "memory": "启动用常开：不按是断，按下应通。",
    },
    "cause_coil": {
        "why": "电源、保护和按钮条件均正常，但线圈模拟连续性异常，因此无法形成题设要求的电磁动作条件。",
        "confusion": "容易过早怀疑线圈。只有前序公共条件和按钮信号均正常时，线圈的异常结果才有足够解释力。",
        "memory": "线圈放在下游查，前面正常再定它。",
    },
    "fr_cause_fuse": {
        "why": "熔断器位于正转和反转共用的控制路径中，模拟断路会同时破坏两个方向的工作条件。",
        "confusion": "容易误查某一方向按钮。当两个方向都不能启动时，应先看公共条件。",
        "memory": "两向都失效，先查公共路。",
    },
    "fr_cause_thermal": {
        "why": "热继电器常闭保护触点是两个方向的共用条件，其模拟断开会使正反转支路同时不成立。",
        "confusion": "容易与公共熔断器或停止按钮异常混淆；关键是对应状态卡显示了哪个公共节点异常。",
        "memory": "保护触点共用，一断就影响两向。",
    },
    "fr_cause_stop": {
        "why": "停止按钮常闭触点串入正反转公共控制条件，其不导通时两个方向都无法形成后续路径。",
        "confusion": "容易将停止按钮异常当成某一方向按钮异常。前者是公共节点，后者只影响对应方向。",
        "memory": "停止按钮管两向，方向按钮管一边。",
    },
    "fr_cause_forward_button": {
        "why": "公共条件正常，但正转按钮按下后的常开触点仍不导通，正转启动信号无法形成。",
        "confusion": "容易与正转线圈异常混淆。先根据按钮通断卡确认启动信号，再看线圈连续性。",
        "memory": "只有正转不启动，沿正转支路查。",
    },
    "fr_cause_reverse_button": {
        "why": "公共条件正常，但反转按钮按下后的常开触点仍不导通，反转启动信号无法形成。",
        "confusion": "容易进入无关的正转支路。题设已说明正转正常时，应聚焦反转方向条件。",
        "memory": "只有反转不启动，沿反转支路查。",
    },
    "fr_cause_forward_coil": {
        "why": "正转支路前序条件均正常，但正转接触器线圈模拟连续性异常，无法形成正转动作条件。",
        "confusion": "容易与正转按钮异常混淆：按钮决定信号是否发出，线圈是接收前序条件后的下游对象。",
        "memory": "按钮正常再看线圈，方向一定要对应。",
    },
    "fr_cause_reverse_coil": {
        "why": "反转支路前序条件均正常，但反转接触器线圈模拟连续性异常，无法形成反转动作条件。",
        "confusion": "容易误看正转线圈。诊断对象必须与反转不能启动的故障现象对应。",
        "memory": "哪个方向失效，就核对哪个方向的线圈。",
    },
    "fr_cause_interlock": {
        "why": "反转接触器未动作时，位于正转支路的反转常闭互锁触点应导通；模拟不导通会阻断正转支路。",
        "confusion": "容易把互锁异常当成线圈异常。互锁是串入对应支路的允许条件，不是线圈本身。",
        "memory": "查本方向，看另一方向的常闭互锁。",
    },
}


def insight_for_result(result_id: str | None) -> dict[str, str] | None:
    """返回结论的学习解释；证据不足结论不伪造固定解释。"""
    return RESULT_INSIGHTS.get(result_id or "")


def validate_result_insights(expected_result_ids: set[str]) -> None:
    if set(RESULT_INSIGHTS) != expected_result_ids:
        missing = expected_result_ids - set(RESULT_INSIGHTS)
        extra = set(RESULT_INSIGHTS) - expected_result_ids
        raise ValueError(f"学习解释与故障结论不一致：缺少={missing}，多余={extra}")
    for result_id, item in RESULT_INSIGHTS.items():
        missing_fields = {"why", "confusion", "memory"} - set(item)
        if missing_fields or any(not value.strip() for value in item.values()):
            raise ValueError(f"学习解释 {result_id} 不完整：{missing_fields}")
