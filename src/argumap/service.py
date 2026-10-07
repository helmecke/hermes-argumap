"""Application services for analysis, verdicts, and portable exports."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .graph import analyze
from .models import Label, Node, NodeType, Relation, RelationType, Snapshot, Verdict, utc_now
from .repository import CaseRepository


class CaseService:
    """Coordinates immutable snapshots with graph analysis and exports."""

    def __init__(self, repository: CaseRepository, export_root: str | Path) -> None:
        self.repository = repository
        self.export_root = Path(export_root).resolve()
        self.export_root.mkdir(parents=True, exist_ok=True)

    def analyze_case(self, case_id: str, snapshot_id: str | None = None) -> tuple[Snapshot, dict[str, Label], tuple[tuple[str, ...], ...]]:
        snapshot = self.repository.get_snapshot(snapshot_id) if snapshot_id else self.repository.create_snapshot(case_id)
        if snapshot.case_id != case_id:
            raise ValueError("snapshot does not belong to the requested case")
        nodes, relations = self._graph_from_snapshot(snapshot)
        result = analyze(nodes, relations)
        return snapshot, result.labels, result.cycles

    def create_verdict(self, case_id: str, snapshot_id: str | None = None) -> Verdict:
        snapshot, labels, cycles = self.analyze_case(case_id, snapshot_id)
        claims = {
            node["id"]: self._classification(labels[node["id"]])
            for node in snapshot.payload["nodes"]
            if node["type"] == NodeType.CLAIM.value
        }
        return Verdict(
            id=str(uuid.uuid4()), case_id=case_id, graph_version=snapshot.graph_version,
            snapshot_id=snapshot.id, labels=labels, cycles=cycles,
            unresolved=tuple(node_id for node_id, label in labels.items() if label is Label.UNDECIDED),
            claims=claims, created_at=utc_now(),
        )

    def export(self, case_id: str, snapshot_id: str | None = None) -> dict[str, Any]:
        verdict = self.create_verdict(case_id, snapshot_id)
        snapshot = self.repository.get_snapshot(verdict.snapshot_id)
        stem = self._safe_stem(f"{case_id}-{snapshot.graph_version}-{snapshot.id}")
        json_path = self.export_root / f"{stem}.json"
        markdown_path = self.export_root / f"{stem}.md"
        document = {
            "snapshot": snapshot.payload,
            "provenance": {"case_id": case_id, "graph_version": snapshot.graph_version, "snapshot_id": snapshot.id},
            "verdict": self.verdict_to_dict(verdict),
        }
        json_path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(self._markdown(snapshot, verdict), encoding="utf-8")
        return {"case_id": case_id, "graph_version": snapshot.graph_version, "snapshot_id": snapshot.id, "json_path": str(json_path), "markdown_path": str(markdown_path)}

    @staticmethod
    def verdict_to_dict(verdict: Verdict) -> dict[str, Any]:
        return {"id": verdict.id, "case_id": verdict.case_id, "graph_version": verdict.graph_version, "snapshot_id": verdict.snapshot_id, "labels": {key: value.value for key, value in verdict.labels.items()}, "cycles": [list(cycle) for cycle in verdict.cycles], "unresolved": list(verdict.unresolved), "claims": verdict.claims, "created_at": verdict.created_at}

    @staticmethod
    def _classification(label: Label) -> str:
        return {Label.IN: "supported", Label.OUT: "undermined", Label.UNDECIDED: "unresolved"}[label]

    @staticmethod
    def _graph_from_snapshot(snapshot: Snapshot) -> tuple[tuple[Node, ...], tuple[Relation, ...]]:
        nodes = tuple(Node(row["id"], row["case_id"], NodeType(row["type"]), row["content"], row["created_at"]) for row in snapshot.payload["nodes"])
        relations = tuple(Relation(row["id"], row["case_id"], RelationType(row["type"]), row["source_id"], row["target_id"], row["created_at"]) for row in snapshot.payload["relations"])
        return nodes, relations

    @staticmethod
    def _safe_stem(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-") or "argumap-export"

    def _markdown(self, snapshot: Snapshot, verdict: Verdict) -> str:
        lines = ["# Argument-map verdict", "", f"- Case: `{verdict.case_id}`", f"- Graph version: `{verdict.graph_version}`", f"- Snapshot: `{verdict.snapshot_id}`", "", "## Claim classifications", ""]
        lines.extend(f"- `{node_id}`: **{classification}**" for node_id, classification in verdict.claims.items())
        lines += ["", "## Node labels", ""]
        lines.extend(f"- `{node_id}`: {label.value}" for node_id, label in verdict.labels.items())
        lines += ["", "## Cycles", ""]
        lines.extend(f"- {' → '.join(cycle)}" for cycle in verdict.cycles) if verdict.cycles else lines.append("- None")
        lines += ["", "## Snapshot", "", "```json", json.dumps(snapshot.payload, sort_keys=True, indent=2), "", "```", ""]
        return "\n".join(lines)
