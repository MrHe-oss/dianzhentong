from pathlib import Path
import pytest
from dianzhentong.plc_lab import LabSession
from dianzhentong.plc_observation import task_evidence


def observing(lab):
    session = LabSession(lab)
    session.begin()
    session.answer("不确定")
    return session


def test_logic_comparison_requires_same_inputs_and_not_b_is_ignored():
    s = observing("logic")
    s.observe(operator="AND", a=True, b=False)
    first = s.history[0]
    s.observe(operator="OR", a=False, b=True)
    assert "compare" not in task_evidence("logic", s.history)
    s.observe(operator="OR", a=True, b=False)
    assert "compare" in task_evidence("logic", s.history)
    s.observe(operator="NOT", a=True, b=True)
    assert len(s.history[-1].nodes) == 2
    s.observe(operator="NOT", a=False, b=False)
    assert all(done for _, done in s.observation_tasks())
    assert first == s.history[0] and first.after != s.history[2].after
    assert "B不参与" in s.history[-1].explanation


def test_scan_pending_and_task_evidence():
    s = observing("scan")
    s.observe(a=False)
    assert s.history[-1].nodes == (("本轮快照", False), ("本轮计算", None), ("本轮显示更新", None))
    s.observe(a=True)
    assert s.history[-1].nodes[1:] == (("本轮计算", False), ("本轮显示更新", None))
    s.observe(a=True)
    assert task_evidence("scan", s.history) == {"snapshot"}
    for _ in range(3): s.observe(a=True)
    assert task_evidence("scan", s.history) == {"snapshot", "next_cycle"}
    assert s.history[-1].nodes[-1] == ("本轮显示更新", True)
    s.observe(a=False)
    assert s.history[-1].nodes[1][1] is None
    other = observing("scan")
    for _ in range(9): other.observe(a=True)
    assert not task_evidence("scan", other.history)


def test_hold_explains_each_condition_and_observed_tasks():
    s = observing("hold")
    s.observe()
    assert "均不成立" in s.history[-1].explanation
    s.observe(start=True)
    assert "启动请求成立" in s.history[-1].explanation
    s.observe(start=False)
    assert "保持分支" in s.history[-1].explanation
    s.observe(start=True, stop=True)
    assert "停止优先" in s.history[-1].explanation
    assert all(done for _, done in s.observation_tasks())
    s.observe(allow=False, start=True)
    assert "许可未成立" in s.history[-1].explanation
    assert not s.running


@pytest.mark.parametrize("lab", ["logic", "scan", "hold"])
def test_report_does_not_score_operations_or_claim_unseen_tasks(lab):
    s = observing(lab)
    for _ in range(6): s.observe()
    s.finish_observation()
    s.answer("不确定")
    record = s.to_record()
    assert record.correct_count == 0 and record.total_count == 2
    assert len(s.history) == 6
    text = s.report_text()
    assert "尚未观察" in text and "操作前" in text and "原因" in text
    assert s.to_record() is record
    assert LabSession(lab).history == []


def test_ui_input_change_is_not_execution_and_report_shows_observations(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "ui.db"))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.session_state["stage"] = 26
    app.session_state["plc_lab_session"] = observing("hold")
    app.run()
    session_id = app.session_state["plc_lab_session"].session_id
    app.checkbox(key=session_id + "start").check().run()
    assert not app.session_state["plc_lab_session"].history
    app.button(key="lab_observe").click().run()
    app.checkbox(key=session_id + "start").uncheck().run()
    assert len(app.session_state["plc_lab_session"].history) == 1
    app.button(key="lab_observe").click().run()
    assert "keep" in task_evidence("hold", app.session_state["plc_lab_session"].history)
    app.run()
    assert len(app.session_state["plc_lab_session"].history) == 2
    app.button(key="lab_transfer").click().run()
    app.radio(key=f"lab_answer_{session_id}_transfer").set_value("假").run()
    app.button(key="lab_submit").click().run()
    assert not app.exception
    assert any("本次观察与原因" in item.value for item in app.markdown)
