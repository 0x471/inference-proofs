# Inference Proofs: product requirements

## 1. Problem

Several open systems now generate cryptographic proofs showing that a language model produced a particular output. Each project publishes its own measurements on its own model, using its own timing conventions and proving its own claim. As a result, readers still cannot answer the practical questions they have when evaluating these systems:

- What exactly does a proof from system X establish, and under what assumptions?
- What does it cost in GPU time, memory, money, and proof size to prove one token on a given model?
- How long does verification take, and what hardware does it require?
- Does the verifier reject a tampered model, prompt, output, or proof?
- Would someone else get the same numbers by running the system themselves?

The first two open systems illustrate this gap. Both are licensed under Apache-2.0, both run on a single NVIDIA H100 80 GB GPU, and both represent substantial engineering work, yet their published figures cannot be compared directly:

| | SASH zk-inference-prover | FlashProve |
|---|---|---|
| Source, pin | `sg-ai-safety-hub/zk-inference-prover` at `eb95bfa`, results in `zk-inference-results` at `11decec` | `anthropics/FlashProve` at `9e2bdd8f` (v0.16.0) |
| Model | Llama-3.1-8B, W8A8 quantized, dense | Llama 4 Maverick, public 4-bit conversion, mixture of experts (about 400B parameters) |
| What one proof covers | One segment (a transformer layer over a block of token positions, or the output head); a full sequence is proved as a grid of segments | One request: a forward pass over a 1,024-token window that states the next token |
| Phase | Prompt and decode positions with greedy continuation | Prefill; full replies are covered under a looser "clipped gap" policy |
| Headline rate | 1.251 positions/s over 4,608 positions in loop scope (0.840 positions/s whole wall) | 111.23 ± 0.92 tokens/s of prefill at 24 requests per batch in steady state, excluding start-up and commitment |
| Proof size | 19.8 GB total for the 4,608-position run (290 segments) | 18.78 MB per proof on average |
| Verification | 119 s total for that run without a GPU | About 21 s per proof on one CPU thread (C++), or about 24 minutes with the Lean verifier |
| Weights | Pinned by commitment; the repository does not claim weight hiding at this pin | Commitment published, with weights masked except for a declared list (zero knowledge proved in Lean for the protocol and tested in code) |
| Soundness statement | Per-edge binding table, where each edge can be turned off with an `--unsound-skip-*` flag | Lean theorem for the Lean verifier under the exact-match policy in the random-oracle model |
| How numbers are graded | `constants.json`, where each figure lists its card, context, timing scope, and grade (measured, derived, projected, external, or asserted) | `docs/figures.tsv` and `limits-all-rows.tsv`; the measurement scripts and run records are not in the repository |

