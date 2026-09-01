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
from dianzhentong.review_plan import build_review_plan, review_overview
from dianzhentong.capstone import (
    CAPSTONE_SAFETY, CAPSTONE_TASKS, CapstoneTaskSession,
    capstone_report_text, task_for_course, task_is_unlocked,
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
    FOURTH_COURSE,
    GLOSSARY,
    chapter_by_id,
    chapter_learning_steps,
    chapter_progress,
    course_is_unlocked,
    course_unlock_requirement,
    experiment_learning_record,
    recommended_chapter_action,
)
from dianzhentong.curriculum_catalog import (
    BOOK_EDITION_MAPPINGS, KNOWLEDGE_TOPICS, LEARNING_DOMAINS,
    topics_for_book_chapter,
)
from dianzhentong.textbook_learning import lesson_for_topic
from dianzhentong.textbook_examples import example_for_unit, formulas_for_topic
from dianzhentong.textbook_visuals import SELF_HOLD_STATES, visual_for_topic
from dianzhentong.textbook_discovery import build_textbook_index, search_textbooks
from dianzhentong.review_notebook import review_notebook_json, review_notebook_text
from dianzhentong.star_delta_learning import (
    STAR_DELTA_STAGES, build_star_delta_course_summary,
    diagram_choice_feedback, star_delta_summary_text,
)
from dianzhentong.time_sequence_learning import demos_for_chapter
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
if (not hasattr(storage_module.ResilientPracticeRepository, "capstone_summary")
        or not hasattr(storage_module.ResilientPracticeRepository, "study_notes")):
    storage_module = importlib.reload(storage_module)

ResilientPracticeRepository = storage_module.ResilientPracticeRepository
choose_weak_scenario = storage_module.choose_weak_scenario
make_learning_activity = storage_module.make_learning_activity
make_diagram_record = storage_module.make_diagram_record
make_capstone_record = storage_module.make_capstone_record
StudyNote = storage_module.StudyNote

