import json

import pytest

from dianzhentong.review_notebook import review_notebook_json, review_notebook_text
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository, StudyNote


BOOK_ID = "electrical_control_plc_s71200_tong"


def note(topic_id="fuse", content="熔断器属于短路保护元件，需要复习它与热继电器的区别。"):
    return StudyNote(BOOK_ID, topic_id, content, "2026-09-01T12:00:00+08:00")


def test_note_validation_save_update_search_and_delete():
    repository = MemoryPracticeRepository()
    assert repository.save_study_note(note()) is True
    assert repository.save_study_note(note(content="更新后的个人理解")) is False
    assert repository.study_notes("个人 理解")[0]["content"] == "更新后的个人理解"
    assert repository.study_notes("不存在") == []
    assert repository.delete_study_note(BOOK_ID, "fuse") is True
    assert repository.delete_study_note(BOOK_ID, "fuse") is False
    with pytest.raises(ValueError):
        note(content="   ")


def test_sqlite_notes_survive_restart_and_clear(tmp_path):
    path = tmp_path / "practice.db"
    first = PracticeRepository(path)
    first.save_study_note(note())
    second = PracticeRepository(path)
    assert second.study_notes()[0]["topic_id"] == "fuse"
    assert second.clear(confirmed=False) == 0
    assert second.clear(confirmed=True) >= 1
    assert second.study_notes() == []


def test_review_notebook_exports_are_anonymous_and_readable():
    notes = [note().as_row()]
    raw = review_notebook_json(notes, [], ["q1"])
    payload = json.loads(raw)
    assert payload["format"] == "dianzhentong-review-notebook"
    assert payload["notes"][0]["topic_id"] == "fuse"
    text = review_notebook_text(notes, {"fuse": "熔断器"})
    assert "熔断器" in text and "短路保护" in text
    assert all(word not in text for word in ("姓名", "邮箱"))


def test_v42_ui_has_notes_review_notebook_and_exports():
    app = open("app.py", encoding="utf-8").read()
    config = open("dianzhentong/config.py", encoding="utf-8").read()
    assert 'APP_VERSION = "4.5"' in config and 'UI_STATE_VERSION = "4.5"' in app
    for phrase in ("我的学习笔记", "我的复习本", "搜索个人笔记", "下载TXT笔记", "下载JSON复习本"):
        assert phrase in app
