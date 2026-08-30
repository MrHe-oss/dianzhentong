from __future__ import annotations

import pytest

from dianzhentong.course import (
    ALL_CHAPTERS, COURSE, COURSES, COURSE_CHAPTERS, SECOND_COURSE_CHAPTERS,
    course_is_unlocked,
)
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.learning import cards_for_experiment, relationship_steps
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.report import build_report
from dianzhentong.storage import MemoryPracticeRepository


JOG_CASES = (
    "jc_cause_public", "jc_cause_stop", "jc_cause_jog_button",
    "jc_cause_continuous_button", "jc_cause_self_hold", "jc_cause_coil",
)


def solve(scenario_id: str) -> DiagnosticSession:
    session = DiagnosticSession(KnowledgeBase("motor_jog_continuous"))
    session.start(True, scenario_id=scenario_id)
    while not session.is_complete:
        session.answer(session.expected_answer or "不确定")
    return session


def test_second_course_has_two_chapters_and_one_experiment():
    assert len(COURSES) == 2
    assert len(ALL_CHAPTERS) == 6
    assert len(SECOND_COURSE_CHAPTERS) == 2
    assert {item["experiment_id"] for item in SECOND_COURSE_CHAPTERS} == {"motor_jog_continuous"}
    assert len(COURSE_CHAPTERS[COURSES[1]["id"]]) == 2


@pytest.mark.parametrize("scenario_id", JOG_CASES)
def test_six_jog_continuous_scenarios_have_unique_safe_paths(scenario_id):
    session = solve(scenario_id)
    assert session.result_id == scenario_id
    assert all(item["is_correct"] is True for item in session.history)
    path = session.recommended_path()
    assert path and path["result_id"] == scenario_id
    assert len(path["steps"]) <= len(session.knowledge.nodes)


def test_jog_and_continuous_symptoms_skip_unrelated_branches():
    jog_nodes = {item["node_id"] for item in solve("jc_cause_jog_button").history}
    continuous_nodes = {item["node_id"] for item in solve("jc_cause_self_hold").history}
    assert "jc_continuous_button" not in jog_nodes and "jc_self_hold" not in jog_nodes
    assert "jc_jog_button" not in continuous_nodes


def test_new_experiment_has_cards_relationship_and_safe_report():
    assert {item["id"] for item in cards_for_experiment("motor_jog_continuous")} >= {
        "jog_control", "self_hold", "button_contacts"
    }
    assert "自锁保持条件" in relationship_steps("motor_jog_continuous")
    report = build_report(solve("jc_cause_self_hold"))
    assert "三相异步电动机点动与连续运行" in report
    assert "短接验证" not in report


def test_second_course_unlocks_after_any_first_course_quiz_pass():
    repository = MemoryPracticeRepository()
    second_id = COURSES[1]["id"]
    assert course_is_unlocked(repository, COURSE["id"])
    assert not course_is_unlocked(repository, second_id)
    question = questions_for_chapter("safety_and_circuits")[0]
    answer = QuizAnswer(question.id, question.answer, question.answer, True, False)
    repository.save_quiz(make_quiz_record("safety_and_circuits", [answer], quiz_id="unlock"))
    assert course_is_unlocked(repository, second_id)


def test_new_chapters_each_have_five_quiz_questions():
    assert [len(questions_for_chapter(item["id"])) for item in SECOND_COURSE_CHAPTERS] == [5, 5]


def test_app_contains_comprehensive_training_and_three_experiment_ui():
    source = open("app.py", encoding="utf-8").read()
    assert "开始跨实验综合训练" in source
    assert "start_comprehensive_training" in source
    assert "综合训练" in source
    assert "st.dataframe" not in source and "st.table" not in source
