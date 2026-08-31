"""电诊通 Streamlit 教学原型。"""
from __future__ import annotations

import importlib
import secrets
import streamlit as st

from dianzhentong.backup import (
    BackupValidationError,
    archive_json_bytes,
    build_learning_summary,
    import_archive,
    parse_archive,
    preview_archive,
)
from dianzhentong.assessment import (
    competency_report, course_exam_eligible, course_learning_status,
    review_route, select_course_questions,
)
from dianzhentong.quick_experience import (
    EXPERIENCE_ITEMS, QuickExperienceSession, experience_report,
)

from dianzhentong.config import load_config
from dianzhentong.engine import DEFAULT_EXPERIMENT_ID, DiagnosticSession, KnowledgeBase, SessionError
from dianzhentong.learning import (
    KNOWLEDGE_CARDS,
    REVIEW_STATUS,
    card_for_node,
    cards_for_experiment,
    relationship_steps,
    review_cards,
)
from dianzhentong.diagram_learning import (
    DIAGRAM_CASES, SAFETY_NOTICE, DiagramTrainingSession,
    cases_for_chapter, diagram_lesson_for_chapter,
)
from dianzhentong.course import (
    ALL_CHAPTERS,
    CHAPTERS,
    COURSE,
    COURSES,
    COURSE_CHAPTERS,
    GLOSSARY,
    chapter_by_id,
    chapter_learning_steps,
    chapter_progress,
    course_is_unlocked,
    course_unlock_requirement,
    experiment_learning_record,
    recommended_chapter_action,
)
from dianzhentong.insights import insight_for_result
from dianzhentong.report import DISCLAIMER, build_report
from dianzhentong.progress import calculate_experiment_progress, learning_overview
from dianzhentong.provenance import (
    CARD_PROVENANCE, SOURCES, STATUS_PARTIAL, STATUS_PENDING, STATUS_VERIFIED,
    coverage_summary, provenance_for_card, provenance_for_diagram,
    provenance_for_question, provenance_for_result, resolved_sources,
)
from dianzhentong.quiz import (
    QUESTION_MAP,
    QuizAnswer,
    answer_feedback,
    card_id_for_question,
    make_quiz_record,
    questions_for_chapter,
    select_questions,
    similar_questions,
)
import dianzhentong.storage as storage_module

# Streamlit Cloud 可能在热更新后保留旧模块与缓存对象；升级存储接口时主动刷新。
if not hasattr(storage_module.ResilientPracticeRepository, "diagram_summary"):
    storage_module = importlib.reload(storage_module)

ResilientPracticeRepository = storage_module.ResilientPracticeRepository
choose_weak_scenario = storage_module.choose_weak_scenario
make_learning_activity = storage_module.make_learning_activity
make_diagram_record = storage_module.make_diagram_record

UI_STATE_VERSION = "2.2"
STORAGE_CACHE_VERSION = "2.2-content-provenance-v1"
st.set_page_config(page_title="电诊通", page_icon="⚡", layout="centered")
st.markdown("""
<style>
.block-container{max-width:920px;padding-top:2rem;padding-bottom:4rem}.dzt-hero{padding:1.5rem 1.6rem;border-radius:20px;color:white;background:linear-gradient(135deg,#1d4ed8,#3b82f6);margin-bottom:1.2rem}.dzt-hero h1{margin:0;font-size:2.25rem}.dzt-hero p{margin:.45rem 0 0;opacity:.9}.dzt-card{min-height:168px;padding:1.1rem 1.2rem;border:1px solid #dbeafe;border-radius:16px;background:#f8fbff;margin-bottom:.75rem}.dzt-card h3{color:#172033;margin:0 0 .5rem;font-size:1.08rem}.dzt-card p{margin:.25rem 0;color:#475569}.dzt-step{padding:.8rem 1rem;border-left:4px solid #2563eb;border-radius:0 12px 12px 0;background:#eff6ff;margin:.5rem 0}.dzt-flow{display:flex;align-items:center;flex-wrap:wrap;gap:.45rem;margin:.8rem 0 1rem}.dzt-flow span{padding:.55rem .7rem;border-radius:9px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a}.dzt-flow b{color:#60a5fa}div.stButton>button,div.stDownloadButton>button{border-radius:10px;min-height:2.8rem}[data-testid="stMetric"]{background:#f8fafc;border:1px solid #e2e8f0;padding:.8rem;border-radius:12px}
@media(max-width:640px){.block-container{padding:1rem .85rem 3rem}.dzt-hero{padding:1.1rem;border-radius:15px}.dzt-hero h1{font-size:1.75rem}.dzt-card{min-height:0}[data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.6rem}[data-testid="stHorizontalBlock"]>div{min-width:100%}}
</style>""", unsafe_allow_html=True)

if st.session_state.get("ui_state_version") != UI_STATE_VERSION:
    for state_key in list(st.session_state):
        del st.session_state[state_key]
    st.session_state.ui_state_version = UI_STATE_VERSION

config = load_config()

@st.cache_resource
def create_repository(path: str, cache_version: str) -> ResilientPracticeRepository:
    del cache_version  # 只用于使旧缓存键失效。
    return ResilientPracticeRepository(path)

catalog = KnowledgeBase.catalog()
saved_state = st.session_state.get("diagnostic_state", {})
selected_experiment_id = saved_state.get("experiment_id", st.session_state.get("selected_experiment_id", DEFAULT_EXPERIMENT_ID))
if selected_experiment_id not in catalog:
    selected_experiment_id = DEFAULT_EXPERIMENT_ID
    st.session_state.pop("diagnostic_state", None)
    st.session_state.selected_experiment_id = selected_experiment_id
knowledge = KnowledgeBase(selected_experiment_id)
repository = create_repository(str(config.storage_path), STORAGE_CACHE_VERSION)
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

def mark_exported() -> None:
    from dianzhentong.storage import beijing_now
    st.session_state.last_exported_at = beijing_now().isoformat(timespec="seconds")

def open_knowledge(card_id: str | None = None) -> None:
    if card_id:
        st.session_state.selected_knowledge_card = card_id
    set_stage(6)

def progress_map():
    result = {}
    for experiment_id in catalog:
        experiment_knowledge = KnowledgeBase(experiment_id)
        card_ids = [item["id"] for item in cards_for_experiment(experiment_id)]
        result[experiment_id] = calculate_experiment_progress(
            repository, experiment_id, experiment_knowledge.scenario_ids, card_ids
        )
    return result

def prepare_task(experiment_id: str, mode: str) -> None:
    target = KnowledgeBase(experiment_id)
    st.session_state.selected_experiment_id = experiment_id
    st.session_state.practice_mode = mode
    st.session_state.selected_symptom_id = target.default_symptom_id
    st.session_state.pop("diagnostic_state", None)
    set_stage(2)

def start_chapter_quiz(chapter_id: str, review: bool = False) -> None:
    wrong_ids = repository.wrong_question_ids(chapter_id) if review else []
    selected = select_questions(chapter_id, 5, wrong_ids)
    st.session_state.quiz_state = {
        "chapter_id": chapter_id,
        "mode": "wrong_review" if review else "chapter_quiz",
        "question_ids": [item.id for item in selected],
        "index": 0,
        "answers": [],
        "answered": False,
    }
    set_stage(10)

def start_similar_quiz(question_id: str) -> None:
    question = QUESTION_MAP[question_id]
    related = similar_questions(question_id, 1)
    selected = related or (question,)
    st.session_state.quiz_state = {
        "chapter_id": question.chapter_id, "mode": "similar_review",
        "question_ids": [item.id for item in selected], "index": 0,
        "answers": [], "answered": False,
    }
    set_stage(10)

def start_diagram_training(case_id: str) -> None:
    st.session_state.diagram_training = DiagramTrainingSession(case_id).to_dict()
    st.session_state.last_learning_chapter_id = DIAGRAM_CASES[case_id]["chapter_id"]
    set_stage(13)

def start_course_exam(course_id: str) -> None:
    selected = select_course_questions(course_id, 10)
    st.session_state.course_exam_state = {
        "course_id": course_id, "question_ids": [item.id for item in selected],
        "index": 0, "answers": [],
    }
    set_stage(14)

def start_quick_experience() -> None:
    st.session_state.quick_experience = QuickExperienceSession().to_dict()
    set_stage(16)

