"""知识卡、错题关联和安全的控制逻辑关系示意。"""

from __future__ import annotations

from typing import Any, Iterable


REVIEW_STATUS = "教学内容已录入，待专业人员复核"

KNOWLEDGE_CARDS: dict[str, dict[str, str]] = {
    "control_power": {
        "title": "控制电源",
        "principle": "控制电源为按钮、保护触点和接触器线圈组成的控制路径提供工作条件。",
        "role": "它位于控制逻辑的上游；条件缺失时，后续元件即使正常也不能形成完整控制过程。",
        "normal": "模拟资料显示控制回路具备题设规定的电源条件。",
        "abnormal": "模拟资料显示控制回路电源条件不可用，后续公共控制路径失去工作前提。",
        "review": "先确认上游公共条件，再检查下游元件，可以避免无依据地更换元件。",
    },
    "fuse": {
        "title": "控制回路熔断器",
        "principle": "熔断器在异常电流作用下断开，用于限制故障影响并保护控制回路。",
        "role": "它通常属于公共控制路径；断路时，接触器线圈无法获得完整控制条件。",
        "normal": "断电模拟通断资料显示熔断器导通。",
        "abnormal": "模拟通断资料显示熔断器不导通，控制路径在此处中断。",
        "review": "教学判断关注模拟通断状态，不推导真实设备的更换或送电操作。",
    },
    "thermal_relay": {
        "title": "热继电器保护触点",
        "principle": "热继电器动作后，其常闭保护触点通常断开控制路径，阻止接触器继续动作。",
        "role": "它反映过载保护状态，直接启动与正反转控制通常都会把它放在公共控制条件中。",
        "normal": "模拟状态显示热继电器已复位，常闭保护触点闭合。",
        "abnormal": "模拟状态显示保护动作存在，常闭保护触点断开。",
        "review": "保护动作代表需要查明原因；本原型不指导真实复位。",
    },
    "button_contacts": {
        "title": "启动与停止按钮触点",
        "principle": "常开触点在未动作时断开、动作时闭合；常闭触点在未动作时闭合、动作时断开。",
        "role": "停止按钮常闭触点维持公共路径，启动按钮常开触点提供对应方向的启动信号。",
        "normal": "按钮处于题设状态时，模拟通断结果与常开、常闭逻辑一致。",
        "abnormal": "按钮动作状态与模拟通断结果不一致，控制信号不能按预期传递。",
        "review": "判断前先明确按钮是否按下，再判断该触点在此状态下应当闭合还是断开。",
    },
    "contactor_coil": {
        "title": "接触器线圈",
        "principle": "接触器线圈在具备控制条件后产生磁力，驱动主触点和辅助触点改变状态。",
        "role": "它位于控制判断的下游；只有前序电源、保护和按钮条件正常后，检查线圈才有解释力。",
        "normal": "模拟连续性资料显示线圈连续，且题设型号条件一致。",
        "abnormal": "模拟连续性资料显示线圈不连续，不能形成题设要求的动作条件。",
        "review": "本卡只解释模拟逻辑，不提供真实线圈测量或拆卸步骤。",
    },
    "self_hold": {
        "title": "自锁控制",
        "principle": "接触器的常开辅助触点可在启动信号消失后维持线圈控制路径，这种逻辑称为自锁。",
        "role": "自锁常用于保持运行状态；其异常更典型的现象是松开启动按钮后停止，而非完全不能启动。",
        "normal": "教学逻辑中，接触器动作后辅助触点形成保持条件。",
        "abnormal": "保持条件不能形成时，按钮释放后控制状态不能维持。",
        "review": "当前两个实验未把自锁异常列为随机故障，本卡用于理解控制关系。",
    },
    "electrical_interlock": {
        "title": "电气互锁",
        "principle": "电气互锁利用另一方向接触器的常闭辅助触点，阻止正转和反转接触器同时形成动作条件。",
        "role": "它把两个方向的控制支路相互约束，是正反转控制的重要安全逻辑。",
        "normal": "另一方向接触器未动作时，模拟互锁常闭触点导通；动作后应断开。",
        "abnormal": "另一方向未动作，但模拟互锁常闭触点仍不导通，对应方向的控制路径被阻断。",
        "review": "严禁把短接互锁当作验证方法；本原型只展示模拟状态。",
    },
    "forward_reverse": {
        "title": "正反转控制逻辑",
        "principle": "正反转控制通过两个接触器形成不同方向的控制支路，并用互锁防止两个方向同时动作。",
        "role": "公共电源、熔断器、保护和停止按钮影响两个方向；方向按钮、线圈和互锁影响对应支路。",
        "normal": "公共条件正常后，所选方向支路能够按按钮、互锁和线圈的顺序形成控制逻辑。",
        "abnormal": "先根据一个方向还是两个方向不能启动，区分公共条件与方向支路问题。",
        "review": "先按故障现象选分支，再沿公共条件到方向条件排查，避免进入无关方向。",
    },
    "jog_control": {
        "title": "点动与连续运行",
        "principle": "点动在按钮保持动作时建立运行条件，释放后结束；连续运行则通过自锁辅助触点维持控制条件。",
        "role": "两种方式共享公共保护与接触器线圈，但按钮请求和保持逻辑不同。",
        "normal": "模拟资料能区分点动请求、连续启动请求和连续保持状态。",
        "abnormal": "根据一个方式还是两个方式异常，区分公共条件、按钮支路与自锁逻辑。",
        "review": "先判断故障现象属于公共部分还是单一运行方式，再沿对应模拟逻辑排查。",
    },
    "diagram_symbols": {
        "title": "图形符号与功能角色",
        "principle": "识读控制图时，先区分保护条件、操作信号、辅助触点和执行元件等功能角色。",
        "role": "功能角色帮助理解元件在逻辑链中的位置，比孤立记忆图形更容易迁移到不同控制任务。",
        "normal": "能够根据题目说明区分公共条件、分支条件和最终执行元件。",
        "abnormal": "只凭外形猜测作用，或把抽象逻辑位置当成真实端子和导线位置。",
        "review": "本卡不展示端子号、电压或真实接线，只训练教学图中的功能识别。",
    },
    "series_logic": {
        "title": "串联条件：逻辑与",
        "principle": "多个条件串联在同一抽象路径中，通常表示这些条件需要同时满足。",
        "role": "公共保护和停止条件常作为上游串联条件，一个条件中断即可阻断后续逻辑。",
        "normal": "沿路径逐项确认，每个串联条件均满足后才继续判断执行元件。",
        "abnormal": "跳过上游异常，直接把结果归因于最末端元件。",
        "review": "串联关系只表达逻辑与，不对应真实布线距离或安装位置。",
    },
    "parallel_logic": {
        "title": "并联分支：逻辑或",
        "principle": "抽象路径出现并联分支时，通常表示存在两条或多条可选的条件路径。",
        "role": "启动请求与保持条件可形成不同分支；应根据当前状态判断哪条分支应有效。",
        "normal": "先确认公共条件，再结合题设状态判断对应分支是否能够形成逻辑路径。",
        "abnormal": "把一条分支异常误判为所有公共条件均异常，或检查与现象无关的分支。",
        "review": "严禁把并联概念理解为指导真实跨接，本卡仅描述教学逻辑。",
    },
    "logic_tracing": {
        "title": "控制路径追踪",
        "principle": "从现象出发，按公共条件、相关分支和执行元件的顺序追踪控制逻辑。",
        "role": "路径追踪把元件知识组织成证据链，可减少无关检查和无依据结论。",
        "normal": "每一步都能说明检查对象、预期状态、模拟证据和下一步分支。",
        "abnormal": "从结果倒猜元件、越过公共条件，或在证据不足时强行确定结论。",
        "review": "路径只服务网页教学模拟，不可作为真实设备检修或送电依据。",
    },
}

