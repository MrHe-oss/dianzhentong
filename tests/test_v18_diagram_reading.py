from __future__ import annotations

from dianzhentong.course import (
    COURSES, SECOND_COURSE_CHAPTERS, THIRD_COURSE, THIRD_COURSE_CHAPTERS,
    course_is_unlocked,
)
from dianzhentong.diagram_learning import DIAGRAM_CASES, cases_for_chapter, diagram_lesson_for_chapter
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository


def test_third_course_has_three_chapters_and_safe_diagram_lessons():
    assert THIRD_COURSE in COURSES
    assert len(THIRD_COURSE_CHAPTERS) == 3
    assert len(DIAGRAM_CASES) == 18
    text = str(DIAGRAM_CASES)
    for forbidden in ("220V", "380V", "端子号", "短接验证", "带电测量"):
        assert forbidden not in text
    for chapter in THIRD_COURSE_CHAPTERS:
        lesson = diagram_lesson_for_chapter(chapter["id"])
        assert lesson and len(cases_for_chapter(chapter["id"])) == 2


def test_each_diagram_chapter_has_five_questions():
    assert [len(questions_for_chapter(item["id"])) for item in THIRD_COURSE_CHAPTERS] == [5, 5, 5]


def test_third_course_unlocks_after_second_course_quiz_pass():
    repository = MemoryPracticeRepository()
    assert not course_is_unlocked(repository, THIRD_COURSE["id"])
    chapter = SECOND_COURSE_CHAPTERS[0]
    question = questions_for_chapter(chapter["id"])[0]
    answer = QuizAnswer(question.id, question.answer, question.answer, True, False)
    repository.save_quiz(make_quiz_record(chapter["id"], [answer], quiz_id="unlock-v18"))
    assert course_is_unlocked(repository, THIRD_COURSE["id"])


def test_app_renders_diagram_exercises_without_pyarrow():
    source = open("app.py", encoding="utf-8").read()
    assert "抽象逻辑识读" in source
    assert "diagram_lesson_for_chapter" in source
    assert "st.dataframe" not in source and "st.table" not in source
