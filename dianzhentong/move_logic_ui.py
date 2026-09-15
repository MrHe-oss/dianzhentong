import streamlit as st
from .move_logic import move_once, MIN_VALUE, MAX_VALUE


def render_move(prefix):
    st.markdown('### 条件互动：单次数据复制')
    st.caption('A、B为两个独立的同类型整数变量，只有本模型写入B。范围-999至999仅为教学输入限制，不是PLC整数类型的完整范围。')
    defaults = {'source':12, 'target':3, 'enabled':True}
    for name, value in defaults.items():
        if f'{prefix}_{name}' not in st.session_state:
            st.session_state[f'{prefix}_{name}'] = value
    st.number_input('源A的当前值', min_value=MIN_VALUE, max_value=MAX_VALUE, step=1, key=prefix+'_source')
    st.number_input('目标B的执行前值', min_value=MIN_VALUE, max_value=MAX_VALUE, step=1, key=prefix+'_target')
    st.checkbox('执行条件', key=prefix+'_enabled')
    def execute():
        source, target, enabled = (st.session_state[f'{prefix}_{name}'] for name in defaults)
        result = move_once(source, target, enabled)
        st.session_state[prefix+'_snapshot'] = (source, target, enabled, result)
        st.session_state[prefix+'_target'] = result['target']
    def reset():
        for name, value in defaults.items(): st.session_state[f'{prefix}_{name}'] = value
        st.session_state.pop(prefix+'_snapshot', None)
    st.button('执行一次', key=prefix+'_execute', type='primary', on_click=execute)
    st.button('重置观察', key=prefix+'_reset', on_click=reset)
    st.caption('修改输入不会复制；每次执行后B成为下一次的目标原值。也可手动准备新的B原值。互动不计分、不记录学习完成。')
    snapshot = st.session_state.get(prefix+'_snapshot')
    if snapshot:
        source, target, enabled, result = snapshot
        st.write(f"上次执行输入快照：源A={source}；目标B原值={target}；执行条件={'真' if enabled else '假'}")
        cols = st.columns(2)
        cols[0].info(f"源A：{source} → {result['source']}（不变）")
        cols[1].success(f"目标B：{target} → {result['target']}")
        st.write(result['reason'])
        st.caption('上方为上次结果；修改输入后，须再次点击执行才会更新该快照。')
    st.caption('单次复制教学模型，不模拟完整扫描、地址、类型转换、其他程序写入或真实设备操作。')
