from __future__ import annotations

import copy
import json

import pytest

from dianzhentong.backup import (
    ARCHIVE_FORMAT, BackupValidationError, archive_json_bytes, build_learning_summary,
    create_archive, import_archive, parse_archive, preview_archive,
)
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import (
    MemoryPracticeRepository, PracticeRepository, make_learning_activity,
)


def populated(repository):
    session = DiagnosticSession(KnowledgeBase())
    session.start(True, scenario_id="cause_fuse")
    while not session.is_complete:
        session.answer(session.expected_answer)
    repository.save(session.to_practice_record("2026-08-30T10:00:00+08:00"))
    repository.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", "fuse"))
    questions = questions_for_chapter("safety_and_circuits")[:5]
    answers = tuple(
        QuizAnswer(item.id, item.answer, item.answer, True, item.answer == "不确定")
        for item in questions
    )
    repository.save_quiz(make_quiz_record("safety_and_circuits", answers, quiz_id="quiz-backup"))
    return repository


def test_archive_is_anonymous_and_contains_all_record_types():
    archive = create_archive(populated(MemoryPracticeRepository()))
    assert archive["format"] == ARCHIVE_FORMAT
    preview = preview_archive(archive)
    assert (preview.practice_records, preview.learning_activities, preview.quiz_sessions) == (1, 1, 1)
    text = json.dumps(archive, ensure_ascii=False)
    for personal in ("姓名", "学校", "邮箱", "手机号", "设备信息"):
        assert personal not in text or personal in archive["privacy"]


@pytest.mark.parametrize("target_kind", ["memory", "sqlite"])
def test_json_round_trip_restores_empty_repository(tmp_path, target_kind):
    source = populated(MemoryPracticeRepository())
    archive = parse_archive(archive_json_bytes(source))
    target = MemoryPracticeRepository() if target_kind == "memory" else PracticeRepository(tmp_path / "restore.db")
    result = import_archive(target, archive, confirmed=True)
    assert result == {"practice_records": 1, "learning_activities": 1, "quiz_sessions": 1, "duplicates": 0}
    assert target.summary()["attempts"] == 1
    assert len(target.activities()) == 1
    assert target.quiz_summary()["attempts"] == 1


def test_duplicate_import_is_idempotent_and_does_not_overwrite():
    target = MemoryPracticeRepository()
    archive = create_archive(populated(MemoryPracticeRepository()))
    first = import_archive(target, archive, confirmed=True)
    second = import_archive(target, archive, confirmed=True)
    assert first["duplicates"] == 0
    assert second["duplicates"] == 3
    assert target.summary()["attempts"] == 1
    assert target.quiz_summary()["attempts"] == 1


def test_unconfirmed_import_has_no_side_effect():
    target = MemoryPracticeRepository()
    archive = create_archive(populated(MemoryPracticeRepository()))
    result = import_archive(target, archive, confirmed=False)
    assert sum(result.values()) == 0
    assert target.export_snapshot() == {
        "practice_records": [], "learning_activities": [], "quiz_sessions": []
    }


@pytest.mark.parametrize(
    "mutator",
    [
        lambda item: item.update(format="unknown"),
        lambda item: item.update(name="personal"),
        lambda item: item["data"]["practice_records"][0].update(experiment_id="unknown"),
        lambda item: item["data"]["quiz_sessions"][0]["answers"][0].update(correct_answer="被修改"),
        lambda item: item["data"]["quiz_sessions"][0]["answers"][0].update(is_correct=False),
    ],
)
def test_invalid_or_tampered_archive_is_rejected_before_write(mutator):
    archive = create_archive(populated(MemoryPracticeRepository()))
    mutator(archive)
    target = MemoryPracticeRepository()
    with pytest.raises(BackupValidationError):
        import_archive(target, archive, confirmed=True)
    assert target.summary()["attempts"] == 0


def test_malformed_json_and_oversized_file_are_rejected():
    with pytest.raises(BackupValidationError):
        parse_archive(b"not-json")
    with pytest.raises(BackupValidationError):
        parse_archive(b"x" * (5 * 1024 * 1024 + 1))


def test_txt_summary_is_readable_and_not_a_certificate():
    summary = build_learning_summary(populated(MemoryPracticeRepository()))
    assert "总练习次数：1" in summary
    assert "测验通过次数：1" in summary
    assert "课程与章节" in summary
    assert "不是职业资格、实训考核或能力认证证书" in summary


def test_app_has_backup_page_confirmation_and_no_pyarrow():
    source = open("app.py", encoding="utf-8").read()
    assert "学习档案导出与恢复" in source
    assert "下载JSON完整备份" in source
    assert "我确认将以上匿名学习记录合并到当前档案" in source
    assert "st.dataframe" not in source and "st.table" not in source
