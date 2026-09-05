"""Small reusable numerical exercise and original circuit lesson controls."""
import streamlit as st
from .numeric_learning import allowed_units, parse_quantity, resistor_state


def numeric_answer_input(question, key, disabled=False):
    st.caption("填写数值并选择单位；可用科学计数法。换算后相对误差在1%以内算正确。")
    value = st.text_input("你的计算结果", key=key + "_value", max_chars=40, disabled=disabled,
                          placeholder="例如：0.03 或 3e-2")
    unit = st.selectbox("结果单位", allowed_units(question.numeric_unit), key=key + "_unit", disabled=disabled)
    uncertain = st.checkbox("这题暂不确定", key=key + "_uncertain", disabled=disabled)
    if uncertain:
        return "不确定"
    if not value.strip():
        return None
    selected = f"{value.strip()} {unit}"
    try:
        parse_quantity(selected, question.numeric_unit)
    except ValueError as error:
        st.caption(str(error))
        return None
    return selected


def render_resistor_explorer(key):
    st.markdown("### 互动观察：改变电压或电阻")
    st.caption("理想直流线性电阻，阻值不随温度改变。这里的数值仅用于模型计算。")
    u = st.slider("电阻两端电压 U（V）", 0, 20, 4, key=key + "_u")
    r = st.slider("电阻 R（Ω）", 10, 1000, 200, step=10, key=key + "_r")
    current = resistor_state(u, r)
    st.latex(r"I=\frac{U}{R},\qquad P=UI=\frac{U^2}{R}")
    st.write(f"代入：I = {u}/{r} = {current['current']:.5g} A；P = {u}²/{r} = {current['power']:.5g} W")
    baseline_key = key + "_baseline"
    if st.button("保存当前值作为对比起点", key=key + "_save"):
        st.session_state[baseline_key] = current
    baseline = st.session_state.get(baseline_key)
    if baseline is not None:
        rows = [("电压（V）", "voltage"), ("电阻（Ω）", "resistance"), ("电流（A）", "current"), ("功率（W）", "power")]
        st.markdown("| 物理量 | 对比起点 | 当前 |\n|---|---:|---:|\n" + "\n".join(
            f"| {label} | {baseline[field]:.5g} | {current[field]:.5g} |" for label, field in rows))
        if current["resistance"] == baseline["resistance"] and baseline["voltage"] > 0:
            ratio = current["voltage"] / baseline["voltage"]
            st.info(f"电阻未变：电压是原来的 {ratio:.3g} 倍，电流是 {ratio:.3g} 倍，功率是 {ratio * ratio:.3g} 倍。")
        elif current["voltage"] == baseline["voltage"]:
            st.info("电压未变：电流与功率都随电阻增大而减小；当电压为0时，两者均为0。")
        else:
            st.info("两项参数发生变化或起点电压为0，请分别代入公式比较，不直接使用倍数结论。")
    st.caption("试一试：保存4 V、200 Ω为起点，保持R不变，将U改为8 V；解释为什么电流变为两倍、功率变为四倍。观察不计入测验成绩。")
