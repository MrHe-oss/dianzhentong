"""位逻辑单元原创题库与无记忆模型；不控制真实设备。"""
from .plc_lab import logic_output

TOPICS = ("bit_contacts", "bit_combinations", "bit_assignment")


def evaluate_request(a, b, stop):
    request = logic_output("OR", a, b)
    permitted = logic_output("NOT", stop)
    return {"request": request, "permitted": permitted, "result": logic_output("AND", request, permitted)}


def _question(qid, stem, options, explanation, topic, wrong):
    titles = {"bit_contacts": "布尔状态与逻辑触点", "bit_combinations": "与或非及组合条件", "bit_assignment": "普通输出赋值与条件判断"}
    return {"id": qid, "chapter_id": "p3_unit_1", "stem": stem, "options": options,
            "answer": options[0], "explanation": explanation, "knowledge_point": titles[topic],
            "card": topic, "wrong": wrong}


QUESTION_SPECS = (
    _question("bit_example", "本例A真、B假、T真，Y=(A∨B)∧¬T应为什么？",
              ("假，停止条件阻止请求", "真，有A即可", "沿用上次Y"),
              "A∨B为真，但¬T为假，最终相与为假。本例无记忆。", "bit_combinations",
              ("有请求还不够，必须同时满足T为假。", "公式没有上一状态参与，不能自行添加保持。")),
    _question("bit_true_check", "模拟变量A为假，常开逻辑触点对A进行检查，本条件是否成立？",
              ("不成立，因为检查目标为A真", "成立，因为按钮可能没按", "由上次A决定"),
              "先确认检查目标，再读给定值；A是假，不满足检查真的条件。", "bit_contacts",
              ("真实按钮状态未给出，不能替代已知布尔值。", "题设给出了当前值，不需要上一次A。")),
    _question("bit_false_check", "变量B为真，常闭逻辑触点检查B为假，结果是什么？",
              ("条件不成立", "常闭二字说明始终成立", "B真就必定成立"),
              "本条件检查的是假；已知B真，所以该条件为假。", "bit_contacts",
              ("常闭是逻辑检查类型，不表示永远成立。", "这把检查假误读成了检查真。")),
    _question("bit_physical_boundary", "仅知道程序对变量C使用常闭逻辑触点，能够断定什么？",
              ("该条件检查C为假，不能据此断定真实按钮状态", "真实按钮一定按下", "真实按钮一定没按"),
              "程序条件针对变量；没有给出物理映射，不能推出真实按钮的机械状态。", "bit_contacts",
              ("缺少变量与物理按钮的映射，不能推出按下。", "缺少物理映射，也不能推出未按下。")),
    _question("bit_any_request", "需求写‘A或B至少一个成立’，A和B同时为真是否满足？",
              ("满足", "不满足，只能一个真", "必须查看上一输出"),
              "至少一个包括两个都真；这是或逻辑，不包含历史状态。", "bit_combinations",
              ("题目没有要求只能一个成立，两者都真也满足。", "当前真假已足以判断，与上一输出无关。")),
    _question("bit_bracket", "规定停止条件T必须约束所有请求，哪个表达式符合要求？",
              ("(A∨B)∧¬T", "A∨(B∧¬T)", "(A∨B)∨¬T"),
              "先合并请求，再与非T合并，停止条件才能约束A、B两者。", "bit_combinations",
              ("A真时此式直接为真，绕过了停止条件。", "最后用或会让请求绕过停止，也可能在没有请求时成立。")),
    _question("bit_recalculate", "本例Y只有一处普通赋值且每次都执行。上次Y真，本次右侧条件假，执行后Y是什么？",
              ("假", "保持真", "无法计算，因为缺少自锁"),
              "普通赋值采用本次右侧结果。本例不需要也没有保持逻辑。", "bit_assignment",
              ("保持真需要额外的状态关系，本题没有。", "没有自锁仍可计算，右侧为假就赋为假。")),
    _question("bit_execution_scope", "‘条件假则执行后Y假’这一学习结论，本单元明确采用什么前提？",
              ("赋值本次确实执行，且Y只有这一处写入", "无论是否执行都自动更新", "任何真实设备都相同"),
              "结论限定在执行普通赋值、单一写入的模型，不推断任意程序或真实系统。", "bit_assignment",
              ("未执行的语句不能被当成已经重新赋值。", "真实系统还涉及其他程序和时序，不能这样推广。")),
)
OPTION_FEEDBACK = {q["id"]: dict(zip(q["options"][1:], q["wrong"])) for q in QUESTION_SPECS}
