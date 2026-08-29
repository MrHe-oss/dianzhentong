"""电诊通 Streamlit 教学原型。"""
from __future__ import annotations

import secrets
import streamlit as st

from dianzhentong.config import load_config
from dianzhentong.engine import DEFAULT_EXPERIMENT_ID, DiagnosticSession, KnowledgeBase, SessionError
from dianzhentong.report import DISCLAIMER, build_report
from dianzhentong.storage import ResilientPracticeRepository, choose_weak_scenario

UI_STATE_VERSION = "0.7"
st.set_page_config(page_title="电诊通", page_icon="⚡", layout="centered")
st.markdown("""
<style>
.block-container{max-width:920px;padding-top:2rem;padding-bottom:4rem}.dzt-hero{padding:1.5rem 1.6rem;border-radius:20px;color:white;background:linear-gradient(135deg,#1d4ed8,#3b82f6);margin-bottom:1.2rem}.dzt-hero h1{margin:0;font-size:2.25rem}.dzt-hero p{margin:.45rem 0 0;opacity:.9}.dzt-card{min-height:168px;padding:1.1rem 1.2rem;border:1px solid #dbeafe;border-radius:16px;background:#f8fbff;margin-bottom:.75rem}.dzt-card h3{color:#172033;margin:0 0 .5rem;font-size:1.08rem}.dzt-card p{margin:.25rem 0;color:#475569}.dzt-step{padding:.8rem 1rem;border-left:4px solid #2563eb;border-radius:0 12px 12px 0;background:#eff6ff;margin:.5rem 0}div.stButton>button,div.stDownloadButton>button{border-radius:10px;min-height:2.8rem}[data-testid="stMetric"]{background:#f8fafc;border:1px solid #e2e8f0;padding:.8rem;border-radius:12px}
@media(max-width:640px){.block-container{padding:1rem .85rem 3rem}.dzt-hero{padding:1.1rem;border-radius:15px}.dzt-hero h1{font-size:1.75rem}.dzt-card{min-height:0}[data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.6rem}[data-testid="stHorizontalBlock"]>div{min-width:100%}}
</style>""", unsafe_allow_html=True)

if st.session_state.get("ui_state_version") != UI_STATE_VERSION:
    for state_key in list(st.session_state):
        del st.session_state[state_key]
    st.session_state.ui_state_version = UI_STATE_VERSION

config = load_config()

@st.cache_resource
def create_repository(path: str) -> ResilientPracticeRepository:
    return ResilientPracticeRepository(path)

catalog = KnowledgeBase.catalog()
saved_state = st.session_state.get("diagnostic_state", {})
selected_experiment_id = saved_state.get("experiment_id", st.session_state.get("selected_experiment_id", DEFAULT_EXPERIMENT_ID))
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

def save_session(current: DiagnosticSession) -> None:
    st.session_state.diagnostic_state = current.to_dict()

def reset_all() -> None:
    for state_key in list(st.session_state):
        del st.session_state[state_key]

def set_stage(stage: int) -> None:
    st.session_state.stage = stage

def start_practice(scenario_id: str) -> None:
    new_session = DiagnosticSession(knowledge)
    new_session.start(True, scenario_id=scenario_id)
    save_session(new_session)
    st.session_state.practice_mode = "随机故障练习"
    set_stage(3)

def start_random_practice() -> None:
    start_practice(secrets.choice(scenario_ids))

def start_weak_practice() -> None:
    stats = repository.fault_stats(scenario_ids, experiment_id=knowledge.experiment_id)
    start_practice(choose_weak_scenario(stats, scenario_ids))

def render_markdown_table(columns: list[str], rows: list[dict[str, object]]) -> None:
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
if stage not in {1, 2, 3, 4, 5}:
    stage = 1
    st.session_state.stage = 1
    st.session_state.pop("diagnostic_state", None)
session = get_session()

