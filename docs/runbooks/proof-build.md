# Proof build (RFC-0018 MC-4a, MC-5)

A machine-checked proof claim remains unverified until we record a build of the publisher's named theorem at the row's pinned commit. This runbook describes how to execute that build on Hugging Face Jobs and record the outcome.

We run the publisher's own build command without patches. For FlashProve at `9e2bdd8`, that command is `LEAN_ABORT_ON_PANIC=1 lake build Johnson.Goal.Skeleton.SoundOfVerifyAt`, which prints the axiom summary line `'VerifierAndGoals.AtTheName.sound_of_verify_at' depends on axioms: [...]` ([lean/THEOREM.md L445-L457](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/lean/THEOREM.md#L445-L457)). As documented by the publisher (`lean/CHECKING.md` L270-L271, `lean/THEOREM.md` L487), this targeted build trusts Mathlib's downloaded compiled files and does not run a second kernel replay pass.

## Run

[`proof-build.sh`](proof-build.sh) executes inside the digest-pinned Ubuntu base image referenced by `systems/flashprove/Dockerfile`. Running as an unprivileged user, the script installs Lean 4.29.1 from its release archive (verifying the release sha256), clones the pinned commit, checks `HEAD`, runs the publisher's build-file check (`scripts/check.py --only tree`), downloads Mathlib's precompiled cache (failing on an empty fetch), and starts the build under `BUILD_TIMEOUT_S` (set below the job timeout). All output streams directly into `OUT`.

```sh
TS=$(date -u +%Y%m%dT%H%M%SZ); D=runs/$TS-proof-build-flashprove
hf buckets cp docs/runbooks/proof-build.sh hf://buckets/<namespace>/iproofs-dev-runs/$D/proof-build.sh
IMG=docker.io/library/ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
hf jobs run --detach --flavor cpu-performance --timeout 8h --name iproofs-proof-build-flashprove \
  -v hf://buckets/<namespace>/iproofs-dev-runs:/upload \
  -e OUT=/upload/$D/out -e IMAGE=$IMG -e BUILD_TIMEOUT_S=25200 \
  "$IMG" bash /upload/$D/proof-build.sh
```

At 1.90 USD per hour on `cpu-performance`, an 8 h timeout caps spend at 15.20 USD. The targeted build on 2026-11-15 finished in 6,388 s on that flavor.

For the publisher's full check (`MODE=check`, `lean/CHECKING.md` step 5), the script builds the library from scratch, replays the kernel, and audits the named theorems. Its heaviest files use up to 49 GiB per process, and the publisher's reference run took 4 h 26 min on 84 cores and 960 GiB (`CHECKING.md` L83-L105), so this mode needs a machine with roughly 1 TB of memory. Our recorded run on 2026-11-16 used `rtx-pro-6000x4` (92 vCPU, 1,024 GB, 11.00 USD per hour, with the GPUs idle) and settings close to the publisher's:

```sh
hf jobs run --detach --flavor rtx-pro-6000x4 --timeout 21h --name iproofs-proof-check-flashprove \
  -v hf://buckets/<namespace>/iproofs-dev-runs:/upload \
  -e OUT=/upload/$D/out -e IMAGE=$IMG -e MODE=check -e BUILD_TIMEOUT_S=72000 \
  -e LEAN_NUM_THREADS=64 -e WIDE_JOBS=24 "$IMG" bash /upload/$D/proof-build.sh
```

That run took 68,494 s (19 h): roughly 2 h 30 min for the build, followed by kernel replay that ran much slower than the publisher's 2 h 24 min. Because the check cannot resume after an interruption, `BUILD_TIMEOUT_S` should only act as a hang guard. An earlier attempt capped at 23,400 s timed out during kernel replay and wrote no record. Set the timeout to several times the expected duration, and re-evaluate it whenever you change machine types. For a local dry run in Docker (`--platform linux/amd64`), set `SETUP_ONLY=1` to stop right after the publisher's build-file check.

## Record

Download `OUT` from the bucket, then record the build and rebuild the board in the repository:

```sh
iproofs proof-build record OUT --system flashprove --release v1.0 [--replace]
iproofs release board v1.0
iproofs validate --all
```

The harness derives the record status from the exit code and log output (MC-4, MC-4a):

- `built`: exited 0 and printed the theorem's axioms line.
- `failed`: Lean aborted on its own (for example, a panic converted to an abort by `LEAN_ABORT_ON_PANIC=1`, a stack overflow, or another abort) or exited with a non-zero build error. This turns the petal red.
- `stopped`: terminated by `BUILD_TIMEOUT_S`, `SIGKILL`, or `SIGTERM` (including out-of-memory kills). This leaves the petal hollow.

No record is written if setup failed before the build started, or if a full check failed to reach a verdict on the library (for instance, it ran nothing, exited 2 or 3, or every failed step was a skipped Lake invocation due to insufficient memory at startup, missing Lake calls, or unexpected Lake files). Passing `--replace` lets a full check with a verdict (`built` or `failed`) replace an existing targeted build. A stopped build, a targeted build attempting to overwrite a full check, or a second full check will never replace an existing record.
