from itertools import product
from pathlib import Path
import random

import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.direction_logic import TOPICS, STATES, direction_next, QUESTION_SPECS
from dianzhentong.engine import DEFAULT_EXPERIMENT_ID
from dianzhentong.content_loader import load_textbook_content
from dianzhentong.quiz import QUESTION_MAP, OPTION_FEEDBACK, textbook_question_pool, QuizAnswer, make_quiz_record
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, ResilientPracticeRepository, make_learning_activity
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.textbook_learning import calculate_unit_progress
from dianzhentong.textbook_project import select_project_questions

BOOK, UNIT = 'electrical_control_plc_s71200_tong', 'p3_unit_2'


def test_exhaustive_transitions():
    for state, inputs in product(STATES, product((False, True), repeat=4)):
        allow, stop, forward, reverse = inputs
        expected = '停止' if not allow or stop or (forward and reverse) else state if state != '停止' else '正向' if forward else '反向' if reverse else '停止'
        result = direction_next(state, *inputs)
        assert result['state'] == expected
        assert not (result['forward'] and result['reverse'])
        assert result['reason']
    with pytest.raises(ValueError):
        direction_next('invalid', True, False, False, False)
    with pytest.raises(ValueError):
        direction_next('停止', 'false', False, False, False)


def test_reverse_requires_stopped_state():
    for initial, request, target in [('正向', (False, True), '反向'), ('反向', (True, False), '正向')]:
        assert direction_next(initial, True, False, *request)['state'] == initial
        stopped = direction_next(initial, True, True, *request)['state']
        assert stopped == '停止'
        assert direction_next(stopped, True, False, *request)['state'] == target


def test_content_and_independent_pool():
    unit = load_textbook_content(BOOK, 'project_3')['project']['units'][1]
    assert unit['id'] == UNIT and tuple(unit['topic_ids']) == TOPICS
    assert not unit['case_ids'] and not unit['experiment_ids']
    assert len(unit['topics']) == 3 and len(QUESTION_SPECS) == 8
    pool = textbook_question_pool((UNIT,), 'direction_example')
    assert len(pool) == 7 and 'direction_example' not in {q.id for q in pool}
    for seed in range(30):
        for count in (3, 5):
            assert len({q.id for q in random.Random(seed).sample(pool, count)}) == count
        assert all(q.chapter_id != UNIT for q in select_project_questions(random.Random(seed)))
    for row in QUESTION_SPECS:
        q = QUESTION_MAP[row['id']]
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}
        assert len(q.options) == len(set(q.options))
        assert provenance_for_card(row['card'])['status'] == STATUS_PARTIAL
    assert unit['worked_example']['practice_answer'] == QUESTION_MAP['direction_example'].answer


@pytest.mark.parametrize('backend', ['sqlite', 'memory', 'fallback'])
def test_archive_progress_and_no_old_record_changes(tmp_path, backend):
    repo = PracticeRepository(tmp_path/'study.db') if backend == 'sqlite' else MemoryPracticeRepository() if backend == 'memory' else ResilientPracticeRepository(tmp_path)
    old = QUESTION_MAP['q91']
    repo.save_quiz(make_quiz_record(old.chapter_id, (QuizAnswer(old.id, old.answer, old.answer, True, False),), quiz_id='old-record'))
    before = list(repo.quiz_history(old.chapter_id))
    assert calculate_unit_progress(TOPICS, set(), repo.quiz_history(UNIT)).completion == 0
    for topic in TOPICS:
        repo.save_activity(make_learning_activity(DEFAULT_EXPERIMENT_ID, 'knowledge_card', topic))
    pool = textbook_question_pool((UNIT,), 'direction_example')[:5]
    record = make_quiz_record(UNIT, tuple(QuizAnswer(q.id, q.answer, q.answer, True, False) for q in pool), 'textbook_unit_assessment', quiz_id='new-post')
    assert repo.save_quiz(record) and not repo.save_quiz(record)
    q = QUESTION_MAP['direction_example']
    repo.save_quiz(make_quiz_record(UNIT, (QuizAnswer(q.id, q.answer, q.answer, True, False),), 'textbook_example', quiz_id='new-example'))
    assert calculate_unit_progress(TOPICS, set(TOPICS), repo.quiz_history(UNIT)).completion == 1
    assert repo.quiz_history(old.chapter_id) == before
    target = MemoryPracticeRepository()
    archive = parse_archive(archive_json_bytes(repo))
    import_archive(target, archive, confirmed=True)
    import_archive(target, archive, confirmed=True)
    assert len(target.quiz_history(UNIT)) == 2
    assert target.quiz_history(old.chapter_id) == before
    assert set(TOPICS) <= target.learned_cards(DEFAULT_EXPERIMENT_ID)


