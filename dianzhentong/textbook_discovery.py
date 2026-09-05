"""教材书架、搜索与学习入口索引。"""
from __future__ import annotations

from typing import Any, Iterable

from .content_loader import load_textbook_projects
from .learning import KNOWLEDGE_CARDS


def build_textbook_index(book_ids: Iterable[str]) -> tuple[dict[str, Any], ...]:
    """把教材、单元、知识点、公式和原创例题整理成可搜索条目。"""
    entries: list[dict[str, Any]] = []
    for book_id in book_ids:
        projects = load_textbook_projects(book_id)
        book = projects[0]["book"]
        entries.append({
            "kind": "教材", "book_id": book_id, "chapter_index": 0, "topic_id": None,
            "title": book["title"], "subtitle": f"{book['author']} · {book['publisher']}",
            "search_text": " ".join(str(book.get(key, "")) for key in ("title", "author", "publisher", "isbn")),
        })
        chapter_index = 0
        for content in projects:
            for unit in content["project"]["units"]:
                entries.append({
                    "kind": "单元", "book_id": book_id, "chapter_index": chapter_index, "topic_id": None,
                    "title": unit["title"], "subtitle": unit["goal"],
                    "search_text": f"{book['title']} {unit['source_title']} {unit['title']} {unit['goal']}",
                })
                for topic in unit["topics"]:
                    lesson = topic["lesson"]
                    title = topic.get("title") or KNOWLEDGE_CARDS.get(topic["id"], {}).get("title", topic["id"])
                    search_parts = [title, book["title"], unit["title"], topic["id"], lesson["lead"], lesson["example"]]
                    search_parts.extend(lesson["points"])
                    search_parts.extend(
                        f"{formula['title']} {formula['meaning']} {' '.join(formula['symbols'])}"
                        for formula in topic.get("formulas", [])
                    )
                    entries.append({
                        "kind": "知识点", "book_id": book_id, "chapter_index": chapter_index,
                        "topic_id": topic["id"], "title": title,
                        "subtitle": lesson["lead"], "search_text": " ".join(search_parts),
                    })
                example = unit["worked_example"]
                entries.append({
                    "kind": "原创例题", "book_id": book_id, "chapter_index": chapter_index,
                    "topic_id": unit["topic_ids"][0], "title": example["title"],
                    "subtitle": example["scenario"],
                    "search_text": " ".join([example["title"], example["scenario"], example["answer"], *example["steps"]]),
                })
                chapter_index += 1
    return tuple(entries)


def search_textbooks(entries: Iterable[dict[str, Any]], query: str, limit: int = 12) -> tuple[dict[str, Any], ...]:
    """支持空格分词的中文包含搜索，并优先标题命中。"""
    terms = tuple(part.casefold() for part in query.split() if part.strip())
    if not terms:
        return tuple()
    matches = []
    for entry in entries:
        haystack = entry["search_text"].casefold()
        if all(term in haystack for term in terms):
            title = entry["title"].casefold()
            score = sum(3 if term in title else 1 for term in terms)
            matches.append((score, entry))
    matches.sort(key=lambda item: (-item[0], item[1]["kind"], item[1]["title"]))
    return tuple(item[1] for item in matches[:max(1, limit)])
