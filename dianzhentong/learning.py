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
    "star_delta_principle": {
        "title": "星—三角降压启动原理",
        "principle": "启动阶段采用星形状态以降低启动影响，电动机加速后再转换到三角运行状态。",
        "role": "这种方式同时降低启动电流和启动转矩，适用性取决于电动机条件与启动负载特征。",
        "normal": "模拟资料显示启动负载较轻，且题设明确允许随后进入三角运行阶段。",
        "abnormal": "忽略启动转矩也会降低，或把所有三相异步电动机都视为适用对象。",
        "review": "本卡只解释通用原理，不提供电机选型、参数计算或真实接线判断。",
    },
    "star_delta_components": {
        "title": "主、星形与三角接触器角色",
        "principle": "典型星—三角启动逻辑包含主接触器、星形接触器和三角接触器三个功能角色。",
        "role": "主接触器承担公共运行条件；星形接触器服务启动阶段；三角接触器服务转换后的运行阶段。",
        "normal": "能够只按抽象功能角色区分公共、启动阶段和运行阶段。",
        "abnormal": "把三个接触器视为同时动作，或只凭图形位置猜测其作用。",
        "review": "先判断当前阶段，再判断哪个角色应有效；不得据此进行真实接线。",
    },
    "star_delta_timing": {
        "title": "星—三角时间转换",
        "principle": "时间控制用于结束星形启动阶段并触发向三角运行阶段的转换。",
        "role": "它表达阶段转换条件，而不是保护元件，也不表示星形与三角能够同时有效。",
        "normal": "启动请求建立后先进入星形阶段，满足题设转换条件后退出星形并进入三角阶段。",
        "abnormal": "跳过星形阶段、把定时器当作过载保护，或认为转换条件允许两阶段重叠。",
        "review": "首版不讲时间整定值，只训练阶段先后关系。",
    },
    "star_delta_interlock": {
        "title": "星形与三角互锁",
        "principle": "互锁约束用于阻止星形接触器和三角接触器同时形成动作条件。",
        "role": "它与时间顺序共同保证抽象逻辑只能处于相应启动阶段或运行阶段。",
        "normal": "星形阶段只允许星形角色有效；转换后星形退出，三角角色才进入有效状态。",
        "abnormal": "模拟逻辑出现星形与三角两个角色同时有效，或没有先退出前一阶段。",
        "review": "严禁把短接互锁作为学习或验证方法，本卡不提供真实操作步骤。",
    },
    "timer_role": {
        "title": "时间继电器的抽象角色",
        "principle": "时间继电器根据输入条件和等待过程改变输出状态，把时间关系加入控制逻辑。",
        "role": "它负责表达延时条件，不替代保护元件，也不自动决定完整控制顺序。",
        "normal": "先识别输入条件，再判断是否处于等待阶段，最后确认输出状态是否已经改变。",
        "abnormal": "把计时开始误认为输出已经形成，或把时间继电器当作保护元件。",
        "review": "本卡只学习抽象时序，不提供型号选择、具体时间值或真实整定方法。",
    },
    "on_delay": {
        "title": "通电延时逻辑",
        "principle": "输入条件形成后开始等待，等待过程结束后，延时输出才改变状态。",
        "role": "用于表达某个后续阶段需要在输入条件持续满足一段过程后才能形成。",
        "normal": "输入形成、进入等待、条件到达、输出改变，四个状态按顺序出现。",
        "abnormal": "输入刚形成就判断延时输出已经改变，或忽略输入提前消失后的复位关系。",
        "review": "重点记忆动作时点，不学习具体整定值和真实触点标识。",
    },
    "off_delay": {
        "title": "断电延时逻辑",
        "principle": "输入条件撤销后开始等待，延时输出在等待期间暂时保持，结束后再改变状态。",
        "role": "用于表达请求撤销后，某个输出条件仍需保持一段过程再退出。",
        "normal": "输入撤销、进入保持等待、条件到达、输出退出，状态顺序清晰。",
        "abnormal": "把输入撤销立即等同于输出退出，或与通电延时的触发时点混淆。",
        "review": "只比较输入与输出的先后关系，不提供真实回路操作信息。",
    },
    "sequence_control": {
        "title": "顺序控制与阶段条件",
        "principle": "顺序控制要求多个执行阶段按照公共条件、前序状态和转换条件依次形成。",
        "role": "时间条件可以成为后续阶段的允许条件，但保护和停止条件仍属于公共约束。",
        "normal": "先确认公共条件，再识别当前阶段，最后判断后续阶段的允许条件。",
        "abnormal": "把顺序控制理解为所有角色同时动作，或越过公共条件直接判断后续阶段。",
        "review": "本卡只描述教学逻辑，不表示真实导线走向或现场操作顺序。",
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
