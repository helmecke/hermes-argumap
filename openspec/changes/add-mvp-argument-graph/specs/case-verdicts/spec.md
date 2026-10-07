# Spec Delta

## Purpose

Produce portable, snapshot-bound conclusions so a verdict can be audited against the exact evidence and argument graph from which it was derived.

## ADDED Requirements

### Requirement: Produce a snapshot-bound verdict
The system SHALL produce a machine-readable verdict for a case snapshot that identifies its case identifier, graph version, snapshot identifier, analysis labels, cycle findings, and unresolved items.

#### Scenario: Create a verdict from current state
- **WHEN** a caller requests a verdict for an existing case without naming a version
- **THEN** the system snapshots the current graph and returns a verdict bound to that snapshot

#### Scenario: Create a verdict from an existing snapshot
- **WHEN** a caller requests a verdict for a valid snapshot identifier
- **THEN** the system returns a verdict that references that same snapshot and graph version

### Requirement: Classify examined claims
The system SHALL classify each examined claim in a verdict as supported, undermined, or unresolved using the analysis result for its bound snapshot.

#### Scenario: Include claim classifications
- **WHEN** a verdict contains one or more claim nodes
- **THEN** every claim appears with exactly one classification and its node identifier

### Requirement: Export a case without mutating curated content
The system SHALL export a snapshot and its verdict in JSON and Markdown formats and SHALL not alter external notes or source files during export.

#### Scenario: Export both portable formats
- **WHEN** a caller requests an export for a valid snapshot
- **THEN** the system creates JSON and Markdown representations that name the same case and snapshot identifiers

#### Scenario: Export never updates external files
- **WHEN** a caller requests an export
- **THEN** the system writes only to its configured export location and reports the created artifact paths
