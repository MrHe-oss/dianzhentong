"""电诊通 Streamlit 教学原型。"""

from __future__ import annotations

import secrets

import streamlit as st

from dianzhentong.config import load_config
from dianzhentong.engine import (
    DEFAULT_EXPERIMENT_ID,
    DiagnosticSession,
    KnowledgeBase,
    KnowledgeError,
    SessionError,
)
from dianzhentong.report import DISCLAIMER, build_report
from dianzhentong.storage import ResilientPracticeRepository, choose_weak_scenario


st.set_page_config(page_title="电诊通", page_icon="⚡", layout="centered")

config = load_config()


@st.cache_resource
def create_repository(path: str) -> ResilientPracticeRepository:
    return ResilientPracticeRepository(path)

catalog = KnowledgeBase.catalog()
saved_state = st.session_state.get("diagnostic_state", {})
selected_experiment_id = saved_state.get(
    "experiment_id", st.session_state.get("selected_experiment_id", DEFAULT_EXPERIMENT_ID)
)
if selected_experiment_id not in catalog:
    selected_experiment_id = DEFAULT_EXPERIMENT_ID
    st.session_state.pop("diagnostic_state", None)
    st.session_state.selected_experiment_id = selected_experiment_id
knowledge = KnowledgeBase(selected_experiment_id)
repository = create_repository(str(config.storage_path))
scenario_ids = list(knowledge.scenario_ids)


def get_session() -> DiagnosticSession:
    if "diagnostic_state" not in st.session_state:
        return DiagnosticSession(knowledge)
    return DiagnosticSession.from_dict(knowledge, st.session_state.diagnostic_state)


def save_session(session: DiagnosticSession) -> None:
    st.session_state.diagnostic_state = session.to_dict()


def reset_all() -> None:
    for key in list(st.session_state):
        del st.session_state[key]


def set_stage(stage: int) -> None:
    st.session_state.stage = stage


def start_practice(scenario_id: str) -> None:
    new_session = DiagnosticSession(knowledge)
    new_session.start(True, scenario_id=scenario_id)
    save_session(new_session)
    st.session_state.practice_mode = "随机故障练习"
    set_stage(5)


def start_random_practice() -> None:
    start_practice(secrets.choice(scenario_ids))


def start_weak_practice() -> None:
    stats = repository.fault_stats(scenario_ids, experiment_id=knowledge.experiment_id)
    start_practice(choose_weak_scenario(stats, scenario_ids))


def render_markdown_table(columns: list[str], rows: list[dict[str, object]]) -> None:
    """渲染小型只读表格，避免依赖本机 PyArrow/NumPy 二进制组合。"""
    if not rows:
        st.caption("暂无记录")
        return

    def safe(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(safe(row.get(column, "")) for column in columns) + " |" for row in rows]
    st.markdown("\n".join([header, divider, *body]))


if "stage" not in st.session_state:
    st.session_state.stage = 1

stage = st.session_state.stage
session = get_session()

st.title("⚡ 电诊通")
st.caption(f"电气控制故障排查教学原型 · 公开测试版 v{config.version}")

steps = ["产品说明", "选择实验", "故障现象", "安全确认", "逐步排查", "诊断报告"]
if stage <= len(steps):
    st.progress(stage / len(steps), text=f"第 {stage} 步：{steps[stage - 1]}")

with st.sidebar:
    st.subheader("当前范围")
    st.write(knowledge.experiment["name"])
    st.caption(knowledge.experiment["scope"])
    st.warning("仅限教学模拟，不可用于真实设备诊断。")
    if config.issues_url:
        st.link_button("💬 提交问题或建议", config.issues_url, use_container_width=True)
    if st.button("📊 学习中心", use_container_width=True):
        set_stage(7)
        st.rerun()
    if session.history:
        st.metric("已记录检查", len(session.history))
        with st.expander("查看检查记录"):
            for item in session.history:
                st.write(f"{item['order']}. {item['object']}：{item['answer']}")
    if st.button("重新开始", use_container_width=True):
        reset_all()
        st.rerun()

if stage == 1:
    st.subheader("产品说明")
    st.success("🧪 公开测试版：欢迎体验两个电机控制故障排查实验。")
    st.info("本原型帮助学生学习排查思路，不连接设备，也不提供真实带电操作指导。")
    st.write("你将阅读模拟状态，依次回答“正常、异常、不确定”，系统依据固定故障树生成过程记录。")
    if config.storage_is_temporary or not repository.persistent:
        st.warning("当前为临时数据模式：练习成绩可能在服务休眠、重启或更新后丢失，请勿将其作为长期学习档案。")
    else:
        st.caption("当前为本机持久化模式，学习记录保存在本机SQLite数据库中。")
    with st.expander("隐私与数据说明"):
        st.write("本应用不要求姓名、邮箱或账号，不主动收集个人身份信息。")
        st.write("练习记录只包含实验、诊断结果、得分、错题节点和完成时间。")
        st.write("公开测试版不承诺云端练习记录长期保存。请勿提交真实设备、单位或人员的敏感信息。")
    if config.issues_url:
        st.link_button("提交测试反馈", config.issues_url)
    st.warning(DISCLAIMER)
    if st.button("我已了解，查看实验", type="primary"):
        set_stage(2)
        st.rerun()

