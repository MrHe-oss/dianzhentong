from pathlib import Path
import random
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.quiz import questions_for_chapter, textbook_question_pool, QUESTION_MAP, OPTION_FEEDBACK
from dianzhentong.diagram_learning import DiagramTrainingSession
from dianzhentong.tia_basics import DIAGRAM_FEEDBACK
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, make_diagram_record
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive

def test_independent_questions_and_feedback():
    assert len(questions_for_chapter('p2_unit_3')) == 8
    pool = textbook_question_pool(('p2_unit_3',), 'q103')
    assert len(pool) == 7 and 'q103' not in {q.id for q in pool}
    for n in (3, 5):
        for seed in range(30):
            assert len({q.id for q in random.Random(seed).sample(pool, n)}) == n
    for q in pool:
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}

@pytest.mark.parametrize('first', ['correct', 'wrong', 'uncertain'])
@pytest.mark.parametrize('memory', [False, True])
def test_training_scores_backup_and_dedup(tmp_path, first, memory):
    repo = MemoryPracticeRepository() if memory else PracticeRepository(tmp_path / 'study.db')
    session = DiagramTrainingSession('plc_tia_objects')
    assert [s['id'] for s in session.case['steps']] == ['plc_tia_container', 'plc_tia_device', 'plc_tia_logic']
    for step in session.case['steps']:
        assert set(DIAGRAM_FEEDBACK[step['id']]) == set(step['options']) - {step['answer']}
        choice = step['answer'] if first == 'correct' else '不确定' if first == 'uncertain' else step['options'][1]
        session.answer(choice)
        session.answer(step['answer'])
        assert session.first_answers[step['id']] == choice
        session.next_step()
    assert session.is_complete and session.correct_steps == (3 if first == 'correct' else 0)
    repo.save_diagram_practice(make_diagram_record(session))
    repo.save_diagram_practice(make_diagram_record(session))
    assert len(repo.diagram_history('p2_unit_3')) == 1
    target = MemoryPracticeRepository()
    archive = parse_archive(archive_json_bytes(repo))
    import_archive(target, archive, confirmed=True)
    import_archive(target, archive, confirmed=True)
    assert len(target.diagram_history('p2_unit_3')) == 1
    assert DiagramTrainingSession('plc_tia_objects').training_id != session.training_id

def test_textbook_training_returns_to_same_unit(tmp_path, monkeypatch):
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(tmp_path / 'ui.db'))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == '进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(5).run()
    app.button(key='tia_objects_practice').click().run()
    assert any('当前对象 · 工程项目' in m.value for m in app.markdown)
    for index in range(3):
        raw = app.session_state['diagram_training']
        step = DiagramTrainingSession.from_dict(raw).current_step
        next(r for r in app.radio if r.label == '选择下一判断').set_value('不确定').run()
        next(b for b in app.button if b.label == '提交本步判断').click().run()
        assert any('先辨认对象' in w.value for w in app.warning)
        next(r for r in app.radio if r.label == '选择下一判断').set_value(step['answer']).run()
        next(b for b in app.button if b.label == '提交本步判断').click().run()
        next(b for b in app.button if b.label == '进入下一步').click().run()
    app.run()
    next(b for b in app.button if b.label == '返回本教材单元').click().run()
    assert app.session_state['stage'] == 20
    assert app.session_state['selected_textbook_chapter'] == 5 and not app.exception
    app.button(key='book_pretest_start_5').click().run()
    assert len(app.session_state['quiz_state']['question_ids']) == 3
    assert 'q103' not in app.session_state['quiz_state']['question_ids']
