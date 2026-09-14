"""教材项目综合复习；省略项目参数时兼容项目2。"""
from collections import Counter
import random

from .curriculum_catalog import BOOK_EDITION_MAPPINGS
from .quiz import QUESTION_MAP, textbook_question_pool

BOOK_ID = "electrical_control_plc_s71200_tong"
MODE = "textbook_project_assessment"
SCOPE = f"textbook:{BOOK_ID}:project_2"
UNITS = tuple((index, unit) for index, unit in enumerate(BOOK_EDITION_MAPPINGS[BOOK_ID]["chapters"])
              if unit["project_id"] == "project_2")
CHAPTER_IDS = frozenset(chapter for _, unit in UNITS for chapter in unit["quiz_chapter_ids"])

PROJECT_IDS = ("project_2", "project_3")
SCOPES = {f"textbook:{BOOK_ID}:{pid}": pid for pid in PROJECT_IDS}


def project_config(project_id="project_2"):
    if project_id not in PROJECT_IDS:
        raise ValueError("未知教材项目")
    units = tuple((i, u) for i, u in enumerate(BOOK_EDITION_MAPPINGS[BOOK_ID]["chapters"])
                  if u["project_id"] == project_id)
    return {"scope": f"textbook:{BOOK_ID}:{project_id}", "title": f"项目{project_id[-1]}",
            "units": units, "chapters": frozenset(c for _, u in units for c in u["quiz_chapter_ids"])}


def unit_pool(unit):
    return textbook_question_pool(unit["quiz_chapter_ids"], unit["worked_example"].get("practice_question_id"))


def select_project_questions(rng=None, project_id="project_2"):
    rng = rng or random.SystemRandom()
    return tuple(question for _, unit in project_config(project_id)["units"] for question in rng.sample(unit_pool(unit), 2))


def valid_project_questions(ids, project_id="project_2"):
    if project_id not in PROJECT_IDS:
        return False
    units = project_config(project_id)["units"]
    if not isinstance(ids, (list, tuple)) or any(not isinstance(qid, str) for qid in ids):
        return False
    if len(ids) != 8 or len(set(ids)) != 8:
        return False
    allowed = {q.id for _, unit in units for q in unit_pool(unit)}
    if not set(ids) <= allowed:
        return False
    counts = Counter(QUESTION_MAP[qid].chapter_id for qid in ids)
    return all(sum(counts[c] for c in unit["quiz_chapter_ids"]) == 2 for _, unit in units)


def unit_results(answers, project_id="project_2"):
    rows = []
    for index, unit in project_config(project_id)["units"]:
        relevant = [a for a in answers if QUESTION_MAP[a["question_id"]].chapter_id in unit["quiz_chapter_ids"]]
        rows.append({"index": index, "title": unit["title"], "total": len(relevant),
                     "correct": sum(bool(a["is_correct"]) for a in relevant)})
    return rows


def recommended_unit(states, answers=(), project_id="project_2"):
    """最近综合测验有错题时先回学；否则继续第一个未完成单元。"""
    weak = [row for row in unit_results(answers, project_id) if row["total"] and row["correct"] < row["total"]]
    if weak:
        return min(weak, key=lambda row: (row["correct"] / row["total"], row["index"]))["index"]
    units = project_config(project_id)["units"]
    return next((index for index, _ in units if states[index].completion < 1),
                units[0][0] if project_id == "project_2" else None)


def report_text(answers, project_id="project_2"):
    lines = [project_config(project_id)["title"] + "综合学习报告", f"本次得分：{sum(a['is_correct'] for a in answers)} / 8；通过要求：至少6题正确。",
             "每单元仅抽取2题，只反映本次作答，不代表整个单元掌握程度，也不改变单元成绩。"]
    for row in unit_results(answers, project_id):
        lines.append(f"{row['title']}：{row['correct']} / {row['total']}")
    from .quiz import answer_feedback, card_id_for_question
    from .learning import KNOWLEDGE_CARDS
    for answer in answers:
        question = QUESTION_MAP[answer["question_id"]]
        lines.extend([question.stem, f"首次答案：{answer['selected_answer']}；正确答案：{question.answer}",
                      question.explanation, answer_feedback(question, answer["selected_answer"])])
        lines.append("回学知识点：" + KNOWLEDGE_CARDS[card_id_for_question(question.id)]["title"])
    lines.append("仅限教学模拟，不用于真实设备操作或能力认证。")
    return "\n\n".join(lines)
