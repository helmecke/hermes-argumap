# Design

## Context

The repository is new. The MVP defined in `proposal.md` requires a durable local argument-review core that Hermes skills can use consistently. The prior Adversaria implementation supplies a useful domain model, but its Claude Code packaging, Bun tooling, hooks, and temporary JSONL persistence are not portable requirements.

The implementation must preserve case history, make verdicts reproducible, and avoid writing to curated Obsidian content. See the change specs for behavioral contracts.

## Goals / Non-Goals

**Goals:**

- Deliver a small Python package with a deterministic graph engine and SQLite-backed case repository.
- Make all durable writes transactional and versioned at the case level.
- Produce immutable JSON snapshots before verdict creation and export.
- Keep the integration boundary thin so a native Hermes tool adapter can be added without embedding Hermes internals in the domain layer.
- Make the graph semantics testable without an LLM, network access, or an Obsidian installation.

**Non-Goals:**

- No multi-agent or long-lived bot orchestration in the MVP.
- No graphical graph editor, Obsidian Canvas output, or automatic edits to `Notizen/` or `Quellen/`.
- No user authentication, shared-network database, or multi-host coordination.
- No attempt to import existing Adversaria runtime artifacts directly.

## Decisions

### Use a layered Python package

The package will separate domain types and labeling logic from SQLite persistence, application services, exporters, and a Hermes adapter. This lets deterministic unit tests exercise the core without a configured Hermes runtime.

Alternative: implement everything inside a Hermes plugin entry point. Rejected because it couples the graph semantics and test suite to host APIs and makes standalone verification harder.

### Use SQLite with explicit transactions and case-level graph versions

A SQLite database will contain cases, nodes, relations, snapshots, and verdict records. Every successful node or relation mutation will occur in one transaction and increment a case graph version once. Snapshot payloads will be stored as canonical JSON alongside their source version.

Alternative: one JSON or JSONL file per case. Rejected because concurrent or interrupted writes are harder to make atomic, referential integrity is weaker, and snapshot queries become less reliable.

### Preserve the seven-node and seven-relation vocabulary

The initial vocabulary will use the domain terms established in the proposal: `claim`, `assumption`, `evidence`, `weakness`, `counter`, `precedent`, `mitigation`; and `supports`, `undermines`, `assumes`, `depends_on`, `contradicts`, `if_fails`, `mitigates`. Unknown values will fail validation at the public boundary.

Alternative: arbitrary user-defined labels. Deferred because fixed types enable deterministic MVP semantics, validation, and exports; extensions can be versioned later.

### Compute analysis from a snapshot, not mutable current rows

Analysis, verdicting, and export will first resolve an immutable snapshot. The returned results will therefore name `case_id`, `graph_version`, and `snapshot_id`; they never silently refer to “latest” after returning.

Alternative: analyze current storage rows directly. Rejected because a concurrent follow-up mutation would make a saved verdict impossible to reproduce.

### Use grounded fixed-point labels with explicit unresolved results

The engine will calculate labels until stable. A node is `IN` only when it has adequate support and no accepted defeating relation; it is `OUT` when accepted defeating material applies; cycles and insufficient support remain `UNDECIDED`. The exact rule table and test fixtures will be documented with the package so changes require an explicit spec update.

Alternative: let the LLM decide node labels. Rejected because outcomes would be non-repeatable and unverifiable. An LLM may propose graph content through skills but cannot replace the deterministic engine.

### Implement a narrow native Hermes adapter after the core

The adapter will expose structured operations named in `hermes-tool-interface`, validate inputs, invoke application services, and return structured responses. It will not itself own the database schema or analysis rules.

Alternative: run the package through an external MCP server. Deferred because a native adapter has less operational overhead for a local-only MVP; an MCP interface can wrap the same application layer later.

### Keep external content read-only in this change

The configured database and export directory will be the only mutable paths. Future vault integration will import selected evidence and write proposed Markdown separately, behind a user-confirmed operation.

Alternative: write verdict summaries directly into claims during export. Rejected because it violates the reviewed-content boundary and creates unreviewed edits.

## Risks / Trade-offs

- [Fixed-point semantics can be disputed at edge cases] → Encode the rule table in focused tests and expose `UNDECIDED` rather than fabricating certainty.
- [SQLite is local to one machine] → Treat case storage as local-first for MVP; portable snapshot exports permit later migration.
- [Concurrent writers can contend] → Use short transactions, foreign keys, and optimistic version checks where a mutation depends on a stated version.
- [Hermes plugin API details may evolve] → Isolate all host-specific code in the adapter and keep domain services host-agnostic.
- [Graph content created by an LLM can be poor] → Preserve provenance and require deterministic validation; later skills will guide review but cannot alter snapshots.

## Migration Plan

1. Initialize the Python package, test suite, and local developer configuration.
2. Implement and test domain types, graph validation, and deterministic labels.
3. Add SQLite schema, migration bootstrap, transactional repository, and snapshot serialization.
4. Add verdict and exporter services with snapshot-bound tests.
5. Add the Hermes adapter and an end-to-end local smoke test.
6. Release as an initial local-only version with a documented database location and export format.

Rollback is deletion of the plugin package and its configured metadata directory. The system will not modify curated vault files, so rollback does not require content restoration.

## Open Questions

- The exact native Hermes plugin registration API will be confirmed when implementing the adapter; this does not affect the domain contract or storage model.
- The default metadata root will be configurable. For the intended vault deployment, the recommended value is `_meta/hermes/argumap/` within the selected vault.
