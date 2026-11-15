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

A rerun is a new record, never a replacement for a stored one. It needs H200 GPUs and the weights, fetched by public source and checked by content hash (`iproofs fetch-model`):

- the counted sessions (`iproofs run`, RFC-0010; the GPU runbooks are in [`docs/runbooks/`](runbooks/));
- the P1 control (commit W, prove with W′), which proves;
- the fidelity runs of the reference and the controls (`iproofs fidelity run`);
- the serving baseline (vLLM, RFC-0015).

A rerun by a runner with no tie to a listed system can raise a figure's evidence tier to `reproduced` (RFC-0007). Nobody else has rerun any Level 1 run yet.
