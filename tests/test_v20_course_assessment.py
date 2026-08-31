from __future__ import annotations
import random
from dianzhentong.assessment import (
    competency_report, course_exam_eligible, course_learning_status,
    questions_for_course, review_route, select_course_questions,
)
from dianzhentong.backup import create_archive, import_archive, parse_archive
from dianzhentong.course import COURSES, COURSE_CHAPTERS
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository

def answer(question, selected=None):
    value=selected or question.answer
    return QuizAnswer(question.id,value,question.answer,value==question.answer,value=="不确定")

def unlock_exam(repository, course_id):
    for chapter in COURSE_CHAPTERS[course_id]:
        question=questions_for_chapter(chapter["id"])[0]
        repository.save_quiz(make_quiz_record(chapter["id"],[answer(question)],quiz_id=f"unlock-{chapter['id']}"))

def test_each_course_has_at_least_fifteen_questions_and_balanced_exam():
    for course in COURSES:
        assert len(questions_for_course(course["id"])) >= 15
        selected=select_course_questions(course["id"],10,random.Random(7))
        assert len(selected)==10 and len({item.id for item in selected})==10
        assert {item.chapter_id for item in selected} == {item["id"] for item in COURSE_CHAPTERS[course["id"]]}

def test_exam_unlock_status_and_seventy_percent_threshold():
    repository=MemoryPracticeRepository(); course_id=COURSES[1]["id"]
    assert not course_exam_eligible(repository,course_id)
    assert course_learning_status(repository,course_id)=="未学习"
    unlock_exam(repository,course_id)
    assert course_exam_eligible(repository,course_id)
    assert course_learning_status(repository,course_id)=="待考试"
    questions=select_course_questions(course_id,10,random.Random(1))
    answers=[answer(item) for item in questions[:7]]+[answer(item,"不确定") for item in questions[7:]]
    record=make_quiz_record(course_id,answers,mode="course_exam",quiz_id="course-pass")
    assert record.passed is True
    repository.save_quiz(record)
    assert course_learning_status(repository,course_id)=="已完成"

def test_competencies_and_review_route_are_explainable():
    course_id=COURSES[0]["id"]
    questions=select_course_questions(course_id,10,random.Random(3))
    answers=[answer(questions[0],"不确定"),*[answer(item) for item in questions[1:]]]
    report=competency_report(answers); route=review_route(answers)
    assert sum(item["total"] for item in report)==10
    assert route and route[0]["chapter_id"]==questions[0].chapter_id
    assert route[0]["card_id"]

def test_course_exam_survives_backup_roundtrip():
    source=MemoryPracticeRepository(); course_id=COURSES[2]["id"]
    questions=select_course_questions(course_id,10,random.Random(5))
    source.save_quiz(make_quiz_record(course_id,[answer(item) for item in questions],mode="course_exam",quiz_id="backup-exam"))
    archive=parse_archive(__import__('json').dumps(create_archive(source)))
    target=MemoryPracticeRepository(); result=import_archive(target,archive,True)
    assert result["quiz_sessions"]==1
    assert target.quiz_summary(course_id)["passed_count"]==1

def test_app_exposes_course_assessment_without_pyarrow():
    source=open("app.py",encoding="utf-8").read()
    for phrase in ("课程综合评测","能力掌握情况","推荐复习路线","下载课程学习总结"):
        assert phrase in source
    assert "st.dataframe" not in source and "st.table" not in source
