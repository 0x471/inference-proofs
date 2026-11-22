# RFC-0017: Requests, tasks and tested states

- Authors: 0xchqrles
- Created: 2026-11-10
- Requires: RFC-0003, RFC-0004, RFC-0005, RFC-0008, RFC-0009, RFC-0012, RFC-0015, RFC-0016
- Amended by RFC-0018 (2026-11-10): Part B is replaced. The Level 1 request is `p512-o512` on every rung; control coverage, the baseline and the verifier of record follow RFC-0018.

Write "None." where a section has no content. Normative text uses MUST, SHOULD and MAY as defined in RFC 2119.

## Summary

Every v0.1 figure is normalised per covered token. Because a "covered token" is simply any position bound by a proof, the two v0.1 systems cover positions for very different workloads: one FlashProve request covers a 1,024-token window and verifies a single output token, whereas one SASH request covers 1,024 prompt positions plus 64 output positions and verifies all 64 output tokens. This RFC makes the request the primary unit readers compare by adding five per-request derived metrics computable from existing runs, displaying the request shape alongside them, and defining a *task* as the rule governing when two rows may be compared side by side. It also adds the median to every stored statistic, and outlines the next wave of benchmark runs: closing control coverage gaps on each card row, adding a serving baseline at the proved precision, and running one row per documented verifier. No existing figure, formula, state, or stored record changes.

The RFC is split into two parts. Part A takes effect immediately and is implemented now. Part B records design decisions that take effect once the corresponding runs exist; until then, its figures remain absent and are never estimated.

## Motivation

Evidence (values are from `releases/v0.1/index.json` unless noted otherwise: grade `derived`, tier `reported`, means over n completed repetitions, on profile `prover-h200-hosted` for proving systems):

