"""End-to-end tests for the local argument graph MVP."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from argumap import CaseNotFoundError, CaseRepository, CaseService, HermesAdapter, Label


@pytest.fixture
def stack(tmp_path):
    repository = CaseRepository.from_metadata_root(tmp_path / "metadata")
    service = CaseService(repository, tmp_path / "exports")
    return repository, service, HermesAdapter(repository, service)


def test_mutations_are_versioned_and_snapshot_is_immutable(stack):
    repository, _, _ = stack
    case = repository.create_case("A claim", case_id="case-1")
    assert case.graph_version == 0
    repository.add_node(case.id, "claim", "The bridge is safe", node_id="claim")
    repository.add_node(case.id, "evidence", "Inspection passed", node_id="evidence")
    repository.add_relation(case.id, "supports", "evidence", "claim", relation_id="support")
    snapshot = repository.create_snapshot(case.id)
    assert snapshot.graph_version == 3
    repository.add_node(case.id, "counter", "New crack report", node_id="counter")
    assert repository.get_case(case.id).graph_version == 4
    assert [node["id"] for node in repository.get_snapshot(snapshot.id).payload["nodes"]] == ["claim", "evidence"]


def test_invalid_mutations_rollback_and_foreign_keys_are_enabled(stack):
    repository, _, _ = stack
    case = repository.create_case("A claim")
    with pytest.raises(ValueError):
        repository.add_node(case.id, "bad", "no")
    with pytest.raises(CaseNotFoundError):
        repository.add_node("missing", "claim", "no")
    assert repository.get_case(case.id).graph_version == 0
    with repository._connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_relations_reject_missing_and_cross_case_endpoints_without_mutation(stack):
    repository, _, _ = stack
    left = repository.create_case("Left", case_id="left")
    right = repository.create_case("Right", case_id="right")
    repository.add_node(left.id, "claim", "left", node_id="left-node")
    repository.add_node(right.id, "claim", "right", node_id="right-node")
    with pytest.raises(ValueError):
        repository.add_relation(left.id, "supports", "left-node", "right-node")
    with pytest.raises(ValueError):
        repository.add_relation(left.id, "supports", "left-node", "missing")
    assert repository.get_case(left.id).graph_version == 1


def test_analysis_handles_support_defeat_and_cycles(stack):
    repository, service, _ = stack
    case = repository.create_case("Graph", case_id="graph")
    for node_id, kind in (("claim", "claim"), ("evidence", "evidence"), ("counter", "counter"), ("mitigation", "mitigation"), ("left", "claim"), ("right", "claim"), ("self", "claim")):
        repository.add_node(case.id, kind, node_id, node_id=node_id)
    repository.add_relation(case.id, "supports", "evidence", "claim")
    repository.add_relation(case.id, "undermines", "evidence", "counter")
    repository.add_relation(case.id, "mitigates", "evidence", "mitigation")
    repository.add_relation(case.id, "supports", "left", "right")
    repository.add_relation(case.id, "supports", "right", "left")
    repository.add_relation(case.id, "supports", "self", "self")
    snapshot, labels, cycles = service.analyze_case(case.id)
    assert labels["claim"] is Label.IN
    assert labels["counter"] is Label.OUT
    assert labels["mitigation"] is Label.IN
    assert labels["left"] is Label.UNDECIDED
    assert cycles == (("left", "right"), ("self",))
    assert service.analyze_case(case.id, snapshot.id)[1:] == (labels, cycles)


def test_analysis_terminates_with_competing_support_and_defeat(stack):
    repository, service, _ = stack
    case = repository.create_case("Competing inputs", case_id="competing")
    repository.add_node(case.id, "claim", "The bridge is safe", node_id="claim")
    repository.add_node(case.id, "evidence", "Inspection passed", node_id="support")
    repository.add_node(case.id, "evidence", "Crack report", node_id="defeat")
    repository.add_relation(case.id, "supports", "support", "claim")
    repository.add_relation(case.id, "undermines", "defeat", "claim")

    _, labels, _ = service.analyze_case(case.id)

    assert labels["claim"] is Label.OUT


def test_verdict_and_export_are_snapshot_bound(stack, tmp_path):
    repository, service, _ = stack
    case = repository.create_case("Export", case_id="export")
    repository.add_node(case.id, "claim", "A", node_id="claim")
    repository.add_node(case.id, "evidence", "B", node_id="evidence")
    repository.add_relation(case.id, "supports", "evidence", "claim")
    result = service.export(case.id)
    json_path = Path(result["json_path"])
    document = json.loads(json_path.read_text())
    assert document["provenance"] == {"case_id": "export", "graph_version": 3, "snapshot_id": result["snapshot_id"]}
    assert document["verdict"]["claims"] == {"claim": "supported"}
    assert json_path.parent == (tmp_path / "exports").resolve()


def test_adapter_validates_inputs_and_returns_provenance(stack):
    _, _, adapter = stack
    assert adapter.invoke("nope", {})["ok"] is False
    created = adapter.invoke("create_case", {"title": "Adapter", "case_id": "adapter"})
    assert created == {"ok": True, "case_id": "adapter", "graph_version": 0}
    invalid = adapter.invoke("add_node", {"case_id": "adapter", "type": "unknown", "content": "x"})
    assert invalid["error"]["field"] == "input"
    node = adapter.invoke("add_node", {"case_id": "adapter", "type": "evidence", "content": "x", "node_id": "e"})
    assert node["graph_version"] == 1
    analysis = adapter.invoke("analyze_case", {"case_id": "adapter"})
    assert analysis["snapshot_id"] and analysis["graph_version"] == 1
