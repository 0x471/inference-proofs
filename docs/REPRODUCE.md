# Reproducing Level 1 v1.0

This guide explains how an outside reader can verify the published board from the repository alone. Tier 1 requires only a laptop, with no GPU, no proof bytes, and no external accounts. It confirms that every state, ranking position, and figure shown on [inferenceproofs.ai](https://www.inferenceproofs.ai) follows directly from the stored run records under the rules of [RFC-0018](../rfcs/0018-level-1-ladder.md). Tier 1 does not prove that the underlying run records are genuine; checking that requires either the raw proof bytes (Tier 2) or a fresh GPU rerun (Tier 3).

All commands below were tested on 2026-11-15 on a macOS laptop without a GPU, using a checkout of the commit that added this document.

## Tier 1: rebuild and recompute (laptop)

### Set up

Clone the full git history rather than a shallow copy. The level's beacon round is derived from the commit timestamp that froze `levels/L1.yaml` (PR-2), which a shallow clone cannot inspect.

```bash
git clone https://github.com/ai-verification-observatory/inference-proofs
cd inference-proofs
uv sync --frozen
```

### The board

Running `iproofs release board v1.0 --check` recomputes `releases/v1.0/board.json` from `results/v1.0/`, `levels/L1.yaml`, the claim cards, `systems/*/properties.yaml`, and the reference profiles, then compares the output byte for byte against the committed file.

```bash
uv run iproofs release board v1.0 --check
# release board: releases/v1.0/board.json matches
```

If you want to inspect differences rather than just get a pass/fail exit code, omit `--check` to rewrite the file in place and inspect the diff:

```bash
uv run iproofs release board v1.0
git diff --stat releases/v1.0/board.json   # empty when the board reproduces
```

### Every derived figure of every run

Each run directory contains the raw records (`run.json`, `manifest.json`, and `logs/`) along with the derived metrics computed from them. Running `iproofs derive --check` recalculates every derived value and checks for a bit-exact match.

```bash
for d in results/v1.0/*/2026-*/; do uv run iproofs --quiet derive --check "$d"; done
# derive: 0 failures (eleven times: four FlashProve, five SASH, two serving)
```

### The level and its prompts

Running `iproofs level check --frozen` validates the level definition, checks every file it references, and verifies that the drand `quicknet` round stored in `levels/L1-beacon.json` is the first round published after the freezing commit's timestamp.

```bash
uv run iproofs level check --frozen
# L1.yaml: ok (frozen 2026-11-11) sha256:6b7b0a06...
```

You can also regenerate a rung's prompts from the stored beacon round. Each counted run records its slot's prompt digest in `manifest.json` under `workload.prompt_set_digest`, which must match the corresponding `slot-K` digest printed by the command below.

```bash
uv run --extra prompts iproofs level prompts --out /tmp/l1-prompts llama-3.1-8b
# "slot-1": "sha256:616727b6...", the digest SASH's slot 1 session names
```

Note that the commit timestamp reflects the committer's own clock. The level was frozen three times on 2026-11-11, taking a fresh beacon round each time; the 2026-11-15 amendment to PR-2 lists all three rounds. The harness checks that `randomness == sha256(signature)` but does not verify the BLS signature itself, which you can check using drand's own client.

### Fidelity

Running `iproofs fidelity score` rescores the stored replies for the reference engine, the controls, and each prover row, updating the rung's `fidelity.json` in place so `git diff` reveals any changes.

```bash
uv run iproofs fidelity score --rung llama-3.1-8b --release v1.0
uv run iproofs fidelity score --rung llama-4-maverick --release v1.0
uv run iproofs fidelity score --rung llama-3.1-8b --release v1.0 --part teacher-forced
git diff --stat results/
```

When tested on 2026-11-15, the teacher-forced scores reproduced identically. The matched-prefix scores reproduced every stored number, while current code appends a `step_tests` block to each row that the stored files predate (39 added lines per rung, with no existing values altered). Run `git checkout results/` afterward to restore the working tree.

### The repository and the site

```bash
uv run iproofs validate --all        # schemas, claim cards, derivations, pins, licences, words
uv run iproofs site build --out /tmp/site
diff -rq /tmp/site web | grep -v '^Only in web'   # empty: the committed pages are the built ones
```

## Tier 2: verify the proofs again (CPU, needs the proof bytes)

The raw proof bytes are not committed to this repository and are not yet public. Each run directory lists the SHA-256 digest of every proof and verifier file in `digests.txt`, while the bytes themselves remain in a private storage bucket.

Once you have the proof bytes, the following checks run on a CPU alone:

- Run `iproofs reverify <run_dir>` on a machine without a GPU to re-verify a kept run (RFC-0018 CH-4a), then compare its verdicts against `run.json`.
- Run the tampering controls C1 to C3 and C4 to C8 (`iproofs controls <run_dir>`, RFC-0008), which mutate a stored proof or its claimed input and re-verify it.
- Submit a forgery attempt of your own: any proof accepted by the pinned verifier for a commitment, prompt, or reply it ought to reject. Report any such finding through the process in [SECURITY.md](../SECURITY.md).

## Tier 3: rerun (GPU)

External reruns are explicitly outside the scope of Level 1 (RFC-0018 §Non-Goals, RFC-0007 §Non-Goals). The harness tags every quantity as `reported`, and the `reproduced` tier remains reserved without an active definition (RFC-0007). Any rerun produces a separate record; it does not overwrite a stored run or alter the published board. No outside party has rerun a Level 1 job yet. The instructions below adapt [`gpu-run.md` §Hosted execution](runbooks/gpu-run.md#hosted-execution-prover-h100-hosted-prover-h200-hosted) and [`level-1.md`](runbooks/level-1.md), and were not executed while writing this page.

Hardware requirements for each row, taken from [`reference/v1.0.yaml`](../reference/v1.0.yaml):

- SASH on Llama 3.1 8B (`l1-l31-8b-p512-o512`): `prover-h200-hosted`, requiring one H200 SXM GPU with at least 140,000 MiB of memory, 15 logical CPUs on the GPU's NUMA node (23 total), 200 GiB of host RAM, 500 GiB of free disk, Ubuntu 24.04, Linux kernel 5.19 or newer, and cgroup v2.
- FlashProve on Llama 4 Maverick (`l1-maverick-p512-o512`): the same profile on a larger host with at least 330 GB of available RAM for `commit`, a CPU supporting SHA extensions, and an environment that permits `madvise(MADV_WIPEONFORK)` ([`systems/flashprove/README.md`](../systems/flashprove/README.md) §Machine needs).
- Serving baselines (vLLM, RFC-0015): `serving-h200x1-hosted` for 8B and `serving-h200x4-hosted` (four H200 GPUs) for Maverick.
- Maverick fidelity reference (RFC-0018 FI-1): `fidelity-h200x8-hosted` (eight H200 GPUs).
- CPU-only re-verification: `verifier-cpu-hosted`, with 16 CPUs and 115 GiB of RAM.

To run one session, start a container from the image specified in `systems/<name>/system.yaml` (`<repository>@<digest>`, matching `system.image.ref` in the run's `manifest.json`) with at least 500 GiB of disk. Gated models require `HF_TOKEN` from your own account in the environment (see [`gpu-run.md`](runbooks/gpu-run.md)).

```bash
git clone https://github.com/ai-verification-observatory/inference-proofs && cd inference-proofs
git checkout <harness.git_commit in the run's manifest.json>
uv sync --frozen --extra gpu --extra fetch --extra prompts
export IPROOFS_CACHE=<a directory on the container disk>
python3 docs/runbooks/host-probe.py --profile prover-h200-hosted
uv run iproofs machine-record --hosted --gpu <index> --provider <name> --selftest
uv run iproofs fetch-model l1-l31-8b-p512-o512
uv run iproofs run --system sash --workload l1-l31-8b-p512-o512 --profile prover-h200-hosted \
  --hosted --gpu <index> --provider <name> --level L1 --session <K> --keep-io
```

Passing `--keep-io` preserves the generated proofs so you can run `iproofs reverify <run_dir> --hosted --provider <name>` afterward inside a container of the same image with no GPU on a host that never downloaded the weights (RFC-0018 CH-4a). Compare the resulting numbers manually against the matching `slot` entry under `rungs[].rows[].sessions[]` in `releases/v1.0/board.json`.

The remaining runs on a rung follow the same pattern: the P1 control (`iproofs run ... --session <K> --control-run --control-suite`, RFC-0018 CH-1b), the fidelity jobs (`iproofs fidelity run`), and the serving baseline.

Keep three caveats in mind when inspecting the resulting records:

- Every v1.0 GPU profile leaves its driver version as `unpinned` (RFC-0006 Q5), so every run on these profiles fails PC-DRIVER and sets `harness.nonconforming: true` in the manifest. The published runs record this as well, and conformance failures never block execution (RFC-0006).
- A different GPU model forms its own configuration and is never pooled or compared directly with H200 rows (RFC-0006 R5). Release v1.0 does not define profiles for other GPU models.
- All counted v1.0 runs executed on Hugging Face Jobs (recorded in `provider` in each manifest). Other providers have not been tested: gVisor blocked FlashProve's `madvise` call (#68), and the verify-without-weights check requires `strace` to monitor file opens inside the container (RFC-0018 CH-4). A provider running a different driver requires its own driver pin (RFC-0006 Q5).
