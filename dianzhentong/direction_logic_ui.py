"""不计分、不持久化的逐步方向逻辑观察。"""
import streamlit as st
from .direction_logic import STATES, direction_next


def render_direction_logic(prefix):
    st.markdown("### 互动观察：方向请求与保持状态")
    st.caption("抽象教学状态，不是实际电机状态或博途界面。只供观察，不计入学习完成度。")
    state_key, evidence_key = f"{prefix}_state", f"{prefix}_evidence"
    if st.session_state.get(state_key) not in STATES:
        st.session_state[state_key] = "停止"
        st.session_state.pop(evidence_key, None)
    allow = st.checkbox("公共允许", value=True, key=f"{prefix}_allow")
    stop = st.checkbox("停止请求", key=f"{prefix}_stop")
    forward = st.checkbox("正向请求", key=f"{prefix}_forward")
    reverse = st.checkbox("反向请求", key=f"{prefix}_reverse")
    st.caption("先调整待计算输入，再按计算。仅改变选框不会更新状态；本题双向请求冲突时停止。")
    if st.button("计算下一步", key=f"{prefix}_calculate", type="primary"):
        previous = st.session_state[state_key]
        result = direction_next(previous, allow, stop, forward, reverse)
        st.session_state[state_key] = result["state"]
        st.session_state[evidence_key] = (previous, (allow, stop, forward, reverse), result)
    if st.button("重置观察状态", key=f"{prefix}_reset"):
        st.session_state[state_key] = "停止"
        st.session_state.pop(evidence_key, None)
    st.info(f"当前教学状态：{st.session_state[state_key]}")
    evidence = st.session_state.get(evidence_key)
    if evidence:
        previous, inputs, result = evidence
        st.caption("以下是上次计算快照；改变上方选框后，需要再次计算才会更新。")
        st.info(f"计算前：{previous}")
        st.write("↓ 输入快照：" + "；".join(f"{label}={'真' if value else '假'}" for label, value in zip(("允许", "停止", "正向请求", "反向请求"), inputs)))
        st.success(f"计算后：{result['state']} · {result['reason']}")
        st.caption(f"抽象方向标志：正向={int(result['forward'])}，反向={int(result['reverse'])}")
    st.warning("逻辑停止不证明真实电机停稳。本互动不提供实际换向、设备连接或接线指导。")
