"""个人复习本的匿名导出。"""
from __future__ import annotations

import json
from typing import Any, Iterable


def review_notebook_json(notes: Iterable[dict[str, Any]], bookmarks: Iterable[dict[str, Any]],
                         wrong_question_ids: Iterable[str]) -> bytes:
    payload = {
        "format": "dianzhentong-review-notebook",
        "version": 1,
        "privacy": "平台不主动收集身份信息；笔记正文由用户自行填写，请勿写入姓名、学校、邮箱或真实设备信息",
        "notes": list(notes),
        "bookmarks": list(bookmarks),
        "wrong_question_ids": list(wrong_question_ids),
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def review_notebook_text(notes: Iterable[dict[str, Any]], topic_titles: dict[str, str]) -> str:
    rows = list(notes)
    lines = ["电诊通｜我的学习笔记", "=" * 24]
    if not rows:
        lines.append("暂无学习笔记。")
    for index, note in enumerate(rows, 1):
        lines.extend([
            "", f"{index}. {topic_titles.get(note['topic_id'], note['topic_id'])}",
            f"更新时间：{note['updated_at'].replace('T', ' ')[:16]}", note["content"],
        ])
    lines.extend(["", "本文件仅用于个人学习复习，不构成真实设备操作指导。"])
    return "\n".join(lines)