def start_comprehensive_training() -> None:
    experiment_id = secrets.choice(list(catalog))
    prepare_task(experiment_id, "综合训练")

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

def render_provenance(item: dict[str, object] | None, label: str = "参考资料与核对状态") -> None:
    if not item:
        st.warning("该内容尚未建立来源映射。")
        return
    with st.expander(label):
        st.write(f"**核对状态：** {item['status']}")
        st.write(f"**参考原理：** {item['principle']}")
        for source in resolved_sources(item):
            st.markdown(f"- [{source['publisher']}｜{source['title']}]({source['url']})")
            st.caption(f"用于核对：{source['scope']} · 最近核对：{source['checked_on']}")
        st.caption("来源仅支持通用原理核对；教学路径不等同于真实设备检修规程。")

if "stage" not in st.session_state:
    st.session_state.stage = 1
stage = st.session_state.stage
if stage not in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17}:
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
    if st.button("📘 知识中心", use_container_width=True):
        open_knowledge(); st.rerun()
    if st.button("📚 内容与资料", use_container_width=True):
        set_stage(17); st.rerun()
    if st.button("🧭 第一次使用", use_container_width=True):
        set_stage(7); st.rerun()
    if st.button("🗺️ 课程地图", use_container_width=True):
        set_stage(1); st.rerun()
    if st.button("📖 电气术语", use_container_width=True):
        set_stage(9); st.rerun()
    if st.button("💾 学习档案备份", use_container_width=True):
        set_stage(12); st.rerun()
    wrong_count = len(repository.wrong_question_ids())
    if wrong_count and st.button(f"📝 错题复习（{wrong_count}）", use_container_width=True):
        wrong_chapter = next((item["id"] for item in ALL_CHAPTERS if repository.wrong_question_ids(item["id"])), CHAPTERS[0]["id"])
        start_chapter_quiz(wrong_chapter, True); st.rerun()
    if session.history:
        st.metric("已记录检查", len(session.history))
        with st.expander("查看检查记录"):
            for item in session.history:
                st.write(f"{item['order']}. {item['object']}：{item['answer']}")
    if st.button("重新开始", use_container_width=True):
        reset_all(); st.rerun()

