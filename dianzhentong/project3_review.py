"""原创跨单元复习，所有计算复用既有教学规则。"""
from .plc_lab import logic_output
from .direction_logic import direction_next
from .jog_hold import compare_jog_hold
from .plc_star_delta import star_delta_next
from .star_delta_stages import stage_by_id


def example_steps():
    current = logic_output("AND", logic_output("OR", False, False), logic_output("NOT", False))
    hold = compare_jog_hold(True, False, False, True)
    direction = direction_next("正向", True, False, True, True)
    stopped = compare_jog_hold(True, True, True, True)
    stage = star_delta_next("star_start", True, False, False, True, True)
    return (
        {"unit": "p3_unit_1", "title": "1. 撤回全部当前请求", "hint": "无记忆模型不引用上次结果。",
         "conditions": "位逻辑例题：A、B都假，停止T假；上一轮结果即使为真，也不参与本轮赋值。",
         "answer": f"本轮Y={'真' if current else '假'}。先算A或B，再与非T组合；不是自动保持。"},
        {"unit": "p3_unit_3", "title": "2. 同样撤回启动，加入上一保持状态", "hint": "分别寻找两个模型是否引用历史状态。",
         "conditions": "公共允许真、停止假、启动假，长动上一步保持为真。",
         "answer": f"点动{'真' if hold['jog'] else '假'}、长动{'真' if hold['next_hold'] else '假'}。{hold['reason']}"},
        {"unit": "p3_unit_2", "title": "3. 两个方向请求同时成立", "hint": "先检查本题明确规定的冲突规则。",
         "conditions": "原为正向；公共允许真、停止假、正向和反向请求都真。",
         "answer": f"下一状态：{direction['state']}。{direction['reason']}；不能推广为所有实际系统的策略。"},
        {"unit": "p3_unit_3", "title": "4. 启动与停止同时成立", "hint": "先判断停止是否阻断启动和保持。",
         "conditions": "公共允许、启动、停止与上一保持都真。",
         "answer": f"点动{'真' if stopped['jog'] else '假'}、长动{'真' if stopped['next_hold'] else '假'}。{stopped['reason']}"},
        {"unit": "p3_unit_4", "title": "5. 转换条件齐全，能否跳阶段", "hint": "一次计算最多转换一个阶段。",
         "conditions": "原为星形启动；允许真、停止假、启动假，阶段结束和转换允许都真。",
         "answer": f"下一阶段：{stage_by_id(stage['stage'])['title']}。{stage['reason']}"},
    )


def render_summary(open_unit):
    import streamlit as st
    st.markdown("### 四种教学逻辑的区别")
    st.markdown("""| 单元 | 本次判断依据 | 撤回请求与停止 |
| --- | --- | --- |
| 位逻辑 | 当前布尔输入；本例每次完整赋值 | 无历史保持；按当前条件重新计算 |
| 正反转 | 当前请求＋上一方向状态 | 撤回请求可保持；停止、失去允许或双向冲突退出 |
| 点动与长动 | 点动只看当前输入；长动还看上一保持 | 撤回启动时二者可能不同；停止优先 |
| 星—三角 | 当前条件＋当前阶段 | 启动后按阶段推进；停止或失去允许回到停止 |""")
    st.caption("仅比较本平台题设模型，不代表实际程序、接线或现场控制策略。")
    st.markdown("### 原创综合例题：同样改变请求，为什么结果不同")
    st.caption("先读条件再展开提示和答案。本例不计分、不另设完成条件；原创跨单元推理待专业复核。")
    for i, step in enumerate(example_steps()):
        with st.container(border=True):
            st.markdown(f"#### {step['title']}")
            st.write(step["conditions"])
            with st.expander("查看提示"):
                st.write(step["hint"])
            with st.expander("展开答案与推理"):
                st.write(step["answer"])
            if st.button("回看对应单元", key=f"project3_example_unit_{i}", use_container_width=True):
                open_unit(step["unit"])
