from dianzhentong.content_loader import load_textbook_content, load_textbook_projects
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.learning import KNOWLEDGE_CARDS
from dianzhentong.provenance import CARD_PROVENANCE, SOURCES
from dianzhentong.textbook_discovery import build_textbook_index, search_textbooks


BOOK_ID = "electrical_control_plc_s71200_tong"


def test_project2_matches_publisher_catalog_and_has_complete_original_lessons():
    content = load_textbook_content(BOOK_ID, "project_2")
    assert content["project"]["title"] == "项目2 初识S7-1200 PLC"
    assert [unit["source_title"] for unit in content["project"]["units"]] == [
        "项目2·任务1 认识S7-1200 PLC硬件系统",
        "项目2·任务2 S7-1200 PLC程序设计基础学习",
        "项目2·任务3 TIA博途编程软件使用",
        "项目2·任务4 简单项目的建立与运行",
    ]
    topics = [topic for unit in content["project"]["units"] for topic in unit["topics"]]
    assert len(topics) == 12
    assert all(topic["id"] in KNOWLEDGE_CARDS and topic["lesson"]["answer"] in topic["lesson"]["options"] for topic in topics)


def test_two_projects_are_loaded_into_catalog_and_search():
    projects = load_textbook_projects(BOOK_ID)
    assert [item["project"]["id"] for item in projects] == ["project_1", "project_2"]
    book = BOOK_EDITION_MAPPINGS[BOOK_ID]
    assert len(book["projects"]) == 2 and len(book["chapters"]) == 7
    results = search_textbooks(build_textbook_index([BOOK_ID]), "TIA 博途")
    assert results and all(item["chapter_index"] >= 3 for item in results)


def test_project2_has_siemens_source_mapping_and_safe_scope():
    assert SOURCES["siemens_s71200_manual"]["publisher"] == "Siemens"
    project2 = load_textbook_content(BOOK_ID, "project_2")
    topic_ids = [topic["id"] for unit in project2["project"]["units"] for topic in unit["topics"]]
    assert all(topic_id in CARD_PROVENANCE for topic_id in topic_ids)
    raw = str(project2)
    for forbidden in ("真实端子号", "强制变量步骤", "送电步骤", "接线步骤"):
        assert forbidden not in raw


def test_v43_ui_exposes_multiple_projects_without_fake_training():
    app = open("app.py", encoding="utf-8").read()
    config = open("dianzhentong/config.py", encoding="utf-8").read()
    assert 'APP_VERSION = "4.6"' in config and 'UI_STATE_VERSION = "4.6"' in app
    for phrase in ("已上线项目", "教材项目学习进度", "本项目专项题库将在后续版本加入", "本项目互动训练正在建设"):
        assert phrase in app
