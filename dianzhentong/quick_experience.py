"""五分钟首次体验：不写入正式成绩的纯规则学习流程。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

EXPERIENCE_ITEMS: tuple[dict[str, Any], ...] = (
    {"id":"quick_diagram","phase":"识图体验","title":"找到路径起点",
     "context":"抽象路径：公共保护条件 → 启动请求 → 执行元件",
     "prompt":"按下启动按钮后没有形成动作条件，第一步应先看哪里？",
     "options":("公共保护条件","直接判断执行元件损坏","无关方向分支"),"answer":"公共保护条件",
     "explanation":"先确认共享的上游条件，再进入局部分支。"},
    {"id":"quick_power","phase":"模拟排查","title":"检查1：控制电源",
     "context":"模拟状态卡：控制回路电源条件可用。预期：电源条件可用。",
     "prompt":"根据模拟资料，本步应判断为？","options":("正常","异常","不确定"),"answer":"正常",
     "explanation":"模拟状态与预期一致，所以判断为正常。"},
    {"id":"quick_protection","phase":"模拟排查","title":"检查2：保护条件",
     "context":"模拟状态卡：保护触点处于题设要求的闭合状态。预期：保护条件满足。",
     "prompt":"根据模拟资料，本步应判断为？","options":("正常","异常","不确定"),"answer":"正常",
     "explanation":"保护条件满足，可以继续沿路径向下检查。"},
    {"id":"quick_request","phase":"模拟排查","title":"检查3：启动请求",
     "context":"模拟状态卡：按钮动作后，启动请求仍未形成。预期：按钮动作后请求应形成。",
     "prompt":"根据模拟资料，本步应判断为？","options":("正常","异常","不确定"),"answer":"异常",
     "explanation":"模拟状态与预期不一致，中断点位于启动请求。"},
    {"id":"quick_evidence","phase":"迷你测验","title":"证据不足时怎么办",
     "context":"题目没有给出足够的模拟状态。",
     "prompt":"最合适的处理是？","options":("选择不确定并复核资料","强行判断正常","进行真实带电测量"),"answer":"选择不确定并复核资料",
     "explanation":"证据不足时应保留不确定，不能猜测或扩大到真实操作。"},
    {"id":"quick_scope","phase":"迷你测验","title":"判断故障范围",
     "context":"正转和反转两个方向都不能形成模拟启动条件。",
     "prompt":"应优先检查哪一类条件？","options":("两个方向共享的公共条件","只检查正转按钮","只检查反转线圈"),"answer":"两个方向共享的公共条件",
     "explanation":"共同异常优先指向共享的公共路径。"},
)

@dataclass
class QuickExperienceSession:
    card_read: bool = False
    index: int = 0
    first_answers: dict[str, str] = field(default_factory=dict)
    wrong_items: list[str] = field(default_factory=list)
    item_solved: bool = False

    @property
    def is_complete(self) -> bool: return self.card_read and self.index >= len(EXPERIENCE_ITEMS)
    @property
    def current_item(self) -> dict[str, Any] | None:
        return None if not self.card_read or self.is_complete else EXPERIENCE_ITEMS[self.index]
    @property
    def correct_count(self) -> int: return len(EXPERIENCE_ITEMS) - len(self.wrong_items)
    def mark_card_read(self) -> None: self.card_read = True
    def answer(self, selected: str) -> bool:
        item=self.current_item
        if item is None: raise ValueError("当前没有可回答的体验题")
        if selected not in item["options"]: raise ValueError("答案不属于当前选项")
        if item["id"] not in self.first_answers:
            self.first_answers[item["id"]]=selected
            if selected != item["answer"]: self.wrong_items.append(item["id"])
        self.item_solved=selected == item["answer"]
        return self.item_solved
    def next_item(self) -> None:
        if not self.item_solved: raise ValueError("请先完成当前体验题")
        self.index += 1; self.item_solved=False
    def to_dict(self) -> dict[str, Any]:
        return {"card_read":self.card_read,"index":self.index,"first_answers":dict(self.first_answers),
                "wrong_items":list(self.wrong_items),"item_solved":self.item_solved}
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuickExperienceSession":
        session=cls(bool(data.get("card_read",False)),int(data.get("index",0)),
                    dict(data.get("first_answers",{})),list(data.get("wrong_items",[])),
                    bool(data.get("item_solved",False)))
        if session.index < 0 or session.index > len(EXPERIENCE_ITEMS): raise ValueError("体验进度无效")
        return session

def experience_report(session: QuickExperienceSession) -> str:
    if not session.is_complete: raise ValueError("体验尚未完成")
    lines=["电诊通｜5分钟体验总结","="*24,
           f"首次判断：{session.correct_count}/{len(EXPERIENCE_ITEMS)}",
           "已体验：知识卡、抽象识图、模拟排查、迷你测验。"]
    if session.wrong_items:
        lines.append("建议复习：")
        for item_id in session.wrong_items:
            item=next(value for value in EXPERIENCE_ITEMS if value["id"]==item_id)
            lines.append(f"- {item['phase']}：{item['explanation']}")
    else: lines.append("全部项目首次判断正确。")
    lines.extend(["","仅限教学模拟，不是职业资格、实训考核或真实设备诊断结论。"])
    return "\n".join(lines)
