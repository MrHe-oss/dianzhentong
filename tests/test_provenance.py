from __future__ import annotations

from pathlib import Path

from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.provenance import (
    RESULT_PROVENANCE,
    SOURCES,
    provenance_for_result,
    resolved_sources,
    validate_provenance,
)
from dianzhentong.report import build_report


def all_scenario_ids() -> set[str]:
    return {
        scenario_id
        for experiment_id in ("motor_dol_no_start", "motor_forward_reverse", "motor_jog_continuous")
        for scenario_id in KnowledgeBase(experiment_id).scenario_ids
    }


def test_all_twenty_faults_have_source_and_review_status():
    expected = all_scenario_ids()
    assert len(expected) == 20
    validate_provenance(expected)
    assert set(RESULT_PROVENANCE) == expected


def test_all_sources_are_https_and_identify_type():
    assert SOURCES
    for source in SOURCES.values():
        assert source["url"].startswith("https://")
        assert source["title"]
        assert source["type"]


def test_inconclusive_results_do_not_claim_reviewed_fault_source():
    assert provenance_for_result("inconsistent") is None
    assert provenance_for_result("fr_inconsistent") is None


def test_download_report_separates_simulated_evidence_and_reference_principle():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_control_power")
    session.answer("异常")
    report = build_report(session)
    assert "证据：控制电源状态被记录为异常" in report
    assert "参考原理" in report
    assert "审校状态" in report
    assert "https://" in report


def test_review_document_and_ui_source_links_exist():
    assert Path("CONTENT_REVIEW.md").exists()
    source = Path("app.py").read_text(encoding="utf-8")
    assert "provenance_for_result(session.result_id)" in source
    assert "参考资料" in source
    item = provenance_for_result("fr_cause_interlock")
    assert item is not None
    assert len(resolved_sources(item)) == 2
