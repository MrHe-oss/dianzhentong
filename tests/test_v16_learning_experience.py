from __future__ import annotations

from dianzhentong.course import ALL_CHAPTERS, chapter_learning_steps, recommended_chapter_action
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.quiz import (
    QUESTIONS, answer_feedback, card_id_for_question, similar_questions,
)
from dianzhentong.report import build_report
from dianzhentong.storage import MemoryPracticeRepository


def solve(knowledge: KnowledgeBase, scenario_id: str) -> DiagnosticSession:
    session = DiagnosticSession(knowledge)
    session.start(True, scenario_id=scenario_id)
    while not session.is_complete:
        session.answer(session.expected_answer or "不确定")
    return session


def test_every_question_has_unique_options_answer_explanation_and_card():
    assert len(QUESTIONS) == 116
    for question in QUESTIONS:
        assert len(question.options) == len(set(question.options))
        assert question.answer in question.options
        assert question.explanation and question.knowledge_point
        assert card_id_for_question(question.id) in KNOWLEDGE_CARDS
        assert answer_feedback(question, "不确定")


def test_similar_questions_stay_in_chapter_and_never_repeat_current():
    for question in QUESTIONS:
        for related in similar_questions(question.id):
            assert related.id != question.id
            assert related.chapter_id == question.chapter_id


def test_all_chapters_have_clear_learning_path_and_recommendation():
    repository = MemoryPracticeRepository()
    for chapter in ALL_CHAPTERS:
        steps = chapter_learning_steps(repository, chapter)
        names = [item.name for item in steps]
        if chapter["id"] in {"diagram_symbols_roles", "series_parallel_logic", "control_path_tracing",
                              "star_delta_principles", "star_delta_components", "star_delta_sequence",
                              "timer_functions", "on_off_delay", "sequence_control"}:
            assert names == ["学习知识卡", "完成互动识图", "通过章节测验", "完成本章总结"]
        else:
            assert names == ["学习知识卡", "通过章节测验", "完成引导实验", "完成随机练习", "完成本章总结"]
        assert recommended_chapter_action(repository, chapter) in {item.name for item in steps}


def test_all_twenty_fault_reports_include_learning_next_step():
    scenario_count = 0
    for experiment_id in KnowledgeBase.catalog():
        knowledge = KnowledgeBase(experiment_id)
        for scenario_id in knowledge.scenario_ids:
            scenario_count += 1
            report = build_report(solve(knowledge, scenario_id))
            assert "核心知识与下一步" in report
            assert "下一步建议" in report
            assert "安全声明" in report
    assert scenario_count == 20


def test_app_has_navigation_unlock_feedback_and_mobile_guards():
    source = open("app.py", encoding="utf-8").read()
    for phrase in (
        "继续上次学习", "course_unlock_requirement",
        "本章学习路径", "为什么这个答案不合适", "再做一道相似题",
        "最近学习位置", "最早在",
    ):
        assert phrase in source
    assert "@media(max-width:640px)" in source
    assert "st.dataframe" not in source and "st.table" not in source
