"""Immutable domain records and vocabulary for argument-review cases."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class NodeType(StrEnum):
    CLAIM = "claim"
    ASSUMPTION = "assumption"
    EVIDENCE = "evidence"
    WEAKNESS = "weakness"
    COUNTER = "counter"
    PRECEDENT = "precedent"
    MITIGATION = "mitigation"


class RelationType(StrEnum):
    SUPPORTS = "supports"
    UNDERMINES = "undermines"
    ASSUMES = "assumes"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    IF_FAILS = "if_fails"
    MITIGATES = "mitigates"


class Label(StrEnum):
    IN = "IN"
    OUT = "OUT"
    UNDECIDED = "UNDECIDED"


@dataclass(frozen=True, slots=True)
class Case:
    id: str
    title: str
    created_at: str
    graph_version: int


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    case_id: str
    type: NodeType
    content: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Relation:
    id: str
    case_id: str
    type: RelationType
    source_id: str
    target_id: str
    created_at: str


@dataclass(frozen=True, slots=True)
class Snapshot:
    id: str
    case_id: str
    graph_version: int
    payload: dict[str, Any]
    created_at: str


@dataclass(frozen=True, slots=True)
class Verdict:
    id: str
    case_id: str
    graph_version: int
    snapshot_id: str
    labels: dict[str, Label]
    cycles: tuple[tuple[str, ...], ...]
    unresolved: tuple[str, ...]
    claims: dict[str, str]
    created_at: str


def utc_now() -> str:
    """Return a sortable, timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def record_to_dict(record: Case | Node | Relation | Snapshot | Verdict) -> dict[str, Any]:
    """Make immutable records JSON-ready without leaking enum instances."""
    return asdict(record)
