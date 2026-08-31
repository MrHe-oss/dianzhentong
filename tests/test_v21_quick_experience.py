from __future__ import annotations
from dianzhentong.quick_experience import EXPERIENCE_ITEMS, QuickExperienceSession, experience_report

def complete(wrong_first=False):
    session=QuickExperienceSession(); session.mark_card_read()
    while not session.is_complete:
        item=session.current_item
        if wrong_first and not session.first_answers:
            session.answer(next(value for value in item["options"] if value != item["answer"]))
        session.answer(item["answer"]); session.next_item()
    return session

def test_experience_has_diagram_three_checks_and_two_quiz_items():
    assert len(EXPERIENCE_ITEMS)==6
    phases=[item["phase"] for item in EXPERIENCE_ITEMS]
    assert phases.count("识图体验")==1
    assert phases.count("模拟排查")==3
    assert phases.count("迷你测验")==2
    assert all(len(set(item["options"]))==len(item["options"]) and item["answer"] in item["options"] for item in EXPERIENCE_ITEMS)

def test_correct_path_finishes_with_full_score_and_roundtrips_state():
    session=complete()
    restored=QuickExperienceSession.from_dict(session.to_dict())
    assert restored.is_complete and restored.correct_count==6
    assert "首次判断：6/6" in experience_report(restored)

def test_first_wrong_answer_counts_once_and_retry_continues():
    session=complete(True)
    assert session.correct_count==5
    assert session.wrong_items==["quick_diagram"]
    assert "识图体验" in experience_report(session)

def test_experience_is_session_only_and_app_has_direct_entry():
    source=open("app.py",encoding="utf-8").read()
    for phrase in ("开始5分钟体验","无需解锁课程","体验结果不写入正式成绩","进入正式课程"):
        assert phrase in source
    assert "save_quick" not in source
    assert "st.dataframe" not in source and "st.table" not in source

def test_experience_contains_no_operational_instruction():
    text=str(EXPERIENCE_ITEMS)
    for forbidden in ("220V","380V","短接验证","真实接线步骤"):
        assert forbidden not in text
