from __future__ import annotations

from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.learning import (
    KNOWLEDGE_CARDS,
    REVIEW_STATUS,
    card_for_node,
    cards_for_experiment,
    relationship_steps,
    review_cards,
)
from dianzhentong.report import build_report


def test_complete_knowledge_cards_exist():
    assert len(KNOWLEDGE_CARDS) == 21
    required = {"title", "principle", "role", "normal", "abnormal", "review"}
    assert all(required <= set(card) for card in KNOWLEDGE_CARDS.values())
    assert "待专业人员复核" in REVIEW_STATUS


def test_every_diagnostic_node_has_a_review_card():
    for experiment_id in ("motor_dol_no_start", "motor_forward_reverse"):
        knowledge = KnowledgeBase(experiment_id)
        for node_id in knowledge.nodes:
            card = card_for_node(node_id)
            assert card is not None, node_id
            assert card["title"]


def test_experiment_cards_are_scoped_and_include_expected_topics():
    direct = {item["id"] for item in cards_for_experiment("motor_dol_no_start")}
    reverse = {item["id"] for item in cards_for_experiment("motor_forward_reverse")}
    assert "control_power" in direct
    assert "electrical_interlock" not in direct
    assert {"electrical_interlock", "forward_reverse"} <= reverse


def test_review_cards_deduplicate_related_wrong_nodes():
    cards = review_cards(["start_button", "stop_button", "fuse", "start_button"])
    assert [item["id"] for item in cards] == ["button_contacts", "fuse"]


def test_relationship_diagrams_are_logic_only():
    text = " ".join(
        relationship_steps("motor_dol_no_start")
        + relationship_steps("motor_forward_reverse")
    )
    for forbidden in ("端子号", "220V", "380V", "短接", "带电测量"):
        assert forbidden not in text


def test_guided_report_keeps_path_but_omits_score():
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    session.answer("正常")
    session.answer("异常")
    report = build_report(session, include_score=False)
    assert "推荐排查顺序" in report
    assert "练习得分" not in report
    assert "有效判断得分" not in report
    assert "错因分析" not in report
