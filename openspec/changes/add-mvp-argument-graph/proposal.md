# Proposal

## Why

Hermes users need a repeatable way to scrutinize a claim without losing the supporting evidence, objections, and reasoning that led to a conclusion. Today, adversarial review can be performed conversationally, but it has no durable, machine-readable case record or snapshot-bound verdict.

This MVP establishes a local argument-graph core that later skills and Obsidian integration can use without allowing automated edits to curated vault content.

## What Changes

- Add durable, versioned local case storage backed by SQLite.
- Add a typed argument graph for claims, assumptions, evidence, weaknesses, counters, precedents, and mitigations.
- Add deterministic graph analysis that labels arguments `IN`, `OUT`, or `UNDECIDED`, identifies cycles, and derives a machine-readable verdict.
- Add immutable case snapshots and JSON/Markdown exports that bind every verdict to an exact graph version.
- Provide a Hermes-facing tool surface for creating cases, adding graph content, analyzing cases, producing verdicts, and exporting results.
- Explicitly exclude automated edits to Obsidian notes and source material from the MVP.

## Capabilities

### New Capabilities

- `case-storage`: Creates, versions, and snapshots durable local argument-review cases.
- `argument-graph`: Captures typed arguments and relations, then deterministically evaluates their status and cycles.
- `case-verdicts`: Produces snapshot-bound, machine-readable verdicts and portable case exports.
- `hermes-tool-interface`: Exposes safe, validated operations for Hermes skills and agents to operate on a case.

### Modified Capabilities

- None.

## Impact

- New Python package and automated tests.
- New SQLite database schema stored under a configured local metadata directory.
- New Hermes plugin/tool integration and structured operation schema.
- Future Obsidian integration will consume exports only; the MVP will not write to `Notizen/` or `Quellen/`.
