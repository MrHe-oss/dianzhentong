from __future__ import annotations

from dianzhentong.course import (
    CHAPTERS,
    COURSE,
    GLOSSARY,
    chapter_by_id,
    chapter_progress,
    experiment_learning_record,
)
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.report import build_report
from dianzhentong.storage import MemoryPracticeRepository, make_learning_activity


def test_course_has_four_complete_chapters_and_known_cards():
    assert COURSE["title"] == "低压电器与电气控制基础"
    assert len(CHAPTERS) == 4
    assert {chapter["experiment_id"] for chapter in CHAPTERS if chapter["experiment_id"]} == {
        "motor_dol_no_start", "motor_forward_reverse"
    }
    for chapter in CHAPTERS:
        assert chapter["goal"] and chapter["points"] and chapter["reflection"] and chapter["next"]
        assert set(chapter["card_ids"]) <= set(KNOWLEDGE_CARDS)
        assert chapter_by_id(chapter["id"]) is chapter


def test_glossary_has_at_least_ten_safe_learning_terms():
    assert len(GLOSSARY) >= 10
    assert {"主回路", "控制回路", "常开触点", "常闭触点", "电气互锁"} <= set(GLOSSARY)
    text = " ".join(GLOSSARY.values())
    assert "短接验证" not in text
    assert "带电测量" not in text


def test_chapter_progress_uses_existing_learning_records_without_migration():
    repository = MemoryPracticeRepository()
    chapter = chapter_by_id("direct_start")
    before = chapter_progress(repository, chapter)
    assert before.status == "未开始"
    repository.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", "self_hold"))
    middle = chapter_progress(repository, chapter)
    assert middle.completion == 0.5
    assert middle.status == "学习中"


def test_completed_diagnosis_exports_experiment_learning_record():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_control_power")
    session.answer("异常")
    record = experiment_learning_record(session)
    assert record["experiment"] == "三相异步电动机直接启动"
    assert record["steps"] == ("控制电源状态（模拟）",)
    assert record["result"] == "模拟控制电源缺失"
    assert record["reflection"]
    report = build_report(session)
    assert "实验学习记录" in report
    assert "实验目的" in report
    assert "关键检查" in report
