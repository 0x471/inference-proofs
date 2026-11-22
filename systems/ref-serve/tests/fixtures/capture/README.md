# Captured engine outputs

These fixtures were captured once on a GPU host (INV-ADAPTER-9) on 2026-11-04 by running `systems/ref-serve/entrypoint` (`info`, then `prove`) inside the pinned engine image `docker.io/vllm/vllm-openai@sha256:befccf0e7e4089aa23926bb6f887a85c0d46c2a99e6de5c5ffdf5cb7957c5b34` (vLLM v0.32.0). The two wheels in `../../../inputs.lock` were installed offline beforehand, matching the Dockerfile. The host was an HF Jobs `l40sx1` container (NVIDIA L40S, driver 580.178.04). Because that hardware does not match the `prover-h100` profile, nothing here is a benchmark measurement.

- **Model:** `unsloth/Llama-3.1-8B-Instruct` at `4699cc75b550f9c6f3173fb80f4703b62d946aa5` (the model used by the SASH workloads, #49), including its `*.safetensors` and `*.json` files.
- **Options:** The `sash-l31-8b-c1024` settings from `../../../system.yaml` (FP8 W8A8 quantized at load, PM-4).
- **Prompt (`prompts.jsonl`):** The first 1,024 token IDs of a repeated public-domain sentence ("It was the best of times, ...", Dickens, 1859), tokenized with the model's `tokenizer.json` without special tokens.
- **Job:** Batch size 1, 1 batch, 64 output tokens.
- **Files:** `out.json` (the adapter's `prove` output), `proofs/req-0/outputs.json` (the released outputs), and `commands.jsonl` (the recorded engine invocation, whose `started_mono_ns` comes from that host's monotonic clock).
