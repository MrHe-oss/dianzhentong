"""时间继电器与顺序控制课程的抽象状态演示。"""
from __future__ import annotations

from typing import Any


def _stage(title: str, description: str, roles: tuple[str, ...], next_condition: str) -> dict[str, Any]:
    return {"title": title, "description": description, "roles": roles,
            "next_condition": next_condition}


ON_DELAY_STAGES = (
    _stage("初始状态", "输入条件尚未形成，输出保持初始状态。", ("计时未开始", "输出未发生延时改变"), "输入条件形成"),
    _stage("启动请求", "输入条件形成，通电延时过程开始。", ("输入有效", "开始计时"), "进入延时等待"),
    _stage("延时等待", "等待尚未完成，输出仍保持原状态。", ("计时进行中", "输出尚未改变"), "时间条件到达"),
    _stage("条件到达", "等待完成，延时输出改变。", ("计时完成", "输出状态改变"), "允许后续逻辑判断"),
    _stage("后续执行", "后续阶段在前序条件满足后被允许。", ("前序有效", "后续阶段进入"), "根据任务继续或复位"),
)

OFF_DELAY_STAGES = (
    _stage("初始有效", "输入与输出均处于题设给出的有效状态。", ("输入有效", "输出有效"), "输入条件消失"),
    _stage("停止请求", "输入条件消失，断电延时过程开始。", ("输入已撤除", "输出暂时保持"), "进入延时等待"),
    _stage("延时等待", "输出在等待期间继续保持原有效状态。", ("计时进行中", "输出尚未退出"), "时间条件到达"),
    _stage("条件到达", "等待完成，输出结束保持。", ("计时完成", "输出退出"), "允许后续退出逻辑"),
    _stage("阶段结束", "相关阶段已按条件结束。", ("输出回到非有效状态", "过程可等待下一次输入"), "新的输入条件"),
)

SEQUENCE_STAGES = (
    _stage("初始状态", "公共条件可用，但各阶段尚未进入。", ("公共条件待确认", "阶段未启动"), "启动请求形成"),
    _stage("第一阶段", "第一阶段先在公共条件下形成。", ("公共条件有效", "第一阶段有效"), "顺序条件开始"),
    _stage("条件等待", "后续阶段等待前序与时间条件。", ("第一阶段保持", "后续阶段未进入"), "顺序条件到达"),
    _stage("后续阶段", "前序条件满足后，后续阶段被允许进入。", ("前序条件有效", "后续阶段有效"), "继续运行或接收停止请求"),
    _stage("有序退出", "停止请求后按题设退出条件结束相关阶段。", ("停止请求有效", "阶段按顺序结束"), "返回初始状态"),
)


def demos_for_chapter(chapter_id: str) -> tuple[tuple[str, tuple[dict[str, Any], ...]], ...]:
    if chapter_id == "timer_functions":
        return (("通电延时过程", ON_DELAY_STAGES),)
    if chapter_id == "on_off_delay":
        return (("通电延时", ON_DELAY_STAGES), ("断电延时", OFF_DELAY_STAGES))
    if chapter_id == "sequence_control":
        return (("顺序过程", SEQUENCE_STAGES),)
    return ()


def validate_time_sequence_demos() -> None:
    for stages in (ON_DELAY_STAGES, OFF_DELAY_STAGES, SEQUENCE_STAGES):
        if len(stages) != 5 or len({item["title"] for item in stages}) != 5:
            raise ValueError("时间过程演示阶段无效")
        if any(not all(item[field] for field in ("description", "roles", "next_condition")) for item in stages):
            raise ValueError("时间过程演示内容不完整")


validate_time_sequence_demos()
