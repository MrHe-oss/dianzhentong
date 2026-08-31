import copy
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from dianzhentong.backup import create_archive, import_archive, parse_archive, preview_archive
from dianzhentong.capstone import (
    CAPSTONE_TASKS, CapstoneTaskSession, capstone_report_text,
    task_for_course, task_is_unlocked,
)
from dianzhentong.course import COURSES, COURSE_CHAPTERS
from dianzhentong.provenance import provenance_for_diagram
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import (
    MemoryPracticeRepository, PracticeRepository, make_capstone_record,
)


TZ = ZoneInfo("Asia/Shanghai")


def solve(task_id: str, wrong_count: int = 0, reflection: str = "这次练习让我学会按现象和控制路径判断，并会先复习首次判断错误的知识点。"):
    session = CapstoneTaskSession(task_id, session_id=f"session-{task_id}-{wrong_count}")
    for index, step in enumerate(session.task["steps"]):
        if index < wrong_count:
            wrong = next(item for item in step["options"] if item != step["answer"])
            assert not session.answer(wrong)
            assert not session.answer(wrong)
        assert session.answer(step["answer"])
        session.next_step()
    session.set_reflection(reflection)
    return session


def test_four_tasks_have_five_safe_sourced_steps():
    assert len(CAPSTONE_TASKS) == len(COURSES) == 5
    assert {task["course_id"] for task in CAPSTONE_TASKS.values()} == {item["id"] for item in COURSES}
    for task in CAPSTONE_TASKS.values():
        assert len(task["steps"]) == 5
        assert len({step["id"] for step in task["steps"]}) == 5
        assert provenance_for_diagram(step["card_id"] for step in task["steps"])["sources"]
    payload = str(CAPSTONE_TASKS)
    for forbidden in ("端子号", "六端子", "电压值", "导线位置", "参数整定", "带电测量"):
        assert forbidden not in payload


def test_first_choice_scores_once_and_wrong_answer_does_not_block():
    session = solve("capstone_low_voltage", wrong_count=1)
    assert session.objective_complete and session.correct_steps == 4
    assert session.passed
    assert len(session.wrong_steps) == 1
    assert session.first_answers["lv_scope"] != session.task["steps"][0]["answer"]


def test_threshold_and_reflection_validation():
    passed = solve("capstone_relay_control", wrong_count=1)
    failed = solve("capstone_relay_control", wrong_count=2)
    assert passed.correct_steps == 4 and passed.passed
    assert failed.correct_steps == 3 and not failed.passed
    short = solve("capstone_relay_control", reflection="不足二十字")
    assert not short.reflection_valid and not short.can_finalize
    with pytest.raises(ValueError):
        make_capstone_record(short)
    assert "学习反思" in capstone_report_text(passed)


@pytest.mark.parametrize("repository_factory", [MemoryPracticeRepository])
def test_memory_storage_deduplicates_and_summarizes(repository_factory):
    repository = repository_factory()
    record = make_capstone_record(solve("capstone_diagram_reading"), datetime(2026, 8, 31, 10, tzinfo=TZ))
    assert repository.save_capstone(record)
    assert not repository.save_capstone(record)
    assert repository.capstone_summary(record.course_id)["best_score"] == 1.0
    assert len(repository.capstone_history(record.course_id)) == 1


def test_sqlite_migration_storage_and_clear(tmp_path):
    database = tmp_path / "old.db"
    repository = PracticeRepository(database)
    record = make_capstone_record(solve("capstone_star_delta"))
    assert repository.save_capstone(record)
    assert not repository.save_capstone(record)
    assert repository.capstone_summary()["passed_count"] == 1
    PracticeRepository(database)  # 重复初始化无副作用。
    assert repository.capstone_summary()["attempts"] == 1
    assert repository.clear(confirmed=False) == 0
    assert repository.clear(confirmed=True) >= 1
    assert repository.capstone_summary()["attempts"] == 0


def test_unlock_requires_all_chapter_quizzes_without_changing_course_status():
    repository = MemoryPracticeRepository()
    course_id = COURSES[0]["id"]
    assert task_for_course(course_id)["course_id"] == course_id
    assert not task_is_unlocked(repository, course_id)
    for chapter in COURSE_CHAPTERS[course_id]:
        question = questions_for_chapter(chapter["id"])[0]
        answer = QuizAnswer(question.id, question.answer, question.answer, True, False)
        repository.save_quiz(make_quiz_record(chapter["id"], (answer,), quiz_id=f"unlock-{chapter['id']}"))
    assert task_is_unlocked(repository, course_id)


def test_v3_archive_roundtrip_and_v1_v2_compatibility():
    source = MemoryPracticeRepository()
    source.save_capstone(make_capstone_record(solve("capstone_star_delta")))
    archive = create_archive(source)
    assert archive["schema_version"] == 3
    assert preview_archive(archive).capstone_task_records == 1
    target = MemoryPracticeRepository()
    first = import_archive(target, archive, confirmed=True)
    second = import_archive(target, archive, confirmed=True)
    assert first["capstone_task_records"] == 1 and second["duplicates"] == 1

    for version in (1, 2):
        old = copy.deepcopy(archive)
        old["schema_version"] = version
        old["data"].pop("capstone_task_records")
        if version == 1:
            old["data"].pop("diagram_practice_records")
        parsed = parse_archive(__import__("json").dumps(old, ensure_ascii=False))
        assert preview_archive(parsed).capstone_task_records == 0


def test_v27_ui_has_course_center_report_and_mobile_layout():
    source = Path("app.py").read_text(encoding="utf-8")
    for phrase in ("课程综合实训", "提交反思并生成报告", "下载实训学习报告",
                   "再练一次", "打开10分钟复习清单", "返回课程"):
        assert phrase in source
    assert "@media(max-width:640px)" in source
    assert "st.dataframe" not in source and "st.table" not in source
