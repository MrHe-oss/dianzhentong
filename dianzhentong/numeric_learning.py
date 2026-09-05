"""Finite dimensional numeric answers and a deterministic resistor model."""
from decimal import Decimal, InvalidOperation
import re

UNITS = {
    "A": ("current", Decimal("1")), "mA": ("current", Decimal("0.001")),
    "V": ("voltage", Decimal("1")), "mV": ("voltage", Decimal("0.001")),
    "Ω": ("resistance", Decimal("1")), "kΩ": ("resistance", Decimal("1000")),
    "W": ("power", Decimal("1")), "mW": ("power", Decimal("0.001")),
    "J": ("energy", Decimal("1")), "kJ": ("energy", Decimal("1000")),
}
RELATIVE_TOLERANCE = Decimal("0.01")


def allowed_units(base_unit):
    return tuple(unit for unit, (dimension, _) in UNITS.items() if dimension == UNITS[base_unit][0])


def parse_quantity(text, base_unit):
    if not isinstance(text, str) or len(text) > 64:
        raise ValueError("请输入数值并选择单位。")
    match = re.fullmatch(r"\s*([+-]?(?:\d{1,16}(?:\.\d{0,16})?|\.\d{1,16})(?:[eE][+-]?\d{1,2})?)\s+([^\s]+)\s*", text)
    if not match or match[2] not in allowed_units(base_unit):
        raise ValueError("请输入有限数值，单位须与题目所求物理量一致。")
    try:
        value = Decimal(match[1]) * UNITS[match[2]][1] / UNITS[base_unit][1]
    except InvalidOperation as error:
        raise ValueError("数值格式无效。") from error
    if not value.is_finite() or abs(value) > Decimal("1e12"):
        raise ValueError("数值超出本练习范围。")
    return value


def numeric_correct(selected, expected, base_unit):
    actual = parse_quantity(selected, base_unit)
    target = parse_quantity(expected, base_unit)
    return abs(actual - target) <= abs(target) * RELATIVE_TOLERANCE


def resistor_state(voltage, resistance):
    """Positive DC ideal resistor; values here are abstract study parameters."""
    try:
        u, r = Decimal(str(voltage)), Decimal(str(resistance))
    except InvalidOperation as error:
        raise ValueError("模型参数必须为有限数值。") from error
    if not u.is_finite() or not r.is_finite() or not 0 <= u <= 100 or not 1 <= r <= 1000000:
        raise ValueError("模型范围：0≤U≤100 V，1≤R≤1000000 Ω。")
    current = u / r
    return {"voltage": u, "resistance": r, "current": current, "power": u * current}


def circuit_question_specs():
    chapter = "dc_resistor_basics"
    conceptual = [
        ("dc_q01", "同一理想电阻保持400 Ω，电压由8 V变为4 V，电流怎样变化？", ("减为原来的一半", "增为原来的两倍", "保持不变"), "减为原来的一半", "I=U/R，R不变，U减半则I减半。", "dc_ohm_law"),
        ("dc_q02", "理想电阻保持不变，电压加倍，消耗功率如何变化？", ("四倍", "两倍", "不变"), "四倍", "P=U²/R，固定R时U加倍使P变为四倍。", "dc_resistor_power"),
        ("dc_q03", "哪个单位用于表示电流？", ("A", "V", "Ω"), "A", "A表示电流，V表示电压，Ω表示电阻。", "dc_current_units"),
        ("dc_q04", "本单元使用U=RI时，采用什么元件模型？", ("阻值固定的理想线性电阻", "所有元件均有固定电阻", "任意温度下电阻都不变"), "阻值固定的理想线性电阻", "本单元忽略温度影响；比例关系不能无条件套用于非线性元件。", "dc_ohm_law"),
    ]
    rows = [{"id": qid, "chapter_id": chapter, "stem": stem, "options": options, "answer": answer,
             "explanation": explanation, "knowledge_point": card, "card": card}
            for qid, stem, options, answer, explanation, card in conceptual]
    numeric = [
        ("dc_q05", "净电荷0.6 C在3 s内通过同一截面，平均电流是多少？", Decimal("0.6") / 3, "A", "Iav=ΔQ/Δt=0.6/3=0.2 A=200 mA。", "dc_current_units"),
        ("dc_q06", "理想线性电阻两端为9 V，阻值300 Ω，求电流。", resistor_state(9, 300)["current"], "A", "I=U/R=9/300=0.03 A=30 mA。", "dc_ohm_law"),
        ("dc_q07", "理想线性电阻两端为6 V，阻值0.2 kΩ，求电流。", resistor_state(6, 200)["current"], "A", "先将0.2 kΩ化为200 Ω，再算I=6/200=0.03 A。", "dc_ohm_law"),
        ("dc_q08", "理想线性电阻两端为10 V，阻值500 Ω，求消耗功率。", resistor_state(10, 500)["power"], "W", "P=U²/R=100/500=0.2 W=200 mW。", "dc_resistor_power"),
        ("dc_q09", "电阻消耗的恒定功率为0.25 W，持续8 s，求转换的能量。", Decimal("0.25") * 8, "J", "E=Pt=0.25×8=2 J，J是能量单位。", "dc_resistor_power"),
        ("dc_q10", "理想电阻两端6 V，电流3 mA，求电阻。", Decimal(6) / Decimal("0.003"), "Ω", "3 mA=0.003 A；R=U/I=6/0.003=2000 Ω=2 kΩ。", "dc_ohm_law"),
    ]
    rows.extend({"id": qid, "chapter_id": chapter, "stem": stem, "options": (), "answer": f"{value} {unit}",
                 "numeric_unit": unit, "explanation": explanation, "knowledge_point": card, "card": card}
                for qid, stem, value, unit, explanation, card in numeric)
    titles = {"dc_current_units": "电流、电压与单位", "dc_ohm_law": "欧姆定律与适用条件", "dc_resistor_power": "电阻功率与能量"}
    for row in rows:
        row["knowledge_point"] = titles[row["card"]]
    return rows
