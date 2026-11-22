# RFC-0015: Reference rows: production serving and recompute

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0003, RFC-0004, RFC-0005, RFC-0006, RFC-0011
- Amended by RFC-0018 (2026-11-10): for Level 1 the serving baseline is a concurrency ladder at full load (RFC-0018 CO-4), not a batch matched to the prover's.

## Summary

Every native workload receives two reference rows: production serving and recompute. Production serving represents plain, unproved model serving as providers actually run it: an optimised serving engine running the publisher's release precision with all weights resident in GPU memory, tensor-parallel across the fewest GPUs of the proving system's GPU model that can hold it. Recompute represents a verifier that holds the weights and reruns the forward pass on the system rows' profile. Production serving supplies the overhead factor in GPU-seconds per token (RFC-0004 D-OVERHEAD-S), while recompute shows what a proof buys compared with simply holding the weights and re-running the model. Both are implemented as standard adapters (`systems/ref-serve` and `systems/ref-recompute`) under the RFC-0005 contract with `kind: reference`, allowing the harness, timing, and statistics pipeline to stay shared without special cases beyond which steps run.

## Motivation

PRD §6 calls for "two reference rows per workload, so every proof cost reads against something": plain serving with a pinned vLLM release on the same model, precision, and hardware, alongside naive recomputation by a verifier holding the weights. A raw proving rate says little about cost relative to the underlying inference work, whereas the overhead multiple against production serving makes that cost legible (RFC-0004 D-OVERHEAD-S, measured in GPU-seconds per token since the 2026-11-09 amendment). Recompute also provides a direct second check on claimed outputs: FlashProve's claim card notes that it proves an integer model whose top token occasionally differs from the 16-bit model (RFC-0002 example residual), and readers need to see how often claimed outputs agree with a standard forward pass.

## Goals

- Recompute rows share the exact workload IDs, versions, prompts, shapes, and hardware profile of the system rows. Production-serving rows share the same workload IDs, versions, prompts (replayed under SRV-8), and shapes on a serving profile of the same GPU model (RFC-0006 R6).
- Tokens are counted using the exact coverage rule declared on the proving system's claim card (RFC-0004 INV-TOK-1) so D-OVERHEAD-S compares like with like.
- Production serving runs a pinned engine on the publisher's release at the precision the publisher releases for serving, pinned via an ungated byte-identical copy (SRV-6). Any precision substitution in recompute is explicitly declared and flagged.
- Output agreement between recompute and each system's claimed outputs is reported as raw counts and a derived rate, completely separate from verification verdicts.
- If a reference row cannot execute on its profile, the failure is recorded and any metric depending on it is set to null with an explicit reason.

## Non-Goals

- Tuning the serving engine beyond its built-in defaults and the options required by the workload shape (SRV-3). The baseline is "production serving with the engine's defaults", not the peak throughput achievable through custom tuning.
- Decode-heavy serving profiles, latency-under-load curves, or arrival-rate simulations (none exist in v0.1).
- Deciding which output is "right" when recompute and a proving system disagree. Agreement is reported as a measurement without changing any verdict.
- Running recompute rows on hardware profiles other than the system rows' profile.

## Proposed Design

### Reference systems

Two adapter directories follow the normal RFC-0005 layout with `kind: reference` and `reference_role: serve | recompute` in `system.yaml`:

```
systems/ref-serve/       Dockerfile (engine image by digest), entrypoint, system.yaml, sizing.py, dev_install.py, README.md, tests/
systems/ref-recompute/   Dockerfile (same engine image by digest), entrypoint, system.yaml, README.md, tests/
```

Reference systems carry neither a `claim.yaml` (they prove nothing) nor negative controls. Each reference adapter's container image is built `FROM` the engine image pinned by digest, pushed like any release image (RFC-0014 B7), and pinned in `system.yaml` under `image`, with the `engine` field naming the underlying engine. A plugin published by the engine's own project counts as part of the engine pin once installed into the adapter image and pinned in `inputs.lock` (RFC-0014 B2), and is documented in the adapter README. On the site, reference systems appear solely as reference rows beside a workload's system rows, never as proving systems.

```yaml
# systems/ref-serve/system.yaml (shape)
schema: "system/1"
name: "ref-serve"
kind: "reference"
reference_role: "serve"
engine: {name: "vllm", version: "<pinned release>", image: "<repo>@sha256:<digest>"}
workloads:
  - id: "sash-l31-8b-c1024"
    load_point: "matched"                # matched | high (SRV-1)
    gpus: 1                              # the serving profile's gpu.count (SRV-6)
    precision_used: "BF16"               # the serving record's precision (SRV-6)
    precision_substitution: null         # always null for reference_role serve
    engine_args: ["--tensor-parallel-size", "1", "--max-model-len", "1088", "--max-num-seqs", "1"]  # SRV-3 allowlist
incremental_proofs: true
deterministic_proofs: false
forbidden_flags: []
```

### Steps per job

For `kind: reference`, the runner (RFC-0010) executes `info`, `setup`, and `prove`, marking `commit` and `verify` as `skipped`. Under RFC-0004, `commit_seconds` and D-COMMIT-AMORT metrics are therefore null with `null_reason: not_applicable`, `whole_wall` is null with `not_applicable` (since there is no commit start event), and `prove.session` and `prove.steady` are measured identically to proving systems.

- REF-1. The `prove` subcommand loads the engine once, processes requests in workload order, and atomically writes one release directory `/io/proofs/<batch_id>/outputs.json` after each batch (RFC-0005 rename contract). The release watcher (RFC-0011) timestamps each directory so `prove.steady` (first batch release to last batch release) excludes engine start-up and weight loading, while `prove.session` includes them, matching the boundaries used for proving systems.
- REF-2. Release directories from reference systems are labelled "outputs" rather than proofs across all records and pages, and the harness computes no proof byte counts for them.
- REF-3. The harness counts tokens per release using the coverage rule of the proving system the reference row serves: window positions for `window` coverage, or prompt plus output positions for `prompt_plus_output` coverage (RFC-0004 INV-TOK-1).