@pytest.mark.parametrize('answer_kind', ['correct', 'wrong', 'uncertain'])
def test_ui_unit_complete_flow(tmp_path, monkeypatch, answer_kind):
    db = tmp_path/'ui.db'
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(db))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == '进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(8).run()
    assert not app.exception
    repo = PracticeRepository(db)
    before = repo.export_snapshot()
    app.checkbox(key='direction_unit_forward').check().run()
    assert app.session_state['direction_unit_state'] == '停止'
    app.button(key='direction_unit_calculate').click().run()
    assert app.session_state['direction_unit_state'] == '正向'
    app.checkbox(key='direction_unit_forward').uncheck().run()
    app.checkbox(key='direction_unit_reverse').check().run()
    app.button(key='direction_unit_calculate').click().run()
    assert app.session_state['direction_unit_state'] == '正向'
    app.checkbox(key='direction_unit_stop').check().run()
    app.button(key='direction_unit_calculate').click().run()
    assert app.session_state['direction_unit_state'] == '停止'
    app.checkbox(key='direction_unit_stop').uncheck().run()
    app.button(key='direction_unit_calculate').click().run()
    assert app.session_state['direction_unit_state'] == '反向'
    app.button(key='direction_unit_reset').click().run()
    assert app.session_state['direction_unit_state'] == '停止'
    assert 'direction_unit_evidence' not in app.session_state
    assert repo.export_snapshot() == before
    app.button(key='book_pretest_start_8').click().run()
    assert len(app.session_state['quiz_state']['question_ids']) == 3
    for i in range(3):
        next(r for r in app.radio if r.label == '请选择一个答案').set_value('不确定').run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        next(b for b in app.button if b.label == ('查看成绩' if i == 2 else '下一题')).click().run()
    next(b for b in app.button if b.label == '返回教材单元').click().run()
    app.button(key='book_quiz_start_8').click().run()
    ids = app.session_state['quiz_state']['question_ids']
    assert len(ids) == 5 and 'direction_example' not in ids
    for i, qid in enumerate(ids):
        q = QUESTION_MAP[qid]
        value = q.answer if answer_kind == 'correct' else q.options[1] if answer_kind == 'wrong' else '不确定'
        app.radio(key=f'quiz_choice_{qid}_{i}').set_value(value).run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        first = list(app.session_state['quiz_state']['answers'])
        if i == 0:
            app.run()
            assert app.session_state['quiz_state']['answers'] == first
            app.button(key='quiz_relearn_topic').click().run()
            assert app.session_state['textbook_context']['chapter_index'] == 8
            app.button(key='return_to_quiz').click().run()
            assert app.session_state['quiz_state']['answers'] == first
        next(b for b in app.button if b.label == ('查看成绩' if i == 4 else '下一题')).click().run()
    assert app.session_state['quiz_state']['record']['correct_count'] == (5 if answer_kind == 'correct' else 0)
    if answer_kind != 'correct':
        app.button(key=f'quiz_card_{ids[0]}').click().run()
        app.button(key='return_to_quiz').click().run()
    app.run()
    assert not app.exception and len(repo.quiz_history(UNIT)) == 2
    next(b for b in app.button if b.label == '返回教材单元').click().run()
    assert app.session_state['selected_textbook_chapter'] == 8
    old_id = app.session_state['quiz_result_id']
    app.button(key='book_quiz_start_8').click().run()
    assert app.session_state['quiz_state']['quiz_id'] != old_id
    assert not app.session_state['quiz_state']['answers']
