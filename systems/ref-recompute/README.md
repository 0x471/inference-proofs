# ref-recompute

This adapter implements recomputation by a verifier that has access to the model weights ([RFC-0015 §Recompute](../../rfcs/0015-reference-rows.md#recompute-ref-recompute)). The pinned engine version, per-workload precision settings, and engine flags are documented in [`ref-serve`'s README, §Recompute](../ref-serve/README.md#recompute-ref-recompute). In particular, `ref-recompute` passes `--max-num-seqs 1` for every workload (RC-2) and sets `--max-model-len` to one token longer than the workload sequence, since the engine generates one extra token after the prompt and claimed output. While production serving (`ref-serve`, RFC-0015 SRV-6) uses different weights and flags, `ref-recompute` continues to follow the PM rules. Its image (`Dockerfile`) reuses `systems/ref-serve/entrypoint` paired with this directory's `system.yaml`.

## What `prove` does

- **Input:** The harness invokes `ref-recompute` only with `--prompts-from` pointing to a completed system run (RC-1). The source run's claimed outputs (from `proofs[]` in its `run.json`) are provided in `/io/claimed.jsonl` (`claims_file` in `job.json`), with one array of token IDs per request.
- **One request at a time** (RC-2), regardless of the workload's batch size.
- **Teacher-forced check** (RC-3, RC-7): Runs a single forward pass over the prompt plus the claimed output using `SamplingParams(prompt_logprobs=1, max_tokens=1)` ([`sampling_params.py`](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/sampling_params.py#L347-L349)). At each claimed position, the adapter records the rank-1 token from the returned prompt log-probabilities (the argmax). Because every position receives the claimed prefix, positions following a mismatch are still compared.
- **Ties** are broken by the engine: rank 1 is the first index returned by `torch.topk` over the log-probabilities ([`Sampler.gather_logprobs`](https://github.com/vllm-project/vllm/blob/v0.32.0/vllm/v1/sample/sampler.py#L312-L337)).
- **Release** (RC-4): Releases `/io/proofs/req-<i>/outputs.json` (containing `request_index` and `argmax`) for each request via atomic rename. The adapter does not judge agreement itself; instead, the harness compares the argmax tokens against the claimed outputs and records `agreement` per proof along with `agreement_positions` and `disagreement_positions` per run (RC-5). Agreement never alters a verdict (INV-REF-1).

## Tests

The tests in `tests/` run on CPU (INV-ADAPTER-9) against argmax tokens captured once on a GPU host (see `tests/fixtures/capture/` and its README).
