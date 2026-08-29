"""只读规则驱动的教学诊断引擎。"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .storage import PracticeRecord


EXPERIMENTS_DIR = Path(__file__).with_name("experiments")
DEFAULT_EXPERIMENT_ID = "motor_dol_no_start"


class KnowledgeError(ValueError):
    """知识库结构无效。"""


class SessionError(ValueError):
    """诊断会话操作无效。"""


class KnowledgeBase:
    def __init__(self, experiment_id: str = DEFAULT_EXPERIMENT_ID, path: Path | str | None = None):
        knowledge_path = Path(path) if path is not None else self.path_for(experiment_id)
        with knowledge_path.open("r", encoding="utf-8") as file:
            self.data: dict[str, Any] = json.load(file)
        self.nodes = {node["id"]: node for node in self.data["nodes"]}
        self.results = {result["id"]: result for result in self.data["results"]}
        self._validate()

    @staticmethod
    def path_for(experiment_id: str) -> Path:
        for path in EXPERIMENTS_DIR.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("experiment", {}).get("id") == experiment_id:
                return path
        raise KnowledgeError(f"实验不存在：{experiment_id}")

    @classmethod
    def catalog(cls) -> dict[str, dict[str, Any]]:
        catalog: dict[str, dict[str, Any]] = {}
        for path in sorted(EXPERIMENTS_DIR.glob("*.json")):
            with path.open("r", encoding="utf-8") as file:
                experiment = json.load(file)["experiment"]
            catalog[experiment["id"]] = experiment
        return catalog

    @property
    def experiment(self) -> dict[str, Any]:
        return self.data["experiment"]

    @property
    def answers(self) -> tuple[str, ...]:
        return tuple(self.data["answers"])

    @property
    def experiment_id(self) -> str:
        return self.experiment["id"]

    @property
    def symptoms(self) -> dict[str, str]:
        items = self.experiment.get("symptoms") or [
            {"id": "default", "name": self.experiment["symptom"]}
        ]
        return {item["id"]: item["name"] for item in items}

    @property
    def default_symptom_id(self) -> str:
        return self.experiment.get("default_symptom_id", next(iter(self.symptoms)))

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return tuple(result_id for result_id in self.results if not self.is_inconclusive(result_id))

    @staticmethod
    def is_inconclusive(result_id: str) -> bool:
        return result_id == "inconsistent" or result_id.endswith("_inconsistent")

    def _validate(self) -> None:
        required_answers = {"正常", "异常", "不确定"}
        if set(self.answers) != required_answers:
            raise KnowledgeError("答案必须且只能包含：正常、异常、不确定")
        if self.experiment["entry_node"] not in self.nodes:
            raise KnowledgeError("入口节点不存在")
        if not self.nodes or not self.results:
            raise KnowledgeError("实验必须包含检查节点和结果")
        if self.default_symptom_id not in self.symptoms:
            raise KnowledgeError("默认故障现象不存在")
        valid_targets = set(self.nodes) | set(self.results)
        for node in self.nodes.values():
            if set(node.get("scenario_observations", {})) != {"正常", "异常"}:
                raise KnowledgeError(f"节点 {node['id']} 缺少随机练习状态卡")
            if set(node["transitions"]) != required_answers:
                raise KnowledgeError(f"节点 {node['id']} 的转移不完整")
            if node["transitions"]["不确定"] != node["id"]:
                raise KnowledgeError(f"节点 {node['id']} 的不确定答案必须留在当前节点")
            unknown = set(node["transitions"].values()) - valid_targets
            if unknown:
                raise KnowledgeError(f"节点 {node['id']} 指向未知目标：{unknown}")
            invalid_symptoms = set(node.get("applies_to", self.symptoms)) - set(self.symptoms)
            if invalid_symptoms:
                raise KnowledgeError(f"节点 {node['id']} 使用未知故障现象：{invalid_symptoms}")
        for result_id in self.scenario_ids:
            symptom_id = self.results[result_id].get("symptom_id", self.default_symptom_id)
            if symptom_id not in self.symptoms:
                raise KnowledgeError(f"结果 {result_id} 使用未知故障现象")


@dataclass
class DiagnosticSession:
    knowledge: KnowledgeBase
    safety_confirmed: bool = False
    current_node_id: str | None = None
    result_id: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)
    eliminated: list[str] = field(default_factory=list)
    scenario_id: str | None = None
    practice_id: str | None = None
    symptom_id: str | None = None

    def start(
        self,
        safety_confirmed: bool,
        scenario_id: str | None = None,
        symptom_id: str | None = None,
    ) -> None:
        if not safety_confirmed:
            raise SessionError("必须完成全部安全确认后才能开始")
        valid_scenarios = set(self.knowledge.scenario_ids)
        if scenario_id is not None and scenario_id not in valid_scenarios:
            raise SessionError("随机练习场景不存在")
        if scenario_id is not None:
            symptom_id = self.knowledge.results[scenario_id].get(
                "symptom_id", self.knowledge.default_symptom_id
            )
        symptom_id = symptom_id or self.knowledge.default_symptom_id
        if symptom_id not in self.knowledge.symptoms:
            raise SessionError("故障现象不存在")
        self.safety_confirmed = True
        self.symptom_id = symptom_id
        self.current_node_id = self._next_applicable(self.knowledge.experiment["entry_node"])
        self.result_id = None
        self.history.clear()
        self.eliminated.clear()
        self.scenario_id = scenario_id
        self.practice_id = str(uuid.uuid4()) if scenario_id is not None else None

    @property
    def experiment_id(self) -> str:
        return self.knowledge.experiment_id

    @property
    def symptom(self) -> str:
        return self.knowledge.symptoms[self.symptom_id or self.knowledge.default_symptom_id]

    def _next_applicable(self, target: str) -> str | None:
        visited: set[str] = set()
        while target in self.knowledge.nodes:
            if target in visited:
                raise KnowledgeError("跳过无关分支时检测到循环")
            visited.add(target)
            node = self.knowledge.nodes[target]
            if self.symptom_id in node.get("applies_to", self.knowledge.symptoms):
                return target
            target = node["transitions"]["正常"]
        if target in self.knowledge.results:
            self.result_id = target
            return None
        raise KnowledgeError(f"分支指向未知目标：{target}")

    @property
    def scenario_result(self) -> dict[str, Any] | None:
        if self.scenario_id is None:
            return None
        return self.knowledge.results[self.scenario_id]

    @property
    def scenario_failure_node_id(self) -> str | None:
        if self.scenario_id is None:
            return None
        for node in self.knowledge.nodes.values():
            if node["transitions"]["异常"] == self.scenario_id:
                return node["id"]
        raise KnowledgeError("随机练习场景没有对应检查节点")

    @property
    def expected_answer(self) -> str | None:
        if self.scenario_id is None or self.current_node_id is None:
            return None
        return "异常" if self.current_node_id == self.scenario_failure_node_id else "正常"

    @property
    def scenario_observation(self) -> str | None:
        if self.current_node is None or self.expected_answer is None:
            return None
        return self.current_node["scenario_observations"][self.expected_answer]

    @property
    def score(self) -> tuple[int, int]:
        graded = [item for item in self.history if item.get("is_correct") is not None]
        return sum(bool(item["is_correct"]) for item in graded), len(graded)

    @property
    def wrong_nodes(self) -> tuple[str, ...]:
        return tuple(item["node_id"] for item in self.history if item.get("is_correct") is False)

    @property
    def uncertain_count(self) -> int:
        return sum(item["answer"] == "不确定" for item in self.history)

    def to_practice_record(self, completed_at: str | None = None) -> PracticeRecord:
        if not self.is_complete or self.scenario_id is None or self.practice_id is None:
            raise SessionError("只有完成的随机练习才能保存学习记录")
        if completed_at is None:
            from datetime import datetime

            completed_at = datetime.now().astimezone().isoformat(timespec="seconds")
        correct, total = self.score
        return PracticeRecord(
            practice_id=self.practice_id,
            completed_at=completed_at,
            experiment_id=self.experiment_id,
            scenario_id=self.scenario_id,
            result_id=self.result_id or "inconsistent",
            matched=self.result_id == self.scenario_id,
            correct_judgments=correct,
            total_judgments=total,
            wrong_nodes=self.wrong_nodes,
            uncertain_count=self.uncertain_count,
        )

    @property
    def is_complete(self) -> bool:
        return self.result_id is not None

    @property
    def current_node(self) -> dict[str, Any] | None:
        if self.current_node_id is None:
            return None
        return self.knowledge.nodes[self.current_node_id]

    @property
    def result(self) -> dict[str, Any] | None:
        if self.result_id is None:
            return None
        return self.knowledge.results[self.result_id]

    def answer(self, value: str) -> None:
        if not self.safety_confirmed or self.current_node is None:
            raise SessionError("诊断尚未开始或已经结束")
        if value not in self.knowledge.answers:
            raise SessionError(f"不支持的答案：{value}")

        node = self.current_node
        expected_answer = self.expected_answer
        self.history.append(
            {
                "node_id": node["id"],
                "order": node["order"],
                "object": node["object"],
                "question": node["question"],
                "answer": value,
                "expected": node["expected"],
                "expected_answer": expected_answer,
                "is_correct": None if expected_answer is None or value == "不确定" else value == expected_answer,
            }
        )
        if value == "正常" and node["object"] not in self.eliminated:
            self.eliminated.append(node["object"])

        target = node["transitions"][value]
        if target in self.knowledge.results:
            self.current_node_id = None
            self.result_id = target
        else:
            self.current_node_id = self._next_applicable(target)

    def go_back(self) -> bool:
        if not self.history:
            return False
        retained = deepcopy(self.history[:-1])
        scenario_id = self.scenario_id
        practice_id = self.practice_id
        symptom_id = self.symptom_id
        self.start(True, scenario_id=scenario_id, symptom_id=symptom_id)
        self.practice_id = practice_id
        for entry in retained:
            self.answer(entry["answer"])
        return True

    def reset(self) -> None:
        self.safety_confirmed = False
        self.current_node_id = None
        self.result_id = None
        self.history.clear()
        self.eliminated.clear()
        self.scenario_id = None
        self.practice_id = None
        self.symptom_id = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "safety_confirmed": self.safety_confirmed,
            "current_node_id": self.current_node_id,
            "result_id": self.result_id,
            "history": deepcopy(self.history),
            "eliminated": list(self.eliminated),
            "scenario_id": self.scenario_id,
            "practice_id": self.practice_id,
            "experiment_id": self.experiment_id,
            "symptom_id": self.symptom_id,
        }

    @classmethod
    def from_dict(cls, knowledge: KnowledgeBase, state: dict[str, Any]) -> "DiagnosticSession":
        session = cls(knowledge)
        session.safety_confirmed = bool(state.get("safety_confirmed", False))
        session.current_node_id = state.get("current_node_id")
        session.result_id = state.get("result_id")
        session.history = deepcopy(state.get("history", []))
        session.eliminated = list(state.get("eliminated", []))
        session.scenario_id = state.get("scenario_id")
        session.practice_id = state.get("practice_id")
        saved_experiment_id = state.get("experiment_id", DEFAULT_EXPERIMENT_ID)
        if saved_experiment_id != knowledge.experiment_id:
            raise SessionError("保存的会话属于其他实验")
        session.symptom_id = state.get("symptom_id", knowledge.default_symptom_id)
        if session.current_node_id and session.current_node_id not in knowledge.nodes:
            raise SessionError("保存的会话包含未知节点")
        if session.result_id and session.result_id not in knowledge.results:
            raise SessionError("保存的会话包含未知结果")
        if session.scenario_id and session.scenario_id not in knowledge.results:
            raise SessionError("保存的会话包含未知练习场景")
        if session.symptom_id not in knowledge.symptoms:
            raise SessionError("保存的会话包含未知故障现象")
        return session