Every entry in the table comes from the two repositories at the stated pins. Level 1 v1.0 runs SASH at `4f41667297430a598165c4a8604258fe37d952ae`, the head of [pull request #36](https://github.com/sg-ai-safety-hub/zk-inference-prover/pull/36) on 2026-11-12, which was written by this project's owner and has not been merged upstream because upstream `eb95bfa` refuses one of the level's prompts ([`systems/sash/README.md`](../systems/sash/README.md)). Because the two systems differ in model, phase, timing scope, and security claim, dividing one headline number by the other tells the reader nothing. This project exists to close that gap.

## 2. Vision

Inference Proofs is an open, reproducible benchmark for provable inference. It evaluates systems on the same models, reference hardware, and timing rules, paired with an explicit statement of what each proof actually claims. Everything is run in the open so that prover teams and relying parties can inspect the methodology, verify the results, and point out errors.

The design draws inspiration from Ethproofs, which made Ethereum block zkVM provers comparable by fixing the workload (real blocks), publishing per-prover rows (hardware, latency, and cost), and letting a credible convener publish targets for teams to meet. Two lessons carry over directly: fixed workloads make results comparable, and externally authored targets show readers what matters in practice. Level 1 also ranks systems, though only within a single model's rung according to a published order rule ([RFC-0018](../rfcs/0018-level-1-ladder.md#order)), and never across rungs. One key difference remains: Ethereum blocks correspond to a single well-defined statement, whereas inference proof systems prove different things, so the claim must accompany every number.

## 3. Users

| User | Needs from the benchmark |
|---|---|
| Prover teams | A low-overhead way to publish credible, reproducible results, compare against peers fairly, and test against a shared negative-control corpus without building one from scratch |
| Researchers | Pinned, rerunnable measurements and a clear breakdown of where time and cost go across commit, prove, verify, and I/O |
| Relying parties (policy analysts, auditors, labs, governments, standards bodies) | A clear statement of what each system proves and what it leaves uncovered, along with whether a system meets a specific operational threshold |
| Funders | Trackable evidence of progress over time that does not rely solely on self-reported numbers from individual teams |

## 4. Goals

1. **G1. Claim first.** Every published figure is accompanied by a claim card stating the proved relation, security notion, assumptions, scope, and residual risks (what a dishonest prover can still get away with). Numbers without a claim card are not published.
2. **G2. Comparable by construction.** Workloads, reference hardware, timing scopes, and cost bases are fixed in advance. When two systems cannot run the same workload, the benchmark states that explicitly and compares only the quantities that are comparable.
3. **G3. Reproducible.** Every row pins the prover commit, container image digest, model hash, hardware and driver versions, and exact command line. A number is marked as measured only once someone other than the system's authors has reproduced it.
4. **G4. Adversarial.** Every system is tested against the same negative-control suite, and each row reports which tampering attempts the verifier rejects.
5. **G5. Open rules.** The methodology is documented in public RFCs, and all prose sticks to factual measurement language without superlatives or self-description. Within a model's rung, systems are ordered by a single published rule (RFC-0018); there is no composite score across properties and no ranking across rungs.
6. **G6. Low cost to join.** Provers integrate through a thin container adapter, and the harness never forks or patches upstream code. The single documented exception in Level 1 is the SASH pin, which points to an unmerged pull request written by this project's owner (Section 1).

## 5. Non-goals

- Ranking systems across rungs, or declaring any prover "fastest" or "best". Inside a rung, only RFC-0018's order rule ranks the systems that passed (owner decision, 2026-11-10).
- Certifying security. The benchmark records declared claims and test outcomes; it does not audit soundness proofs or upstream source code.
- Building or maintaining provers or shared proving libraries.
- Covering training, fine-tuning, or compute-accounting claims (out of scope for v0; see Roadmap).
- Setting policy thresholds. Relying parties define and publish their own thresholds (Section 9).

## 6. Scope of v0.1

> **Status, 2026-11-20.** Level 1 ([RFC-0018](../rfcs/0018-level-1-ladder.md), [`levels/L1.yaml`](../levels/L1.yaml)) and release v1.0 have superseded this scope and the roadmap in Section 10. Level 1 consists of three rungs with one system on each: FlashProve on Llama 4 Maverick 17B-128E Instruct (`l1-maverick-p512-o512`), SASH on Llama 3.1 8B Instruct (`l1-l31-8b-p512-o512`), and DeepProve on GPT-2 (`l1-gpt2-p512-o512`). DeepProve's `prove` step is wired up, while its `verify` step refuses to run because the upstream verifier reads its verifier key only from inside the proof file and provides no documented way to derive that key from the weights alone ([`systems/deepprove/README.md`](../systems/deepprove/README.md#weights-binding)). Because only passed rows are ranked and only within a rung (RFC-0018 OR-1), systems are ranked against one another only when at least two systems share a model. The rest of this section records the original v0.1 scope.

v0.1 runs two systems unchanged at pinned commits on a single reference machine type (unlike Level 1 v1.0, which runs SASH at a pull request; see G6):

1. **SASH zk-inference-prover**, on its native workload: Llama-3.1-8B W8A8 at both the headline shape (4,096 prompt positions plus 512 continuation positions) and one shorter shape.
2. **FlashProve**, on its native workload: Llama 4 Maverick (public 4-bit conversion) over 1,024-token windows at batch sizes 1 and 24.

Each workload also includes two reference rows to put proving costs into context:

- **Plain serving:** the same model and precision served unproved on the same hardware using a pinned vLLM release. The resulting overhead factor is the metric readers ask for most often.
- **Naive recompute:** a verifier that already holds the weights simply reruns the forward pass, showing what a cryptographic proof buys over direct recomputation.

v0.1 does not compare SASH and FlashProve on a shared model because neither system supports the other's model at these pins. Instead, v0.1 publishes both on their native workloads side by side, reporting normalised metrics (cost per proved token at the reference price, overhead relative to plain serving, and prover time per bit of active weights) alongside the claim cards that explain why their headline figures differ.

v0.1 also defines one closed workload, `l31-8b-c1024`: Llama-3.1-8B W8A8 at SASH's shorter shape under a fixed claim class where rows can be compared directly. Rows for this workload will be published only once a second system in the same claim class runs it through an adapter without upstream changes (RFC-0003 Q7, enforced at release freeze). Among the systems reviewed so far, only SASH runs it today; the source repositories for TOPLOC, Verde, the Private ML SDK, and zkPyTorch mention the model, but none of them has a claim card yet ([RFC-0003 §Closed workloads](../rfcs/0003-workloads.md#closed-workloads), [`workloads/README.md`](../workloads/README.md#closed-workloads)). Additional common workloads are planned for v0.2 (RFC-0003).

Historical note: Level 1 does not run `l31-8b-c1024`. Its Llama 3.1 8B rung runs `l1-l31-8b-p512-o512` ([`levels/L1.yaml`](../levels/L1.yaml)).

## 7. Requirements

### Functional

| ID | Requirement | RFC |
|---|---|---|
| F1 | A machine-checkable claim card schema, populated for each system from its own documentation | 0002 |
| F2 | A workload registry defining models by content hash, prompt sets by hash, shapes, and decoding rules, covering both native and common workloads | 0003 |
| F3 | A metric suite with fixed timing scopes (commit, prove, verify, whole wall, and steady state) and an explicit grade on every number | 0004 |
| F4 | An adapter contract using one OCI container per system that exposes `info`, `setup`, `commit`, `prove`, and `verify` over JSON files | 0005 |
| F5 | A reference hardware profile and a cost basis fixed for each release | 0006 |
| F6 | Evidence tiers (reported, peer-reviewed, reproduced), a reproduction protocol, and closed and open divisions | 0007 |
| F7 | A negative-control suite combining shared controls with system-specific controls, expecting rejection and recording outcomes per row | 0008 |
| F8 | A structured results format, a generated static website, and a per-release report | 0009 |
| F9 | A harness that executes jobs end to end, measures timing and resources externally, collects adapter-reported timings, and writes schema-valid result files | SPEC |
| F10 | CI checks that validate every submission against the schemas and recompute every derived number | SPEC |

### Non-functional

- **N1 Reproducibility.** Every run can be reproduced on rented commodity hardware that no maintainer controls.
- **N2 Transparency.** Raw outputs, logs, and verifier transcripts are preserved. Proofs above the size cap are stored by digest, with one archived proof kept per configuration.
- **N3 Honesty of numbers.** Results report ranges and sample sizes rather than a single cherry-picked run, and failed runs are always recorded rather than dropped.
- **N5 Licences.** Code is licensed under Apache-2.0, while specifications, data, and reports are licensed under CC BY 4.0. Contributions require DCO sign-off.

## 8. Success metrics

- v0.1: both initial systems reproduced end to end on the reference hardware by someone outside their authoring teams.
- v0.2: at least one common workload run by both systems through adapters alone, with no harness modifications.
- Within a year: at least five systems spanning at least two proof families, with at least one external team submitting its own runs unprompted.
- Adoption over attention: progress is measured by submissions and reproductions, not repository stars.

## 9. Targets set by relying parties

The benchmark does not decide what counts as "good enough". Instead, it invites relying parties (policy researchers, auditors, labs, and standards bodies) to publish their own targets, such as a maximum cost per proved token, a maximum verification time on a laptop, a minimum security level, or zero knowledge for model weights. Each row then reports "meets this target" or "does not" for every target and author alongside the claim card. All targets are versioned and attributed.

## 10. Roadmap

> **Status, 2026-11-20.** Historical. Level 1 and release v1.0 replaced this roadmap (see Section 6 for the current rungs and systems). DeepProve, a zkML prover of the type listed under v0.3, is already Level 1's GPT-2 system.

| Release | Content |
|---|---|
| v0.1 | SASH and FlashProve on native workloads, plain-serving and recompute reference rows, claim cards, negative controls, harness, and static site |
| v0.2 | A common workload family runnable by both initial systems and new entrants (RFC-0003), including a small dense transformer supported broadly and a mid-size open model, plus a first external system |
| v0.3 | Additional systems and proof families (other zkML provers, TEE attestation baselines, sampled recompute) with their own claim cards, plus the first targets from relying parties |
| later | Decode-heavy and long-context workloads, batch and latency profiles, and on-chain verification costs where relevant |

## 11. Risks

| Risk | Mitigation |
|---|---|
| Apples-to-oranges comparisons of headline numbers out of context | Pair every number with its claim card, separate rows by division, publish only normalised metrics, and avoid composite scores |
| Perception that the benchmark is captured by a single organisation | Keep the methodology, code, and data open, and ensure every run can be reproduced on outside hardware |
| High GPU cost of proving runs | Start with smaller and native workloads, run three repetitions instead of thirty, and store large proofs by digest |
| Provers that do not accept external patches (FlashProve is a research artifact explicitly "not accepting contributions") | Keep adapters in this repository pinned to upstream commits so no upstream change is ever required |
| Missing public measurement scripts or run records upstream | Measure externally under the harness's own timing rules and label upstream numbers as reported until reproduced |
| Negative controls that appear to pass only because the control itself is broken | Pair every negative control with a positive twin that must be accepted, and review controls with the same rigor as code |

## 12. Decisions

1. Name: "Inference Proofs", hosted at www.inferenceproofs.ai.
2. Runners do not cryptographically sign their result files (RFC-0014 Q1).
3. The reference price per GPU-hour is the median on-demand list price across at least three named providers, recorded on a stated date and held fixed for the lifetime of a release (RFC-0006 C3, C4).
