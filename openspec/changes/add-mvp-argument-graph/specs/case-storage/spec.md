# Spec Delta

## Purpose

Provide durable, versioned local case records so argument reviews can be resumed, audited, and reproduced without modifying curated vault content.

## ADDED Requirements

### Requirement: Create and retrieve a case
The system SHALL create a case with a stable identifier, title, creation timestamp, and initial graph version, and SHALL retrieve the complete current case by identifier.

#### Scenario: Create a new case
- **WHEN** a caller creates a case with a non-empty title
- **THEN** the system returns a new stable case identifier and graph version zero

#### Scenario: Retrieve an unknown case
- **WHEN** a caller requests a case identifier that does not exist
- **THEN** the system returns a not-found error without creating a record

### Requirement: Version graph mutations
The system SHALL record every accepted graph mutation against its case and advance the case graph version exactly once per committed mutation.

#### Scenario: Add graph content to an existing case
- **WHEN** a valid node or relation is added to a case
- **THEN** the mutation is durable and the returned graph version is one greater than the prior version

#### Scenario: Reject mutation of an unknown case
- **WHEN** a caller adds graph content using an unknown case identifier
- **THEN** the system returns a not-found error and persists no mutation

### Requirement: Create immutable snapshots
The system SHALL create an immutable snapshot of a requested case graph version and SHALL preserve it after later graph mutations.

#### Scenario: Snapshot survives a later mutation
- **WHEN** a snapshot is created and the case is subsequently changed
- **THEN** retrieving that snapshot returns the graph state at the snapshotted version
