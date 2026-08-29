from __future__ import annotations

from datetime import datetime

import pytest

from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.report import build_report


def completed_session() -> DiagnosticSession:
    session = DiagnosticSession(KnowledgeBase())
    session.start(True)
    session.answer("正常")
    session.answer("异常")
    return session


def test_report_preserves_history_order_and_disclaimer():
    session = completed_session()
    report = build_report(session, datetime(2026, 8, 29, 12, 0))
    first = report.index("控制电源状态")
    second = report.index("控制回路熔断器")
    assert first < second
    assert "模拟熔断器断路" in report
    assert "仅用于教学模拟" in report
    assert "禁止据此进行带电测量、拆线或送电操作" in report


def test_incomplete_session_cannot_generate_report():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True)
    with pytest.raises(ValueError):
        build_report(session)


def test_knowledge_contains_no_actionable_live_work_instructions():
    raw = KnowledgeBase().data
    text = str(raw)
    forbidden_phrases = ["带电拆线", "合闸后测量", "直接短接", "强制吸合"]
    for phrase in forbidden_phrases:
        assert phrase not in text
    assert "不进行任何真实电压测量" in text
    assert "不操作真实带电设备" in raw["safety_notice"]


def test_every_result_has_source_and_review_status():
    knowledge = KnowledgeBase()
    for result in knowledge.results.values():
        assert result["source"]
        assert result["confidence"]

