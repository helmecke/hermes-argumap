# Spec Delta

## Purpose

Represent structured claims and challenges as a typed graph that can be inspected and evaluated deterministically across repeated analyses.

## ADDED Requirements

### Requirement: Store typed argument nodes
The system SHALL accept nodes of type `claim`, `assumption`, `evidence`, `weakness`, `counter`, `precedent`, or `mitigation`, each with a stable identifier and non-empty content.

#### Scenario: Add a typed node
- **WHEN** a caller supplies a supported node type and non-empty content
- **THEN** the system stores the node in the specified case

#### Scenario: Reject an unsupported node type
- **WHEN** a caller supplies a node type outside the supported set
- **THEN** the system rejects the request without changing the case graph

### Requirement: Store typed graph relations
The system SHALL accept relations of type `supports`, `undermines`, `assumes`, `depends_on`, `contradicts`, `if_fails`, or `mitigates` only when both referenced nodes belong to the same case.

#### Scenario: Add a valid relation
- **WHEN** a caller connects two nodes in the same case with a supported relation type
- **THEN** the system stores the relation and reports the new graph version

#### Scenario: Reject cross-case relation
- **WHEN** a caller connects nodes that belong to different cases
- **THEN** the system rejects the request without changing either case

### Requirement: Evaluate argument status and cycles
The system SHALL deterministically label every graph node `IN`, `OUT`, or `UNDECIDED` and SHALL report every detected directed cycle in the evaluated graph.

#### Scenario: Repeat an unchanged analysis
- **WHEN** analysis is run twice against the same graph version
- **THEN** both results contain identical node labels and cycle findings

#### Scenario: Evaluate a cyclic graph
- **WHEN** analysis encounters one or more directed cycles
- **THEN** the result identifies the involved node identifiers and keeps unresolved nodes `UNDECIDED`
