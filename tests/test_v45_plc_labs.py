from itertools import product
from pathlib import Path

import pytest

from dianzhentong.plc_lab import LABS, LabSession, ScanModel, logic_output, hold_next
from dianzhentong.quiz import QUESTION_MAP, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.review_plan import review_overview


@pytest.mark.parametrize("a,b", product((False, True), repeat=2))
def test_truth_tables(a, b):
    assert logic_output("AND", a, b) == (a and b)
    assert logic_output("OR", a, b) == (a or b)
    assert logic_output("NOT", a, b) == (not a)


@pytest.mark.parametrize("allow,stop,start,previous", product((False, True), repeat=4))
def test_hold_priority(allow, stop, start, previous):
    assert hold_next(allow, stop, start, previous) == (allow and not stop and (start or previous))


def test_scan_snapshot_and_hold_recovery():
    scan = ScanModel()
    scan.step(False)
    scan.step(True)
    scan.step(True)
    assert not scan.output and scan.cycles == 1
    scan.step(True)
    scan.step(False)
    assert not scan.output
    scan.step(False)
    assert scan.output and scan.cycles == 2
    running = hold_next(False, False, False, True)
    assert not hold_next(True, False, False, running)


def complete(lab, correct=True):
    session = LabSession(lab)
    session.begin()
    for phase in ("predict", "transfer"):
        q = QUESTION_MAP[f"plc_{lab}_{phase}"]
        session.answer(q.answer if correct else "不确定")
        with pytest.raises(ValueError):
            session.answer(q.answer)
        if phase == "predict":
            for _ in range(3):
                session.observe(a=True)
            session.finish_observation()
    return session


@pytest.mark.parametrize("lab", LABS)
@pytest.mark.parametrize("sqlite", [False, True])
def test_lab_records_backup_and_mastery(lab, sqlite, tmp_path):
    repo = PracticeRepository(tmp_path / "lab.db") if sqlite else MemoryPracticeRepository()
    session = complete(lab, False)
    record = session.to_record()
    assert record.correct_count == 0 and record.total_count == 2
    assert repo.save_quiz(record) and not repo.save_quiz(session.to_record())
    ids = {f"plc_{lab}_predict", f"plc_{lab}_transfer"}
    assert ids <= {x.reference_id for x in review_overview(repo)["pending"]}
    repo.save_quiz(complete(lab).to_record())
    assert ids <= {x.reference_id for x in review_overview(repo)["pending"]}
    repo.save_quiz(complete(lab).to_record())
    assert ids.isdisjoint({x.reference_id for x in review_overview(repo)["pending"]})
    restored = MemoryPracticeRepository()
    archive = parse_archive(archive_json_bytes(repo))
    import_archive(restored, archive, confirmed=True)
    assert len(restored.quiz_history()) == 3
    import_archive(restored, archive, confirmed=True)
    assert len(restored.quiz_history()) == 3
    assert not restored.quiz_history("p2_unit_2")
    assert "首次判断" in session.report_text()


def test_gates_and_old_pools():
    s = LabSession("scan")
    with pytest.raises(ValueError): s.to_record()
    with pytest.raises(ValueError): s.observe()
    s.begin()
    with pytest.raises(ValueError): s.answer("invalid")
    s.answer("不确定")
    with pytest.raises(ValueError): s.finish_observation()
    s.observe()
    with pytest.raises(ValueError): s.finish_observation()
    for index in range(1, 5):
        assert len(questions_for_chapter(f"p2_unit_{index}")) == 5


def test_storage_failure_and_invalid_state(tmp_path, monkeypatch):
    from dianzhentong.storage import ResilientPracticeRepository
    from streamlit.testing.v1 import AppTest
    blocked = tmp_path / "a_file"
    blocked.touch()
    repo = ResilientPracticeRepository(blocked / "bad.db")
    assert not repo.persistent
    assert repo.save_quiz(complete("hold").to_record())
    assert len(repo.quiz_history()) == 1
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(blocked / "ui.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.session_state["stage"] = 26
    app.session_state["plc_lab_session"] = {"obsolete": True}
    app.run()
    assert not app.exception and app.session_state["stage"] == 20
    app.session_state["stage"] = 26
    app.session_state["plc_lab_session"] = complete("logic", False)
    app.run()
    assert not app.exception
    assert any("存储不可用" in w.value for w in app.warning)
    app.button(key="lab_review").click().run()
    assert not app.exception
    next(b for b in app.button if b.key and b.key.startswith("review_task_1_plc_logic")).click().run()
    assert not app.exception and app.session_state["stage"] == 10


@pytest.mark.parametrize("lab", LABS)
@pytest.mark.parametrize("environment", ["local", "community_cloud"])
def test_full_ui(lab, environment, tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    path = tmp_path / "ui.db"
    monkeypatch.setenv("DIANZHENTONG_ENV", environment)
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(path))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.session_state["stage"] = 20
    app.session_state["selected_textbook_id"] = "electrical_control_plc_s71200_tong"
    app.session_state["selected_textbook_chapter"] = LABS[lab]["unit"]
    app.run()
    app.button(key=f"open_lab_{lab}").click().run()
    app.button(key="lab_begin").click().run()
    session_id = app.session_state["plc_lab_session"].session_id
    app.radio(key=f"lab_answer_{session_id}_predict").set_value("不确定").run()
    app.button(key="lab_submit").click().run()
    for _ in range(3): app.button(key="lab_observe").click().run()
    app.button(key="lab_transfer").click().run()
    q = QUESTION_MAP[f"plc_{lab}_transfer"]
    app.radio(key=f"lab_answer_{session_id}_transfer").set_value(q.answer).run()
    app.button(key="lab_submit").click().run()
    assert not app.exception
    repo = PracticeRepository(path)
    assert len(repo.quiz_history(f"plc_lab_{lab}")) == 1
    app.run()
    assert not app.exception and len(repo.quiz_history(f"plc_lab_{lab}")) == 1
    app.session_state["stage"] = 5
    app.run()
    assert not app.exception
    app.session_state["stage"] = 26
    app.run()
    app.button(key="lab_restart").click().run()
    assert app.session_state["plc_lab_session"].session_id != session_id
    app.button(key="lab_back").click().run()
    assert not app.exception and app.session_state["stage"] == 20
