# SASH slot 2 again, and its weakened-prover controls

Prepared 2026-11-15. Steps 1 through 3 ran on 2026-11-16: the replacement session is `2026-11-16-sash-l1-l31-8b-p512-o512-prover-h200-hosted-1` (self-test passed, 5 of 5 proofs accepted; the `h200` job ran 20,174 s as measured by the provider, n = 1), and CPU-only reverification took 1,539 to 2,164 s per proof (job log, n = 5, 8 CPUs of an AMD EPYC 7R13). Steps 4 and 5 have not been run yet.

This runbook replaces SASH's Level 1 session in slot 2 on a host that passes its self-test, reverifies the proofs on a CPU-only host, and then runs two of SASH's registered soundness switches as control jobs. Every job runs through [`hf-job.sh`](hf-job.sh) using the shell setup from [`hf-jobs.md` §The job command](hf-jobs.md#the-job-command), and follows the spend log and stop rule defined there.

## Why slot 2

- `2026-11-13-sash-l1-l31-8b-p512-o512-prover-h200-hosted-2` failed its machine self-test (`self_test.passed: false`, ST-SAMPLER and ST-JITTER). Because a run with a failed self-test is ineligible for a release ([RFC-0014 §Manifest](../../rfcs/0014-provenance-and-integrity.md)), slot 2 had no eligible session.
- The earlier session in slot 2, `2026-11-12-sash-l1-l31-8b-p512-o512-prover-h200-hosted-2`, was replaced on the board because its verification ran on a host with a visible GPU and its proofs were not kept for reverification (RFC-0018 SE-3a).
- The replacement session must therefore pass its self-test, retain its proofs (`keep-io`), and be reverified on a host without a GPU (RFC-0018 CH-4a).

The session runs SASH at the pin in [`systems/sash/system.yaml`](../../systems/sash/system.yaml): upstream commit `4f41667297430a598165c4a8604258fe37d952ae` (pull request #36) and image digest `sha256:14defac4f5635bf2665b9f320e81c1ad0b6c6512b644565e7b7a9c189d84d3a5`.

## Before the first job

- Set `IPROOFS_COMMIT` to a commit on `main` that includes `IPROOFS_REQUIRE_SELFTEST` in `hf-job.sh` (added 2026-11-15), and use that same commit for every job on this page.
- Override `SASH_IMAGE` with the current pin (the digest in `hf-jobs.md` is older):

```sh
SASH_IMAGE=ghcr.io/ai-verification-observatory/sash@sha256:14defac4f5635bf2665b9f320e81c1ad0b6c6512b644565e7b7a9c189d84d3a5
```

## Step 1: the session (`h200`)

```sh
EXTRA=(-e IPROOFS_REQUIRE_SELFTEST=1 -e IPROOFS_RUNNER_SYSTEMS=sash)
iproofs_job h200 28800 "$SASH_IMAGE" sash-l1-s2-again run sash l1-l31-8b-p512-o512:1:level=L1:session=2:keep-io
EXTRA=()
```

- **Affiliation tag:** Setting `IPROOFS_RUNNER_SYSTEMS=sash` records `runner.affiliated_systems: ["sash"]` in the manifest (RFC-0014 §Manifest) because this row runs a pull request written by this project's owner. Earlier v1.0 SASH manifests recorded `[]` (`systems/sash/README.md`).
- **Fail-fast self-test:** With `IPROOFS_REQUIRE_SELFTEST=1`, a failed self-test exits 5 right after the probe and self-test, before installing weights or starting the run. Inspect `out/selftest.json` in the bucket folder, log the attempt in the spend log, and rerun the same command to land on a fresh host. Each aborted attempt bills only the pull, clone, harness install, probe, and self-test (roughly 10 to 20 minutes assumed, or 0.83 to 1.67 USD at 5.00 USD per hour).
- **Duration and cost estimate:** Across the five stored Level 1 SASH sessions, `whole_wall_seconds` ran from 12,452 to 14,005 s (measured, tier reported, n = 5, profile `prover-h200-hosted`). Adding 1,200 s for pull, install, 16.1 GB of weights, and self-test (the assumption from `hf-jobs.md` stage 2) plus up to 3,600 s for the `keep-io` upload (19,556,169,519 B of proofs in `2026-11-13-...-hosted-2`, `proof_bytes_total`, measured, n = 1, plus `io/state` of unrecorded size) gives 13,652 to 18,805 s, or 3.8 to 5.2 hours on one H200. At the provider's 5.00 USD per hour rate, that is 18.96 to 26.12 USD; on the benchmark's cost basis (`reference/v1.0.yaml#/costs/h200`, asserted), it is 3.8 to 5.2 GPU-hours at 5.345 USD per GPU-hour.
- **Timeout:** 28,800 s (8 h), capping spend at 40.00 USD. With `keep-io`, the script reserves 3,600 s for upload, leaving up to 24,600 s for the run itself.
- **Completion criteria:** The session is complete when its bucket folder contains `upload.done`, `manifest.json` has `self_test.passed: true`, and `run.json` reports `status: completed` with five accepted proofs. Record any other outcome as a failed run (AGENTS.md rule 5). You may rerun a failed session in the same slot up to five times (`level-1.md` §Step 3), and never delete prior attempts.

## Step 2: verify again without a GPU (`cpu-xl`)

```sh
R2=runs/<the step 1 folder>/dev-results/v1.0/sash/<its run id>
iproofs_job cpu-xl 21600 "$SASH_IMAGE" sash-l1-s2-reverify reverify sash "$R2"
```

- **Duration and cost estimate:** CPU-only reverification of `2026-11-13-...-hosted-2` took 1,087 to 1,436 s per proof (`reverify/reverify.json`, n = 5, 8 CPUs of an AMD EPYC 7R13). With five proofs, 600 s for setup, and 600 to 3,600 s to copy the run from the bucket, total time is 6,636 to 11,380 s (1.84 to 3.16 USD at 1.00 USD per hour). The 21,600 s timeout caps spend at 6.00 USD.
- **Parallel option:** To shorten wall time, launch one job per proof (`reverify sash "$R2" req-0` through `req-4`) and combine the parts with `iproofs reverify RUN_DIR --merge PART...` (`hf-jobs.md`, `reverify` mode).

## Step 3: into the board (the owner's machine, no cost)

```sh
D=<a directory outside the checkout>
hf buckets sync "hf://buckets/$NS/iproofs-dev-runs/$R2" "$D/run" --exclude 'io/*' --exclude 'commitment/*' --dry-run   # check the plan, then again without --dry-run
uv run iproofs results import "$D/run"                       # prints the run id it was given
uv run iproofs results import "$D/run" --add-to results/v1.0/sash/<that run id>   # adds reverify/
uv run iproofs release board v1.0 && uv run iproofs release board v1.0 --check
uv run iproofs site build
```

- Once imported, slot 2 uses the new session if it is eligible (passing self-test, CPU reverified, and all proofs accepted). The board still lists `2026-11-13-...-hosted-2` and `2026-11-12-...-hosted-2` along with the reason each was excluded. Until this replacement lands, SASH shows "not passed yet" once ineligible sessions are filtered out.
- `iproofs results import` omits proof bytes, `io/`, and `commitment/`; those proofs remain in the bucket for the control jobs below.

## Step 4: two weakened-prover controls (control jobs only)

[`systems/sash/controls.yaml`](../../systems/sash/controls.yaml) registers six of SASH's `--unsound-*` flags as `weakened_prover` controls, none of which have been run yet. Because these flags weaken SASH's statement, they are strictly restricted to control jobs and are never passed during a normal session (AGENTS.md rule 4, RFC-0008). Run `sash-unsound-argmax-lax` first, followed by `sash-unsound-skip-residual-stream`. Each control records whether `boundary-grid --verify` (invoked the same way the benchmark row invokes it) accepts the weakened proof, and whether the binding report flags the edge as unbound. An accepted weakened proof is never reported as "passed".

Target a stored Level 1 session saved with `keep-io` that does not yet have a `controls.json`: either the step 1 session, or `2026-11-13-sash-l1-l31-8b-p512-o512-prover-h200-hosted-1` if its bucket folder still contains `io/proofs` and `commitment/` (otherwise `controls` mode will refuse it). Set `R1` to that run and define `ctl` as in `hf-jobs.md` stage 5:

```sh
R1=runs/<that folder>/dev-results/v1.0/sash/<its run id>
iproofs_job cpu-basic 1800 "$SASH_IMAGE" sash-l1-ctl-seed seed sash "$R1"   # once; refused if the run has a seed record
ctl h200 39600 p-lax      sash-unsound-argmax-lax
# once p-lax's log shows `controls prove sash-unsound-argmax-lax ... exit 0`:
ctl h200 39600 p-residual sash-unsound-skip-residual-stream
```

- **Estimate per job:** At Level 1, a weakened prove covers all five requests in the session (`batches_per_session`), taking roughly 11,030 to 12,255 s (`prove_call_seconds` across the five stored sessions, measured, n = 5). That is followed by the honest twin and one verify call per weakened proof: up to six calls at 1,087 to 1,436 s each (from the reverification numbers above; on the prover host with a visible GPU they took 994 to 1,087 s per request, `verify_seconds_per_request`, n = 5). Adding 1,200 s for pull, install, weights, and self-test plus 600 to 3,600 s to copy the run gives 19,352 to 25,671 s, or 5.4 to 7.1 hours on one H200 (26.88 to 35.65 USD at 5.00 USD per hour). The 39,600 s (11 h) timeout caps each job at 55.00 USD. Together, both jobs require an estimated 10.8 to 14.3 H200-hours (53.76 to 71.30 USD; combined cap 110.00 USD). Note that a controls job records its self-test in its part file, because `IPROOFS_REQUIRE_SELFTEST` only takes effect in `run` mode.
- **Open question before running:** `iproofs controls --merge` rejects any part whose control IDs fall outside a level session's suite, which is C1, C2, C3, and P1 (`runner.py`, the split-suite part's `suite`, RFC-0018 CH-1). As a result, these two parts cannot be merged into `controls.json`. Each part is self-contained (holding its outcome, verify verdicts, binding report, and host record), so decide how these artifacts will enter `results/` (for example, as a non-gating record beside the run) before spending compute on them.

## Step 5: the verifier probes C4, C5, C6 and C8 on SASH's kept proofs (`cpu-xl`)

FlashProve's stored control suites included C4 through C8, while SASH's Level 1 suite ran only C1, C2, C3, and P1 (RFC-0018 CH-1). These four CPU-only jobs run the same verifier probes against a kept SASH session so both rows have comparable coverage. C7 is not applicable to SASH because its batch size is 1. Reuse `R1` and the seed record from step 4 (each stored run keeps a single seed):

```sh
ctl cpu-xl 25200 c4 C4
ctl cpu-xl 25200 c5 C5
ctl cpu-xl 25200 c8 C8
ctl cpu-xl 61200 c6 C6
```

- **Calls and cost estimate:** C4 runs three verify calls (the honest twins of its two proofs plus the replay), C5 and C8 run two calls each, and C6 runs six calls (the honest twin plus five trials). At 1,087 to 1,436 s per call (from the reverification measurements above), plus 600 s for install and 600 to 3,600 s to copy the run, expected durations are 4,461 to 8,508 s for c4, 3,374 to 7,072 s each for c5 and c8, and 7,722 to 12,816 s for c6. Across all four jobs, that totals 18,931 to 35,468 s on `cpu-xl` (5.26 to 9.85 USD at 1.00 USD per hour). Using the timeouts from `hf-jobs.md` stage 5 caps c4, c5, and c8 at 7.00 USD each and c6 at 17.00 USD.
- The same merge restriction from step 4 applies here, because these control IDs sit outside a level session's suite.
