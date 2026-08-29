"""教学规则的来源与审校状态。"""

from __future__ import annotations


SOURCES = {
    "abb_dol": {
        "title": "ABB DRAF enclosed DOL starter",
        "url": "https://new.abb.com/low-voltage/nl/producten/motorbeveiligingen-en-besturingen/starting-solutions/draf-enclosed-dol-starter",
        "type": "厂家产品与技术资料",
    },
    "abb_motor_control": {
        "title": "ABB Manual motor starters, contactors and overload relays panorama",
        "url": "https://library.e.abb.com/public/4345418d61514245af8fa8c5f70adf7d/1SBC100191L0203_MMS_Contactors_Overload_Relays_Panorama.pdf",
        "type": "厂家产品技术手册",
    },
    "abb_contactor": {
        "title": "ABB Open NEMA contactors and motor starters",
        "url": "https://new.abb.com/low-voltage/products/motor-protection/starting-solutions/open-nema-contactors-%28cr305%29",
        "type": "厂家接触器技术资料",
    },
    "schneider_interlock": {
        "title": "Schneider Electric LE2GBK reversing starter FAQ",
        "url": "https://www.se.com/uk/en/faqs/FA139509/",
        "type": "厂家正反转启动器技术资料",
    },
}


COMMON_STATUS = "已与厂家资料核对通用原理；教学排查顺序仍待专业人员复核"
TEXTBOOK_PENDING = "通用原理已录入；按钮触点与教学排查顺序待补充教材章节页码并由专业人员复核"

RESULT_PROVENANCE: dict[str, dict[str, object]] = {
    "cause_control_power": {"principle": "控制电源是接触器控制逻辑的前置条件。", "sources": ("abb_dol", "abb_contactor"), "status": COMMON_STATUS},
    "cause_fuse": {"principle": "保护与通断元件属于电动机启动控制组合的一部分。", "sources": ("abb_dol", "abb_motor_control"), "status": COMMON_STATUS},
    "cause_thermal": {"principle": "过载继电器用于电动机过载保护，保护状态可影响启动控制。", "sources": ("abb_motor_control", "abb_dol"), "status": COMMON_STATUS},
    "cause_stop": {"principle": "停止按钮常闭触点作为启停控制的通用教学逻辑。", "sources": ("abb_contactor",), "status": TEXTBOOK_PENDING},
    "cause_start": {"principle": "启动按钮常开触点用于提供启动信号的通用教学逻辑。", "sources": ("abb_contactor",), "status": TEXTBOOK_PENDING},
    "cause_coil": {"principle": "磁力接触器用于控制交流电动机的启动和停止。", "sources": ("abb_contactor", "abb_motor_control"), "status": COMMON_STATUS},
    "fr_cause_fuse": {"principle": "正反转启动器包含两个方向的接触器控制逻辑及共用保护条件。", "sources": ("schneider_interlock", "abb_motor_control"), "status": COMMON_STATUS},
    "fr_cause_thermal": {"principle": "过载保护是电动机正反转启动组合的公共保护环节。", "sources": ("abb_motor_control", "schneider_interlock"), "status": COMMON_STATUS},
    "fr_cause_stop": {"principle": "停止按钮常闭触点作为两个方向的公共停止条件。", "sources": ("schneider_interlock",), "status": TEXTBOOK_PENDING},
    "fr_cause_forward_button": {"principle": "正转启动按钮提供正转支路启动信号。", "sources": ("schneider_interlock",), "status": TEXTBOOK_PENDING},
    "fr_cause_reverse_button": {"principle": "反转启动按钮提供反转支路启动信号。", "sources": ("schneider_interlock",), "status": TEXTBOOK_PENDING},
    "fr_cause_forward_coil": {"principle": "正转接触器线圈对应正转方向的接触器动作条件。", "sources": ("abb_contactor", "schneider_interlock"), "status": COMMON_STATUS},
    "fr_cause_reverse_coil": {"principle": "反转接触器线圈对应反转方向的接触器动作条件。", "sources": ("abb_contactor", "schneider_interlock"), "status": COMMON_STATUS},
    "fr_cause_interlock": {"principle": "正反转启动器使用接触器常闭辅助触点实现电气互锁。", "sources": ("schneider_interlock", "abb_contactor"), "status": COMMON_STATUS},
}


def provenance_for_result(result_id: str | None) -> dict[str, object] | None:
    return RESULT_PROVENANCE.get(result_id or "")


def resolved_sources(item: dict[str, object]) -> tuple[dict[str, str], ...]:
    return tuple(SOURCES[source_id] for source_id in item["sources"])


def validate_provenance(expected_result_ids: set[str]) -> None:
    if set(RESULT_PROVENANCE) != expected_result_ids:
        raise ValueError("内容审校清单未完整覆盖故障结论")
    for item in RESULT_PROVENANCE.values():
        if not item["principle"] or not item["status"] or not item["sources"]:
            raise ValueError("内容审校项不完整")
        if any(source_id not in SOURCES for source_id in item["sources"]):
            raise ValueError("内容审校项引用了未知资料")
