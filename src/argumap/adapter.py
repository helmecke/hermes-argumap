"""Thin, host-agnostic structured interface intended for Hermes tools."""

from __future__ import annotations

from typing import Any

from .models import NodeType, RelationType
from .repository import CaseRepository
from .service import CaseService


class HermesAdapter:
    """Validate operation payloads before delegating to the application layer."""

    def __init__(self, repository: CaseRepository, service: CaseService) -> None:
        self.repository = repository
        self.service = service

    def invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation not in {"create_case", "get_case", "add_node", "add_relation", "analyze_case", "create_verdict", "export_snapshot"}:
            return self._error("operation", "unsupported operation")
        if not isinstance(payload, dict):
            return self._error("payload", "must be an object")
        try:
            return self._invoke(operation, payload)
        except (KeyError, ValueError) as error:
            return self._error("input", str(error))

    def _invoke(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "create_case":
            title = self._text(payload, "title")
            case = self.repository.create_case(title, case_id=payload.get("case_id"))
            return {"ok": True, "case_id": case.id, "graph_version": case.graph_version}
        case_id = self._text(payload, "case_id")
        if operation == "get_case":
            case = self.repository.get_case(case_id)
            nodes, relations = self.repository.list_graph(case_id)
            return {"ok": True, "case": {"id": case.id, "title": case.title, "created_at": case.created_at, "graph_version": case.graph_version}, "nodes": [node.id for node in nodes], "relations": [relation.id for relation in relations]}
        if operation == "add_node":
            kind = self._enum(payload, "type", NodeType)
            node = self.repository.add_node(case_id, kind, self._text(payload, "content"), node_id=payload.get("node_id"))
            return {"ok": True, "case_id": case_id, "graph_version": self.repository.get_case(case_id).graph_version, "node_id": node.id}
        if operation == "add_relation":
            kind = self._enum(payload, "type", RelationType)
            relation = self.repository.add_relation(case_id, kind, self._text(payload, "source_id"), self._text(payload, "target_id"), relation_id=payload.get("relation_id"))
            return {"ok": True, "case_id": case_id, "graph_version": self.repository.get_case(case_id).graph_version, "relation_id": relation.id}
        if operation == "analyze_case":
            snapshot, labels, cycles = self.service.analyze_case(case_id, payload.get("snapshot_id"))
            return {"ok": True, "case_id": case_id, "graph_version": snapshot.graph_version, "snapshot_id": snapshot.id, "labels": {key: value.value for key, value in labels.items()}, "cycles": [list(cycle) for cycle in cycles]}
        if operation == "create_verdict":
            verdict = self.service.create_verdict(case_id, payload.get("snapshot_id"))
            return {"ok": True, **self.service.verdict_to_dict(verdict)}
        return {"ok": True, **self.service.export(case_id, payload.get("snapshot_id"))}

    @staticmethod
    def _text(payload: dict[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field}: must be a non-empty string")
        return value.strip()

    @staticmethod
    def _enum(payload: dict[str, Any], field: str, enum_type: type[NodeType] | type[RelationType]) -> NodeType | RelationType:
        value = payload.get(field)
        try:
            return enum_type(value)
        except (TypeError, ValueError) as error:
            choices = ", ".join(item.value for item in enum_type)
            raise ValueError(f"{field}: must be one of {choices}") from error

    @staticmethod
    def _error(field: str, message: str) -> dict[str, Any]:
        return {"ok": False, "error": {"field": field, "message": message}}
