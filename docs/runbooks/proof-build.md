# Proof build (RFC-0018 MC-4a, MC-5)

Machine-checked stays hollow until a build of the publisher's named theorem is recorded at the
row's pin. This page runs that build on a CPU host of Hugging Face Jobs and records it.

The build is the publisher's own command, unpatched. For FlashProve at `9e2bdd8`:
`LEAN_ABORT_ON_PANIC=1 lake build Johnson.Goal.Skeleton.SoundOfVerifyAt`, then its line
`'VerifierAndGoals.AtTheName.sound_of_verify_at' depends on axioms: [...]`
([lean/THEOREM.md L445-L457](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/lean/THEOREM.md#L445-L457)).
It trusts Mathlib's downloaded compiled files and runs no second kernel pass, as the publisher
says (lean/CHECKING.md L270-L271, lean/THEOREM.md L487).

## Run

[`proof-build.sh`](proof-build.sh) runs in the Ubuntu image that `systems/flashprove/Dockerfile`
pins by digest. It installs Lean 4.29.1 from its release archive, checked against the sha256 that
the release lists, as an ordinary user. It clones the pin and checks `HEAD`, runs the publisher's
check of its build files (`scripts/check.py --only tree`), fetches Mathlib's compiled files and
refuses an empty fetch, then builds under a time limit of its own (`BUILD_TIMEOUT_S`, below the
job's timeout). Everything it prints goes into `OUT` as it goes.

```sh
TS=$(date -u +%Y%m%dT%H%M%SZ); D=runs/$TS-proof-build-flashprove
hf buckets cp docs/runbooks/proof-build.sh hf://buckets/<namespace>/iproofs-dev-runs/$D/proof-build.sh
IMG=docker.io/library/ubuntu@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852
hf jobs run --detach --flavor cpu-performance --timeout 8h --name iproofs-proof-build-flashprove \
  -v hf://buckets/<namespace>/iproofs-dev-runs:/upload \
  -e OUT=/upload/$D/out -e IMAGE=$IMG -e BUILD_TIMEOUT_S=25200 \
  "$IMG" bash /upload/$D/proof-build.sh
```

Cap: 8 h on `cpu-performance` at 1.90 USD per hour, 15.20 USD.

## Record

Copy `OUT` from the bucket, then, in the repository:

```sh
iproofs proof-build record OUT --system flashprove --release v1.0
iproofs release board v1.0
iproofs validate --all
```

The record's status follows from the exit code and the output (MC-4, MC-4a): `built` at exit 0
with the theorem's axioms line; `failed` when Lean gave up on its own (a panic, which
`LEAN_ABORT_ON_PANIC=1` turns into an abort, a stack overflow or another abort), which sets the
petal red; `stopped` at the build's own time limit or a SIGKILL or SIGTERM (out of memory among
them), which leaves it hollow; `failed` otherwise. A job whose setup failed never started the
build and gives no record. A stored record is never written over.
