# RFC-0001: RFC format

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: none

## Summary

This RFC establishes how project decisions are documented, covering the RFC format, numbering rules, the roles referenced across the specification, and the standard repository files.

## Motivation

Methodology choices and core technical decisions need a single canonical location so that both code and documentation can cite them reliably.

## Goals

- Document every methodology decision in an RFC.
- Assign every RFC a permanent, stable number.

## Non-Goals

- Certifying any system ([PRD §5](../docs/PRD.md#5-non-goals)).

## Proposed Design

### Roles

| Role | Definition |
|---|---|
| Relying party | Publishes performance or verification targets under their own name (RFC-0009) |
| Runner | Anyone who executes benchmark jobs and submits run directories, as declared in the run manifest |

### RFC format

1. Start each new RFC by copying [0000-template.md](0000-template.md) and completing the sections that apply.
2. Assign the next available RFC number when the pull request is opened. RFC numbers are never reused.
3. Never edit past results (following the append-only rule in RFC-0009). When methodology changes, relabel or rerun jobs rather than modifying stored records.

### Repository files

| File | Content |
|---|---|
| `CONTRIBUTING.md` | Guidelines for opening issues and pull requests, along with test and CI requirements |
| `SECURITY.md` | The private reporting channel for harness vulnerabilities and for privately reporting accepted negative controls (RFC-0008) |
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1, including the enforcement contact |
| `LICENSE` | Apache-2.0 licence for code |
| `LICENSES/CC-BY-4.0.txt` and a note in `README.md` | CC BY 4.0 licence for specifications, data, results, and reports |

## Alternatives Considered

None.

## Drawbacks

None.

## Migration / Rollout

None.

## Testing Strategy

None.

## Decisions

- Q1. The working name of the project is "Inference Proofs", hosted in the current repository. Schema `$id` hostnames do not resolve over the network and do not affect validation.
- Q3. The private reporting channel referenced in `SECURITY.md` is the hosting platform's private vulnerability reporting feature.

## References

- [docs/PRD.md](../docs/PRD.md).
- Contributor Covenant 2.1, contributor-covenant.org.
- RFC 2119, key words for use in RFCs to indicate requirement levels.
