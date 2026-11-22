# DeepProve adapter

DeepProve (Lagrange Labs) proves inference for quantized language models. This adapter targets the Level 1 GPT-2 rung (`l1-gpt2-p512-o512`, RFC-0018): 512 prompt tokens, a 512-token greedy reply, and five requests per session. Upstream is pinned at [`9d1a53e2ef49ffa2c902b8689cd3c58057a4e662`][pin] (on the `master` branch, committed 2026-05-26, still the branch head as of 2026-11-11). Every detail below comes from inspecting the source code at that commit; "read, not run" indicates behavior that has not yet been confirmed by an execution.

**Current status at this commit: `prove` is wired up, while `verify` refuses to run.** The upstream verifier reads its verifier key solely from inside the proof file itself, and no documented command derives that key from the model weights alone (see [§Weights binding](#weights-binding)). Until upstream provides a way to bind verification to an externally committed key, no session can complete and every Level 1 check requiring a verdict remains undecided.

[pin]: https://github.com/Lagrange-Labs/deep-prove/tree/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662
[U]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662

## Licence

- DeepProve is distributed under Lagrange's proprietary licence agreement rather than an open-source licence ([`LICENSE`][U-lic], [`README.md` L43-L45](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/README.md#L43-L45)). Although the workspace manifest includes `license = "MIT OR Apache-2.0"` ([`Cargo.toml` L16](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/Cargo.toml#L16)), that is package metadata; the README explicitly specifies `LICENSE` as governing, so we follow `LICENSE`.
- Section 2 ([L12][U-lic12]) grants "a personal, non-exclusive, non-sublicenseable, non-transferable, revocable, limited license ... (i) to download, install, and internally use the Software solely for the purpose of testing and evaluating it".
- Section 4 ([L16][U-lic16]): "You must not reproduce, distribute, publicly perform, publicly display, or create derivative works of or based on the Software, or disclose, rent, lease, loan, provide, or otherwise transfer, in any manner, to any third party the Software, Documentation or any portion thereof".
- Section 7 ([L25][U-lic25]): the licence terminates "immediately and automatically" upon any breach, and Lagrange may revoke it at any time with notice.
- The `dp-crypto` dependency fetched during build (`Cargo.lock`, commit `22e8e93`) uses the same agreement ([`LICENSE` L35-L46, L72](https://github.com/Lagrange-Labs/dp-crypto/blob/22e8e93cd0f94a7638616a1ae22190feb0a6b275/LICENSE#L35-L72)).

Practical implications for this benchmark (our reading, not legal advice):

- Building and executing DeepProve internally to benchmark it falls under "testing and evaluating".
- The container image is built by the `images` workflow, pushed to the project registry like other adapters, and pulled by hosted runners.
- No upstream code is vendored into this repository: the adapter, tests, and mock proof files contain no upstream source.

[U-lic]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/LICENSE
[U-lic12]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/LICENSE#L12
[U-lic16]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/LICENSE#L16
[U-lic25]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/LICENSE#L25

## What upstream documents

- The README quickstart features `bench-llm` ([`zkml/README.md` L113-L242][U-zr]), which proves **random** prompts ([`zkml/src/bin/bench/llm.rs` L273][U-b273]), verifies in-process, and writes no proof file (L311-L343). Its `--sequence n` flag uses `n - 2` prompt tokens plus 2 generated tokens (L78-L81), meaning the published "GPT-2, 512 tokens" benchmark is 510 + 2. Because `bench-llm` cannot prove a specified prompt, this adapter does not use it.
- The binaries that accept a given prompt and emit a proof file are `deep-prove-worker one-shot` and `deep-prove-cli verify` ([`README.md` L37](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/README.md#L37)). Their CLI flags are documented via `--help` and their clap doc comments ([`deep-prove/src/bin/worker/main.rs` L197-L347][U-wm], [`deep-prove/src/bin/cli/main.rs` L17-L70][U-cm]). The adapter passes only arguments documented there (AGENTS.md rule 1).
- What a proof certifies ([`zkml/README.md` L17-L21][U-zr17]): "concatenates the input tokens and the claimed output tokens into a single sequence, and runs the model on that sequence once ... the model's prediction at position `t` certifies the token at position `t+1`."
- Quantization defaults to 12-bit symmetric and can be overridden via `ZKML_BIT_LEN` ([`zkml/README.md` L11][U-zr11]); the adapter leaves this variable unset.

[U-zr]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L113-L242
[U-zr11]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L11
[U-zr17]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L17-L21
[U-b273]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/bin/bench/llm.rs#L273
[U-wm]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/main.rs#L197-L347
[U-cm]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/cli/main.rs#L17-L70

## 1. Subcommands and the arguments passed

| Subcommand | What runs | Arguments and source |
|---|---|---|
| `info`, `setup` | No upstream command | |
| `commit` | No upstream command; hashes `model.safetensors`, `config.json`, `tokenizer.json`, and `vocab.json` with SHA-256 into `/io/state/commit.json` with `verifier_key: null` | [§Weights binding](#weights-binding) |
| `prove` | `deep-prove-worker --tensor-store temporary one-shot --model /models/model.safetensors --model-format safetensors --tokenizer /models/tokenizer.json --config /models/config.json --max-new-tokens 512 --prompt=<text>`, invoked once per request with cwd `/io/proofs/.tmp-req-<i>/` and `TMPDIR=/io/state/tmp` | `--tensor-store` is required, with `temporary` storing tensors in a temp directory ([worker/main.rs L203-L205, L359-L361][U-ts]; [tenstore genstore.rs L77-L83][U-gs]); `one-shot` flags at [L277-L332][U-os]; `--prompt=` ensures prompts beginning with `-` are parsed as values |
| `verify` | Exits 1 immediately before invoking any upstream binary | [§Weights binding](#weights-binding) |
| `mutate_reply` | No upstream command (RFC-0018 AD-6) | [§Proof file](#proof-file) |

Step-by-step flow for `prove` (launching one worker process per request, since `one-shot` handles a single prompt per invocation, [`immediate.rs` L140-L207][U-im140]):

1. The request's token IDs are decoded back to text by mapping each `vocab.json` entry through GPT-2's byte alphabet, joining the bytes, and decoding UTF-8. Because the worker accepts text rather than raw IDs, it retokenizes the string with `tokenizer.json` including special tokens ([`immediate.rs` L280-L282][U-im280]; [`zkml/src/parser/llm/tokenizer.rs` L152-L163][U-tok]). Any request whose bytes are invalid UTF-8 (such as a window splitting a multi-byte character) or contain a NUL byte is rejected.
2. The worker loads GPT-2 with a context window of `prompt + 512 = 1,024` tokens (L255, L283-L286), initializes fresh proving and verifier contexts (L159-L162), generates the greedy reply and proves one forward pass over prompt plus reply (L164-L166), and writes `llm-proof-<random>.bin` in its working directory (L193-L205). Because generation happens inside the proving call, no separate generation marks are required (RFC-0018 AD-4), and the reply is produced directly by upstream code (AD-3).
3. The adapter renames the proof file to `proof.bin` (since the CLI selects its deserializer based on the `.bin` suffix, [`cli/main.rs` L187-L201][U-cm187]), verifies that the file's recorded `tokens` exactly match the input request IDs (rejecting any retokenization mismatch), extracts `claimed_output` from the proof's IO section ([§Proof file](#proof-file)), and atomically renames the proof directory into place.

[U-ts]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/main.rs#L203-L205
[U-os]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/main.rs#L277-L332
[U-gs]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/tenstore/src/genstore.rs#L77-L83
[U-im140]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/immediate.rs#L140-L207
[U-im280]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/immediate.rs#L280-L287
[U-tok]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/parser/llm/tokenizer.rs#L152-L163
[U-cm187]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/cli/main.rs#L187-L201

## Weights binding

AGENTS.md rule 6 requires that the commitment checked by the verifier come from the harness's commit record, never from files bundled with the proof. At the pinned commit, DeepProve provides no way to satisfy this requirement:

- `deep-prove-cli verify <proof.bin>` takes only a single argument, the proof file itself ([`cli/main.rs` L64-L69][U-cm64]). It deserializes `LlmOneShotOutput` from that file and calls `llm.verifier.verify(llm.proof.proof, llm.tokens, llm.proof.io)` ([L221-L235][U-cm221]), meaning the verifier key (`LLMVerifierContext`, which contains the model commitments, [`zkml/src/model/llm.rs` L63-L77][U-llm63]) comes straight out of the proof.
- The worker generates a fresh key inside every proving call ([`immediate.rs` L159-L162][U-im159]) and provides no CLI flag to load an existing one ([worker/main.rs L277-L332][U-os]).
- Commitment parameters are initialized via `PCS::test_setup(rng, ...)` ([`zkml/src/poly_commit/context.rs` L161-L167][U-pc166]) using `rng_from_env_or_random()` ([`zkml/src/iop/context.rs` L190-L197][U-ic190]), which reads `RNG_SEED` or falls back to random entropy ([`zkml/src/lib.rs` L277-L288][U-lib278]). Because `RNG_SEED` is undocumented at the pinned commit, the adapter does not set it (rule 1). Every invocation therefore samples fresh parameters, so a key created separately would not match the key embedded in the proof.
- While `bench-llm --save_params <name>` writes `<name>.vk` from the weights ([`zkml/README.md` L158-L174][U-zr158]; [`bench/llm.rs` L248-L263][U-b248]), `bench-llm` only proves random prompts (L273), emits no proof files, and also runs a random setup, so it cannot serve as the commit step.
- Upstream does not state whether generating two contexts with the same seed produces identical bytes.

Consequently, `commit` hashes the model files and sets `verifier_key: null`, while `verify` refuses to execute and cites these source lines. Resolving this requires upstream to document either (a) separate commands to generate a verifier key from weights, prove against a supplied key, and verify against an externally supplied key, or (b) `RNG_SEED` together with a guarantee that key serialization is a deterministic function of weights, seed, and context length so `commit` can derive the key and `verify` can check byte-for-byte equality against the recorded one.

[U-cm64]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/cli/main.rs#L64-L69
[U-cm221]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/cli/main.rs#L221-L235
[U-llm63]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/model/llm.rs#L63-L77
[U-im159]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/immediate.rs#L159-L162
[U-pc166]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/poly_commit/context.rs#L161-L167
[U-ic190]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/iop/context.rs#L190-L197
[U-lib278]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/lib.rs#L277-L288
[U-zr158]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L158-L174
[U-b248]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/bin/bench/llm.rs#L248-L263

## The end token

- The worker halts generation as soon as it emits `eos_token` ([`zkml/src/model/llm.rs` L471-L481][U-llm471]), which GPT-2 reads from `config.json`'s `eos_token_id` (50256, [`gpt2/mod.rs` L182][U-g182]). Neither `deep-prove-worker` ([worker/main.rs L277-L332][U-os]) nor `bench-llm` (L59-L142) exposes an option to continue past EOS, whereas Level 1 keeps any generated end token and continues to 512 tokens (RFC-0018 §Terms, `ignore_eos: true`).
- The adapter does not work around this (we neither patch upstream nor edit the model's `config.json`). If a reply hits token 50256 before reaching 512 tokens, it is proved at that shorter length; `prove` logs a warning alongside the shorter `claimed_output`, and the harness coverage check (RFC-0017 INV-REQ-2, `check_requests`) marks the request failed and the session incomplete.
- Verifier EOS behavior (read, not run): `verify` searches for the first 50256 starting from output row `P - 1` and treats its offset **within those rows** as `unpadded_output_len` ([`llm.rs` L835-L847][U-llm835]), then runs the shift check over `for i in seq_len - 1 .. unpadded_output_len - 1` ([L865-L875][U-llm865]) using indices relative to the sequence start. As written, if 50256 appears anywhere in those rows (whether truncating the reply early or appearing as the next prediction at row 1,023), the loop checks zero reply positions. Regardless of this reading, the REPLY check's C1 trials test the verifier empirically on our runs.

[U-llm471]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/model/llm.rs#L471-L491
[U-g182]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/parser/llm/models/gpt2/mod.rs#L182
[U-llm835]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/model/llm.rs#L835-L847
[U-llm865]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/model/llm.rs#L865-L875

## Proof file

The worker serializes `LlmOneShotOutput` using bincode 2 with `config::standard()` (little-endian, variable-length integers) ([`immediate.rs` L184-L200][U-im184]; type definition in [`deep-prove/src/middleware/llm.rs` L11-L21][U-mw]). Based on source inspection (not yet confirmed against a real proof file), the fields lay out as follows:

| Field | Encoding | Used for |
|---|---|---|
| `model_name`, `prompt` | varint length, UTF-8 | Unused |
| `tokens` | varint count, varint IDs (`Token(usize)`, [`parser/llm/mod.rs` L50][U-tokty]) | Passed by the CLI to the verifier as `user_input` ([`cli/main.rs` L235][U-cm221]); `prove` checks that it matches the request |
| `llm_response` | option tag, string; "for logging only" ([`middleware/llm.rs` L11][U-mw]) | Unused |
| `proof.proof` | zkml's `Proof` (opaque to the adapter) | Unused |
| `proof.io` | `IO { input: Vec<Tensor>, output: Vec<Tensor>, .. }` ([`iop/verifier.rs` L68-L75][U-io]); each tensor contains `data`, `shape`, and `unpadded_shape` ([`tensor/mod.rs` L108-L116][U-ten]); each element is serde-encoded compressed arkworks scalar bytes, 32 bytes little-endian ([`zkml/src/lib.rs` L58][U-sf]; [dp-crypto `lib.rs` L9-L31][D-ser]) | Extracting `claimed_output` (input elements from index `P` up to `unpadded_shape`) |
| `verifier` | `LLMVerifierContext` (opaque) | Embedded verifier key disallowed by rule 6 ([§Weights binding](#weights-binding)) |

Because `proof.io` appears after the opaque proof blob, the adapter locates it by pattern matching: the 512 prompt elements must appear exactly once, preceded by vector count 1 and the data length, and followed by the shape fields and output tensor. Any mismatch causes `prove` or `mutate_reply` to exit non-zero before writing or releasing output. The first live worker run will confirm or refute this binary layout.

[U-im184]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/immediate.rs#L184-L200
[U-mw]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/middleware/llm.rs#L11-L21
[U-tokty]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/parser/llm/mod.rs#L50
[U-io]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/iop/verifier.rs#L68-L75
[U-ten]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/tensor/mod.rs#L108-L116
[U-sf]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/lib.rs#L58
[D-ser]: https://github.com/Lagrange-Labs/dp-crypto/blob/22e8e93cd0f94a7638616a1ae22190feb0a6b275/dp-crypto/src/lib.rs#L9-L31

## Level 1 checks: how each control reaches the verifier

- **REPLY, C1.** The verifier does not accept a separate claimed reply; instead, it reads the reply from `proof.io.input` and checks each reply token against the preceding row's argmax output ([`llm.rs` L865-L875][U-llm865]). C1 therefore runs through `mutate_reply` (RFC-0018 AD-6), overwriting IO input element `P + k` and IO output element `P + k - 1` (32 bytes each, in place) with the mutated token while leaving all other bytes intact. `mutate_reply` itself makes no verdict decision.
- **PROMPT, C2.** The CLI reads the prompt from the file's `tokens` field and verifies it against `proof.io.input` ([`llm.rs` L856-L863][U-llm856]). A working `verify` step would substitute the job's `request` into `tokens`, though this is not yet implemented while `verify` refuses to run.
- **MODEL, P1 and C3.** `perturb` (AD-5) is not yet implemented. `levels/L1.yaml` defines the perturbation as shifting one quantized weight in a block-0 dense layer by one step, "which its setup then commits". Because DeepProve quantizes FP32 weights inside each worker invocation (12-bit by default), W' must modify an FP32 weight enough to move its quantized code by one step. Moreover, because no separate setup produces a reusable commitment (every proving call generates a fresh key), the weight change can only be tracked via file digests rather than a commitment ID, and C3 requires closing the weights-binding gap first.
- **NO WEIGHT FILE.** `deep-prove-cli verify` reads only the proof file (L183-L185). The container image includes `strace` for CH-4 file-access tracing once `verify` is enabled.

[U-llm856]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/model/llm.rs#L856-L863

## 2. Verdict mapping

At this commit, `verify` never produces a verdict; it exits 1 with the rule 6 refusal message before running any upstream binary. For reference, `deep-prove-cli verify` returns `Ok` and logs "Proof verified successfully" upon success ([`cli/main.rs` L239-L242][U-cm239]), while any error (from file I/O failure to proof rejection) returns an `anyhow` error from `main` (exit 1). A complete four-verdict mapping will be added once the verifier-key gap is resolved.

[U-cm239]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/cli/main.rs#L239-L242

## 3. commitment_id, verifier_files, prover_files

- `verifier_files`: `/io/state/commit.json`, recording the SHA-256 digests of the model files, `verifier_key: null`, and the explanation. `commitment_id` is the SHA-256 over that file's digest (matching the SASH adapter convention). It identifies the commit record only and is not verified by upstream code.
- `prover_files`: None; the worker reads model files directly from `/models` on each call.

## 4. Values for system.yaml

- `granularity: request`, `incremental_proofs: true`, `steady_boundary: first_proof`: one worker process produces and releases one proof per request upon completion.
- `tokens_covered: prompt_plus_output`: each proof covers a single forward pass across both prompt and reply ([`zkml/README.md` L17-L21][U-zr17]).
- `deterministic_proofs: false`: every proving call runs a randomized setup ([§Weights binding](#weights-binding)).
- `verify_reads: all`: the single proof file `proof.bin` is read in full.
- `forbidden_flags: []`: upstream exposes no flags that weaken the proved statement; the adapter rejects all control flags.
- `image`: `ghcr.io/ai-verification-observatory/deepprove`, pinned to the manifest digest emitted by the `images` workflow.

## 5. Toolchain

- Rust `nightly-2026-01-27`, matching upstream's `rust-toolchain.toml` ([L2](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/rust-toolchain.toml#L2)), installed from the standalone checksummed tarball listed in `inputs.lock`.
- Build dependencies match upstream's Dockerfile (`git`, `protobuf-compiler`, `libssl-dev`, `pkg-config`, `cmake`, `build-essential`, `g++`, `libclang-dev`, [`docker/deep-prove-worker.dockerfile` L2][U-df]) pinned to exact Ubuntu 24.04 package versions, with an Ubuntu 24.04 runtime base matching upstream (L11). Whereas upstream uses the unpinned `rustlang/rust:nightly-slim` tag, this adapter pins the exact nightly from `rust-toolchain.toml`.
- Compiled with default Cargo features: CPU backend, ndarray, and HyperKZG over BN254 ([`zkml/README.md` L36, L111][U-zr36]). The worker hardcodes `HyperKZG<Bn254>` regardless of feature flags ([`immediate.rs` L38-L39][U-im38]); GPU proving (`HyperKZGGpu`) is only wired into `bench-llm` ([`bench/llm.rs` L36-L39][U-b36]).
- No GPU has been used with this adapter yet, and no container image has been built for a live run.

[U-df]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/docker/deep-prove-worker.dockerfile#L1-L11
[U-zr36]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L36
[U-im38]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/src/bin/worker/immediate.rs#L38-L39
[U-b36]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/bin/bench/llm.rs#L36-L39

## 6. CPU binding

Upstream gives no CPU-binding guidance for `deep-prove-worker`. While `bench-llm` accepts `--num_threads` for Rayon threads ([`bench/llm.rs` L109-L113, L163-L177][U-b109]), the worker has no equivalent flag, so the adapter passes none and lets the process run across the CPUs assigned by the harness cpuset.

[U-b109]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/src/bin/bench/llm.rs#L109-L177

## Machine

- Upstream's published benchmarks run on CPU: "24-core / 504 GB CPU machine (AMD EPYC 9254, 2.9 GHz), HyperKZG PCS, default quantization". For GPT-2 at "sequence 512" (510 + 2), upstream reports 7.64 min proving time, 1.33 s verification time, and a 10.71 MiB proof ([`zkml/README.md` L244-L253][U-zr244]). No timings are published for 1,024 positions or 512 generated tokens, and peak RAM is unpublished (though `bench-llm` measures it at L315-L328 and notes "Large LLMs at long context windows require substantial RAM" at L324).
- Proposed profile `prover-cpu-hosted` (not yet added to `reference/`): no GPU, at least 24 physical cores, at least 504 GB host RAM (matching upstream's machine until a probe measures peak RAM at 1,024 tokens), and 50 GB disk (proofs are ~11 MiB, temporary tensor-store size unmeasured). Verification uses the standard `verifier-cpu-hosted` profile, as upstream verifies in ~1.3 s at 512 positions.
- Because Level 1 currently prices GPU-seconds only (`reference/v1.0.yaml`, `priced: [gpu]`), running a CPU row requires either adding a CPU price basis or running on a priced H200 host with its GPU idle; the integrator decides which approach to take.

[U-zr244]: https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md#L244-L253

## 7. Deviations from upstream's own measuring setup

- Upstream benchmarks `bench-llm` with random prompts and 2 generated tokens, whereas this adapter runs `deep-prove-worker` on Level 1's fixed prompts with 512 generated tokens.
- The worker constructs proving and verifier contexts on every call, so each request includes setup cost (unlike `bench-llm --load_params`, which can reload saved parameters).
- Prompts are converted to text and retokenized by upstream ([§1](#1-subcommands-and-the-arguments-passed)); any Level 1 prompt that fails to round-trip back to its original token IDs fails that request.
- Built without upstream's `otel` OpenTelemetry feature ([`deep-prove/Cargo.toml` L12-L18](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/deep-prove/Cargo.toml#L12-L18)), since network-isolated containers cannot export telemetry.
- `TMPDIR` redirects the temporary tensor store to `/io/state/tmp` instead of the container's `/tmp` tmpfs.

## Open items

1. **Weights binding (above):** Clarify with Lagrange how to decouple verifier keys from proof files.
2. **End tokens:** Checked on CPU for the beacon round in `levels/L1-beacon.json` (33867489): greedy FP32 GPT-2 (Transformers, pinned revision) does not emit token 50256 in any of the 15 prompts' 512-token replies or as the 513th prediction. DeepProve's quantized model could behave differently, which the first live worker run will check.
3. **Prompt round-tripping:** Verified on CPU for the same beacon round: all 15 prompts round-trip cleanly back to their exact token IDs using `tokenizer.json` (`tokenizers` 0.23.3).
4. **Model perturbation and metadata:** `perturb` is not yet implemented, and neither `claim.yaml` nor `properties.yaml` exists yet, leaving statement petals hollow (not read, RFC-0018 GL-3). Note also that the level file's security summary cites the book's Basefold commitment scheme (`docs/src/commitments.md`), whereas the binaries invoked by this adapter use HyperKZG over BN254 ([`zkml/README.md` L36][U-zr36]; [`immediate.rs` L38-L39][U-im38]).
5. **Image build:** Verified on 2026-11-11 that apt version pins, archive digests, and the offline Cargo workspace build all succeed. No worker run has been executed yet.

## Tests

The CPU test suite in `systems/deepprove/tests/` uses `deepprove_stub.py` to mock the worker. Its synthetic proof files mirror the binary layout analyzed above rather than captured upstream outputs.
