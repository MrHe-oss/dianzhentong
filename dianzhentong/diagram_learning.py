"""安全的抽象控制逻辑示意与课堂练习，不表示真实接线。"""

from __future__ import annotations


DIAGRAM_LESSONS = {
    "diagram_symbols_roles": {
        "title": "从角色读取一条控制链",
        "flows": (("保护条件", "操作信号", "执行元件"),),
        "prompt": "在这条抽象链中，哪个角色通常位于逻辑末端？",
        "options": ("执行元件", "保护条件", "操作信号"),
        "answer": "执行元件",
        "explanation": "先满足保护和操作条件，逻辑才到达执行元件。",
    },
    "series_parallel_logic": {
        "title": "串联与并联的逻辑差异",
        "flows": (
            ("公共条件", "条件A", "条件B", "执行元件"),
            ("公共条件", "分支A 或 分支B", "执行元件"),
        ),
        "prompt": "若公共条件异常，两条可选分支会怎样？",
        "options": ("都不能形成完整路径", "只有分支A受影响", "都自动恢复"),
        "answer": "都不能形成完整路径",
        "explanation": "公共条件位于分支之前，因此会同时影响后续可选路径。",
    },
    "control_path_tracing": {
        "title": "按现象追踪相关路径",
        "flows": (("公共条件", "现象对应分支", "局部条件", "执行元件"),),
        "prompt": "只有一个方向异常、公共条件正常时，下一步应查看哪里？",
        "options": ("现象对应的方向分支", "无关方向分支", "直接判断执行元件损坏"),
        "answer": "现象对应的方向分支",
        "explanation": "公共条件已经排除，应沿现象对应分支继续建立证据链。",
    },
}


def diagram_lesson_for_chapter(chapter_id: str) -> dict[str, object] | None:
    return DIAGRAM_LESSONS.get(chapter_id)


def validate_diagram_lessons() -> None:
    for lesson in DIAGRAM_LESSONS.values():
        if lesson["answer"] not in lesson["options"]:
            raise ValueError("逻辑识读练习答案不在选项中")
        if not lesson["flows"]:
            raise ValueError("逻辑识读练习缺少抽象路径")


validate_diagram_lessons()
