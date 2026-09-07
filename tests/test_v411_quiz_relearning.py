from pathlib import Path
from streamlit.testing.v1 import AppTest
from dianzhentong.quiz import QUESTION_MAP, OPTION_FEEDBACK, answer_feedback
from dianzhentong.storage import PracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive

BOOK = "electrical_control_plc_s71200_tong"


def test_specific_explanations_match_actual_wrong_options():
    for question_id, explanations in OPTION_FEEDBACK.items():
        question = QUESTION_MAP[question_id]
        assert set(explanations) == set(question.options) - {question.answer}
        for selected, expected in explanations.items():
            assert answer_feedback(question, selected) == expected


def test_relearning_preserves_first_answer_report_and_backup(tmp_path, monkeypatch):
    db = tmp_path / "study.db"
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(db))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    question = QUESTION_MAP["hw_cpu_transfer"]
    app.session_state["quiz_state"] = {
        "quiz_id": "relearn-test", "chapter_id": "p2_unit_1", "mode": "textbook_unit_assessment",
        "question_ids": [question.id], "index": 0, "answers": [], "answered": False,
        "book_id": BOOK, "book_chapter_index": 3,
    }
    app.session_state["stage"] = 10
    app.run()
    app.radio(key=f"quiz_choice_{question.id}_0").set_value(question.options[1]).run()
    next(b for b in app.button if b.label == "提交答案").click().run()
    answer = dict(app.session_state["quiz_state"]["answers"][0])
    app.button(key="quiz_relearn_topic").click().run()
    assert app.session_state["textbook_context"] == {"book_id": BOOK, "chapter_index": 3, "topic_id": "plc_cpu"}
    app.run()
    app.button(key="return_to_quiz").click().run()
    assert app.session_state["quiz_state"]["answers"] == [answer]
    assert app.session_state["quiz_state"]["answered"]
    next(b for b in app.button if b.label == "查看成绩").click().run()
    app.button(key=f"quiz_card_{question.id}").click().run()
    app.button(key="return_to_quiz").click().run()
    assert app.session_state["stage"] == 11 and not app.exception
    repo = PracticeRepository(db)
    assert repo.quiz_summary("p2_unit_1")["attempts"] == 1
    parse_archive(archive_json_bytes(repo))
    app.session_state["textbook_quiz_return"] = {"quiz_id": "old", "stage": 10, "topic_id": "plc_cpu"}
    app.session_state["stage"] = 24
    app.run()
    assert not any(b.key == "return_to_quiz" for b in app.button)


def test_hardware_pretest_excludes_example_question(tmp_path, monkeypatch):
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "pool.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == "进入教材学习").click().run()
    app.selectbox(key="selected_textbook_chapter").set_value(3).run()
    app.button(key="book_pretest_start_3").click().run()
    assert "q91" not in app.session_state["quiz_state"]["question_ids"]
    assert len(app.session_state["quiz_state"]["question_ids"]) == 3
    assert not app.exception
