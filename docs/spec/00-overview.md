# 00. Overview

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). Normative decisions live in the RFCs under [rfcs/](../../rfcs/README.md); if this section conflicts with an RFC, the RFC takes precedence.

## Thesis

Inference Proofs is an open benchmark for provable inference. It runs language-model proof systems unchanged on fixed workloads and reference hardware, measures them externally under fixed timing rules, tests every verifier against the same negative controls, and publishes every figure alongside a claim card explaining what an accepted proof establishes. The project measures provers; it does not build, certify, or globally rank them.

What sets this approach apart is pairing comparable measurement with an explicit statement of the proved claim. Neither suffices on its own: because inference proof systems establish different statements, a throughput figure without its claim cannot be compared meaningfully, and a claim without measured cost is not actionable.

## Problem

Several open systems now generate cryptographic proofs that a language model produced a given output, yet each publishes measurements taken in its own way, on its own model, and for its own claim ([PRD §1](../PRD.md#1-problem)). The first two systems in scope highlight the gap:

| | SASH zk-inference-prover | FlashProve |
|---|---|---|
| Pin | `sg-ai-safety-hub/zk-inference-prover` at `eb95bfa887299d1637550228d42086c27cbb2b3b`; results in `sg-ai-safety-hub/zk-inference-results` at `11decec3c0b62c707618aab5deb82750b355d202` | `anthropics/FlashProve` at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c` (v0.16.0) |
| Model | Llama-3.1-8B, W8A8, dense | Llama 4 Maverick, public 4-bit conversion, mixture of experts |
| One proof covers | One segment (a single layer over a block of token positions, or the output head); a sequence is proved as a grid of segments | One request: a pass over a 1,024-token window stating the next token |
| Headline rate (external, reported, upstream at the pins) | 1.251 positions/s over 4,608 positions in upstream loop scope; 0.840 positions/s in upstream whole-wall scope | 111.23 ± 0.92 tokens/s of prefill at 24 requests per batch in upstream steady scope, excluding start-up and commitment |

Level 1 v1.0 runs SASH at `4f41667297430a598165c4a8604258fe37d952ae`, the head of [pull request #36](https://github.com/sg-ai-safety-hub/zk-inference-prover/pull/36) on 2026-11-12, authored by this project's owner and not merged upstream because upstream `eb95bfa` refuses one of the level's prompts ([`systems/sash/README.md`](../../systems/sash/README.md)).

Because the models, phases, timing scopes, and claims all differ, dividing one headline number by the other tells the reader nothing. Users still lack consistent answers to basic questions: what a proof actually proves, what it costs per token on fixed hardware, how long verification takes, whether the verifier catches tampering, and whether a rerun reproduces the published figures.

## Users

| User | Needs | Served by |
|---|---|---|
| Prover teams | Low-cost, credible, reproducible benchmarks, fair comparisons, and a shared negative-control corpus | Adapter contract (RFC-0005), controls (RFC-0008) |
| Researchers | Pinned, rerunnable measurements and a clear cost breakdown across commit, prove, verify, and I/O | Timing scopes (RFC-0004), measurement (RFC-0011), provenance (RFC-0014) |
| Relying parties (policy analysts, auditors, labs, governments, standards bodies) | Clear statements of what is proved and unproved, and whether a system meets specific thresholds | Claim card (RFC-0002), targets (RFC-0009) |
| Funders | Evidence of progress over time that does not depend solely on self-reported metrics | Evidence tiers (RFC-0007), releases (RFC-0009) |

## Goals

| Goal | Statement | Mechanism | RFC |
|---|---|---|---|
| G1 Claim first | Every published number is accompanied by a claim card; no number is published without one | `claim/1` schema, card-first site rule INV-CLAIM-1 | [RFC-0002](../../rfcs/0002-claim-card.md) |
| G2 Comparable by construction | Fixed workloads, reference hardware, timing scopes, and cost basis; incomparable rows are clearly labelled | Workloads and divisions, scopes, profiles, derived metrics | [RFC-0003](../../rfcs/0003-workloads.md), [RFC-0004](../../rfcs/0004-metrics-timing-grades.md), [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md), [RFC-0015](../../rfcs/0015-reference-rows.md) |
| G3 Reproducible | Every row pins the prover commit, image digest, model hash, hardware, driver, and command | Provenance records | [RFC-0014](../../rfcs/0014-provenance-and-integrity.md) |
| G4 Adversarial | Every verifier faces the same negative controls, and every row reports its outcomes | Harness-applied controls with honest twins | [RFC-0008](../../rfcs/0008-negative-controls.md) |
| G5 Open rules | Open methodology documented in RFCs, factual measurement wording, and no single composite score | Publication rules | [RFC-0009](../../rfcs/0009-results-and-publication.md) |
| G6 Low cost to join | Thin container adapter without forking or patching upstream provers | One OCI container exposing five subcommands over JSON files | [RFC-0005](../../rfcs/0005-adapter-contract.md), [RFC-0010](../../rfcs/0010-harness-runner.md) |

Cross-cutting mechanisms support all six goals: labelled quantities and canonical serialization ([RFC-0012](../../rfcs/0012-schemas-and-serialization.md)), CI validation gates ([RFC-0013](../../rfcs/0013-validation-and-ci.md)), and external measurement ([RFC-0011](../../rfcs/0011-measurement-and-sampling.md)).

## Non-goals

- Ranking systems across rungs or declaring any prover superior. Within a single rung, only RFC-0018's order rule ranks systems, and there is no aggregate score.
- Certifying security. The benchmark copies declared claims and reports test results; it does not audit soundness proofs or upstream code.
- Building or maintaining provers or shared proving libraries.
- Measuring training, fine-tuning, or compute-accounting claims.
- Setting policy thresholds. Relying parties publish targets under their own names.
- In v0.1: common or closed workloads, sampled decoding, multi-GPU profiles (including for reference rows, RFC-0015 Q2), signed or attested results, and structured proof-format fuzzing.
- Publishing a normalised proof size: succinct proofs grow very little with model size, so dividing by model size would bias the figure toward larger models by construction (RFC-0004 §Non-Goals).

## v0.1 scope

v0.1 evaluates two systems unchanged at the commits pinned above on one reference prover profile (`prover-h200`: a single NVIDIA H200 141 GB SXM; its hosted form `prover-h200-hosted` and the H100 profiles remain declared in [RFC-0006 §H200 profiles](../../rfcs/0006-reference-hardware-and-cost.md#h200-profiles)) and one verifier profile (`verifier-cpu`: 8 CPUs, 32 GiB RAM, no GPU). Both run in the native division, alongside one closed workload on Llama 3.1 8B (`l31-8b-c1024`) whose rows will publish once a second system in the same claim class runs it (RFC-0003 Q7, [RFC-0003 §Closed workloads](../../rfcs/0003-workloads.md#closed-workloads)).

In the run matrix below, each configuration is measured for at least 3 repetitions (RFC-0004), and the first successful repetition of each configuration is followed by both the shared and system-specific negative controls (RFC-0008).

| Workload | Proving system | `ref-serve` row | `ref-recompute` row |
|---|---|---|---|
| `sash-l31-8b-c4096` | SASH | yes | yes |
| `sash-l31-8b-c1024` | SASH | yes | yes |
| `fp-maverick-w1024-b1` | FlashProve | yes, or recorded as not measurable on profile (RFC-0015) | yes, or recorded as not measurable on profile |
| `fp-maverick-w1024-b24` | FlashProve | same | same |

Each published row includes the claim card, per-scope timings and rates, GPU and host memory peaks, proof byte totals, verification times on 8 CPUs and 1 CPU, control outcomes, and derived metrics: cost per 1,000 proved tokens at the release price, overhead relative to plain serving, prover time per bit of active weights (shown with the claim cards and its stated limit, RFC-0004 INV-DERIVE-7), proof bytes and verification seconds per proved token, and amortised commit cost at 1 and 1,000 requests. Every figure is published with its timing scope, grade, evidence tier, and source.

v0.1 does not compare SASH and FlashProve on a shared model because neither supports the other's model at these pins.

## Success criteria

v0.1 is complete when every condition below holds, each verifiable directly from the repository:

1. SC-1: `releases/v0.1/index.json` exists and `iproofs validate` passes across the entire tree.
5. SC-5: Every row includes control outcomes for C1 through C8 and P1 through P2 (with `not_applicable` permitted when accompanied by a reason), and CI flags `fake-broken`.
6. SC-6: No quantity in the release is missing a unit, grade, tier, or source, and no time-based quantity is missing a scope (CI gate 5).

Looking past v0.1 ([PRD §8](../PRD.md#8-success-metrics)), v0.2 targets one common workload run by two systems through adapters alone, and the one-year target is five systems across at least two proof families. Adoption is measured by submissions and reproductions rather than repository stars.

## Design reflection

### What this solves that nothing else does

Each prover team's own benchmarks answer "how fast is my system under my own rules". Standard ML serving benchmarks measure unproved inference, while zkVM dashboards compare provers of a single well-defined statement such as an Ethereum block. Until now, nothing measured inference proof systems under one set of timing rules, on pinned hardware, and against the same tampering checks while keeping differing security claims visible. Pairing the claim card with every measurement is what makes cross-system results interpretable when the underlying claims differ.

### The three hardest problems on the path to v1

1. **Fair comparison across different claims and models.** Native workloads differ in model, phase, and proof unit. The design addresses this by leading with claim cards, separating divisions, explicitly flagging rough normalised metrics, and never placing native rows in head-to-head rankings (RFC-0002, RFC-0003, RFC-0004).
2. **External measurement without patching provers.** Upstream provers report internal phases under their own timing boundaries. The harness must time unmodified containerised binaries from outside, observe per-proof release timestamps through atomic file renames, and sample GPU and cgroup counters without perturbing execution (RFC-0005, RFC-0011). Whenever a scope cannot be observed externally, the metric is recorded as null with an explicit reason rather than estimated.
3. **Operating under GPU cost constraints.** A single configuration can consume hours of H100 time, model weights are often gated, and proofs can span tens of gigabytes. The design keeps costs manageable through three-repetition campaigns, storing proofs by digest rather than committing raw bytes, and replaying recorded seeds (RFC-0014).

### Load-bearing abstractions and their contracts

| Abstraction | Contract | Invariants | Owner |
|---|---|---|---|
| Labelled quantity | Every number is stored as `{value, unit, scope, grade, tier, source, null_reason}`; nulls require a reason and time units require a scope | No unlabelled number appears in any record | RFC-0012, RFC-0004 |
| Claim card | Per-configuration statement copied from upstream with citations, using `not stated` wherever upstream is silent | INV-CLAIM-1 to INV-CLAIM-4 | RFC-0002 |
| Workload | Model pinned by digest, prompts generated from a corpus digest with a recorded seed, fixed shape, and greedy decoding | INV-WL-1 to INV-WL-5 | RFC-0003 |
| Adapter | One OCI image exposing five subcommands over JSON I/O, with no upstream patches and harness-supplied commitments | Contract `adapter/1` | RFC-0005 |
| Job | One combination of system, workload, shape, and repetition, managed by a state machine that records failures instead of dropping them | Failed jobs are always written | RFC-0010 |
| Run directory | Append-only record of a job containing its manifest, controls, verifier outputs, and digests | `run.json` tiers are `reported`; derived numbers recompute bit-exactly | RFC-0009, RFC-0012 |
| Control | Harness-applied mutation paired with an honest twin and an expected outcome set | Marked `void` if the honest twin is not accepted | RFC-0008 |
| Release | Frozen snapshot of runs, reference hardware file, RFC commit, and claim card versions | Published releases are immutable | RFC-0009 |

### Failure modes designed against

| Failure mode | Design response |
|---|---|
| Headline numbers compared out of context | Display claim cards first, separate divisions, keep scope and tier attached to every number, and avoid composite scores |
| Adapter whose verifier always reports `accept` | Harness-applied controls catch this on C1 to C8, and CI runs `fake-broken` to confirm the suite detects it |
| Broken control mistaken for a working verifier | Run an honest twin first; any control whose twin is not accepted is marked `void` |
| Precomputed proofs for a public prompt set | Draw a fresh 64-bit seed per measured job and record it for replay |
| Swapped weight files | Verify per-file SHA-256 hashes before mounting weights into any container |
| Commitment supplied by the prover rather than the harness | Always pass the commitment from the harness's own `commit` record (AGENTS rule 6) |
| Weakened configuration published as a measured row | Enforce `forbidden_flags` in `system.yaml`, check command logs in CI, and prohibit claim cards for weakened configurations |
| Failed runs silently dropped | Record every failure with its kind, step, exit code, and trailing log lines, and count it in `n_failed` |
| Hand-typed derived figures drifting from raw data | Recompute every derived quantity bit-exactly in CI |
| Leaked secrets or host identifiers | Redact logs before writing, scan commits in CI, and construct machine records from an allowlist |

### Explicitly out of scope, and why

- Common workloads: neither v0.1 system can run the other's model without source patches, and patching provers is prohibited. Common workloads arrive via RFC in v0.2.
- Security certification: auditing cryptographic proofs and implementations requires effort beyond what a benchmark project of this size can credibly perform.
- Cross-rung rankings and single composite scores: both collapse distinct models or security claims onto one axis. Within a rung, RFC-0018 ranks passed systems by a single cost figure on a fixed request.
- Attested runners: hardware attestation shows where code ran, not whether a number reproduces on another machine; this is deferred to v0.3.

### The contributor in six months

A contributor adding a third system reads [RFC-0005](../../rfcs/0005-adapter-contract.md) for the container contract, uses `systems/fake/` as a template, authors `claim.yaml` per [RFC-0002](../../rfcs/0002-claim-card.md) with citations at the pinned commit, runs the CPU-only adapter tests, and opens a pull request. A contributor updating a metric checks its formula in [RFC-0004](../../rfcs/0004-metrics-timing-grades.md), updates `iproofs.derive` alongside its hand-computed unit test, and updates the RFC in the same change. Every canonical term is defined once in the [glossary](10-glossary.md).

### Where this spec is likely wrong

- RISK: Running the plain-serving reference for Maverick on the single-GPU FlashProve profile (one H100 80 GB or one H200 141 GB) may be infeasible because the 4-bit weights total 232 GB (external, reported, `systems/flashprove/README.md`) and exceed GPU memory. Plan: use llama.cpp on the same profile with partial host-memory offloading (RFC-0015 SRV-6) rather than introducing a multi-GPU profile; if that fails, record the failed runs and publish overhead as null.
- RISK: `prove.steady` cannot be observed externally if an upstream prover writes all proof files only at the end of execution. Plan: record the value as null with `not_externally_observable`, and display upstream steady rates only as `external` figures (RFC-0004, RFC-0011).
- RISK: SASH's segment grid does not align neatly with per-request proofs, so both tokens covered and the steady-state boundary depend on adapter declarations. Plan: verify the exact grid geometry from upstream documentation prior to the first beta run (RFC-0003 Q4, RFC-0005).
- RISK: Emulating the 8-CPU verifier profile on the prover host may behave differently from a dedicated 8-core machine due to cache topology and memory bandwidth. Plan: record `verifier_host` and CPU model, support separate verifier hosts, and reassess after v0.1 (RFC-0006).
- RISK: Large proof volumes complicate storage; the SASH 4,096-context run generates about 19.8 GB of proofs (external, reported, SASH results repository at `11decec3c0b62c707618aab5deb82750b355d202`). Plan: commit only digests to git and store raw proofs externally (RFC-0014).
- RISK: Host memory peaks excluding file cache are sampled at 10 Hz rather than tracked synchronously, so brief spikes can be missed. Plan: report both the exact kernel `memory.peak` (which includes page cache) and the sampled anonymous memory peak (RFC-0011).
