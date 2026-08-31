import random
from datetime import datetime
from zoneinfo import ZoneInfo

from dianzhentong.assessment import questions_for_course, select_course_questions
from dianzhentong.course import (
    FOURTH_COURSE, FOURTH_COURSE_CHAPTERS, THIRD_COURSE,
    chapter_progress, course_is_unlocked,
)
from dianzhentong.diagram_learning import DIAGRAM_CASES, DiagramTrainingSession, cases_for_chapter
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository, make_diagram_record, make_learning_activity


STAR_CARDS = {
    "star_delta_principle", "star_delta_components",
    "star_delta_timing", "star_delta_interlock",
}


def _correct_answers(questions):
    return [QuizAnswer(item.id, item.answer, item.answer, True, False) for item in questions]


def test_fourth_course_content_counts_and_paths_are_complete():
    assert len(FOURTH_COURSE_CHAPTERS) == 3
    assert STAR_CARDS <= set(KNOWLEDGE_CARDS)
    assert [len(questions_for_chapter(item["id"])) for item in FOURTH_COURSE_CHAPTERS] == [5, 5, 5]
    star_cases = [case for case in DIAGRAM_CASES.values() if case["chapter_id"].startswith("star_delta_")]
    assert len(star_cases) == 6
    assert [len(cases_for_chapter(item["id"])) for item in FOURTH_COURSE_CHAPTERS] == [2, 2, 2]
    for case_id, case in DIAGRAM_CASES.items():
        if not case["chapter_id"].startswith("star_delta_"):
            continue
        session = DiagramTrainingSession(case_id)
        while not session.is_complete:
            assert session.answer(session.current_step["answer"])
            session.next_step()
        assert session.correct_steps == len(case["steps"])


def test_fourth_course_unlock_requires_completed_third_course_exam():
    repository = MemoryPracticeRepository()
    assert not course_is_unlocked(repository, FOURTH_COURSE["id"])
    third_questions = select_course_questions(THIRD_COURSE["id"], 10, random.Random(5))
    repository.save_quiz(make_quiz_record(
        THIRD_COURSE["id"], _correct_answers(third_questions),
        mode="course_exam", quiz_id="third-course-pass",
    ))
    assert course_is_unlocked(repository, FOURTH_COURSE["id"])


def test_star_delta_assessment_has_ten_sourced_questions():
    available = questions_for_course(FOURTH_COURSE["id"])
    selected = select_course_questions(FOURTH_COURSE["id"], 10, random.Random(9))
    assert len(available) == 15
    assert len(selected) == 10
    assert {item.chapter_id for item in selected} <= {item["id"] for item in FOURTH_COURSE_CHAPTERS}


def test_star_delta_chapter_uses_40_30_30_completion_weights():
    repository = MemoryPracticeRepository()
    chapter = FOURTH_COURSE_CHAPTERS[0]
    moment = datetime(2026, 8, 31, 8, tzinfo=ZoneInfo("Asia/Shanghai"))
    repository.save_activity(make_learning_activity(
        "motor_dol_no_start", "knowledge_card", "star_delta_principle", moment,
    ))
    assert chapter_progress(repository, chapter).completion == 0.4
    case = cases_for_chapter(chapter["id"])[0]
    session = DiagramTrainingSession(case["id"], training_id="star-diagram")
    while not session.is_complete:
        session.answer(session.current_step["answer"]); session.next_step()
    repository.save_diagram_practice(make_diagram_record(session, moment))
    assert chapter_progress(repository, chapter).completion == 0.7
    questions = questions_for_chapter(chapter["id"])
    repository.save_quiz(make_quiz_record(chapter["id"], _correct_answers(questions), quiz_id="star-quiz"))
    state = chapter_progress(repository, chapter)
    assert state.completion == 1.0 and state.status == "已完成"


def test_star_delta_content_stays_abstract_and_safe():
    payload = str([
        FOURTH_COURSE, FOURTH_COURSE_CHAPTERS,
        {key: KNOWLEDGE_CARDS[key] for key in STAR_CARDS},
        [case for case in DIAGRAM_CASES.values() if case["chapter_id"].startswith("star_delta_")],
    ])
    for forbidden in ("端子号", "六端子", "电压值", "导线位置", "带电测量"):
        assert forbidden not in payload
