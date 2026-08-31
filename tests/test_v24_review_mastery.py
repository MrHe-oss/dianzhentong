from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from dianzhentong.quiz import QUESTION_MAP, QuizAnswer, make_quiz_record
from dianzhentong.review_plan import build_review_plan, review_overview
from dianzhentong.storage import DiagramPracticeRecord, MemoryPracticeRepository, PracticeRecord, PracticeRepository

TZ = ZoneInfo("Asia/Shanghai")

def save_answer(repo, question_id, correct, day, suffix):
    question = QUESTION_MAP[question_id]
    answer = QuizAnswer(question_id, question.answer if correct else "错误", question.answer, correct, False)
    repo.save_quiz(make_quiz_record(question.chapter_id, (answer,), quiz_id=f"quiz-{question_id}-{suffix}", completed_at=datetime(2026,8,day,10,tzinfo=TZ)))

def save_diagram(repo, wrong, day, suffix):
    repo.save_diagram_practice(DiagramPracticeRecord(f"diagram-{suffix}", datetime(2026,8,day,11,tzinfo=TZ).isoformat(), f"2026-08-{day:02d}", "diagram_symbols_roles", "dol_roles", 2 if wrong else 3, 3, ("dol_roles_scope",) if wrong else ()))

def test_question_requires_two_consecutive_correct_answers():
    repo = MemoryPracticeRepository(); save_answer(repo,"q01",False,20,"a"); save_answer(repo,"q01",True,21,"b")
    item = next(item for item in review_overview(repo)["statuses"] if item.reference_id == "q01")
    assert not item.mastered and item.consecutive_correct == 1
    save_answer(repo,"q01",True,22,"c")
    item = next(item for item in review_overview(repo)["statuses"] if item.reference_id == "q01")
    assert item.mastered and item.consecutive_correct == 2
    assert all(task.reference_id != "q01" for task in build_review_plan(repo))

def test_sqlite_uses_the_same_question_history_rule(tmp_path):
    repo=PracticeRepository(tmp_path / "review.db")
    save_answer(repo,"q01",False,20,"a"); save_answer(repo,"q01",True,21,"b"); save_answer(repo,"q01",True,22,"c")
    item=next(item for item in review_overview(repo)["statuses"] if item.reference_id=="q01")
    assert item.mastered and item.consecutive_correct == 2

def test_new_error_resets_consecutive_correct_count():
    repo=MemoryPracticeRepository()
    save_answer(repo,"q01",False,20,"a"); save_answer(repo,"q01",True,21,"b"); save_answer(repo,"q01",False,22,"c")
    item=next(item for item in review_overview(repo)["statuses"] if item.reference_id=="q01")
    assert not item.mastered and item.consecutive_correct == 0 and item.error_count == 2

def test_diagram_step_closes_after_two_clean_attempts():
    repo=MemoryPracticeRepository(); save_diagram(repo,True,20,"a"); save_diagram(repo,False,21,"b")
    item=next(item for item in review_overview(repo)["statuses"] if item.reference_id=="dol_roles_scope")
    assert not item.mastered and item.consecutive_correct == 1
    save_diagram(repo,False,22,"c")
    item=next(item for item in review_overview(repo)["statuses"] if item.reference_id=="dol_roles_scope")
    assert item.mastered

def test_fault_latest_two_correct_remove_target_without_changing_history():
    repo=MemoryPracticeRepository()
    for index, matched in enumerate((False,True,True),1):
        repo.save(PracticeRecord(f"p{index}",f"2026-08-{20+index:02d}T10:00:00+08:00","motor_dol_no_start","cause_control_power","cause_control_power" if matched else "inconsistent",matched,1,1,(),0))
    before=repo.summary("motor_dol_no_start")
    item=next(item for item in review_overview(repo)["statuses"] if item.reference_id=="cause_control_power")
    assert item.mastered and item.consecutive_correct == 2
    assert repo.summary("motor_dol_no_start") == before

def test_recent_seven_day_mastery_and_priority_order():
    repo=MemoryPracticeRepository()
    save_answer(repo,"q01",False,20,"a"); save_answer(repo,"q01",False,21,"b")
    save_answer(repo,"q02",False,22,"a")
    assert build_review_plan(repo)[0].reference_id == "q01"
    save_answer(repo,"q02",True,29,"b"); save_answer(repo,"q02",True,30,"c")
    overview=review_overview(repo, datetime(2026,8,31,tzinfo=TZ).date())
    assert overview["recently_mastered"] == 1

def test_no_history_has_no_fake_mastered_or_pending_items():
    overview=review_overview(MemoryPracticeRepository(), datetime(2026,8,31,tzinfo=TZ).date())
    assert not overview["statuses"] and not overview["pending"] and not overview["mastered"]
    assert overview["recently_mastered"] == 0

def test_ui_has_return_path_and_no_pyarrow_widgets():
    source=Path("app.py").read_text(encoding="utf-8")
    assert source.count("返回复习清单") >= 3
    assert "已消除薄弱点" in source and "最近7天掌握" in source
    assert "st.dataframe" not in source and "st.table" not in source
