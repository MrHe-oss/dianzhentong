"""无存储、手动计算的双模型对比。"""
import streamlit as st
from .jog_hold import compare_jog_hold


def render_jog_hold(prefix):
    st.markdown("### 对比互动：点动与长动")
    st.caption("两个独立教学模型使用同一组输入，不是实际设备运行方式切换。不计分、不标记学习完成。")
    state, evidence = f"{prefix}_hold", f"{prefix}_evidence"
    if type(st.session_state.get(state)) is not bool:
        st.session_state[state] = False
        st.session_state.pop(evidence, None)
    p = st.checkbox("P：公共允许", value=True, key=f"{prefix}_allow")
    t = st.checkbox("T：停止请求", key=f"{prefix}_stop")
    s = st.checkbox("S：启动请求", key=f"{prefix}_start")
    st.caption("选框是待计算输入；改变选框不更新结果。按计算后查看本次快照。")
    if st.button("计算下一步", key=f"{prefix}_calculate", type="primary"):
        previous = st.session_state[state]
        result = compare_jog_hold(p, t, s, previous)
        st.session_state[evidence] = (p, t, s, previous, result)
        st.session_state[state] = result['next_hold']
    if st.button("重置观察", key=f"{prefix}_reset"):
        st.session_state[state] = False
        st.session_state.pop(evidence, None)
    snapshot = st.session_state.get(evidence)
    if snapshot:
        p0, t0, s0, previous, result = snapshot
        truth = lambda v: '真' if v else '假'
        st.caption(f"上次计算输入快照：P={truth(p0)}，T={truth(t0)}，S={truth(s0)}；上一步H={truth(previous)}")
        left, right = st.columns(2)
        with left:
            st.markdown("#### 点动：只看当前条件")
            st.latex(r"J=P\land\neg T\land S")
            (st.success if result['jog'] else st.info)(f"点动结果：{truth(result['jog'])}")
        with right:
            st.markdown("#### 长动：加入上一保持")
            st.latex(r"H_{next}=P\land\neg T\land(S\lor H_{prev})")
            (st.success if result['next_hold'] else st.info)(f"长动结果：{truth(result['next_hold'])}")
        st.write(result['reason'])
    else:
        st.info("尚未计算；初始保持H为假。可先提出启动，再撤回启动进行比较。")
    st.caption("保持由题设公式明确建立，不是普通赋值自动产生；每次手动计算不代表真实CPU时序。仅限教学模拟，不用于真实设备操作。")
