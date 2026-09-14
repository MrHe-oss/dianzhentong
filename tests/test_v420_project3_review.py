from dataclasses import asdict
from types import SimpleNamespace
from pathlib import Path
import random
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong import textbook_project as project
from dianzhentong.quiz import QuizAnswer, QUESTION_MAP, make_quiz_record
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository, ResilientPracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive, BackupValidationError
from dianzhentong.project3_review import example_steps
from dianzhentong.textbook_learning import calculate_unit_progress

PID = 'project_3'
CONFIG = project.project_config(PID)


def record(correct=6, pid=PID):
    questions = project.select_project_questions(random.Random(11), pid)
    answers = tuple(QuizAnswer(q.id, q.answer if i < correct else '不确定', q.answer, i < correct, i >= correct)
                    for i, q in enumerate(questions))
    return make_quiz_record(project.project_config(pid)['scope'], answers, project.MODE, quiz_id=pid+'-test')


def test_configuration_selection_and_legacy_defaults():
    assert project.UNITS == project.project_config()['units']
    assert project.SCOPE == project.project_config()['scope']
    assert project.CHAPTER_IDS == project.project_config()['chapters']
    for seed in range(100):
        for pid in project.PROJECT_IDS:
            ids = [q.id for q in project.select_project_questions(random.Random(seed), pid)]
            assert project.valid_project_questions(ids, pid)
            other = 'project_2' if pid == PID else PID
            assert not project.valid_project_questions(ids, other)
            excluded = {u['worked_example']['practice_question_id'] for _, u in project.project_config(pid)['units']}
            assert not excluded.intersection(ids)
    assert not project.valid_project_questions(ids, 'unknown')
    assert not project.valid_project_questions(ids[:-1], PID)
    assert not project.valid_project_questions([ids[0]] * 8, PID)
    with pytest.raises(ValueError): project.project_config('unknown')


@pytest.mark.parametrize('correct', [0, 5, 6, 8])
@pytest.mark.parametrize('backend', ['sqlite', 'memory', 'fallback'])
def test_storage_archives_scores_and_progress(tmp_path, correct, backend):
    repo = (PracticeRepository(tmp_path/'a.db') if backend == 'sqlite' else
            ResilientPracticeRepository(tmp_path) if backend == 'fallback' else MemoryPracticeRepository())
    old = record(6, 'project_2')
    repo.save_quiz(old)
    legacy = parse_archive(archive_json_bytes(repo))
    new = record(correct)
    assert new.passed == (correct >= 6)
    assert repo.save_quiz(new) and not repo.save_quiz(new)
    assert repo.quiz_answers(new.quiz_id) == [asdict(a) for a in new.answers]
    for _, unit in CONFIG['units']:
        assert calculate_unit_progress(unit['topic_ids'], set(), repo.quiz_history(unit['quiz_chapter_ids'][0])).completion == 0
    target = MemoryPracticeRepository()
    import_archive(target, legacy, confirmed=True)
    assert not target.quiz_history(CONFIG['scope'])
    archive = parse_archive(archive_json_bytes(repo))
    for _ in range(2): import_archive(target, archive, confirmed=True)
    assert len(target.quiz_history(CONFIG['scope'])) == 1
    assert len(target.quiz_history(project.SCOPE)) == 1
    assert target.quiz_answers(new.quiz_id) == repo.quiz_answers(new.quiz_id)
    assert '项目3综合学习报告' in project.report_text(repo.quiz_answers(new.quiz_id), PID)
    assert '回学知识点' in project.report_text(repo.quiz_answers(new.quiz_id), PID)
    raw = archive_json_bytes(repo).decode().replace(CONFIG['scope'], project.SCOPE)
    with pytest.raises(BackupValidationError): parse_archive(raw.encode())


