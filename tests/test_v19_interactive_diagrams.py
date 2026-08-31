from __future__ import annotations

import copy
from datetime import datetime

from dianzhentong.backup import create_archive, import_archive, parse_archive, preview_archive
from dianzhentong.course import THIRD_COURSE_CHAPTERS, chapter_learning_steps, chapter_progress
from dianzhentong.diagram_learning import DIAGRAM_CASES, DiagramTrainingSession, cases_for_chapter
from dianzhentong.quiz import QuizAnswer, make_quiz_record, questions_for_chapter
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository, make_diagram_record, make_learning_activity


def solve(case_id: str, wrong_first: bool = False) -> DiagramTrainingSession:
    session = DiagramTrainingSession(case_id, training_id=f"training-{case_id}")
    while not session.is_complete:
        step = session.current_step
        if wrong_first and not session.first_answers:
            session.answer(next(item for item in step["options"] if item != step["answer"]))
        session.answer(step["answer"])
        session.next_step()
    return session


def test_six_cases_have_three_unique_safe_steps_and_finish():
    assert len(DIAGRAM_CASES) == 12
    for case_id, case in DIAGRAM_CASES.items():
        assert len(case["steps"]) == 3
        assert len({item["id"] for item in case["steps"]}) == 3
        session = solve(case_id)
        assert session.is_complete and session.correct_steps == 3


def test_first_wrong_choice_scores_once_but_retry_can_finish():
    session = solve("dol_roles", wrong_first=True)
    assert session.correct_steps == 2
    assert session.wrong_steps == ["dol_roles_scope"]
    assert len(session.first_answers) == 3


def test_sqlite_and_memory_save_deduplicate_and_summarize(tmp_path):
    record = make_diagram_record(solve("reverse_branch", wrong_first=True), datetime.fromisoformat("2026-08-30T12:00:00+08:00"))
    for repository in (MemoryPracticeRepository(), PracticeRepository(tmp_path / "v19.db")):
        assert repository.save_diagram_practice(record) is True
        assert repository.save_diagram_practice(record) is False
        summary = repository.diagram_summary()
        assert summary["attempts"] == 1 and summary["completed_cases"] == 1
        assert summary["accuracy"] == 2 / 3
        assert summary["weakest_step"] == "reverse_branch_scope"


def test_diagram_chapter_progress_uses_40_30_30_weights():
    repository = MemoryPracticeRepository()
    chapter = THIRD_COURSE_CHAPTERS[0]
    repository.save_activity(make_learning_activity("motor_dol_no_start", "knowledge_card", chapter["card_ids"][0]))
    assert chapter_progress(repository, chapter).completion == 0.4
    repository.save_diagram_practice(make_diagram_record(solve(cases_for_chapter(chapter["id"])[0]["id"])))
    assert chapter_progress(repository, chapter).completion == 0.7
    question = questions_for_chapter(chapter["id"])[0]
    answer = QuizAnswer(question.id, question.answer, question.answer, True, False)
    repository.save_quiz(make_quiz_record(chapter["id"], [answer], quiz_id="v19-pass"))
    progress = chapter_progress(repository, chapter)
    assert progress.completion == 1 and progress.status == "已完成"
    assert [item.name for item in chapter_learning_steps(repository, chapter)] == [
        "学习知识卡", "完成互动识图", "通过章节测验", "完成本章总结"
    ]


def test_v3_backup_roundtrip_and_v1_import_compatibility():
    source = MemoryPracticeRepository()
    source.save_diagram_practice(make_diagram_record(solve("hold_parallel")))
    archive = create_archive(source)
    assert archive["schema_version"] == 3
    assert preview_archive(archive).diagram_practice_records == 1
    target = MemoryPracticeRepository()
    result = import_archive(target, parse_archive(str(__import__('json').dumps(archive))), True)
    assert result["diagram_practice_records"] == 1
    old = copy.deepcopy(archive)
    old["schema_version"] = 1
    old["data"].pop("diagram_practice_records")
    old["data"].pop("capstone_task_records")
    assert preview_archive(old).diagram_practice_records == 0


def test_app_contains_training_report_and_no_pyarrow():
    source = open("app.py", encoding="utf-8").read()
    for phrase in ("提交本步判断", "首次错误步骤", "推荐路径", "再练一个案例", "互动识图训练"):
        assert phrase in source
    assert "st.dataframe" not in source and "st.table" not in source
