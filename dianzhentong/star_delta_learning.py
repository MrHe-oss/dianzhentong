"""星—三角课程的抽象阶段演示、识图反馈与课程总结。"""
from __future__ import annotations

from typing import Any

from .course import FOURTH_COURSE, FOURTH_COURSE_CHAPTERS, chapter_progress
from .diagram_learning import DIAGRAM_CASES
from .learning import KNOWLEDGE_CARDS
from .quiz import QUESTION_MAP, card_id_for_question


STAR_DELTA_STAGES: tuple[dict[str, object], ...] = (
    {
        "id": "stopped", "title": "停止",
        "description": "启动请求尚未形成，三个接触器角色均不应有效。",
        "roles": ("主接触器：未形成", "星形接触器：未形成", "三角接触器：未形成"),
        "next_condition": "收到教学情境中的启动请求",
    },
    {
        "id": "star_start", "title": "星形启动",
        "description": "公共主角色与星形角色有效，用较低启动电流和启动转矩完成启动阶段。",
        "roles": ("主接触器：有效", "星形接触器：有效", "三角接触器：被互锁阻止"),
        "next_condition": "题设中的时间转换条件到达",
    },
    {
        "id": "transition", "title": "转换等待",
        "description": "星形角色已经退出，三角角色尚未进入，避免两个阶段重叠。",
        "roles": ("主接触器：保持公共条件", "星形接触器：已退出", "三角接触器：等待允许"),
        "next_condition": "星形退出且互锁条件允许",
    },
    {
        "id": "delta_run", "title": "三角运行",
        "description": "公共主角色与三角角色有效，进入题设中的稳定运行阶段。",
        "roles": ("主接触器：有效", "星形接触器：被互锁阻止", "三角接触器：有效"),
        "next_condition": "停止请求或公共条件改变",
    },
)


def stage_by_id(stage_id: str) -> dict[str, object]:
    return next(item for item in STAR_DELTA_STAGES if item["id"] == stage_id)


def stage_for_diagram_step(case_id: str, step_index: int) -> dict[str, object] | None:
    """根据案例和步骤返回当前抽象阶段，不解析真实设备状态。"""
    case = DIAGRAM_CASES.get(case_id)
    if not case or not case["chapter_id"].startswith("star_delta_"):
        return None
    stage_ids = {
        "sd_purpose": ("stopped", "star_start", "delta_run"),
        "sd_suitability": ("stopped", "star_start", "delta_run"),
        "sd_roles": ("stopped", "star_start", "delta_run"),
        "sd_timer": ("star_start", "transition", "delta_run"),
        "sd_sequence": ("star_start", "transition", "delta_run"),
        "sd_interlock": ("stopped", "star_start", "transition"),
    }
    return stage_by_id(stage_ids[case_id][min(step_index, 2)])


def diagram_choice_feedback(case_id: str, step_index: int, selected: str) -> dict[str, str]:
    """生成星—三角识图反馈；正确答案仍来自案例库。"""
    case = DIAGRAM_CASES[case_id]
    step = case["steps"][step_index]
    correct = selected == step["answer"]
    stage = stage_for_diagram_step(case_id, step_index)
    card_id = case["card_ids"][min(step_index, len(case["card_ids"]) - 1)]
    return {
        "stage": str(stage["title"]) if stage else "当前逻辑步骤",
        "role": str(step["answer"]),
        "reason": step["explanation"] if correct else f"“{selected}”与当前模拟现象或阶段顺序不一致。{step['explanation']}",
        "card_id": card_id,
        "card_title": KNOWLEDGE_CARDS[card_id]["title"],
        "is_correct": str(correct),
    }


def build_star_delta_course_summary(repository: Any) -> dict[str, object]:
    chapter_rows = []
    weak_card_ids: list[str] = []
    for chapter in FOURTH_COURSE_CHAPTERS:
        progress = chapter_progress(repository, chapter)
        wrong_questions = repository.wrong_question_ids(chapter["id"])
        for question_id in wrong_questions:
            card_id = card_id_for_question(question_id)
            if card_id not in weak_card_ids:
                weak_card_ids.append(card_id)
        chapter_rows.append({
            "chapter_id": chapter["id"], "title": chapter["title"],
            "completion": progress.completion, "status": progress.status,
            "quiz_passed": progress.quiz_passed,
        })
    diagram = repository.diagram_summary()
    star_case_ids = {case_id for case_id, case in DIAGRAM_CASES.items()
                     if case["chapter_id"].startswith("star_delta_")}
    star_history = [item for item in repository.diagram_history()
                    if item["case_id"] in star_case_ids]
    for item in star_history:
        case = DIAGRAM_CASES[item["case_id"]]
        if item["wrong_steps"]:
            for card_id in case["card_ids"]:
                if card_id not in weak_card_ids:
                    weak_card_ids.append(card_id)
    total_steps = sum(int(item["total_steps"]) for item in star_history)
    correct_steps = sum(int(item["correct_steps"]) for item in star_history)
    return {
        "course_id": FOURTH_COURSE["id"],
        "chapters": tuple(chapter_rows),
        "completed_chapters": sum(item["status"] == "已完成" for item in chapter_rows),
        "diagram_attempts": len(star_history),
        "diagram_accuracy": correct_steps / total_steps if total_steps else 0.0,
        "weak_cards": tuple({"id": card_id, "title": KNOWLEDGE_CARDS[card_id]["title"]}
                            for card_id in weak_card_ids),
        "principles": (
            "适用性同时考虑启动电流、启动转矩和题设负载条件。",
            "主接触器承担公共角色，星形与三角接触器分别服务不同阶段。",
            "标准顺序为星形启动、星形退出、三角运行。",
            "互锁约束用于排除星形与三角角色同时有效。",
        ),
        "all_diagram_attempts": int(diagram["attempts"]),
    }


def star_delta_summary_text(summary: dict[str, object]) -> str:
    lines = ["电诊通｜星—三角降压启动课程总结", "", "核心理解："]
    lines.extend(f"- {item}" for item in summary["principles"])
    lines.extend(("", "章节进度："))
    lines.extend(f"- {item['title']}：{item['status']}（{item['completion']:.0%}）" for item in summary["chapters"])
    lines.extend(("", f"互动识图：{summary['diagram_attempts']}次，首次判断正确率 {summary['diagram_accuracy']:.0%}"))
    if summary["weak_cards"]:
        lines.append("建议复习：" + "、".join(item["title"] for item in summary["weak_cards"]))
    else:
        lines.append("建议复习：当前没有已记录的薄弱知识点，可继续巩固阶段顺序。")
    lines.extend(("", "仅用于教学学习，不提供真实设备选型、接线、整定或操作指导。"))
    return "\n".join(lines)
