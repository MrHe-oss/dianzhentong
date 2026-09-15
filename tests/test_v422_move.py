from itertools import product
from pathlib import Path
import random
import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong.move_logic import move_once, TOPICS, QUESTION_SPECS, MIN_VALUE, MAX_VALUE
from dianzhentong.content_loader import load_textbook_content
from dianzhentong.quiz import QUESTION_MAP, OPTION_FEEDBACK, textbook_question_pool, QuizAnswer, make_quiz_record
from dianzhentong.textbook_project import select_project_questions, valid_project_questions
from dianzhentong.storage import PracticeRepository, MemoryPracticeRepository, ResilientPracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive
from dianzhentong.textbook_learning import calculate_unit_progress
from dianzhentong.provenance import provenance_for_card, STATUS_PARTIAL

BOOK, UNIT = 'electrical_control_plc_s71200_tong', 'p4_unit_1'


def test_copy_rules_and_repeated_execution():
    for source,target,enabled in product((MIN_VALUE,-1,0,1,MAX_VALUE),(-10,0,10),(False,True)):
        result=move_once(source,target,enabled)
        assert result['source']==source and result['target']==(source if enabled else target)
        assert result['executed'] is enabled and result['reason']
    first=move_once(5,2,True)
    assert move_once(9,first['target'],False)['target']==5
    assert move_once(9,first['target'],True)['target']==9
    assert move_once(0,9,True)['target']==0


@pytest.mark.parametrize('source,target,enabled', [(True,1,True),(1,False,True),(1.2,0,True),('1',0,True),(1000,0,False),(0,-1000,True),(1,2,1)])
def test_reject_outside_teaching_model(source,target,enabled):
    with pytest.raises(ValueError): move_once(source,target,enabled)


def test_content_and_pool():
    content=load_textbook_content(BOOK,'project_4')
    assert len(content['project']['units'])==1
    unit=content['project']['units'][0]
    assert unit['id']==UNIT and tuple(unit['topic_ids'])==TOPICS and len(unit['topics'])==3
    assert len(QUESTION_SPECS)==8 and unit['worked_example']['practice_answer']==QUESTION_MAP['move_example'].answer
    pool=textbook_question_pool((UNIT,),'move_example')
    assert len(pool)==7 and 'move_example' not in {q.id for q in pool}
    for seed in range(40):
        for count in (3,5): assert len({q.id for q in random.Random(seed).sample(pool,count)})==count
        for pid in ('project_2','project_3'):
            qs=select_project_questions(random.Random(seed),pid)
            assert all(q.chapter_id!=UNIT for q in qs) and valid_project_questions([q.id for q in qs],pid)
    for row in QUESTION_SPECS:
        q=QUESTION_MAP[row['id']]
        assert set(OPTION_FEEDBACK[q.id])==set(q.options)-{q.answer}
        assert len(set(q.options))==len(q.options)
        assert provenance_for_card(row['card'])['status']==STATUS_PARTIAL


@pytest.mark.parametrize('backend',['sqlite','memory','fallback'])
def test_backup_progress_and_old_record(tmp_path,backend):
    repo=PracticeRepository(tmp_path/'a.db') if backend=='sqlite' else MemoryPracticeRepository() if backend=='memory' else ResilientPracticeRepository(tmp_path)
    old=QUESTION_MAP['traffic_start']
    repo.save_quiz(make_quiz_record(old.chapter_id,(QuizAnswer(old.id,old.answer,old.answer,True,False),),quiz_id='old'))
    legacy=parse_archive(archive_json_bytes(repo))
    assert calculate_unit_progress(TOPICS,set(),repo.quiz_history(UNIT)).completion==0
    qs=textbook_question_pool((UNIT,),'move_example')[:5]
    record=make_quiz_record(UNIT,tuple(QuizAnswer(q.id,q.answer,q.answer,True,False) for q in qs),'textbook_unit_assessment',quiz_id='move')
    assert repo.save_quiz(record) and not repo.save_quiz(record)
    example=QUESTION_MAP['move_example']
    repo.save_quiz(make_quiz_record(UNIT,(QuizAnswer(example.id,example.answer,example.answer,True,False),),'textbook_example',quiz_id='example'))
    assert calculate_unit_progress(TOPICS,set(TOPICS),repo.quiz_history(UNIT)).completion==1
    target=MemoryPracticeRepository()
    import_archive(target,legacy,confirmed=True)
    assert not target.quiz_history(UNIT)
    archive=parse_archive(archive_json_bytes(repo))
    for _ in range(2): import_archive(target,archive,confirmed=True)
    assert len(target.quiz_history(UNIT))==2 and len(target.quiz_history(old.chapter_id))==1


@pytest.mark.parametrize('kind',['correct','wrong','uncertain'])
def test_ui_copy_and_learning_flow(tmp_path,monkeypatch,kind):
    db=tmp_path/'ui.db'; monkeypatch.setenv('DIANZHENTONG_DB_PATH',str(db))
    app=AppTest.from_file(Path('app.py').resolve(),default_timeout=30).run()
    def button(label): return next(b for b in app.button if b.label==label)
    button('进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(12).run()
    repo=PracticeRepository(db); before=repo.export_snapshot()
    assert app.session_state['move_unit_target']==3
    app.number_input(key='move_unit_source').set_value(8).run()
    assert 'move_unit_snapshot' not in app.session_state and app.session_state['move_unit_target']==3
    app.button(key='move_unit_execute').click().run()
    assert app.session_state['move_unit_target']==8 and app.session_state['move_unit_source']==8
    app.number_input(key='move_unit_source').set_value(-2).run()
    app.checkbox(key='move_unit_enabled').uncheck().run()
    app.button(key='move_unit_execute').click().run()
    assert app.session_state['move_unit_target']==8
    app.checkbox(key='move_unit_enabled').check().run()
    app.button(key='move_unit_execute').click().run()
    assert app.session_state['move_unit_target']==-2
    app.button(key='move_unit_reset').click().run()
    assert app.session_state['move_unit_target']==3 and app.session_state['move_unit_source']==12
    assert app.session_state['move_unit_enabled'] and 'move_unit_snapshot' not in app.session_state
    assert not app.exception and repo.export_snapshot()==before
    for label,count in [('开始学前小测',3),('开始学后评测',5)]:
        button(label).click().run()
        ids=app.session_state['quiz_state']['question_ids']
        assert len(ids)==count and 'move_example' not in ids
        for i,qid in enumerate(ids):
            q=QUESTION_MAP[qid]; answer=q.answer if kind=='correct' else '不确定' if kind=='uncertain' else next(o for o in q.options if o!=q.answer)
            next(r for r in app.radio if r.label=='请选择一个答案').set_value(answer).run()
            button('提交答案').click().run()
            first=list(app.session_state['quiz_state']['answers']); app.run()
            if i==0:
                app.button(key='quiz_relearn_topic').click().run()
                app.button(key='return_to_quiz').click().run()
            assert app.session_state['quiz_state']['answers']==first
            button('查看成绩' if i==count-1 else '下一题').click().run()
        app.run()
        assert app.session_state['quiz_state']['record']['correct_count']==(count if kind=='correct' else 0)
        if kind!='correct':
            app.button(key=f'quiz_card_{ids[0]}').click().run();app.button(key='return_to_quiz').click().run()
        button('返回教材单元').click().run()
        assert app.session_state['selected_textbook_chapter']==12 and not app.exception
    assert len(repo.quiz_history(UNIT))==2
    parse_archive(archive_json_bytes(repo))