elif stage == 2:
    st.subheader("选择实验")
    experiment_options = list(catalog)
    chosen_experiment_id = st.radio(
        "可用实验",
        experiment_options,
        index=experiment_options.index(knowledge.experiment_id),
        format_func=lambda item: catalog[item]["name"],
    )
    mode = st.radio(
        "练习方式",
        ["随机故障练习", "自由诊断演示"],
        help="随机练习会秘密抽取一种故障并在结束后评分；自由演示保留首版流程。",
    )
    st.session_state.practice_mode = mode
    st.caption("每个实验拥有独立故障题库、薄弱项和学习统计。")
    col1, col2 = st.columns(2)
    if col1.button("返回"):
        set_stage(1)
        st.rerun()
    if col2.button("选择此实验", type="primary"):
        st.session_state.selected_experiment_id = chosen_experiment_id
        st.session_state.pop("diagnostic_state", None)
        set_stage(3)
        st.rerun()

elif stage == 3:
    st.subheader("故障现象")
    if st.session_state.get("practice_mode", "随机故障练习") == "随机故障练习":
        st.info("系统将在开始时随机生成一种故障现象和对应故障。")
        for symptom in knowledge.symptoms.values():
            st.write(f"- {symptom}")
        st.session_state.selected_symptom_id = knowledge.default_symptom_id
    else:
        symptom_ids = list(knowledge.symptoms)
        selected_symptom_id = st.radio(
            "请选择模拟故障现象",
            symptom_ids,
            format_func=lambda item: knowledge.symptoms[item],
        )
        st.session_state.selected_symptom_id = selected_symptom_id
    st.write(f"限定任务：从本实验的 {len(scenario_ids)} 类常见原因中进行排查；若证据不足，系统将明确给出不确定结果。")
    col1, col2 = st.columns(2)
    if col1.button("返回"):
        set_stage(2)
        st.rerun()
    if col2.button("开始安全确认", type="primary"):
        set_stage(4)
        st.rerun()

elif stage == 4:
    st.subheader("安全确认")
    st.warning(knowledge.data["safety_notice"])
    safe_simulation = st.checkbox("我确认本次只使用网页中的模拟资料")
    safe_no_power = st.checkbox("我不会依据本工具进行带电测量、拆线或送电")
    safe_education = st.checkbox("我理解结果仅供教学，不能用于真实设备诊断")
    all_safe = safe_simulation and safe_no_power and safe_education
    col1, col2 = st.columns(2)
    if col1.button("返回"):
        set_stage(3)
        st.rerun()
    if col2.button("确认并开始", type="primary", disabled=not all_safe):
        try:
            scenario_id = None
            if st.session_state.get("practice_mode", "随机故障练习") == "随机故障练习":
                scenario_id = secrets.choice(scenario_ids)
            session.start(
                True,
                scenario_id=scenario_id,
                symptom_id=st.session_state.get("selected_symptom_id", knowledge.default_symptom_id),
            )
            save_session(session)
            set_stage(5)
            st.rerun()
        except SessionError as exc:
            st.error(str(exc))

elif stage == 5:
    st.subheader("逐步排查")
    if not session.safety_confirmed:
        st.error("安全确认状态已丢失，请重新确认。")
        if st.button("返回安全确认"):
            set_stage(4)
            st.rerun()
    elif session.is_complete:
        set_stage(6)
        st.rerun()
    else:
        node = session.current_node
        assert node is not None
        st.error(f"故障现象：{session.symptom}")
        st.caption(f"检查 {node['order']} / {len(knowledge.nodes)} · {node['object']}")
        st.markdown(f"### {node['question']}")
        if session.scenario_observation:
            st.info(f"**本题模拟资料**\n\n{session.scenario_observation}")
        st.write(f"**模拟检查方法：** {node['offline_check']}")
        st.write(f"**预期状态：** {node['expected']}")
        st.warning(node["safety"])
        with st.expander("术语解释"):
            st.write(node["term_help"])

        answer = st.radio("选择观察结果", knowledge.answers, index=None, key=f"answer_{len(session.history)}")
        if answer == "不确定":
            st.info("不确定不会产生诊断结论。请阅读术语解释和模拟资料后重新选择；本次回答仍会写入记录。")
        col1, col2 = st.columns(2)
        if col1.button("返回上一步", disabled=not session.history):
            session.go_back()
            save_session(session)
            st.rerun()
        if col2.button("提交结果", type="primary", disabled=answer is None):
            session.answer(answer)
            save_session(session)
            if session.is_complete:
                set_stage(6)
            st.rerun()

