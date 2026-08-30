"""生成可下载的纯文本教学诊断报告。"""

from __future__ import annotations

from datetime import datetime

from .engine import DiagnosticSession
from .course import experiment_learning_record
from .insights import insight_for_result
from .learning import review_cards
from .provenance import provenance_for_result, resolved_sources


DISCLAIMER = (
    "本报告仅用于教学模拟，不是对真实设备的诊断结论。不得替代持证电工、"
    "设备说明书或现场安全规程，禁止据此进行带电测量、拆线或送电操作。"
)


def build_report(
    session: DiagnosticSession,
    generated_at: datetime | None = None,
    include_score: bool = True,
) -> str:
    if not session.is_complete or session.result is None:
        raise ValueError("诊断完成后才能生成报告")
    moment = generated_at or datetime.now()
    experiment = session.knowledge.experiment
    result = session.result
    insight = insight_for_result(session.result_id)
    provenance = provenance_for_result(session.result_id)
    lines = [
        "电诊通｜教学诊断报告",
        "=" * 28,
        f"生成时间：{moment:%Y-%m-%d %H:%M}",
        f"实验：{experiment['name']}",
        f"故障现象：{session.symptom}",
        "安全确认：已确认仅使用模拟资料，不操作真实带电设备",
        "",
        "本次结论",
        "-" * 28,
        f"最可能原因：{result['cause']}",
        f"解释：{result['explanation']}",
        f"证据：{result['evidence']}",
        f"依据来源：{result['source']}",
        f"可信度：{result['confidence']}",
    ]
    if insight:
        lines.extend(
            [
                "",
                "学习解释",
                "-" * 28,
                f"为什么这样判断：{insight['why']}",
                f"容易混淆：{insight['confusion']}",
                f"记忆提示：{insight['memory']}",
            ]
        )
    if provenance:
        lines.extend(
            [
                "",
                "内容来源与审校状态",
                "-" * 28,
                f"参考原理：{provenance['principle']}",
                f"审校状态：{provenance['status']}",
            ]
        )
        for source in resolved_sources(provenance):
            lines.append(f"- {source['title']}（{source['type']}）：{source['url']}")
    if session.scenario_result is not None and include_score:
        correct, total = session.score
        matched = session.result_id == session.scenario_id
        lines.extend(
            [
                "",
                "练习得分",
                "-" * 28,
                f"练习预设故障：{session.scenario_result['cause']}",
                f"诊断是否匹配：{'是' if matched else '否'}",
                f"有效判断得分：{correct}/{total}",
                "",
                "错因分析",
                "-" * 28,
            ]
        )
        wrong_entries = [item for item in session.history if item.get("is_correct") is False]
        if wrong_entries:
            for entry in wrong_entries:
                node = session.knowledge.nodes[entry["node_id"]]
                expected_answer = entry["expected_answer"]
                lines.extend(
                    [
                        f"- {entry['object']}",
                        f"  你的判断：{entry['answer']}；正确判断：{expected_answer}",
                        f"  模拟依据：{node['scenario_observations'][expected_answer]}",
                    ]
                )
        else:
            lines.append("- 判断过程正确，无错误判断。")

    if session.scenario_result is not None:
        path = session.recommended_path()
        assert path is not None
        lines.extend(["", "推荐排查顺序", "-" * 28])
        for index, step in enumerate(path["steps"], 1):
            lines.extend(
                [
                    f"{index}. {step['object']} → {step['answer']}",
                    f"   模拟依据：{step['observation']}",
                ]
            )
        lines.append(f"最终故障：{path['cause']}")

    lines.extend(["", "完整检查记录", "-" * 28])
    for index, entry in enumerate(session.history, 1):
        lines.extend(
            [
                f"{index}. {entry['object']}",
                f"   问题：{entry['question']}",
                f"   回答：{entry['answer']}",
                f"   预期：{entry['expected']}",
            ]
        )

    core_cards = review_cards(item["node_id"] for item in session.history)
    lines.extend(["", "核心知识与下一步", "-" * 28])
    lines.append("本次涉及：" + ("、".join(item["title"] for item in core_cards) if core_cards else "故障树证据判断"))
    first_wrong = next((item for item in session.history if item.get("is_correct") is False), None)
    if first_wrong:
        lines.append(
            f"最早偏离：{first_wrong['object']}；你的判断={first_wrong['answer']}；"
            f"推荐判断={first_wrong['expected_answer']}"
        )
        suggested = review_cards([first_wrong["node_id"]])
        lines.append("下一步建议：复习" + "、".join(item["title"] for item in suggested) + "后再练习同类故障。")
    elif session.scenario_result is not None:
        lines.append("路径表现：判断顺序未偏离本题推荐路径。")
        lines.append("下一步建议：继续完成同实验随机练习，巩固不同故障现象。")

    learning_record = experiment_learning_record(session)
    lines.extend(
        [
            "",
            "实验学习记录",
            "-" * 28,
            f"实验目的：{learning_record['purpose']}",
            f"实验结果：{learning_record['result']}",
            f"关键检查：{' → '.join(learning_record['steps'])}",
            "复盘问题：",
        ]
    )
    lines.extend(f"- {question}" for question in learning_record["reflection"])

    lines.extend(["", "已排除项目", "-" * 28])
    lines.extend(f"- {item}" for item in session.eliminated)
    if not session.eliminated:
        lines.append("- 无")
    lines.extend(["", "复盘问题", "-" * 28])
    lines.extend(f"- {question}" for question in session.knowledge.data["reflection_questions"])
    lines.extend(["", "安全声明", "-" * 28, DISCLAIMER])
    return "\n".join(lines)
