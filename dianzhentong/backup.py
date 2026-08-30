"""匿名学习档案导出、校验与去重恢复。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from .config import APP_VERSION
from .course import ALL_CHAPTERS, COURSES, COURSE_CHAPTERS, chapter_progress
from .engine import KnowledgeBase
from .learning import KNOWLEDGE_CARDS, cards_for_experiment
from .progress import calculate_experiment_progress, learning_streak, beijing_today
from .quiz import QUESTION_MAP, QuizAnswer, make_quiz_record
from .storage import LearningActivity, PracticeRecord, beijing_now


ARCHIVE_FORMAT = "dianzhentong-learning-archive"
SCHEMA_VERSION = 1
MAX_ARCHIVE_BYTES = 5 * 1024 * 1024
DISCLAIMER = "这是教学学习记录，不是职业资格、实训考核或能力认证证书。"


class BackupValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ImportPreview:
    practice_records: int
    learning_activities: int
    quiz_sessions: int

    @property
    def total(self) -> int:
        return self.practice_records + self.learning_activities + self.quiz_sessions


def _iso(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise BackupValidationError(f"{field}格式无效")
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise BackupValidationError(f"{field}不是有效时间") from exc
    return value


def _text(value: Any, field: str, limit: int = 160) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise BackupValidationError(f"{field}格式无效")
    return value


def _integer(value: Any, field: str) -> int:
    if type(value) is not int or value < 0 or value > 1_000_000:
        raise BackupValidationError(f"{field}格式无效")
    return value


def _boolean(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise BackupValidationError(f"{field}格式无效")
    return value


def create_archive(repository: Any) -> dict[str, Any]:
    return {
        "format": ARCHIVE_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "app_version": APP_VERSION,
        "exported_at": beijing_now().isoformat(timespec="seconds"),
        "privacy": "不包含姓名、学校、邮箱、账号或设备信息",
        "data": repository.export_snapshot(),
    }


def archive_json_bytes(repository: Any) -> bytes:
    return json.dumps(create_archive(repository), ensure_ascii=False, indent=2).encode("utf-8")


def parse_archive(payload: bytes | str) -> dict[str, Any]:
    raw = payload.encode("utf-8") if isinstance(payload, str) else payload
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise BackupValidationError("备份文件超过5MB限制")
    try:
        archive = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BackupValidationError("文件不是有效的UTF-8 JSON备份") from exc
    return validate_archive(archive)


def validate_archive(archive: Any) -> dict[str, Any]:
    if not isinstance(archive, dict) or archive.get("format") != ARCHIVE_FORMAT:
        raise BackupValidationError("不是电诊通学习档案")
    if set(archive) != {"format", "schema_version", "app_version", "exported_at", "privacy", "data"}:
        raise BackupValidationError("备份顶层结构异常")
    if archive.get("schema_version") != SCHEMA_VERSION:
        raise BackupValidationError("备份版本不受支持")
    _iso(archive.get("exported_at"), "导出时间")
    data = archive.get("data")
    if not isinstance(data, dict) or set(data) != {"practice_records", "learning_activities", "quiz_sessions"}:
        raise BackupValidationError("备份数据结构不完整")
    if any(not isinstance(data[key], list) or len(data[key]) > 50_000 for key in data):
        raise BackupValidationError("备份记录数量异常")

    catalog = KnowledgeBase.catalog()
    chapters = {item["id"] for item in ALL_CHAPTERS}
    for item in data["practice_records"]:
        required = {"practice_id", "completed_at", "experiment_id", "scenario_id", "result_id", "matched", "correct_judgments", "total_judgments", "wrong_nodes", "uncertain_count"}
        if not isinstance(item, dict) or set(item) != required:
            raise BackupValidationError("练习记录字段不完整")
        experiment_id = _text(item["experiment_id"], "实验ID")
        if experiment_id not in catalog:
            raise BackupValidationError("练习记录包含未知实验")
        knowledge = KnowledgeBase(experiment_id)
        if item["scenario_id"] not in knowledge.scenario_ids or item["result_id"] not in knowledge.results:
            raise BackupValidationError("练习记录包含未知故障")
        _text(item["practice_id"], "练习ID"); _iso(item["completed_at"], "练习时间")
        _boolean(item["matched"], "诊断结果")
        if item["matched"] != (item["result_id"] == item["scenario_id"]):
            raise BackupValidationError("诊断匹配状态不一致")
        correct = _integer(item["correct_judgments"], "正确判断数")
        total = _integer(item["total_judgments"], "有效判断数")
        if correct > total:
            raise BackupValidationError("正确判断数不能超过有效判断数")
        if not isinstance(item["wrong_nodes"], list) or any(node not in knowledge.nodes for node in item["wrong_nodes"]):
            raise BackupValidationError("错题节点无效")
        _integer(item["uncertain_count"], "不确定次数")

    for item in data["learning_activities"]:
        required = {"activity_id", "occurred_at", "local_date", "experiment_id", "activity_type", "reference_id"}
        if not isinstance(item, dict) or set(item) != required:
            raise BackupValidationError("学习活动字段不完整")
        if item["experiment_id"] not in catalog or item["activity_type"] not in {"knowledge_card", "guided_session"}:
            raise BackupValidationError("学习活动类型或实验无效")
        _text(item["activity_id"], "活动ID"); _iso(item["occurred_at"], "活动时间")
        try:
            date.fromisoformat(item["local_date"])
        except (TypeError, ValueError) as exc:
            raise BackupValidationError("学习日期无效") from exc
        reference = _text(item["reference_id"], "关联ID")
        if item["activity_type"] == "knowledge_card" and reference not in KNOWLEDGE_CARDS:
            raise BackupValidationError("知识卡记录无效")

    for item in data["quiz_sessions"]:
        required = {"quiz_id", "chapter_id", "completed_at", "correct_count", "total_count", "passed", "mode", "answers"}
        if not isinstance(item, dict) or set(item) != required:
            raise BackupValidationError("测验记录字段不完整")
        if item["chapter_id"] not in chapters:
            raise BackupValidationError("测验包含未知章节")
        _text(item["quiz_id"], "测验ID"); _iso(item["completed_at"], "测验时间")
        correct = _integer(item["correct_count"], "测验正确数")
        total = _integer(item["total_count"], "测验题数")
        passed = _boolean(item["passed"], "测验通过状态")
        _text(item["mode"], "测验模式")
        answers = item["answers"]
        if not isinstance(answers, list) or len(answers) != total or correct > total:
            raise BackupValidationError("测验答案数量不一致")
        seen: set[str] = set()
        actual_correct = 0
        for answer in answers:
            fields = {"question_id", "selected_answer", "correct_answer", "is_correct", "uncertain"}
            if not isinstance(answer, dict) or set(answer) != fields:
                raise BackupValidationError("测验答案字段不完整")
            question_id = answer["question_id"]
            if question_id in seen or question_id not in QUESTION_MAP or QUESTION_MAP[question_id].chapter_id != item["chapter_id"]:
                raise BackupValidationError("测验题目无效或重复")
            seen.add(question_id)
            _text(answer["selected_answer"], "用户答案"); _text(answer["correct_answer"], "正确答案")
            is_correct = _boolean(answer["is_correct"], "答题结果")
            _boolean(answer["uncertain"], "不确定状态")
            if answer["correct_answer"] != QUESTION_MAP[question_id].answer:
                raise BackupValidationError("测验正确答案被篡改")
            allowed_answers = set(QUESTION_MAP[question_id].options) | {"不确定"}
            if answer["selected_answer"] not in allowed_answers:
                raise BackupValidationError("用户答案不属于题目选项")
            if is_correct != (answer["selected_answer"] == answer["correct_answer"]):
                raise BackupValidationError("单题得分与答案不一致")
            if answer["uncertain"] != (answer["selected_answer"] == "不确定"):
                raise BackupValidationError("不确定状态与答案不一致")
            actual_correct += int(is_correct)
        if actual_correct != correct or passed != bool(total and correct / total >= 0.6):
            raise BackupValidationError("测验得分与答案不一致")
    return archive


def preview_archive(archive: dict[str, Any]) -> ImportPreview:
    data = validate_archive(archive)["data"]
    return ImportPreview(len(data["practice_records"]), len(data["learning_activities"]), len(data["quiz_sessions"]))


def import_archive(repository: Any, archive: dict[str, Any], confirmed: bool = False) -> dict[str, int]:
    archive = validate_archive(archive)
    if not confirmed:
        return {"practice_records": 0, "learning_activities": 0, "quiz_sessions": 0, "duplicates": 0}
    counts = {"practice_records": 0, "learning_activities": 0, "quiz_sessions": 0, "duplicates": 0}
    data = archive["data"]
    for item in data["practice_records"]:
        record = PracticeRecord(**{**item, "wrong_nodes": tuple(item["wrong_nodes"])})
        key = "practice_records" if repository.save(record) else "duplicates"
        counts[key] += 1
    for item in data["learning_activities"]:
        key = "learning_activities" if repository.save_activity(LearningActivity(**item)) else "duplicates"
        counts[key] += 1
    for item in data["quiz_sessions"]:
        answers = tuple(QuizAnswer(**answer) for answer in item["answers"])
        record = make_quiz_record(
            item["chapter_id"], answers, item["mode"], item["quiz_id"],
            datetime.fromisoformat(item["completed_at"]),
        )
        key = "quiz_sessions" if repository.save_quiz(record) else "duplicates"
        counts[key] += 1
    return counts


def build_learning_summary(repository: Any) -> str:
    snapshot = repository.export_snapshot()
    quiz = repository.quiz_summary()
    lines = [
        "电诊通｜匿名学习档案摘要", "=" * 28,
        f"生成时间：{beijing_now():%Y-%m-%d %H:%M}",
        f"总练习次数：{repository.summary()['attempts']}",
        f"测验通过次数：{quiz['passed_count']}",
        f"连续学习天数：{learning_streak(repository.active_dates(), beijing_today())}", "",
        "课程与章节", "-" * 28,
    ]
    for course in COURSES:
        lines.append(course["title"])
        for chapter in COURSE_CHAPTERS[course["id"]]:
            progress = chapter_progress(repository, chapter)
            lines.append(f"- {chapter['title']}：{progress.status}（{progress.completion:.0%}）")
    lines.extend(["", "实验掌握情况", "-" * 28])
    mastered_total = 0
    for experiment_id, experiment in KnowledgeBase.catalog().items():
        knowledge = KnowledgeBase(experiment_id)
        cards = [item["id"] for item in cards_for_experiment(experiment_id)]
        progress = calculate_experiment_progress(repository, experiment_id, knowledge.scenario_ids, cards)
        mastered_total += progress.mastered_faults
        lines.append(
            f"- {experiment['name']}：{progress.status}，掌握度{progress.mastery:.0%}，"
            f"已掌握故障{progress.mastered_faults}/{progress.total_faults}"
        )
    lines.extend([
        "", f"已掌握故障总数：{mastered_total}",
        f"档案记录：练习{len(snapshot['practice_records'])}条、学习活动{len(snapshot['learning_activities'])}条、测验{len(snapshot['quiz_sessions'])}条。",
        "", DISCLAIMER,
        "档案不包含姓名、学校、邮箱、账号或设备信息。",
    ])
    return "\n".join(lines)
