# SASH slot 2 again, and its weakened-prover controls

Prepared 2026-11-15. Steps 1 to 3 ran on 2026-11-16: the session is `2026-11-16-sash-l1-l31-8b-p512-o512-prover-h200-hosted-1` (self-test passed, 5 of 5 proofs accepted; the `h200` job ran 20,174 s, measured by the provider, n = 1), and its verify without a GPU took 1,539 to 2,164 s per proof (job log, n = 5, 8 CPUs of an AMD EPYC 7R13). Steps 4 and 5 have not run. It replaces SASH's Level 1 session in slot 2 on a host whose self-test passes, verifies it again on a host without a GPU, and then runs two of SASH's registered soundness switches as control jobs. Every job goes through [`hf-job.sh`](hf-job.sh) with the shell set up as in [`hf-jobs.md` §The job command](hf-jobs.md#the-job-command); the spend log and the stop rule of that page apply.

## Why slot 2

- `2026-11-13-sash-l1-l31-8b-p512-o512-prover-h200-hosted-2` failed its machine self-test (`self_test.passed: false`, ST-SAMPLER and ST-JITTER). A run with a failed self-test is ineligible for a release ([RFC-0014 §Manifest](../../rfcs/0014-provenance-and-integrity.md)), so slot 2 has no eligible session.
- The session before it in slot 2, `2026-11-12-sash-l1-l31-8b-p512-o512-prover-h200-hosted-2`, is replaced on the board: its verify ran on a host with a GPU visible and its proofs were not kept to verify again (RFC-0018 SE-3a).
- So the new session must pass its self-test, keep its proofs (`keep-io`) and be verified again on a host with no GPU (RFC-0018 CH-4a).

The session runs SASH at the pin of [`systems/sash/system.yaml`](../../systems/sash/system.yaml): upstream `4f41667297430a598165c4a8604258fe37d952ae` (pull request #36), image `sha256:14defac4f5635bf2665b9f320e81c1ad0b6c6512b644565e7b7a9c189d84d3a5`.

## Before the first job

- `IPROOFS_COMMIT` is a commit on `main` that has `IPROOFS_REQUIRE_SELFTEST` in `hf-job.sh` (added 2026-11-15). Every job on this page uses that one commit.
- The image of `hf-jobs.md` is older; set this one:

```sh
SASH_IMAGE=ghcr.io/ai-verification-observatory/sash@sha256:14defac4f5635bf2665b9f320e81c1ad0b6c6512b644565e7b7a9c189d84d3a5
```

## Step 1: the session (`h200`)

```sh
EXTRA=(-e IPROOFS_REQUIRE_SELFTEST=1 -e IPROOFS_RUNNER_SYSTEMS=sash)
iproofs_job h200 28800 "$SASH_IMAGE" sash-l1-s2-again run sash l1-l31-8b-p512-o512:1:level=L1:session=2:keep-io
EXTRA=()
```

- `IPROOFS_RUNNER_SYSTEMS=sash` records `runner.affiliated_systems: ["sash"]` in the manifest (RFC-0014 §Manifest): the row runs a pull request this project's owner wrote. The v1.0 SASH manifests before it record `[]` (`systems/sash/README.md`).
- With `IPROOFS_REQUIRE_SELFTEST=1` a failed self-test ends the job with exit 5, after the probe and the self-test and before the install, the weights and the run. Read `out/selftest.json` in its bucket folder, write the attempt in the spend log, and start the same command again: a new job gets a new host. Each stopped attempt bills the pull, clone, harness install, probe and self-test, about 10 to 20 minutes (an assumption), 0.83 to 1.67 USD at 5.00 USD per hour.
- Estimate. The harness whole wall of the five stored Level 1 SASH sessions is 12,452 to 14,005 s (`whole_wall_seconds`, measured, tier reported, n = 5, profile `prover-h200-hosted`). Add 1,200 s for the pull, install, 16.1 GB of weights and self-test (the assumption of `hf-jobs.md` stage 2) and up to 3,600 s for the `keep-io` upload (19,556,169,519 B of proofs in `2026-11-13-...-hosted-2`, `proof_bytes_total`, measured, n = 1, plus `io/state`, size not recorded): 13,652 to 18,805 s, 3.8 to 5.2 hours of one H200. At the provider's 5.00 USD per hour that is 18.96 to 26.12 USD; in the benchmark's cost basis it is 3.8 to 5.2 GPU-hours at 5.345 USD per GPU-hour (`reference/v1.0.yaml#/costs/h200`, asserted).
- Timeout 28,800 s (8 h): cap 40.00 USD. With `keep-io` the script keeps 3,600 s for the upload, so the run may use up to 24,600 s.
- The session is done when its bucket folder has `upload.done`, its `manifest.json` has `self_test.passed: true`, and `run.json` has `status: completed` with five accepted proofs. Anything else is recorded like any failed run (AGENTS.md rule 5): a failed session is rerun in the same slot, at most five times (`level-1.md` §Step 3), and is never deleted.

## Step 2: verify again without a GPU (`cpu-xl`)

```sh
R2=runs/<the step 1 folder>/dev-results/v1.0/sash/<its run id>
iproofs_job cpu-xl 21600 "$SASH_IMAGE" sash-l1-s2-reverify reverify sash "$R2"
```

- Estimate. The CPU-only reverify of `2026-11-13-...-hosted-2` took 1,087 to 1,436 s per proof (`reverify/reverify.json`, n = 5, 8 CPUs of an AMD EPYC 7R13). Five proofs, 600 s of install and 600 to 3,600 s to copy the run: 6,636 to 11,380 s, 1.84 to 3.16 USD at 1.00 USD per hour. Timeout 21,600 s, cap 6.00 USD.
- To cut the wall time, run one job per proof (`reverify sash "$R2" req-0`, and so on to `req-4`) and merge the parts with `iproofs reverify RUN_DIR --merge PART...` (`hf-jobs.md`, `reverify` mode).

## Step 3: into the board (the owner's machine, no cost)

```sh
D=<a directory outside the checkout>
hf buckets sync "hf://buckets/$NS/iproofs-dev-runs/$R2" "$D/run" --exclude 'io/*' --exclude 'commitment/*' --dry-run   # check the plan, then again without --dry-run
uv run iproofs results import "$D/run"                       # prints the run id it was given
uv run iproofs results import "$D/run" --add-to results/v1.0/sash/<that run id>   # adds reverify/
uv run iproofs release board v1.0 && uv run iproofs release board v1.0 --check
uv run iproofs site build
```

- Slot 2 then counts the new session if it is eligible (passed self-test, reverified, every proof accepted); the board keeps `2026-11-13-...-hosted-2` and `2026-11-12-...-hosted-2` listed with the cause that removed each. Until this lands, SASH reads "not passed yet" once the board drops ineligible sessions.
- The import leaves out the proof bytes, `io/` and `commitment/` (`iproofs results import`); the proofs stay in the bucket for the controls below.

## Step 4: two weakened-prover controls (control jobs only)

[`systems/sash/controls.yaml`](../../systems/sash/controls.yaml) registers six of SASH's `--unsound-*` switches as `weakened_prover` controls; none has run. These flags weaken SASH's statement, so they run only in these control jobs, never in a session (AGENTS.md rule 4, RFC-0008). Run `sash-unsound-argmax-lax` first, then `sash-unsound-skip-residual-stream`. What each records: whether `boundary-grid --verify`, called as the row calls it, accepts the weakened proof, and whether the binding report marks the edge unbound. An accepted weakened proof is never printed as "passed".

Against a stored Level 1 session kept with `keep-io` that has no `controls.json`: the step 1 session, or `2026-11-13-sash-l1-l31-8b-p512-o512-prover-h200-hosted-1` if its bucket folder still has `io/proofs` and `commitment/` (the `controls` mode refuses it otherwise). Set `R1` to it and `ctl` as in `hf-jobs.md` stage 5:

```sh
R1=runs/<that folder>/dev-results/v1.0/sash/<its run id>
iproofs_job cpu-basic 1800 "$SASH_IMAGE" sash-l1-ctl-seed seed sash "$R1"   # once; refused if the run has a seed record
ctl h200 39600 p-lax      sash-unsound-argmax-lax
# once p-lax's log shows `controls prove sash-unsound-argmax-lax ... exit 0`:
ctl h200 39600 p-residual sash-unsound-skip-residual-stream
```

- Estimate per job. A weakened prove at Level 1 proves the session's five requests (`batches_per_session`): about 11,030 to 12,255 s (`prove_call_seconds` of the five stored sessions, measured, n = 5). Then the honest twin and one verify call per weakened proof, up to six calls of 1,087 to 1,436 s (the reverify above; on the prover's host with a GPU visible they took 994 to 1,087 s per request, `verify_seconds_per_request`, n = 5). With 1,200 s of pull, install, weights and self-test and 600 to 3,600 s to copy the run: 19,352 to 25,671 s, 5.4 to 7.1 hours of one H200, 26.88 to 35.65 USD at 5.00 USD per hour. Timeout 39,600 s (11 h), cap 55.00 USD each. Both jobs: 10.8 to 14.3 H200-hours, 53.76 to 71.30 USD, caps 110.00 USD. A controls job's self-test is recorded in its part; `IPROOFS_REQUIRE_SELFTEST` acts in run mode only.
- Not resolved before running: `iproofs controls --merge` refuses a part whose ids are outside a level session's suite, which is C1, C2, C3 and P1 (`runner.py`, the split-suite part's `suite`, RFC-0018 CH-1). So the parts of these two jobs cannot become a `controls.json`. Each part is complete on its own (outcome, verify verdicts, binding report, host); decide how it enters `results/` (for example as a record beside the run that gates nothing) before spending on the jobs.

