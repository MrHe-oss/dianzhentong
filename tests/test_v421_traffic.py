from itertools import product
from pathlib import Path
import random
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.traffic_logic import STAGES, TOPICS, traffic_next, QUESTION_SPECS
from dianzhentong.quiz import QUESTION_MAP, OPTION_FEEDBACK, textbook_question_pool, QuizAnswer, make_quiz_record
from dianzhentong.content_loader import load_textbook_content
from dianzhentong.textbook_project import project_config, select_project_questions, valid_project_questions
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, ResilientPracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.textbook_learning import calculate_unit_progress
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL

UNIT = 'p3_unit_5'
BOOK = 'electrical_control_plc_s71200_tong'


def test_all_112_combinations_and_cycle():
    cycle = ('a_green','a_yellow','all_red_ab','b_green','b_yellow','all_red_ba')
    for stage in STAGES:
        for allow, start, stop, end in product((False, True), repeat=4):
            expected = 'stopped' if stop or not allow else (
                ('a_green' if start else 'stopped') if stage == 'stopped' else
                cycle[(cycle.index(stage)+1)%6] if end else stage)
            r = traffic_next(stage, allow, start, stop, end)
            assert r['stage'] == expected and r['reason']
            assert not (r['a'] == r['b'] == '绿')
            assert (r['a'], r['b']) == STAGES[expected][1:]
    stage = traffic_next('stopped', True, True, False, True)['stage']
    for expected in (*cycle[1:], *cycle, 'a_green'):
        assert traffic_next(stage, True, False, False, False)['stage'] == stage
        stage = traffic_next(stage, True, False, False, True)['stage']
        assert stage == expected
    assert traffic_next(stage, True, True, True, True)['stage'] == 'stopped'
    assert traffic_next('stopped', True, False, False, True)['stage'] == 'stopped'
    with pytest.raises(ValueError): traffic_next('bad', True, False, False, False)
    with pytest.raises(ValueError): traffic_next('stopped', 1, False, False, False)


def test_content_pool_and_frozen_project_scope():
    unit = load_textbook_content(BOOK, 'project_3')['project']['units'][4]
    assert unit['id'] == UNIT and tuple(unit['topic_ids']) == TOPICS
    assert len(unit['topics']) == 3 and len(QUESTION_SPECS) == 8
    assert unit['worked_example']['practice_answer'] == QUESTION_MAP['traffic_example'].answer
    pool = textbook_question_pool((UNIT,), 'traffic_example')
    assert len(pool) == 7 and 'traffic_example' not in {q.id for q in pool}
    for seed in range(50):
        for n in (3,5): assert len({q.id for q in random.Random(seed).sample(pool,n)}) == n
        for pid in ('project_2','project_3'):
            qs = select_project_questions(random.Random(seed), pid)
            assert valid_project_questions([q.id for q in qs], pid)
            assert len(qs) == 8 and all(q.chapter_id != UNIT for q in qs)
            assert len(project_config(pid)['units']) == 4
    for row in QUESTION_SPECS:
        q = QUESTION_MAP[row['id']]
        assert len(q.options) == len(set(q.options))
        assert set(OPTION_FEEDBACK[q.id]) == set(q.options)-{q.answer}
        assert provenance_for_card(row['card'])['status'] == STATUS_PARTIAL


@pytest.mark.parametrize('backend', ['sqlite','memory','fallback'])
def test_archive_and_old_progress(tmp_path, backend):
    repo = PracticeRepository(tmp_path/'a.db') if backend == 'sqlite' else MemoryPracticeRepository() if backend == 'memory' else ResilientPracticeRepository(tmp_path)
    questions = select_project_questions(random.Random(1), 'project_3')
    old = make_quiz_record(project_config('project_3')['scope'], tuple(QuizAnswer(q.id,q.answer,q.answer,True,False) for q in questions), 'textbook_project_assessment', quiz_id='old-project')
    repo.save_quiz(old)
    legacy = parse_archive(archive_json_bytes(repo))
    assert calculate_unit_progress(TOPICS,set(),repo.quiz_history(UNIT)).completion == 0
    qs = textbook_question_pool((UNIT,), 'traffic_example')[:5]
    record = make_quiz_record(UNIT,tuple(QuizAnswer(q.id,q.answer,q.answer,True,False) for q in qs),'textbook_unit_assessment',quiz_id='traffic-new')
    assert repo.save_quiz(record) and not repo.save_quiz(record)
    target = MemoryPracticeRepository()
    import_archive(target,legacy,confirmed=True)
    assert not target.quiz_history(UNIT)
    archive = parse_archive(archive_json_bytes(repo))
    for _ in range(2): import_archive(target,archive,confirmed=True)
    assert len(target.quiz_history(UNIT)) == 1
    assert len(target.quiz_history(old.chapter_id)) == 1


@pytest.mark.parametrize('kind', ['correct','wrong','uncertain'])
def test_ui_full_flow(tmp_path, monkeypatch, kind):
    db=tmp_path/'ui.db'
    monkeypatch.setenv('DIANZHENTONG_DB_PATH',str(db))
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    def button(label): return next(b for b in app.button if b.label == label)
    button('进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(11).run()
    repo=PracticeRepository(db); before=repo.export_snapshot()
    app.checkbox(key='traffic_unit_start').check().run()
    assert app.session_state['traffic_unit_stage'] == 'stopped'
    app.checkbox(key='traffic_unit_end').check().run()
    for stage in ('a_green','a_yellow','all_red_ab','b_green','b_yellow','all_red_ba','a_green'):
        app.button(key='traffic_unit_calculate').click().run()
        assert app.session_state['traffic_unit_stage'] == stage
    app.button(key='traffic_unit_reset').click().run()
    assert app.session_state['traffic_unit_stage'] == 'stopped'
    assert 'traffic_unit_evidence' not in app.session_state
    assert repo.export_snapshot() == before
    for label,count in [('开始学前小测',3),('开始学后评测',5)]:
        button(label).click().run()
        ids=app.session_state['quiz_state']['question_ids']
        assert len(ids)==count and 'traffic_example' not in ids
        for i,qid in enumerate(ids):
            q=QUESTION_MAP[qid]
            answer=q.answer if kind=='correct' else '不确定' if kind=='uncertain' else next(o for o in q.options if o!=q.answer)
            next(r for r in app.radio if r.label=='请选择一个答案').set_value(answer).run()
            button('提交答案').click().run()
            first=list(app.session_state['quiz_state']['answers'])
            app.run()
            if i==0:
                app.button(key='quiz_relearn_topic').click().run()
                app.button(key='return_to_quiz').click().run()
            assert app.session_state['quiz_state']['answers']==first
            button('查看成绩' if i==count-1 else '下一题').click().run()
        app.run()
        assert app.session_state['quiz_state']['record']['correct_count']==(count if kind=='correct' else 0)
        if kind!='correct':
            app.button(key=f'quiz_card_{ids[0]}').click().run()
            app.button(key='return_to_quiz').click().run()
        button('返回教材单元').click().run()
        assert app.session_state['selected_textbook_chapter']==11 and not app.exception
    assert len(repo.quiz_history(UNIT))==2
    parse_archive(archive_json_bytes(repo))
