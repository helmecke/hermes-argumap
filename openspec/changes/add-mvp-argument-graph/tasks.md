# Tasks

## 1. Project foundation

- [ ] 1.1 Create the Python package layout, `pyproject.toml`, test configuration, and local development documentation; verify a clean environment can discover the package and test suite.
- [ ] 1.2 Define domain enums and immutable data models for all required node, relation, label, case, snapshot, and verdict records; verify model validation unit tests pass.
- [ ] 1.3 Document the deterministic label rule table and supported graph vocabulary in the package documentation; verify every documented type is covered by validation tests.

## 2. Argument graph engine

- [ ] 2.1 Implement graph construction and validation for typed nodes and same-case typed relations; verify unit tests cover valid inputs, unsupported types, missing nodes, and cross-case links.
- [ ] 2.2 Implement fixed-point `IN`, `OUT`, and `UNDECIDED` analysis; verify fixtures cover support, defeat, mitigation, unresolved evidence, and repeated deterministic analysis.
- [ ] 2.3 Implement directed-cycle detection and analysis reporting; verify unit tests cover acyclic, self-referential, and multi-node cyclic graphs.

## 3. Durable case storage

- [ ] 3.1 Implement SQLite schema initialization and a configurable local metadata root; verify a fresh database passes schema and foreign-key checks.
- [ ] 3.2 Implement transactional case, node, and relation persistence with one graph-version increment per accepted mutation; verify persistence tests cover rollback and unknown-case errors.
- [ ] 3.3 Implement canonical immutable graph snapshots and snapshot retrieval; verify a snapshot remains unchanged after later graph mutations.

## 4. Verdicts and exports

- [ ] 4.1 Implement snapshot-bound verdict generation and claim classifications; verify verdict tests assert case, graph-version, and snapshot provenance.
- [ ] 4.2 Implement JSON and Markdown exports to the configured export directory; verify integration tests parse both outputs and assert no files outside the export root change.
- [ ] 4.3 Document local database, snapshot, and export formats; verify documented example commands reproduce an export in a temporary directory.

## 5. Hermes integration

- [ ] 5.1 Confirm the native Hermes plugin registration API and implement a thin adapter for the required structured operations; verify adapter tests reject unknown operations and malformed mutation input.
- [ ] 5.2 Return case, version, and snapshot provenance in all applicable adapter results; verify end-to-end tests cover create, mutate, analyze, verdict, and export flows.
- [ ] 5.3 Add Hermes skills for steelman, crucible, verdict, and full review that use the adapter without bypassing snapshot creation; verify each skill's documented flow uses supported operations only.

## 6. MVP acceptance

- [ ] 6.1 Run the complete automated test suite, static checks, and a clean-database end-to-end smoke test; verify all commands exit successfully.
- [ ] 6.2 Perform a manual acceptance run on a representative claim and confirm the exported verdict is reproducible from its named snapshot; record the result in project documentation.

## Workflow follow-up

- Review the completed change before archiving it into the main OpenSpec capability specifications.
- Archive the change only after the MVP acceptance tasks and repository review requirements are satisfied.