def test_recommendations_and_examples():
    states = {i: SimpleNamespace(completion=0) for i, _ in CONFIG['units']}
    assert project.recommended_unit(states, project_id=PID) == 7
    states[7].completion = 1
    assert project.recommended_unit(states, project_id=PID) == 8
    answers = [asdict(a) for a in record(0).answers]
    assert project.recommended_unit(states, answers, PID) == 7  # tie, textbook order
    assert project.recommended_unit(states, [asdict(a) for a in record(6).answers], PID) == 10
    for state in states.values(): state.completion = 1
    assert project.recommended_unit(states, project_id=PID) is None
    assert project.recommended_unit(states, [asdict(a) for a in record(8).answers], PID) is None
    steps = example_steps()
    assert len(steps) == 5
    assert 'Y=假' in steps[0]['answer']
    assert '点动假、长动真' in steps[1]['answer']
    assert '下一状态：停止' in steps[2]['answer']
    assert '点动假、长动假' in steps[3]['answer']
    assert '转换等待' in steps[4]['answer']


@pytest.mark.parametrize('correct', [5, 6])
def test_project3_ui_history_return_and_first_answer(tmp_path, monkeypatch, correct):
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(tmp_path/'ui.db'))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=30).run()
    def button(label): return next(b for b in app.button if b.label == label)
    button('进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(7).run()
    app.button(key='project3_overview').click().run()
    assert not app.exception
    app.button(key='project3_example_unit_4').click().run()
    assert app.session_state['selected_textbook_chapter'] == 10
    app.button(key='project3_overview').click().run()
    button('开始项目3综合测验').click().run()
    initial_id = app.session_state['quiz_state']['quiz_id']
    ids = app.session_state['quiz_state']['question_ids']
    for i, qid in enumerate(ids):
        q = QUESTION_MAP[qid]
        selected = q.answer if i < correct else ('不确定' if i == 7 else next(o for o in q.options if o != q.answer))
        next(r for r in app.radio if r.label == '请选择一个答案').set_value(selected).run()
        button('提交答案').click().run()
        first = list(app.session_state['quiz_state']['answers'])
        app.run()
        assert app.session_state['quiz_state']['answers'] == first
        if i == 7:
            app.button(key='quiz_relearn_topic').click().run()
            assert app.session_state['stage'] == 24
            app.button(key='return_to_quiz').click().run()
            assert app.session_state['quiz_state']['answers'] == first
        button('查看成绩' if i == 7 else '下一题').click().run()
    assert not app.exception
    assert app.session_state['quiz_state']['record']['passed'] == (correct >= 6)
    app.button(key='project_report_relearn').click().run()
    app.button(key='return_to_quiz').click().run()
    app.run()
    repo = PracticeRepository(tmp_path/'ui.db')
    assert len(repo.quiz_history(CONFIG['scope'])) == 1
    button('返回项目3复习').click().run()
    button('查看最近综合报告').click().run()
    app.button(key=f'quiz_card_{ids[7]}').click().run()
    app.button(key='return_to_quiz').click().run()
    assert app.session_state['quiz_state']['quiz_id'] == initial_id
    assert len(repo.quiz_history(CONFIG['scope'])) == 1
    button('再测一次').click().run()
    assert app.session_state['quiz_state']['quiz_id'] != initial_id
    assert app.session_state['quiz_state']['chapter_id'] == CONFIG['scope']
    button('退出测验').click().run()
    assert app.session_state['stage'] == 27 and not app.exception


def test_invalid_project_session_recovers(tmp_path, monkeypatch):
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(tmp_path/'invalid.db'))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=30).run()
    app.session_state['stage'] = 10
    app.session_state['quiz_state'] = {'mode': project.MODE, 'chapter_id': CONFIG['scope'],
                                      'question_ids': ['q91'] * 8, 'answers': [], 'index': 0}
    app.run()
    next(b for b in app.button if b.label == '返回教材入口').click().run()
    assert app.session_state['stage'] == 20 and not app.exception
    assert 'quiz_state' not in app.session_state