- FlashProve on `fp-maverick-w1024-b24` records 0.0056112 gpu_s/token at `prove.steady` (n = 4), while SASH on `sash-l31-8b-c1024` records 4.8442 gpu_s/token at `prove.session` (n = 3; SASH has no steady scope, RFC-0004 Q2). Neither figure directly answers what most readers want to know: how much it costs to prove one request.
- The two workloads ask for different requests. The FlashProve adapter passes range r = T − 1, e = T so `verify` checks only the single token following a 1,024-token window ([`systems/flashprove/README.md`](../systems/flashprove/README.md) §verify), while the SASH workload proves 1,024 prompt positions plus a 64-token greedy continuation. Accordingly, `workloads/fp-maverick-w1024-b24.yaml` sets `shape.output_tokens: 1`, whereas `workloads/sash-l31-8b-c1024.yaml` sets 64.
- Reporting cost per output token would measure adapter configuration rather than prover performance. At its pinned commit, FlashProve explains: "A request holds a window of exactly T tokens: the prompt, then the reply, then filler tokens"; "At full size, T is 1,024"; "To check a whole reply of R tokens (its end token included) after a prompt of P tokens, set r = P - 1 and e = P + R - 1" ([`docs/verifying.md` L115 to L123](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/docs/verifying.md#L115-L123)). It also reports: "With every token of a stored reply checked, under the looser clipped-gap policy, the rate at 24 per batch is 108.67 ± 2.8 tokens/second [...] The same requests, with no reply token checked, ran at 108.73 ± 2.7" ([`guide/performance.md` L17](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md#L17); upstream figures, grade external, tier reported). Because FlashProve's cost is driven by processing the entire window regardless of how many reply tokens fall in the checked range, dividing by our adapter's 1-token range would shift the reported cost 64-fold without changing anything in the prover.
- Session means currently mix sessions of different lengths. For production serving on `sash-l31-8b-c1024` (`serving-h200x1-hosted`, GPU-seconds per request at `prove.session`, n = 5), the mean is 12.29 and the median is 0.4996, with a range from 0.4927 to 58.47. Those five runs processed 1, 50, 360, 360, and 360 requests (the first ran before session lengthening, and the second was the sizing capture from RFC-0015 SRV-1), yielding 58.47, 1.497, 0.4960, 0.4996, and 0.4927 respectively, because fixed engine start-up is amortised over different session lengths. The Maverick serving row behaves similarly: 120 requests averaged 7.101, while three runs of 5,136 requests ranged from 0.2532 to 0.2568. Across all 297 v0.1 statistics that have non-zero spread, 34 have a maximum exceeding twice their minimum; all 34 belong to production serving, none to a proving system, and none feed an overhead ratio (which uses only the steady scope of lengthened runs, RFC-0004 INV-DERIVE-2).
- Under RFC-0016 INV-GLYPH-5, a card-row state means "not contradicted by the benchmark's negative controls", yet in v0.1 only two runs have a `controls.json`, both for FlashProve on `fp-maverick-w1024-b1`. Neither SASH nor FlashProve at batch 24 has run controls. In both existing control files, C3, P1, and P2 are `not_applicable`, leaving Model bound untested on every row and Whole output checked tested on only one configuration. One trial fell outside its expected set: C6 returned `accepted` in `2026-11-08-flashprove-fp-maverick-w1024-b1-prover-h200-hosted-3` (and `rejected` in `2026-11-09-flashprove-fp-maverick-w1024-b1-prover-h200-hosted-2`), though C6 does not map to any glyph property.
- Current overhead ratios compare a single-GPU prover running 4.839-bit weights against 4-GPU production serving of the publisher's FP8 release (RFC-0015 SRV-6). [PRD §6](../docs/PRD.md#6-scope-of-v01) originally asked for "the same model and precision served unproved on the same hardware". Both comparisons are informative, but v0.1 supplies only the first.
- FlashProve's active claim card is `exact-match-cp-verify`. Its Formally verified cell is No and its Security level cell is Not stated because upstream's formal statements cover only the Lean verifier and do not apply to `cp_verify` (RFC-0016 SRC-1). The Lean verifier is a documented acceptance path, yet no benchmark row exercises it.

Concrete user scenarios:

1. A policy analyst wants to know what it costs to prove a single model reply, but the site reports cost per 1M covered tokens without making clear how many covered tokens make up one reply.
2. When a second system joins on a different model and shape, its per-token numbers sit in a separate table; readers need an explicit rule explaining when two per-request costs answer the same question.
3. A reviewer sees Yes on SASH's Model bound cell and assumes a tampered-weights control ran and passed, when in reality no such control was executed.

## Goals

- Provide per-request metrics for GPU-seconds, GPU cost, proof size, and verification time that can be recomputed from existing v0.1 runs without running new jobs.
- Display the request shape (prompt tokens, checked output tokens, and covered tokens) directly alongside those figures.
- Define a single comparability rule across rows: the task.
- Store the median alongside the mean in every aggregate statistic.
- Document the next set of runs and the rules each one activates.

## Non-Goals

- Removing, renaming, or altering any existing RFC-0004 metric; per-token and per-weight-bit figures remain untouched.
- Introducing any composite score, ranking, or ordering across different tasks.
- Changing any glyph property, state definition, control mapping, or wording from RFC-0016.
- Executing new runs as part of this RFC (Part B defines future runs without adding any now).

## Proposed Design

### Terms

- **Request.** A single prompt paired with the output tokens submitted to the verifier, counted by `requests_count` (RFC-0004 §Recorded metrics). A system may emit one proof per request (as both v0.1 systems do) or multiple proofs per request.
- **Request shape.** The triple (P, N, W): P is the number of prompt tokens (`shape.prompt_tokens`), N is the number of checked output tokens (`shape.output_tokens`), and W is the number of covered tokens (D-TPR). W follows the coverage kind in RFC-0004 INV-TOK-1: `window` yields W = P (the token after the window is checked without evaluating its own position), while `prompt_plus_output` yields W = P + N.
- **Task.** A request shape paired with a decoding rule: (P, N, `decoding.rule`), identified as `p<P>-o<N>` (for example, `p1024-o64`).

### Part A: in force

#### Request rules

- INV-REQ-1. Every request within a workload shares the workload's shape, so any per-request quantity equals the corresponding per-token quantity multiplied by the covered tokens per request: X per request = X per token × `tokens_covered_total` / `requests_count`.
- INV-REQ-2. The checked output tokens for a request are the `claimed_output` tokens across its proofs, which the harness passes to `verify` from its own record (AGENTS.md rule 6). Summed across all proofs belonging to one request, their count MUST equal `shape.output_tokens`; any mismatch fails `prove` with error kind `adapter` (`iproofs.adapter.check_requests`). This invariant already holds across all 48 completed runs in `results/v0.1/` (verified on 2026-11-10), confirming that the displayed shape matches what each verifier actually checked.
- INV-REQ-3. Pages always display P and N alongside any per-request figure. Per-request figures belonging to different tasks must never be combined in one table, sorted together, or divided by one another.
- INV-REQ-4. No per-output-token figure is computed or displayed. For `window` systems, the checked token range is a request parameter with no measured effect on proving cost (see Motivation), so dividing by N would measure adapter settings rather than the prover. Readers who want a per-output-token number can divide the per-request figure by the adjacent N while seeing N explicitly.

#### Per-request figures

The following formulas extend the RFC-0004 catalogue. Level, grade, tier, quality-flag propagation, and null propagation follow RFC-0004's standard rules for repetition-level derived metrics, and D-STAT aggregates each one across repetitions:

| Formula id | Metric id | Formula | Unit | Scope | Null when |
|---|---|---|---|---|---|
| D-TPR | `tokens_covered_per_request` | `tokens_covered_total` / `requests_count` | token/request | none | Either operand is 0 (`not_applicable`) |
| D-GSPR-S | `gpu_seconds_per_request_<S>` | D-SPT-S × `gpus` × `tokens_covered_total` / `requests_count` | gpu_s/request | S | D-SPT-S is null (propagating its reason); `gpu_count` is missing (metric omitted, matching D-GSPT-S); `requests_count` is 0 (`not_applicable`) |
| D-COST-REQ-S | `cost_per_request_<S>` | D-COST-1K-S / 1000 × `tokens_covered_total` / `requests_count` | USD/request | S | D-COST-1K-S is null (propagating its reason); `requests_count` is 0 (`not_applicable`) |
| D-BPR | `proof_bytes_per_request` | `proof_bytes_total` / `requests_count` | B/request | none | `proof_bytes_total` is absent (`missing_input`), matching D-BPT on reference rows |
| D-VSPR | `verify_seconds_per_request` | `verify_seconds_total` / `requests_count` | s/request | `verify` | `verify_seconds_total` is absent (`missing_input`), matching D-VSPT |

Here S is `prove.steady`, `prove.session`, or `whole_wall` (as in D-SPT-S), and `gpus` is `inputs.gpu_count` (RFC-0004 INV-DERIVE-8). Each formula evaluates left to right directly on its listed inputs rather than chaining through another per-request derived metric, allowing release freezes to compute them cleanly for historical runs. D-GSPR-S and D-COST-REQ-S also apply to reference rows: production serving answers requests of the same shape, so per-request overhead equals per-token overhead.

The units `token/request`, `gpu_s/request`, `USD/request`, `B/request`, and `s/request` are added to `quantity/1`; `gpu_s/request`, `USD/request`, and `s/request` are time-based and therefore require a non-null scope (INV-QTY-3). Distinct units ensure per-request and per-token values cannot be mixed accidentally in formulas.

Because every v0.1 run predates these formulas, all five join `FREEZE_FORMULAS`: `iproofs release freeze` computes them from each unchanged `run.json`, records them under `freeze_derived`, and points D-STAT there (RFC-0004 Q3). New runs store them directly inside `run.json`, where gate G4 recomputes them.

#### Worked example

Using the synthetic round-number fixture from RFC-0004 §Worked example (invented values, not benchmark results): 5,000 tokens covered, 5 requests, 1 GPU, 3.60 USD per GPU-hour, 10,000,000 proof bytes, and 25 s of verification:

| Formula | Computation | Expected |
|---|---|---|
| D-TPR | 5,000 / 5 | 1,000 token/request |
| D-GSPR-prove.steady | 0.01 × 1 × 5,000 / 5 | 10 gpu_s/request |
| D-COST-REQ-prove.steady | 0.01 / 1,000 × 5,000 / 5 | 0.01 USD/request |
| D-COST-REQ-prove.session | 0.0125 / 1,000 × 5,000 / 5 | 0.0125 USD/request |
| D-BPR | 10,000,000 / 5 | 2,000,000 B/request |
| D-VSPR | 25 / 5 | 5 s/request |

#### What v0.1 reads per request

From the 2026-11-10 freeze (grade `derived`, tier `reported`, source `releases/v0.1/index.json`, ranges showing min to max across completed repetitions, and costs using the release's price basis from RFC-0006 C7):

| Row (workload, profile) | Request shape | GPU-seconds per request | GPU cost per request | Proof size per request | Check time per request |
|---|---|---|---|---|---|
| FlashProve (`fp-maverick-w1024-b24`, `prover-h200-hosted`) | P 1,024, N 1, W 1,024 | 5.746 (5.696 to 5.805), `prove.steady`, n = 4 | 0.008531 USD (0.008457 to 0.008618), `prove.steady` | 18.78 MB | 16.74 s (16.64 to 16.88), `verify` |
| FlashProve (`fp-maverick-w1024-b1`, `prover-h200-hosted`) | P 1,024, N 1, W 1,024 | 22.25 (22.16 to 22.36), `prove.steady`, n = 4, 1 failed | 0.03303 USD (0.03290 to 0.03319), `prove.steady` | 18.78 MB | 16.68 s (16.63 to 16.74), `verify` |
| SASH (`sash-l31-8b-c1024`, `prover-h200-hosted`) | P 1,024, N 64, W 1,088 | 5,271 (5,209 to 5,369), `prove.session`, n = 3, 1 failed | 7.825 USD (7.733 to 7.971), `prove.session` | 44.72 GB | 3,568 s (3,507 to 3,608), `verify` |
| Production serving (`fp-maverick-w1024-b24`, `serving-h200x4-hosted`, matched load) | P 1,024, N 1, W 1,024 | 0.09416 (0.09381 to 0.09459), `prove.steady`, n = 4 | 0.0001398 USD | not applicable | not applicable |
| Production serving (`sash-l31-8b-c1024`, `serving-h200x1-hosted`) | P 1,024, N 64, W 1,088 | 0.3345 (0.3311 to 0.3379), `prove.steady`, n = 4 | 0.0004966 USD | not applicable | not applicable |

Because the two systems run different tasks on different models at different timing scopes, this table simply lists the numbers without comparing them (INV-REQ-3).

#### Statistics

- ST-1. Every D-STAT aggregate, as well as every statistic computed across the proofs of a single repetition, stores `stats.median` alongside `n`, `n_failed`, `mean`, `stdev`, `min`, and `max`. The field is optional in `quantity/1` so earlier documents remain valid, and gate G4 continues to recompute older statistics that omit it.
- ST-2. A statistic's primary `value` remains its mean (RFC-0004 §Statistics, INV-QTY-8). The median adds visibility rather than fixing mixed populations: when a configuration pools sessions of different lengths (see Motivation), neither summary describes a single population. The actual fix is tracked in [Q4](#decisions).

#### Site

On each system page, the secondary metrics table adds three rows per configuration below the existing entries: covered tokens per request (with P and N in the row label), GPU-seconds per request, and GPU cost per request. The latter two display the steady-scope statistic (or the session-scope statistic when a system has no steady scope) with the scope explicitly named, matching how the per-weight-bit column works (RFC-0004 INV-DERIVE-7). The overview page is unchanged. Per-request proof size and verification time are stored in the release index but omitted from the page because, at one proof per request, they duplicate the overview's existing proof size and verification time figures.

### Part B: decided, in force with its runs

#### B1. Tasks

- TASK-1. Two workloads belong to the same task when their P, N, and decoding rule all match. Rows sharing a task may appear in the same table and be sorted together by per-request cost even across different models: each row identifies its model, while overhead against serving (RFC-0004 D-OVERHEAD-S) factors out the underlying model's cost.
- TASK-2. The first shared task MUST fit within the documented constraints of every participating system at its pinned commit:
  - FlashProve packs prompt and reply into a single window of T = 1,024 tokens, with the reply allowed to end one token past the window, requiring P + N ≤ 1,025 (see Motivation and [`docs/verifying.md` L125 to L128](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/docs/verifying.md#L125-L128)).
  - SASH requires the prompt length to be a power of two and an exact multiple of the block size, with the generated block serving as the output: `assert a.prefix > 0 and (a.prefix & (a.prefix - 1)) == 0, "prefix must be a power of two"` ([`gen_ids.py` L52 to L53](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/eb95bfa887299d1637550228d42086c27cbb2b3b/harness/witness/gen_ids.py#L52-L53); `systems/sash/entrypoint` `geometry` rejects any other shape). Consequently, for any multi-token reply, P cannot exceed 512 (leaving room inside FlashProve's 1,024-token window) and N must divide P.
  - SASH's existing 1,024 + 64 shape overflows FlashProve's window, while a 960-token prompt fails SASH's power-of-two constraint.
  The proposed first common task is `p512-o64` with greedy decoding ([Q5](#decisions)). On FlashProve this uses r = 511 and e = 575 with 448 filler tokens and no token file; upstream's own full-size real-weight runs generated replies under `--max-tokens 64` ([`integrations/LIMITS.md` L117 to L120](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/LIMITS.md#L117-L120)). On SASH it corresponds to 9 blocks of 64 positions, a subset of the 17-block grid already proved across its three v0.1 runs. A follow-up task, `p512-o512`, fills FlashProve's window with zero filler and matches the block size used across SASH's recorded runs ("Every recorded run has `S = 512`"); it comes second because FlashProve's pinned commit demonstrates exact-match replies of that length only on synthetic weights ([`integrations/README.md` L56 to L66](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/README.md#L56-L66)).
- TASK-3. Under exact match, the reply for a task request MUST be produced by the committed model itself. At its pin, FlashProve notes: "At exact match a reply passes only if every token is the integer model's own choice: of 96 stored replies each from stock vLLM at 16 bits and at FP8, none did"; "Through vLLM with a plug-in that is designed to compute the integer model exactly, 48 of 48† short replies were proved and checked" ([`guide/performance.md` L35](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md#L35)). That plug-in exists in the repository (`integrations/vllm/integer_model/`, described as "lets vLLM run the integer model"), though upstream cautions about those runs: "None of them was made on the released programs, or with the scripts exactly as they are in this repository" ([`integrations/LIMITS.md` L110](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/LIMITS.md#L110)). Adapters may rely only on what upstream documents without patching source (AGENTS.md rule 1). If a system cannot generate an exact-match reply at its pin, its row for that task states this explicitly and carries no figure; using a looser acceptance policy constitutes a different claim class and requires a separate claim card (RFC-0002 §Configuration identity).

RISK: The integer-model plug-in path might not work inside the adapter contract (no network, single container, vLLM shut down before `cp_prove` starts). To manage this risk, the workload will land together with the adapter update and its first verified run, never beforehand.

#### B2. Control coverage

- COV-1. For every card row, each negative control mapped to a property in RFC-0016 SHOULD have a recorded pass or contradiction in at least one run read by that row, rather than `not_applicable`, `void`, `error`, or missing. Currently, Model bound has no control outcomes on any row, and Whole output checked has C1, C2, and C4 outcomes only on FlashProve at batch 1.
- COV-2. Closing these gaps requires:
  - For SASH: running the control suite in split parts (RFC-0008 §Split suites) against a repetition whose proofs were retained (`--keep-io`), followed by preparing a perturbed commitment for C3 and P1.
  - For FlashProve: generating the perturbed commitment (`iproofs controls --prepare-perturbed`), then running the suite on both a batch-1 job and a batch-24 job (needed for C7, which requires at least two requests in one batch).
- COV-3. Until those controls run, the system page displays "not run" for each missing control, as already required by RFC-0016 OVR-7. This RFC adds no visual indicator to the overview; distinguishing tested from untested Yes states on the overview is left to a dedicated site design change reviewed by the owner before merge.

#### B3. A serving baseline at the proved precision

- BASE-1. Reserves a second overhead metric, D-OVERHEAD-SP-S (`overhead_vs_same_precision_<S>`), defined as the prover's GPU-seconds per token divided by an unproved engine serving the workload's own weight files at the proved precision on the prover's profile. This isolates pure proving overhead, while D-OVERHEAD-S against production serving remains the headline metric and retains its name.
- BASE-2. The identifier and formula are reserved until a reference adapter serves the proved precision. For Maverick workloads, that corresponds to the llama.cpp adapter on branch `ref-serve-gguf`. Because SASH quantizes weights at load time and no standard engine serves its W8A8 format unproved, SASH's row retains only the production-serving overhead and notes why.

#### B4. One row per verifier

- VER-1. Whenever a system documents multiple acceptance paths carrying different security statements (such as FlashProve's `cp_verify` and Lean `verify`), each path forms a distinct configuration with its own claim card and row (RFC-0002 §Configuration identity 5). The benchmark will add a second FlashProve row running the Lean verifier on the batch-1 workload, reporting its verification time alongside its other figures.

### Failure modes

| Failure | Response |
|---|---|
| A proof claims a different count of output tokens than the workload shape specifies | `adapter` failure during `prove` (INV-REQ-2) |
| A historical run lacks an input required by a per-request formula | Recorded as null with `missing_input` in `freeze_derived`, while the run still counts in `n` for other metrics |
| Per-request metrics are computed on a CPU-only test profile | D-GSPR-S is omitted (no GPU count), while the remaining metrics are computed normally |
| Two rows from different tasks are placed into one per-request comparison table | Caught in review (INV-REQ-3); no automated gate checks page layout |

## Alternatives Considered

- **Publish cost per output token.** Although intuitive for readers, upstream FlashProve measurements show zero additional cost for verifying more reply tokens inside a fixed window, so dividing by checked output tokens would mostly reflect adapter configuration (INV-REQ-4).
- **Replace per-token metrics altogether.** Removing older metrics would avoid showing two units, but the project owner wants to keep the existing per-token numbers, stored runs already carry them, and distinct units prevent accidental mixing in formulas.
- **Add an explicit `task` field to `workload/1`.** Deferred because P, N, and the decoding rule already exist in the schema, and storing a redundant derived field risks inconsistency.
- **Use the median as a statistic's primary `value`.** Although more resilient to outliers, switching away from the mean would alter every existing published statistic; deferred to Q4.
- **Add an overview badge for untested states immediately.** Deferred (COV-3) because it is a visual design choice and the underlying control coverage already appears on each system page.

## Drawbacks

- Requests are not uniform across workloads, so a per-request figure is meaningless without its shape (which is why INV-REQ-3 binds them together).
- Until systems actually execute a common task, per-request figures for FlashProve and SASH still answer different questions just like per-token figures; this RFC establishes the unit, while Part B1 is what enables direct comparison.
- Adds five new metric ids and five new units to maintain.

## Migration / Rollout

- `quantity/1` (additive under RFC-0012 §Schema versioning): adds the five new units (three added to INV-QTY-3), the metric ids `tokens_covered_per_request`, `proof_bytes_per_request`, `verify_seconds_per_request`, `gpu_seconds_per_request_<S>`, and `cost_per_request_<S>`, plus optional `stats.median`. The invalid example `statistic.unknown-key` is updated to use the key `mode`.
- `releases/v0.1/index.json` is re-frozen, adding 261 keys (the new per-request statistics, their `freeze_derived` entries, and `median` on each statistic) without changing any existing value or `inputs_digest`.
- No `run.json` files or adapters need changes, as INV-REQ-2 already holds for every stored run and test system.
- Part B rollout order and rough cost estimates (derived from stored job durations and list prices in `docs/runbooks/hf-jobs.md`, not measurements):
  1. Control coverage (B2): roughly 95 USD, primarily CPU time.
  2. Same-precision baseline and recompute rows on H200 (B3): roughly 20 USD.
  3. First shared task (B1): roughly 30 USD for FlashProve, plus SASH repetitions at the new shape.
  4. Lean verifier row (B4): roughly 80 USD, dominated by verification wall time at about 24 minutes per proof per upstream figures ([PRD §1](../docs/PRD.md#1-problem); external, reported).

## Testing Strategy

- `test_derive.py::test_worked_example`: checks all five expected per-request values above against `expected.json`.
- `test_derive.py::test_freeze_values_fill_only_missing_keys`: verifies that freezing a stored run populates D-TPR, D-BPR, and D-VSPR (1,000, 2,000,000, and 5) and yields null with `missing_input` for D-COST-REQ-S when D-COST-1K-S is absent.
- `test_stats.py::test_stat_median_is_not_the_mean_when_one_run_is_far_off`: confirms that `[577, 16000, 16100, 16200]` produces mean 12,219.25 and median 16,050.
- `test_adapter_requests.py::test_claimed_tokens_per_request_must_match_the_shape`: confirms that one 64-token proof or two proofs summing to 64 pass at N = 64, while 63 tokens fails as `adapter` at `prove`.
- `test_site_e2e.py::test_every_figure_traces_to_the_index`: asserts every newly displayed row matches its stored index statistic to four significant digits.
- `test_freeze.py::test_deterministic_index`: checks the golden index output including the new keys.

## Decisions

- Q1. The request becomes the primary unit for reader comparison, while existing per-token and per-weight-bit figures remain unchanged.
- Q2. No per-output-token figure is published (INV-REQ-4).
- Q3. Task identity is derived from existing workload shape fields rather than adding a redundant field.
- Q4. Open, recommended: keep the mean on pages, and restrict session-scope statistics on reference rows to runs matching the release's configured session length (`batches_per_session_run`), mirroring how the steady-scope overhead join filters runs; excluded runs of other lengths are listed with the reason. Displaying the median instead would mask the mixed sample (here it happens to read 0.4996 only because three of the five runs were lengthened).
- Q5. Open, recommended: adopt `p512-o64` (greedy) as the first common task (TASK-2) and `p512-o512` as the second. An earlier `p960-o64` proposal, drafted before checking SASH's pinned code, cannot run on SASH.
- Q6. Recommended: do not add an untested-state badge to the overview. System pages already show which mapped controls ran and which did not, and running the missing controls (B2) closes the gap directly.

## References

- FlashProve at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`: [`docs/verifying.md`](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/docs/verifying.md) and [`guide/performance.md`](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md), read 2026-11-10.
- [RFC-0004](0004-metrics-timing-grades.md) §Tokens covered, §Derived metric catalogue, §Statistics, Q3.
- [RFC-0008](0008-negative-controls.md) §Split suites; [RFC-0016](0016-glyph-properties-and-states.md) §Negative control override.
- SASH at `eb95bfa887299d1637550228d42086c27cbb2b3b`: [`harness/witness/gen_ids.py`](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/eb95bfa887299d1637550228d42086c27cbb2b3b/harness/witness/gen_ids.py), read 2026-11-10.
- [RFC-0015](0015-reference-rows.md) SRV-1, SRV-6; [PRD §6](../docs/PRD.md#6-scope-of-v01).