if stage == 1:
    st.markdown('<div class="dzt-card"><h3>第一次来？先用5分钟体验完整学习流程</h3><p>知识卡 → 识图 → 模拟排查 → 迷你测验 → 学习总结，无需解锁课程。</p></div>', unsafe_allow_html=True)
    if st.button("⚡ 开始5分钟体验", type="primary", use_container_width=True):
        start_quick_experience(); st.rerun()
    if not st.session_state.get("onboarding_seen"):
        st.info("👋 第一次使用？先用1分钟了解如何阅读模拟资料和选择答案。")
        if st.button("开始1分钟新手引导", type="primary", use_container_width=True):
            set_stage(7); st.rerun()
    st.subheader("课程学习地图")
    last_chapter_id = st.session_state.get("last_learning_chapter_id")
    if last_chapter_id in {item["id"] for item in ALL_CHAPTERS}:
        last_chapter = chapter_by_id(last_chapter_id)
        if st.button(f"继续上次学习：{last_chapter['title']}", type="primary", use_container_width=True):
            st.session_state.selected_chapter_id = last_chapter_id
            set_stage(8); st.rerun()
    course_columns = st.columns(len(COURSES))
    for index, course in enumerate(COURSES):
        unlocked = course_is_unlocked(repository, course["id"])
        course_chapters = COURSE_CHAPTERS[course["id"]]
        course_progress = sum(chapter_progress(repository, item).completion for item in course_chapters) / len(course_chapters)
        with course_columns[index]:
            st.markdown(
                f'<div class="dzt-card"><h3>{course["title"]}</h3><p>{course["description"]}</p>'
                f'<p><b>{"已解锁" if unlocked else "待解锁"}</b> · {course_progress:.0%}</p></div>',
                unsafe_allow_html=True,
            )
            if not unlocked:
                st.caption(f"还差：{course_unlock_requirement(course['id'])}。")
            if st.button("进入课程" if unlocked else "完成前一门课程后解锁", key=f"course_{course['id']}", disabled=not unlocked, use_container_width=True):
                st.session_state.selected_course_id = course["id"]; st.rerun()
    selected_course_id = st.session_state.get("selected_course_id", COURSE["id"])
    if selected_course_id not in COURSE_CHAPTERS or not course_is_unlocked(repository, selected_course_id):
        selected_course_id = COURSE["id"]
    selected_course = next(item for item in COURSES if item["id"] == selected_course_id)
    selected_chapters = COURSE_CHAPTERS[selected_course_id]
    st.markdown(f"### {selected_course['title']}")
    st.write(selected_course["description"])
    chapter_states = [(chapter, chapter_progress(repository, chapter)) for chapter in selected_chapters]
    course_completion = sum(item.completion for _, item in chapter_states) / len(chapter_states)
    st.progress(course_completion, text=f"课程完成度 {course_completion:.0%}")
    current_chapter = next((chapter for chapter, item in chapter_states if item.status != "已完成"), selected_chapters[-1])
    if st.button(f"继续学习：{current_chapter['title']}", type="primary", use_container_width=True):
        st.session_state.selected_chapter_id = current_chapter["id"]
        st.session_state.last_learning_chapter_id = current_chapter["id"]
        set_stage(8); st.rerun()
    chapter_columns = st.columns(2)
    for index, (chapter, item) in enumerate(chapter_states):
        with chapter_columns[index % 2]:
            st.markdown(
                f'<div class="dzt-card"><h3>{chapter["title"]}</h3>'
                f'<p>{chapter["goal"]}</p><p><b>{item.status}</b> · {item.completion:.0%}</p></div>',
                unsafe_allow_html=True,
            )
            if st.button("进入本章", key=f"chapter_{chapter['id']}", use_container_width=True):
                st.session_state.selected_chapter_id = chapter["id"]
                st.session_state.last_learning_chapter_id = chapter["id"]
                set_stage(8); st.rerun()
    st.markdown("### 课程综合评测")
    exam_summary = repository.quiz_summary(selected_course_id)
    eligible = course_exam_eligible(repository, selected_course_id)
    if exam_summary["attempts"]:
        st.write(f"已评测 {exam_summary['attempts']} 次 · 最好成绩 {exam_summary['best_score']:.0%} · {'已完成' if exam_summary['passed_count'] else '待提高'}")
    elif not eligible:
        st.caption("通过本课程全部章节测验后开放；每次10题，达到70%完成课程评测。")
    if st.button("开始课程综合评测", type="primary", disabled=not eligible,
                 key=f"course_exam_{selected_course_id}", use_container_width=True):
        start_course_exam(selected_course_id); st.rerun()
    st.divider()
    current_progress = progress_map()
    overview = learning_overview(repository, current_progress)
    tasks = overview["tasks"]
    recommended_id = overview["recommended_experiment_id"]
    st.subheader("今日学习任务 · 约10分钟")
    st.progress(tasks["completion"], text=f"今日完成 {tasks['completed_count']} / 3 项 · 连续学习 {overview['streak']} 天")
    task_columns = st.columns(3)
    task_columns[0].metric("知识卡", "已完成" if tasks["knowledge"] else "0 / 1")
    task_columns[1].metric("引导学习", "已完成" if tasks["guided"] else "0 / 1")
    task_columns[2].metric("随机练习", f"{min(tasks['random_practices'], 2)} / 2")
    if not tasks["knowledge"]:
        if st.button("开始今日知识卡", use_container_width=True):
            target_cards = cards_for_experiment(recommended_id)
            learned = repository.learned_cards(recommended_id)
            target = next((item for item in target_cards if item["id"] not in learned), target_cards[0])
            st.session_state.selected_experiment_id = recommended_id
            st.session_state.selected_knowledge_card = target["id"]
            open_knowledge(target["id"]); st.rerun()
    if not tasks["guided"]:
        if st.button("开始今日引导学习", use_container_width=True):
            prepare_task(recommended_id, "引导学习模式"); st.rerun()
    if not tasks["practice"]:
        if st.button("开始今日随机练习", type="primary", use_container_width=True):
            prepare_task(recommended_id, "随机故障练习"); st.rerun()
    st.divider()
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
    if st.button("🎯 开始跨实验综合训练", use_container_width=True, help="系统随机选择一个实验和故障，完成安全确认后进入排查。"):
        start_comprehensive_training(); st.rerun()
    chosen_experiment_id = st.radio("实验", experiment_options, index=experiment_options.index(knowledge.experiment_id), format_func=lambda item: catalog[item]["name"], horizontal=True, label_visibility="collapsed")
    mode_options = ["随机故障练习", "引导学习模式", "自由诊断演示"]
    saved_mode = st.session_state.get("practice_mode", "随机故障练习")
    mode = st.segmented_control("学习方式", mode_options, default=saved_mode if saved_mode in mode_options else mode_options[0], help="随机练习自动评分；引导模式先讲解再判断且不计分；自由诊断用于探索规则。") or "随机故障练习"
    chosen_knowledge = KnowledgeBase(chosen_experiment_id)
    selected_symptom_id = chosen_knowledge.default_symptom_id
    if mode == "自由诊断演示":
        symptom_ids = list(chosen_knowledge.symptoms)
        selected_symptom_id = st.radio("选择模拟故障现象", symptom_ids, format_func=lambda item: chosen_knowledge.symptoms[item])
    elif mode == "随机故障练习":
        st.info("系统会随机生成故障和对应现象；完成后显示评分与推荐排查顺序。")
    else:
        st.info("每一步会先解释元件作用，再提供模拟资料供你判断；本模式不计分，但完成后会计入今日学习任务。")
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
            current_mode = st.session_state.get("practice_mode", "随机故障练习")
            scenario_id = secrets.choice(scenario_ids) if (
                current_mode in {"随机故障练习", "引导学习模式"} or current_mode == "综合训练"
            ) else None
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
        if st.session_state.get("practice_mode") == "引导学习模式":
            guided_card = card_for_node(node["id"])
            if guided_card:
                st.info(f"**先理解：{guided_card['title']}**\n\n{guided_card['principle']}\n\n**在本回路中的作用：** {guided_card['role']}")
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
        scored_practice = session.scenario_id is not None and st.session_state.get("practice_mode") in {"随机故障练习", "综合训练"}
        guided_practice = session.scenario_id is not None and st.session_state.get("practice_mode") == "引导学习模式"
        if scored_practice:
            repository.save(session.to_practice_record())
        elif guided_practice and session.practice_id:
            repository.save_activity(
                make_learning_activity(
                    knowledge.experiment_id, "guided_session", session.practice_id
                )
            )
        st.markdown("### 1. 本次结论")
        st.write(f"**实验：** {knowledge.experiment['name']}")
        st.write(f"**故障现象：** {session.symptom}")
        (st.warning if knowledge.is_inconclusive(session.result_id or "") else st.success)(result["cause"])
        st.write(result["explanation"])
        insight = insight_for_result(session.result_id)
        if insight:
            st.markdown("### 💡 学会这个故障")
            st.info(f"**为什么这样判断**\n\n{insight['why']}")
            with st.expander("容易混淆的故障"):
                st.write(insight["confusion"])
            st.success(f"**记忆提示：** {insight['memory']}")
        with st.expander("查看证据、来源与可信度"):
            st.write(f"**证据：** {result['evidence']}")
            st.write(f"**依据来源：** {result['source']}")
            st.write(f"**可信度：** {result['confidence']}")
            provenance = provenance_for_result(session.result_id)
            if provenance:
                st.write(f"**参考原理：** {provenance['principle']}")
                st.write(f"**审校状态：** {provenance['status']}")
                st.markdown("**参考资料：**")
                for source in resolved_sources(provenance):
                    st.markdown(f"- [{source['title']}]({source['url']})（{source['type']}）")
        if scored_practice:
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
            suggested_cards = review_cards(entry["node_id"] for entry in wrong_entries)
            for review_card in suggested_cards:
                if st.button(f"复习：{review_card['title']}", key=f"report_review_{review_card['id']}", use_container_width=True):
                    open_knowledge(review_card["id"]); st.rerun()
            st.markdown("### 3. 推荐排查顺序")
            path = session.recommended_path()
            assert path is not None
            for index, step in enumerate(path["steps"], 1):
                st.markdown(f"<div class='dzt-step'><b>{index}. {step['object']} → {step['answer']}</b><br><small>{step['observation']}</small></div>", unsafe_allow_html=True)
            st.success(f"推荐路径最终结论：{path['cause']}")
        elif session.scenario_result is not None:
            st.markdown("### 2. 引导学习小结")
            st.info("本模式不计分，也不会写入随机练习成绩；完成记录只用于每日学习任务。下面展示推荐排查顺序。")
            path = session.recommended_path()
            assert path is not None
            for index, step in enumerate(path["steps"], 1):
                st.markdown(f"<div class='dzt-step'><b>{index}. {step['object']} → {step['answer']}</b><br><small>{step['observation']}</small></div>", unsafe_allow_html=True)
        st.markdown("### 本次核心知识与下一步")
        core_cards = review_cards(item["node_id"] for item in session.history)
        if core_cards:
            st.write("本次涉及：" + "、".join(item["title"] for item in core_cards))
        first_wrong = next((item for item in session.history if item.get("is_correct") is False), None)
        if first_wrong:
            st.warning(
                f"你最早在“{first_wrong['object']}”偏离推荐路径："
                f"选择了“{first_wrong['answer']}”，推荐判断为“{first_wrong['expected_answer']}”。"
            )
        elif scored_practice:
            st.success("你的判断顺序没有偏离本题推荐路径。")
        experiment_card_ids = [item["id"] for item in cards_for_experiment(knowledge.experiment_id)]
        experiment_progress = calculate_experiment_progress(
            repository, knowledge.experiment_id, scenario_ids, experiment_card_ids
        )
        st.info(f"下一次学习建议：{experiment_progress.route_stage}")
        st.markdown("### 4. 完整检查记录")
        with st.expander("展开本次操作顺序"):
            for index, item in enumerate(session.history, 1):
                grade = " ✅" if item.get("is_correct") is True else (f" ❌（正确判断：{item['expected_answer']}）" if item.get("is_correct") is False else "")
                st.write(f"{index}. {item['object']} → **{item['answer']}**{grade}")
        learning_record = experiment_learning_record(session)
        st.markdown("### 5. 实验学习记录")
        st.write(f"**实验目的：** {learning_record['purpose']}")
        st.write(f"**实验结果：** {learning_record['result']}")
        st.write(f"**关键检查：** {' → '.join(learning_record['steps'])}")
        with st.expander("实验复盘问题"):
            for question in learning_record["reflection"]:
                st.write(f"- {question}")
        report = build_report(session, include_score=scored_practice)
        st.download_button("下载文本学习报告", data=report.encode("utf-8"), file_name="电诊通_教学诊断报告.txt", mime="text/plain", use_container_width=True)
        if scored_practice:
            if st.button("练习薄弱项", type="primary", use_container_width=True):
                start_weak_practice(); st.rerun()
            if st.button("再来一题", use_container_width=True):
                start_random_practice(); st.rerun()
        if st.button("返回实验首页", use_container_width=True):
            st.session_state.pop("diagnostic_state", None); set_stage(1); st.rerun()
        st.warning(DISCLAIMER)

