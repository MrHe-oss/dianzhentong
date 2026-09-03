"""Native Streamlit, single-column interactive lessons."""
import streamlit as st
from html import escape
from .plc_lab import BOOK_ID, LABS, SAFETY, SCAN_NOTE, SOURCE_URL, LabSession
from .quiz import QUESTION_MAP


def render_lab(repository, set_stage, open_topic, render_provenance, provenance_for_card):
    session = st.session_state.get("plc_lab_session")
    if (not isinstance(session, LabSession) or session.lab_id not in LABS
            or session.phase not in {"intro", "predict", "observe", "transfer", "report"}):
        st.session_state.pop("plc_lab_session", None)
        set_stage(20)
        st.rerun()
    lab = LABS[session.lab_id]
    st.subheader(lab["title"])
    st.caption(SAFETY)
    st.write(lab["goal"])
    phases = ("intro", "predict", "observe", "transfer", "report")
    st.progress((phases.index(session.phase) + 1) / len(phases),
                text="任务 → 预测 → 互动观察 → 迁移题 → 学习报告")
    if session.lab_id == "scan":
        st.info(SCAN_NOTE)
    if session.phase == "intro":
        st.write("先独立预测，再改变抽象输入并观察结果，最后完成迁移题。两题只记录首次选择；操作次数不计分。")
        if st.button("先做预测", key="lab_begin", type="primary"):
            session.begin(); st.rerun()
    elif session.phase in {"predict", "transfer"}:
        q = QUESTION_MAP[f"plc_{session.lab_id}_{session.phase}"]
        st.markdown("### " + ("先预测" if session.phase == "predict" else "换个条件，再判断"))
        choice = st.radio(q.stem, (*q.options, "不确定"), index=None,
                          key=f"lab_answer_{session.session_id}_{session.phase}")
        if st.button("提交首次判断", key="lab_submit", type="primary", disabled=choice is None):
            session.answer(choice); st.rerun()
    elif session.phase == "observe":
        first = next(iter(session.answers.values()))
        q = QUESTION_MAP[first.question_id]
        st.info(f"首次预测：{first.selected_answer}；正确答案：{q.answer}。{q.explanation}")
        st.markdown("### 改变条件，观察结果")
        prefix = session.session_id
        inputs = {}
        if session.lab_id == "logic":
            inputs["operator"] = st.selectbox("逻辑运算", ["AND", "OR", "NOT"], key=prefix + "operator")
            inputs["a"] = st.checkbox("输入A为真", key=prefix + "a")
            inputs["b"] = st.checkbox("输入B为真", disabled=inputs["operator"] == "NOT", key=prefix + "b")
            st.code({"AND": "结果 = A AND B", "OR": "结果 = A OR B", "NOT": "结果 = NOT A"}[inputs["operator"]])
            action = "计算并观察"
        elif session.lab_id == "scan":
            inputs["a"] = st.checkbox("当前模拟输入为真", key=prefix + "a")
            action = ("读取输入快照", "执行本轮逻辑", "更新显示结果")[session.scan.phase]
            st.write(f"已完成周期：{session.scan.cycles}；下一步：{action}")
            st.caption("试一试：先读取假，再把输入改为真，继续执行和更新；对比下一周期。")
        else:
            inputs["allow"] = st.checkbox("运行许可成立", value=True, key=prefix + "allow")
            inputs["start"] = st.checkbox("启动请求", key=prefix + "start")
            inputs["stop"] = st.checkbox("停止请求", key=prefix + "stop")
            st.code("下一状态 = 许可 AND NOT 停止 AND (启动 OR 先前运行)")
            st.caption("先启动一步，再撤回启动请求；最后同时提出启动和停止请求。")
            action = "推进一步并观察"
        if st.button(action, key="lab_observe", type="primary"):
            session.observe(**inputs); st.rerun()
        if session.last_observation:
            st.success(session.last_observation)
        if session.lab_id == "scan":
            nodes = [f"输入快照：{session.scan.sampled}", f"逻辑计算：{session.scan.computed}",
                     f"显示结果：{session.scan.output}"]
        elif session.lab_id == "hold":
            nodes = ["许可与停止条件", "启动或先前保持", f"已执行状态：{'运行' if session.running else '停止'}"]
        else:
            nodes = ["抽象输入A、B", inputs["operator"], "点击计算更新结果"]
        st.markdown('<div class="dzt-flow">' + '<b>→</b>'.join(
            '<span>' + escape(node) + '</span>' for node in nodes) + '</div>', unsafe_allow_html=True)
        st.caption("输入改变后，请点击推进按钮；上方结果保留的是最近一次已执行的观察。")
        ready = session.observations > 0 and (session.lab_id != "scan" or session.scan.cycles > 0)
        if st.button("完成观察，做迁移题", key="lab_transfer", disabled=not ready):
            session.finish_observation(); st.rerun()
    else:
        record = session.to_record()
        repository.save_quiz(record)
        if not getattr(repository, "persistent", True):
            st.warning("存储不可用：本次成绩仅在当前会话内保存，刷新或重启可能丢失。")
        st.metric("首次判断正确数", f"{record.correct_count} / {record.total_count}")
        st.caption("已计入答题记录和错题复习，不改变原单元测验通过状态。云端记录可能丢失，请按需备份。")
        for answer in record.answers:
            q = QUESTION_MAP[answer.question_id]
            st.markdown("#### " + q.stem)
            st.write(f"你的首次判断：{answer.selected_answer}；正确判断：{q.answer}")
            st.info(q.explanation)
        st.download_button("下载互动学习报告", session.report_text(),
                           file_name=f"plc-{session.lab_id}.txt", mime="text/plain")
        if st.button("复习关联知识卡", key="lab_card"):
            open_topic(BOOK_ID, lab["unit"], lab["card"]); st.rerun()
        if st.button("再练一次", key="lab_restart"):
            st.session_state.plc_lab_session = LabSession(session.lab_id); st.rerun()
        if st.button("打开10分钟复习清单", key="lab_review"):
            set_stage(18); st.rerun()
    render_provenance(provenance_for_card(lab["card"]))
    with st.expander("互动模型的教学边界"):
        st.markdown(f"[Siemens：RUN模式扫描周期]({SOURCE_URL})")
        st.caption("控制原理依据已有知识卡；交互顺序为原创简化教学模型，部分核对。")
    if st.button("返回教材单元", key="lab_back", use_container_width=True):
        st.session_state.selected_textbook_id = BOOK_ID
        st.session_state.selected_textbook_chapter = lab["unit"]
        set_stage(20); st.rerun()
