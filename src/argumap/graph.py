"""Deterministic graph validation, cycle detection, and label analysis."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from typing import Iterable

from .models import Label, Node, Relation, RelationType


class GraphValidationError(ValueError):
    """Raised when a graph cannot be evaluated safely."""


@dataclass(frozen=True, slots=True)
class Analysis:
    labels: dict[str, Label]
    cycles: tuple[tuple[str, ...], ...]

    @property
    def unresolved(self) -> tuple[str, ...]:
        return tuple(node_id for node_id, label in self.labels.items() if label is Label.UNDECIDED)


# An accepted source promotes its target; an accepted source defeats its target.
_PROMOTING = {RelationType.SUPPORTS, RelationType.MITIGATES}
_DEFEATING = {
    RelationType.UNDERMINES,
    RelationType.CONTRADICTS,
    RelationType.IF_FAILS,
}


def validate_graph(nodes: Iterable[Node], relations: Iterable[Relation]) -> None:
    """Validate identity uniqueness and same-case relation endpoints."""
    node_list = tuple(nodes)
    node_ids = {node.id for node in node_list}
    if len(node_ids) != len(node_list):
        raise GraphValidationError("node identifiers must be unique")
    cases = {node.case_id for node in node_list}
    for relation in relations:
        if relation.source_id not in node_ids or relation.target_id not in node_ids:
            raise GraphValidationError("relation references a missing node")
        if relation.case_id not in cases:
            raise GraphValidationError("relation references an unknown case")
        endpoints = [node for node in node_list if node.id in {relation.source_id, relation.target_id}]
        if any(node.case_id != relation.case_id for node in endpoints):
            raise GraphValidationError("relation endpoints must belong to its case")


def find_cycles(nodes: Iterable[Node], relations: Iterable[Relation]) -> tuple[tuple[str, ...], ...]:
    """Return stable strongly connected components representing directed cycles."""
    ids = sorted(node.id for node in nodes)
    adjacency: dict[str, list[str]] = defaultdict(list)
    for relation in relations:
        adjacency[relation.source_id].append(relation.target_id)
    for targets in adjacency.values():
        targets.sort()

    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    def visit(node_id: str) -> None:
        nonlocal index
        indices[node_id] = lowlinks[node_id] = index
        index += 1
        stack.append(node_id)
        on_stack.add(node_id)
        for target in adjacency[node_id]:
            if target not in indices:
                visit(target)
                lowlinks[node_id] = min(lowlinks[node_id], lowlinks[target])
            elif target in on_stack:
                lowlinks[node_id] = min(lowlinks[node_id], indices[target])
        if lowlinks[node_id] == indices[node_id]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == node_id:
                    break
            component.sort()
            if len(component) > 1 or component[0] in adjacency[component[0]]:
                cycles.append(tuple(component))

    for node_id in ids:
        if node_id not in indices:
            visit(node_id)
    return tuple(sorted(cycles))


def analyze(nodes: Iterable[Node], relations: Iterable[Relation]) -> Analysis:
    """Compute stable labels using the documented conservative rule table.

    Evidence and precedent start accepted.  Accepted `supports`/`mitigates`
    relations accept their target, while accepted `undermines`, `contradicts`,
    and `if_fails` relations defeat their target.  A defeat always wins. Nodes
    in a directed cycle are deliberately left unresolved rather than inferred.
    `assumes` and `depends_on` preserve the conservative default: without an
    accepted promoting path their targets remain unresolved.
    """
    node_list = tuple(nodes)
    relation_list = tuple(relations)
    validate_graph(node_list, relation_list)
    cycles = find_cycles(node_list, relation_list)
    cyclic = {node_id for cycle in cycles for node_id in cycle}
    labels = {node.id: Label.UNDECIDED for node in node_list}
    non_cyclic = {node.id for node in node_list} - cyclic
    incoming: dict[str, list[Relation]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    in_degree = {node_id: 0 for node_id in non_cyclic}
    for relation in relation_list:
        if relation.target_id not in non_cyclic:
            continue
        incoming[relation.target_id].append(relation)
        if relation.source_id in non_cyclic:
            outgoing[relation.source_id].append(relation.target_id)
            in_degree[relation.target_id] += 1

    ready: list[str] = []
    for node_id, degree in in_degree.items():
        if degree == 0:
            heappush(ready, node_id)

    nodes_by_id = {node.id: node for node in node_list}
    while ready:
        node_id = heappop(ready)
        node = nodes_by_id[node_id]
        accepted = [
            relation
            for relation in incoming[node_id]
            if labels[relation.source_id] is Label.IN
        ]
        if any(relation.type in _DEFEATING for relation in accepted):
            labels[node_id] = Label.OUT
        elif node.type.value in {"evidence", "precedent"} or any(
            relation.type in _PROMOTING for relation in accepted
        ):
            labels[node_id] = Label.IN
        for target_id in outgoing[node_id]:
            in_degree[target_id] -= 1
            if in_degree[target_id] == 0:
                heappush(ready, target_id)
    return Analysis(labels=labels, cycles=cycles)
