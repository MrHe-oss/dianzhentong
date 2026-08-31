"""教学内容的官方来源、核对状态与可追溯关系。"""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from urllib.parse import urlparse

STATUS_VERIFIED = "已核对通用原理"
STATUS_PARTIAL = "部分核对：通用原理已有官方资料，教学顺序仍待专业复核"
STATUS_PENDING = "待复核：不进入课程综合评测"
ASSESSABLE_STATUSES = {STATUS_VERIFIED, STATUS_PARTIAL}
CHECKED_ON = "2026-08-31"

SOURCES: dict[str, dict[str, str]] = {
    "abb_dol": {"title":"ABB DRAF enclosed direct-on-line starter","publisher":"ABB","url":"https://new.abb.com/low-voltage/nl/producten/motorbeveiligingen-en-besturingen/starting-solutions/draf-enclosed-dol-starter","type":"厂家产品与技术资料","scope":"直接启动器、控制与保护组合的通用构成","checked_on":CHECKED_ON},
    "abb_motor_control": {"title":"ABB Manual motor starters, contactors and overload relays panorama","publisher":"ABB","url":"https://library.e.abb.com/public/4345418d61514245af8fa8c5f70adf7d/1SBC100191L0203_MMS_Contactors_Overload_Relays_Panorama.pdf","type":"厂家产品技术手册","scope":"接触器、热过载继电器和电动机保护元件的功能","checked_on":CHECKED_ON},
    "abb_contactor": {"title":"ABB Open NEMA contactors and motor starters","publisher":"ABB","url":"https://new.abb.com/low-voltage/products/motor-protection/starting-solutions/open-nema-contactors-%28cr305%29","type":"厂家接触器技术资料","scope":"接触器、线圈和辅助触点的通用功能","checked_on":CHECKED_ON},
    "schneider_interlock": {"title":"Schneider Electric LE2GBK reversing starter FAQ","publisher":"Schneider Electric","url":"https://www.se.com/uk/en/faqs/FA139509/","type":"厂家正反转启动器技术资料","scope":"正反转启动器与机械、电气互锁的通用原理","checked_on":CHECKED_ON},
}

def _item(principle: str, sources: tuple[str, ...], status: str = STATUS_PARTIAL) -> dict[str, object]:
    return {"principle": principle, "sources": sources, "status": status}

CARD_PROVENANCE: dict[str, dict[str, object]] = {
    "control_power": _item("控制电源是接触器控制逻辑的前置条件。", ("abb_dol", "abb_contactor")),
    "fuse": _item("保护元件属于电动机启动控制组合的公共环节。", ("abb_dol", "abb_motor_control"), STATUS_VERIFIED),
    "thermal_relay": _item("热过载继电器的保护状态会影响电动机控制条件。", ("abb_motor_control", "abb_dol"), STATUS_VERIFIED),
    "button_contacts": _item("按钮触点用于表达启动、停止等操作请求。", ("abb_contactor",)),
    "contactor_coil": _item("接触器线圈驱动接触器及其辅助触点改变状态。", ("abb_contactor", "abb_motor_control"), STATUS_VERIFIED),
    "self_hold": _item("辅助触点可构成启动请求之外的保持逻辑。", ("abb_contactor",)),
    "electrical_interlock": _item("正反转控制使用另一方向的辅助触点构成电气互锁。", ("schneider_interlock", "abb_contactor"), STATUS_VERIFIED),
    "forward_reverse": _item("正反转启动器由方向接触器、公共保护及互锁关系构成。", ("schneider_interlock", "abb_motor_control"), STATUS_VERIFIED),
    "jog_control": _item("点动与连续运行共享部分控制元件，但操作和保持逻辑不同。", ("abb_contactor",)),
    "diagram_symbols": _item("控制图可按保护、操作、辅助和执行等功能角色进行识读。", ("abb_motor_control", "abb_contactor")),
    "series_logic": _item("多个串联控制条件需要共同满足，任一中断都会阻断路径。", ("abb_dol", "abb_contactor")),
    "parallel_logic": _item("辅助触点与操作触点可形成不同的控制条件分支。", ("abb_contactor",)),
    "logic_tracing": _item("控制逻辑可按公共条件、相关分支和执行元件顺序追踪。", ("abb_dol", "schneider_interlock")),
}