### Production serving (`ref-serve`)

Amendment of 2026-11-09. This amendment replaces SRV-1 through SRV-7 (including the 2026-11-08 amendment) and drops the rule that plain serving runs on the proving system's profile. Readers want to know how much overhead proving adds under normal serving conditions, the conditions providers use in production. The figure constructed here follows the structure of FlashProve's own published baseline ([guide/performance.md L27](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md?plain=1#L27): stock vLLM, FP8, all weights in GPU memory, steady state) and states its conditions just as explicitly.

- SRV-1. Load points. Each workload defines two serving configurations distinguished by `load_point`:
  - `matched`: batch size equal to the workload's `batch_size`. Batches per session match the workload's `batches_per_session`, or increase at the same batch size until the steady window is expected to last at least 60 s. This count is fixed per `(workload, GPU count)` in `system.yaml` as `batches_per_session_run`, derived from the first capture, and printed in the conditions line. Any additional prompts come from the same seeded generator used at high load (SRV-8).
    - Sizing (amendment of 2026-11-09). `batches_per_session_run` is computed rather than typed: `iproofs serving size-session RUN_DIR` reads a completed matched capture for that `(workload, GPU count)`. Seconds per steady batch equal `prove_steady_seconds` divided by `(batches - 1)` because the steady window begins at the first batch's final release (RFC-0004 INV-SCOPE-5). The required steady batch count is the smallest integer `n` such that `n × seconds_per_steady_batch ≥ 120 s`, giving a total count of `n + 1` (accounting for the first batch outside the steady window) and never falling below the workload's `batches_per_session`. Targeting 120 s (double the 60 s join minimum) provides headroom so runs up to twice as slow per batch as the sizing capture still clear 60 s, while keeping the 60 s join minimum unchanged. A single-batch capture has no steady window and is refused (`config`) because start-up time cannot be separated from batch time. A comment in `system.yaml` records the capture's run ID and the command used.
    - Sizing capture (amendment of 2026-11-09, Q10). While a matched entry's `batches_per_session_run` is null, `iproofs run --system ref-serve ... --sizing-batches N` (or `hf-job.sh` option `sizing=N`) serves `N` batches at the workload's batch size (`N ≥ 2`) to establish a steady window, with `--prompts-from` replaying the source run's prompts as required by SRV-8. The runner rejects this option (`config`, before any step) at high load, when `batches_per_session_run` is already set, when `N < 2`, or for any system other than production serving. The manifest records `workload.sizing_capture: true`, `run.json` logs the warning "sizing capture: it sizes batches_per_session_run and joins no overhead (RFC-0015 SRV-1)", and the run never enters overhead calculations regardless of steady duration (RFC-0004 INV-DERIVE-2 (f)). `iproofs serving size-session` accepts sizing captures like any matched capture and prints `capture.sizing_capture`. `N` is picked so the steady window clearly exceeds one second (minimizing per-request round-trip and watcher granularity noise) while keeping the job brief: for `sash-l31-8b-c1024` at TP1, `N = 50` (a single request of 1,024 prompt tokens and 64 output tokens at batch 1 on one H200 takes roughly 0.5 s projected, never measured, yielding about 25 s steady time across 49 batches; `docs/runbooks/hf-jobs.md` S1b).
  - `high`: a batch sized to the engine's default maximum sequence count for the profile's GPU (1,024 on GPUs with 70 GiB or more in both usage contexts, [vllm/engine/arg_utils.py L2933 to L2942](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/engine/arg_utils.py#L2933-L2942)), leaving `--max-num-seqs` at its default. Batches per session equal `max(batches_per_session, 2)`. The engine admits as many sequences from the batch as its KV cache holds and queues the rest, just like a loaded server.
  - Any serving run whose steady window is shorter than 60 s keeps its recorded value alongside the warning "steady scope under 60 s" in `run.json`, but joins neither D-OVERHEAD-S nor D-OVERHEAD-HIGH-S (RFC-0004 INV-DERIVE-2) because short windows are dominated by per-batch round-trip overhead and watcher granularity. Serving runs require `mechanism: inotify` (RFC-0011 W-1); falling back to polling fails the job with `environment`.
  The load point is recorded as part of the configuration (`workload.load_point` in the RFC-0010 manifest).
- SRV-2. Greedy decoding (temperature 0), `max_tokens` equal to the workload's `output_tokens` (1 for next-token workloads), and `ignore_eos` set to true ([sampling_params.py L331](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/sampling_params.py#L331-L333)), ensuring every request produces the exact token count the harness expects. Returning any other token count fails with `adapter`.
- SRV-3. Engine options are strictly limited to engine defaults plus an allowlist of three flags, recorded verbatim in `system.yaml` per `(workload, load point, GPU count)` and documented at the pinned version:
  - `--tensor-parallel-size` (equal to the serving profile's `gpu.count`);
  - `--max-model-len` (prompt tokens plus output tokens);
  - `--max-num-seqs` (equal to the batch size, `matched` load only).
  The validator rejects any other flag for `reference_role: serve`. Disallowed flags include offloading (`--cpu-offload-gb`, `--kv-offloading-*`), quantization overrides, memory-fraction tweaks, `--language-model-only` (which zeroes every modality limit at [config/multimodal.py L304 to L306](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/config/multimodal.py#L304-L306), altering memory profiling in a way that differs from normal multimodal serving; Q4), and `--skip-tokenizer-init` (the engine runs its full default initialization using Meta's own `tokenizer_config.json`; Q7). If the engine cannot load without a disallowed flag, the failure is recorded and escalated to the owner rather than admitting flags without an RFC amendment.
  - The engine is launched strictly from these allowlisted flags (Q8: `vllm serve MODEL <flags>`, or alternatively `LLM(model=..., tensor_parallel_size=..., max_model_len=..., max_num_seqs=...)`), never by dumping every `EngineArgs` field. Passing all `EngineArgs` fields to `LLM` (as the adapter did before this amendment) matches neither `LLM`'s nor the server's defaults, since `LLM.__init__` only sets `disable_log_stats=True` when that key is omitted ([entrypoints/llm.py L226 to L227](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/entrypoints/llm.py#L226-L227)).
  - The adapter logs the exact engine command in `/io/commands.jsonl`, and the runner verifies that it ends with the `engine_args` from `system.yaml` at the run's commit. The adapter also captures the engine's start-up resolved-configuration log line. A CPU test checks that this resolved configuration differs from a stored default dump (for the same pinned version, interface, and usage context) only in the allowlisted fields and fields defined by the serving record's model files (model path, served name, `dtype`, `quantization`, and `quantization_config`), with `quantization` matching the release's `config.json` (`quantization_config.quant_method`, or none). Until the first live capture replaces it, the stored default is a shape fixture and is not enforced on live runs (Q9).
  - The adapter records the observed runtime details (`engine_observed` in `commands.jsonl`, copied to `engine.observed` in the manifest): installed version, the image ENV's `VLLM_BUILD_COMMIT`, and the info-level batched-token limit ("Chunked prefill is enabled with max_num_batched_tokens=N", [config/scheduler.py L307](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/config/scheduler.py#L307)). Because the pinned version logs resolved `max_num_seqs` only at debug level ([engine/arg_utils.py L3182](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/engine/arg_utils.py#L3182)) and changing the log level via environment variable is disallowed by SRV-3, the high-load limit of 1,024 sequences is verified from source rather than logs. Since the default batched-token limit is `min(usage_context_default, max_num_seqs × max_model_len)` (L3167 to L3170), a matched batch-1 run uses 1,025 rather than 8,192, and the conditions line prints the observed value for each load point.
  - Environment variables. The adapter records all `VLLM_*`, `NCCL_*`, `CUDA_*`, and `TORCH_*` variables visible to the engine process in `commands.jsonl`, and rejects the job (`config`, before building the engine) if any variable is not present in the pinned image's own `ENV` (read from the image config by digest and logged in `inputs.json`), apart from harness binding variables (`CUDA_VISIBLE_DEVICES`, `CUDA_DEVICE_ORDER`) allowlisted in the adapter. The development install enforces the same rule. As FlashProve's RES-13 notes, flags like `VLLM_USE_V2_MODEL_RUNNER=1` alter baseline throughput and effectively act as engine options.
- SRV-4. Outputs (`outputs.json` containing request index, batch, and token IDs) are archived for auditing, but serving outputs are never compared against proving system outputs.
- SRV-5. Recorded metrics include `rate_<S>`, `seconds_per_token_<S>`, `gpu_seconds_per_token_<S>`, and GPU/host resource telemetry per RFC-0011 (aggregated across all bound GPUs), feeding D-OVERHEAD-S, D-OVERHEAD-HIGH-S, and D-OVERHEAD-WARM (RFC-0004). For `ref-serve`, `prove.session` (RFC-0004 §Timing scopes) spans the entire `prove` call from before `vllm serve` launches (preceded only by file checks) through the final request's output release, covering process start-up, weight loading into GPU memory, compilation, CUDA graph capture, and inference. Every run records `prove_session_seconds` and `gpu_seconds_per_token_prove.session`. D-OVERHEAD-WARM divides the prover's session figure by the matched serving `gpu_seconds_per_token_prove.steady` figure for warm serving (RFC-0004 INV-DERIVE-11).
- SRV-6. Production serving specification:
  - **Engine.** vLLM selected by Q1 (v0.32.0 as of 2026-11-04 and still current on 2026-11-09, when GitHub Releases listed v0.32.0 from 2026-10-18 as the newest release and v0.33.0rc3 as a release candidate; image `docker.io/vllm/vllm-openai@sha256:befccf0e7e4089aa23926bb6f887a85c0d46c2a99e6de5c5ffdf5cb7957c5b34`), running with defaults via the Q8 interface (the OpenAI-compatible HTTP server `vllm serve`, usage context `OPENAI_API_SERVER`, matching typical provider deployments). Because server defaults differ from the Python `LLM` class (8,192 vs 16,384 batched tokens on an H200, [engine/arg_utils.py L2933 to L2942](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/engine/arg_utils.py#L2933-L2942)), the chosen interface is always printed in the conditions line. FlashProve's RES-13 at `9e2bdd8` ([limits-all-rows.tsv](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/docs/limits-all-rows.tsv)) compares the HTTP server against the Python interface "with tuned settings" and notes that "the two differ in more than the interface"; since it does not isolate the interface as the cause of the gap, it is not cited to justify either choice.
  - **Weights.** The model publisher's own release at the precision fixed per model by amendment. For future models, the rule selects the release the publisher designates for serving, falling back to its original release, always quoted and linked from publisher documentation or marked "not stated" where silent. The v0.1 selections are:
    - Llama 4 Maverick: Meta's FP8 release, `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` at `94125d2bd83076b21eed33119525e29eaf3894f4`. Meta's model card at that revision (§Quantization, [README.md](https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8/blob/94125d2bd83076b21eed33119525e29eaf3894f4/README.md)) states: "the Llama 4 Maverick model is released as both BF16 and FP8 quantized weights. The FP8 quantized weights fit on a single H100 DGX host while still maintaining quality." Because the card does not explicitly use the word "serving", designating FP8 is the owner's decision based on that text.
    - Llama 3.1 8B Instruct: Meta's release, `meta-llama/Llama-3.1-8B-Instruct` at `0e9e39f249a16976918f6564b8830bc894c89659`, in BF16 (the safetensors dtype; the model card example loads it in `torch.bfloat16`, [README.md](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/blob/0e9e39f249a16976918f6564b8830bc894c89659/README.md)). Designated serving precision: not stated.
    - Mirror links in serving records supply files only and never serve as authority for precision choices.
    - Files are fetched from an ungated mirror where every pinned file is byte-identical to the publisher's release at that revision, pinned in a serving record `workloads/serving/<id>.yaml` (`serving-model/1`, RFC-0012) listing source repository, revision, and per-file path, SHA-256, byte length, and publisher git blob ID. Identity verification follows SM-1 to SM-3 (RFC-0014 §Model fetch). Each serving record lists its workloads as the sole mapping; the loader verifies that every listed workload exists and references a serve-role system, that no workload appears in two records, that every serve-role workload belongs to one record, and that `vocab_size` matches the workload.
    - Production serving always runs the release's native precision with no substitutions; PM-0 through PM-4 apply exclusively to `ref-recompute`.
  - **Placement.** All weights reside in GPU memory, tensor-parallel across the smallest GPU count on a serving profile of the proving system's GPU model (RFC-0006 R6) that holds both the weights and the matched load's KV cache (`batch × max_model_len`).
    - Planning estimates (`systems/ref-serve/sizing.py`, grade projected, never published) only choose the starting GPU count: the smallest count dividing the model's attention and KV head counts whose combined device memory exceeds total weight bytes. Live loading confirms placement: the adapter fails with `resource` if the engine reports insufficient KV-cache tokens for the matched load (logging the KV-capacity line as evidence) or exits at start-up with an out-of-memory error (PyTorch's `OutOfMemoryError`, or vLLM's "No available memory for the cache blocks" or "larger than the available KV cache memory").
    - A larger GPU count is attempted only after `resource` failures at count `n` with recorded KV-capacity or OOM evidence; `adapter` failures are bugs to fix and rerun rather than grounds to add GPUs. Releases join the smallest GPU count with a joinable run (RFC-0004 INV-DERIVE-2); that placement governs both load points, while earlier smaller-count failures remain archived.
  - **Scope.** `prove.steady` is the headline scope because engine start-up, compilation, and CUDA graph capture finish before the first batch's last release (RFC-0004 INV-SCOPE-5). `prove.session` is also recorded (SRV-5). For systems without a steady scope (SASH), the headline is D-OVERHEAD-WARM, dividing the prover's session figure by this row's steady scope and displaying both scopes (RFC-0004 INV-DERIVE-11).
- SRV-7. Each workload names at most one system with `reference_role: serve` (`ref-serve`), enforced by the loader (`config`). CI workloads name none. Tables label the row `ref-serve` alongside the engine, GPU count, and serving release.
- SRV-8. Prompts. A production-serving job replays prompts from a recorded run of the proving system it pairs with via `iproofs run --system ref-serve --workload W --profile P --load matched|high --prompts-from RUN_DIR`. Both runs process the exact same token set only when batch size and batch count match.
  - When the serving run processes more batches (high load or a lengthened matched run under SRV-1), `corpus-window/1` draws `B × batches` offsets sequentially from the same seed so the opening `prompts.count` prompts match the source run exactly. The manifest records `prompt_prefix_digest` over those opening prompts, and the runner requires it to equal the source run's `prompt_set_digest`.
  - Any difference in prompt counts is stated explicitly in the conditions line using each manifest's `prompt_count_run`, for example: "at high load: the prover's 120 prompts plus 5,000 further windows of the same seeded generator" (the counts for `fp-maverick-w1024-b24`, where `5 × 1,024 = 5,120` serving prompts; workload facts, not results).
  - Development runs may use a fresh seed (`prompts_from` null), but never join D-OVERHEAD-S.
- SRV-9. Precision note. Because serving precision reflects the publisher's release rather than the proved precision, every page displaying overhead prints the precision note from RFC-0004 INV-DERIVE-9 beside it.
- SRV-10. Stored attempts. Earlier `ref-serve` runs in `results/v0.1` used the prior definition (plain serving on the system rows' profile `prover-h100-hosted` using workload files), comprising 12 completed SASH-workload runs (FP8 substituted at load, PM-4) and 8 failed Maverick runs (6 `config` failures at resolve, plus 2 `adapter` failures where vLLM rejected the GGUF folder with "Unrecognized model ... Should have a `model_type` key in its config.json").
  - These runs remain untouched as recorded (APP-1). Because they ran on `prover-h100-hosted` rather than a serving profile, they do not join any overhead calculation (RFC-0004 INV-DERIVE-2 (c)).
  - Releases list them among reference configurations labelled "plain serving on the system rows' profile (RFC-0015 before 2026-11-09)".

### Recompute (`ref-recompute`)

Recompute models a verifier that holds the model weights and checks claimed outputs directly by running the forward pass itself.

- RC-1. Recompute jobs reuse the exact prompt seeds from a named system run via `iproofs run --system ref-recompute --workload W --profile P --prompts-from RUN_DIR`, recording the source run ID in the manifest so prompts match request for request. Because every run stores each proof's `request_index` and `claimed_output` in `run.json` `proofs[]`, the harness writes those claimed outputs to `/io/claimed.jsonl` (`claims_file` in `job.json`, one token-ID array per request in request order) and passes it to `prove`.
- RC-2. Batch size is always 1 regardless of the workload's batch size, reflecting single-request verification and avoiding batch-composition effects on greedy tie-breaks.
- RC-3. Teacher-forced check: for each request, the engine executes a single forward pass over the prompt concatenated with the system's claimed output tokens and records the argmax token at every claimed output position (or the single position following the window for next-token workloads). Each position is marked `agree` if the argmax equals the claimed token, and `disagree` otherwise. Tie-breaking follows the pinned engine's native argmax rule, documented in the adapter README with a link to the pinned upstream documentation or source.
- RC-4. Each request writes `/io/proofs/<request_id>/outputs.json` containing per-position argmax tokens, timed under REF-1. Recompute cost is reported as D-SPT-prove.steady and D-COST-1K-prove.steady for the `ref-recompute` configuration: time and cost per token for a warm verifier holding the weights on `prover-h100`.
- RC-5. The harness compares argmax tokens against claimed tokens, writes `{agree, disagree, first_disagreement}` into `run.json` `proofs[].agreement`, and aggregates totals into `agreement_positions` and `disagreement_positions` (measured by the harness, source `run.json#/proofs`). The release index reports agreement per `(system configuration, ref-recompute configuration)` pair:

| Metric id | Unit | Scope | Grade | Formula |
|---|---|---|---|---|
| `agreement_positions` | count | null | derived | positions with `agree` |
| `disagreement_positions` | count | null | derived | positions with `disagree` |
| `first_disagreement` | count | null | derived | per request, index of the first disagreeing output position, or null |
| `agreement_rate` | ratio | null | derived | D-AGREE: `agreement_positions / (agreement_positions + disagreement_positions)` |

- RC-6. INV-REF-1: agreement never alters a verdict, control outcome, or evidence tier. A proof accepted by its verifier remains accepted even if recompute disagrees. Expected divergence belongs in the claim card's `quality_gap` and `residual` fields (RFC-0002), and the site displays the agreement rate beside them.
- RC-7. For multi-token continuations (SASH-style workloads), positions after the first disagreement continue under teacher forcing (feeding the claimed prefix rather than the recomputed tokens) so every position is evaluated against the same claimed context.

### Precision matching

PM-0 through PM-4 govern `ref-recompute`. Production serving always uses the publisher's release precision directly (SRV-6).

- PM-0. Reference runs load only the workload's pinned model files (RFC-0003), never a separate pre-quantized checkpoint, ensuring they evaluate the exact pinned weights.
- PM-1. When the pinned engine documents support for the workload's `precision.served` (RFC-0003) on the profile's GPU using the pinned files, recompute runs at that precision.
- PM-2. Otherwise, recompute steps up to the nearest supported scheme in this order: same weight bit width with a higher activation bit width, then the next higher weight bit width with the lowest supported activation bit width. Substitutions are declared in `system.yaml` `precision_substitution` with a reason and an engine documentation link, and every resulting metric carries `quality.precision_substituted: true` (RFC-0012).
- PM-4. If the engine supports the workload's scheme only via a separate checkpoint (disallowed by PM-0), recompute first uses the same bit widths in another numeric format quantized at load time from the pinned files (for instance, FP8 W8A8 in place of integer W8A8) before falling back to PM-2's order. This counts as a declared substitution like any other.
- PM-3. D-OVERHEAD-S over a substituted reference is still computed and flagged rather than hidden so readers see both the ratio and the substitution warning. Substituting a lower bit width than the workload is never permitted because it would artificially speed up the reference.

### Feasibility on the profile

For recompute, the runner attempts each job on the system rows' profile using only documented engine options. For production serving, the runner starts on the serving profile at the GPU count selected by SRV-6 sizing and steps up to a larger GPU count only after `resource` failures backed by KV-capacity or out-of-memory logs (declaring the larger profile at that point under RFC-0006 R6). An `adapter` failure never justifies scaling up GPUs; it is fixed as a bug and rerun. All failures are recorded normally (RFC-0010), and any metric lacking a successful run is null with `missing_input` or `step_failed`. The `not_measurable_on_profile` classification (NM-1) is deferred during the research phase.

RISK: Meta's FP8 release of Maverick totals 416.8 GB of safetensors (Hub listing read 2026-11-09, grade external, tier reported). Planning arithmetic (grade projected) starts at 4 H200 GPUs and skips 2; only `resource` failures at 4 GPUs with KV-capacity evidence advance to 8 GPUs.

### Failure modes

| Failure | Response |
|---|---|
| Engine cannot load the model or precision | job failed (`adapter` or `resource`); see §Feasibility on the profile |
| `--prompts-from` run missing, failed, or from another workload version | `config` error before any step |
| Claimed outputs missing in the source run | `config` error; recompute requires a successful source run |
| Engine option not documented at the pinned version | fails policy review; the adapter README links upstream docs for every option |
| Precision substitution to fewer bits | validator rejects `system.yaml` (PM-3) |
| Serve-role `engine_args` includes an option outside SRV-3 | validator rejects `system.yaml` |
| Bound GPU count differs from profile `gpu.count` or `--tensor-parallel-size` | `config` error before `info` |
| Engine KV cache falls short of the matched load | job fails `resource`; try a larger GPU count (SRV-6) |
| A request returns fewer or more tokens than `output_tokens` | job fails `adapter` |
| A serving file's byte size or blob ID differs from the serving record | `fetch-model` fails `config`; no job runs |
| `--prompts-from` targets another workload version, or high-load prefix digest mismatches | `config` error before any step |
| A workload lists two serve-role systems | `config` error at load (SRV-7) |
| Any `VLLM_*`, `NCCL_*`, `CUDA_*`, or `TORCH_*` variable absent from image `ENV` (and not a harness binding variable) | `config` error before engine launch |
| Job attempts a larger GPU count when a smaller count already succeeded for that workload | `config` error before any step |
| Release watcher falls back to polling on a serving run | job fails `environment` |
| Production-serving row runs on a profile that does not pair with the system row's profile | D-OVERHEAD-S is null with `not_applicable` (RFC-0004 INV-DERIVE-2) |

## Alternatives Considered

- **Use published upstream engine benchmarks.** Attractive because it uses no GPU hours, but rejected because published benchmarks differ in hardware, request shapes, and timing scopes; overhead ratios require matched hardware and token accounting.
- **Use an eager Hugging Face Transformers forward pass.** Simple to implement, but rejected for serving because eager execution dramatically understates real serving throughput and would artificially shrink overhead factors. Retained as a future fallback for recompute via a later RFC if a serving engine cannot run a required precision.
- **Run recompute through `verify` with one container invocation per request.** Considered because recompute acts as a verifier, but rejected because reloading weights on every call would mostly measure model load time rather than per-request verification cost; RC-4 measures warm cost while keeping start-up visible in `prove.session`.
- **Run plain serving on the proving profile with weights partially offloaded to host memory (`llama.cpp`, SRV-6 of 2026-11-08).** Rejected by the owner on 2026-11-09 because providers do not deploy models with host offloading, and host-to-GPU transfers would distort the production serving baseline.
- **Run vLLM directly on the prover's GGUF files.** Rejected because the vLLM GGUF plugin does not list Llama 4 among its tested families, no provider serves Maverick from GGUF in production, and stored attempts failed (SRV-10).
- **Divide raw serving throughput by proving throughput across different GPU counts.** Rejected because dividing a 4-GPU rate by a 1-GPU rate ignores hardware scaling; GPU-seconds per token (RFC-0004 INV-DERIVE-8) properly accounts for GPU count.
- **Adopt FlashProve's published overhead multiple directly.** Rejected as a primary metric because external numbers are never mixed with benchmark runs (INV-MAP-1). Recording it as an `external` quantity in `systems/flashprove/external.yaml` is deferred.
- **Allow `--language-model-only` and `--skip-tokenizer-init`.** Rejected under SRV-3: neither is a workload-shape requirement. They were workarounds for mirrors missing Meta's `tokenizer_config.json`, and `--language-model-only` alters multimodal memory profiling.
- **Run recompute on the CPU-only verifier profile.** Considered because proving verifiers are timed there, but rejected because running an 8B or ~400B model on 8 CPUs and 32 GiB RAM is not a realistic verifier deployment; recompute runs on `prover-h100` and is labelled accordingly.
- **Compare free-running greedy generations instead of teacher forcing.** Simpler, but rejected because once outputs diverge at one token, subsequent prefixes differ and later positions can no longer be compared; teacher forcing tests every claimed position against the same prefix.
- **Create separate workload files for reference rows.** Rejected because duplicating workload definitions invites drift in shapes or prompts; sharing workload IDs makes INV-DERIVE-2 mechanically verifiable.

## Drawbacks

- "Production serving with the engine's defaults" does not represent the theoretical ceiling of tuned serving throughput, so overhead factors are relative to a clearly documented default configuration rather than a physical limit.
- Serving engines evolve quickly; upgrading a pinned engine can shift overhead factors across the board, which is why versions are pinned per release and different engine pins are never pooled (RFC-0004 INV-DERIVE-2 (e)).
- Overhead ratios combine the cost of proving with any precision difference chosen by the model publisher (SRV-9).
- Multi-GPU serving profiles carry more GPUs and host resources than single-GPU prover profiles, yet only GPU-seconds are counted (RFC-0006 C5).
- Engine defaults vary between interfaces and usage contexts, so the chosen interface (Q8) must always appear alongside the figure.
- High-load runs and lengthened matched sessions process more prompts than the proving run (SRV-8); only the prover's prompt prefix is shared.

## Migration / Rollout

An earlier draft of RFC-0003 defined `ref-serve-*` and `ref-recompute-*` as separate workload IDs; this RFC replaces them with reference systems running on existing workload IDs (matching the revised RFC-0003). Schema additions (RFC-0012): `kind`, `reference_role`, `engine`, `precision_used`, and `precision_substitution` in `system/1`; `prompts_from` in `manifest/1`; `quality.precision_substituted` on quantities; and the agreement block in the release index.

The 2026-11-08 amendment (using llama.cpp v0.9.0 on the system profile for Maverick plain serving) was superseded on 2026-11-09 before its adapter was ever merged.

Amendment of 2026-11-09: production serving replaces plain serving. SRV-1 through SRV-10 replace the earlier SRV rules, Q2 is amended, PM rules apply only to `ref-recompute`, and Maverick workloads continue naming `ref-serve`. Schema additions (RFC-0012): `serving-model/1`; `load_point`, `gpus`, `batch_size`, and `batches_per_session_run` in `system/1` workloads; `workload.load_point`, `workload.batch_size_run`, `workload.batches_per_session_run`, `workload.prompt_count_run`, `workload.prompt_prefix_digest`, `workload.steady_rule`, `engine` (with `engine.observed`), and `serving_model` in `manifest/1`; and `engine.commit` in `system/1`. Previously stored `ref-serve` runs remain unchanged (SRV-10). Publishing the first D-OVERHEAD-S requires an H200 driver pin (RFC-0006 Q5 for hosted, issue #77 for Docker), a public digest-pinned rebuild of `ref-serve`, and conforming prover rows on the paired profile; until then, serving runs remain development runs (POL-4).

Amendment of 2026-11-09 (with RFC-0004 INV-DERIVE-10): SRV-5 defines `prove.session` for `ref-serve` as engine start to last token. No new recording logic is needed because every production-serving `ref-serve` run already records `prove_session_seconds` and `gpu_seconds_per_token_prove.session`.

Amendment of 2026-11-09 (with RFC-0004 INV-DERIVE-11): single-batch matched serving sessions are sized from sizing captures (SRV-1, `--sizing-batches N`, manifest `workload.sizing_capture`, RFC-0012, Q10), and SRV-5/SRV-6 establish D-OVERHEAD-WARM as the headline for systems lacking a steady scope. Existing stored runs are untouched; the development capture of `sash-l31-8b-c1024` remains a single-request run that cannot size a session.

## Testing Strategy

CPU-only tests:

- TC-REF-SKIP: running a fake reference system (`systems/fake` with a `kind: reference` fixture) records `commit` and `verify` as `skipped`, sets `whole_wall` and commit metrics to null (`not_applicable`), and records steady and session metrics.
- TC-REF-TOKENS: fake reference releases on a 1,024-position `window` workload count 1,024 tokens per request.
- TC-AGREE-FIXTURE: hand-computed fixture with 3 requests and 4-token claimed outputs disagreeing at 1 position in request 2 verifies `agreement_positions` = 11, `disagreement_positions` = 1, `first_disagreement` = `[null, index, null]`, and `agreement_rate` = 11/12.
- TC-AGREE-NO-VERDICT-CHANGE: a disagreeing recompute run leaves source-run verdicts and tiers untouched in the release index (INV-REF-1).
- TC-PROMPTS-FROM: recompute reproduces the exact prompt digest of its source run and fails with `config` if pointed at a different workload version.
- TC-PRECISION-SUBST: `system.yaml` rejects lower-bit substitutions, accepts higher-bit substitutions, and marks every resulting quantity with `precision_substituted: true`.
- TC-OVERHEAD-JOIN: superseded by RFC-0004 tests TC-OVERHEAD-GSPT, -PAIR-PROFILE, -FEWEST, -PROMPTS, -SASH, and -DIGEST.

GPU host and adapter tests:

- GH-REF-SERVE-L31: `ref-serve` on `sash-l31-8b-c1024` using Meta's BF16 release at TP1 on `serving-h200x1-hosted` across three repetitions, schema-valid with non-null `rate_prove.steady`.
- GH-REF-RECOMPUTE-L31: `ref-recompute` with `--prompts-from` pointing to a SASH run, producing a populated agreement block.
- GH-REF-SERVE-MAVERICK-FP8: `ref-serve` on `fp-maverick-w1024-b24` using Meta's FP8 release at TP4 on `serving-h200x4-hosted` for both load points (advancing to TP8 only after TP4 fails `resource`), supplying captures for CPU tests.
- TC-SRV-7 (CPU, with adapter): workloads naming two `reference_role: serve` systems fail `config` at load, workloads naming none (`fake-tiny-ci`) load cleanly, and releases join D-OVERHEAD-S to the named serving system.
- TC-SRV-ALLOWLIST: serve-role entries containing `--cpu-offload-gb`, `--quantization`, `--gpu-memory-utilization`, `--language-model-only`, or `--skip-tokenizer-init` fail validation.
- TC-SRV-PROMPT-PREFIX: high-load runs match the source run's `prompt_set_digest` across their first `prompts.count` prompts and fail `config` on mismatch.
- TC-SRV-GPU-COUNT: TP4 with only one visible GPU fails `config` before building the engine.
- TC-SRV-ENV: setting `VLLM_ATTENTION_BACKEND` outside the image's `ENV` fails `config` before building the engine.
- TC-SRV-RESOLVED: the resolved configuration differs from the stored default dump only in allowlisted and record-owned fields; unexpected quantization fails, while FP8 `compressed-tensors` for Maverick passes.
- TC-SRV-SHORT (`test_cross_rows.py`): a matched serving run carrying the "steady scope under 60 s" warning produces null (`missing_input`).
- TC-SRV-HIGH-PLACEMENT (`test_cross_rows.py`): matched at TP4 paired with high load at TP8 yields null (`not_applicable`) for D-OVERHEAD-HIGH-S.
- TC-SRV-SESSION (`test_serving_runs.py`, `test_cross_rows.py`): a fake serving job records `gpu_seconds_per_token_prove.session` equal to D-SPT multiplied by GPU count.
- TC-SRV-OOM (`test_ref_serve.py`): an engine exiting on start-up with PyTorch's out-of-memory error fails `resource` with that line as evidence, while other exits remain `adapter`.
- TC-SRV-SIZE (`test_session_size.py`): verifies the sizing formula against hand-computed cases including the first two captures: the `fp-maverick-w1024-b24` TP4 capture (5 batches of 24, `prove_steady_seconds` 2.260716798 s, measured, development run) yields 214; the single-request `sash-l31-8b-c1024` TP1 capture and high-load captures fail `config`; counts below the workload minimum clamp upward; and exact boundaries do not round up.
- TC-SRV-SIZE-RUN (`test_serving_runs.py`, `test_session_size.py`, `test_cli.py`, `test_hf_job.py`, `test_cross_rows.py`): with a null matched count, `--sizing-batches 4` replaying a fake run serves `4 × 2 = 8` prompts whose first 6 match the source digest, records `sizing_capture: true` and the warning, and lets `size-session` divide `prove_steady_seconds` by 3 steady batches; a `sash-l31-8b-c1024` fixture (50 batches of 1, `prove_steady_seconds` 24.5 s, or 0.5 s per batch) yields 240 steady batches and a total of 241; CLI rejects counts below 2, high load, already-sized entries, and non-serving systems with `config` before any step; `hf-job.sh` `sizing=50` with `from=` emits `--sizing-batches 50 --prompts-from ...`; and sizing captures never enter overhead (`missing_input`).
- TC-SRV-LENGTHEN-REPLAY (`test_serving_runs.py`, `test_ref_serve.py`): a lengthened matched entry replaying a source run serves `batch_size × batches_per_session_run` prompts whose opening `prompts.count` prompts match the source digest (`prompt_prefix_digest`), and the adapter executes every batch listed in the job.

## Decisions

- Q1. The serving engine is the newest vLLM release on the date the `systems/ref-serve` pull request opened (2026-11-04): vLLM v0.32.0 (released 2026-10-18; v0.33.0rc3 was a release candidate), image `docker.io/vllm/vllm-openai@sha256:befccf0e7e4089aa23926bb6f887a85c0d46c2a99e6de5c5ffdf5cb7957c5b34`, source commit `5df63a7203cdb9328d824a27b682e77c7b9928be`. Its [supported models](https://github.com/vllm-project/vllm/blob/v0.32.0/docs/models/supported_models.md) page lists `LlamaForCausalLM` (Llama 3.1) and `Llama4ForConditionalGeneration` (Llama 4), and its [quantization](https://github.com/vllm-project/vllm/blob/v0.32.0/docs/features/quantization/README.md) documentation covers INT8 W8A8 and FP8 W8A8 on Hopper. Under the earlier recompute/plain-serving setup: SASH workloads use FP8 W8A8 quantized at load from pinned files (PM-4) because INT8 W8A8 requires an llm-compressor checkpoint ([int8_w8a8.md](https://github.com/vllm-project/vllm/blob/v0.32.0/docs/features/quantization/llm_compressor/int8_w8a8.md), [online.md](https://github.com/vllm-project/vllm/blob/v0.32.0/docs/features/quantization/online.md)), while Maverick workloads load pinned GGUF files via `vllm-gguf-plugin` v0.0.5 ([gguf.md](https://github.com/vllm-project/vllm/blob/v0.32.0/docs/features/quantization/gguf.md)), which does not list Llama 4 among tested families so NM-1 was expected. Full details live in [`systems/ref-serve/README.md`](../systems/ref-serve/README.md).
- Q2. Multi-GPU serving profiles are admitted for production serving only (RFC-0006 R6), with overhead measured in GPU-seconds per token (RFC-0004 INV-DERIVE-8).
- Q3. Recompute extracts teacher-forced argmax tokens via prompt log-probabilities by submitting prompt plus claimed output as one token-ID sequence with `SamplingParams(prompt_logprobs=1, max_tokens=1)` ([`sampling_params.py`](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/sampling_params.py#L347-L349)). At each position, vLLM returns the top-1 token from `torch.topk` over log-probabilities ([`Sampler.gather_logprobs`](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/v1/sample/sampler.py#L312-L337)), breaking ties in `torch.topk` order with no engine source edits.
- Q4. `--language-model-only` is not a shape requirement: it zeroes all modality limits, altering Maverick's memory profiling in a way that does not match multimodal serving, and is disallowed under SRV-3.
- Q5. High-load batch size equals the engine's default maximum sequence limit (1,024 on an H200).
- Q6. Release runs use the public pinned `ref-serve` image on GHCR rather than the development install; while GHCR rejects anonymous pulls for it, runs fall back to the development install. On 2026-11-09, anonymous token requests returned `UNAUTHORIZED` for `ref-serve` and `ref-recompute` while succeeding for `sash` and `flashprove`.
- Q7. Each serving record pins Meta's own `tokenizer_config.json` (`source: publisher`) because no checked ungated mirror held Meta's exact bytes for either model; a read token from an account that accepted Meta's licence is passed solely to `iproofs serving pin` and `iproofs fetch-model --serving`, and `--skip-tokenizer-init` is never admitted. Meta's `special_tokens_map.json` for Maverick FP8 (blob `d2b717ab`, identical in Meta's and RedHatAI's repos) contains invalid JSON due to a trailing comma before its closing brace (inspected 2026-11-09). Without `tokenizer_config.json`, the pinned image's `transformers` reads that broken file and crashes tokenizer loading, as reproduced in the pinned `linux/arm64` image on 2026-11-09. The Maverick record omits `special_tokens_map.json` while keeping every pinned file byte-identical to Meta's; since prompts are submitted as token IDs, special tokens are never looked up by name. Development jobs validate tokenizer loading before downloading weights via `fetch-model --serving R --no-weights DIR` and `dev_install.py --tokenizer-check DIR`.
- Q9. The first live capture for each serving record and interface becomes its stored default configuration dump via pull request; afterward, the adapter compares every run's resolved configuration against that dump and rejects discrepancies with `config`. Prior to the first capture, SRV-3 tests use a typed shape fixture and live runs are not gated on it.
- Q8. Production serving runs through `vllm serve` with only allowlisted flags (`OPENAI_API_SERVER` usage context, matching provider deployments) rather than the Python `LLM` class (`LLM_CLASS`, which defaults to 16,384 rather than 8,192 batched tokens on an H200). Either way, the interface is stated in the conditions line. `systems/ref-serve/README.md` documents and links the completions API field returning output token IDs in v0.32.0.
- Q10. Single-batch matched workloads (such as SASH's single-request batch-1 workloads) are sized from a dedicated sizing capture (`--sizing-batches N`, SRV-1) that is flagged as a sizing run and excluded from overhead joins so `size-session` can read its steady window. Systems without a steady scope headline D-OVERHEAD-WARM, dividing by the lengthened serving session's steady scope so engine start-up never enters either the serving side or the ratio (RFC-0004 INV-DERIVE-11).

## References

- docs/PRD.md §6, §7.
- [RFC-0002](0002-claim-card.md) for `quality_gap` and `residual`; [RFC-0003](0003-workloads.md) for workload IDs, precision, and seeds; [RFC-0004](0004-metrics-timing-grades.md) for D-OVERHEAD-S, D-SPT, and INV-DERIVE-2; [RFC-0005](0005-adapter-contract.md) for the adapter contract; [RFC-0006](0006-reference-hardware-and-cost.md) for profiles; [RFC-0010](0010-harness-runner.md) for skipped steps; [RFC-0011](0011-measurement-and-sampling.md) for release timing.
- vLLM documentation at the pinned release (engine options, supported quantisation schemes).
- Meta's model cards at the pinned revisions ([Llama 4 Maverick FP8](https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8/blob/94125d2bd83076b21eed33119525e29eaf3894f4/README.md), [Llama 3.1 8B Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/blob/0e9e39f249a16976918f6564b8830bc894c89659/README.md)).
