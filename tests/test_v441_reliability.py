import copy
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from dianzhentong.backup import BackupValidationError, archive_json_bytes, parse_archive, import_archive
from dianzhentong.quiz import QUESTION_MAP, QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository
from dianzhentong.review_plan import build_review_plan, review_overview
from dianzhentong.textbook_learning import calculate_unit_progress


def save(repo, question_ids, correct_count, mode="original_review", sequence=0):
    answers = []
    for i, qid in enumerate(question_ids):
        q = QUESTION_MAP[qid]
        selected = q.answer if i < correct_count else next(x for x in q.options if x != q.answer)
        answers.append(QuizAnswer(qid, selected, q.answer, selected == q.answer, False))
    q = QUESTION_MAP[question_ids[0]]
    record = make_quiz_record(q.chapter_id, answers, mode,
        completed_at=datetime(2026, 9, 3, tzinfo=ZoneInfo("Asia/Shanghai")) + timedelta(seconds=sequence))
    assert repo.save_quiz(record)
    return record


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
@pytest.mark.parametrize("unit", range(1, 5))
@pytest.mark.parametrize("correct", [3, 4, 5])
def test_plc_backup_restore_and_duplicate_import(tmp_path, kind, unit, correct):
    source = MemoryPracticeRepository()
    ids = [q.id for q in questions_for_chapter(f"p2_unit_{unit}")]
    record = save(source, ids, correct, "textbook_unit_assessment")
    assert record.passed == (correct >= 4)
    archive = parse_archive(archive_json_bytes(source))
    target = PracticeRepository(tmp_path / "restore.db") if kind == "sqlite" else MemoryPracticeRepository()
    result = import_archive(target, archive, confirmed=True)
    assert result["quiz_sessions"] == 1
    assert target.quiz_summary(record.chapter_id)["best_score"] == correct / 5
    assert import_archive(target, archive, confirmed=True)["duplicates"] == 1
    parse_archive(archive_json_bytes(target))


def test_old_mixed_chapter_unit_backup_and_invalid_scope():
    repo = MemoryPracticeRepository()
    save(repo, ["q07", "q17", "q31"], 2, "textbook_unit_pretest")
    archive = parse_archive(archive_json_bytes(repo))
    invalid = copy.deepcopy(archive)
    invalid["data"]["quiz_sessions"][0]["chapter_id"] = "unknown_chapter"
    with pytest.raises(BackupValidationError):
        parse_archive(json.dumps(invalid))
    invalid = copy.deepcopy(archive)
    invalid["data"]["quiz_sessions"][0]["chapter_id"] = "p2_unit_1"
    with pytest.raises(BackupValidationError):
        parse_archive(json.dumps(invalid))


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
def test_original_review_closes_only_after_two_original_answers(tmp_path, kind):
    repo = PracticeRepository(tmp_path / "review.db") if kind == "sqlite" else MemoryPracticeRepository()
    save(repo, ["q92"], 0)
    for i in (1, 2):
        save(repo, ["q93"], 1, "similar_review", i)
    assert build_review_plan(repo)[0].reference_id == "q92"
    save(repo, ["q92"], 1, sequence=3)
    pending = next(x for x in review_overview(repo)["pending"] if x.reference_id == "q92")
    assert pending.consecutive_correct == 1
    record = save(repo, ["q92"], 1, sequence=4)
    assert not repo.save_quiz(record)
    assert all(x.reference_id != "q92" for x in review_overview(repo)["pending"])
    restored = MemoryPracticeRepository()
    import_archive(restored, parse_archive(archive_json_bytes(repo)), confirmed=True)
    assert next(x for x in review_overview(restored)["mastered"] if x.reference_id == "q92").consecutive_correct == 2


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
def test_example_is_real_progress_but_not_mastery_evidence(tmp_path, kind):
    repo = PracticeRepository(tmp_path / "example.db") if kind == "sqlite" else MemoryPracticeRepository()
    topics = ("plc_system_role", "plc_cpu", "plc_modules")
    assert not calculate_unit_progress(topics, set(topics), []).example_completed
    save(repo, ["q91"], 0)
    record = save(repo, ["q91"], 1, "textbook_example", 1)
    assert not repo.save_quiz(record)
    assert calculate_unit_progress(topics, set(topics), repo.quiz_history("p2_unit_1")).example_completed
    assert next(x for x in review_overview(repo)["pending"] if x.reference_id == "q91").consecutive_correct == 0
    parse_archive(archive_json_bytes(repo))


@pytest.mark.parametrize("environment", ["local", "community_cloud"])
def test_review_ui_targets_original_question_and_refresh_does_not_save_twice(tmp_path, monkeypatch, environment):
    monkeypatch.setenv("DIANZHENTONG_ENV", environment)
    monkeypatch.setenv("DIANZHENTONG_DB_PATH", str(tmp_path / "ui.db"))
    from streamlit.testing.v1 import AppTest
    repo = PracticeRepository(tmp_path / "ui.db")
    # Use real current timestamps so UI attempts sort after the initial error.
    q = QUESTION_MAP["q92"]
    repo.save_quiz(make_quiz_record(q.chapter_id, [QuizAnswer(q.id, q.options[1], q.answer, False, False)]))
    app = AppTest.from_file(Path("app.py").resolve(), default_timeout=20).run()
    app.session_state["stage"] = 18
    app.run()
    assert not app.exception
    next(b for b in app.button if b.key == "review_task_1_q92").click().run()
    for attempt in range(2):
        assert app.session_state["quiz_state"]["question_ids"] == ["q92"]
        assert app.session_state["quiz_state"]["mode"] == "original_review"
        next(r for r in app.radio if r.label == "请选择一个答案").set_value(q.answer).run()
        next(b for b in app.button if b.label == "提交答案").click().run()
        next(b for b in app.button if b.label == "查看成绩").click().run()
        assert not app.exception
        count = len(repo.quiz_history())
        app.run()
        assert len(repo.quiz_history()) == count
        next(b for b in app.button if b.label == "返回复习清单").click().run()
        assert not app.exception
        if attempt == 0:
            next(b for b in app.button if b.key == "review_task_1_q92").click().run()
    assert not review_overview(repo)["pending"]
