# Reproducing Level 1 v1.0

How an outsider checks the published board from the repository alone. Tier 1 needs a laptop: no GPU, no proof bytes, no account. It shows that every state, position and figure on [inferenceproofs.ai](https://www.inferenceproofs.ai) follows from the stored run records by the rules in [RFC-0018](../rfcs/0018-level-1-ladder.md). It does not show that the run records are true: that needs the proof bytes (tier 2) or a rerun (tier 3).

Every command below was run on 2026-11-15, on a macOS laptop with no GPU, on a checkout of the commit that adds this file.

## Tier 1: rebuild and recompute (laptop)

### Set up

Clone the whole history, not a shallow copy: the level's beacon round is computed from the commit that froze the level file (PR-2), and a shallow clone cannot date it.

```bash
git clone https://github.com/ai-verification-observatory/inference-proofs
cd inference-proofs
uv sync --frozen
```

### The board

`iproofs release board v1.0 --check` recomputes `releases/v1.0/board.json` from `results/v1.0/`, `levels/L1.yaml`, the claim cards, `systems/*/properties.yaml` and the reference profiles, and compares it byte for byte with the stored file.

```bash
uv run iproofs release board v1.0 --check
# release board: releases/v1.0/board.json matches
```

To see a difference rather than a verdict, run it without `--check` (it rewrites the file) and diff:

```bash
uv run iproofs release board v1.0
git diff --stat releases/v1.0/board.json   # empty when the board reproduces
```

### Every derived figure of every run

Each run directory holds the raw records (`run.json`, `manifest.json`, `logs/`) and the derived metrics computed from them. `iproofs derive --check` recomputes the derived metrics and compares them bit for bit.

```bash
for d in results/v1.0/*/2026-*/; do uv run iproofs --quiet derive --check "$d"; done
# derive: 0 failures (eleven times: four FlashProve, five SASH, two serving)
```

### The level and its prompts

`iproofs level check --frozen` checks the level file, the files it names, and that the stored beacon round in `levels/L1-beacon.json` is the first drand `quicknet` round after the freezing commit's time.

```bash
uv run iproofs level check --frozen
# L1.yaml: ok (frozen 2026-11-11) sha256:6b7b0a06...
```

The prompts of a rung are drawn again from the stored round. Each counted run's `manifest.json` names its slot's prompt digest (`workload.prompt_set_digest`), which the printed `slot-K` digest must equal.

```bash
uv run --extra prompts iproofs level prompts --out /tmp/l1-prompts llama-3.1-8b
# "slot-1": "sha256:616727b6...", the digest SASH's slot 1 session names
```

The round's commit time is the committer's own clock. The level was frozen three times on 2026-11-11, and each freeze took a fresh round; PR-2's amendment of 2026-11-15 lists them. The harness checks `randomness == sha256(signature)` but not the BLS signature: check it with drand's own client.

### Fidelity

`iproofs fidelity score` rescores the stored replies of the reference, the controls and each row, and writes the rung's `fidelity.json` in place, so `git diff` shows any difference.

```bash
uv run iproofs fidelity score --rung llama-3.1-8b --release v1.0
uv run iproofs fidelity score --rung llama-4-maverick --release v1.0
uv run iproofs fidelity score --rung llama-3.1-8b --release v1.0 --part teacher-forced
git diff --stat results/
```

On 2026-11-15 the teacher-forced scores reproduced exactly. The matched-prefix scores reproduced every stored value, and the current code adds a `step_tests` block to each row that the stored files predate (39 added lines per rung, none changed). Run `git checkout results/` afterwards.

### The repository and the site

```bash
uv run iproofs validate --all        # schemas, claim cards, derivations, pins, licences, words
uv run iproofs site build --out /tmp/site
diff -rq /tmp/site web | grep -v '^Only in web'   # empty: the committed pages are the built ones
```

## Tier 2: verify the proofs again (CPU, needs the proof bytes)

The proof bytes are not in the repository and are not public yet. Each run directory names every proof and verifier file by sha256 in `digests.txt`; the bytes sit in a private bucket.

With the bytes, these need a CPU only:

- `iproofs reverify <run_dir>` verifies a kept run again on a host with no GPU (RFC-0018 CH-4a), and the verdicts can be compared with `run.json`.
- The tampering controls C1 to C3 and C4 to C8 (`iproofs controls <run_dir>`, RFC-0008) change a stored proof or its claimed input and verify it again.
- A forgery attempt of your own: a proof the pinned verifier accepts for a commitment, prompt or reply it should refuse. Report it as [SECURITY.md](../SECURITY.md) says.

## Tier 3: rerun (GPU)

Outside reruns are a non-goal of Level 1 (RFC-0018 §Non-Goals, RFC-0007 §Non-Goals). The harness records every quantity as `reported`, and the `reproduced` tier is reserved, with no definition yet (RFC-0007). A rerun is a new record: it replaces no stored run and does not change the board. Nobody else has rerun any Level 1 run yet. The steps below follow [`gpu-run.md` §Hosted execution](runbooks/gpu-run.md#hosted-execution-prover-h100-hosted-prover-h200-hosted) and [`level-1.md`](runbooks/level-1.md). They were not run for this page.

What each row needs, from [`reference/v1.0.yaml`](../reference/v1.0.yaml):

- SASH on Llama 3.1 8B (`l1-l31-8b-p512-o512`): `prover-h200-hosted`, one H200 SXM with at least 140,000 MiB, 15 logical CPUs on the GPU's NUMA node and 23 in all, 200 GiB of host memory, 500 GiB of free disk, Ubuntu 24.04, kernel 5.19 or later, cgroup v2.
- FlashProve on Llama 4 Maverick (`l1-maverick-p512-o512`): the same profile on a larger host, with 330 GB available to `commit`, a CPU with the SHA extensions and a sandbox that lets `madvise(MADV_WIPEONFORK)` through ([`systems/flashprove/README.md`](../systems/flashprove/README.md) §Machine needs).
- The serving baselines (vLLM, RFC-0015): `serving-h200x1-hosted` (8B) and `serving-h200x4-hosted` (Maverick, four H200).
- The Maverick fidelity reference (RFC-0018 FI-1): `fidelity-h200x8-hosted`, eight H200.
- Verify again with no GPU: `verifier-cpu-hosted`, 16 CPUs and 115 GiB.

One session, in a container started from the image of `systems/<name>/system.yaml` (`<repository>@<digest>`, the `system.image.ref` of the run's `manifest.json`), with at least 500 GiB of disk. A gated model needs `HF_TOKEN` from your own account in the environment ([`gpu-run.md`](runbooks/gpu-run.md)).

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

`--keep-io` keeps the proofs, so `iproofs reverify <run_dir> --hosted --provider <name>` can verify them again in a container of the same image with no GPU, on a host that never fetched the weights (RFC-0018 CH-4a). Compare the run's figures by hand with its slot's entry in `releases/v1.0/board.json` (`rungs[].rows[].sessions[]`, matched by `slot`).

A rung's other runs follow the same setup: the P1 control (`iproofs run ... --session <K> --control-run --control-suite`, RFC-0018 CH-1b), the fidelity runs (`iproofs fidelity run`) and the serving baseline.

What the record will show:

- Every v1.0 GPU profile records the driver as `unpinned` (RFC-0006 Q5), so every run on them fails PC-DRIVER and records `harness.nonconforming: true`. The published runs record it too. No conformance check refuses a run (RFC-0006).
- A different GPU model is its own configuration, never pooled or compared with the H200 rows (RFC-0006 R5). v1.0 declares no profile for another GPU model.
- Every counted v1.0 run ran on Hugging Face Jobs (`provider` in each manifest). Another provider is untested: gVisor refused FlashProve's `madvise` call (#68), and the verify-without-weights check needs `strace` to trace the verify call's file opens inside the provider's container (RFC-0018 CH-4). A provider with another driver needs its own pin (RFC-0006 Q5).
