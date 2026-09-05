from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from dianzhentong.backup import BackupValidationError, archive_json_bytes, parse_archive, import_archive, create_archive
from dianzhentong.content_loader import ContentValidationError, load_textbook_projects, validate_textbook_content
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.numeric_learning import parse_quantity, resistor_state
from dianzhentong.quiz import QUESTION_MAP, QuizAnswer, make_quiz_record, is_correct_answer, questions_for_chapter
from dianzhentong.provenance import provenance_for_card
from dianzhentong.review_plan import review_overview
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository, make_learning_activity, beijing_now
from dianzhentong.textbook_examples import example_for_unit
from dianzhentong.textbook_learning import calculate_unit_progress, lesson_for_topic

BOOK = "circuit_foundations"


@pytest.mark.parametrize("answer,expected", [("30 mA", True), ("3e-2 A", True), (".03 A", True),
                                           ("0.0297 A", True), ("0.0303 A", True), ("0.03031 A", False),
                                           ("30 A", False), ("-0.03 A", False), ("不确定", False)])
def test_numeric_units_and_tolerance(answer, expected):
    assert is_correct_answer(QUESTION_MAP["dc_q06"], answer) is expected


@pytest.mark.parametrize("answer", ["nan A", "inf A", "1e999 A", "1 V", "1", "1,000 A", "", "1 A extra", "1e20 A"])
def test_invalid_numeric_input(answer):
    with pytest.raises(ValueError):
        parse_quantity(answer, "A")


def test_model_independent_examples_and_scaling():
    first, second = resistor_state(4, 200), resistor_state(8, 200)
    assert first["current"] == Decimal("0.02") and first["power"] == Decimal("0.08")
    assert second["current"] == first["current"] * 2
    assert second["power"] == first["power"] * 4
    assert resistor_state(0, 200)["current"] == 0
    for u, r in [(4, 0), (4, -1), ("nan", 20), (4, "inf")]:
        with pytest.raises(ValueError): resistor_state(u, r)
    assert is_correct_answer(QUESTION_MAP["dc_q10"], "2 kΩ")
    assert is_correct_answer(QUESTION_MAP["q04"], "不确定")  # Legacy evidence question.


def test_original_course_content_and_book_identity():
    original = BOOK_EDITION_MAPPINGS[BOOK]
    assert original["kind"] == "original" and not original["isbn"]
    topics = original["chapters"][0]["topic_ids"]
    assert len(topics) == 3 and len(questions_for_chapter("dc_resistor_basics")) == 10
    for topic in topics:
        assert topic in KNOWLEDGE_CARDS and lesson_for_topic(topic)
        assert provenance_for_card(topic)
    assert example_for_unit(0, BOOK) != example_for_unit(0)
    invalid = deepcopy(load_textbook_projects(BOOK)[0])
    invalid["book"]["isbn"] = "invented"
    with pytest.raises(ContentValidationError): validate_textbook_content(invalid)


def record(selected, sequence=0):
    q = QUESTION_MAP["dc_q06"]
    return make_quiz_record(q.chapter_id, [QuizAnswer(q.id, selected, q.answer,
                            is_correct_answer(q, selected), selected == "不确定")],
                            quiz_id=f"numeric-{sequence}",
                            completed_at=beijing_now() + timedelta(seconds=sequence))


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
def test_numeric_backup_reviews_and_legacy_scores(tmp_path, kind):
    repo = MemoryPracticeRepository() if kind == "memory" else PracticeRepository(tmp_path / "numeric.db")
    for selected, seq in [("30 A", 0), ("30 mA", 1)]: repo.save_quiz(record(selected, seq))
    assert any(s.reference_id == "dc_q06" for s in review_overview(repo)["pending"])
    correct = record("0.03 A", 2)
    assert repo.save_quiz(correct) and not repo.save_quiz(correct)
    assert not review_overview(repo)["pending"]
    repo.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", "dc_ohm_law"))
    restored = MemoryPracticeRepository()
    archive = parse_archive(archive_json_bytes(repo))
    import_archive(restored, archive, confirmed=True)
    assert restored.quiz_summary()["attempts"] == 3
    assert restored.quiz_summary()["question_accuracy"] == pytest.approx(2/3)
    assert import_archive(restored, archive, confirmed=True)["duplicates"] == 4
    assert restored.learned_cards("motor_dol_no_start") == {"dc_ohm_law"}
    changed = deepcopy(archive)
    changed["data"]["quiz_sessions"][0]["answers"][0]["is_correct"] ^= True
    with pytest.raises(BackupValidationError): parse_archive(__import__('json').dumps(changed))
    assert not restored.quiz_history("p2_unit_1")


