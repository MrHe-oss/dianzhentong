from dataclasses import asdict
from pathlib import Path
import random

import pytest
from streamlit.testing.v1 import AppTest
from dianzhentong import textbook_project as project
from dianzhentong.quiz import QuizAnswer, QUESTION_MAP, make_quiz_record
from dianzhentong.storage import MemoryPracticeRepository, PracticeRepository, ResilientPracticeRepository
from dianzhentong.backup import archive_json_bytes, parse_archive, import_archive, BackupValidationError
from dianzhentong.textbook_learning import calculate_unit_progress


def record(correct=6):
    answers = tuple(QuizAnswer(q.id, q.answer if i < correct else '不确定', q.answer, i < correct, i >= correct)
                    for i, q in enumerate(project.select_project_questions(random.Random(1))))
    return make_quiz_record(project.SCOPE, answers, project.MODE, quiz_id='project-test')


def test_balanced_independent_selection():
    for seed in range(100):
        ids = [q.id for q in project.select_project_questions(random.Random(seed))]
        assert project.valid_project_questions(ids)
        assert not set(ids) & {'q91', 'q98', 'q103', 'q107'}
    assert not project.valid_project_questions(ids[:-1])
    assert not project.valid_project_questions([ids[0]] * 8)
    assert not project.valid_project_questions(['q91', *ids[1:]])


@pytest.mark.parametrize('correct', [0, 5, 6, 8])
@pytest.mark.parametrize('memory', [True, False])
def test_storage_backup_and_old_progress(tmp_path, correct, memory):
    repo = MemoryPracticeRepository() if memory else PracticeRepository(tmp_path/'history.db')
    result = record(correct)
    assert result.passed == (correct >= 6)
    assert repo.save_quiz(result)
    assert not repo.save_quiz(result)
    assert repo.quiz_answers(result.quiz_id) == [asdict(a) for a in result.answers]
    for _, unit in project.UNITS:
        assert repo.quiz_summary(unit['quiz_chapter_ids'][0])['attempts'] == 0
        assert calculate_unit_progress(unit['topic_ids'], set(), repo.quiz_history(unit['quiz_chapter_ids'][0])).completion == 0
    archive = parse_archive(archive_json_bytes(repo))
    target = MemoryPracticeRepository()
    import_archive(target, archive, confirmed=True)
    import_archive(target, archive, confirmed=True)
    assert len(target.quiz_history(project.SCOPE)) == 1
    assert target.quiz_answers(result.quiz_id) == repo.quiz_answers(result.quiz_id)
    assert sum(r['correct'] for r in project.unit_results(repo.quiz_answers(result.quiz_id))) == correct


def test_recommendation_and_report():
    states = {i: calculate_unit_progress(unit['topic_ids'], set(), []) for i, unit in project.UNITS}
    assert project.recommended_unit(states) == 3
    answers = [asdict(a) for a in record(6).answers]
    assert project.recommended_unit(states, answers) == 6
    assert '不代表整个单元' in project.report_text(answers)
    assert '不确定' in project.report_text(answers)


def test_unwritable_storage_fallback(tmp_path):
    # A directory cannot be opened as a SQLite database on either supported platform.
    repo = ResilientPracticeRepository(tmp_path)
    assert not repo.persistent
    result = record()
    assert repo.save_quiz(result)
    assert repo.quiz_answers(result.quiz_id) == [asdict(a) for a in result.answers]
    assert len(repo.quiz_history(project.SCOPE)) == 1


def test_reject_wrong_project_scope():
    repo = MemoryPracticeRepository(); repo.save_quiz(record())
    # Archive envelope is validated by the existing parser as well as the new project scope.
    raw = archive_json_bytes(repo).decode().replace(project.SCOPE, 'p2_unit_1')
    with pytest.raises(BackupValidationError):
        parse_archive(raw.encode())


def test_project_ui_complete_and_relearn(tmp_path, monkeypatch):
    monkeypatch.setenv('DIANZHENTONG_DB_PATH', str(tmp_path/'ui.db'))
    app = AppTest.from_file(Path('app.py').resolve(), default_timeout=20).run()
    next(b for b in app.button if b.label == '进入教材学习').click().run()
    app.selectbox(key='selected_textbook_chapter').set_value(3).run()
    app.button(key='project2_overview').click().run()
    assert app.session_state['stage'] == 27
    next(b for b in app.button if b.label == '开始项目2综合测验').click().run()
    ids = app.session_state['quiz_state']['question_ids']
    for i, qid in enumerate(ids):
        next(r for r in app.radio if r.label == '请选择一个答案').set_value('不确定').run()
        next(b for b in app.button if b.label == '提交答案').click().run()
        first = list(app.session_state['quiz_state']['answers'])
        app.button(key='quiz_relearn_topic').click().run()
        assert app.session_state['textbook_context']['chapter_index'] == next(index for index, unit in project.UNITS if QUESTION_MAP[qid].chapter_id in unit['quiz_chapter_ids'])
        app.button(key='return_to_quiz').click().run()
        assert app.session_state['quiz_state']['answers'] == first
        next(b for b in app.button if b.label == ('查看成绩' if i == 7 else '下一题')).click().run()
    assert not app.exception and app.session_state['stage'] == 11
    app.button(key=f'quiz_card_{ids[4]}').click().run()
    app.button(key='return_to_quiz').click().run()
    app.run()
    assert not app.exception and app.session_state['quiz_state']['record']['correct_count'] == 0
    repo = PracticeRepository(tmp_path/'ui.db')
    assert len(repo.quiz_history(project.SCOPE)) == 1
    parse_archive(archive_json_bytes(repo))
    next(b for b in app.button if b.label == '返回项目2学习概览').click().run()
    assert app.session_state['stage'] == 27 and not app.exception
    next(b for b in app.button if b.label == '查看最近综合报告').click().run()
    assert app.session_state['stage'] == 11 and not app.exception
    assert len(repo.quiz_history(project.SCOPE)) == 1
    next(b for b in app.button if b.label == '返回项目2学习概览').click().run()
    app.button(key='project_unit_5').click().run()
    assert app.session_state['selected_textbook_chapter'] == 5 and not app.exception
