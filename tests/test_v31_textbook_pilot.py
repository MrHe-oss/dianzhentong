from pathlib import Path

from dianzhentong.course import chapter_by_id
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS, topics_for_book_chapter
from dianzhentong.diagram_learning import DIAGRAM_CASES
from dianzhentong.engine import KnowledgeBase


BOOK_ID = "electrical_control_plc_s71200_tong"


def test_real_textbook_metadata_comes_from_publisher_listing():
    book = BOOK_EDITION_MAPPINGS[BOOK_ID]
    assert book["title"] == "电气控制与PLC应用技术（S7-1200）"
    assert book["author"] == "童克波"
    assert book["publisher"] == "机械工业出版社"
    assert book["isbn"] == "978-7-111-73129-0"
    assert book["published_at"] == "2023-07-24"
    assert book["source_url"] == "https://www.cmpedu.com/books/book/5606823.htm"
    assert book["official"] is False and "非出版社官方" in book["notice"]


def test_project_one_has_three_complete_original_learning_mappings():
    book = BOOK_EDITION_MAPPINGS[BOOK_ID]
    assert len(book["chapters"]) == 3
    assert [chapter["title"] for chapter in book["chapters"]] == [
        "电动机单向旋转控制", "电动机正反转控制", "星—三角减压启动控制",
    ]
    catalog = KnowledgeBase.catalog()
    for index, chapter in enumerate(book["chapters"]):
        assert topics_for_book_chapter(BOOK_ID, index)
        assert set(chapter["case_ids"]) <= set(DIAGRAM_CASES)
        assert set(chapter["experiment_ids"]) <= set(catalog)
        assert all(chapter_by_id(item) for item in chapter["quiz_chapter_ids"])


def test_textbook_page_shows_source_progress_practice_and_training():
    app = Path("app.py").read_text(encoding="utf-8")
    for phrase in (
        "查看出版社公开书目信息", "对应公开目录", "知识点学习",
        "本单元练习与实训", "开始5题练习", "开始互动识图", "开始引导实训",
        "不替代纸质或正版电子教材",
    ):
        assert phrase in app
    assert "st.dataframe" not in app and "st.table" not in app