st.markdown(f'<div class="dzt-hero"><h1>⚡ 电诊通</h1><p>电气控制故障排查教学原型 · 公开测试版 v{config.version}</p></div>', unsafe_allow_html=True)
steps = ["选择实验", "安全确认", "逐步排查", "学习报告"]
if stage <= 4:
    st.progress(stage / 4, text=f"第 {stage} 步 / 4：{steps[stage - 1]}")

with st.sidebar:
    st.subheader("当前实验")
    st.write(knowledge.experiment["name"])
    st.caption(knowledge.experiment["scope"])
    st.warning("仅限教学模拟，不可用于真实设备诊断。")
    if config.issues_url:
        st.link_button("🛠️ 程序故障或专业纠错", config.issues_url, use_container_width=True)
    if st.button("📊 学习中心", use_container_width=True):
        set_stage(5); st.rerun()
    if session.history:
        st.metric("已记录检查", len(session.history))
        with st.expander("查看检查记录"):
            for item in session.history:
                st.write(f"{item['order']}. {item['object']}：{item['answer']}")
    if st.button("重新开始", use_container_width=True):
        reset_all(); st.rerun()

if stage == 1:
    st.subheader("选择一个学习实验")
    st.caption("选好实验和练习方式，下一步完成安全确认后即可开始。")
    experiment_options = list(catalog)
    card_columns = st.columns(len(experiment_options))
    for column, experiment_id in zip(card_columns, experiment_options):
        experiment_knowledge = KnowledgeBase(experiment_id)
        experiment = catalog[experiment_id]
        symptoms = "、".join(experiment_knowledge.symptoms.values())
        with column:
            st.markdown(f'<div class="dzt-card"><h3>{experiment["name"]}</h3><p><b>{len(experiment_knowledge.scenario_ids)} 类</b>模拟故障</p><p>{experiment["scope"]}</p><p><small>现象：{symptoms}</small></p></div>', unsafe_allow_html=True)
    chosen_experiment_id = st.radio("实验", experiment_options, index=experiment_options.index(knowledge.experiment_id), format_func=lambda item: catalog[item]["name"], horizontal=True, label_visibility="collapsed")
    mode = st.segmented_control("练习方式", ["随机故障练习", "自由诊断演示"], default=st.session_state.get("practice_mode", "随机故障练习"), help="随机练习会隐藏一种故障并自动评分；自由诊断用于探索固定规则。") or "随机故障练习"
    chosen_knowledge = KnowledgeBase(chosen_experiment_id)
    selected_symptom_id = chosen_knowledge.default_symptom_id
    if mode == "自由诊断演示":
        symptom_ids = list(chosen_knowledge.symptoms)
        selected_symptom_id = st.radio("选择模拟故障现象", symptom_ids, format_func=lambda item: chosen_knowledge.symptoms[item])
    else:
        st.info("系统会随机生成故障和对应现象；完成后显示评分与推荐排查顺序。")
    with st.expander("使用范围与隐私说明"):
        st.write("应用只读取网页内的模拟资料，不连接设备，也不提供真实带电操作指导。")
        st.write("应用不要求姓名、邮箱或账号；练习记录只包含实验、结果、得分和时间。")
        if config.storage_is_temporary or not repository.persistent:
            st.write("当前云端成绩为临时数据，服务休眠、重启或更新后可能丢失。")
    st.warning(DISCLAIMER)
    if st.button("继续安全确认", type="primary", use_container_width=True):
        st.session_state.selected_experiment_id = chosen_experiment_id
        st.session_state.practice_mode = mode
        st.session_state.selected_symptom_id = selected_symptom_id
        st.session_state.pop("diagnostic_state", None)
        set_stage(2); st.rerun()