## Step 5: the verifier probes C4, C5, C6 and C8 on SASH's kept proofs (`cpu-xl`)

FlashProve's stored control suites ran C4 to C8; SASH's Level 1 suite ran C1, C2, C3 and P1 only (RFC-0018 CH-1). These four jobs run the same probes on a kept SASH session, so both rows have them. C7 is not applicable to SASH (batch size 1). They use the `R1` and the seed record of step 4 (one seed per stored run), and need no GPU:

```sh
ctl cpu-xl 25200 c4 C4
ctl cpu-xl 25200 c5 C5
ctl cpu-xl 25200 c8 C8
ctl cpu-xl 61200 c6 C6
```

- Calls: C4 three (the honest twins of its two proofs, then the replay), C5 and C8 two each, C6 six (the twin and five trials). At 1,087 to 1,436 s a call (the reverify above), with 600 s of install and 600 to 3,600 s to copy the run: c4 4,461 to 8,508 s, c5 and c8 3,374 to 7,072 s each, c6 7,722 to 12,816 s. All four: 18,931 to 35,468 s of `cpu-xl`, 5.26 to 9.85 USD at 1.00 USD per hour; caps 7.00 USD each for c4, c5 and c8 and 17.00 USD for c6 (the timeouts of `hf-jobs.md` stage 5).
- The same merge refusal as step 4 applies: these ids are outside a level session's suite.
