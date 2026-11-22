# ref-fidelity: the fidelity reference

This adapter implements the fidelity reference baseline defined in [RFC-0018 §Fidelity](../../rfcs/0018-level-1-ladder.md#fidelity) (FI-1, FI-2, FI-7): running each rung's 16-bit publisher release greedily in llama.cpp, constructing the quantized and damaged control models from it, and computing llama.cpp KL divergence for each control against the reference. It is a reference job rather than a ranked row. `iproofs fidelity run` executes it, and `iproofs fidelity score` (CPU-only) combines its outputs with the counted system sessions to produce `fidelity.json` (`harness/src/iproofs/fidelity.py`, schema `fidelity/1`).

## Engine

- Uses llama.cpp v0.9.0, the latest non-prerelease available on GitHub on 2026-11-10 (published 2026-11-04), pinned at commit `cd959bae99ff4bed22bef2604f45241c09bbb8c8` (targeted by the annotated tag `v0.9.0`). This matches the commit already tracked by `iproofs.gguf`. `inputs.lock` pins the SHA-256 of `git archive --format=tar HEAD`, which the image build verifies.
- Compiled from source in `Dockerfile` following upstream's [.devops/cuda.Dockerfile](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/.devops/cuda.Dockerfile) at the pinned commit: digest-pinned `nvidia/cuda:12.8.1-devel-ubuntu24.04`, `GGML_CUDA=ON`, `GGML_NATIVE=OFF`, and `--allow-shlib-undefined`. Adjustments relative to upstream's Dockerfile are limited to build scope: targeting compute capability 9.0 only (H200), linking static libraries, building only the three binaries this adapter invokes (`llama-server`, `llama-quantize`, `llama-perplexity`), and disabling the web UI and HTTPS (`LLAMA_BUILD_UI=OFF`, `LLAMA_USE_PREBUILT_UI=OFF` to prevent configure-time downloads, and `LLAMA_OPENSSL=OFF`).
- Python dependencies for GGUF conversion (`convert-requirements.txt`) come from upstream's `requirements/requirements-convert_hf_to_gguf.txt` at the pinned commit, resolved with hashes for CPython 3.12 on x86_64 Linux (CPU torch 2.11.0, transformers 4.57.6, numpy 2.2.6). The `gguf` package is loaded directly from `gguf-py` in the llama.cpp source tree.
- No upstream source files are modified (AGENTS.md rule 1).

## What a job does

Running `iproofs fidelity run --level L1 --rung R --release v1.0 --prompts-dir DIR --gpus 0,...` performs one `info` call followed by one `prove` call per model source, sharing a single `/io` directory:

| Call | `/models` | Builds and runs |
|---|---|---|
| `reference` | The rung's 16-bit release (from the serving record for the 8B rung, or `--reference-dir` for Maverick) | The reference model plus every control derived from it in the level spec |
| `other_model` | `--other-model-dir`, the smaller model from the same publisher | The `other_model` control |
| `file` (per `--row-gguf SYSTEM`) | The row's fetched and verified workload files | KL divergence only, evaluated on the model file committed by the system |

Each call runs through four stages:

1. **Convert** (FI-1): Runs `python3 convert_hf_to_gguf.py /models --outtype bf16 --outfile /io/work/reference.gguf` offline (`HF_HUB_OFFLINE=1`).
2. **Replies** (FI-1, FI-2): Starts `llama-server -m <file> --host 127.0.0.1 --port <free> -c <slots x 1,088> -np <slots> -ngl 999 --cache-ram 0 --no-webui` and submits one `/completion` request per prompt ([tools/server/README.md](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md)):
   - `prompt` receives the 512 token IDs directly (llama.cpp does not prepend a BOS token to token-ID prompts, per README §POST /completion).
   - `n_predict` requests the remaining token count with `return_tokens` enabled, reading the reply from `tokens`. If the server slightly overshoots `n_predict` to finish a multi-byte character (as documented in the README), the adapter truncates the reply at 512 tokens.
   - Greedy decoding uses `samplers: ["temperature"]`, `temperature: 0`, and `n_probs: 0` ([common/sampling.cpp L403 to L406](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/common/sampling.cpp#L403-L406)).
   - **End tokens** (RFC-0018 §Terms, Request): When greedy decoding selects an end-of-generation token, it must remain in the reply and generation must continue. We leave `ignore_eos` false because llama.cpp's `ignore_eos` biases every end token's logit to negative infinity ([server-schema.cpp L442 to L452](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/server-schema.cpp#L442-L452)), which would suppress the token instead. Instead, when the server stops on `stop_type: "eos"` with the end token at the tail of `tokens` ([server-context.cpp L2142 to L2145, L2254 to L2256](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/server-context.cpp#L2142-L2145)), `greedy_reply` sends the prompt plus generated tokens so far as a fresh request for the remaining count, repeating as needed. Each prompt's continuation count is logged under `continuations` in `status.json`. Stopping early for any other reason fails the control. Note that each continuation re-evaluates the extended prompt from an empty cache, so subsequent tokens can differ in edge cases from uninterrupted decoding.
   - `cache_prompt: false` and `--cache-ram 0` ensure every prompt starts from an empty cache.
   - `-ngl 999` places all layers on the visible GPUs using llama.cpp's default `--split-mode layer`.
   - We use `llama-server` rather than `llama-cli` or `llama-completion` because at this commit only the server accepts raw token IDs and returns token IDs directly (`return_tokens`), avoiding a text retokenization round trip.
   - `--slots` (default 1) sets `-np`. All replies for a given rung must use the same slot count; the `reference-2` honest control reruns the reference under identical settings.
3. **KL** (FI-7): Detokenizes the KL prompt windows via `/detokenize`, joins them with blank lines into `kl.txt`, and runs `llama-perplexity -m reference.gguf -f kl.txt -c 512 --chunks 64 --kl-divergence-base kl-base.kld` to save 16-bit base logits (retokenizing `kl.txt`). Each control and row file then runs `llama-perplexity -m <file> -c 512 --kl-divergence-base kl-base.kld --kl-divergence`. The recorded value is `Mean    KLD:` in nats per token over the second half of each 512-token chunk ([tools/perplexity/README.md](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/perplexity/README.md)). KL divergence is informational only and never gates a check.
4. **Cleanup:** Each control GGUF is deleted once its replies and KL pass finish, and `reference.gguf` is deleted at the end of the `reference` call.

### Controls (FI-2)

| Recipe | Built by |
|---|---|
| `rerun` | Reuses `reference.gguf` with a fresh server instance |
| `quantize` | `llama-quantize reference.gguf <id>.gguf <TYPE>` |
| `drop_blocks` | `drop_blocks.py reference.gguf <id>.gguf --every 4`, verified by reading back with the source tree's `gguf` package |
| `other_model` | Converted separately using step 1 |

`drop_blocks.py` drops one quarter of the transformer blocks, renumbers the remaining blocks, updates `<arch>.block_count`, and filters per-block metadata arrays. For models with interleaved mixture-of-experts blocks (`<arch>.interleave_moe_layer_step` `s > 1`, such as `s = 2` on Llama 4 Maverick), blocks are removed in contiguous groups of `s` because llama.cpp identifies MoE blocks whenever `(i + 1)` is divisible by `s` ([src/models/llama4.cpp L62](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/src/models/llama4.cpp#L62)), so removing a single block would make the model unloadable. This drops blocks 3, 7, ..., 31 on Llama 3.1 8B (8 of 32) and pairs (6, 7), (14, 15), ..., (46, 47) on Maverick (12 of 48). Because `drop_blocks.py` uses only the Python standard library, its CPU tests require no llama.cpp build.

### Records

Under `/io`, the container writes `fidelity/replies/<id>.jsonl` (one reply per line in prompt order, with `reference.jsonl` for FI-1), `fidelity/kl/<id>.log`, `fidelity/logs/`, `fidelity/status.json` (tracking each call's status, control outcome, and continuation counts; failed controls record their cause without aborting remaining controls), and `commands.jsonl`. `iproofs fidelity run` copies these artifacts to `results/<release>/fidelity/<rung>/` (redacting host paths from logs) and writes `fidelity-run.json` (schema `fidelity-run/1`) with the level digest, engine commit and image, adapter and harness commits, prompt digests, GPU list, slot count, reference file SHA-256s, and each call's exit code, last lines, and timing phases.

## Teacher-forced pass (RFC-0018 FI-10 to FI-13)

When `teacher_forced` is set in the job, the adapter builds the same model files but skips free generation, instead scoring each prompt concatenated with the stored reference reply one position at a time. Because llama.cpp at the pinned commit has no CLI utility that outputs logits for raw token IDs (`llama-perplexity` operates on text, which can retokenize differently), this pass uses `llama-server` as documented in its [README](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md). It sends one `/completion` request per reply position with the prefix token IDs up to that point, `n_predict: 1`, greedy sampler settings, `cache_prompt: true`, and a pinned `id_slot`. As a result, the 512-token prompt is evaluated once as a batch and each subsequent position advances by a single token, matching greedy decoding. The returned token (`tokens`) gives the model's top choice, and setting `n_probs: 256` returns "the probabilities of top N tokens for each generated token", computed "via a simple softmax of the logits without considering any other sampler settings".

One server quirk at the pinned commit: `llama-server` omits the top-N probability list whenever a generated token ends mid-UTF-8 character ([server-context.cpp L2149-L2177](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/server-context.cpp#L2149-L2177), where `add_token` fires only on complete characters). The top token itself is still returned; affected positions are tallied in `positions_without_list` and excluded from that engine's KL calculation (FI-12).

Outputs are written to `/io/fidelity/teacher-forced/top/<id>.jsonl` and `raw/<id>/<prompt>.topk`. No KL binary runs and no reply files are written in this mode.

On Llama 3.1 8B (1 H200, 1 slot, `results/v1.0/teacher-forced/llama-3.1-8b/run-llama.cpp.json`, n = 1 run), scoring 15 prompts (7,680 positions with top-256 lists) took 73 to 104 s including control conversion and loading, or roughly 9 ms per position for the reference. Only 1 position out of 61,440 lacked a probability list (in `drop_blocks`). Both the reference pass and its rerun matched the stored reference reply at every position, confirming single-slot determinism.

On Llama 4 Maverick (4 H200, 16 slots, Q8_0 and Q4_K_M controls split into three 120-prompt runs each, `results/v1.0/teacher-forced/llama-4-maverick/run-controls-*.json`), throughput dropped to 6.7 positions/s (2.5 s per request), meaning 61,440 positions took about 2 h 35 min per run after a 9 to 20 min build and load. Server logs showed 6 prompt tokens being re-evaluated on every request at 1.5 to 2.5 s each, even though the same server evaluated a 512-token prompt at 347 tokens/s. By comparison, Llama 3.1 8B evaluated 1 token per request (5 ms at 1 slot; 26 ms at 16 slots, with or without `GGML_CUDA_DISABLE_GRAPHS=1`, n = 1 run each, 2026-11-14).

A diagnostic probe on 2026-11-14 (Q4_K_M on 4 H200, 16 slots, 16 prompts × 10 to 12 positions, manual server instance) identified the cause: at this commit, llama.cpp assigns Maverick a sliding-window attention (SWA) cache that cannot evict just its final token, preventing single-token incremental updates:

| Server option | Prompt tokens evaluated per request | Request, median | Positions per second |
|---|---|---|---|
| default | 6 | 1,543 ms | 10.4 |
| `--ctx-checkpoints 0` | 519 to 521 (the whole prompt again) | 975 ms | 15.6 |
| `--swa-full` | 1 | 90 ms | 168 |

`--swa-full` is documented in [tools/server/README.md](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/tools/server/README.md) as "use full-size SWA cache". Both the default and `--swa-full` rows were measured twice in that job with identical results (n = 2). Teacher-forced jobs can pass extra server flags via `teacher_forced.server_args` (`iproofs fidelity run --server-arg=--swa-full`), which are recorded in `server_args`.

Full passes with `--swa-full` (one job on 2026-11-14, 4 H200, 16 slots, n = 1 run each, timed from first to last server request):

| Control | Requests | Pass | Positions per second |
|---|---|---|---|
| Q4_K_M, prompts 0 to 119 (a repeat) | 61,440 | 421 s | 146 |
| Q3_K_S, 360 prompts | 184,320 | 1,306 s | 141 |
| Q2_K, 360 prompts | 184,320 | 1,390 s | 133 |

Every request after the first token of each prompt evaluated exactly 1 token. All three controls finished in 5,613 s combined, whereas Q8_0 and Q4_K_M with the default cache took about 7 h 40 min each.

Does `--swa-full` alter outputs? Not beyond normal run-to-run variance on a 16-slot llama.cpp Maverick run, which is not strictly bit-reproducible:

- Comparing the `--swa-full` Q4_K_M repeat against the stored default-cache pass on the same 120 prompts (`results/v1.0/teacher-forced/llama-4-maverick/top/q4_k_m@0.jsonl`): 1,689 of 61,440 top tokens differed across 119 of 120 prompts, starting from the very first request of a prompt. Mean agreement with the reference was 439.53 positions with `--swa-full` versus 439.34 without it; the repeat scored higher on 48 prompts, lower on 52, and tied on 20 (differing by at most 15 positions on any prompt). The original pass remains the scored record, while the repeat is archived unscored in `results/v1.0/teacher-forced/llama-4-maverick/repeat/q4_k_m-0-swa-full/`.
- Running the same 256 requests (16 prompts × 16 positions on Q3_K_S, manual server in the same job, saved under `results/v1.0/teacher-forced/llama-4-maverick/repeat/q3_k_s-by-hand/`) twice with `--swa-full` and twice without: top tokens differed on 3 requests between the two `--swa-full` runs, on 7 between the two default runs, and on 3 to 10 across all four mixed pairs. Agreement with the reference reply was 206 and 206 with `--swa-full`, versus 204 and 202 without.
- On Llama 3.1 8B (15 prompts at 16 slots), toggling `GGML_CUDA_DISABLE_GRAPHS` alone changed 28 of 7,680 top tokens.

In short, single-prompt scores on multi-slot runs carry a few positions of run-to-run jitter, while the 120-prompt mean shifted by only 0.19 positions between runs. The underlying source of this non-determinism is not yet established; differences appear on the first request of a prompt without `--swa-full` and on later requests with it.

## Resources

- **Llama 3.1 8B:** 16 GB at 16-bit precision; fits on 1 H200 and takes a few minutes per control for 15 prompts.
- **Llama 4 Maverick:** Roughly 800 GB at 16-bit precision, requiring at least 6 H200 GPUs (141 GB each) before accounting for KV cache. `/io/work` needs about 1.4 TB to store the 16-bit GGUF and the largest control simultaneously, in addition to ~800 GB for the 16-bit source files. Llama 4 Scout is roughly 220 GB at 16-bit precision (2 H200 GPUs).

## Tests

The CPU test suite in `tests/` verifies `drop_blocks.py` on a small synthetic GGUF (read back by the harness GGUF parser), the EOS continuation loop against a mock server, a complete `reference` call using fake llama.cpp binaries (checking file creation, reply writing, graceful handling of a failing control, cleanup, and `out.json` validity), request formatting, and Dockerfile rules (RFC-0014 B1 to B3).
