from itertools import product
from pathlib import Path
import random

import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.bit_logic import TOPICS, evaluate_request
from dianzhentong.engine import DEFAULT_EXPERIMENT_ID
from dianzhentong.content_loader import load_textbook_content
from dianzhentong.curriculum_catalog import BOOK_EDITION_MAPPINGS
from dianzhentong.quiz import QUESTIONS, QUESTION_MAP, OPTION_FEEDBACK, QuizAnswer, make_quiz_record, textbook_question_pool
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, ResilientPracticeRepository, make_learning_activity
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.textbook_learning import calculate_unit_progress
from dianzhentong.textbook_project import select_project_questions, valid_project_questions

BOOK = 'electrical_control_plc_s71200_tong'
UNIT = 'p3_unit_1'


def test_content_pool_sources_and_project2_unchanged():
    content = load_textbook_content(BOOK, 'project_3')
    assert len(content['project']['units']) == 1
    unit = content['project']['units'][0]
    assert unit['id'] == UNIT and tuple(unit['topic_ids']) == TOPICS
    assert not unit['case_ids'] and not unit['experiment_ids']
    assert len(BOOK_EDITION_MAPPINGS[BOOK]['chapters']) == 8
    assert BOOK_EDITION_MAPPINGS[BOOK]['chapters'][7]['quiz_chapter_ids'] == (UNIT,)
    assert len([q for q in QUESTIONS if q.chapter_id == UNIT]) == 8
    pool = textbook_question_pool((UNIT,), 'bit_example')
    assert len(pool) == 7 and 'bit_example' not in {q.id for q in pool}
    for q in [q for q in QUESTIONS if q.chapter_id == UNIT]:
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}
    for topic in TOPICS:
        assert provenance_for_card(topic)['status'] == STATUS_PARTIAL
    for seed in range(30):
        for count in (3, 5):
            assert len({q.id for q in random.Random(seed).sample(pool, count)}) == count
        selected = select_project_questions(random.Random(seed))
        assert valid_project_questions([q.id for q in selected])
        assert all(q.chapter_id != UNIT for q in selected)
    for topic in unit['topics']:
        for formula in topic['formulas']:
            assert '\\\\' not in formula['expression']


@pytest.mark.parametrize('a,b,t', list(product((False, True), repeat=3)))
def test_all_combinations_and_no_memory(a, b, t):
    values = evaluate_request(a, b, t)
    assert values == {'request': a or b, 'permitted': not t, 'result': (a or b) and not t}
    evaluate_request(True, True, False)
    assert evaluate_request(a, b, t) == values
    assert evaluate_request(False, False, False)['result'] is False


@pytest.mark.parametrize('backend', ['sqlite', 'memory', 'fallback'])
def test_progress_backup_and_dedup(tmp_path, backend):
    repo = PracticeRepository(tmp_path/'study.db') if backend == 'sqlite' else MemoryPracticeRepository() if backend == 'memory' else ResilientPracticeRepository(tmp_path)
    pool = textbook_question_pool((UNIT,), 'bit_example')[:5]
    answers = tuple(QuizAnswer(q.id, q.answer, q.answer, True, False) for q in pool)
    result = make_quiz_record(UNIT, answers, 'textbook_unit_assessment', quiz_id='bit-test')
    assert repo.save_quiz(result) and not repo.save_quiz(result)
    assert calculate_unit_progress(TOPICS, set(), repo.quiz_history(UNIT)).completion == .4
    example = QUESTION_MAP['bit_example']
    repo.save_quiz(make_quiz_record(UNIT, (QuizAnswer(example.id, example.answer, example.answer, True, False),), 'textbook_example', quiz_id='bit-example'))
    for topic in TOPICS:
        repo.save_activity(make_learning_activity(DEFAULT_EXPERIMENT_ID, 'knowledge_card', topic))
    state = calculate_unit_progress(TOPICS, set(TOPICS), repo.quiz_history(UNIT))
    assert state.completion == 1 and state.status == '已完成'
    archive = parse_archive(archive_json_bytes(repo))
    target = MemoryPracticeRepository()
    import_archive(target, archive, confirmed=True); import_archive(target, archive, confirmed=True)
    assert len(target.quiz_history(UNIT)) == 2
    assert set(TOPICS) <= target.learned_cards(DEFAULT_EXPERIMENT_ID)
    old_repo = MemoryPracticeRepository()
    old = QUESTION_MAP['q91']
    old_repo.save_quiz(make_quiz_record(old.chapter_id, (QuizAnswer(old.id, old.answer, old.answer, True, False),), quiz_id='old'))
    old_archive = parse_archive(archive_json_bytes(old_repo))
    import_archive(target, old_archive, confirmed=True)
    assert len(target.quiz_history(old.chapter_id)) == 1
    assert len(target.quiz_history(UNIT)) == 2


@pytest.mark.parametrize('answer_kind', ['correct', 'wrong', 'uncertain'])
def test_full_unit_quiz_relearning(tmp_path, monkeypatch, answer_kind):
    db = tmp_path/'ui.db'
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(db))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == '进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(7).run()
    assert not app.exception
    assert any('题库总量 8 题 · 可用于独立测验 7 题' in c.value for c in app.caption)
    repo = PracticeRepository(db)
    before = repo.export_snapshot()
    app.checkbox(key='bit_unit_a').check().run()
    assert any('当前结果 Y：真' in x.value for x in app.success)
    app.checkbox(key='bit_unit_t').check().run()
    assert any('当前结果 Y：假' in x.value for x in app.info)
    assert repo.export_snapshot() == before
    app.button(key='book_pretest_start_7').click().run()
    assert len(app.session_state['quiz_state']['question_ids']) == 3
    for i in range(3):
        next(r for r in app.radio if r.label == '请选择一个答案').set_value('不确定').run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        next(b for b in app.button if b.label == ('查看成绩' if i == 2 else '下一题')).click().run()
    next(b for b in app.button if b.label == '返回教材单元').click().run()
    app.button(key='book_quiz_start_7').click().run()
    ids = app.session_state['quiz_state']['question_ids']
    assert len(ids) == 5 and 'bit_example' not in ids
    for i, qid in enumerate(ids):
        q = QUESTION_MAP[qid]
        value = q.answer if answer_kind == 'correct' else q.options[1] if answer_kind == 'wrong' else '不确定'
        app.radio(key=f'quiz_choice_{qid}_{i}').set_value(value).run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        first = list(app.session_state['quiz_state']['answers'])
        if i == 0:
            app.button(key='quiz_relearn_topic').click().run()
            assert app.session_state['textbook_context']['chapter_index'] == 7
            app.button(key='return_to_quiz').click().run()
            assert app.session_state['quiz_state']['answers'] == first
        next(b for b in app.button if b.label == ('查看成绩' if i == 4 else '下一题')).click().run()
    assert app.session_state['quiz_state']['record']['correct_count'] == (5 if answer_kind == 'correct' else 0)
    if answer_kind != 'correct':
        app.button(key=f'quiz_card_{ids[0]}').click().run()
        app.button(key='return_to_quiz').click().run()
    app.run()
    assert not app.exception and len(repo.quiz_history(UNIT)) == 2
    parse_archive(archive_json_bytes(repo))
    next(b for b in app.button if b.label == '返回教材单元').click().run()
    assert app.session_state['selected_textbook_chapter'] == 7
    previous_id = app.session_state['quiz_result_id']
    app.button(key='book_quiz_start_7').click().run()
    assert app.session_state['quiz_state']['quiz_id'] != previous_id
    assert not app.session_state['quiz_state']['answers']