@pytest.mark.parametrize("environment", ["local", "community_cloud"])
def test_actual_numeric_quiz_ui_and_course_switching(tmp_path, monkeypatch, environment):
    from streamlit.testing.v1 import AppTest
    db = tmp_path / "ui.db"
    monkeypatch.setenv("DIANZHENTONG_ENV", environment)
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(db))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.selectbox(key="home_book_selection").set_value(BOOK).run()
    next(b for b in app.button if b.label == "进入教材学习").click().run()
    assert not app.exception
    assert any("先换单位" in e.label for e in app.expander)
    app.button(key="book_topic_dc_ohm_law").click().run()
    assert not app.exception and app.session_state["textbook_context"]["book_id"] == BOOK
    next(b for b in app.button if b.label == "返回本单元").click().run()
    app.selectbox(key="selected_textbook_id").set_value("electrical_control_plc_s71200_tong").run()
    app.selectbox(key="selected_textbook_chapter").set_value(6).run()
    app.selectbox(key="selected_textbook_id").set_value(BOOK).run()
    assert not app.exception and app.session_state["selected_textbook_chapter"] == 0
    app.session_state["quiz_state"] = {"chapter_id": "dc_resistor_basics", "mode": "textbook_unit_assessment", "quiz_id": "ui-numeric",
        "question_ids": ["dc_q06", "dc_q08"], "index": 0, "answers": [], "answered": False, "book_id": BOOK, "book_chapter_index": 0}
    app.session_state["stage"] = 10
    app.run()
    app.text_input(key="numeric_ui-numeric_dc_q06_0_value").set_value("nan").run()
    assert next(b for b in app.button if b.label == "提交答案").disabled
    app.text_input(key="numeric_ui-numeric_dc_q06_0_value").set_value("30").run()
    app.selectbox(key="numeric_ui-numeric_dc_q06_0_unit").set_value("mA").run()
    next(b for b in app.button if b.label == "提交答案").click().run()
    assert app.session_state["quiz_state"]["answers"][0]["is_correct"]
    next(b for b in app.button if b.label == "下一题").click().run()
    app.text_input(key="numeric_ui-numeric_dc_q08_1_value").set_value("0.2").run()
    next(b for b in app.button if b.label == "提交答案").click().run()
    next(b for b in app.button if b.label == "查看成绩").click().run()
    assert not app.exception
    app.run()
    repo = PracticeRepository(db)
    assert repo.quiz_summary("dc_resistor_basics")["attempts"] == 1
    assert repo.quiz_summary("dc_resistor_basics")["best_score"] == 1
    parse_archive(archive_json_bytes(repo))
    app.session_state["stage"] = 5
    app.run()
    assert not app.exception


def test_numeric_wrong_question_opens_from_review(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    db = tmp_path / "review.db"
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(db))
    repo = PracticeRepository(db)
    repo.save_quiz(record("30 A"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.session_state["stage"] = 18
    app.run()
    app.button(key="review_task_1_dc_q06").click().run()
    assert not app.exception
    assert any(t.label == "你的计算结果" for t in app.text_input)
