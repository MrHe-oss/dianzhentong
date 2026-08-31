"""课程综合评测、能力维度与复习路线。"""
from __future__ import annotations
import random
from typing import Any, Sequence
from .course import COURSES, COURSE_CHAPTERS, chapter_progress
from .quiz import QUESTIONS, QuizAnswer, QuizQuestion, card_id_for_question
from .provenance import is_card_assessable

COMPETENCY_NAMES = {
    "safety": "安全与证据意识", "components": "元件认识",
    "control_logic": "控制逻辑", "fault_reasoning": "故障排查",
    "diagram_reading": "识图与路径追踪",
}
CHAPTER_COMPETENCY = {
    "safety_and_circuits":"safety", "components":"components",
    "direct_start":"fault_reasoning", "forward_reverse":"fault_reasoning",
    "jog_continuous_basics":"control_logic", "jog_continuous_training":"fault_reasoning",
    "diagram_symbols_roles":"diagram_reading", "series_parallel_logic":"control_logic",
    "control_path_tracing":"diagram_reading",
    "star_delta_principles":"control_logic", "star_delta_components":"components",
    "star_delta_sequence":"diagram_reading",
    "timer_functions":"components", "on_off_delay":"control_logic",
    "sequence_control":"diagram_reading",
}

def course_by_id(course_id: str) -> dict[str, Any]:
    return next(course for course in COURSES if course["id"] == course_id)

def questions_for_course(course_id: str) -> tuple[QuizQuestion, ...]:
    chapter_ids = {item["id"] for item in COURSE_CHAPTERS[course_id]}
    return tuple(item for item in QUESTIONS if item.chapter_id in chapter_ids and is_card_assessable(card_id_for_question(item.id)))

def select_course_questions(course_id: str, count: int = 10,
                            rng: random.Random | None = None) -> tuple[QuizQuestion, ...]:
    generator = rng or random.Random()
    chapters = COURSE_CHAPTERS[course_id]
    selected: list[QuizQuestion] = []
    buckets = {item["id"]: list(question for question in questions_for_course(course_id) if question.chapter_id == item["id"]) for item in chapters}
    for values in buckets.values(): generator.shuffle(values)
    while len(selected) < count and any(buckets.values()):
        for chapter in chapters:
            bucket = buckets[chapter["id"]]
            if bucket and len(selected) < count: selected.append(bucket.pop())
    return tuple(selected)

def course_exam_eligible(repository: Any, course_id: str) -> bool:
    return all(repository.quiz_summary(chapter["id"])["passed_count"] for chapter in COURSE_CHAPTERS[course_id])

def course_learning_status(repository: Any, course_id: str) -> str:
    exam = repository.quiz_summary(course_id)
    if exam["passed_count"]: return "已完成"
    if course_exam_eligible(repository, course_id): return "待考试"
    if any(chapter_progress(repository, item).completion > 0 for item in COURSE_CHAPTERS[course_id]): return "学习中"
    return "未学习"

def competency_report(answers: Sequence[QuizAnswer]) -> tuple[dict[str, Any], ...]:
    totals: dict[str, list[int]] = {}
    for answer in answers:
        question = next(item for item in QUESTIONS if item.id == answer.question_id)
        key = CHAPTER_COMPETENCY[question.chapter_id]
        totals.setdefault(key, [0, 0]); totals[key][1] += 1; totals[key][0] += int(answer.is_correct)
    return tuple({"id":key, "name":COMPETENCY_NAMES[key], "correct":value[0], "total":value[1],
                  "accuracy":value[0]/value[1]} for key,value in totals.items())

def review_route(answers: Sequence[QuizAnswer]) -> tuple[dict[str, str], ...]:
    result=[]; seen=set()
    for answer in answers:
        if answer.is_correct: continue
        question=next(item for item in QUESTIONS if item.id == answer.question_id)
        if question.chapter_id in seen: continue
        seen.add(question.chapter_id)
        result.append({"chapter_id":question.chapter_id, "card_id":card_id_for_question(question.id),
                       "reason":f"复习“{question.knowledge_point}”后再测"})
    return tuple(result)
