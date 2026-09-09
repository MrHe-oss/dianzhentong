import random
from itertools import product
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.quiz import QUESTION_MAP, questions_for_chapter, textbook_question_pool, card_id_for_question, OPTION_FEEDBACK
from dianzhentong.plc_lab import ScanModel, logic_output
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL
from dianzhentong.storage import PracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive
from dianzhentong.textbook_examples import formulas_for_topic

BOOK = "electrical_control_plc_s71200_tong"

def test_independent_pools_and_old_answers():
    assert len(questions_for_chapter("p2_unit_2")) == 8
    for chapter, excluded, size in (("p2_unit_1", "q91", 5), ("p2_unit_2", "q98", 7)):
        pool = textbook_question_pool((chapter,), excluded)
        assert len(pool) == size and excluded not in {q.id for q in pool}
        for seed in range(30):
            for n in (3, 5):
                selected = random.Random(seed).sample(pool, n)
                assert len({q.id for q in selected}) == n
    assert "q106" in {q.id for q in textbook_question_pool(("p2_unit_4",), "q106")}
    assert QUESTION_MAP["q100"].answer == "当前输入与状态影响下一轮结果"
    for q in textbook_question_pool(("p2_unit_2",), "q98"):
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}
        assert provenance_for_card(card_id_for_question(q.id))["status"] == STATUS_PARTIAL

def test_current_request_truth_table_and_snapshot():
    for topic in ("plc_program_cycle", "plc_logic_structure"):
        assert "\\\\" not in formulas_for_topic(topic)[0]["expression"]
    for allow, start, stop in product((False, True), repeat=3):
        request = logic_output("AND", logic_output("AND", allow, start), logic_output("NOT", stop))
        assert request == ((allow, start, stop) == (True, True, False))
    model = ScanModel()
    model.step(False)
    model.step(True)
    model.step(True)
    assert not model.output
    for _ in range(3):
        model.step(True)
    assert model.output

@pytest.mark.parametrize("answer_index", [0, 1, None])
def test_program_return_first_answer_and_backup(tmp_path, monkeypatch, answer_index):
    db = tmp_path / "study.db"
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(db))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    q = QUESTION_MAP["plc_stop_priority"]
    app.session_state["quiz_state"] = {"quiz_id": "program-return", "chapter_id": "p2_unit_2", "mode": "textbook_unit_assessment", "question_ids": [q.id], "index": 0, "answers": [], "answered": False, "book_id": BOOK, "book_chapter_index": 4}
    app.session_state["stage"] = 10
    app.run()
    app.radio(key=f"quiz_choice_{q.id}_0").set_value("不确定" if answer_index is None else q.options[answer_index]).run()
    next(b for b in app.button if b.label == "提交答案").click().run()
    first = list(app.session_state["quiz_state"]["answers"])
    app.button(key="quiz_relearn_topic").click().run()
    app.button(key="return_to_quiz").click().run()
    assert app.session_state["quiz_state"]["answers"] == first
    next(b for b in app.button if b.label == "查看成绩").click().run()
    if answer_index != 0:
        app.button(key=f"quiz_card_{q.id}").click().run()
        app.button(key="return_to_quiz").click().run()
    app.run()
    assert not app.exception and app.session_state["stage"] == 11
    repo = PracticeRepository(db)
    assert repo.quiz_summary("p2_unit_2")["attempts"] == 1
    parse_archive(archive_json_bytes(repo))

def test_program_unit_entry_pretest(tmp_path, monkeypatch):
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "entry.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == "进入教材学习").click().run()
    app.selectbox(key="selected_textbook_chapter").set_value(4).run()
    assert any("题库总量 8 题 · 可用于独立测验 7 题" in c.value for c in app.caption)
    app.button(key="book_pretest_start_4").click().run()
    ids = app.session_state["quiz_state"]["question_ids"]
    assert len(set(ids)) == 3 and "q98" not in ids and not app.exception