elif stage == 2:
    st.subheader("开始前的安全确认")
    st.info(f"已选择：{knowledge.experiment['name']} · {st.session_state.get('practice_mode', '随机故障练习')}")
    st.warning(knowledge.data["safety_notice"])
    safe_simulation = st.checkbox("我确认本次只使用网页中的模拟资料")
    safe_no_power = st.checkbox("我不会依据本工具进行带电测量、拆线或送电")
    safe_education = st.checkbox("我理解结果仅供教学，不能用于真实设备诊断")
    if st.button("返回修改实验", use_container_width=True):
        set_stage(1); st.rerun()
    if st.button("确认并开始排查", type="primary", disabled=not (safe_simulation and safe_no_power and safe_education), use_container_width=True):
        try:
            scenario_id = secrets.choice(scenario_ids) if st.session_state.get("practice_mode", "随机故障练习") == "随机故障练习" else None
            session.start(True, scenario_id=scenario_id, symptom_id=st.session_state.get("selected_symptom_id", knowledge.default_symptom_id))
            save_session(session); set_stage(3); st.rerun()
        except SessionError as exc:
            st.error(str(exc))

elif stage == 3:
    st.subheader("逐步排查")
    if not session.safety_confirmed:
        st.error("安全确认状态已丢失，请重新确认。")
        if st.button("返回安全确认"):
            set_stage(2); st.rerun()
    elif session.is_complete:
        set_stage(4); st.rerun()
    else:
        node = session.current_node
        assert node is not None
        st.error(f"当前故障现象：{session.symptom}")
        st.markdown(f"<div class='dzt-step'><b>检查 {node['order']} / {len(knowledge.nodes)}</b><br>{node['object']}</div>", unsafe_allow_html=True)
        st.markdown(f"### {node['question']}")
        if session.scenario_observation:
            st.info(f"**本题模拟资料**\n\n{session.scenario_observation}")
        st.write(f"**模拟检查方法：** {node['offline_check']}")
        st.write(f"**预期状态：** {node['expected']}")
        st.warning(node["safety"])
        with st.expander("术语解释"):
            st.write(node["term_help"])
        answer = st.radio("根据模拟资料选择判断", knowledge.answers, index=None, key=f"answer_{len(session.history)}", horizontal=True)
        if answer == "不确定":
            st.info("请阅读术语解释和模拟资料后重新选择；本次“不确定”仍会写入记录，但不计分。")
        if st.button("返回上一步", disabled=not session.history, use_container_width=True):
            session.go_back(); save_session(session); st.rerun()
        if st.button("提交本步判断", type="primary", disabled=answer is None, use_container_width=True):
            session.answer(answer); save_session(session)
            if session.is_complete:
                set_stage(4)
            st.rerun()

