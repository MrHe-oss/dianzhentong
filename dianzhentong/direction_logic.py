"""正反转单元的原创、离散教学模型；不代表真实电机状态。"""
from .plc_lab import hold_next

TOPICS = ("direction_requests", "direction_exclusion", "direction_transition")
STATES = ("停止", "正向", "反向")


def direction_next(previous, allow, stop, forward, reverse):
    """一次明确的模型计算；停止/不允许/冲突优先，不直接换向。"""
    if previous not in STATES:
        raise ValueError("未知教学状态")
    if any(type(value) is not bool for value in (allow, stop, forward, reverse)):
        raise ValueError("输入必须为布尔量")
    if stop or not allow or (forward and reverse):
        state = "停止"
        reason = "停止条件成立" if stop else "公共允许不成立" if not allow else "双向请求冲突：本题规定停止"
    elif hold_next(allow, stop, forward and previous == "停止", previous == "正向"):
        state, reason = "正向", "保持原正向状态，反向请求不能直接换向" if previous == "正向" else "停止状态下只有正向请求"
    elif hold_next(allow, stop, reverse and previous == "停止", previous == "反向"):
        state, reason = "反向", "保持原反向状态，正向请求不能直接换向" if previous == "反向" else "停止状态下只有反向请求"
    else:
        state, reason = "停止", "没有方向请求，保持停止"
    return {"state": state, "forward": state == "正向", "reverse": state == "反向", "reason": reason}


def _q(qid, stem, options, explanation, topic, wrong):
    titles = dict(zip(TOPICS, ("方向请求与状态", "方向互斥与冲突", "停止与逻辑换向")))
    return dict(id=qid, chapter_id="p3_unit_2", stem=stem, options=options,
                answer=options[0], explanation=explanation, knowledge_point=titles[topic], card=topic, wrong=wrong)


QUESTION_SPECS = (
    _q("direction_example", "本单元模型原为正向，允许真、停止假，只有反向请求；计算后状态是什么？",
       ("仍为正向", "直接反向", "两个方向都有效"), "当前方向保持，反向请求不能绕过停止状态。", TOPICS[2],
       ("本题要求先经过停止状态，不能直接换向。", "模型状态互斥，不允许两个方向同时有效。")),
    _q("direction_request_state", "模型已经正向；允许真、停止假，两个请求都撤回，下一状态是什么？",
       ("保持正向", "必定停止", "变为反向"), "本单元明确使用上一状态保持，撤回请求不等于停止；与上一单元无记忆模型不同。", TOPICS[0],
       ("这里有明确保持规则，不能套用无记忆赋值例题。", "没有从停止状态进入反向的条件。")),
    _q("direction_stop_priority", "原为反向，允许真、停止真、正向请求真、反向请求假，下一状态是什么？",
       ("停止", "正向", "保持反向"), "停止条件先于请求和保持条件处理。", TOPICS[2],
       ("正向请求不能越过停止条件。", "停止会撤销原状态，不继续保持。")),
    _q("direction_conflict", "本单元规定双向请求冲突时停止。原为停止，允许真、停止假，两个请求都真，结果是什么？",
       ("停止", "正向优先", "按选框先后决定"), "双向请求同时为真触发本题冲突规则；这不是所有控制系统的统一策略。", TOPICS[1],
       ("题设没有正向优先，而是冲突时停止。", "计算读取同一组条件，不按勾选先后仲裁。")),
    _q("direction_allow", "原为正向，公共允许变假，停止假且正向请求真，下一状态是什么？",
       ("停止", "保持正向", "反向"), "公共允许是全部运行状态的前提，不满足时退出保持。", TOPICS[1],
       ("保持不能绕过公共允许条件。", "失去允许不是反向命令，两个方向都应无效。")),
    _q("direction_sequence", "原为反向，以下哪组计算能使本教学模型进入正向？",
       ("先计算停止；再在允许真、停止假且仅正向请求真时计算", "只撤回反向请求", "反向状态下仅提出正向请求"),
       "先有一个停止逻辑状态，再满足单一正向请求。模型停止不证明真实电机停稳。", TOPICS[2],
       ("撤回请求不撤销明确的状态保持。", "反向保持期间正向请求不能直接换向。")),
    _q("direction_exclusive", "本模型每次只有停止、正向、反向一个状态，这能保证哪项？",
       ("两个抽象方向标志不会同时为真", "真实设备绝无故障", "无需真实安全措施"),
       "互斥只针对模型输出，不能证明真实系统安全。", TOPICS[1],
       ("抽象模型没有检测真实设备，不能保证其无故障。", "模型不能替代任何现场安全要求。")),
    _q("direction_snapshot", "互动中只改变请求选框，尚未按‘计算下一步’，屏幕保留上次状态，应怎样理解？",
       ("输入待计算；状态仅在明确计算时更新", "请求与状态永远相同", "代表真实CPU延时"),
       "这是逐步观察工具；选框是待计算输入，不是实时控制，也不模拟真实CPU时序。", TOPICS[0],
       ("请求是输入，状态还受历史和规则约束，二者不能混同。", "手动计算节奏是教学设计，不是CPU时间测量。")),
)
OPTION_FEEDBACK = {q["id"]: dict(zip(q["options"][1:], q["wrong"])) for q in QUESTION_SPECS}
