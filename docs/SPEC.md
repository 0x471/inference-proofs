# Inference Proofs: specification

This page serves as the index and executive summary for the specification corpus. Detailed specifications live under `docs/spec/`, and normative design decisions live in `rfcs/`. If any document here conflicts with an RFC, the RFC takes precedence (see `AGENTS.md`, Sources of truth). Requirement keywords (MUST, SHOULD, MAY) follow RFC 2119, and every canonical term is defined once in the [glossary](spec/10-glossary.md).

## Executive summary

Several open systems now prove that a language model produced a given output, but each publishes results on a different model, under different timing rules, and for a different security claim, making direct comparisons impossible ([PRD §1](PRD.md#1-problem)). Inference Proofs removes those differences wherever possible and labels them explicitly wherever they remain.

Five mechanisms underpin the design:

1. **A claim card with every number** ([RFC-0002](../rfcs/0002-claim-card.md)). No figure is published without a machine-checkable statement of the proved relation, security notion, assumptions, bound and unbound edges, and residual risks.
2. **A single labelled-quantity type** ([RFC-0012](../rfcs/0012-schemas-and-serialization.md), [RFC-0004](../rfcs/0004-metrics-timing-grades.md)). Every stored number carries its unit, timing scope, grade, evidence tier, and source. CI recomputes all derived numbers bit for bit from raw measurements.
3. **External measurement of provers at public pins** ([RFC-0005](../rfcs/0005-adapter-contract.md), [RFC-0010](../rfcs/0010-harness-runner.md), [RFC-0011](../rfcs/0011-measurement-and-sampling.md)). Each system runs at a pinned public commit behind a five-subcommand adapter contract without local source patches; the sole exception in Level 1 is SASH's pin, which points to an unmerged pull request written by this project's owner (see below). Hosted runs, including every v1.0 run, record the provider's network environment in their manifests, and the verification trace records which files the verifier opens rather than its network connections. The harness times adapter calls and proof releases externally while sampling GPU and host resource usage.
4. **Adversarial checks run by the harness** ([RFC-0008](../rfcs/0008-negative-controls.md)). Every verifier is tested against the same tampering controls, each paired with an honest twin so that a broken control or a verifier that accepts everything is caught immediately.
5. **Evidence tiers** ([RFC-0007](../rfcs/0007-evidence-tiers-and-reproduction.md)). Every quantity carries an evidence tier; all currently stored numbers are at tier `reported`.

Level 1 v1.0 ([RFC-0018](../rfcs/0018-level-1-ladder.md)) runs FlashProve on Llama 4 Maverick 17B-128E Instruct and SASH on Llama 3.1 8B Instruct on the level's fixed request, ranking passed rows only within their model's rung. Earlier, benchmark release v0.1 covered SASH zk-inference-prover and FlashProve on their native workloads on a single NVIDIA H200 141 GB reference profile ([RFC-0006 §H200 profiles](../rfcs/0006-reference-hardware-and-cost.md#h200-profiles)), along with plain-serving and recompute reference rows ([RFC-0003](../rfcs/0003-workloads.md), [RFC-0015](../rfcs/0015-reference-rows.md)), publishing no ranking and no aggregate score ([PRD §5](PRD.md#5-non-goals)).

## Corpus

| Section | Content |
|---|---|
| [00 Overview](spec/00-overview.md) | Thesis, users, goals and non-goals, v0.1 scope and run matrix, success criteria, design reflection, and risks |
| [01 Architecture](spec/01-architecture.md) | Components, module boundaries and allowed dependencies, and data flow from workload to site |
| [02 Public API](spec/02-public-api.md) | Public surfaces (CLI, schemas, adapter contract, file layout) and their stability guarantees |
| [03 Data model](spec/03-data-model.md) | Stored objects, keys, references, cross-object invariants, and lifecycles |
| [04 Error model](spec/04-error-model.md) | Error taxonomy and failure-mode catalogue |
| [05 Observability](spec/05-observability.md) | Structured logs, event catalogue, redaction rules, and diagnosing runs from a run directory |
| [06 Security](spec/06-security.md) | Threat model, trust boundaries, container hardening, secrets handling, privacy, and disclosure |
| [07 Testing strategy](spec/07-testing-strategy.md) | Test pyramid, named suites, fixtures, fake systems, and GPU-host tests |
| [08 Performance budget](spec/08-performance-budget.md) | Harness overhead limits, CI and build budgets, and the run-campaign budget method |
| [09 Release and versioning](spec/09-release-and-versioning.md) | Harness SemVer, schema and contract majors, benchmark releases, deprecation, and changelog rules |
| [10 Glossary](spec/10-glossary.md) | Canonical vocabulary |

## RFC index

| RFC | Title | Decides |
|---|---|---|
| [0001](../rfcs/0001-rfc-format.md) | RFC format | RFC template and numbering rules |
| [0002](../rfcs/0002-claim-card.md) | Claim card | What a proof establishes for each system configuration |
| [0003](../rfcs/0003-workloads.md) | Workloads, prompt sets and divisions | Workload schema, v0.1 workloads, prompt generation, seeds, and divisions |
| [0004](../rfcs/0004-metrics-timing-grades.md) | Metrics, timing scopes and grades | Recorded metrics, timing scopes, grades, derived formulas, and statistics |
| [0005](../rfcs/0005-adapter-contract.md) | Adapter contract | Container interface, `system.yaml`, proof release protocol, and verdict mapping |
| [0006](../rfcs/0006-reference-hardware-and-cost.md) | Reference hardware and cost basis | Hardware profiles, machine record fields, CPU binding, and cost basis |
| [0007](../rfcs/0007-evidence-tiers-and-reproduction.md) | Evidence tiers | Definition and rules for the `tier` label |
| [0008](../rfcs/0008-negative-controls.md) | Negative controls | Shared and system-specific controls, honest twins, outcomes, and disclosure |
| [0009](../rfcs/0009-results-and-publication.md) | Results format and publication | Run directories, releases, static site generation, and relying-party targets |
| [0010](../rfcs/0010-harness-runner.md) | Harness runner and job lifecycle | CLI commands, job state machine, error taxonomy, retries, and timeouts |
| [0011](../rfcs/0011-measurement-and-sampling.md) | External measurement and resource sampling | Clocks, proof-release watcher, and NVML and cgroup sampling |
| [0012](../rfcs/0012-schemas-and-serialization.md) | Artifact schemas, labelled quantities and serialization | Schema catalogue, versioning, quantity type, digests, and canonical JSON writer |
| [0013](../rfcs/0013-validation-and-ci.md) | Validation pipeline and CI gates | Exact rules for every CI gate |
| [0014](../rfcs/0014-provenance-and-integrity.md) | Provenance, pinning and artifact integrity | Pinning rules, image builds, model fetching, manifests, and commitment handling |
| [0015](../rfcs/0015-reference-rows.md) | Reference rows: plain serving and recompute | What reference rows measure and when they are null |
| [0016](../rfcs/0016-glyph-properties-and-states.md) | Glyph properties and states (no longer drives the site from Level 1, RFC-0018) | Six glyph properties, four states, state sources by row class, negative-control overrides, and the criteria file |
| [0018](../rfcs/0018-level-1-ladder.md) | Level 1: the ladder, six checks, cost and fidelity | Level file, rungs, common request, beacon prompts, sessions, release-group steady rule, serving ladder, six checks, fidelity and KL, five-petal glyph and decision tables, order rule, board file, and site; takes precedence over earlier RFCs for Level 1 releases |
| [0017](../rfcs/0017-requests-tasks-and-tested-states.md) | Requests, tasks and tested states | The request as the unit of comparison, per-request figures, task rules, medians, and planned additions (control coverage, proved-precision baselines, one row per verifier) |

## Pinned upstreams

Release v0.1 pinned the commits below. In Level 1, each system's pin is stored in `systems/<name>/system.yaml`.

| System | Repository | Commit |
|---|---|---|
| SASH zk-inference-prover | `sg-ai-safety-hub/zk-inference-prover` | `eb95bfa887299d1637550228d42086c27cbb2b3b` |
| SASH results (external figures) | `sg-ai-safety-hub/zk-inference-results` | `11decec3c0b62c707618aab5deb82750b355d202` |
| FlashProve | `anthropics/FlashProve` | `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c` (v0.16.0) |

Full commit hashes were resolved from the short pins in the PRD through the GitHub API on 2026-11-03.

Level 1 v1.0 runs SASH at `4f41667297430a598165c4a8604258fe37d952ae`, the head of [pull request #36](https://github.com/sg-ai-safety-hub/zk-inference-prover/pull/36) on 2026-11-12, written by this project's owner and not merged upstream, because upstream `eb95bfa` refuses one of the level's prompts ([`systems/sash/README.md`](../systems/sash/README.md)).
