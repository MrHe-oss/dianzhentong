import streamlit as st
from .traffic_logic import STAGES, traffic_next


def render_traffic(prefix):
    st.markdown('### 条件互动：交通信号阶段循环')
    st.caption('原创抽象教学模型，不是实际道路交通控制方案；无真实时长，不计分、不记录完成。')
    key, evidence = prefix + '_stage', prefix + '_evidence'
    if st.session_state.get(key) not in STAGES:
        st.session_state[key] = 'stopped'
        st.session_state.pop(evidence, None)
    values = tuple(st.checkbox(label, value=name == 'allow', key=f'{prefix}_{name}')
                   for name, label in [('allow', '运行允许'), ('start', '启动请求'), ('stop', '停止请求'), ('end', '阶段结束条件')])
    st.caption('选框只准备输入；点击计算才转换。结束条件用于当前阶段，不代表真实计时或现场反馈。')
    if st.button('计算下一步', key=prefix+'_calculate', type='primary'):
        previous = st.session_state[key]
        result = traffic_next(previous, *values)
        st.session_state[key] = result['stage']
        st.session_state[evidence] = (previous, values, result)
    if st.button('重置观察', key=prefix+'_reset'):
        st.session_state[key] = 'stopped'
        st.session_state.pop(evidence, None)
    stage = STAGES[st.session_state[key]]
    st.markdown(f'**当前阶段：{stage[0]}**')
    colors = {'红': '#fee2e2', '黄': '#fef3c7', '绿': '#dcfce7'}
    for column, group, color in zip(st.columns(2), ('A组', 'B组'), stage[1:]):
        with column:
            st.markdown(f'<div style="background:{colors[color]};color:#172554;padding:1rem;border-radius:12px">{group}：<strong>{color}灯有效</strong></div>', unsafe_allow_html=True)
    st.caption('A绿 → A黄 → 全红过渡（A→B） → B绿 → B黄 → 全红过渡（B→A） → A绿')
    if evidence in st.session_state:
        previous, inputs, result = st.session_state[evidence]
        st.write('上次计算输入快照：' + '；'.join(f"{label}={'真' if value else '假'}" for label, value in zip(('允许', '启动', '停止', '阶段结束'), inputs)))
        st.info(f"{STAGES[previous][0]} → {STAGES[result['stage']][0]}：{result['reason']}")
    st.caption('停止和两个全红过渡的显示相同，但状态与退出条件不同。模型不包含真实配时、接线或安全认证。')
