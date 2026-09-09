from pathlib import Path
import random
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.quiz import questions_for_chapter, textbook_question_pool, OPTION_FEEDBACK
from dianzhentong.diagram_learning import DiagramTrainingSession
from dianzhentong.plc_lab import logic_output, hold_next
from dianzhentong.project_basics import DIAGRAM_FEEDBACK
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, make_diagram_record
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive

def test_counterexample_and_pool():
    assert logic_output('AND', True, False) is False
    assert logic_output('OR', True, False) is True
    assert hold_next(True, False, False, True) is True
    assert hold_next(True, True, True, True) is False
    assert len(questions_for_chapter('p2_unit_4')) == 8
    pool = textbook_question_pool(('p2_unit_4',), 'q107')
    assert len(pool) == 7 and 'q107' not in {q.id for q in pool}
    for n in (3,5):
        for seed in range(20):
            assert len({q.id for q in random.Random(seed).sample(pool,n)}) == n
    for q in pool:
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}

@pytest.mark.parametrize('mode', ['correct','wrong','uncertain'])
@pytest.mark.parametrize('memory', [False,True])
def test_project_training_history(tmp_path, mode, memory):
    repo = MemoryPracticeRepository() if memory else PracticeRepository(tmp_path/'study.db')
    session=DiagramTrainingSession('plc_project_check')
    for step in session.case['steps']:
        assert set(DIAGRAM_FEEDBACK[step['id']]) == set(step['options'])-{step['answer']}
        first=step['answer'] if mode=='correct' else '不确定' if mode=='uncertain' else step['options'][1]
        session.answer(first); session.answer(step['answer']); session.next_step()
        assert session.first_answers[step['id']] == first
    assert session.correct_steps == (3 if mode=='correct' else 0)
    repo.save_diagram_practice(make_diagram_record(session))
    repo.save_diagram_practice(make_diagram_record(session))
    target=MemoryPracticeRepository()
    archive=parse_archive(archive_json_bytes(repo))
    import_archive(target,archive,confirmed=True); import_archive(target,archive,confirmed=True)
    assert len(target.diagram_history('p2_unit_4')) == 1

def test_project_case_return_and_pretest(tmp_path,monkeypatch):
    monkeypatch.setenv('DIANZHENTONG_DB_PATH',str(tmp_path/'ui.db'))
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=20).run()
    next(b for b in app.button if b.label=='进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(6).run()
    assert any('题库总量 8 题 · 可用于独立测验 7 题' in c.value for c in app.caption)
    app.button(key='book_case_start_6').click().run()
    for _ in range(3):
        step=DiagramTrainingSession.from_dict(app.session_state['diagram_training']).current_step
        next(r for r in app.radio if r.label=='选择下一判断').set_value('不确定').run()
        next(b for b in app.button if b.label=='提交本步判断').click().run()
        next(r for r in app.radio if r.label=='选择下一判断').set_value(step['answer']).run()
        next(b for b in app.button if b.label=='提交本步判断').click().run()
        next(b for b in app.button if b.label=='进入下一步').click().run()
    app.run()
    next(b for b in app.button if b.label=='返回本教材单元').click().run()
    assert app.session_state['stage']==20 and app.session_state['selected_textbook_chapter']==6
    assert not app.exception
    app.button(key='book_pretest_start_6').click().run()
    assert len(app.session_state['quiz_state']['question_ids'])==3
    assert 'q107' not in app.session_state['quiz_state']['question_ids']