UI_STATE_VERSION = "4.3"
STORAGE_CACHE_VERSION = "4.3-textbook-project2"
st.set_page_config(page_title="电诊通", page_icon="⚡", layout="centered")
st.markdown("""
<style>
:root{--dzt-blue:#2563eb;--dzt-blue-dark:#1e3a8a;--dzt-ink:#172033;--dzt-muted:#64748b;--dzt-line:#e2e8f0;--dzt-surface:#fff;--dzt-soft:#f6f8fc}
.stApp{background:linear-gradient(180deg,#f7faff 0,#fff 18rem)}
.block-container{max-width:1040px;padding-top:1.4rem;padding-bottom:5rem}
.dzt-hero{padding:2rem 2.1rem;border-radius:24px;color:white;background:linear-gradient(125deg,#173b8f 0%,#2563eb 62%,#60a5fa 100%);box-shadow:0 18px 45px rgba(37,99,235,.18);margin-bottom:1.25rem}.dzt-hero h1{margin:0;font-size:2.45rem;letter-spacing:-.04em}.dzt-hero p{margin:.55rem 0 0;opacity:.9;font-size:1.02rem}.dzt-brandbar{display:flex;align-items:center;justify-content:space-between;padding:.7rem 0 1rem;border-bottom:1px solid var(--dzt-line);margin-bottom:1.35rem}.dzt-brandbar strong{font-size:1.15rem;color:var(--dzt-blue-dark)}.dzt-brandbar span{font-size:.82rem;color:var(--dzt-muted)}
.dzt-dashboard{padding:1.25rem 1.35rem;border:1px solid #dbeafe;border-radius:18px;background:rgba(255,255,255,.94);box-shadow:0 8px 24px rgba(30,64,175,.07);margin:.8rem 0 1.25rem}.dzt-dashboard h3{margin:0 0 .25rem;color:var(--dzt-ink)}.dzt-dashboard p{margin:.2rem 0;color:var(--dzt-muted)}
.dzt-section-label{margin:1.8rem 0 .25rem;color:var(--dzt-blue);font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.dzt-card{min-height:154px;padding:1.2rem 1.25rem;border:1px solid var(--dzt-line);border-radius:18px;background:var(--dzt-surface);box-shadow:0 6px 20px rgba(15,23,42,.045);margin-bottom:.7rem;transition:border-color .2s,transform .2s}.dzt-card:hover{border-color:#bfdbfe;transform:translateY(-1px)}.dzt-card h3{color:var(--dzt-ink);margin:0 0 .55rem;font-size:1.08rem}.dzt-card p{margin:.3rem 0;color:var(--dzt-muted);line-height:1.55}.dzt-card b{color:var(--dzt-blue-dark)}
.dzt-step{padding:.9rem 1rem;border-left:4px solid var(--dzt-blue);border-radius:0 12px 12px 0;background:#eff6ff;margin:.6rem 0}.dzt-stage{padding:1.05rem 1.15rem;border:1px solid #bfdbfe;border-radius:15px;background:linear-gradient(135deg,#eff6ff,#fff);margin:.7rem 0}.dzt-stage strong{color:var(--dzt-blue-dark)}.dzt-flow{display:flex;align-items:center;flex-wrap:wrap;gap:.45rem;margin:.8rem 0 1rem}.dzt-flow span{padding:.55rem .7rem;border-radius:9px;background:#eff6ff;border:1px solid #bfdbfe;color:#1e3a8a}.dzt-flow b{color:#60a5fa}
div.stButton>button,div.stDownloadButton>button,div.stLinkButton>a{border-radius:11px;min-height:2.85rem;font-weight:600}div.stButton>button[kind="primary"]{box-shadow:0 6px 16px rgba(37,99,235,.18)}[data-testid="stMetric"]{background:#fff;border:1px solid var(--dzt-line);padding:.9rem;border-radius:14px;box-shadow:0 4px 14px rgba(15,23,42,.035)}[data-testid="stSidebar"]{background:#f8fafc;border-right:1px solid var(--dzt-line)}[data-testid="stSidebar"] .stButton button{text-align:left;justify-content:flex-start;border-color:transparent;background:transparent}[data-testid="stSidebar"] .stButton button:hover{background:#eaf2ff;border-color:#dbeafe;color:var(--dzt-blue-dark)}hr{border-color:var(--dzt-line)}
@media(max-width:640px){.block-container{padding:1rem .8rem 4rem}.dzt-hero{padding:1.3rem 1.15rem;border-radius:17px}.dzt-hero h1{font-size:1.85rem}.dzt-brandbar{padding-top:.1rem}.dzt-dashboard{padding:1rem;border-radius:15px}.dzt-card{min-height:0;padding:1rem;border-radius:15px}[data-testid="stHorizontalBlock"]{flex-wrap:wrap;gap:.55rem}[data-testid="stHorizontalBlock"]>div{min-width:100%}.stRadio [role="radiogroup"]{gap:.25rem}.stRadio [role="radiogroup"] label{margin-right:.2rem}}
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

def open_textbook_topic(book_id: str, chapter_index: int, topic_id: str) -> None:
    """打开教材语境下的知识页，避免跳入实验知识中心。"""
    st.session_state.textbook_context = {
        "book_id": book_id, "chapter_index": chapter_index, "topic_id": topic_id,
    }
    repository.record_textbook_visit(book_id, chapter_index, topic_id)
    set_stage(24)

TEXTBOOK_SEARCH_INDEX = build_textbook_index(BOOK_EDITION_MAPPINGS)

def progress_map():
    result = {}
    for experiment_id in catalog:
        experiment_knowledge = KnowledgeBase(experiment_id)
        card_ids = [item["id"] for item in cards_for_experiment(experiment_id)]
        result[experiment_id] = calculate_experiment_progress(
            repository, experiment_id, experiment_knowledge.scenario_ids, card_ids
        )
    return result

def textbook_progress(book_id: str) -> dict[str, object]:
    """汇总教材映射知识点的学习进度，不改变原有课程和实验成绩。"""
    book = BOOK_EDITION_MAPPINGS[book_id]
    topic_ids = [topic_id for chapter in book["chapters"] for topic_id in chapter["topic_ids"]]
    learned = set().union(*(repository.learned_cards(item) for item in catalog))
    learned_count = sum(topic_id in learned for topic_id in topic_ids)
    return {
        "learned": learned_count,
        "total": len(topic_ids),
        "completion": learned_count / len(topic_ids) if topic_ids else 0.0,
    }

def open_search_result(item: dict[str, object]) -> None:
    """从搜索、收藏或最近学习直达教材单元/知识点。"""
    book_id = str(item["book_id"])
    chapter_index = int(item["chapter_index"])
    topic_id = item.get("topic_id")
    if topic_id:
        open_textbook_topic(book_id, chapter_index, str(topic_id))
    else:
        st.session_state.selected_textbook_id = book_id
        st.session_state.selected_textbook_chapter = chapter_index
        set_stage(20)

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

def start_textbook_unit_assessment(book_id: str, chapter_index: int, pretest: bool = False) -> None:
    """从同一单元知识范围抽题，沿用原有答题、错题和备份体系。"""
    unit = BOOK_EDITION_MAPPINGS[book_id]["chapters"][chapter_index]
    pool = [question for chapter_id in unit["quiz_chapter_ids"] for question in questions_for_chapter(chapter_id)]
    count = 3 if pretest else 5
    selected = secrets.SystemRandom().sample(pool, min(count, len(pool)))
    st.session_state.quiz_state = {
        "chapter_id": unit["quiz_chapter_ids"][0],
        "mode": "textbook_unit_pretest" if pretest else "textbook_unit_assessment",
        "question_ids": [item.id for item in selected], "index": 0, "answers": [], "answered": False,
        "book_id": book_id, "book_chapter_index": chapter_index,
    }
    set_stage(10)

def textbook_unit_effect(book_id: str, chapter_index: int) -> dict[str, object]:
    """基于既有测验记录计算最近一次学前、学后成绩。"""
    unit = BOOK_EDITION_MAPPINGS[book_id]["chapters"][chapter_index]
    history = repository.quiz_history(unit["quiz_chapter_ids"][0], 100)
    pretests = [item for item in history if item["mode"] == "textbook_unit_pretest"]
    posttests = [item for item in history if item["mode"] == "textbook_unit_assessment"]
    def score(items):
        return items[0]["correct_count"] / items[0]["total_count"] if items and items[0]["total_count"] else None
    before, after = score(pretests), score(posttests)
    return {"before": before, "after": after,
            "improvement": after - before if before is not None and after is not None else None}

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

def start_capstone(course_id: str) -> None:
    task = task_for_course(course_id)
    st.session_state.capstone_state = CapstoneTaskSession(task["id"]).to_dict()
    st.session_state.pop("capstone_report_ready", None)
    st.session_state.selected_course_id = course_id
    set_stage(19)

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

def start_targeted_practice(experiment_id: str, scenario_id: str) -> None:
    target = KnowledgeBase(experiment_id)
    new_session = DiagnosticSession(target)
    new_session.start(True, scenario_id=scenario_id)
    st.session_state.selected_experiment_id = experiment_id
    st.session_state.selected_symptom_id = target.default_symptom_id
    st.session_state.practice_mode = "随机故障练习"
    save_session(new_session); set_stage(3)

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

def render_experiment_selector() -> None:
    st.markdown('<div class="dzt-section-label">Virtual training</div>', unsafe_allow_html=True)
    st.subheader("选择一个虚拟实训")
    st.caption("故障诊断是实训方式之一。所有任务只使用网页模拟资料。")
    experiment_options = list(catalog)
    card_columns = st.columns(len(experiment_options))
    for column, experiment_id in zip(card_columns, experiment_options):
        experiment_knowledge = KnowledgeBase(experiment_id)
        experiment = catalog[experiment_id]
        with column:
            st.markdown(
                f'<div class="dzt-card"><h3>{experiment["name"]}</h3>'
                f'<p><b>{len(experiment_knowledge.scenario_ids)} 类</b>模拟故障</p>'
                f'<p>{experiment["scope"]}</p></div>', unsafe_allow_html=True,
            )
    if st.button("🎯 开始跨实验综合训练", use_container_width=True):
        start_comprehensive_training(); st.rerun()
    chosen_experiment_id = st.radio(
        "实训项目", experiment_options, index=experiment_options.index(knowledge.experiment_id),
        format_func=lambda item: catalog[item]["name"], horizontal=True,
    )
    mode_options = ["随机故障练习", "引导学习模式", "自由诊断演示"]
    saved_mode = st.session_state.get("practice_mode", mode_options[0])
    mode = st.segmented_control(
        "训练方式", mode_options,
        default=saved_mode if saved_mode in mode_options else mode_options[0],
        help="随机练习自动评分；引导模式先讲解；自由诊断用于探索规则。",
    ) or mode_options[0]
    chosen_knowledge = KnowledgeBase(chosen_experiment_id)
    selected_symptom_id = chosen_knowledge.default_symptom_id
    if mode == "自由诊断演示":
        symptom_ids = list(chosen_knowledge.symptoms)
        selected_symptom_id = st.radio(
            "选择模拟故障现象", symptom_ids,
            format_func=lambda item: chosen_knowledge.symptoms[item],
        )
    with st.expander("使用范围与隐私说明"):
        st.write("应用不连接真实设备，也不要求姓名、邮箱或账号。")
        if config.storage_is_temporary or not repository.persistent:
            st.write("当前云端成绩为临时数据，服务休眠、重启或更新后可能丢失。")
    st.warning(DISCLAIMER)
    if st.button("继续安全确认", type="primary", use_container_width=True):
        st.session_state.selected_experiment_id = chosen_experiment_id
        st.session_state.practice_mode = mode
        st.session_state.selected_symptom_id = selected_symptom_id
        st.session_state.pop("diagnostic_state", None)
        set_stage(2); st.rerun()

if "stage" not in st.session_state:
    st.session_state.stage = 1
stage = st.session_state.stage
if stage not in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25}:
    stage = 1
    st.session_state.stage = 1
    st.session_state.pop("diagnostic_state", None)
session = get_session()

if stage == 1:
    st.markdown(f'<div class="dzt-hero"><h1>⚡ 电诊通</h1><p>把电气知识、识图训练和模拟实训连成一条学习路径 · v{config.version}</p></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="dzt-brandbar"><strong>⚡ 电诊通</strong><span>教学模拟 · v{config.version}</span></div>', unsafe_allow_html=True)
steps = ["选择实验", "安全确认", "逐步排查", "学习报告"]
if stage in {2, 3, 4}:
    st.progress(stage / 4, text=f"第 {stage} 步 / 4：{steps[stage - 1]}")

with st.sidebar:
    st.markdown("### ⚡ 电诊通")
    st.caption("电气专业教材学习平台")
    if st.button("🏠 学习首页", use_container_width=True): set_stage(1); st.rerun()
    if st.button("📚 教材中心", use_container_width=True): set_stage(20); st.rerun()
    if st.button("📝 我的复习本", use_container_width=True): set_stage(25); st.rerun()
    if st.button("🧠 知识", use_container_width=True): open_knowledge(); st.rerun()
    if st.button("✍️ 练习", use_container_width=True): set_stage(21); st.rerun()
    if st.button("🧰 实训", use_container_width=True): set_stage(22); st.rerun()
    if st.button("📊 我的学习", use_container_width=True): set_stage(5); st.rerun()
    st.divider()
    st.caption("实训与诊断为辅助学习工具")
    st.warning("仅限教学模拟，不可用于真实设备诊断。")
    with st.expander("更多工具"):
        if st.button("📘 知识中心", use_container_width=True): open_knowledge(); st.rerun()
        if st.button("📚 内容与资料", use_container_width=True): set_stage(17); st.rerun()
        if st.button("🧭 第一次使用", use_container_width=True): set_stage(7); st.rerun()
        if st.button("📖 电气术语", use_container_width=True): set_stage(9); st.rerun()
        if st.button("💾 学习档案备份", use_container_width=True): set_stage(12); st.rerun()
        if config.issues_url:
            st.link_button("🛠️ 程序故障或专业纠错", config.issues_url, use_container_width=True)
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
    book_id = next(iter(BOOK_EDITION_MAPPINGS))
    home_book = BOOK_EDITION_MAPPINGS[book_id]
    book_state = textbook_progress(book_id)
    last_chapter_id = st.session_state.get("last_learning_chapter_id")
    valid_chapter_ids = {item["id"] for item in ALL_CHAPTERS}
    last_chapter = chapter_by_id(last_chapter_id) if last_chapter_id in valid_chapter_ids else ALL_CHAPTERS[0]
    st.markdown('<div class="dzt-section-label">Start learning</div>', unsafe_allow_html=True)
    st.subheader("今天想学什么？")
    st.markdown(
        f'<div class="dzt-dashboard"><h3>📘 {home_book["title"]}</h3>'
        f'<p>{home_book["author"]} · {home_book["edition"]}</p>'
        f'<p>当前试点教材 · 已学习 {book_state["learned"]}/{book_state["total"]} 个知识点</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("进入教材学习", type="primary", use_container_width=True):
        set_stage(20); st.rerun()
    recent_lessons = repository.recent_textbook_visits(1)
    if recent_lessons:
        recent_lesson = recent_lessons[0]
        recent_title = KNOWLEDGE_TOPICS.get(recent_lesson["topic_id"], {}).get("title", "上次知识点")
        if st.button(f"继续教材学习 · {recent_title}", use_container_width=True):
            open_search_result(recent_lesson); st.rerun()
    if last_chapter_id in valid_chapter_ids:
        if st.button(f"继续上次学习 · {last_chapter['title']}", use_container_width=True):
            st.session_state.selected_chapter_id = last_chapter["id"]
            set_stage(8); st.rerun()
    st.caption("其他学习方式")
    simple_entries = st.columns(3)
    if simple_entries[0].button("🗺️ 课程路线", use_container_width=True): set_stage(23); st.rerun()
    if simple_entries[1].button("✍️ 练习复习", use_container_width=True): set_stage(21); st.rerun()
    if simple_entries[2].button("🧰 实训诊断", use_container_width=True): set_stage(22); st.rerun()
    st.caption("教材知识学习为主 · 练习、识图、实训和诊断用于巩固")

elif stage == 23:
    current_progress = progress_map()
    overview = learning_overview(repository, current_progress)
    tasks = overview["tasks"]
    recommended_id = overview["recommended_experiment_id"]
    last_chapter_id = st.session_state.get("last_learning_chapter_id")
    last_chapter = chapter_by_id(last_chapter_id) if last_chapter_id in {item["id"] for item in ALL_CHAPTERS} else ALL_CHAPTERS[0]
    book_id = next(iter(BOOK_EDITION_MAPPINGS))
    home_book = BOOK_EDITION_MAPPINGS[book_id]
    book_state = textbook_progress(book_id)
    st.markdown('<div class="dzt-section-label">Textbook first</div>', unsafe_allow_html=True)
    st.subheader("从教材开始学习")
    st.markdown(
        f'<div class="dzt-dashboard"><h3>📘 {home_book["title"]}</h3>'
        f'<p>{home_book["author"]} · {home_book["publisher"]} · {home_book["edition"]}</p>'
        f'<p>按教材目录学习知识，再用练习、识图、实训和诊断巩固。</p></div>',
        unsafe_allow_html=True,
    )
    st.progress(book_state["completion"], text=f"教材知识点进度 {book_state['learned']} / {book_state['total']}")
    textbook_actions = st.columns(2)
    if textbook_actions[0].button("进入教材目录", type="primary", use_container_width=True):
        set_stage(20); st.rerun()
    if textbook_actions[1].button(f"继续学习 · {last_chapter['title']}", use_container_width=True):
        st.session_state.selected_chapter_id = last_chapter["id"]
        set_stage(8); st.rerun()
    st.markdown(
        f'<div class="dzt-dashboard"><h3>今日学习建议</h3>'
        f'<p>从“{last_chapter["title"]}”继续，完成约10分钟的小任务。</p></div>',
        unsafe_allow_html=True,
    )
    dashboard_metrics = st.columns(3)
    dashboard_metrics[0].metric("今日任务", f"{tasks['completed_count']} / 3")
    dashboard_metrics[1].metric("连续学习", f"{overview['streak']} 天")
    dashboard_metrics[2].metric("待复习", len(review_overview(repository)["pending"]))
    home_actions = st.columns(2)
    if home_actions[0].button(f"继续学习 · {last_chapter['title']}", type="primary", use_container_width=True):
        st.session_state.selected_chapter_id = last_chapter["id"]
        set_stage(8); st.rerun()
    if home_actions[1].button("打开今日复习", use_container_width=True):
        set_stage(18); st.rerun()
    with st.expander(f"今日学习任务 · 已完成 {tasks['completed_count']} / 3"):
        st.progress(tasks["completion"])
        st.write(f"知识卡：{'已完成' if tasks['knowledge'] else '待完成'} · "
                 f"引导学习：{'已完成' if tasks['guided'] else '待完成'} · "
                 f"随机练习：{min(tasks['random_practices'], 2)} / 2")
        if not tasks["knowledge"] and st.button("开始今日知识卡", use_container_width=True):
            target_cards = cards_for_experiment(recommended_id)
            learned = repository.learned_cards(recommended_id)
            target = next((item for item in target_cards if item["id"] not in learned), target_cards[0])
            st.session_state.selected_experiment_id = recommended_id
            open_knowledge(target["id"]); st.rerun()
        if not tasks["guided"] and st.button("开始今日引导学习", use_container_width=True):
            prepare_task(recommended_id, "引导学习模式"); st.rerun()
        if not tasks["practice"] and st.button("开始今日随机练习", use_container_width=True):
            prepare_task(recommended_id, "随机故障练习"); st.rerun()
    with st.expander("第一次来？用5分钟体验完整流程"):
        st.write("知识卡 → 识图 → 模拟排查 → 迷你测验 → 学习总结，无需解锁课程。")
        if st.button("⚡ 开始5分钟体验", type="primary", use_container_width=True):
            start_quick_experience(); st.rerun()
    if not st.session_state.get("onboarding_seen"):
        st.info("👋 第一次使用？先用1分钟了解如何阅读模拟资料和选择答案。")
        if st.button("开始1分钟新手引导", type="primary", use_container_width=True):
            set_stage(7); st.rerun()
    st.markdown('<div class="dzt-section-label">Supporting courses</div>', unsafe_allow_html=True)
    st.subheader("配套课程与知识路线")
    if last_chapter_id in {item["id"] for item in ALL_CHAPTERS}:
        last_chapter = chapter_by_id(last_chapter_id)
        if st.button(f"继续上次学习：{last_chapter['title']}", type="primary", use_container_width=True):
            st.session_state.selected_chapter_id = last_chapter_id
            set_stage(8); st.rerun()
    course_columns = st.columns(2)
    for index, course in enumerate(COURSES):
        unlocked = course_is_unlocked(repository, course["id"])
        course_chapters = COURSE_CHAPTERS[course["id"]]
        course_progress = sum(chapter_progress(repository, item).completion for item in course_chapters) / len(course_chapters)
        with course_columns[index % 2]:
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
    st.markdown("### 课程综合实训")
    capstone = task_for_course(selected_course_id)
    capstone_unlocked = task_is_unlocked(repository, selected_course_id)
    capstone_summary = repository.capstone_summary(selected_course_id)
    st.write(f"**{capstone['title']}** · {capstone['goal']}")
    if capstone_summary["attempts"]:
        st.write(f"已练习 {capstone_summary['attempts']} 次 · 最好成绩 {capstone_summary['best_score']:.0%} · "
                 f"{'已完成' if capstone_summary['passed_count'] else '待提高'}")
    elif not capstone_unlocked:
        st.caption("通过本课程全部章节测验后开放；完成5个判断和学习反思，至少答对4题。")
    if st.button("开始课程综合实训", type="primary", disabled=not capstone_unlocked,
                 key=f"capstone_{selected_course_id}", use_container_width=True):
        start_capstone(selected_course_id); st.rerun()

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
    st.markdown('<div class="dzt-section-label">Supporting tools</div>', unsafe_allow_html=True)
    next_columns = st.columns(3)
    if next_columns[0].button("📚 返回教材中心", use_container_width=True): set_stage(20); st.rerun()
    if next_columns[1].button("✍️ 进入练习中心", use_container_width=True): set_stage(21); st.rerun()
    if next_columns[2].button("🧰 进入虚拟实训", use_container_width=True): set_stage(22); st.rerun()

elif stage == 2:
    st.markdown('<div class="dzt-section-label">Simulation setup</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="dzt-section-label">Guided diagnosis</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="dzt-section-label">Learning report</div>', unsafe_allow_html=True)
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
        if st.session_state.get("review_origin") and scored_practice:
            if st.button("返回复习清单", type="primary", use_container_width=True):
                st.session_state.pop("review_origin", None); set_stage(18); st.rerun()
        if scored_practice:
            if st.button("练习薄弱项", type="primary", use_container_width=True):
                start_weak_practice(); st.rerun()
            if st.button("再来一题", use_container_width=True):
                start_random_practice(); st.rerun()
        if st.button("返回实验首页", use_container_width=True):
            st.session_state.pop("diagnostic_state", None); st.session_state.pop("review_origin", None); set_stage(1); st.rerun()
        st.warning(DISCLAIMER)

elif stage == 5:
    st.markdown('<div class="dzt-section-label">My learning</div>', unsafe_allow_html=True)
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
    mastery_overview = review_overview(repository)
    mastery_metrics = st.columns(3)
    mastery_metrics[0].metric("待复习", len(mastery_overview["pending"]))
    mastery_metrics[1].metric("已消除薄弱点", len(mastery_overview["mastered"]))
    mastery_metrics[2].metric("最近7天掌握", mastery_overview["recently_mastered"])
    kind_names = {"quiz":"错题", "diagram":"识图", "fault":"故障"}
    mastery_rows = [{"类型":name, "待复习":sum(item.kind == kind for item in mastery_overview["pending"]), "已掌握":sum(item.kind == kind for item in mastery_overview["mastered"])} for kind,name in kind_names.items()]
    render_markdown_table(["类型", "待复习", "已掌握"], mastery_rows)
    if st.button("打开个性化复习清单", type="primary", use_container_width=True):
        set_stage(18); st.rerun()
    st.subheader("教材学习进度")
    notebook_columns = st.columns(2)
    notebook_columns[0].metric("个人学习笔记", len(repository.study_notes()))
    notebook_columns[1].metric("收藏知识点", len(repository.textbook_bookmarks()))
    if st.button("打开我的复习本", use_container_width=True):
        set_stage(25); st.rerun()
    textbook_rows = []
    for book_id, book in BOOK_EDITION_MAPPINGS.items():
        item = textbook_progress(book_id)
        textbook_rows.append({
            "教材": book["title"], "版本": book["edition"],
            "知识点": f"{item['learned']}/{item['total']}", "完成度": f"{item['completion']:.0%}",
        })
    render_markdown_table(["教材", "版本", "知识点", "完成度"], textbook_rows)
    if st.button("继续教材学习", type="primary", use_container_width=True):
        set_stage(20); st.rerun()
    last_chapter_id = st.session_state.get("last_learning_chapter_id")
    if last_chapter_id in {item["id"] for item in ALL_CHAPTERS}:
        last_chapter = chapter_by_id(last_chapter_id)
        st.info(f"最近学习位置：{last_chapter['title']} · 下一步：{recommended_chapter_action(repository, last_chapter)}")
        if st.button("继续最近章节", use_container_width=True):
            st.session_state.selected_chapter_id = last_chapter_id; set_stage(8); st.rerun()
    st.subheader("配套课程完成情况")
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
        capstone_item = repository.capstone_summary(course["id"])
        if capstone_item["attempts"]:
            st.caption(f"综合实训：{capstone_item['attempts']} 次 · 最好成绩 {capstone_item['best_score']:.0%} · "
                       f"{'已完成' if capstone_item['passed_count'] else '待提高'}")
        elif task_is_unlocked(repository, course["id"]):
            st.caption("综合实训已开放，尚未开始。")
    st.subheader("课程综合实训")
    overall_capstone = repository.capstone_summary()
    capstone_metrics = st.columns(3)
    capstone_metrics[0].metric("实训次数", overall_capstone["attempts"])
    capstone_metrics[1].metric("完成次数", overall_capstone["passed_count"])
    capstone_metrics[2].metric("最好成绩", f"{overall_capstone['best_score']:.0%}" if overall_capstone["best_score"] is not None else "暂无")
    recent_capstones = repository.capstone_history(limit=4)
    if recent_capstones:
        capstone_rows = [{"课程": next(item["title"] for item in COURSES if item["id"] == record["course_id"]),
                          "成绩": f"{record['correct_steps']}/{record['total_steps']}",
                          "状态": "已完成" if record["passed"] else "待提高",
                          "时间": record["completed_at"].replace("T", " ")[:16]}
                         for record in recent_capstones]
        render_markdown_table(["课程", "成绩", "状态", "时间"], capstone_rows)
    else:
        st.caption("通过任一课程的全部章节测验后，可完成该课程综合实训。")
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

    # 课程知识中心同时承载不属于故障实验的原理卡片，例如识图与星—三角课程。
    available_cards = tuple({"id": card_id, **card} for card_id, card in KNOWLEDGE_CARDS.items())
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
    st.markdown('<div class="dzt-section-label">Chapter learning</div>', unsafe_allow_html=True)
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

    if chapter["id"].startswith("star_delta_"):
        st.markdown("### 启动阶段状态演示")
        st.caption("点击阶段查看当前有效角色与进入下一阶段的条件。只表达抽象逻辑。")
        stage_title = st.radio(
            "选择阶段", [item["title"] for item in STAR_DELTA_STAGES], horizontal=True,
            key=f"star_delta_stage_{chapter['id']}",
        )
        stage_item = next(item for item in STAR_DELTA_STAGES if item["title"] == stage_title)
        role_html = "<br>".join(f"• {item}" for item in stage_item["roles"])
        st.markdown(
            f"<div class='dzt-stage'><strong>{stage_item['title']}</strong><p>{stage_item['description']}</p>"
            f"<p>{role_html}</p><p><strong>下一条件：</strong>{stage_item['next_condition']}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(" → ".join(item["title"] for item in STAR_DELTA_STAGES))

    time_demos = demos_for_chapter(chapter["id"])
    if time_demos:
        st.markdown("### 时间过程状态演示")
        st.caption("点击阶段观察输入、等待和输出的先后关系。这里只表达抽象状态。")
        demo_label = time_demos[0][0]
        if len(time_demos) > 1:
            demo_label = st.radio(
                "选择延时类型", [item[0] for item in time_demos], horizontal=True,
                key=f"time_demo_type_{chapter['id']}",
            )
        demo_stages = next(stages for label, stages in time_demos if label == demo_label)
        time_stage_title = st.radio(
            "选择过程阶段", [item["title"] for item in demo_stages], horizontal=True,
            key=f"time_demo_stage_{chapter['id']}_{demo_label}",
        )
        time_stage = next(item for item in demo_stages if item["title"] == time_stage_title)
        time_roles = "<br>".join(f"• {item}" for item in time_stage["roles"])
        st.markdown(
            f"<div class='dzt-stage'><strong>{time_stage['title']}</strong>"
            f"<p>{time_stage['description']}</p><p>{time_roles}</p>"
            f"<p><strong>下一条件：</strong>{time_stage['next_condition']}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(" → ".join(item["title"] for item in demo_stages))

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
            st.session_state.pop("quiz_state", None); st.session_state.pop("review_origin", None); set_stage(8); st.rerun()

elif stage == 11:
    quiz = st.session_state.get("quiz_state", {})
    result = quiz.get("record")
    if not result:
        st.warning("没有可显示的测验结果。")
    else:
        chapter = chapter_by_id(quiz["chapter_id"])
        score = result["correct_count"] / result["total_count"]
        unit_pretest = quiz.get("mode") == "textbook_unit_pretest"
        unit_assessment = quiz.get("mode") == "textbook_unit_assessment"
        unit_mode = unit_pretest or unit_assessment
        st.subheader("📋 学前小测报告" if unit_pretest else ("📋 单元评测报告" if unit_assessment else "📋 章节测验报告"))
        if unit_mode:
            book = BOOK_EDITION_MAPPINGS[quiz["book_id"]]
            mapped_chapter = book["chapters"][quiz["book_chapter_index"]]
            st.markdown(f"### {mapped_chapter['title']}")
        else:
            st.markdown(f"### {chapter['title']}")
        st.metric("本次成绩", f"{result['correct_count']} / {result['total_count']}（{score:.0%}）")
        if unit_assessment:
            effect = textbook_unit_effect(quiz["book_id"], quiz["book_chapter_index"])
            if effect["before"] is not None:
                st.metric("学习效果", f"{effect['before']:.0%} → {score:.0%}",
                          delta=f"{score - effect['before']:+.0%}")
        if unit_pretest:
            st.info("这是学习起点记录，不计入单元掌握成绩。完成小课后再参加学后评测。")
        elif result["passed"]:
            st.success("已达到70%通过标准，单元评测完成。" if unit_assessment else "已达到60%通过标准，本章测验完成。")
        else:
            st.warning("尚未达到70%，建议先复习下方错题再测一次。" if unit_assessment else "尚未达到60%，建议先复习下方错题再测一次。")
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
                    if unit_mode and card_id in mapped_chapter["topic_ids"]:
                        open_textbook_topic(quiz["book_id"], quiz["book_chapter_index"], card_id)
                    else:
                        chapter = chapter_by_id(question.chapter_id)
                        st.session_state.selected_experiment_id = chapter["experiment_id"] or DEFAULT_EXPERIMENT_ID
                        open_knowledge(card_id)
                    st.rerun()
                if action_columns[1].button("再做一道相似题", key=f"similar_{question.id}", use_container_width=True):
                    start_similar_quiz(question.id); st.rerun()
        st.warning("测验仅用于电气知识学习，不得据此进行真实带电测量、拆线或送电操作。")
        if wrong_answers and unit_mode:
            first_wrong_card = card_id_for_question(wrong_answers[0]["question_id"])
            if first_wrong_card in mapped_chapter["topic_ids"] and st.button("返回教材复习薄弱知识点", type="primary", use_container_width=True):
                open_textbook_topic(quiz["book_id"], quiz["book_chapter_index"], first_wrong_card); st.rerun()
        elif wrong_answers and st.button("立即复习本章错题", type="primary", use_container_width=True):
            start_chapter_quiz(quiz["chapter_id"], True); st.rerun()
        if st.session_state.get("review_origin"):
            if st.button("返回复习清单", type="primary", use_container_width=True):
                st.session_state.pop("review_origin", None); st.session_state.pop("quiz_state", None)
                set_stage(18); st.rerun()
        if st.button("再测一次", use_container_width=True):
            if unit_mode:
                start_textbook_unit_assessment(quiz["book_id"], quiz["book_chapter_index"], pretest=unit_pretest)
            else:
                start_chapter_quiz(quiz["chapter_id"])
            st.rerun()
        if st.button("返回教材单元" if unit_mode else "返回本章", use_container_width=True):
            st.session_state.pop("quiz_state", None); st.session_state.pop("review_origin", None)
            if unit_mode:
                st.session_state.selected_textbook_chapter = quiz["book_chapter_index"]
                set_stage(20)
            else:
                st.session_state.selected_chapter_id = quiz["chapter_id"]
                set_stage(8)
            st.rerun()

elif stage == 12:
    st.subheader("💾 学习档案导出与恢复")
    st.info("档案只包含课程、实验、答案、得分和时间，不包含姓名、学校、邮箱、账号或设备信息。")
    if config.storage_is_temporary or not repository.persistent:
        st.warning("当前记录可能在服务休眠、重启、更新或会话结束后丢失，建议下载JSON备份。")
    snapshot = repository.export_snapshot()
    record_count = sum(len(items) for items in snapshot.values())
    metrics = st.columns(5)
    metrics[0].metric("练习记录", len(snapshot["practice_records"]))
    metrics[1].metric("学习活动", len(snapshot["learning_activities"]))
    metrics[2].metric("章节测验", len(snapshot["quiz_sessions"]))
    metrics[3].metric("识图训练", len(snapshot["diagram_practice_records"]))
    metrics[4].metric("综合实训", len(snapshot["capstone_task_records"]))
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
                f"识图训练 {preview.diagram_practice_records} 条、综合实训 {preview.capstone_task_records} 条。"
            )
            st.caption("导入按记录唯一标识去重；已有记录会保留，不会被较差或修改后的记录覆盖。")
            confirm_import = st.checkbox("我确认将以上匿名学习记录合并到当前档案")
            if st.button("确认导入", type="primary", disabled=not confirm_import, use_container_width=True):
                result = import_archive(repository, archive, confirmed=True)
                added = (result["practice_records"] + result["learning_activities"]
                         + result["quiz_sessions"] + result["diagram_practice_records"]
                         + result["capstone_task_records"])
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
            first_selected = training.first_answers.get(step["id"])
            if first_selected is not None and first_selected != step["answer"] and case["chapter_id"].startswith("star_delta_"):
                feedback = diagram_choice_feedback(training.case_id, training.index, first_selected)
                st.markdown(f"<div class='dzt-stage'><strong>当前阶段：{feedback['stage']}</strong>"
                            f"<p><strong>应判断：</strong>{feedback['role']}</p>"
                            f"<p><strong>为什么：</strong>{feedback['reason']}</p>"
                            f"<p><strong>推荐复习：</strong>{feedback['card_title']}</p></div>", unsafe_allow_html=True)
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
            if st.session_state.get("review_origin"):
                if st.button("返回复习清单", type="primary", use_container_width=True):
                    st.session_state.pop("review_origin", None); st.session_state.pop("diagram_training", None)
                    set_stage(18); st.rerun()
            chapter_cases = cases_for_chapter(case["chapter_id"])
            next_case = next((item for item in chapter_cases if item["id"] != training.case_id), chapter_cases[0])
            if st.button("再练一个案例", type="primary", use_container_width=True):
                start_diagram_training(next_case["id"]); st.rerun()
            if st.button("返回本章", use_container_width=True):
                st.session_state.selected_chapter_id = case["chapter_id"]
                st.session_state.pop("diagram_training", None); st.session_state.pop("review_origin", None); set_stage(8); st.rerun()

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
        star_summary = None
        if course_id == FOURTH_COURSE["id"]:
            star_summary = build_star_delta_course_summary(repository)
            st.markdown("### 星—三角课程总结")
            summary_metrics = st.columns(3)
            summary_metrics[0].metric("完成章节", f"{star_summary['completed_chapters']} / 3")
            summary_metrics[1].metric("识图训练", f"{star_summary['diagram_attempts']} 次")
            summary_metrics[2].metric("识图正确率", f"{star_summary['diagram_accuracy']:.0%}")
            for principle in star_summary["principles"]:
                st.write(f"- {principle}")
            if star_summary["weak_cards"]:
                st.warning("建议复习：" + "、".join(item["title"] for item in star_summary["weak_cards"]))
            else:
                st.success("当前没有已记录的薄弱知识点，可继续巩固阶段顺序。")
        report_lines = ["电诊通｜课程学习总结", course["title"],
                        f"本次成绩：{result['correct_count']}/{result['total_count']}（{score:.0%}）",
                        f"内容来源：本次题目通过 {len(exam_sources)} 个知识主题映射到官方资料；核对状态请见应用内内容与资料中心。",
                        "能力情况：", *[f"- {item['name']}：{item['accuracy']:.0%}" for item in competency_report(answers)],
                        "", "仅用于教学学习，不是职业资格、实训考核或能力认证证书。"]
        if star_summary:
            report_lines.extend(("", star_delta_summary_text(star_summary)))
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
    capstone_covered = sum(bool(provenance_for_diagram(step["card_id"] for step in task["steps"])["sources"])
                           for task in CAPSTONE_TASKS.values())
    st.info(f"课程综合实训来源覆盖：{capstone_covered} / {len(CAPSTONE_TASKS)}。")
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

elif stage == 18:
    st.subheader("🎯 我的10分钟复习清单")
    st.caption("根据当前设备上的错题、识图错误和模拟故障成绩即时生成；不上传数据，也不额外计分。")
    mastery = review_overview(repository)
    review_tasks = build_review_plan(repository)
    total_minutes = sum(item.minutes for item in review_tasks)
    if mastery["pending"]:
        st.info(f"今天建议完成 {len(review_tasks)} 项，预计 {total_minutes} 分钟。完成后返回本页，清单会按最新记录更新。")
    else:
        st.success("当前复习任务已完成。下面提供一项自由巩固建议，不代表存在新的薄弱点。")
    for index, item in enumerate(review_tasks, 1):
        st.markdown(f'<div class="dzt-card"><h3>{index}. {item.title} · {item.minutes}分钟</h3><p>{item.reason}</p></div>', unsafe_allow_html=True)
        if item.kind == "knowledge":
            if st.button(f"开始第{index}项", key=f"review_task_{index}_{item.reference_id}", type="primary" if index == 1 else "secondary", use_container_width=True):
                st.session_state.selected_experiment_id = item.experiment_id
                open_knowledge(item.reference_id); st.rerun()
        elif item.kind == "quiz":
            if st.button(f"开始第{index}项", key=f"review_task_{index}_{item.reference_id}", type="primary" if index == 1 else "secondary", use_container_width=True):
                st.session_state.review_origin = True
                start_similar_quiz(item.reference_id); st.rerun()
        elif item.kind == "diagram":
            if st.button(f"开始第{index}项", key=f"review_task_{index}_{item.reference_id}", type="primary" if index == 1 else "secondary", use_container_width=True):
                st.session_state.review_origin = True
                start_diagram_training(item.reference_id); st.rerun()
        elif item.kind == "fault":
            if st.button(f"开始第{index}项", key=f"review_task_{index}_{item.reference_id}", type="primary" if index == 1 else "secondary", use_container_width=True):
                st.session_state.review_origin = True
                start_targeted_practice(item.experiment_id, item.reference_id); st.rerun()
    if mastery["statuses"]:
        st.markdown("### 薄弱项状态")
        kind_names = {"quiz":"错题", "diagram":"识图", "fault":"故障"}
        status_rows = [{"类型":kind_names[item.kind], "状态":"已掌握" if item.mastered else "待复习", "连续正确":f"{item.consecutive_correct}/2", "历史错误":item.error_count} for item in mastery["statuses"]]
        render_markdown_table(["类型", "状态", "连续正确", "历史错误"], status_rows)
    st.warning("复习任务仅使用教学模拟记录生成，不代表真实设备能力评估或检修建议。")
    if st.button("返回学习中心", use_container_width=True):
        set_stage(5); st.rerun()

elif stage == 19:
    raw_capstone = st.session_state.get("capstone_state")
    try:
        capstone_session = CapstoneTaskSession.from_dict(raw_capstone or {})
    except (TypeError, ValueError, KeyError):
        st.warning("综合实训状态已失效，请返回课程重新开始。")
        if st.button("返回课程地图", use_container_width=True):
            st.session_state.pop("capstone_state", None); set_stage(1); st.rerun()
    else:
        task = capstone_session.task
        st.subheader(f"🧰 {task['title']}")
        st.info(f"**任务目标：** {task['goal']}")
        st.error(f"**模拟情境：** {task['scenario']}")
        st.warning(CAPSTONE_SAFETY)
        if not capstone_session.objective_complete:
            step = capstone_session.current_step
            st.progress(capstone_session.index / len(task["steps"]),
                        text=f"首次判断 {capstone_session.index + 1} / {len(task['steps'])}")
            st.markdown(f"### {step['prompt']}")
            first_selected = capstone_session.first_answers.get(step["id"])
            if first_selected is not None and first_selected != step["answer"]:
                st.warning(f"首次判断“{first_selected}”已记录。{step['explanation']}")
                st.info(f"推荐复习：{KNOWLEDGE_CARDS[step['card_id']]['title']}")
            selected = st.radio(
                "选择判断", [*step["options"], "不确定"], index=None,
                key=f"capstone_choice_{capstone_session.session_id}_{step['id']}_{len(capstone_session.first_answers)}",
            )
            if st.button("提交本步判断", type="primary", disabled=selected is None, use_container_width=True):
                solved = capstone_session.answer(selected)
                st.session_state.capstone_state = capstone_session.to_dict()
                if solved:
                    st.success(f"判断正确：{step['explanation']}")
                st.rerun()
            if capstone_session.step_solved:
                st.success(f"本步完成：{step['explanation']}")
                if st.button("进入下一步", type="primary", use_container_width=True):
                    capstone_session.next_step()
                    st.session_state.capstone_state = capstone_session.to_dict(); st.rerun()
            if st.button("退出本次实训", use_container_width=True):
                st.session_state.pop("capstone_state", None); set_stage(1); st.rerun()
        elif not st.session_state.get("capstone_report_ready"):
            score = capstone_session.correct_steps / len(task["steps"])
            st.progress(1.0, text=f"客观步骤完成 · 首次判断 {score:.0%}")
            st.markdown("### 学习反思")
            reflection = st.text_area(
                "请用20—300字说明本次判断中最重要的依据，以及下一次准备怎样改进。",
                value=capstone_session.reflection, max_chars=300, height=140,
                key=f"capstone_reflection_{capstone_session.session_id}",
            )
            length = len(reflection.strip())
            st.caption(f"当前 {length} 字；至少20字。请勿填写姓名、学校或真实设备信息。")
            if st.button("提交反思并生成报告", type="primary", disabled=not 20 <= length <= 300,
                         use_container_width=True):
                capstone_session.set_reflection(reflection)
                record = make_capstone_record(capstone_session)
                repository.save_capstone(record)
                st.session_state.capstone_state = capstone_session.to_dict()
                st.session_state.capstone_report_ready = True
                st.rerun()
        else:
            report = capstone_report_text(capstone_session)
            score = capstone_session.correct_steps / len(task["steps"])
            st.markdown("### 📋 综合实训学习报告")
            metrics = st.columns(3)
            metrics[0].metric("首次判断", f"{capstone_session.correct_steps} / {len(task['steps'])}")
            metrics[1].metric("正确率", f"{score:.0%}")
            metrics[2].metric("状态", "已完成" if capstone_session.passed else "待提高")
            if capstone_session.passed:
                st.success("已完成全部步骤、学习反思，并达到70%标准。")
            else:
                st.warning("已完成全部步骤和学习反思，但尚未达到70%；报告仍已保存。")
            st.markdown("### 判断过程与错因")
            for index, step in enumerate(task["steps"], 1):
                selected = capstone_session.first_answers[step["id"]]
                marker = "✅" if selected == step["answer"] else "❌"
                st.write(f"{marker} **{index}. {step['prompt']}**")
                st.caption(f"首次判断：{selected} · 正确判断：{step['answer']} · {step['explanation']}")
            card_ids = tuple(dict.fromkeys(step["card_id"] for step in task["steps"]))
            st.markdown("### 关联知识卡与复习建议")
            st.write("、".join(KNOWLEDGE_CARDS[item]["title"] for item in card_ids))
            if capstone_session.wrong_steps:
                weak_cards = tuple(dict.fromkeys(step["card_id"] for step in task["steps"]
                                                 if step["id"] in capstone_session.wrong_steps))
                st.warning("建议优先复习：" + "、".join(KNOWLEDGE_CARDS[item]["title"] for item in weak_cards))
            else:
                st.success("本次首次判断全部正确，可进入10分钟复习继续巩固。")
            st.markdown("### 我的学习反思")
            st.write(capstone_session.reflection)
            render_provenance(provenance_for_diagram(card_ids), "综合实训参考资料")
            st.download_button("下载实训学习报告", data=report.encode("utf-8"),
                               file_name="电诊通_课程综合实训报告.txt", mime="text/plain",
                               use_container_width=True)
            if st.button("再练一次", type="primary", use_container_width=True):
                st.session_state.pop("capstone_report_ready", None)
                start_capstone(task["course_id"]); st.rerun()
            if st.button("打开10分钟复习清单", use_container_width=True):
                st.session_state.pop("capstone_report_ready", None)
                st.session_state.pop("capstone_state", None); set_stage(18); st.rerun()
            if st.button("返回课程", use_container_width=True):
                st.session_state.selected_course_id = task["course_id"]
                st.session_state.pop("capstone_report_ready", None)
                st.session_state.pop("capstone_state", None); set_stage(1); st.rerun()

elif stage == 20:
    st.markdown('<div class="dzt-section-label">Textbook learning</div>', unsafe_allow_html=True)
    st.subheader("📚 我的教材书架")
    st.write("搜索教材、单元、知识点、公式或原创例题，也可以从收藏和最近学习继续。")
    st.caption("按教材学习：选择教材路线和章节，知识学习是主入口，练习与实训用于巩固。")
    st.info("教材只用于章节映射；平台不提供教材正文、扫描图片或课后题答案。")
    search_query = st.text_input(
        "搜索学习内容", placeholder="例如：接触器、自锁、串联条件、星三角",
        key="textbook_search_query",
    )
    search_results = search_textbooks(TEXTBOOK_SEARCH_INDEX, search_query)
    if search_query:
        st.markdown(f"### 搜索结果 · {len(search_results)}项")
        if not search_results:
            st.warning("暂未找到相关内容。可以减少关键词，或按教材目录浏览。")
        for result_index, item in enumerate(search_results):
            display_title = KNOWLEDGE_TOPICS.get(item.get("topic_id"), {}).get("title", item["title"])
            result_columns = st.columns([4, 1])
            result_columns[0].markdown(f"**{item['kind']} · {display_title}**  \n{item['subtitle']}")
            if result_columns[1].button("打开", key=f"search_open_{result_index}", use_container_width=True):
                open_search_result(item); st.rerun()
        st.divider()
    bookmarks = repository.textbook_bookmarks()
    recent_visits = repository.recent_textbook_visits(6)
    navigation_columns = st.columns(2)
    with navigation_columns[0]:
        st.markdown(f"### ⭐ 我的收藏 · {len(bookmarks)}")
        if not bookmarks:
            st.caption("打开知识点后点击收藏，常用内容会出现在这里。")
        for item_index, item in enumerate(bookmarks[:6]):
            topic = KNOWLEDGE_TOPICS.get(item["topic_id"])
            if topic and st.button(topic["title"], key=f"bookmark_open_{item_index}", use_container_width=True):
                target = next((entry for entry in TEXTBOOK_SEARCH_INDEX
                               if entry.get("book_id") == item["book_id"] and entry.get("topic_id") == item["topic_id"]), None)
                if target: open_search_result(target); st.rerun()
    with navigation_columns[1]:
        st.markdown("### 🕘 最近学习")
        if not recent_visits:
            st.caption("开始学习知识点后，这里会记录最近访问位置。")
        for item_index, item in enumerate(recent_visits):
            topic = KNOWLEDGE_TOPICS.get(item["topic_id"])
            if topic and st.button(topic["title"], key=f"recent_open_{item_index}", use_container_width=True):
                open_search_result(item); st.rerun()
    st.divider()
    st.markdown("### 全部教材")
    book_ids = list(BOOK_EDITION_MAPPINGS)
    if st.session_state.get("selected_textbook_id") not in book_ids:
        st.session_state.selected_textbook_id = book_ids[0]
    selected_book_id = st.selectbox(
        "教材与版本", book_ids,
        format_func=lambda item: f"{BOOK_EDITION_MAPPINGS[item]['title']} · {BOOK_EDITION_MAPPINGS[item]['edition']}",
        key="selected_textbook_id",
    )
    book = BOOK_EDITION_MAPPINGS[selected_book_id]
    book_metrics = st.columns(3)
    book_metrics[0].metric("作者", book["author"])
    book_metrics[1].metric("出版社", book["publisher"])
    book_metrics[2].metric("已上线项目", len(book.get("projects", ())))
    st.write(f"**ISBN：** {book['isbn']} · **出版时间：** {book['published_at']}")
    st.link_button("查看出版社公开书目信息", book["source_url"], use_container_width=True)
    st.caption(book["notice"])
    learned_topic_ids = set().union(*(repository.learned_cards(item) for item in catalog))
    st.markdown("### 教材项目学习进度")
    unit_rows = []
    all_book_topic_ids = []
    completed_case_ids = {item["case_id"] for item in repository.diagram_history(limit=1000)}
    for index, unit in enumerate(book["chapters"]):
        unit_topic_ids = list(unit["topic_ids"])
        all_book_topic_ids.extend(unit_topic_ids)
        completed = sum(topic_id in learned_topic_ids for topic_id in unit_topic_ids)
        knowledge_done = completed == len(unit_topic_ids)
        has_assessment = bool(unit["quiz_chapter_ids"])
        assessment_done = any(repository.quiz_summary(item)["passed_count"] for item in unit["quiz_chapter_ids"])
        diagram_done = bool(set(unit["case_ids"]) & completed_case_ids)
        if knowledge_done and not has_assessment:
            unit_status = "知识完成"
        elif knowledge_done and assessment_done and diagram_done:
            unit_status = "基本掌握"
        elif knowledge_done:
            unit_status = "待评测" if not assessment_done else "待识图巩固"
        elif completed:
            unit_status = "学习中"
        else:
            unit_status = "未开始"
        unit_rows.append({
            "项目": unit["project_title"], "单元": unit['title'],
            "知识点": f"{completed}/{len(unit_topic_ids)}",
            "状态": unit_status,
        })
    render_markdown_table(["项目", "单元", "知识点", "状态"], unit_rows)
    project_completed = sum(topic_id in learned_topic_ids for topic_id in all_book_topic_ids)
    st.progress(project_completed / len(all_book_topic_ids), text=f"教材知识学习 {project_completed}/{len(all_book_topic_ids)}")
    if project_completed == len(all_book_topic_ids):
        st.success("当前上线教材项目的知识小课已完成。可继续使用已有配套练习、识图和实训进行巩固。")
    chapter_index = st.selectbox(
        "选择章节", range(len(book["chapters"])),
        format_func=lambda item: f"{book['chapters'][item]['project_title']} · {book['chapters'][item]['title']}",
        key="selected_textbook_chapter",
    )
    mapped_chapter = book["chapters"][chapter_index]
    st.markdown(
        f'<div class="dzt-dashboard"><h3>{mapped_chapter["title"]}</h3>'
        f'<p>对应公开目录：{mapped_chapter["source_title"]}</p>'
        f'<p>{mapped_chapter["goal"]}</p></div>', unsafe_allow_html=True,
    )
    topics = topics_for_book_chapter(selected_book_id, chapter_index)
    learned_count = sum(topic["id"] in learned_topic_ids for topic in topics)
    st.progress(learned_count / len(topics), text=f"知识点学习 {learned_count} / {len(topics)}")
    learning_effect = textbook_unit_effect(selected_book_id, chapter_index) if mapped_chapter["quiz_chapter_ids"] else {"before": None, "after": None, "improvement": None}
    if learning_effect["before"] is not None:
        effect_columns = st.columns(2)
        effect_columns[0].metric("学前小测", f"{learning_effect['before']:.0%}")
        effect_columns[1].metric(
            "学后评测", f"{learning_effect['after']:.0%}" if learning_effect["after"] is not None else "待完成",
            delta=f"{learning_effect['improvement']:+.0%}" if learning_effect["improvement"] is not None else None,
        )
    unit_minutes = sum((lesson_for_topic(topic["id"]) or {}).get("minutes", 2) for topic in topics)
    st.caption(f"本单元共 {len(topics)} 个知识点 · 预计学习 {unit_minutes} 分钟")
    first_unlearned = next((topic["id"] for topic in topics if topic["id"] not in learned_topic_ids), topics[0]["id"])
    if st.button("继续本单元学习" if learned_count else "开始本单元学习", type="primary", use_container_width=True):
        open_textbook_topic(selected_book_id, chapter_index, first_unlearned); st.rerun()
    st.markdown("### 本单元知识点")
    topic_columns = st.columns(2)
    for index, topic in enumerate(topics):
        with topic_columns[index % 2]:
            st.markdown(
                f'<div class="dzt-card"><h3>{topic["title"]}</h3>'
                f'<p>{topic["summary"]}</p></div>', unsafe_allow_html=True,
            )
            if st.button("学习这个知识点", key=f"book_topic_{topic['id']}", use_container_width=True):
                open_textbook_topic(selected_book_id, chapter_index, topic["id"]); st.rerun()
    unit_example = example_for_unit(chapter_index)
    with st.expander(f"🧩 {unit_example['title']}"):
        st.write(f"**题目：** {unit_example['scenario']}")
        for step_index, step in enumerate(unit_example["steps"], 1):
            st.write(f"{step_index}. {step}")
        st.success(f"**结论：** {unit_example['answer']}")
        st.caption("平台原创例题，不是教材原题或课后题答案。")
    st.markdown("### 本单元练习与实训")
    action_columns = st.columns(3)
    action_columns[0].markdown("**单元评测**")
    if not mapped_chapter["quiz_chapter_ids"]:
        action_columns[0].caption("本项目专项题库将在后续版本加入；当前可完成每节即时检查与原创变式练习。")
    elif learning_effect["before"] is None:
        action_columns[0].caption("先完成3题学前小测，不计入掌握成绩。")
        if action_columns[0].button("开始学前小测", key=f"book_pretest_start_{chapter_index}", use_container_width=True):
            start_textbook_unit_assessment(selected_book_id, chapter_index, pretest=True); st.rerun()
    else:
        action_columns[0].caption("学后随机5题，答对至少4题通过。")
    if action_columns[0].button("开始学后评测", key=f"book_quiz_start_{chapter_index}",
                                disabled=(not mapped_chapter["quiz_chapter_ids"] or learning_effect["before"] is None), use_container_width=True):
        start_textbook_unit_assessment(selected_book_id, chapter_index); st.rerun()
    if mapped_chapter["case_ids"]:
        case_id = action_columns[1].selectbox(
            "互动识图", mapped_chapter["case_ids"],
            format_func=lambda item: DIAGRAM_CASES[item]["title"],
            key=f"book_case_{selected_book_id}_{chapter_index}",
        )
        if action_columns[1].button("开始互动识图", key=f"book_case_start_{chapter_index}", use_container_width=True):
            start_diagram_training(case_id); st.rerun()
    else:
        action_columns[1].info("本项目互动训练正在建设，当前先完成知识学习。")
    experiment_ids = mapped_chapter["experiment_ids"]
    if experiment_ids:
        mapped_experiment_id = action_columns[2].selectbox(
            "故障模拟", experiment_ids, format_func=lambda item: catalog[item]["name"],
            key=f"book_experiment_{selected_book_id}_{chapter_index}",
        )
        if action_columns[2].button("开始引导实训", key=f"book_experiment_start_{chapter_index}", use_container_width=True):
            prepare_task(mapped_experiment_id, "引导学习模式"); st.rerun()
    else:
        action_columns[2].info("本单元使用识图和课程综合实训，暂不提供独立故障模拟。")
    st.warning(book["notice"] + " 平台内容为原创讲解与训练，不替代纸质或正版电子教材。")
    if st.button("返回学习首页", use_container_width=True): set_stage(1); st.rerun()

elif stage == 24:
    context = st.session_state.get("textbook_context", {})
    book_id = context.get("book_id")
    chapter_index = context.get("chapter_index")
    topic_id = context.get("topic_id")
    if book_id not in BOOK_EDITION_MAPPINGS:
        st.warning("教材学习位置已失效，请重新选择教材。")
        if st.button("返回教材中心", type="primary", use_container_width=True): set_stage(20); st.rerun()
    else:
        book = BOOK_EDITION_MAPPINGS[book_id]
        if not isinstance(chapter_index, int) or not 0 <= chapter_index < len(book["chapters"]):
            st.warning("教材单元已失效，请重新选择。")
            if st.button("返回教材中心", type="primary", use_container_width=True): set_stage(20); st.rerun()
        else:
            mapped_chapter = book["chapters"][chapter_index]
            topic_ids = list(mapped_chapter["topic_ids"])
            if topic_id not in topic_ids:
                topic_id = topic_ids[0]
                st.session_state.textbook_context["topic_id"] = topic_id
            card = KNOWLEDGE_CARDS[topic_id]
            lesson = lesson_for_topic(topic_id)
            topic_index = topic_ids.index(topic_id)
            st.markdown('<div class="dzt-section-label">Textbook lesson</div>', unsafe_allow_html=True)
            st.caption(f"{book['title']}  ›  {mapped_chapter['title']}  ›  知识点 {topic_index + 1}/{len(topic_ids)}")
            st.subheader(card["title"])
            is_bookmarked = any(
                item["book_id"] == book_id and item["topic_id"] == topic_id
                for item in repository.textbook_bookmarks()
            )
            if st.button("★ 取消收藏" if is_bookmarked else "☆ 收藏知识点", use_container_width=True,
                         key=f"toggle_bookmark_{book_id}_{topic_id}"):
                repository.toggle_textbook_bookmark(book_id, topic_id)
                st.rerun()
            existing_note = next((item for item in repository.study_notes()
                                  if item["book_id"] == book_id and item["topic_id"] == topic_id), None)
            with st.expander("📝 我的学习笔记", expanded=bool(existing_note)):
                with st.form(f"study_note_form_{book_id}_{topic_id}"):
                    note_content = st.text_area(
                        "记录自己的理解、易错点或待复习问题",
                        value=existing_note["content"] if existing_note else "",
                        max_chars=2000, height=140,
                    )
                    st.caption("请勿在笔记中填写姓名、学校、邮箱或真实设备信息。")
                    if st.form_submit_button("保存笔记", type="primary", use_container_width=True):
                        if note_content.strip():
                            repository.save_study_note(StudyNote(
                                book_id, topic_id, note_content,
                                storage_module.beijing_now().isoformat(timespec="seconds"),
                            ))
                            st.success("学习笔记已保存。")
                            st.rerun()
                        else:
                            st.warning("请先写下内容再保存。")
                if existing_note:
                    confirm_note_delete = st.checkbox("确认删除这条笔记", key=f"confirm_note_delete_{book_id}_{topic_id}")
                    if st.button("删除笔记", disabled=not confirm_note_delete,
                                 key=f"delete_note_{book_id}_{topic_id}", use_container_width=True):
                        repository.delete_study_note(book_id, topic_id)
                        st.rerun()
            if lesson:
                st.caption(f"预计学习 {lesson['minutes']} 分钟")
                st.info(lesson["lead"])
                visual = visual_for_topic(topic_id)
                if visual:
                    st.markdown("### 原理图解")
                    visual_html = "<b>→</b>".join(f"<span>{node}</span>" for node in visual["nodes"])
                    st.write(f"**{visual['title']}**")
                    st.markdown(f"<div class='dzt-flow'>{visual_html}</div>", unsafe_allow_html=True)
                    st.caption(visual["caption"] + " 图中只表达抽象关系，不是接线图。")
                if topic_id == "self_hold":
                    with st.expander("查看自锁状态变化演示"):
                        for state_index, (state_title, state_text) in enumerate(SELF_HOLD_STATES, 1):
                            st.markdown(f"<div class='dzt-step'><b>{state_index}. {state_title}</b><br>{state_text}</div>", unsafe_allow_html=True)
                st.markdown("### 本节要点")
                for point in lesson["points"]:
                    st.write(f"- {point}")
                st.markdown("### 放到控制过程里理解")
                st.write(lesson["example"])
                st.markdown("### 即时检查")
                check_key = f"textbook_check_{book_id}_{chapter_index}_{topic_id}"
                answer = st.radio(lesson["question"], lesson["options"], index=None, key=check_key)
                if answer == lesson["answer"]:
                    st.success(f"回答正确。{lesson['explanation']}")
                elif answer:
                    st.warning(f"再想一想。{lesson['explanation']}")
            else:
                st.info(f"**核心原理：** {card['principle']}")
                st.markdown("### 理解这个知识点")
                st.write(card["role"])
                st.success(f"**正确理解：** {card['normal']}")
                st.warning(f"**常见误区：** {card['abnormal']}")
            st.markdown("### 学习小结")
            st.write(card["review"])
            formulas = formulas_for_topic(topic_id)
            if formulas:
                st.markdown("### 抽象逻辑公式")
                for formula in formulas:
                    st.write(f"**{formula['title']}**")
                    st.latex(formula["expression"])
                    for symbol in formula["symbols"]:
                        st.write(f"- {symbol}")
                    st.caption(formula["meaning"])
                st.caption("公式表达控制逻辑关系，不代表真实接线方式。")
            unit_example = example_for_unit(chapter_index)
            with st.expander("原创例题与分步解析"):
                st.write(f"**题目：** {unit_example['scenario']}")
                for step_index, step in enumerate(unit_example["steps"], 1):
                    st.write(f"{step_index}. {step}")
                st.success(f"**结论：** {unit_example['answer']}")
                st.markdown("#### 变式练习")
                variant_key = f"textbook_variant_{book_id}_{chapter_index}_{topic_id}"
                variant_answer = st.radio(unit_example["practice"], unit_example["options"], index=None, key=variant_key)
                if variant_answer == unit_example["practice_answer"]:
                    st.success(f"回答正确。{unit_example['practice_explanation']}")
                elif variant_answer:
                    st.warning(f"请重新分析。{unit_example['practice_explanation']}")
                st.caption("平台原创例题与练习，不是教材原题或官方答案。")
            render_provenance(provenance_for_card(topic_id))
            activity_experiment_id = (mapped_chapter["experiment_ids"] or (DEFAULT_EXPERIMENT_ID,))[0]
            learned = set().union(*(repository.learned_cards(item) for item in catalog))
            if topic_id in learned:
                st.success("这个知识点已标记为学过，可以继续复习。")
            elif st.button("完成本节学习", type="primary", use_container_width=True,
                           disabled=bool(lesson and st.session_state.get(f"textbook_check_{book_id}_{chapter_index}_{topic_id}") != lesson["answer"])):
                repository.save_activity(make_learning_activity(activity_experiment_id, "knowledge_card", topic_id))
                st.success("已记录教材学习进度。")
                st.rerun()
            if lesson and topic_id not in learned:
                st.caption("完成即时检查后即可记录本节进度。")
            lesson_actions = st.columns(2)
            if topic_index + 1 < len(topic_ids):
                if lesson_actions[0].button("下一个知识点", type="primary", use_container_width=True):
                    st.session_state.textbook_context["topic_id"] = topic_ids[topic_index + 1]
                    st.rerun()
            else:
                lesson_actions[0].success("本单元知识点已浏览完成")
            if lesson_actions[1].button("返回本单元", use_container_width=True):
                st.session_state.pop("textbook_context", None)
                set_stage(20); st.rerun()
            st.caption("本页属于教材知识学习，不是故障诊断或真实设备操作指导。")

elif stage == 25:
    st.markdown('<div class="dzt-section-label">Personal review notebook</div>', unsafe_allow_html=True)
    st.subheader("📝 我的复习本")
    st.write("把个人笔记、收藏知识点和历史错题集中到一个复习入口。")
    notes = repository.study_notes()
    bookmarks = repository.textbook_bookmarks()
    wrong_ids = repository.wrong_question_ids()
    review_metrics = st.columns(3)
    review_metrics[0].metric("学习笔记", len(notes))
    review_metrics[1].metric("知识收藏", len(bookmarks))
    review_metrics[2].metric("历史错题", len(wrong_ids))
    note_query = st.text_input("搜索个人笔记", placeholder="输入笔记中的关键词")
    note_terms = [item.casefold() for item in note_query.split() if item.strip()]
    filtered_notes = [
        note for note in notes
        if all(term in (note["content"] + " " + KNOWLEDGE_TOPICS.get(note["topic_id"], {}).get("title", "")).casefold()
               for term in note_terms)
    ]
    st.markdown("### 我的笔记")
    if not filtered_notes:
        st.info("暂无匹配笔记。打开教材知识点即可开始记录。")
    for note_index, note in enumerate(filtered_notes):
        topic = KNOWLEDGE_TOPICS.get(note["topic_id"])
        if not topic:
            continue
        with st.expander(f"{topic['title']} · {note['updated_at'].replace('T', ' ')[:16]}"):
            st.write(note["content"])
            target = next((item for item in TEXTBOOK_SEARCH_INDEX
                           if item.get("book_id") == note["book_id"] and item.get("topic_id") == note["topic_id"]), None)
            if target and st.button("打开知识点并编辑", key=f"note_open_{note_index}", use_container_width=True):
                open_search_result(target); st.rerun()
    st.markdown("### 收藏知识点")
    if not bookmarks:
        st.caption("暂无收藏。")
    for bookmark_index, bookmark in enumerate(bookmarks):
        topic = KNOWLEDGE_TOPICS.get(bookmark["topic_id"])
        target = next((item for item in TEXTBOOK_SEARCH_INDEX
                       if item.get("book_id") == bookmark["book_id"] and item.get("topic_id") == bookmark["topic_id"]), None)
        if topic and target and st.button(topic["title"], key=f"review_bookmark_{bookmark_index}", use_container_width=True):
            open_search_result(target); st.rerun()
    st.markdown("### 历史错题")
    if wrong_ids:
        for question_id in wrong_ids[:10]:
            question = QUESTION_MAP.get(question_id)
            if question:
                st.write(f"- {question.prompt}")
        if st.button("开始错题复习", type="primary", use_container_width=True):
            target_chapter = next(item for item in ALL_CHAPTERS if repository.wrong_question_ids(item["id"]))
            start_chapter_quiz(target_chapter["id"], True); st.rerun()
    else:
        st.caption("暂无历史错题。")
    st.markdown("### 导出复习本")
    topic_titles = {topic_id: item["title"] for topic_id, item in KNOWLEDGE_TOPICS.items()}
    export_columns = st.columns(2)
    export_columns[0].download_button(
        "下载TXT笔记", review_notebook_text(notes, topic_titles).encode("utf-8"),
        file_name="电诊通_我的学习笔记.txt", mime="text/plain", use_container_width=True,
    )
    export_columns[1].download_button(
        "下载JSON复习本", review_notebook_json(notes, bookmarks, wrong_ids),
        file_name="电诊通_我的复习本.json", mime="application/json", use_container_width=True,
    )
    st.caption("平台不主动收集身份信息；请勿在笔记中填写姓名、学校、邮箱或真实设备信息。云端记录可能随服务重启丢失，建议定期下载。")

elif stage == 21:
    st.markdown('<div class="dzt-section-label">Practice center</div>', unsafe_allow_html=True)
    st.subheader("✍️ 练习中心")
    st.write("按章节练习、课程综合评测或复习历史薄弱点。")
    practice_cards = st.columns(2)
    with practice_cards[0]:
        st.markdown('<div class="dzt-card"><h3>10分钟复习</h3><p>根据错题、识图错误和故障练习自动生成。</p></div>', unsafe_allow_html=True)
        if st.button("打开复习清单", type="primary", use_container_width=True): set_stage(18); st.rerun()
    with practice_cards[1]:
        wrong_count = len(repository.wrong_question_ids())
        st.markdown(f'<div class="dzt-card"><h3>错题复习</h3><p>当前记录到 {wrong_count} 道待巩固错题。</p></div>', unsafe_allow_html=True)
        if st.button("开始错题复习", disabled=wrong_count == 0, use_container_width=True):
            target = next(item for item in ALL_CHAPTERS if repository.wrong_question_ids(item["id"]))
            start_chapter_quiz(target["id"], True); st.rerun()
    unlocked_courses = [course for course in COURSES if course_is_unlocked(repository, course["id"])]
    selected_practice_course = st.selectbox(
        "选择课程", [course["id"] for course in unlocked_courses],
        format_func=lambda item: next(course["title"] for course in unlocked_courses if course["id"] == item),
    )
    practice_chapters = COURSE_CHAPTERS[selected_practice_course]
    selected_practice_chapter = st.selectbox(
        "选择章节", [chapter["id"] for chapter in practice_chapters],
        format_func=lambda item: chapter_by_id(item)["title"],
    )
    if st.button("开始5题章节练习", type="primary", use_container_width=True):
        start_chapter_quiz(selected_practice_chapter); st.rerun()
    eligible = course_exam_eligible(repository, selected_practice_course)
    if st.button("开始10题课程综合评测", disabled=not eligible, use_container_width=True):
        start_course_exam(selected_practice_course); st.rerun()
    if not eligible:
        st.caption("通过该课程全部章节测验后开放综合评测。")

elif stage == 22:
    st.markdown('<div class="dzt-section-label">Virtual laboratory</div>', unsafe_allow_html=True)
    st.subheader("🧰 虚拟实训中心")
    st.write("通过过程演示、互动识图、课程综合实训和故障诊断理解电气控制逻辑。")
    training_columns = st.columns(3)
    training_columns[0].metric("互动识图", f"{len(DIAGRAM_CASES)} 个案例")
    training_columns[1].metric("课程综合实训", f"{len(CAPSTONE_TASKS)} 项")
    training_columns[2].metric("故障模拟", f"{sum(len(KnowledgeBase(item).scenario_ids) for item in catalog)} 类")
    st.markdown("### 学习型实训")
    st.caption("建议先在课程章节中学习知识卡，再完成识图和综合实训。")
    training_course_ids = [course["id"] for course in COURSES if course_is_unlocked(repository, course["id"])]
    training_course_id = st.selectbox(
        "选择课程实训", training_course_ids,
        format_func=lambda item: next(course["title"] for course in COURSES if course["id"] == item),
    )
    training_chapters = COURSE_CHAPTERS[training_course_id]
    available_cases = [case for chapter in training_chapters for case in cases_for_chapter(chapter["id"])]
    if available_cases:
        case_id = st.selectbox("互动识图案例", [case["id"] for case in available_cases], format_func=lambda item: DIAGRAM_CASES[item]["title"])
        if st.button("开始互动识图", type="primary", use_container_width=True): start_diagram_training(case_id); st.rerun()
    capstone = task_for_course(training_course_id)
    if st.button(f"开始综合实训 · {capstone['title']}", disabled=not task_is_unlocked(repository, training_course_id), use_container_width=True):
        start_capstone(training_course_id); st.rerun()
    st.divider()
    st.markdown("### 故障诊断模拟")
    st.caption("诊断功能是虚拟实训的一部分，不是平台的主学习入口。")
    render_experiment_selector()
