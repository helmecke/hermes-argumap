# Hermes Argumap

A local, deterministic argument-graph core for Hermes.  It stores review cases
in SQLite, versions every accepted graph mutation, and binds analysis, verdicts,
and exports to immutable snapshots.  It never edits curated vault content.

## Vocabulary and deterministic labels

Nodes are `claim`, `assumption`, `evidence`, `weakness`, `counter`,
`precedent`, or `mitigation`. Relations are `supports`, `undermines`,
`assumes`, `depends_on`, `contradicts`, `if_fails`, or `mitigates`.

The conservative, repeatable analysis rule table is:

| Input | Result |
| --- | --- |
| `evidence` or `precedent` with no accepted defeat | `IN` |
| an `IN` source with `supports` or `mitigates` | target is `IN` |
| an `IN` source with `undermines`, `contradicts`, or `if_fails` | target is `OUT` (defeat wins) |
| `assumes`, `depends_on`, or no accepted promoting path | `UNDECIDED` |
| member of a directed cycle | `UNDECIDED` and listed in the cycle report |

## Storage and export format

`CaseRepository.from_metadata_root(path)` creates `argumap.sqlite3` below the
chosen metadata root. It contains `cases`, `nodes`, `relations`, `snapshots`,
and `verdicts` tables with foreign-key constraints. Nodes and relations record
the graph version in which they were accepted. A snapshot stores canonical JSON
for one exact version and remains unchanged after later mutations.

`CaseService(repository, export_root).export(case_id)` writes a JSON document
and Markdown report only below `export_root`. Both include case id, graph
version, snapshot id, the snapshot payload, analysis labels, cycles, unresolved
items, and claim classifications.

## Local development and smoke test

Use Python 3.11 or later. `uv` will create an isolated environment and install
the test dependency:

```console
uv run --extra dev pytest
```

A small reproducible export flow:

```python
from pathlib import Path
from argumap import CaseRepository, CaseService

repository = CaseRepository.from_metadata_root(Path(".local/metadata"))
service = CaseService(repository, Path(".local/exports"))
case = repository.create_case("Bridge safety", case_id="bridge-safety")
repository.add_node(case.id, "claim", "The bridge is safe", node_id="claim")
repository.add_node(case.id, "evidence", "Inspection passed", node_id="inspection")
repository.add_relation(case.id, "supports", "inspection", "claim")
print(service.export(case.id))
```

The acceptance smoke run uses this bridge-safety case and reproduces a
`supported` verdict for `claim` from the exported snapshot identifier.

The `HermesAdapter` exposes the structured operations `create_case`,
`get_case`, `add_node`, `add_relation`, `analyze_case`, `create_verdict`, and
`export_snapshot`. It returns field-level validation errors before persistence
and includes case/version/snapshot provenance in successful results.
