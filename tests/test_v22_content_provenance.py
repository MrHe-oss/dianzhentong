from pathlib import Path
from dianzhentong.assessment import questions_for_course, select_course_questions
from dianzhentong.course import COURSES
from dianzhentong.diagram_learning import DIAGRAM_CASES
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.provenance import CARD_PROVENANCE, RESULT_PROVENANCE, SOURCES, coverage_summary, is_card_assessable, provenance_for_diagram, provenance_for_question
from dianzhentong.quiz import QUESTIONS, card_id_for_question

def test_all_learning_content_is_traceable():
    assert set(CARD_PROVENANCE) == set(KNOWLEDGE_CARDS)
    question_cards = [card_id_for_question(item.id) for item in QUESTIONS]
    assert len(QUESTIONS) == 90
    assert all(provenance_for_question(card_id) for card_id in question_cards)
    assert len(RESULT_PROVENANCE) == 20
    assert len(DIAGRAM_CASES) == 18
    assert all(provenance_for_diagram(case["card_ids"])["sources"] for case in DIAGRAM_CASES.values())
    coverage = coverage_summary(question_cards, [case["card_ids"] for case in DIAGRAM_CASES.values()])
    assert coverage["questions"] == coverage["question_total"] == 90
    assert coverage["diagrams"] == coverage["diagram_total"] == 18

def test_sources_have_auditable_metadata_and_no_vague_labels():
    for source in SOURCES.values():
        assert source["url"].startswith("https://")
        assert source["publisher"] in {"ABB", "Schneider Electric", "Siemens"}
        assert source["checked_on"] == "2026-08-31"
        assert source["scope"]
        assert "某教材" not in source["title"] and "网络资料" not in source["title"]

def test_only_sourced_cards_enter_course_assessments():
    assert all(is_card_assessable(card_id_for_question(item.id)) for item in QUESTIONS)
    for course in COURSES:
        available = questions_for_course(course["id"])
        assert len(available) >= 10
        assert len(select_course_questions(course["id"], 10)) == 10

def test_source_center_and_ui_references_exist_without_pyarrow_widgets():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "内容与资料中心" in source
    assert "provenance_for_card(selected_card_id)" in source
    assert "provenance_for_question(card_id_for_question(question.id))" in source
    assert "provenance_for_diagram(case[\"card_ids\"])" in source
    assert "st.dataframe" not in source and "st.table" not in source