NODE_CARD_MAP: dict[str, str] = {
    "control_power": "control_power",
    "fuse": "fuse", "fr_fuse": "fuse",
    "thermal_relay": "thermal_relay", "fr_thermal": "thermal_relay",
    "stop_button": "button_contacts", "start_button": "button_contacts",
    "fr_stop": "button_contacts", "fr_forward_button": "button_contacts",
    "fr_reverse_button": "button_contacts",
    "contactor_coil": "contactor_coil", "fr_forward_coil": "contactor_coil",
    "fr_reverse_coil": "contactor_coil",
    "fr_interlock": "electrical_interlock",
    "jc_public_condition": "control_power", "jc_stop": "button_contacts",
    "jc_jog_button": "jog_control", "jc_continuous_button": "button_contacts",
    "jc_self_hold": "self_hold", "jc_coil": "contactor_coil",
}

EXPERIMENT_CARD_ORDER = {
    "motor_dol_no_start": (
        "control_power", "fuse", "thermal_relay", "button_contacts",
        "contactor_coil", "self_hold",
    ),
    "motor_forward_reverse": (
        "fuse", "thermal_relay", "button_contacts", "contactor_coil",
        "electrical_interlock", "forward_reverse", "self_hold",
    ),
    "motor_jog_continuous": (
        "control_power", "button_contacts", "contactor_coil", "self_hold", "jog_control",
    ),
}

RELATIONSHIP_STEPS = {
    "motor_dol_no_start": (
        "控制电源", "熔断器", "热继电器保护", "停止按钮", "启动按钮", "接触器线圈",
    ),
    "motor_forward_reverse": (
        "公共控制条件", "方向启动按钮", "另一方向互锁触点", "对应接触器线圈",
    ),
    "motor_jog_continuous": (
        "公共控制条件", "停止按钮", "点动或连续启动请求", "自锁保持条件", "接触器线圈",
    ),
}


def cards_for_experiment(experiment_id: str) -> tuple[dict[str, str], ...]:
    return tuple(
        {"id": card_id, **KNOWLEDGE_CARDS[card_id]}
        for card_id in EXPERIMENT_CARD_ORDER[experiment_id]
    )


def card_for_node(node_id: str) -> dict[str, str] | None:
    card_id = NODE_CARD_MAP.get(node_id)
    return {"id": card_id, **KNOWLEDGE_CARDS[card_id]} if card_id else None


def review_cards(node_ids: Iterable[str]) -> tuple[dict[str, str], ...]:
    card_ids: list[str] = []
    for node_id in node_ids:
        card_id = NODE_CARD_MAP.get(node_id)
        if card_id and card_id not in card_ids:
            card_ids.append(card_id)
    return tuple({"id": item, **KNOWLEDGE_CARDS[item]} for item in card_ids)


def relationship_steps(experiment_id: str) -> tuple[str, ...]:
    return RELATIONSHIP_STEPS[experiment_id]


def validate_learning_content() -> None:
    for card_id, card in KNOWLEDGE_CARDS.items():
        missing = {"title", "principle", "role", "normal", "abnormal", "review"} - set(card)
        if missing:
            raise ValueError(f"知识卡 {card_id} 缺少字段：{missing}")
    unknown = set(NODE_CARD_MAP.values()) - set(KNOWLEDGE_CARDS)
    if unknown:
        raise ValueError(f"节点关联到未知知识卡：{unknown}")


validate_learning_content()
