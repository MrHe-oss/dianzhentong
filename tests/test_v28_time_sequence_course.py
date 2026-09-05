from pathlib import Path

from dianzhentong.assessment import questions_for_course, select_course_questions
from dianzhentong.capstone import CAPSTONE_TASKS, CapstoneTaskSession
from dianzhentong.course import (
    FIFTH_COURSE, FIFTH_COURSE_CHAPTERS, course_is_unlocked,
)
from dianzhentong.diagram_learning import DIAGRAM_CASES, DiagramTrainingSession, cases_for_chapter
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.provenance import CARD_PROVENANCE, SOURCES, provenance_for_diagram
from dianzhentong.quiz import card_id_for_question, questions_for_chapter
from dianzhentong.time_sequence_learning import (
    OFF_DELAY_STAGES, ON_DELAY_STAGES, SEQUENCE_STAGES, demos_for_chapter,
)


class UnlockRepository:
    def __init__(self, fourth_passed: bool):
        self.fourth_passed = fourth_passed

    def quiz_summary(self, course_id: str):
        return {"passed_count": 1 if course_id == "star_delta_starting" and self.fourth_passed else 0}


def test_fifth_course_has_expected_complete_content():
    assert len(FIFTH_COURSE_CHAPTERS) == 3
    card_ids = {card_id for chapter in FIFTH_COURSE_CHAPTERS for card_id in chapter["card_ids"]}
    assert card_ids == {"timer_role", "on_delay", "off_delay", "sequence_control"}
    assert card_ids <= set(KNOWLEDGE_CARDS) == set(CARD_PROVENANCE)
    questions = questions_for_course(FIFTH_COURSE["id"])
    assert len(questions) == 15
    assert all(len(questions_for_chapter(chapter["id"])) == 5 for chapter in FIFTH_COURSE_CHAPTERS)
    assert len(select_course_questions(FIFTH_COURSE["id"], 10)) == 10
    assert all(card_id_for_question(item.id) in card_ids for item in questions)


def test_fifth_course_unlocks_only_after_fourth_course_assessment():
    assert not course_is_unlocked(UnlockRepository(False), FIFTH_COURSE["id"])
    assert course_is_unlocked(UnlockRepository(True), FIFTH_COURSE["id"])


def test_six_time_cases_are_sourced_safe_and_finish_after_mistakes():
    chapter_ids = {chapter["id"] for chapter in FIFTH_COURSE_CHAPTERS}
    cases = {case_id: case for case_id, case in DIAGRAM_CASES.items() if case["chapter_id"] in chapter_ids}
    assert len(cases) == 6
    assert all(len(cases_for_chapter(chapter_id)) == 2 for chapter_id in chapter_ids)
    banned = ("端子号", "电压值", "导线位置", "接线步骤", "整定值", "带电操作")
    for case_id, case in cases.items():
        assert provenance_for_diagram(case["card_ids"])["sources"]
        assert not any(term in str(case) for term in banned)
        session = DiagramTrainingSession(case_id)
        while not session.is_complete:
            step = session.current_step
            wrong = next(option for option in step["options"] if option != step["answer"])
            assert not session.answer(wrong)
            assert session.answer(step["answer"])
            session.next_step()
        assert session.correct_steps == 0


def test_time_demo_and_capstone_are_complete_and_abstract():
    assert all(len(stages) == 5 for stages in (ON_DELAY_STAGES, OFF_DELAY_STAGES, SEQUENCE_STAGES))
    assert demos_for_chapter("on_off_delay")[1][0] == "断电延时"
    task = CAPSTONE_TASKS["capstone_time_sequence"]
    assert task["course_id"] == FIFTH_COURSE["id"] and len(task["steps"]) == 5
    session = CapstoneTaskSession("capstone_time_sequence")
    while not session.objective_complete:
        session.answer(session.current_step["answer"])
        session.next_step()
    session.set_reflection("我会先识别输入变化，再区分等待阶段和输出变化，并依据题设判断后续顺序。")
    assert session.passed and session.can_finalize


def test_v28_sources_version_and_ui_guards():
    assert {"abb_time_relay", "schneider_time_relay"} <= set(SOURCES)
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    assert 'UI_STATE_VERSION = "4.7"' in app and 'APP_VERSION = "4.7"' in config
    assert "时间过程状态演示" in app and "demos_for_chapter" in app
    assert "st.dataframe" not in app and "st.table" not in app