elif stage == 4:
    st.subheader("学习报告")
    if not session.is_complete or session.result is None:
        st.error("诊断尚未完成。")
        if st.button("返回排查"):
            set_stage(3); st.rerun()
    else:
        result = session.result
        if session.scenario_id is not None:
            repository.save(session.to_practice_record())
        st.markdown("### 1. 本次结论")
        st.write(f"**实验：** {knowledge.experiment['name']}")
        st.write(f"**故障现象：** {session.symptom}")
        (st.warning if knowledge.is_inconclusive(session.result_id or "") else st.success)(result["cause"])
        st.write(result["explanation"])
        with st.expander("查看证据、来源与可信度"):
            st.write(f"**证据：** {result['evidence']}")
            st.write(f"**依据来源：** {result['source']}")
            st.write(f"**可信度：** {result['confidence']}")
        if session.scenario_result is not None:
            correct, total = session.score
            matched = session.result_id == session.scenario_id
            st.markdown("### 2. 得分与错因")
            score_columns = st.columns(2)
            score_columns[0].metric("有效判断得分", f"{correct}/{total}")
            score_columns[1].metric("诊断结果", "正确" if matched else "需要复盘")
            st.write(f"**本题预设故障：** {session.scenario_result['cause']}")
            wrong_entries = [item for item in session.history if item.get("is_correct") is False]
            if wrong_entries:
                st.warning("以下判断与本题模拟资料不一致：")
                for entry in wrong_entries:
                    expected_answer = entry["expected_answer"]
                    observation = knowledge.nodes[entry["node_id"]]["scenario_observations"][expected_answer]
                    st.markdown(f"- **{entry['object']}**：你的判断为“{entry['answer']}”，正确判断为“{expected_answer}”。模拟依据：{observation}")
            else:
                st.success("判断过程正确，无错误判断。")
            if session.uncertain_count:
                st.caption(f"本次共有 {session.uncertain_count} 次“不确定”回答，不计入有效判断得分。")
            st.markdown("### 3. 推荐排查顺序")
            path = session.recommended_path()
            assert path is not None
            for index, step in enumerate(path["steps"], 1):
                st.markdown(f"<div class='dzt-step'><b>{index}. {step['object']} → {step['answer']}</b><br><small>{step['observation']}</small></div>", unsafe_allow_html=True)
            st.success(f"推荐路径最终结论：{path['cause']}")
        st.markdown("### 4. 完整检查记录")
        with st.expander("展开本次操作顺序"):
            for index, item in enumerate(session.history, 1):
                grade = " ✅" if item.get("is_correct") is True else (f" ❌（正确判断：{item['expected_answer']}）" if item.get("is_correct") is False else "")
                st.write(f"{index}. {item['object']} → **{item['answer']}**{grade}")
        report = build_report(session)
        st.download_button("下载文本学习报告", data=report.encode("utf-8"), file_name="电诊通_教学诊断报告.txt", mime="text/plain", use_container_width=True)
        if session.scenario_result is not None:
            if st.button("练习薄弱项", type="primary", use_container_width=True):
                start_weak_practice(); st.rerun()
            if st.button("再来一题", use_container_width=True):
                start_random_practice(); st.rerun()
        if st.button("返回实验首页", use_container_width=True):
            st.session_state.pop("diagnostic_state", None); set_stage(1); st.rerun()
        st.warning(DISCLAIMER)

elif stage == 5:
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
        if st.button("开始第一题", type="primary", use_container_width=True):
            start_random_practice(); st.rerun()
    else:
        metrics = st.columns(2); metrics[0].metric("累计练习", summary["attempts"]); metrics[1].metric("连续诊断正确", summary["current_streak"])
        metrics = st.columns(2); metrics[0].metric("诊断正确率", f"{summary['diagnosis_accuracy']:.0%}"); judgment = summary["judgment_accuracy"]; metrics[1].metric("判断正确率", f"{judgment:.0%}" if judgment is not None else "暂无")
        st.subheader("各故障掌握情况")
        rows = []
        for scenario_id in scenario_ids:
            item = stats[scenario_id]; accuracy = item["accuracy"]
            rows.append({"故障": knowledge.results[scenario_id]["cause"], "练习次数": item["attempts"], "诊断正确": item["correct"], "正确率": f"{accuracy:.0%}" if accuracy is not None else "未练习"})
        render_markdown_table(["故障", "练习次数", "诊断正确", "正确率"], rows)
        if st.button("练习薄弱项", type="primary", use_container_width=True):
            start_weak_practice(); st.rerun()
        st.subheader("最近10次练习")
        recent_rows = [{"时间": item["completed_at"].replace("T", " ")[:19], "预设故障": knowledge.results[item["scenario_id"]]["cause"], "诊断": "正确" if item["matched"] else "错误", "判断得分": f"{item['correct_judgments']}/{item['total_judgments']}", "不确定": item["uncertain_count"]} for item in recent]
        render_markdown_table(["时间", "预设故障", "诊断", "判断得分", "不确定"], recent_rows)
        with st.expander("清空学习记录"):
            st.warning("清空后无法恢复，但不会影响故障知识库和应用功能。")
            confirm_clear = st.checkbox("我确认删除全部本地练习记录")
            if st.button("永久清空", disabled=not confirm_clear):
                repository.clear(confirmed=True); st.success("学习记录已清空。"); st.rerun()
    if st.button("返回实验首页", use_container_width=True):
        set_stage(1); st.rerun()
