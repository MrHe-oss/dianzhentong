"""只观察、不计分的条件驱动阶段互动。"""
import streamlit as st
from .plc_star_delta import STAGE_IDS, star_delta_next
from .star_delta_stages import STAR_DELTA_STAGES, stage_by_id, role_is_active


def render_plc_star_delta(prefix):
    st.markdown('### 条件互动：星—三角阶段转换')
    st.caption('仅限抽象教学模拟，不计分、不记录学习完成。条件不代表真实时间或现场反馈。')
    state, evidence = f'{prefix}_stage', f'{prefix}_evidence'
    if st.session_state.get(state) not in STAGE_IDS:
        st.session_state[state] = 'stopped'
        st.session_state.pop(evidence, None)
    values = [st.checkbox(label, value=key == 'allow', key=f'{prefix}_{key}') for key, label in
              [('allow', '公共允许'), ('start', '启动请求'), ('stop', '停止请求'), ('end', '星形阶段结束条件'), ('transition', '转换允许')]]
    st.caption('修改选框只准备输入；每按一次计算，最多前进一个阶段。停止或失去允许可从任意阶段返回停止。')
    if st.button('计算下一步', key=f'{prefix}_calculate', type='primary'):
        previous = st.session_state[state]
        result = star_delta_next(previous, *values)
        st.session_state[state] = result['stage']
        st.session_state[evidence] = (previous, tuple(values), result)
    if st.button('重置观察', key=f'{prefix}_reset'):
        st.session_state[state] = 'stopped'
        st.session_state.pop(evidence, None)
    current = st.session_state[state]
    for column, stage in zip(st.columns(4), STAR_DELTA_STAGES):
        with column:
            (st.success if stage['id'] == current else st.info)(str(stage['title']))
    st.markdown(f"**当前阶段：{stage_by_id(current)['title']}**")
    for role in stage_by_id(current)['roles']:
        (st.success if role_is_active(role) else st.info)(role)
    snapshot = st.session_state.get(evidence)
    if snapshot:
        previous, inputs, result = snapshot
        st.caption('上次计算快照；改变选框后须再次计算才会更新。')
        st.write('输入：' + '；'.join(f"{label}={'真' if value else '假'}" for label, value in zip(('允许', '启动', '停止', '星形结束', '转换允许'), inputs)))
        st.info(f"{stage_by_id(previous)['title']} → {stage_by_id(result['stage'])['title']}：{result['reason']}")
    st.caption('转换等待是独立教学阶段，不指定实际等待时长；不模拟定时器指令或CPU时序，不提供接线、时间整定或真实操作依据。')