elif stage == 6:
    st.subheader("诊断报告")
    if not session.is_complete or session.result is None:
        st.error("诊断尚未完成。")
        if st.button("返回排查"):
            set_stage(5)
            st.rerun()
    else:
        result = session.result
        if session.scenario_id is not None:
            repository.save(session.to_practice_record())
        st.write(f"**实验：** {knowledge.experiment['name']}")
        st.write(f"**故障现象：** {session.symptom}")
        if knowledge.is_inconclusive(session.result_id or ""):
            st.warning(result["cause"])
        else:
            st.success(result["cause"])
        st.write(result["explanation"])
        st.write(f"**证据：** {result['evidence']}")
        st.write(f"**依据来源：** {result['source']}")
        st.write(f"**可信度：** {result['confidence']}")

        if session.scenario_result is not None:
            correct, total = session.score
            matched = session.result_id == session.scenario_id
            st.divider()
            st.subheader("练习评分")
            col1, col2 = st.columns(2)
            col1.metric("有效判断得分", f"{correct}/{total}")
            col2.metric("诊断匹配", "正确" if matched else "需要复盘")
            st.write(f"**本题预设故障：** {session.scenario_result['cause']}")
            if matched:
                st.success("你找到的故障与随机场景一致。")
            else:
                st.warning("你的诊断与预设故障不一致。请比较检查记录中的模拟状态卡和判断。")
            wrong_labels = [knowledge.nodes[node_id]["object"] for node_id in session.wrong_nodes]
            if wrong_labels:
                st.write("**本次错题：** " + "、".join(wrong_labels))
            elif session.uncertain_count:
                st.write(f"**不确定回答：** {session.uncertain_count} 次；这些回答不计分。")
            else:
                st.write("**本次错题：** 无")

        with st.expander("完整检查记录", expanded=True):
            for index, item in enumerate(session.history, 1):
                grade = ""
                if item.get("is_correct") is True:
                    grade = " ✅"
                elif item.get("is_correct") is False:
                    grade = f" ❌（应判断为{item['expected_answer']}）"
                st.write(f"{index}. {item['object']} → **{item['answer']}**{grade}")

        report = build_report(session)
        st.download_button(
            "下载文本报告",
            data=report.encode("utf-8"),
            file_name="电诊通_教学诊断报告.txt",
            mime="text/plain",
            type="primary",
        )
        if session.scenario_result is not None:
            col1, col2 = st.columns(2)
            if col1.button("练习薄弱项", use_container_width=True):
                start_weak_practice()
                st.rerun()
            if col2.button("再来一题", use_container_width=True):
                start_random_practice()
                st.rerun()
        st.warning(DISCLAIMER)

elif stage == 7:
    st.subheader("📊 学习中心")
    st.write(f"**当前实验：{knowledge.experiment['name']}**")
    if config.storage_is_temporary:
        st.warning("云端成绩使用临时存储，服务重启或更新后可能清空。")
    if not repository.persistent:
        st.warning("SQLite当前不可用，已切换到内存记录；关闭或重启应用后数据会丢失。")
    summary = repository.summary(experiment_id=knowledge.experiment_id)
    stats = repository.fault_stats(scenario_ids, experiment_id=knowledge.experiment_id)
    recent = repository.recent(10, experiment_id=knowledge.experiment_id)

    if not summary["attempts"]:
        st.info("还没有练习记录。完成一次随机故障练习后，这里会显示学习统计。")
        if st.button("开始第一题", type="primary"):
            start_random_practice()
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        col1.metric("累计练习", summary["attempts"])
        col2.metric("连续诊断正确", summary["current_streak"])
        col3, col4 = st.columns(2)
        col3.metric("诊断正确率", f"{summary['diagnosis_accuracy']:.0%}")
        judgment = summary["judgment_accuracy"]
        col4.metric("判断正确率", f"{judgment:.0%}" if judgment is not None else "暂无")

        st.subheader("各故障掌握情况")
        rows = []
        for scenario_id in scenario_ids:
            item = stats[scenario_id]
            accuracy = item["accuracy"]
            rows.append(
                {
                    "故障": knowledge.results[scenario_id]["cause"],
                    "练习次数": item["attempts"],
                    "诊断正确": item["correct"],
                    "正确率": f"{accuracy:.0%}" if accuracy is not None else "未练习",
                }
            )
        render_markdown_table(["故障", "练习次数", "诊断正确", "正确率"], rows)
        if st.button("练习薄弱项", type="primary"):
            start_weak_practice()
            st.rerun()

        st.subheader("最近10次练习")
        recent_rows = []
        for item in recent:
            recent_rows.append(
                {
                    "时间": item["completed_at"].replace("T", " ")[:19],
                    "预设故障": knowledge.results[item["scenario_id"]]["cause"],
                    "诊断": "正确" if item["matched"] else "错误",
                    "判断得分": f"{item['correct_judgments']}/{item['total_judgments']}",
                    "不确定": item["uncertain_count"],
                }
            )
        render_markdown_table(["时间", "预设故障", "诊断", "判断得分", "不确定"], recent_rows)

        with st.expander("清空学习记录"):
            st.warning("清空后无法恢复，但不会影响故障知识库和应用功能。")
            confirm_clear = st.checkbox("我确认删除全部本地练习记录")
            if st.button("永久清空", disabled=not confirm_clear):
                repository.clear(confirmed=True)
                st.success("学习记录已清空。")
                st.rerun()
