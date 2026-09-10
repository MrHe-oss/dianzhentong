"""只读教学观察组件：开关状态留在当前页面，不写学习记录。"""
import streamlit as st
from .bit_logic import evaluate_request


def render_bit_logic(prefix):
    st.markdown("### 互动观察：两个请求与停止条件")
    st.caption("抽象逻辑图，不是博途界面或接线图。只供观察，不计分，也不标记单元完成。")
    a = st.checkbox("A：请求一为真", key=f"{prefix}_a")
    b = st.checkbox("B：请求二为真", key=f"{prefix}_b")
    stop = st.checkbox("T：停止条件为真", key=f"{prefix}_t")
    values = evaluate_request(a, b, stop)
    st.latex(r"Y=(A\lor B)\land\neg T")
    columns = st.columns(2)
    for column, label, value in ((columns[0], "M = A∨B：至少一个请求", values["request"]),
                                 (columns[1], "N = ¬T：没有停止请求", values["permitted"])):
        with column:
            (st.success if value else st.info)(f"{label} → {'真' if value else '假'}")
    st.markdown("↓ 两个分支的结果必须同时为真（与）")
    (st.success if values["result"] else st.info)(f"当前结果 Y：{'真' if values['result'] else '假'}")
    st.caption("尝试先让A为真，再撤回A；即使刚才Y为真，本次也重新计算，不保留旧结果。T为真时Y始终为假。")
    st.caption("本例每次完整执行普通赋值、Y只有一处写入；不模拟真实CPU响应时间，不连接设备。")
