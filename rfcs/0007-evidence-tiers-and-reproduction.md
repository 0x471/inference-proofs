# RFC-0007: Evidence tiers

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0004, RFC-0012

## Summary

Every published quantity includes a `tier` field indicating the level of verification behind the number. Every quantity recorded by the harness uses the `reported` tier, meaning a single runner produced it and no second party has verified it yet. Peer review, reproduction records, reproduction tolerances, and effective-tier computation at release freeze are left undefined for now.

## Motivation

Published proving numbers are almost always self-reported by their authors, often from scripts and run records that readers cannot inspect ([PRD §11](../docs/PRD.md#11-risks)). FlashProve's performance page notes that its timed runs came from measurement scripts outside the repository and states that "a reader cannot check the figures on this page against" the run records. SASH publishes its run manifests, but its headline manifest shows that the prover source tree was dirty during the run. Readers need a clear indication that a figure comes from a single runner until another party reruns and confirms it.

## Goals

- Attach a tier label to every quantity.
- Preserve the tier given by the original source when importing upstream figures.

## Non-Goals

- Defining peer review or reproduction workflows.
- Auditing a system's security claims; evidence tiers apply to numerical measurements, not claims.
- Ranking runners or hardware providers.

## Proposed Design

### Tiers

| Tier | Meaning |
|---|---|
| `reported` | Produced by a single runner and not yet verified by another party; the runner may be declared in the manifest |
| `peer-reviewed` | Reserved for future use |
| `reproduced` | Reserved for future use |

Both `run.json` and `index.json` record `reported` for every quantity produced by the harness (LBL-3, RFC-0013). The schema retains the other two enum values so a later release can adopt them without a schema change. In prose, describe a `reported` quantity as "reported", never simply as "measured" without its accompanying labels.

## Alternatives Considered

None.

## Drawbacks

No published number has been verified by a second party.

## Migration / Rollout

Existing stored records already carry `reported`, so no relabelling is required.

## Testing Strategy

- LBL-3 (RFC-0013): verify that a `run.json` quantity with any tier other than `reported` fails gate G5.

## Decisions

None.

## References

- [docs/PRD.md](../docs/PRD.md), sections 7 and 11.
- FlashProve at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c` (performance page); SASH results at `11decec3c0b62c707618aab5deb82750b355d202` (headline manifest, dirty tree).
- [RFC-0004](0004-metrics-timing-grades.md), [RFC-0012](0012-schemas-and-serialization.md).
