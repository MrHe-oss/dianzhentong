from __future__ import annotations

import random
import sqlite3

from dianzhentong.course import CHAPTERS, chapter_progress
from dianzhentong.quiz import (
    QUESTIONS, QuizAnswer, make_quiz_record, questions_for_chapter, select_questions,
)
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository


def answer(question, selected=None):
    value = selected or question.answer
    return QuizAnswer(question.id, value, question.answer, value == question.answer, value == "不确定")


def test_bank_has_safe_questions_with_expected_distribution():
    assert len(QUESTIONS) == 55
    assert [len(questions_for_chapter(item["id"])) for item in CHAPTERS] == [6, 10, 7, 7]
    assert len({item.id for item in QUESTIONS}) == 55
    text = " ".join(item.stem + item.explanation for item in QUESTIONS)
    assert "短接验证" not in text
    assert "进行带电测量" not in text


def test_each_quiz_selects_five_unique_questions_from_one_chapter():
    selected = select_questions("components", rng=random.Random(7))
    assert len(selected) == 5
    assert len({item.id for item in selected}) == 5
    assert {item.chapter_id for item in selected} == {"components"}


def test_wrong_questions_are_selected_first():
    selected = select_questions("components", wrong_ids=("q07", "q08"), rng=random.Random(1))
    assert {item.id for item in selected[:2]} == {"q07", "q08"}


def test_scoring_passes_at_three_of_five_and_tracks_uncertain():
    questions = questions_for_chapter("direct_start")[:5]
    answers = [answer(item) for item in questions[:3]] + [answer(item, "不确定") for item in questions[3:]]
    record = make_quiz_record("direct_start", answers, quiz_id="fixed")
    assert record.correct_count == 3
    assert record.passed is True
    assert sum(item.uncertain for item in record.answers) == 2


def test_sqlite_migration_and_duplicate_save_preserve_old_records(tmp_path):
    repository = PracticeRepository(tmp_path / "quiz.db")
    question = questions_for_chapter("safety_and_circuits")[0]
    record = make_quiz_record("safety_and_circuits", [answer(question)], quiz_id="same")
    assert repository.save_quiz(record) is True
    assert repository.save_quiz(record) is False
    with sqlite3.connect(repository.path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"practice_records", "learning_activities", "quiz_sessions", "quiz_answers"} <= tables


def test_quiz_stats_and_wrong_priority_work_in_sqlite(tmp_path):
    repository = PracticeRepository(tmp_path / "stats.db")
    questions = questions_for_chapter("components")[:5]
    answers = [answer(questions[0], "不确定"), *[answer(item) for item in questions[1:]]]
    repository.save_quiz(make_quiz_record("components", answers, quiz_id="one"))
    summary = repository.quiz_summary("components")
    assert summary["attempts"] == 1
    assert summary["question_accuracy"] == 0.8
    assert repository.wrong_question_ids("components") == [questions[0].id]


def test_memory_repository_supports_quizzes_and_clear():
    repository = MemoryPracticeRepository()
    question = questions_for_chapter("forward_reverse")[0]
    repository.save_quiz(make_quiz_record("forward_reverse", [answer(question)], quiz_id="memory"))
    assert repository.quiz_summary("forward_reverse")["passed_count"] == 1
    assert repository.clear(True) == 1
    assert repository.quiz_summary()["attempts"] == 0


def test_chapter_requires_quiz_after_prerequisites_and_completes_after_pass():
    repository = MemoryPracticeRepository()
    chapter = CHAPTERS[0]
    # 基础章节的卡片通过直接启动实验记录，兼容现有知识卡存储。
    from dianzhentong.storage import make_learning_activity
    repository.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", "control_power"))
    waiting = chapter_progress(repository, chapter)
    assert waiting.status == "待测验"
    question = questions_for_chapter(chapter["id"])[0]
    repository.save_quiz(make_quiz_record(chapter["id"], [answer(question)], quiz_id="pass"))
    completed = chapter_progress(repository, chapter)
    assert completed.status == "已完成"
    assert completed.quiz_passed is True


def test_app_exposes_quiz_pages_without_pyarrow_components():
    source = open("app.py", encoding="utf-8").read()
    assert "start_chapter_quiz" in source
    assert "章节测验报告" in source
    assert "st.dataframe" not in source
    assert "st.table" not in source
