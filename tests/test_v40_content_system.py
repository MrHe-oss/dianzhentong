import copy
from pathlib import Path

import pytest

from dianzhentong.content_loader import ContentValidationError, load_textbook_content, load_textbook_projects, validate_textbook_content
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.textbook_learning import TEXTBOOK_LESSONS


BOOK_ID = "electrical_control_plc_s71200_tong"


def test_structured_content_drives_catalog_and_all_lessons():
    content = load_textbook_content(BOOK_ID)
    assert content["schema_version"] == 1
    assert content["book"]["id"] in BOOK_EDITION_MAPPINGS
    topic_ids = [topic["id"] for project in load_textbook_projects(BOOK_ID)
                 for unit in project["project"]["units"] for topic in unit["topics"]]
    assert topic_ids == list(TEXTBOOK_LESSONS)
    assert len(topic_ids) == 30


def test_content_validation_rejects_bad_answer_and_insecure_source():
    content = copy.deepcopy(load_textbook_content(BOOK_ID))
    content["project"]["units"][0]["topics"][0]["lesson"]["answer"] = "不存在的选项"
    with pytest.raises(ContentValidationError):
        validate_textbook_content(content)
    content = copy.deepcopy(load_textbook_content(BOOK_ID))
    content["book"]["source_url"] = "http://example.com/book"
    with pytest.raises(ContentValidationError):
        validate_textbook_content(content)


def test_v40_has_authoring_guide_and_keeps_ui_data_components_safe():
    app = Path("app.py").read_text(encoding="utf-8")
    config = Path("dianzhentong/config.py").read_text(encoding="utf-8")
    guide = Path("CONTENT_AUTHORING.md").read_text(encoding="utf-8")
    assert 'APP_VERSION = "4.7"' in config and 'UI_STATE_VERSION = "4.7"' in app
    assert "结构化教材内容" in guide and "不得复制教材正文" in guide
    assert "st.dataframe" not in app and "st.table" not in app
