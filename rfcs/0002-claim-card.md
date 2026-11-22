# RFC-0002: Claim card

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0001, RFC-0012

## Summary

A claim card is a machine-readable record, defined per system configuration, stating what an accepted proof establishes, what assumptions it relies on, which parts of the computation it binds, and what a dishonest prover can still do. Every published benchmark number is accompanied by its claim card, and no number may be published without one. This RFC defines the card's fields and types, the rule that every field must quote the system's own documentation or record `not stated`, the per-field source link requirement, what constitutes a distinct configuration, the review metadata, and the `claim_class` string used to filter closed divisions and targets. The normative schema is `schema/claim/1.schema.json` (RFC-0012).

## Motivation

The first two v0.1 systems prove substantially different statements ([PRD §1](../docs/PRD.md#1-problem)). A FlashProve proof establishes that the next token after a 1,024-token window is the top choice of a committed integer model, with soundness formally proved in Lean for its Lean verifier under an exact-match policy, and weights kept hidden apart from a declared list. A SASH proof consists of a grid of per-segment proofs covering transformer layers and token blocks of Llama-3.1-8B W8A8, accompanied by a per-edge binding table and `--unsound-skip-*` flags that disable individual edge bindings. A cost-per-token figure is meaningless until a reader knows which of these statements it actually buys.

Concrete scenarios:

1. A policy analyst comparing two cost-per-token figures needs to tell, without inspecting source code, whether either proof hides the model weights.
2. A relying party publishes a target requiring "verification under 60 s on a laptop, for exact-match next-token claims". The site needs a mechanical way to determine which rows match that target.
3. SASH is executed with an `--unsound-skip-*` flag inside a negative-control job. That run must never appear as a measured row under SASH's claim card.
4. A system's documentation makes no mention of quantum adversaries. Its claim card must not fill in "classical only" on the system's behalf.

## Goals

- Ensure every published row resolves to exactly one claim card, presented before any performance number (INV-CLAIM-1).
- Ensure every field on a card either copies what the system's documentation states at the pinned commit (with a source link) or contains the literal string `not stated` (INV-CLAIM-2).
- Validate every card against `schema/claim/1.schema.json` in CI.
- Make cards comparable field by field across systems and filterable via `claim_class`.
- Ensure any configuration that weakens the proved statement has no claim card and cannot produce a measured row (INV-CLAIM-4).

## Non-Goals

- Auditing or certifying security claims. A claim card documents what a system states; it does not verify soundness proofs or audit code ([PRD §5](../docs/PRD.md#5-non-goals)).
- Defining a controlled vocabulary for assumptions (Q1).
- Creating a formal specification language for relations. `relation` is plain English, with an optional link to a formal statement.
- Ranking systems by the strength of their claims.

## Proposed Design

### File and identity

- Location: use `systems/<system>/claim.yaml` when a system has a single configuration, or `systems/<system>/claims/<configuration>.yaml` when it has multiple configurations. A system uses one layout or the other, never both.
- Identity: each card is uniquely identified by `(system, configuration, card_version)`. `card_version` is a positive integer that increments with every merged edit to the card.
- Manifest reference: each run's manifest records the card it ran under as `claim: {system, configuration, card_version}`. CI rejects any run whose referenced card does not exist or whose configuration does not match the run's recorded configuration (RFC-0013).

### Configuration identity

A new configuration (meaning a separate card rather than a version bump on an existing card) is REQUIRED whenever any of the following changes, because each alters what an accepted proof establishes:

1. The upstream commit (a new pin can alter the statement, so the card is copied forward under the new configuration).
2. The acceptance policy (for example, FlashProve's exact-match policy versus its clipped-gap policy for full replies).
3. The proved model family or precision.
4. The hiding mode (whether weights are hidden or public).
5. The verifier used to decide acceptance (for example, a formally proved Lean verifier versus a tested C++ verifier), whenever they carry different security statements.

Changes that do NOT require a new configuration include batch size, prompt length within the workload's supported shapes, and hardware profile. Those belong to workloads and hardware profiles (RFC-0003, RFC-0006).

### Fields

Field types follow RFC-0012 conventions. `Text` is a non-empty string, `NotStated` is the literal string `not stated`, and `SourceRef` is either a URL containing the full 40-character hexadecimal upstream commit hash or a path in this repository at a full commit hash.

| Field | Required | Type | Content |
|---|---|---|---|
| `schema` | yes | `"claim/1"` | Schema identifier |
| `system` | yes | system id (`^[a-z][a-z0-9-]{1,31}$`) | Must match `systems/<system>/` |
| `configuration` | yes | id (`^[a-z0-9][a-z0-9-]{0,47}$`, RFC-0012) | Configuration identifier, e.g. `exact-match-lean` |
| `card_version` | yes | integer >= 1 | Monotonically increasing version number |
| `upstream` | yes | `{repo: Text, commit: 40-hex}` | Upstream repository and full commit hash |
| `claim_class` | yes | string, see [Claim class](#claim-class) | Filter key for closed divisions and targets |
| `relation` | yes | `Text` | One English sentence stating what holds if the verifier accepts. Optional `relation_formal: SourceRef` links to a formal statement (such as a Lean theorem) |
| `security.notion` | yes | `{kind: enum, verifier: Text}` | `kind` is one of `soundness`, `knowledge_soundness`, `other`, `not_stated`; `verifier` identifies which verifier the notion applies to |
| `security.level` | yes | `Text` or `NotStated` | Declared security level in its exact upstream form (for example, "q/2^124 + 2^-101 after q hash queries"), never rounded to a headline bit count |
| `security.model` | yes | `{assumption: Text or NotStated, adversary: enum}` | `assumption` describes the model (random oracle, standard model, interactive, other); `adversary` is one of `classical`, `quantum`, `not_stated` |
| `security.setup` | yes | enum | `transparent`, `trusted`, `not_applicable`, or `not_stated` |
| `zero_knowledge` | yes | `{claimed: bool or NotStated, hidden: Text or NotStated, not_hidden: Text or NotStated, status: enum}` | `status` is one of `proved`, `tested`, `proved_and_tested`, `neither`, `not_stated` |
| `assumptions` | yes | list of `Text`, empty only if `assumptions_not_stated: true` | Trusted commitments, configuration files, hardware assumptions, honest parties, or trusted inputs |
| `coverage` | yes | object, see below | Scope of computation covered by one proof |
| `binding` | yes | `{edges: list of Edge}` or `{statement: Text}` or `NotStated` | Per-edge binding table when the system provides one |
| `residual` | yes | list of `Text`, at least one entry, or `[not stated]` | What a dishonest prover can still do while passing verification |
| `quality_gap` | no | list of `{metric: Text, value: Text, source: SourceRef}` | Difference between the proved model and the reference model (for example, top-token disagreement rate), as reported upstream |
| `availability` | yes | enum | `available` (open source and runnable), `preview` (announced, not runnable), or `research` (paper code, runnable, unmaintained) |
| `sources` | yes | map from field path to `SourceRef` | One entry for every field above whose value is not `not stated` |
| `reviewed_by` | yes | list of `{handle: Text, organisation: Text, date: "YYYY-MM-DD", card_version: integer}` | Recorded review metadata; not rendered on the site or enforced by validation |
| `forbidden_flags` | no | list of strings | Flags that weaken the proved statement; mirrored into `system.yaml` (RFC-0005) for the CI policy gate |

`coverage`:

| Field | Type | Content |
|---|---|---|
| `phase` | enum `prefill`, `decode`, `both`, `not_stated` | Which inference phase a single proof covers |
| `unit` | enum `request`, `sequence`, `segment_grid`, `other` | What constitutes one proof in the benchmark |
| `tokens_covered` | `Text` | How tokens covered are counted per proof, in RFC-0004 terms (for example, "the window's 1,024 positions" or "every position in the grid") |
| `operations` | `Text` or `NotStated` | Which operations fall inside the proved computation (for example, "all transformer layers and the output head") |
| `policy` | `{kind: enum, detail: Text}` | `kind` is one of `exact_match`, `tolerance`, `other`, `not_stated` |

`Edge`:

```yaml
- edge: <Text, the system's own edge name>
  state: bound | unbound | absent | not_stated
  switch: <flag name that unbinds it, or null>
  source: <SourceRef>
```

The `state` values mean: `bound` (the system documents that this edge is bound in this configuration), `unbound` (the system documents that it is not bound, such as when a flag disables it), `absent` (this edge does not exist in the system's computation), and `not_stated` (upstream documentation is silent on this edge).

### Example (shape only)

```yaml
schema: claim/1
system: flashprove
configuration: exact-match-lean
card_version: 1
upstream: {repo: anthropics/FlashProve, commit: 9e2bdd8ff5bf9c62f18263d7dac189b0400b260c}
claim_class: next-token/exact-match/committed-weights
relation: >
  The output token is the top choice of the integer model whose weights were
  committed under the given commitment ID, on the given 1,024-token window.
relation_formal: not stated
security:
  notion: {kind: knowledge_soundness, verifier: "Lean verifier; C++ verifier tested against it"}
  level: "q/2^124 + 2^-101 after q hash queries, exact-match policy"
  model: {assumption: random oracle, adversary: classical}
  setup: not_stated
zero_knowledge:
  claimed: true
  hidden: weights
  not_hidden: "a declared list of weights"
  status: proved_and_tested
assumptions:
  - configuration files fixed before the hash function is drawn
  - the commitment ID is obtained from a trusted party
coverage:
  phase: prefill
  unit: request
  tokens_covered: "the window's 1,024 positions"
  operations: not stated
  policy: {kind: exact_match, detail: "top token of the integer model"}
binding: not stated
residual:
  - proves the integer model, which differs from the 16-bit model's top token at some positions
availability: research
sources:
  relation: https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/<path>
reviewed_by: []
```

The values above are illustrative examples drawn from `docs/PRD.md`. A production card fills in `<path>` and every other source link directly from upstream documentation and copies what upstream states.

### Rules

1. **Copy, do not infer (INV-CLAIM-2).** Every field reflects what the system's own documentation states at the pinned commit. Whenever upstream documentation is silent, the field MUST be `not stated` (or the enum value `not_stated`). The benchmark never infers undocumented properties, nor does it strengthen or round a stated security level.
2. **Card first (INV-CLAIM-1).** On every page and in every report showing a number for a system, the claim card for that number's configuration appears before the number. RFC-0009 enforces this ordering in the site generator.
3. **Sources (INV-CLAIM-3).** `sources` MUST contain an entry for every field path whose value is not `not stated`. Each `SourceRef` MUST include the full upstream commit hash matching `upstream.commit`. CI fails any card with a missing or mismatched source.
4. **Weakening configurations (INV-CLAIM-4).** Any configuration that weakens the proved statement (such as passing a SASH `--unsound-skip-*` flag) has no claim card. Runs using such flags are permitted only as negative-control jobs (`control: true`, RFC-0008). Those flags are recorded in `forbidden_flags`, and the CI policy gate (RFC-0013 gate 6) rejects any measured run whose logged command lines contain them.
5. **Versions.** Every modification to a card increments `card_version`.
6. **Published cards are frozen.** Each release records the `card_version` of every card it includes (RFC-0009), so subsequent card edits never alter an already published release.

### Claim class

`claim_class` is a slash-separated string of three lowercase tokens, `<output>/<policy>/<weights>`:

- `<output>`: `next-token`, `greedy-continuation`, `segment-grid`, `other`.
- `<policy>`: `exact-match`, `tolerance`, `other`.
- `<weights>`: `committed-weights`, `public-weights`, `other`.

Regex pattern: `^(next-token|greedy-continuation|segment-grid|other)/(exact-match|tolerance|other)/(committed-weights|public-weights|other)$`. A closed workload (RFC-0003) specifies a single `claim_class`, and only cards carrying that exact string compete in it. A target (RFC-0009) specifies a `claim_class` filter, which may use `*` as a wildcard for one token. Card authors assign the class based on the card's `coverage` and `relation`; it serves strictly as a filter key, not as a security statement.

### Validation

Running `iproofs validate systems/<name>/claim.yaml` executes these checks in order: YAML safe loading, schema validation against `claim/1`, INV-CLAIM-3 source completeness and commit matching, verifying that `upstream.commit` matches the commit pinned in `systems/<name>/system.yaml`, and verifying that `forbidden_flags` is a subset of `forbidden_flags` in `system.yaml`. Any failure produces an `integrity` or `config` error (RFC-0010) identifying the offending field path.

### Failure modes

| Failure | Response |
|---|---|
| A field contains an inference made by the benchmark | INV-CLAIM-3 catches it because the inferred field lacks an upstream source |
| Upstream documentation changes after the pin | No effect; source links pin the commit, and moving to a new pin creates a new configuration |
| Upstream documentation contradicts itself | The card quotes both statements in the field, each with its source link, and the release report notes the contradiction |
| A run references a card version that was later updated | The run retains its recorded `card_version`; the release displays the version frozen at release time, and CI fails if the run's version disagrees with the frozen card |
| A run has no matching claim card | CI fails the run, and no number is published (INV-CLAIM-1) |

## Alternatives Considered

- **Free-text claim paragraph.** Easy for teams to write, but rejected because CI cannot validate it, readers cannot compare claims field by field across systems, and targets cannot filter on it.
- **Formal statements only (such as Lean or a formal claim logic).** Precise, but rejected for v0.1 because most systems lack formal statements, and readers outside cryptography rely most on the plain-English relation and residual fields.
- **Benchmark-assigned security levels (such as normalised security bits).** Would enable a single summary column, but rejected because interpreting security proofs amounts to certification (a non-goal) and discards the exact stated formula.
- **One card per system regardless of configuration.** Rejected because distinct modes such as FlashProve's exact-match and clipped-gap policies prove different statements; collapsing them into one card would misrepresent at least one mode.
- **Publishing weakened configurations as labelled rows.** Considered because those measurements can be informative, but rejected because placing a fast figure for a weakened statement next to a full proof creates the exact comparison hazard this project exists to avoid. Weakened runs remain negative controls only.

The field structure combines three influences: the separation of relation, security definition, and assumptions common in proof-system harnesses; the edge-binding tables already produced by some provers; and the residual field, which captures what non-cryptographers most often overlook.

## Drawbacks

- Maintaining claim cards requires close reading of each system's documentation and keeping source links accurate, placing ongoing effort on card authors.
- Seeing `not stated` can look like criticism of a system; the site explicitly explains that it records upstream silence rather than the absence of a property.
- `claim_class` is intentionally coarse. Two cards sharing a class can still differ in security level or weight hiding, so the class only narrows a comparison and readers still need to inspect the card.

## Migration / Rollout

1. Land `schema/claim/1.schema.json` along with valid and invalid examples, the loader dataclass, and `iproofs validate` support.
2. Author claim cards for SASH and FlashProve, copying every field from upstream documentation at the pins listed in `docs/spec/00-overview.md`, with `reviewed_by: []`.

An earlier draft of this RFC used `reviewed_by_maintainers: false` and `security.bits` in the SPEC example. Both have been replaced by `reviewed_by: []` and `security.level`; no published data uses the older field names.

## Testing Strategy

Schema examples in `schema/claim/examples/`:

- `valid/minimal-all-not-stated.yaml`: all optional fields omitted, all stateable fields set to `not stated`; passes.
- `valid/flashprove-shape.yaml`: the shape example above with all source links populated; passes.
- `valid/binding-edges.yaml`: a `binding.edges` table exercising all four edge states; passes.
- `invalid/missing-relation.yaml`: fails validation on `relation`.
- `invalid/short-commit.yaml`: `upstream.commit: 9e2bdd8f`; fails pattern validation.
- `invalid/rounded-level-number.yaml`: `security.level: 124` (numeric instead of string); fails type validation.
- `invalid/bad-claim-class.yaml`: `claim_class: next-token/exact`; fails pattern validation.
- `invalid/date-unquoted.yaml`: `reviewed_by[0].date` given as an unquoted YAML date; fails type validation.
- `invalid/zk-status-unknown.yaml`: `zero_knowledge.status: likely`; fails enum validation.

Unit tests:

- `test_sources_complete`: a card with `relation` populated but missing `sources.relation` fails INV-CLAIM-3; adding the source link passes.
- `test_source_commit_mismatch`: a source URL pointing to a different commit hash fails.
- `test_forbidden_flags_subset`: a card listing a flag absent from `system.yaml` fails.
- `test_run_card_resolution`: a run manifest referencing a missing configuration fails; referencing an existing configuration passes.
- `test_claim_class_wildcard`: target filter `next-token/*/committed-weights` matches `next-token/exact-match/committed-weights` and rejects `segment-grid/exact-match/committed-weights`.
- Drift test (RFC-0012): confirms dataclass fields match the schema properties.

## Decisions

- Q1. `assumptions` is free text with no controlled vocabulary.
- Q2. Systems offering statistical guarantees (such as sampled recompute) populate `security` using `kind: other` along with the system's own description.
- Q3. `claim_class` does not include a fourth token for weight hiding. Hiding is recorded in `zero_knowledge.claimed`, and targets filter on that field directly.

## References

- [docs/PRD.md](../docs/PRD.md), sections 1, 4 (G1), 5 and 7 (F1).
- [RFC-0003](0003-workloads.md) (closed divisions use `claim_class`), [RFC-0005](0005-adapter-contract.md) (`system.yaml` `forbidden_flags`), [RFC-0008](0008-negative-controls.md) (weakened configurations as controls), [RFC-0009](0009-results-and-publication.md) (card-first site, targets), [RFC-0012](0012-schemas-and-serialization.md) (schema conventions), [RFC-0013](0013-validation-and-ci.md) (gates).
- FlashProve at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`; SASH zk-inference-prover at `eb95bfa887299d1637550228d42086c27cbb2b3b`.
