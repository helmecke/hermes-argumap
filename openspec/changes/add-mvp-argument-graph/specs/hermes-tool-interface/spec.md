# Spec Delta

## Purpose

Expose validated, predictable case operations to Hermes agents while making state-changing actions explicit and safe to compose in skills.

## ADDED Requirements

### Requirement: Expose case lifecycle operations
The Hermes-facing interface SHALL expose operations to create a case, retrieve a case, add a node, add a relation, analyze a case, create a verdict, and export a snapshot.

#### Scenario: Invoke a supported operation
- **WHEN** a Hermes agent invokes a supported operation with valid inputs
- **THEN** the interface returns the operation result in structured form

#### Scenario: Request an unknown operation
- **WHEN** a Hermes agent requests an operation outside the supported set
- **THEN** the interface returns a structured validation error without changing state

### Requirement: Validate mutation inputs before persistence
The interface SHALL validate required identifiers, supported argument types, and non-empty textual fields before passing a mutation to case storage.

#### Scenario: Reject invalid mutation input
- **WHEN** an add-node or add-relation request omits or invalidates a required field
- **THEN** the interface returns field-level validation details and persists no mutation

### Requirement: Return version and provenance metadata
Every successful state-changing operation SHALL return the affected case identifier and resulting graph version; every analysis, verdict, or export SHALL also return its snapshot identifier when one exists.

#### Scenario: Report mutation provenance
- **WHEN** an agent successfully adds a node or relation
- **THEN** the result includes the case identifier and new graph version

#### Scenario: Report verdict provenance
- **WHEN** an agent successfully creates a verdict
- **THEN** the result includes the case identifier, graph version, and snapshot identifier
