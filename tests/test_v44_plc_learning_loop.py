from pathlib import Path

from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.diagram_learning import DIAGRAM_CASES, DiagramTrainingSession
from dianzhentong.quiz import QUESTIONS, card_id_for_question, questions_for_chapter
from dianzhentong.textbook_learning import calculate_unit_progress


BOOK_ID = "electrical_control_plc_s71200_tong"
PLC_CHAPTERS = ("p2_unit_1", "p2_unit_2", "p2_unit_3", "p2_unit_4")
PLC_CASES = ("plc_hardware_roles", "plc_scan_cycle", "plc_tia_objects", "plc_project_check")


def test_four_plc_units_have_five_traceable_questions_and_one_case():
    units = [item for item in BOOK_EDITION_MAPPINGS[BOOK_ID]["chapters"] if item["project_id"] == "project_2"]
    assert len(units) == 4
    for unit, chapter_id, case_id in zip(units, PLC_CHAPTERS, PLC_CASES):
        assert unit["quiz_chapter_ids"] == (chapter_id,)
        assert unit["case_ids"] == (case_id,)
        questions = questions_for_chapter(chapter_id)
        assert len(questions) == 5
        assert all(card_id_for_question(item.id) in unit["topic_ids"] for item in questions)
        example_question = next(item for item in questions if item.id == unit["worked_example"]["practice_question_id"])
        assert example_question.stem == unit["worked_example"]["practice"]
        assert example_question.answer == unit["worked_example"]["practice_answer"]
        assert example_question.options == tuple(unit["worked_example"]["options"])


def test_plc_cases_are_unique_safe_and_finish_after_a_wrong_first_choice():
    for case_id in PLC_CASES:
        case = DIAGRAM_CASES[case_id]
        assert case["chapter_id"] in PLC_CHAPTERS
        assert len(case["steps"]) == 3
        session = DiagramTrainingSession(case_id)
        for step in case["steps"]:
            wrong = next(item for item in step["options"] if item != step["answer"])
            assert session.answer(wrong) is False
            assert session.answer(step["answer"]) is True
            session.next_step()
        assert session.is_complete and session.correct_steps == 0


def test_unit_progress_uses_fixed_40_20_40_weights():
    topics = ("a", "b", "c")
    start = calculate_unit_progress(topics, set(), [])
    assert start.completion == 0 and start.status == "未开始"
    learning = calculate_unit_progress(topics, {"a", "b"}, [{"mode": "textbook_example"}])
    assert round(learning.completion, 4) == round(2 / 3 * 0.4 + 0.2, 4)
    mastered = calculate_unit_progress(topics, set(topics), [
        {"mode": "textbook_example"},
        {"mode": "textbook_unit_assessment", "passed": True},
    ])
    assert mastered.completion == 1.0 and mastered.status == "已完成"


def test_v44_ui_and_counts_are_updated():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.7"' in config and 'UI_STATE_VERSION = "4.7"' in app
    assert len(QUESTIONS) == 116 and len(DIAGRAM_CASES) == 22
    for phrase in ("知识学习 · 40%", "例题练习 · 20%", "单元评测 · 40%"):
        assert phrase in app
    assert "116道题" in readme and "22个识图案例" in readme
