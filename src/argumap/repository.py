"""SQLite-backed, transactional repository for versioned argument cases."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from .models import Case, Node, NodeType, Relation, RelationType, Snapshot, utc_now


class CaseNotFoundError(KeyError):
    """Raised when a requested case does not exist."""


class SnapshotNotFoundError(KeyError):
    """Raised when a requested snapshot does not exist."""


class CaseRepository:
    """Local repository whose graph mutations each advance a case once."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @classmethod
    def from_metadata_root(cls, root: str | Path) -> "CaseRepository":
        return cls(Path(root) / "argumap.sqlite3")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS cases (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL CHECK (trim(title) <> ''),
                    created_at TEXT NOT NULL, graph_version INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                    type TEXT NOT NULL, content TEXT NOT NULL CHECK (trim(content) <> ''),
                    created_at TEXT NOT NULL, graph_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                    type TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES nodes(id),
                    target_id TEXT NOT NULL REFERENCES nodes(id), created_at TEXT NOT NULL,
                    graph_version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
                    graph_version INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL,
                    UNIQUE(case_id, graph_version)
                );
                CREATE TABLE IF NOT EXISTS verdicts (
                    id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(id),
                    payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )

    def create_case(self, title: str, *, case_id: str | None = None) -> Case:
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be non-empty")
        result = Case(case_id or str(uuid.uuid4()), title.strip(), utc_now(), 0)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO cases (id, title, created_at, graph_version) VALUES (?, ?, ?, 0)",
                (result.id, result.title, result.created_at),
            )
        return result

    def get_case(self, case_id: str) -> Case:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise CaseNotFoundError(case_id)
        return Case(row["id"], row["title"], row["created_at"], row["graph_version"])

    def add_node(self, case_id: str, node_type: NodeType | str, content: str, *, node_id: str | None = None) -> Node:
        try:
            kind = NodeType(node_type)
        except ValueError as error:
            raise ValueError(f"unsupported node type: {node_type}") from error
        if not isinstance(content, str) or not content.strip():
            raise ValueError("content must be non-empty")
        now, identifier = utc_now(), node_id or str(uuid.uuid4())
        with self._connect() as connection:
            case = self._locked_case(connection, case_id)
            version = case.graph_version + 1
            connection.execute(
                "INSERT INTO nodes VALUES (?, ?, ?, ?, ?, ?)",
                (identifier, case_id, kind.value, content.strip(), now, version),
            )
            connection.execute("UPDATE cases SET graph_version = ? WHERE id = ?", (version, case_id))
        return Node(identifier, case_id, kind, content.strip(), now)

    def add_relation(
        self, case_id: str, relation_type: RelationType | str, source_id: str, target_id: str, *, relation_id: str | None = None
    ) -> Relation:
        try:
            kind = RelationType(relation_type)
        except ValueError as error:
            raise ValueError(f"unsupported relation type: {relation_type}") from error
        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required")
        now, identifier = utc_now(), relation_id or str(uuid.uuid4())
        with self._connect() as connection:
            case = self._locked_case(connection, case_id)
            endpoints = connection.execute(
                "SELECT id, case_id FROM nodes WHERE id IN (?, ?)", (source_id, target_id)
            ).fetchall()
            expected_endpoints = {source_id, target_id}
            if {row["id"] for row in endpoints} != expected_endpoints or any(row["case_id"] != case_id for row in endpoints):
                raise ValueError("relation endpoints must exist in the specified case")
            version = case.graph_version + 1
            connection.execute(
                "INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?, ?)",
                (identifier, case_id, kind.value, source_id, target_id, now, version),
            )
            connection.execute("UPDATE cases SET graph_version = ? WHERE id = ?", (version, case_id))
        return Relation(identifier, case_id, kind, source_id, target_id, now)

    def list_graph(self, case_id: str, graph_version: int | None = None) -> tuple[tuple[Node, ...], tuple[Relation, ...]]:
        case = self.get_case(case_id)
        version = case.graph_version if graph_version is None else graph_version
        if version < 0 or version > case.graph_version:
            raise ValueError("requested graph version does not exist")
        with self._connect() as connection:
            nodes = tuple(
                Node(row["id"], row["case_id"], NodeType(row["type"]), row["content"], row["created_at"])
                for row in connection.execute("SELECT * FROM nodes WHERE case_id = ? AND graph_version <= ? ORDER BY id", (case_id, version))
            )
            relations = tuple(
                Relation(row["id"], row["case_id"], RelationType(row["type"]), row["source_id"], row["target_id"], row["created_at"])
                for row in connection.execute("SELECT * FROM relations WHERE case_id = ? AND graph_version <= ? ORDER BY id", (case_id, version))
            )
        return nodes, relations

    def create_snapshot(self, case_id: str, graph_version: int | None = None) -> Snapshot:
        case = self.get_case(case_id)
        version = case.graph_version if graph_version is None else graph_version
        nodes, relations = self.list_graph(case_id, version)
        payload = {
            "case": {"id": case.id, "title": case.title, "created_at": case.created_at, "graph_version": version},
            "nodes": [{"id": n.id, "case_id": n.case_id, "type": n.type.value, "content": n.content, "created_at": n.created_at} for n in nodes],
            "relations": [{"id": r.id, "case_id": r.case_id, "type": r.type.value, "source_id": r.source_id, "target_id": r.target_id, "created_at": r.created_at} for r in relations],
        }
        with self._connect() as connection:
            existing = connection.execute("SELECT * FROM snapshots WHERE case_id = ? AND graph_version = ?", (case_id, version)).fetchone()
            if existing:
                return self._snapshot_from_row(existing)
            snapshot = Snapshot(str(uuid.uuid4()), case_id, version, payload, utc_now())
            connection.execute("INSERT INTO snapshots VALUES (?, ?, ?, ?, ?)", (snapshot.id, case_id, version, json.dumps(payload, sort_keys=True, separators=(",", ":")), snapshot.created_at))
        return snapshot

    def get_snapshot(self, snapshot_id: str) -> Snapshot:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if row is None:
            raise SnapshotNotFoundError(snapshot_id)
        return self._snapshot_from_row(row)

    @staticmethod
    def _snapshot_from_row(row: sqlite3.Row) -> Snapshot:
        return Snapshot(row["id"], row["case_id"], row["graph_version"], json.loads(row["payload"]), row["created_at"])

    @staticmethod
    def _locked_case(connection: sqlite3.Connection, case_id: str) -> Case:
        row = connection.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise CaseNotFoundError(case_id)
        return Case(row["id"], row["title"], row["created_at"], row["graph_version"])
