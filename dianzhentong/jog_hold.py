"""点动与长动的独立教学模型、原创题库；不控制设备。"""
from .plc_lab import hold_next

TOPICS = ("plc_jog_request", "plc_continuous_hold", "plc_jog_hold_compare")


def compare_jog_hold(allow, stop, start, previous_hold):
    if any(type(v) is not bool for v in (allow, stop, start, previous_hold)):
        raise ValueError("模型输入和上一保持状态必须为布尔量")
    jog = allow and not stop and start
    hold = hold_next(allow, stop, start, previous_hold)
    reason = ("停止成立或允许不成立，两条路径都被阻断。" if stop or not allow else
              "启动请求成立，两个模型本次都为真。" if start else
              "启动已撤回：点动为假，长动通过上一状态保持为真。" if previous_hold else
              "没有启动请求且上一保持为假，两个模型都为假。")
    return {"jog": jog, "next_hold": hold, "reason": reason}


def result_label(result):
    return f"点动{'真' if result['jog'] else '假'}、长动{'真' if result['next_hold'] else '假'}"


def _q(qid, stem, inputs, topic, wrong):
    result = compare_jog_hold(*inputs)
    answer = result_label(result)
    alternatives = [value for value in ("点动假、长动假", "点动假、长动真", "点动真、长动真") if value != answer]
    return dict(id=qid, chapter_id="p3_unit_3", stem=stem, options=(answer, *alternatives), answer=answer,
                explanation=result['reason'], knowledge_point=("点动的当前条件", "长动的保持条件", "停止优先与逻辑比较")[TOPICS.index(topic)],
                card=topic, wrong=dict(zip(alternatives, wrong)))


QUESTION_SPECS = (
    _q("jog_hold_example", "本单元两个独立模型：P真、T假、S假，上一保持H真。本次结果是什么？", (True, False, False, True), TOPICS[2],
       ("长动明确引用上一保持；没有停止或失去允许，不能把它也清除。", "点动需要当前启动S真，不能借用长动的历史。")),
    _q("jog_hold_initial", "初始H假，P真、T假、S假，第一次计算结果是什么？", (True, False, False, False), TOPICS[0],
       ("初始保持为假且没有启动，长动不能自行变真。", "当前没有启动请求，两个模型都不应启动。")),
    _q("jog_hold_start", "初始H假，P真、T假、S真，计算后是什么？", (True, False, True, False), TOPICS[0],
       ("公共条件通过且启动成立，两个模型都应为真。", "点动也有当前启动请求，不能只让长动为真。")),
    _q("jog_hold_stop", "H真，P真、T真、S真，停止与启动同时成立，结果是什么？", (True, True, True, True), TOPICS[2],
       ("停止也阻断保持路径，长动不能继续为真。", "启动不能绕过停止条件，两者都应为假。")),
    _q("jog_hold_permission", "H真，P假、T假、S真，允许失效后计算结果是什么？", (False, False, True, True), TOPICS[2],
       ("长动保持仍需要允许P，不能绕过公共前提。", "启动请求不能代替允许条件，两个结果都应为假。")),
    _q("jog_hold_release", "刚完成启动得到H真，下一次P真、T假、S假，结果是什么？", (True, False, False, True), TOPICS[1],
       ("撤回启动不等于停止，本例长动仍有上一状态保持。", "点动不引用历史，S假后点动为假。")),
    _q("jog_hold_after_stop", "上次停止计算已把H变假。现在P真、T假、S假，结果是什么？", (True, False, False, False), TOPICS[1],
       ("保持已被停止清除，仅撤回停止不会产生启动请求。", "两个模型都缺少启动，且长动历史为假。")),
    _q("jog_hold_history", "与初始状态相比，现在上一保持H为真；当前P真、T假、S假，哪些结果成立？", (True, False, False, True), TOPICS[1],
       ("忽略了长动公式中的上一保持状态。", "点动公式没有H，不能因为历史为真就让点动为真。")),
)
OPTION_FEEDBACK = {q['id']: q['wrong'] for q in QUESTION_SPECS}
