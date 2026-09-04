"""Explanations and evidence-based tasks; no independent scoring rules."""
from dataclasses import dataclass


def truth(value):
    return "尚未执行" if value is None else ("成立（真）" if value else "不成立（假）")


TASKS = {
    "logic": (("compare", "保持A、B相同且一真一假，分别执行AND和OR，比较结果。"),
              ("invert", "选择NOT，分别观察A为真和为假时的结果；B不参与。")),
    "scan": (("snapshot", "先读取假，再把当前输入改为真，执行并更新，观察本轮仍为假。"),
             ("next_cycle", "接着保持输入为真，再完成一轮读取、执行和更新，观察结果变真。")),
    "hold": (("keep", "许可成立时启动一步，再撤回启动请求，观察保持运行。"),
             ("stop_priority", "许可成立时同时选择启动和停止，观察停止优先。")),
}


@dataclass(frozen=True)
class Observation:
    number: int
    action: str
    inputs: tuple
    before: str
    after: str
    explanation: str
    nodes: tuple
    changes: str = "首次设置"

    def text(self):
        return f"第{self.number}步 · {self.action}\n操作前：{self.before}\n改变：{self.changes}\n条件：{format_inputs(self.inputs)}\n操作后：{self.after}\n原因：{self.explanation}"


def format_inputs(values):
    labels = {"operator": "运算", "a": "输入A", "b": "输入B", "live": "当前输入",
              "phase": "执行阶段", "allow": "许可", "stop": "停止请求", "start": "启动请求", "previous": "先前运行"}
    return "；".join(f"{labels[key]}={truth(value) if isinstance(value, bool) else ('读取', '执行', '更新')[value] if key == 'phase' else value}"
                    for key, value in values)


def task_evidence(lab_id, history):
    """Evaluate executed observations only, never checkbox changes or self-report."""
    done = set()
    if lab_id == "logic":
        seen = {}
        for event in history:
            values = dict(event.inputs)
            seen[(values["operator"], values["a"], values["b"])] = True
        for a, b in ((True, False), (False, True)):
            if ("AND", a, b) in seen and ("OR", a, b) in seen:
                done.add("compare")
        if all(any(op == "NOT" and a == target for op, a, b in seen) for target in (True, False)):
            done.add("invert")
    elif lab_id == "hold":
        for event in history:
            v = dict(event.inputs)
            if v["allow"] and not v["stop"] and not v["start"] and v["previous"]:
                done.add("keep")
            if v["allow"] and v["stop"] and v["start"]:
                done.add("stop_priority")
    else:
        # Six consecutive executed phases demonstrate both cycles without
        # confusing a change after execution with a change before sampling.
        for index in range(len(history) - 2):
            trio = history[index:index + 3]
            vals = [dict(e.inputs) for e in trio]
            if ([v["phase"] for v in vals] == [0, 1, 2]
                    and [v["live"] for v in vals] == [False, True, True]):
                done.add("snapshot")
                following = history[index + 3:index + 6]
                if (len(following) == 3 and [dict(e.inputs)["phase"] for e in following] == [0, 1, 2]
                        and all(dict(e.inputs)["live"] for e in following)):
                    done.add("next_cycle")
    return done