elif stage == 5:
    st.subheader("📊 学习中心")
    if config.storage_is_temporary:
        st.warning("云端成绩与进度使用临时存储，服务重启或更新后可能清空。")
    if not repository.persistent:
        st.warning("SQLite当前不可用，已切换到内存记录；关闭或重启应用后数据会丢失。")
    total_learning_records = sum(len(items) for items in repository.export_snapshot().values())
    if config.storage_is_temporary and total_learning_records:
        st.info("云端记录可能在休眠、重启或更新后丢失，建议定期下载匿名JSON备份。")
    if total_learning_records >= 5 and not st.session_state.get("last_exported_at"):
        st.warning("你已经积累了多条学习记录，建议现在导出一次备份。")
    backup_columns = st.columns(2)
    if backup_columns[0].button("导出或恢复学习档案", type="primary", use_container_width=True):
        set_stage(12); st.rerun()
    last_exported_at = st.session_state.get("last_exported_at")
    backup_columns[1].metric("本次会话最近导出", last_exported_at.replace("T", " ")[:16] if last_exported_at else "尚未导出")
    all_progress = progress_map()
    overview = learning_overview(repository, all_progress)
    tasks = overview["tasks"]
    top_metrics = st.columns(2)
    top_metrics[0].metric("连续学习", f"{overview['streak']} 天")
    top_metrics[1].metric("今日任务", f"{tasks['completed_count']} / 3")
    st.progress(tasks["completion"], text="今日任务完成度")
    last_chapter_id = st.session_state.get("last_learning_chapter_id")
    if last_chapter_id in {item["id"] for item in ALL_CHAPTERS}:
        last_chapter = chapter_by_id(last_chapter_id)
        st.info(f"最近学习位置：{last_chapter['title']} · 下一步：{recommended_chapter_action(repository, last_chapter)}")
        if st.button("继续最近章节", use_container_width=True):
            st.session_state.selected_chapter_id = last_chapter_id; set_stage(8); st.rerun()
    st.subheader("课程完成情况")
    for course in COURSES:
        unlocked = course_is_unlocked(repository, course["id"])
        learning_status = course_learning_status(repository, course["id"])
        st.markdown(f"**{course['title']}** · {'已解锁' if unlocked else '待解锁'} · {learning_status}")
        chapter_rows = []
        for chapter in COURSE_CHAPTERS[course["id"]]:
            item = chapter_progress(repository, chapter)
            chapter_rows.append({
                "章节": chapter["title"], "完成度": f"{item.completion:.0%}",
                "测验": "已通过" if item.quiz_passed else "待通过",
                "状态": item.status, "推荐下一步": recommended_chapter_action(repository, chapter),
            })
        render_markdown_table(["章节", "完成度", "测验", "状态", "推荐下一步"], chapter_rows)
        exam = repository.quiz_summary(course["id"])
        if course_exam_eligible(repository, course["id"]):
            st.caption(f"综合评测：{exam['attempts']} 次 · 最好成绩 {exam['best_score']:.0%}" if exam["attempts"] else "综合评测已开放，尚未作答。")
    quiz_overview = repository.quiz_summary()
    st.subheader("章节测验与课程评测")
    quiz_metrics = st.columns(2)
    quiz_metrics[0].metric("测验次数", quiz_overview["attempts"])
    quiz_accuracy = quiz_overview["question_accuracy"]
    quiz_metrics[1].metric("答题正确率", f"{quiz_accuracy:.0%}" if quiz_accuracy is not None else "暂无")
    wrong_ids = repository.wrong_question_ids()
    if wrong_ids:
        st.caption(f"目前有 {len(wrong_ids)} 个知识点题目需要复习，复习模式会优先抽取。")
        if st.button("开始错题优先复习", type="primary", use_container_width=True):
            target_chapter = next((item["id"] for item in ALL_CHAPTERS if repository.wrong_question_ids(item["id"])),
                                  QUESTION_MAP[wrong_ids[0]].chapter_id)
            start_chapter_quiz(target_chapter, True); st.rerun()
    else:
        st.caption("完成章节测验后，这里会显示错题复习入口。")
    st.subheader("互动识图训练")
    diagram_overview = repository.diagram_summary()
    diagram_metrics = st.columns(3)
    diagram_metrics[0].metric("训练次数", diagram_overview["attempts"])
    diagram_metrics[1].metric("已完成案例", f"{diagram_overview['completed_cases']} / {len(DIAGRAM_CASES)}")
    diagram_metrics[2].metric("平均正确率", f"{diagram_overview['accuracy']:.0%}" if diagram_overview["accuracy"] is not None else "暂无")
    if diagram_overview["weakest_step"]:
        weak_step = next(step for case in DIAGRAM_CASES.values() for step in case["steps"] if step["id"] == diagram_overview["weakest_step"])
        st.info(f"当前最常出错的逻辑点：{weak_step['prompt']}")
    else:
        st.caption("完成第三门课程的互动识图案例后，这里会显示路径掌握情况。")
    st.subheader("实验掌握进度")
    progress_rows = []
    for experiment_id, item in all_progress.items():
        progress_rows.append({
            "实验": catalog[experiment_id]["name"],
            "掌握度": f"{item.mastery:.0%}",
            "状态": item.status,
            "知识卡": f"{item.learned_cards}/{item.total_cards}",
            "已掌握故障": f"{item.mastered_faults}/{item.total_faults}",
        })
    render_markdown_table(["实验", "掌握度", "状态", "知识卡", "已掌握故障"], progress_rows)
    st.subheader("新手学习路线")
    selected_route_id = st.selectbox(
        "查看实验路线", list(catalog),
        index=list(catalog).index(knowledge.experiment_id),
        format_func=lambda item: catalog[item]["name"],
    )
    route = all_progress[selected_route_id]
    route_steps = [
        ("学习知识卡", route.learned_cards == route.total_cards),
        ("完成引导学习", route.guided_sessions >= 1),
        ("完成3次随机练习", route.practice_attempts >= 3),
        ("掌握全部故障", route.mastered_faults == route.total_faults),
    ]
    for item, completed in route_steps:
        marker = "✅" if completed else ("👉" if item == route.route_stage else "▫️")
        st.write(f"{marker} {item}")
    st.info(f"当前阶段：{route.route_stage}")
    st.divider()
    st.write(f"**当前实验详细统计：{knowledge.experiment['name']}**")
    summary = repository.summary(experiment_id=knowledge.experiment_id)
    stats = repository.fault_stats(scenario_ids, experiment_id=knowledge.experiment_id)
    recent = repository.recent(10, experiment_id=knowledge.experiment_id)
    recommended_cards = review_cards(
        node_id for item in recent for node_id in item.get("wrong_nodes", [])
    )
    if recommended_cards:
        st.subheader("建议复习")
        st.caption("根据最近错题生成，只使用本机或当前云端临时记录。")
        for review_card in recommended_cards:
            if st.button(f"复习：{review_card['title']}", key=f"center_review_{review_card['id']}", use_container_width=True):
                open_knowledge(review_card["id"]); st.rerun()
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
            st.warning("清空后，练习成绩、知识卡标记、识图训练、引导记录和连续天数都无法恢复；不会影响故障知识库。")
            confirm_clear = st.checkbox("我确认删除全部本地学习与练习记录")
            if st.button("永久清空", disabled=not confirm_clear):
                repository.clear(confirmed=True); st.success("学习记录已清空。"); st.rerun()
    if st.button("返回实验首页", use_container_width=True):
        set_stage(1); st.rerun()

elif stage == 6:
    st.subheader("📘 知识中心")
    st.write(f"**当前实验：{knowledge.experiment['name']}**")
    st.caption("以下内容解释控制逻辑与模拟判断，不构成真实设备接线、测量或维修指导。")
    flow = relationship_steps(knowledge.experiment_id)
    flow_html = "<b>→</b>".join(f"<span>{item}</span>" for item in flow)
    st.markdown(f"<div class='dzt-flow'>{flow_html}</div>", unsafe_allow_html=True)
    st.warning("教学关系示意：不含端子号、真实电压、接线位置或带电操作步骤。")

    available_cards = cards_for_experiment(knowledge.experiment_id)
    card_ids = [item["id"] for item in available_cards]
    selected_card_id = st.session_state.get("selected_knowledge_card")
    if selected_card_id not in card_ids:
        selected_card_id = card_ids[0]
    selected_card_id = st.selectbox(
        "选择知识卡",
        card_ids,
        index=card_ids.index(selected_card_id),
        format_func=lambda item: next(card["title"] for card in available_cards if card["id"] == item),
    )
    st.session_state.selected_knowledge_card = selected_card_id
    card = next(item for item in available_cards if item["id"] == selected_card_id)
    st.markdown(f"### {card['title']}")
    st.info(card["principle"])
    st.write(f"**在控制逻辑中的作用：** {card['role']}")
    st.success(f"**正常模拟状态：** {card['normal']}")
    st.warning(f"**异常模拟状态：** {card['abnormal']}")
    st.write(f"**复习要点：** {card['review']}")
    render_provenance(provenance_for_card(selected_card_id))
    learned_cards = repository.learned_cards(knowledge.experiment_id)
    if selected_card_id in learned_cards:
        st.success("这张知识卡已标记为学过，可以继续复习。")
    elif st.button("标记为已学习", type="primary", use_container_width=True):
        repository.save_activity(
            make_learning_activity(
                knowledge.experiment_id, "knowledge_card", selected_card_id
            )
        )
        st.success("已记录学习进度。")
        st.rerun()
    if st.button("练习当前实验", type="primary", use_container_width=True):
        st.session_state.pop("diagnostic_state", None); set_stage(1); st.rerun()
    if st.button("返回学习中心", use_container_width=True):
        set_stage(5); st.rerun()

