"""生成可下载的纯文本教学诊断报告。"""

from __future__ import annotations

from datetime import datetime

from .engine import DiagnosticSession


DISCLAIMER = (
    "本报告仅用于教学模拟，不是对真实设备的诊断结论。不得替代持证电工、"
    "设备说明书或现场安全规程，禁止据此进行带电测量、拆线或送电操作。"
)


def build_report(session: DiagnosticSession, generated_at: datetime | None = None) -> str:
    if not session.is_complete or session.result is None:
        raise ValueError("诊断完成后才能生成报告")
    moment = generated_at or datetime.now()
    experiment = session.knowledge.experiment
    result = session.result
    lines = [
        "电诊通｜教学诊断报告",
        "=" * 28,
        f"生成时间：{moment:%Y-%m-%d %H:%M}",
        f"实验：{experiment['name']}",
        f"故障现象：{session.symptom}",
        "安全确认：已确认仅使用模拟资料，不操作真实带电设备",
        "",
        "检查过程",
        "-" * 28,
    ]
    for index, entry in enumerate(session.history, 1):
        lines.extend(
            [
                f"{index}. {entry['object']}",
                f"   问题：{entry['question']}",
                f"   回答：{entry['answer']}",
                f"   预期：{entry['expected']}",
            ]
        )
    lines.extend(
        [
            "",
            "诊断结果",
            "-" * 28,
            f"最可能原因：{result['cause']}",
            f"解释：{result['explanation']}",
            f"证据：{result['evidence']}",
            f"依据来源：{result['source']}",
            f"可信度：{result['confidence']}",
            "",
            "已排除项目",
            "-" * 28,
        ]
    )
    if session.scenario_result is not None:
        correct, total = session.score
        matched = session.result_id == session.scenario_id
        lines.extend(
            [
                f"练习预设故障：{session.scenario_result['cause']}",
                f"诊断是否匹配：{'是' if matched else '否'}",
                f"有效判断得分：{correct}/{total}",
                "",
            ]
        )
    lines.extend(f"- {item}" for item in session.eliminated)
    if not session.eliminated:
        lines.append("- 无")
    lines.extend(["", "复盘问题", "-" * 28])
    lines.extend(f"- {question}" for question in session.knowledge.data["reflection_questions"])
    lines.extend(["", "安全声明", "-" * 28, DISCLAIMER])
    return "\n".join(lines)
