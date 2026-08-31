from dianzhentong.diagram_learning import DiagramTrainingSession
from dianzhentong.engine import DiagnosticSession, KnowledgeBase
from dianzhentong.quiz import QuizAnswer, QUESTION_MAP, make_quiz_record
from dianzhentong.review_plan import build_review_plan
from dianzhentong.storage import MemoryPracticeRepository, make_diagram_record

def test_empty_history_gets_a_safe_starter_task():
    tasks = build_review_plan(MemoryPracticeRepository())
    assert len(tasks) == 1 and tasks[0].kind == "knowledge"
    assert sum(item.minutes for item in tasks) <= 10

def test_wrong_quiz_and_diagram_errors_become_review_tasks():
    repo = MemoryPracticeRepository()
    question = QUESTION_MAP["q01"]
    repo.save_quiz(make_quiz_record(question.chapter_id, (QuizAnswer(question.id, "错误", question.answer, False, False),)))
    training = DiagramTrainingSession("dol_roles")
    while not training.is_complete:
        step = training.current_step
        wrong = next(item for item in step["options"] if item != step["answer"])
        training.answer(wrong); training.answer(step["answer"]); training.next_step()
    repo.save_diagram_practice(make_diagram_record(training))
    tasks = build_review_plan(repo)
    assert {item.kind for item in tasks} == {"quiz", "diagram"}
    assert sum(item.minutes for item in tasks) <= 10

def test_plan_is_read_only_and_does_not_create_learning_records():
    repo = MemoryPracticeRepository()
    before = repo.export_snapshot()
    build_review_plan(repo)
    assert repo.export_snapshot() == before

def test_incorrect_fault_practice_becomes_targeted_task():
    repo = MemoryPracticeRepository()
    session = DiagnosticSession(KnowledgeBase("motor_dol_no_start"))
    session.start(True, scenario_id="cause_control_power")
    while not session.is_complete:
        session.answer("正常")
    repo.save(session.to_practice_record())
    task = next(item for item in build_review_plan(repo) if item.kind == "fault")
    assert task.experiment_id == "motor_dol_no_start"
    assert task.reference_id == "cause_control_power"

def test_app_exposes_review_plan_without_new_table_widget():
    source = __import__("pathlib").Path("app.py").read_text(encoding="utf-8")
    assert "我的10分钟复习清单" in source
    assert "build_review_plan(repository)" in source
    assert "st.dataframe" not in source and "st.table" not in source