elif stage == 7:
    st.subheader("🧭 1分钟新手引导")
    st.caption("这是一个不计分、不保存成绩的纯模拟示例。")
    guide_columns = st.columns(3)
    guide_cards = (
        ("1. 选择实验", "先看故障现象，再选择直接启动或正反转实验。新手建议先用引导学习模式。"),
        ("2. 阅读模拟资料", "只根据网页状态卡判断，不联想或操作真实设备。先找到检查对象，再对照预期状态。"),
        ("3. 选择答案", "与预期一致选‘正常’，不一致选‘异常’；资料不足或术语没看懂时选‘不确定’。"),
    )
    for column, (title, text) in zip(guide_columns, guide_cards):
        with column:
            st.markdown(f'<div class="dzt-card"><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)

    st.markdown("### 试一题")
    st.write("**检查对象：** 停止按钮常闭触点（模拟）")
    st.write("**预期状态：** 按钮未按下时，常闭触点应导通。")
    st.info("**模拟状态卡：** 停止按钮未按下，常闭触点显示导通。")
    onboarding_answer = st.radio(
        "这个模拟状态应如何判断？",
        ["正常", "异常", "不确定"],
        index=None,
        horizontal=True,
        key="onboarding_answer",
    )
    if onboarding_answer == "正常":
        st.success("回答正确：模拟状态与预期状态一致，所以判断为‘正常’。")
        st.caption("记忆：停止按钮常用常闭触点，未按下时应导通。")
    elif onboarding_answer:
        st.warning("再对照一次：状态卡显示‘导通’，与预期状态完全一致，因此应选‘正常’。")

    st.warning("新手引导和正式练习都只使用网页模拟资料，不得用于真实设备诊断。")
    if st.button("我已学会，返回选择实验", type="primary", use_container_width=True):
        st.session_state.onboarding_seen = True
        set_stage(1); st.rerun()

elif stage == 8:
    selected_chapter_id = st.session_state.get("selected_chapter_id", CHAPTERS[0]["id"])
    if selected_chapter_id not in {item["id"] for item in ALL_CHAPTERS}:
        selected_chapter_id = CHAPTERS[0]["id"]
    chapter = chapter_by_id(selected_chapter_id)
    st.session_state.last_learning_chapter_id = chapter["id"]
    chapter_state = chapter_progress(repository, chapter)
    st.subheader(chapter["title"])
    st.info(f"**本章学习目标：** {chapter['goal']}")
    st.progress(chapter_state.completion, text=f"{chapter_state.status} · {chapter_state.completion:.0%}")
    st.markdown("### 本章学习路径")
    learning_steps = chapter_learning_steps(repository, chapter)
    for index, item in enumerate(learning_steps, 1):
        marker = "✅" if item.status == "已完成" else ("▫️" if item.status == "本章无独立实验" else "👉")
        st.write(f"{marker} {index}. **{item.name}** · {item.status}（{item.detail}）")
    next_action = recommended_chapter_action(repository, chapter)
    st.info(f"推荐下一步：{next_action}")
    if next_action == "学习知识卡":
        missing_card = next((item for item in chapter["card_ids"] if item not in repository.learned_cards(chapter["experiment_id"] or DEFAULT_EXPERIMENT_ID)), chapter["card_ids"][0])
        if st.button("立即学习推荐知识卡", type="primary", use_container_width=True):
            st.session_state.selected_experiment_id = chapter["experiment_id"] or DEFAULT_EXPERIMENT_ID
            open_knowledge(missing_card); st.rerun()
    elif next_action == "完成互动识图":
        chapter_cases = cases_for_chapter(chapter["id"])
        completed_ids = {item["case_id"] for item in repository.diagram_history(chapter["id"])}
        target_case = next((item for item in chapter_cases if item["id"] not in completed_ids), chapter_cases[0])
        if st.button("立即开始互动识图", type="primary", use_container_width=True):
            start_diagram_training(target_case["id"]); st.rerun()
    elif next_action == "通过章节测验":
        if st.button("立即开始章节测验", type="primary", use_container_width=True):
            start_chapter_quiz(chapter["id"]); st.rerun()
    elif next_action == "完成引导实验" and chapter["experiment_id"]:
        if st.button("立即开始引导实验", type="primary", use_container_width=True):
            prepare_task(chapter["experiment_id"], "引导学习模式"); st.rerun()
    elif next_action == "完成随机练习" and chapter["experiment_id"]:
        if st.button("立即开始随机练习", type="primary", use_container_width=True):
            prepare_task(chapter["experiment_id"], "随机故障练习"); st.rerun()
    st.markdown("### 知识要点")
    for point in chapter["points"]:
        st.write(f"- {point}")

    diagram_lesson = diagram_lesson_for_chapter(chapter["id"])
    if diagram_lesson:
        st.markdown("### 抽象逻辑识读")
        st.write(diagram_lesson["title"])
        chapter_cases = cases_for_chapter(chapter["id"])
        completed_case_ids = {item["case_id"] for item in repository.diagram_history(chapter["id"])}
        for case, flow in zip(chapter_cases, diagram_lesson["flows"]):
            flow_html = "<b>→</b>".join(f"<span>{item}</span>" for item in flow)
            st.markdown(f"<div class='dzt-flow'>{flow_html}</div>", unsafe_allow_html=True)
            marker = "✅" if case["id"] in completed_case_ids else "🧩"
            if st.button(f"{marker} {case['title']}", key=f"diagram_case_{case['id']}", use_container_width=True):
                start_diagram_training(case["id"]); st.rerun()
        st.caption("只表达功能角色和条件关系，不包含端子号、电压、真实导线或安装位置。")

    if chapter["experiment_id"]:
        target_knowledge = KnowledgeBase(chapter["experiment_id"])
        flow = relationship_steps(chapter["experiment_id"])
        flow_html = "<b>→</b>".join(f"<span>{item}</span>" for item in flow)
        st.markdown("### 控制逻辑关系")
        st.markdown(f"<div class='dzt-flow'>{flow_html}</div>", unsafe_allow_html=True)
        st.caption("只表达教学逻辑，不包含端子号、接线位置或真实电压。")
    else:
        target_knowledge = KnowledgeBase(DEFAULT_EXPERIMENT_ID)

    st.markdown("### 本章知识卡")
    if chapter["card_ids"]:
        for card_id in chapter["card_ids"]:
            card = KNOWLEDGE_CARDS[card_id]
            learned_experiment = chapter["experiment_id"] or DEFAULT_EXPERIMENT_ID
            learned = card_id in repository.learned_cards(learned_experiment)
            marker = "✅" if learned else "📘"
            if st.button(f"{marker} {card['title']}", key=f"chapter_card_{card_id}", use_container_width=True):
                st.session_state.selected_experiment_id = learned_experiment
                st.session_state.selected_knowledge_card = card_id
                open_knowledge(card_id); st.rerun()
    else:
        st.caption("本章暂无独立知识卡。")

    if chapter["experiment_id"]:
        st.markdown("### 本章模拟实验")
        st.write(target_knowledge.experiment["name"])
        if st.button("开始引导学习", type="primary", use_container_width=True):
            prepare_task(chapter["experiment_id"], "引导学习模式"); st.rerun()
        if st.button("开始随机故障练习", use_container_width=True):
            prepare_task(chapter["experiment_id"], "随机故障练习"); st.rerun()
    elif not diagram_lesson:
        st.caption("本章先学习基础概念，实验将在后续章节中开放。")

    st.markdown("### 复盘问题")
    st.write(chapter["reflection"])
    st.success(f"**推荐下一步：** {chapter['next']}")
    st.markdown("### 章节测验")
    quiz_summary = repository.quiz_summary(chapter["id"])
    if quiz_summary["attempts"]:
        best = quiz_summary["best_score"]
        st.write(f"已完成 {quiz_summary['attempts']} 次 · 最好成绩 {best:.0%} · {'已通过' if quiz_summary['passed_count'] else '尚未通过'}")
    else:
        st.caption("每次随机抽取5题，答对3题（60%）即通过；选择“不确定”不会被强行判为正确。")
    if st.button("开始本章测验", type="primary", use_container_width=True):
        start_chapter_quiz(chapter["id"]); st.rerun()
    if repository.wrong_question_ids(chapter["id"]):
        if st.button("复习本章错题", use_container_width=True):
            start_chapter_quiz(chapter["id"], True); st.rerun()
    if st.button("返回课程地图", use_container_width=True):
        set_stage(1); st.rerun()

elif stage == 9:
    st.subheader("📖 电气术语中心")
    st.caption("术语解释用于理解教学模拟，不代替教材、设备说明书或安全规程。")
    selected_term = st.selectbox("选择术语", list(GLOSSARY))
    st.markdown(f"### {selected_term}")
    st.info(GLOSSARY[selected_term])
    st.write("学习建议：先确认元件的基准状态，再阅读题目中的模拟状态卡。")
    st.warning("本页不提供真实测量、拆线、短接或送电指导。")
    if st.button("返回课程地图", use_container_width=True):
        set_stage(1); st.rerun()

elif stage == 10:
    quiz = st.session_state.get("quiz_state")
    if not quiz or quiz.get("chapter_id") not in {item["id"] for item in ALL_CHAPTERS}:
        st.warning("测验状态已失效，请重新开始。")
        if st.button("返回课程地图", use_container_width=True):
            set_stage(1); st.rerun()
    else:
        chapter = chapter_by_id(quiz["chapter_id"])
        question_ids = quiz["question_ids"]
        index = min(int(quiz["index"]), len(question_ids) - 1)
        question = QUESTION_MAP[question_ids[index]]
        st.subheader(f"📝 {chapter['title']} · {'错题复习' if quiz['mode'] == 'wrong_review' else '章节测验'}")
        st.progress((index + 1) / len(question_ids), text=f"第 {index + 1} / {len(question_ids)} 题")
        st.markdown(f"### {question.stem}")
        selected = st.radio(
            "请选择一个答案", [*question.options, "不确定"], index=None,
            key=f"quiz_choice_{question.id}_{index}",
        )
        if not quiz["answered"]:
            if st.button("提交答案", type="primary", disabled=selected is None, use_container_width=True):
                answer = QuizAnswer(
                    question_id=question.id,
                    selected_answer=selected,
                    correct_answer=question.answer,
                    is_correct=selected == question.answer,
                    uncertain=selected == "不确定",
                )
                quiz["answers"].append({
                    "question_id": answer.question_id, "selected_answer": answer.selected_answer,
                    "correct_answer": answer.correct_answer, "is_correct": answer.is_correct,
                    "uncertain": answer.uncertain,
                })
                quiz["answered"] = True
                st.session_state.quiz_state = quiz
                st.rerun()
        else:
            answer = quiz["answers"][-1]
            if answer["is_correct"]:
                st.success("回答正确。")
            else:
                st.error(f"本题正确答案：{question.answer}")
            st.info(f"**解析：** {question.explanation}")
            st.write(f"**针对你的答案：** {answer_feedback(question, answer['selected_answer'])}")
            st.caption(f"对应知识点：{question.knowledge_point}。仅限教学模拟，不用于真实设备操作。")
            render_provenance(provenance_for_question(card_id_for_question(question.id)), "本题参考资料")
            if st.button("查看成绩" if index == len(question_ids) - 1 else "下一题", type="primary", use_container_width=True):
                if index == len(question_ids) - 1:
                    answers = tuple(QuizAnswer(**item) for item in quiz["answers"])
                    record = make_quiz_record(quiz["chapter_id"], answers, quiz["mode"])
                    repository.save_quiz(record)
                    st.session_state.quiz_result_id = record.quiz_id
                    st.session_state.quiz_state = {**quiz, "record": {
                        "quiz_id": record.quiz_id, "correct_count": record.correct_count,
                        "total_count": record.total_count, "passed": record.passed,
                    }}
                    set_stage(11)
                else:
                    quiz["index"] = index + 1; quiz["answered"] = False
                    st.session_state.quiz_state = quiz
                st.rerun()
        if st.button("退出测验", use_container_width=True):
            st.session_state.pop("quiz_state", None); set_stage(8); st.rerun()

elif stage == 11:
    quiz = st.session_state.get("quiz_state", {})
    result = quiz.get("record")
    if not result:
        st.warning("没有可显示的测验结果。")
    else:
        chapter = chapter_by_id(quiz["chapter_id"])
        score = result["correct_count"] / result["total_count"]
        st.subheader("📋 章节测验报告")
        st.markdown(f"### {chapter['title']}")
        st.metric("本次成绩", f"{result['correct_count']} / {result['total_count']}（{score:.0%}）")
        if result["passed"]:
            st.success("已达到60%通过标准，本章测验完成。")
        else:
            st.warning("尚未达到60%，建议先复习下方错题再测一次。")
        wrong_answers = [item for item in quiz["answers"] if not item["is_correct"]]
        if not wrong_answers:
            st.success("本次没有错题，判断过程正确。")
        else:
            st.markdown("### 错题与知识点")
            for item in wrong_answers:
                question = QUESTION_MAP[item["question_id"]]
                st.markdown(f"**{question.stem}**")
                st.write(f"你的答案：{item['selected_answer']}；正确答案：{item['correct_answer']}")
                st.info(question.explanation)
                st.write(f"**为什么这个答案不合适：** {answer_feedback(question, item['selected_answer'])}")
                card_id = card_id_for_question(question.id)
                card = KNOWLEDGE_CARDS[card_id]
                st.caption(f"对应知识卡：{card['title']} · 知识点：{question.knowledge_point}")
                action_columns = st.columns(2)
                if action_columns[0].button("复习知识卡", key=f"quiz_card_{question.id}", use_container_width=True):
                    chapter = chapter_by_id(question.chapter_id)
                    st.session_state.selected_experiment_id = chapter["experiment_id"] or DEFAULT_EXPERIMENT_ID
                    open_knowledge(card_id); st.rerun()
                if action_columns[1].button("再做一道相似题", key=f"similar_{question.id}", use_container_width=True):
                    start_similar_quiz(question.id); st.rerun()
        st.warning("测验仅用于电气知识学习，不得据此进行真实带电测量、拆线或送电操作。")
        if wrong_answers and st.button("立即复习本章错题", type="primary", use_container_width=True):
            start_chapter_quiz(quiz["chapter_id"], True); st.rerun()
        if st.button("再测一次", use_container_width=True):
            start_chapter_quiz(quiz["chapter_id"]); st.rerun()
        if st.button("返回本章", use_container_width=True):
            st.session_state.selected_chapter_id = quiz["chapter_id"]
            st.session_state.pop("quiz_state", None); set_stage(8); st.rerun()

elif stage == 12:
    st.subheader("💾 学习档案导出与恢复")
    st.info("档案只包含课程、实验、答案、得分和时间，不包含姓名、学校、邮箱、账号或设备信息。")
    if config.storage_is_temporary or not repository.persistent:
        st.warning("当前记录可能在服务休眠、重启、更新或会话结束后丢失，建议下载JSON备份。")
    snapshot = repository.export_snapshot()
    record_count = sum(len(items) for items in snapshot.values())
    metrics = st.columns(4)
    metrics[0].metric("练习记录", len(snapshot["practice_records"]))
    metrics[1].metric("学习活动", len(snapshot["learning_activities"]))
    metrics[2].metric("章节测验", len(snapshot["quiz_sessions"]))
    metrics[3].metric("识图训练", len(snapshot["diagram_practice_records"]))
    st.markdown("### 导出")
    st.download_button(
        "下载JSON完整备份", data=archive_json_bytes(repository),
        file_name="电诊通_匿名学习档案.json", mime="application/json",
        on_click=mark_exported, type="primary", use_container_width=True,
    )
    st.download_button(
        "下载TXT学习摘要", data=build_learning_summary(repository).encode("utf-8"),
        file_name="电诊通_学习档案摘要.txt", mime="text/plain",
        on_click=mark_exported, use_container_width=True,
    )
    if st.session_state.get("last_exported_at"):
        st.caption("本次会话最近导出：" + st.session_state.last_exported_at.replace("T", " ")[:19])
    st.caption("TXT用于阅读；JSON用于以后恢复。请不要手工修改JSON内容。")
    st.warning("学习档案不是职业资格、实训考核或能力认证证书。")

    st.markdown("### 恢复JSON备份")
    uploaded = st.file_uploader("选择电诊通JSON学习档案", type=["json"], accept_multiple_files=False)
    if uploaded is not None:
        try:
            archive = parse_archive(uploaded.getvalue())
            preview = preview_archive(archive)
            st.success("文件校验通过，尚未写入任何记录。")
            st.write(
                f"档案包含：练习 {preview.practice_records} 条、学习活动 "
                f"{preview.learning_activities} 条、测验 {preview.quiz_sessions} 条、"
                f"识图训练 {preview.diagram_practice_records} 条。"
            )
            st.caption("导入按记录唯一标识去重；已有记录会保留，不会被较差或修改后的记录覆盖。")
            confirm_import = st.checkbox("我确认将以上匿名学习记录合并到当前档案")
            if st.button("确认导入", type="primary", disabled=not confirm_import, use_container_width=True):
                result = import_archive(repository, archive, confirmed=True)
                added = (result["practice_records"] + result["learning_activities"]
                         + result["quiz_sessions"] + result["diagram_practice_records"])
                st.success(f"导入完成：新增 {added} 条，跳过重复 {result['duplicates']} 条。")
        except BackupValidationError as exc:
            st.error(f"无法导入：{exc}。当前学习记录未被修改。")
    if not record_count:
        st.caption("当前还没有学习记录；仍可使用本页恢复以前导出的JSON档案。")
    if st.button("返回学习中心", use_container_width=True):
        set_stage(5); st.rerun()

elif stage == 13:
    raw_training = st.session_state.get("diagram_training")
    try:
        training = DiagramTrainingSession.from_dict(raw_training or {})
    except (TypeError, ValueError, KeyError):
        st.warning("识图训练状态已失效，请重新选择案例。")
        if st.button("返回课程地图", use_container_width=True):
            st.session_state.pop("diagram_training", None); set_stage(1); st.rerun()
    else:
        case = training.case
        st.subheader(f"🧩 {case['title']}")
        st.error(f"**模拟现象：** {case['phenomenon']}")
        st.warning(SAFETY_NOTICE)
        flow_html = "<b>→</b>".join(
            f"<span style='font-weight:{'700' if index == training.index else '400'}'>{node}</span>"
            for index, node in enumerate(case["nodes"])
        )
        st.markdown(f"<div class='dzt-flow'>{flow_html}</div>", unsafe_allow_html=True)
        if not training.is_complete:
            step = training.current_step
            st.progress(training.index / len(case["steps"]), text=f"路径步骤 {training.index + 1} / {len(case['steps'])}")
            st.markdown(f"### {step['prompt']}")
            selected = st.radio("选择下一判断", step["options"], index=None,
                                key=f"diagram_choice_{training.training_id}_{step['id']}_{len(training.first_answers)}")
            if st.button("提交本步判断", type="primary", disabled=selected is None, use_container_width=True):
                solved = training.answer(selected)
                st.session_state.diagram_training = training.to_dict()
                if solved: st.success(f"判断正确：{step['explanation']}")
                else: st.warning(f"本次首次判断已记录。{step['explanation']} 请重新选择正确路径后继续。")
                st.rerun()
            if training.step_solved:
                st.success(f"当前步骤已完成：{step['explanation']}")
                if st.button("进入下一步", type="primary", use_container_width=True):
                    training.next_step(); st.session_state.diagram_training = training.to_dict(); st.rerun()
        else:
            record = make_diagram_record(training)
            repository.save_diagram_practice(record)
            score = training.correct_steps / len(case["steps"])
            st.progress(1.0, text="案例完成")
            st.metric("首次判断得分", f"{training.correct_steps} / {len(case['steps'])}（{score:.0%}）")
            if training.wrong_steps:
                st.markdown("### 首次错误步骤")
                for step_id in training.wrong_steps:
                    step = next(item for item in case["steps"] if item["id"] == step_id)
                    st.write(f"- {step['prompt']}：{step['explanation']}")
            else:
                st.success("全部步骤首次判断正确。")
            st.markdown("### 推荐路径")
            st.markdown(" → ".join(step["answer"] for step in case["steps"]))
            st.markdown("### 对应知识卡")
            st.write("、".join(KNOWLEDGE_CARDS[item]["title"] for item in case["card_ids"]))
            render_provenance(provenance_for_diagram(case["card_ids"]), "本案例参考资料")
            chapter_cases = cases_for_chapter(case["chapter_id"])
            next_case = next((item for item in chapter_cases if item["id"] != training.case_id), chapter_cases[0])
            if st.button("再练一个案例", type="primary", use_container_width=True):
                start_diagram_training(next_case["id"]); st.rerun()
            if st.button("返回本章", use_container_width=True):
                st.session_state.selected_chapter_id = case["chapter_id"]
                st.session_state.pop("diagram_training", None); set_stage(8); st.rerun()

elif stage == 14:
    exam = st.session_state.get("course_exam_state", {})
    course_id = exam.get("course_id")
    if course_id not in COURSE_CHAPTERS or not exam.get("question_ids"):
        st.warning("课程评测状态已失效，请重新开始。")
        if st.button("返回课程地图", use_container_width=True): set_stage(1); st.rerun()
    else:
        course = next(item for item in COURSES if item["id"] == course_id)
        index = min(int(exam["index"]), len(exam["question_ids"]) - 1)
        question = QUESTION_MAP[exam["question_ids"][index]]
        st.subheader(f"📝 {course['title']} · 综合评测")
        st.progress((index + 1) / len(exam["question_ids"]), text=f"第 {index + 1} / {len(exam['question_ids'])} 题")
        st.markdown(f"### {question.stem}")
        selected = st.radio("请选择一个答案", [*question.options, "不确定"], index=None,
                            key=f"course_exam_choice_{course_id}_{question.id}_{index}")
        if st.button("提交并进入下一题" if index < len(exam["question_ids"]) - 1 else "提交并查看报告",
                     type="primary", disabled=selected is None, use_container_width=True):
            answer = QuizAnswer(question.id, selected, question.answer,
                                selected == question.answer, selected == "不确定")
            exam["answers"].append({
                "question_id":answer.question_id, "selected_answer":answer.selected_answer,
                "correct_answer":answer.correct_answer, "is_correct":answer.is_correct,
                "uncertain":answer.uncertain,
            })
            if index == len(exam["question_ids"]) - 1:
                answers = tuple(QuizAnswer(**item) for item in exam["answers"])
                record = make_quiz_record(course_id, answers, mode="course_exam")
                repository.save_quiz(record)
                exam["record"] = {"quiz_id":record.quiz_id, "correct_count":record.correct_count,
                                  "total_count":record.total_count, "passed":record.passed}
                st.session_state.course_exam_state = exam; set_stage(15)
            else:
                exam["index"] = index + 1; st.session_state.course_exam_state = exam
            st.rerun()
        st.caption("答题过程中不显示答案，完成后统一生成能力报告。仅限教学学习。")
        if st.button("退出本次评测", use_container_width=True):
            st.session_state.pop("course_exam_state", None); set_stage(1); st.rerun()

elif stage == 15:
    exam = st.session_state.get("course_exam_state", {})
    result = exam.get("record")
    course_id = exam.get("course_id")
    if not result or course_id not in COURSE_CHAPTERS:
        st.warning("没有可显示的课程评测报告。")
        if st.button("返回课程地图", use_container_width=True): set_stage(1); st.rerun()
    else:
        course = next(item for item in COURSES if item["id"] == course_id)
        answers = tuple(QuizAnswer(**item) for item in exam["answers"])
        score = result["correct_count"] / result["total_count"]
        st.subheader("📋 课程综合评测报告")
        st.markdown(f"### {course['title']}")
        st.metric("本次成绩", f"{result['correct_count']} / {result['total_count']}（{score:.0%}）")
        if result["passed"]: st.success("达到70%课程评测标准，本课程状态更新为“已完成”。")
        else: st.warning("尚未达到70%，请按下方路线复习后再次评测。")
        history = repository.quiz_history(course_id, 20)
        best = max(item["correct_count"] / item["total_count"] for item in history)
        st.write(f"评测次数：{len(history)} · 最好成绩：{best:.0%}")
        if len(history) >= 2:
            previous = history[1]["correct_count"] / history[1]["total_count"]
            st.write(f"相比上一次：{score - previous:+.0%}")
        st.markdown("### 能力掌握情况")
        ability_rows = [{"能力维度":item["name"], "得分":f"{item['correct']}/{item['total']}",
                         "正确率":f"{item['accuracy']:.0%}"} for item in competency_report(answers)]
        render_markdown_table(["能力维度", "得分", "正确率"], ability_rows)
        route = review_route(answers)
        exam_sources = tuple(dict.fromkeys(card_id_for_question(answer.question_id) for answer in answers))
        st.info(f"本次 {len(answers)} 道题均通过知识卡来源映射生成；涉及 {len(exam_sources)} 个知识主题。")
        st.markdown("### 推荐复习路线")
        if route:
            for index, item in enumerate(route, 1):
                chapter = chapter_by_id(item["chapter_id"])
                st.write(f"{index}. **{chapter['title']}**：{item['reason']}")
                if st.button(f"复习第{index}项", key=f"exam_review_{item['chapter_id']}", use_container_width=True):
                    st.session_state.selected_course_id = course_id
                    st.session_state.selected_chapter_id = item["chapter_id"]
                    st.session_state.last_learning_chapter_id = item["chapter_id"]
                    set_stage(8); st.rerun()
        else: st.success("本次没有错题，可继续下一门课程或进行巩固练习。")
        report_lines = ["电诊通｜课程学习总结", course["title"],
                        f"本次成绩：{result['correct_count']}/{result['total_count']}（{score:.0%}）",
                        f"内容来源：本次题目通过 {len(exam_sources)} 个知识主题映射到官方资料；核对状态请见应用内内容与资料中心。",
                        "能力情况：", *[f"- {item['name']}：{item['accuracy']:.0%}" for item in competency_report(answers)],
                        "", "仅用于教学学习，不是职业资格、实训考核或能力认证证书。"]
        st.download_button("下载课程学习总结", data="\n".join(report_lines).encode("utf-8"),
                           file_name="电诊通_课程学习总结.txt", mime="text/plain", use_container_width=True)
        if st.button("重新评测", type="primary", use_container_width=True): start_course_exam(course_id); st.rerun()
        if st.button("返回课程地图", use_container_width=True):
            st.session_state.pop("course_exam_state", None); set_stage(1); st.rerun()

elif stage == 16:
    try:
        quick = QuickExperienceSession.from_dict(st.session_state.get("quick_experience", {}))
    except (TypeError, ValueError):
        quick = QuickExperienceSession(); st.session_state.quick_experience = quick.to_dict()
    st.subheader("⚡ 5分钟体验电诊通")
    st.caption("知识卡 → 识图体验 → 模拟排查 → 迷你测验 → 学习总结")
    completed_units = (1 if quick.card_read else 0) + quick.index
    st.progress(completed_units / (len(EXPERIENCE_ITEMS) + 1),
                text=f"体验进度 {completed_units} / {len(EXPERIENCE_ITEMS) + 1}")
    st.warning("全程只使用网页模拟资料，不连接设备，不提供真实接线或带电操作指导。")
    if not quick.card_read:
        card = KNOWLEDGE_CARDS["control_power"]
        st.markdown("### 1. 阅读一张知识卡")
        st.markdown(f'<div class="dzt-card"><h3>{card["title"]}</h3><p><b>原理：</b>{card["principle"]}</p><p><b>作用：</b>{card["role"]}</p></div>', unsafe_allow_html=True)
        st.info("学习方法：先理解上游公共条件，再检查下游操作信号和执行元件。")
        if st.button("我已读懂，进入识图体验", type="primary", use_container_width=True):
            quick.mark_card_read(); st.session_state.quick_experience = quick.to_dict(); st.rerun()
    elif not quick.is_complete:
        item = quick.current_item
        phase_number = {"识图体验":2, "模拟排查":3, "迷你测验":4}[item["phase"]]
        st.markdown(f"### {phase_number}. {item['phase']} · {item['title']}")
        st.info(item["context"])
        st.markdown(f"**{item['prompt']}**")
        selected = st.radio("请选择", item["options"], index=None,
                            key=f"quick_choice_{item['id']}_{len(quick.first_answers)}")
        if st.button("提交判断", type="primary", disabled=selected is None, use_container_width=True):
            solved = quick.answer(selected); st.session_state.quick_experience = quick.to_dict()
            if solved: st.success(f"判断正确：{item['explanation']}")
            else: st.warning(f"首次判断已记录。{item['explanation']} 请重新选择后继续。")
            st.rerun()
        if quick.item_solved:
            st.success(f"本步完成：{item['explanation']}")
            if st.button("继续下一步", type="primary", use_container_width=True):
                quick.next_item(); st.session_state.quick_experience = quick.to_dict(); st.rerun()
    else:
        report = experience_report(quick)
        score = quick.correct_count / len(EXPERIENCE_ITEMS)
        st.markdown("### 5. 体验学习总结")
        st.metric("首次判断", f"{quick.correct_count} / {len(EXPERIENCE_ITEMS)}（{score:.0%}）")
        st.success("你已经体验了电诊通的知识、识图、模拟排查和测验流程。")
        if quick.wrong_items:
            st.markdown("### 建议巩固")
            for item_id in quick.wrong_items:
                item = next(value for value in EXPERIENCE_ITEMS if value["id"] == item_id)
                st.write(f"- **{item['phase']}：** {item['explanation']}")
        else: st.info("全部项目首次判断正确，可以进入正式课程继续学习。")
        st.download_button("下载体验学习总结", data=report.encode("utf-8"),
                           file_name="电诊通_5分钟体验总结.txt", mime="text/plain", use_container_width=True)
        st.caption("体验结果不写入正式成绩，也不会解锁或改变课程进度。")
        if st.button("进入正式课程", type="primary", use_container_width=True):
            st.session_state.onboarding_seen = True
            st.session_state.selected_course_id = COURSE["id"]
            st.session_state.pop("quick_experience", None); set_stage(1); st.rerun()
        if st.button("再体验一次", use_container_width=True): start_quick_experience(); st.rerun()
    if not quick.is_complete and st.button("退出体验", use_container_width=True):
        st.session_state.pop("quick_experience", None); set_stage(1); st.rerun()

elif stage == 17:
    st.subheader("📚 内容与资料中心")
    st.caption("查看教学内容来自哪里、核对到什么程度，以及哪些边界仍需谨慎。")
    question_cards = [card_id_for_question(question_id) for question_id in QUESTION_MAP]
    diagram_groups = [case["card_ids"] for case in DIAGRAM_CASES.values()]
    coverage = coverage_summary(question_cards, diagram_groups)
    columns = st.columns(4)
    columns[0].metric("官方资料", coverage["sources"])
    columns[1].metric("知识卡", f"{coverage['cards']} / {len(KNOWLEDGE_CARDS)}")
    columns[2].metric("题目可追溯", f"{coverage['questions']} / {coverage['question_total']}")
    columns[3].metric("故障结论", coverage["results"])
    st.info(f"识图案例来源覆盖：{coverage['diagrams']} / {coverage['diagram_total']}。")
    st.markdown("### 核对状态怎么理解")
    st.success(f"**{STATUS_VERIFIED}**：厂家资料能够支持当前呈现的通用功能或控制关系。")
    st.warning(f"**{STATUS_PARTIAL}**：通用原理有来源，但教学排查顺序仍不是工业检修规程。")
    st.error(f"**{STATUS_PENDING}**：不会进入课程综合评测，直到补齐可靠来源。")
    st.markdown("### 官方资料目录")
    for source in SOURCES.values():
        with st.expander(f"{source['publisher']}｜{source['title']}"):
            st.write(f"**资料类型：** {source['type']}")
            st.write(f"**核对范围：** {source['scope']}")
            st.write(f"**最近核对：** {source['checked_on']}")
            st.link_button("打开官方资料", source["url"])
    st.markdown("### 知识卡核对清单")
    rows = [{"知识卡":KNOWLEDGE_CARDS[card_id]["title"], "状态":item["status"], "资料数":len(item["sources"])} for card_id,item in CARD_PROVENANCE.items()]
    render_markdown_table(["知识卡", "状态", "资料数"], rows)
    st.warning("这些资料用于解释抽象教学逻辑，不提供真实端子、电压、接线、测量或送电步骤。")
    if st.button("返回课程地图", use_container_width=True):
        set_stage(1); st.rerun()
