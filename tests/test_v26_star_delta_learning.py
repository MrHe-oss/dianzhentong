from pathlib import Path

from dianzhentong.diagram_learning import DIAGRAM_CASES, DiagramTrainingSession
from dianzhentong.star_delta_learning import (
    STAR_DELTA_STAGES, build_star_delta_course_summary,
    diagram_choice_feedback, stage_for_diagram_step, star_delta_summary_text,
)
from dianzhentong.storage import MemoryPracticeRepository, make_diagram_record


def test_four_stage_demo_has_safe_unique_sequence():
    assert [item["id"] for item in STAR_DELTA_STAGES] == [
        "stopped", "star_start", "transition", "delta_run",
    ]
    assert len({item["title"] for item in STAR_DELTA_STAGES}) == 4
    payload = str(STAR_DELTA_STAGES)
    assert "星形接触器：已退出" in payload
    assert "三角接触器：等待允许" in payload
    for forbidden in ("端子号", "六端子", "电压值", "导线位置", "带电测量"):
        assert forbidden not in payload


def test_each_star_delta_step_has_stage_and_actionable_feedback():
    for case_id, case in DIAGRAM_CASES.items():
        if not case["chapter_id"].startswith("star_delta_"):
            continue
        for index, step in enumerate(case["steps"]):
            wrong = next(item for item in step["options"] if item != step["answer"])
            feedback = diagram_choice_feedback(case_id, index, wrong)
            assert stage_for_diagram_step(case_id, index)
            assert feedback["stage"] and feedback["role"] == step["answer"]
            assert wrong in feedback["reason"]
            assert feedback["card_title"]


def test_course_summary_reports_diagram_progress_without_false_weakness():
    repository = MemoryPracticeRepository()
    empty = build_star_delta_course_summary(repository)
    assert empty["diagram_attempts"] == 0
    assert empty["diagram_accuracy"] == 0
    assert empty["weak_cards"] == ()

    training = DiagramTrainingSession("sd_sequence", training_id="v26-sequence")
    while not training.is_complete:
        training.answer(training.current_step["answer"])
        training.next_step()
    repository.save_diagram_practice(make_diagram_record(training))
    summary = build_star_delta_course_summary(repository)
    assert summary["diagram_attempts"] == 1
    assert summary["diagram_accuracy"] == 1.0
    assert "星—三角降压启动课程总结" in star_delta_summary_text(summary)


def test_v26_ui_contains_demo_feedback_report_and_mobile_rules():
    source = Path("app.py").read_text(encoding="utf-8")
    for phrase in ("启动阶段状态演示", "当前阶段：", "星—三角课程总结", "推荐复习："):
        assert phrase in source
    assert "@media(max-width:640px)" in source
    assert "st.dataframe" not in source and "st.table" not in source