RESULT_CARD_MAP = {
    "cause_control_power":"control_power", "cause_fuse":"fuse", "cause_thermal":"thermal_relay", "cause_stop":"button_contacts", "cause_start":"button_contacts", "cause_coil":"contactor_coil",
    "fr_cause_fuse":"fuse", "fr_cause_thermal":"thermal_relay", "fr_cause_stop":"button_contacts", "fr_cause_forward_button":"button_contacts", "fr_cause_reverse_button":"button_contacts", "fr_cause_forward_coil":"contactor_coil", "fr_cause_reverse_coil":"contactor_coil", "fr_cause_interlock":"electrical_interlock",
    "jc_cause_public":"control_power", "jc_cause_stop":"button_contacts", "jc_cause_jog_button":"jog_control", "jc_cause_continuous_button":"button_contacts", "jc_cause_self_hold":"self_hold", "jc_cause_coil":"contactor_coil",
}
RESULT_PROVENANCE = {result_id: {**CARD_PROVENANCE[card_id], "card_id":card_id} for result_id, card_id in RESULT_CARD_MAP.items()}

def provenance_for_card(card_id: str | None) -> dict[str, object] | None:
    return CARD_PROVENANCE.get(card_id or "")

def provenance_for_result(result_id: str | None) -> dict[str, object] | None:
    return RESULT_PROVENANCE.get(result_id or "")

def provenance_for_question(card_id: str | None) -> dict[str, object] | None:
    """题目来源由其唯一关联知识卡派生，避免维护第二套引用。"""
    return provenance_for_card(card_id)

def provenance_for_diagram(card_ids: Iterable[str]) -> dict[str, object]:
    items = [CARD_PROVENANCE[card_id] for card_id in card_ids]
    source_ids = tuple(dict.fromkeys(source for item in items for source in item["sources"]))
    statuses = {str(item["status"]) for item in items}
    status = STATUS_PENDING if STATUS_PENDING in statuses else (STATUS_PARTIAL if STATUS_PARTIAL in statuses else STATUS_VERIFIED)
    return _item("本案例的路径依据来自所关联知识卡的控制逻辑。", source_ids, status)

def is_card_assessable(card_id: str) -> bool:
    item = CARD_PROVENANCE.get(card_id)
    return bool(item and item["status"] in ASSESSABLE_STATUSES)

def resolved_sources(item: Mapping[str, object]) -> tuple[dict[str, str], ...]:
    return tuple({"id": source_id, **SOURCES[source_id]} for source_id in item["sources"])

def coverage_summary(question_card_ids: Iterable[str], diagram_card_groups: Iterable[Iterable[str]]) -> dict[str, object]:
    question_cards = tuple(question_card_ids); diagrams = tuple(tuple(group) for group in diagram_card_groups)
    counts = {STATUS_VERIFIED:0, STATUS_PARTIAL:0, STATUS_PENDING:0}
    for item in CARD_PROVENANCE.values(): counts[str(item["status"])] += 1
    return {"sources":len(SOURCES), "cards":len(CARD_PROVENANCE), "questions":sum(card in CARD_PROVENANCE for card in question_cards), "question_total":len(question_cards), "results":len(RESULT_PROVENANCE), "diagrams":sum(all(card in CARD_PROVENANCE for card in group) for group in diagrams), "diagram_total":len(diagrams), "status_counts":counts}

def validate_provenance(expected_result_ids: set[str]) -> None:
    if set(RESULT_PROVENANCE) != expected_result_ids: raise ValueError("内容审校清单未完整覆盖故障结论")
    for source in SOURCES.values():
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password: raise ValueError("资料链接必须是无身份信息的HTTPS地址")
        if not all(source.get(field) for field in ("title","publisher","type","scope","checked_on")): raise ValueError("资料元数据不完整")
    for group in (CARD_PROVENANCE, RESULT_PROVENANCE):
        for item in group.values():
            if not item["principle"] or item["status"] not in {STATUS_VERIFIED,STATUS_PARTIAL,STATUS_PENDING} or not item["sources"]: raise ValueError("内容审校项不完整")
            if any(source_id not in SOURCES for source_id in item["sources"]): raise ValueError("内容审校项引用了未知资料")
