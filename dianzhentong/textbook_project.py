"""项目2综合复习：复用教材映射及独立题池，不改变单元掌握规则。"""
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


def unit_pool(unit):
    return textbook_question_pool(unit["quiz_chapter_ids"], unit["worked_example"].get("practice_question_id"))


def select_project_questions(rng=None):
    rng = rng or random.SystemRandom()
    return tuple(question for _, unit in UNITS for question in rng.sample(unit_pool(unit), 2))


def valid_project_questions(ids):
    if not isinstance(ids, (list, tuple)) or any(not isinstance(qid, str) for qid in ids):
        return False
    if len(ids) != 8 or len(set(ids)) != 8:
        return False
    allowed = {q.id for _, unit in UNITS for q in unit_pool(unit)}
    if not set(ids) <= allowed:
        return False
    counts = Counter(QUESTION_MAP[qid].chapter_id for qid in ids)
    return all(sum(counts[c] for c in unit["quiz_chapter_ids"]) == 2 for _, unit in UNITS)


def unit_results(answers):
    rows = []
    for index, unit in UNITS:
        relevant = [a for a in answers if QUESTION_MAP[a["question_id"]].chapter_id in unit["quiz_chapter_ids"]]
        rows.append({"index": index, "title": unit["title"], "total": len(relevant),
                     "correct": sum(bool(a["is_correct"]) for a in relevant)})
    return rows


def recommended_unit(states, answers=()):
    """最近综合测验有错题时先回学；否则继续第一个未完成单元。"""
    weak = [row for row in unit_results(answers) if row["total"] and row["correct"] < row["total"]]
    if weak:
        return min(weak, key=lambda row: (row["correct"] / row["total"], row["index"]))["index"]
    return next((index for index, _ in UNITS if states[index].completion < 1), UNITS[0][0])


def report_text(answers):
    lines = ["项目2综合学习报告", f"本次得分：{sum(a['is_correct'] for a in answers)} / 8；通过要求：至少6题正确。",
             "每单元仅抽取2题，只反映本次作答，不代表整个单元掌握程度，也不改变单元成绩。"]
    for row in unit_results(answers):
        lines.append(f"{row['title']}：{row['correct']} / {row['total']}")
    from .quiz import answer_feedback
    for answer in answers:
        question = QUESTION_MAP[answer["question_id"]]
        lines.extend([question.stem, f"首次答案：{answer['selected_answer']}；正确答案：{question.answer}",
                      question.explanation, answer_feedback(question, answer["selected_answer"])])
    lines.append("仅限教学模拟，不用于真实设备操作或能力认证。")
    return "\n\n".join(lines)
