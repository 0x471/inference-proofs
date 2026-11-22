# RFC-NNNN: Title

- Authors: handle
- Created: YYYY-MM-DD
- Requires: RFC numbers this one depends on

Write "None." in any section that does not apply. Normative text uses MUST, SHOULD, and MAY as defined in RFC 2119.

## Summary

Summarize in one paragraph what this RFC decides and why it matters.

## Motivation

Explain the problem with concrete evidence and scenarios, such as a specific run, a system's documentation at a pinned commit, a user requirement, a passage in `docs/PRD.md`, or a section of `docs/spec/`.

## Goals

- List concrete, testable goals as bullet points.

## Non-Goals

- State clearly what this RFC does not attempt to address.

## Proposed Design

Present the full design using `###` subsections covering:

- Public interfaces: CLI commands and flags, JSON Schemas in `schema/` (referenced rather than copied), Python signatures, and on-disk formats.
- Internal architecture: module and class responsibilities.
- Data flow and lifecycle.
- Concurrency, determinism, and error propagation.
- Failure modes and how the system responds to each one.

Mark any assumption or design point that may turn out to be wrong with `RISK:`, followed by the plan for resolving it.

## Alternatives Considered

For each alternative, explain what it is, why it was considered, and why it was rejected.

## Drawbacks

Describe the trade-offs and limitations of this design.

## Migration / Rollout

Describe how this change affects existing adapters, claim cards, schemas, and past results, including how they will be migrated or relabelled and any schema version changes (RFC-0012).

## Testing Strategy

List named test cases that verify the design across unit, property, schema example, fixture, integration, and GPU-host tests. Describe specific cases rather than broad categories.

## Decisions

Prefix each entry with `Qn. ` and state the rule clearly. Preserve the number once code or documentation references it.

## References

List specifications, prior art, papers, related RFCs, and upstream documentation at pinned commits.
