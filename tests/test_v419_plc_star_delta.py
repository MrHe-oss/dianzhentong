from itertools import product
from pathlib import Path
import random

import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.plc_star_delta import TOPICS, STAGE_IDS, star_delta_next, QUESTION_SPECS
from dianzhentong.star_delta_stages import STAR_DELTA_STAGES, stage_by_id, role_is_active
from dianzhentong.engine import DEFAULT_EXPERIMENT_ID
from dianzhentong.content_loader import load_textbook_content
from dianzhentong.quiz import QUESTION_MAP, OPTION_FEEDBACK, textbook_question_pool, QuizAnswer, make_quiz_record
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, ResilientPracticeRepository, make_learning_activity
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.textbook_learning import calculate_unit_progress
from dianzhentong.textbook_project import select_project_questions

BOOK, UNIT = 'electrical_control_plc_s71200_tong', 'p3_unit_4'


def test_exhaustive_transitions():
    for stage in STAGE_IDS:
        for allow, start, stop, end, convert in product((False, True), repeat=5):
            expected = 'stopped' if stop or not allow else (
                'star_start' if stage == 'stopped' and start else
                'transition' if stage == 'star_start' and end else
                'delta_run' if stage == 'transition' and convert else stage)
            result = star_delta_next(stage, allow, start, stop, end, convert)
            assert result['stage'] == expected and result['reason']
            active = [role_is_active(r) for r in stage_by_id(result['stage'])['roles']]
            assert not (active[1] and active[2])
    with pytest.raises(ValueError):
        star_delta_next('bad', True, True, False, False, False)
    with pytest.raises(ValueError):
        star_delta_next('stopped', 'false', True, False, False, False)


def test_sequence_and_shared_legacy_roles():
    from dianzhentong.star_delta_learning import STAR_DELTA_STAGES as old_stages, stage_by_id as old_lookup
    assert old_stages is STAR_DELTA_STAGES and old_lookup is stage_by_id
    assert [[role_is_active(r) for r in x['roles']] for x in STAR_DELTA_STAGES] == [
        [False, False, False], [True, True, False], [True, False, False], [True, False, True]]
    stage = 'stopped'
    for inputs, expected in [
        ((True, True, False, True, True), 'star_start'),
        ((True, False, False, False, True), 'star_start'),
        ((True, False, False, True, True), 'transition'),
        ((True, False, False, True, False), 'transition'),
        ((True, False, False, False, True), 'delta_run'),
        ((True, False, False, False, False), 'delta_run'),
        ((True, True, True, True, True), 'stopped'),
        ((True, False, False, True, True), 'stopped')]:
        stage = star_delta_next(stage, *inputs)['stage']
        assert stage == expected


def test_content_and_independent_pool():
    unit = load_textbook_content(BOOK, 'project_3')['project']['units'][3]
    assert unit['id'] == UNIT and tuple(unit['topic_ids']) == TOPICS
    assert not unit['case_ids'] and not unit['experiment_ids']
    assert len(unit['topics']) == 3 and len(QUESTION_SPECS) == 8
    pool = textbook_question_pool((UNIT,), 'plc_sd_example')
    assert len(pool) == 7 and 'plc_sd_example' not in {q.id for q in pool}
    for seed in range(30):
        for count in (3, 5):
            assert len({q.id for q in random.Random(seed).sample(pool, count)}) == count
        assert all(q.chapter_id != UNIT for q in select_project_questions(random.Random(seed)))
    for row in QUESTION_SPECS:
        q = QUESTION_MAP[row['id']]
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options) - {q.answer}
        assert len(q.options) == len(set(q.options))
        assert provenance_for_card(row['card'])['status'] == STATUS_PARTIAL
    assert unit['worked_example']['practice_answer'] == QUESTION_MAP['plc_sd_example'].answer


@pytest.mark.parametrize('backend', ['sqlite', 'memory', 'fallback'])
def test_archive_progress_and_no_old_record_changes(tmp_path, backend):
    repo = PracticeRepository(tmp_path/'study.db') if backend == 'sqlite' else MemoryPracticeRepository() if backend == 'memory' else ResilientPracticeRepository(tmp_path)
    old = QUESTION_MAP['q91']
    repo.save_quiz(make_quiz_record(old.chapter_id, (QuizAnswer(old.id, old.answer, old.answer, True, False),), quiz_id='old-record'))
    before = list(repo.quiz_history(old.chapter_id))
    assert calculate_unit_progress(TOPICS, set(), repo.quiz_history(UNIT)).completion == 0
    for topic in TOPICS:
        repo.save_activity(make_learning_activity(DEFAULT_EXPERIMENT_ID, 'knowledge_card', topic))
    pool = textbook_question_pool((UNIT,), 'plc_sd_example')[:5]
    record = make_quiz_record(UNIT, tuple(QuizAnswer(q.id, q.answer, q.answer, True, False) for q in pool), 'textbook_unit_assessment', quiz_id='new-post')
    assert repo.save_quiz(record) and not repo.save_quiz(record)
    q = QUESTION_MAP['plc_sd_example']
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
    app.selectbox(key='selected_textbook_chapter').set_value(10).run()
    assert not app.exception
    repo = PracticeRepository(db)
    before = repo.export_snapshot()
    assert app.session_state['plc_sd_unit_stage'] == 'stopped'
    app.checkbox(key='plc_sd_unit_start').check().run()
    assert app.session_state['plc_sd_unit_stage'] == 'stopped'
    for start, stop, end, convert, expected in [
        (True, False, True, True, 'star_start'),
        (False, False, True, True, 'transition'),
        (False, False, True, False, 'transition'),
        (False, False, False, True, 'delta_run'),
        (False, True, False, False, 'stopped'),
        (False, False, False, False, 'stopped')]:
        for key, value in [('start', start), ('stop', stop), ('end', end), ('transition', convert)]:
            app.checkbox(key=f'plc_sd_unit_{key}').set_value(value).run()
        app.button(key='plc_sd_unit_calculate').click().run()
        assert app.session_state['plc_sd_unit_stage'] == expected
    app.button(key='plc_sd_unit_reset').click().run()
    assert app.session_state['plc_sd_unit_stage'] == 'stopped'
    assert 'plc_sd_unit_evidence' not in app.session_state
    app.session_state['plc_sd_unit_stage'] = 'invalid-old-state'
    app.run()
    assert app.session_state['plc_sd_unit_stage'] == 'stopped'
    assert repo.export_snapshot() == before
    app.button(key='book_pretest_start_10').click().run()
    assert len(app.session_state['quiz_state']['question_ids']) == 3
    for i in range(3):
        next(r for r in app.radio if r.label == '请选择一个答案').set_value('不确定').run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        next(b for b in app.button if b.label == ('查看成绩' if i == 2 else '下一题')).click().run()
    next(b for b in app.button if b.label == '返回教材单元').click().run()
    app.button(key='book_quiz_start_10').click().run()
    ids = app.session_state['quiz_state']['question_ids']
    assert len(ids) == 5 and 'plc_sd_example' not in ids
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
            assert app.session_state['textbook_context']['chapter_index'] == 10
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
    assert app.session_state['selected_textbook_chapter'] == 10
    old_id = app.session_state['quiz_result_id']
    app.button(key='book_quiz_start_10').click().run()
    assert app.session_state['quiz_state']['quiz_id'] != old_id
    assert not app.session_state['quiz_state']['answers']
