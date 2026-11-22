# RFC-0010: Harness runner and job lifecycle

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0004, RFC-0005, RFC-0008, RFC-0011, RFC-0012

## Summary

This RFC specifies the `iproofs` command-line interface, the structure of a job (one system, one workload, one shape, one repetition, and one machine), and the state machine that governs a job from start to finish. It also defines what is written to disk at each stage, the concurrency model, step timeouts, the retry policy, the error taxonomy, and how failures are recorded so that no run is ever dropped or silently resumed. Together, these rules form the operational layer that turns the adapter contract ([RFC-0005](0005-adapter-contract.md)) and measurement rules ([RFC-0011](0011-measurement-and-sampling.md)) into published run directories ([RFC-0009](0009-results-and-publication.md)).

## Motivation

PRD requirement F9 calls for "a harness that runs a job end to end, measures externally, collects the adapter's internal timings and writes a result file valid against the schema", while non-functional requirement N3 specifies that failed runs must be "recorded, not dropped" ([PRD Section 7](../docs/PRD.md#7-requirements)). [AGENTS.md hard rule 5](../AGENTS.md#hard-rules) also prohibits rounding away or omitting results. If a runner silently retried a failed proving step until it succeeded, or resumed a half-finished job after a crash, it would publish figures that did not happen as measured. For that reason, the runner's lifecycle and failure semantics need to be fixed before any adapter is implemented.

Consider three concrete scenarios:

1. A runner on an H100 host executes three repetitions of `fp-maverick-w1024-b24`, and the second repetition is OOM-killed during `prove`. The runner writes a run directory for repetition 2 recording a `resource` failure, completes repetitions 1 and 3 normally, and computes statistics showing n = 2 and n_failed = 1.
2. The host loses power during `commit`. When the runner restarts, it detects the incomplete staging directory, records it as an `internal` failure at step `commit`, and begins the next repetition cleanly from `pending`.
3. A CI job runs `iproofs run --system fake --workload fake-tiny-ci --profile ci-cpu --control-suite` on a hosted CPU runner in a few minutes without a GPU.

## Goals

- Maintain a single deterministic state machine per job, logging every transition and writing a record for every terminal outcome.
- Never retry any timed step; restrict retries strictly to network fetches that happen outside timed scopes.
- Provide a stable CLI with documented exit codes that works cleanly both in CI and interactively.
- Write run directories atomically by keeping partial work in a staging directory, so any directory under `results/` is either absent or complete and schema-valid.
- Guarantee that a crash never produces a measured row.
- Expose a typed internal API so unit and integration tests can drive the runner without Docker containers.

## Non-Goals

- Multi-host scheduling, job queues, or a background daemon service. A single runner process manages one host.
- Running multiple jobs concurrently on the same GPU.
- Resuming a job mid-step after an interruption.
- Uploading results automatically to any remote store. Publication happens exclusively through pull requests ([RFC-0009](0009-results-and-publication.md)).

## Proposed Design

### Command line

`iproofs` is built on Python's standard-library `argparse`. Its subcommands, arguments, and behaviour are listed below:

| Command | Arguments | Behaviour |
|---|---|---|
| `iproofs validate [PATH ...] [--all] [--changed-since REF] [--format {text,json}]` | Paths to files or directories; defaults and flags are defined in [RFC-0013](0013-validation-and-ci.md#local-use) | Runs every CI check from [RFC-0013](0013-validation-and-ci.md) across the selected paths |
| `iproofs derive RUN_DIR [--check]` | One run directory | Computes derived metrics and statistics ([RFC-0004](0004-metrics-timing-grades.md)); without `--check` it writes them into a new `run.json` only during run creation; with `--check` it recomputes them and checks for bit-for-bit equality |
| `iproofs run --system S --workload W --profile P [--repetitions N] [--results DIR] [--control-suite] [--provider NAME] [--prompts-from RUN_DIR] [--load matched|high] [--gpus LIST] [--allow-nonconforming]` | `N` defaults to 3 with a minimum of 1 (values below 3 are allowed for tests and set `repetitions_below_minimum: true`); `DIR` defaults to `results/`; `--provider` records the hosting provider in the machine record ([RFC-0006](0006-reference-hardware-and-cost.md#machine-record)); `--prompts-from` replays the prompt seeds of an earlier run for reference rows and reruns ([RFC-0015](0015-reference-rows.md#steps-per-job)); `--load` selects the load point for a production-serving job (serve role only, defaulting to `matched`, [RFC-0015](0015-reference-rows.md) SRV-1); `--gpus` binds a serving profile's GPUs by index in hosted runs (`--gpu` remains for prover profiles); `--allow-nonconforming` is accepted as a no-op because profile conformance is recorded in the manifest (`harness.nonconforming`) and never blocks a run | Runs N jobs sequentially, then derives statistics across them |
| `iproofs controls RUN_DIR [--prepare-perturbed WORKLOAD]` | Completed run directory | Executes the negative control suite ([RFC-0008](0008-negative-controls.md)) and writes `controls.json`; `--draw-seed` writes the seed record for a split suite, `--only` runs one subset using that seed, and `--merge` assembles `controls.json` from the completed parts ([RFC-0008 §Split suites](0008-negative-controls.md#split-suites)) |
| `iproofs machine-record [--selftest]` | None | Writes the machine record ([RFC-0006](0006-reference-hardware-and-cost.md)) to stdout as JSON; `--selftest` also runs the calibration checks from [RFC-0011](0011-measurement-and-sampling.md#calibration-self-test) and exits 3 if any check fails |
| `iproofs fetch-model WORKLOAD [--headers-only] [--serving RECORD]` | Workload id | Downloads model weights by source and revision, verifies every file hash ([RFC-0014](0014-provenance-and-integrity.md)), and recomputes a `computed` weight width from the verified files ([RFC-0003](0003-workloads.md#weight-bits) WB-5); `--headers-only` skips downloading weights and recomputes the width via HTTP range reads of file headers at the pinned revision, outputting JSON; `--serving` fetches a production-serving record's files instead (RFC-0014 SM-2) |
| `iproofs prompts build WORKLOAD --seed SEED` | Workload id and 64-bit seed | Materialises the prompt set and outputs its digest ([RFC-0003](0003-workloads.md)) |
| `iproofs release freeze RELEASE` | Release id | Writes `releases/<release>/index.json` |
| `iproofs release plan RELEASE` | Release id | Projects the run-campaign compute budget from external figures using the derivation code ([08](../docs/spec/08-performance-budget.md#run-campaign-compute-budget)); the output is `projected` and is never treated as a result |
| `iproofs site build [--out DIR]` | Defaults to the repository's `web/` directory | Generates the static public site from the newest frozen release (RFC-0009 §Site) |

Global options are `--log-level {debug,info,warning}` (default `info`) and `--quiet` (which suppresses progress output on stderr). None of the CLI options alter what is measured; any parameter that affects measurement belongs in the workload or system file and goes through code review.

All commands share a single exit code table:

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | A check failed (such as a validation error or a `derive --check` mismatch) |
| 2 | Usage error reported by `argparse` |
| 3 | The host environment does not meet the profile or a prerequisite (for example, no cgroup v2, another process using the GPU, or Docker missing) |
| 4 | At least one job ran and finished with a recorded failure |
| 5 | Internal harness error; if a run directory was created, it records the failure |

For `iproofs run`, a run directory is written for every job whenever the command exits 0 or 4. Exit code 3 is raised before any job starts, so nothing is written to disk.

### Job specification

```python
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True, slots=True)
class JobSpec:
    system: str            # system id, RFC-0012 pattern
    workload: str          # workload id
    workload_version: int
    profile: str           # prover profile id, RFC-0006
    repetition: int        # 1-based index within this invocation
    control_suite: bool    # run RFC-0008 controls after verify
    results_root: str      # path to results/
    release: str           # e.g. "v0.1", from reference/<release>.yaml in force
```

Each run receives an id of the form `<YYYY-MM-DD>-<system>-<workload>-<profile>-<n>`, where the date is the UTC date when the job starts and `n` is the smallest positive integer not yet used under `results/<release>/<system>/` for that prefix (INV-RUN-6).

### State machine

```
pending -> resolved -> image_ready -> machine_recorded -> info -> setup -> commit -> prove -> verify -> controls -> written
   any non-terminal state --(failure)--> failed(step) -> written
```

- When `control_suite` is false, the runner skips `controls` and transitions directly from `verify` to `written`.
- `written` is the sole terminal state. Even when a job fails, it still reaches `written` with `status: "failed"` and a populated failure record.

| State | Action on entry | Writes to staging |
|---|---|---|
| `pending` | Create staging directory `results/<release>/<system>/.staging-<run-id>/` and write `job.lock` with the process id and start time | `job.lock`, `logs/harness.jsonl` |
| `resolved` | Load and validate the system, workload, and reference files; resolve the model directory by digest; draw the job seed; materialise prompts and compute their digest | `manifest.partial.json` (inputs) |
| `image_ready` | Verify that the local image digest matches `system.yaml` `image.digest` (pulling by digest if absent, using `fetch` retries) | Image record |
| `machine_recorded` | Capture the machine record, check the profile, confirm no other compute process is active on the bound GPU, and select the cpuset | Machine record |
| `info` | Run `info` and verify that `upstream_commit` matches `system.yaml` | `io/info/out.json` |
| `setup` | Run `setup` | `io/setup/` |
| `commit` | Run `commit` with resource sampling enabled | Commit record (commitment id, files, sizes, timings) |
| `prove` | Run `prove` with resource sampling and the proof release watcher | Proof release times, proof digests, `out.json` |
| `verify` | Run `verify` on the verifier profile (8 CPUs) for each proof, then run it once on 1 CPU for the first proof | `verifier/<proof_id>.json` |
| `controls` | Run the negative control suite | `controls.json` |
| `written` | Compute raw metrics, assemble `run.json` and `manifest.json`, validate both, and rename staging into the final run directory | Final run directory |

Every state transition emits a `job.state` event ([05-observability](../docs/spec/05-observability.md#events-catalogue)). During `verify`, the runner checks every proof on the standard verifier profile, but runs the single-threaded verification check on only the first proof to bound CPU time.

### Writing the run directory

- All job outputs are written first to the staging directory. Each individual file is written to `<name>.tmp`, flushed, `fsync`ed, and renamed into place. JSON files are always written through the single canonical writer defined in [RFC-0012](0012-schemas-and-serialization.md).
- Upon entering `written`, the runner validates `run.json`, `manifest.json`, and (when present) `controls.json` against their JSON Schemas. If any document fails validation, the job is recorded as an `internal` failure (indicating a harness bug), and the offending document is preserved under `logs/invalid/`.
- Once validation succeeds, the staging directory is renamed to `results/<release>/<system>/<run-id>/` and its parent directory is `fsync`ed. Because of this atomic rename, a run directory never appears in a partial state (INV-RUN-2).
- The `io/` working directories containing proof bytes are not committed to git. Instead, proof files are hashed into `digests.txt` ([RFC-0014](0014-provenance-and-integrity.md)), and the `io/` directory is removed once the job finishes unless `--keep-io` is passed.

### Crash recovery

Whenever `iproofs run` starts, it scans `results/<release>/*/.staging-*` for leftover staging directories. If a staging directory's `job.lock` refers to a process that is no longer alive, the runner finalises it as a failed run with `status: "failed"` and failure `{kind: "internal", step: <last state reached>, message: "runner terminated before completion"}`, preserving its logs and any partial records before renaming it into a normal run directory. An interrupted job is never resumed (INV-RUN-3). Conversely, if a staging directory's locked process is still alive, the runner exits 3 because another runner is currently active on the same results tree.

### Concurrency

- In v0.1, the runner executes one job at a time per GPU and permits only one runner process per host, enforced by holding an exclusive `flock` on `results/.runner.lock` for the lifetime of `iproofs run`.
- All steps inside a job execute strictly sequentially.
- During `commit`, `prove`, and `verify`, the runner spawns background sampler threads ([RFC-0011](0011-measurement-and-sampling.md)): an NVML sampler, a cgroup sampler, and (during `prove`) a release watcher. These threads write into in-memory ring buffers so they never block the main thread, which joins them after the container exits.
- The main thread creates the container with `docker create` (untimed) and then blocks on `docker start --attach` under the step's wall-clock timeout ([RFC-0011](0011-measurement-and-sampling.md#timing-a-container-call)).

### Timeouts

Each step's wall-time limit comes from `timeouts_s` in `system.yaml`, falling back to the defaults in [RFC-0005](0005-adapter-contract.md#systemyaml). If a step exceeds its limit, the runner invokes `docker kill --signal KILL iproofs-<run-id>-<step>`, waits up to 30 s for the container to exit, and records a `timeout` failure. Model fetches and image pulls each carry a separate 6-hour limit, sized for downloads of roughly 200 GB models (this is an operational timeout, not a measured quantity).

### Retry policy

- Only `fetch` operations (downloading model weights, fetching prompt corpora, and pulling container images by digest) may be retried. They allow up to 3 attempts with backoff intervals of 2 s, 8 s, and 32 s, and they always finish before `machine_recorded`, outside every timed scope.
- Timed steps (`setup`, `commit`, `prove`, `verify`, and controls) are never retried within a job (INV-RUN-1). A failed repetition is recorded, counted in `n_failed` ([RFC-0004](0004-metrics-timing-grades.md)), and followed normally by the next repetition.
- A runner MAY start a separate invocation later to collect additional repetitions. Those runs are distinct jobs with new run ids, and every job (failed runs included) enters the configuration's aggregate statistics.

### Error taxonomy

```python
from enum import StrEnum

class ErrorKind(StrEnum):
    CONFIG = "config"
    ENVIRONMENT = "environment"
    INTEGRITY = "integrity"
    FETCH = "fetch"
    ADAPTER = "adapter"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    POLICY = "policy"
    INTERNAL = "internal"

class IProofsError(Exception):
    kind: ErrorKind
    def __init__(self, kind: ErrorKind, message: str, *, step: str | None = None,
                 exit_code: int | None = None, last_lines: tuple[str, ...] = ()) -> None: ...
```

| Kind | Triggers | CLI exit |
|---|---|---|
| `config` | Input file fails schema validation; unknown system or workload; workload missing from `system.yaml` `workloads` | 1 (validate) or 2 (run, before jobs) |
| `environment` | cgroup v1; kernel older than 5.19; Docker older than 25.0; profile requirements not met; another compute process active on the GPU | 3 |
| `integrity` | Model file hash mismatch; image digest mismatch; `info` upstream commit mismatch; unpinned reference | 4 (inside a job) or 1 (validate) |
| `fetch` | Network failure persisting after 3 attempts | 4 |
| `adapter` | Non-zero exit code; invalid `out.json`; violation of INV-ADAPTER-6, 7, or 8 | 4 |
| `timeout` | Step wall-time limit exceeded | 4 |
| `resource` | Container OOM-killed; disk full (`ENOSPC`) | 4 |
| `policy` | Forbidden flag passed outside a control job; control job submitted as a measured row | 4 (run) or 1 (validate) |
| `internal` | Unexpected exception; harness output fails its own schema; crash recovery | 5 |

Verifier verdicts (`accept`, `reject`, `no_verdict`, `invalid_call`) are benchmark results rather than errors.

### Failure record

```python
@dataclass(frozen=True, slots=True)
class Failure:
    kind: ErrorKind
    step: str                      # state name at which the failure occurred
    message: str                   # redacted, <= 4096 bytes
    exit_code: int | None          # container or process exit code, if any
    last_lines: tuple[str, ...]    # last 50 lines of adapter stderr, redacted
    at: str                        # RFC 3339 UTC timestamp
```

This record is serialised into `run.json` under the `failure` key (which is `null` for successful jobs). Redaction follows the rules in [05-observability](../docs/spec/05-observability.md#redaction).

### Internal API

```python
@dataclass(frozen=True, slots=True)
class StepResult:
    step: str
    started_mono_ns: int
    ended_mono_ns: int
    exit_code: int
    out: dict[str, object] | None        # validated adapter-out document
    samples: "SampleSet"                 # RFC-0011
    releases: tuple[tuple[str, int], ...] = ()  # (proof_id, release_mono_ns), prove only

class ContainerRunner(Protocol):
    def run(self, image: str, subcommand: str, io_dir: Path, *, gpu: int | None,
            cpuset: str, mems: str, memory: str | None, timeout_s: float) -> StepResult: ...

@dataclass(slots=True)
class Job:
    spec: JobSpec
    state: str
    staging: Path
    steps: dict[str, StepResult]
    failure: Failure | None
    def advance(self) -> None: ...       # performs the action for the next state; raises IProofsError

class Runner:
    def __init__(self, containers: ContainerRunner, clock: Callable[[], int] = time.monotonic_ns) -> None: ...
    def run(self, spec: JobSpec) -> Path: ...                         # returns the written run dir
    def run_many(self, base: JobSpec, repetitions: int) -> list[Path]: ...
    def recover(self, results_root: Path) -> list[Path]: ...          # crash recovery
```

`ContainerRunner` has two implementations: `DockerRunner` for real execution and `InProcessRunner` for tests, which invokes the fake adapter's Python entrypoint directly while honouring the same file contract. Injecting the clock keeps state-machine tests deterministic.

### Interaction with measurement and controls

- The runner owns the timed window for every container step: it samples the monotonic clock immediately before launching `docker start --attach` and immediately after the process exits ([RFC-0011](0011-measurement-and-sampling.md)). Sampler threads start before that window opens and stop after it closes.
- Raw metrics (wall durations, resource samples, proof release timestamps, and byte sizes) are stored in `run.json` as quantities with `grade: "measured"` and `source.kind: "harness"`. Adapter-reported phases are stored separately with `source.kind: "adapter"`. Derived metrics are always computed by `iproofs.derive` from the stored raw values, never from transient in-memory state (INV-RUN-5).
- The negative control suite reuses the same verify path and `ContainerRunner` with `control: true`, writing its outputs exclusively to `controls.json` (INV-CTRL-4).

### Invariants

- **INV-RUN-1:** No timed step is retried within a job.
- **INV-RUN-2:** A run directory under `results/` is either complete and schema-valid, or it does not exist.
- **INV-RUN-3:** A job interrupted before reaching `written` is recorded as failed and never resumed.
- **INV-RUN-4:** Every job reaches `written`, including failed ones; the only exception is exit code 3 raised before the first job begins.
- **INV-RUN-5:** Derived values stored in `run.json` always equal what `iproofs derive` computes from the stored raw values.
- **INV-RUN-6:** Run ids are unique within `results/<release>/<system>/`.
- **INV-RUN-7:** The commitment passed to every `verify` call comes from the job's own commit record (INV-ADAPTER-5).

## Alternatives Considered

1. **Retry a failed `prove` step once.** Transient GPU errors do occur, and a single retry would be cheaper than launching a fresh invocation. However, retrying silently removes failures from the published distribution, violating N3. The runner instead records the failure and moves on to the next repetition so failure rates remain visible.
2. **Resume interrupted jobs from the last completed step.** Although commits for Maverick workloads take a long time, resuming a job would blend two separate process lifetimes and machine states (page cache contents, GPU clocks), making `whole_wall` meaningless.
3. **Use a workflow engine (such as a DAG scheduler) or a job queue service.** While useful for large multi-host campaigns, v0.1 targets one host, one GPU, and sequential execution, which does not justify running an extra service or taking on a heavy dependency. A future RFC can layer distributed scheduling on top of the same `JobSpec`.
4. **Build the CLI with Click or Typer.** `argparse` handles the command surface cleanly, introduces zero external dependencies, and keeps exit-code handling completely explicit.
5. **Write files directly into the final run directory during execution.** A crash mid-job would leave a partial directory that looks like a finished run. Staging first and renaming atomically enforces INV-RUN-2 cleanly.

## Drawbacks

- A transient error costs an entire repetition, which can be expensive on large shapes such as the SASH 4,096-position workload (upstream whole-wall rate 0.840 positions/s over 4,608 positions, grade external, tier reported, source SASH results at `11decec3c0b62c707618aab5deb82750b355d202`).
- Running jobs strictly sequentially leaves the GPU idle during CPU-only `verify` and control steps. Pipelining could be added later, though it would risk contaminating the next job's CPU measurements.
- Relying on process-id liveness alone for crash recovery can be fooled if a PID is reused after a reboot. To prevent that, `job.lock` records the kernel boot id (`/proc/sys/kernel/random/boot_id`) alongside the PID.

## Migration / Rollout

- This RFC supersedes the earlier job description in Section 3 of the initial SPEC.
- The state machine ships first with `InProcessRunner` and `DockerRunner` tested against `systems/fake`, followed by GPU sampling and the real system adapters.
- CLI evolution follows the harness SemVer policy ([09-release-and-versioning](../docs/spec/09-release-and-versioning.md)). Exit codes are part of the public API and may change only in a major release (or a minor release during 0.x, accompanied by a CHANGELOG entry).

Amendment of 2026-11-09 (RFC-0015 SRV-6 production serving): `iproofs run` adds `--load matched|high` and `--gpus LIST`, and `iproofs fetch-model` adds `--serving RECORD`. Two new network commands are introduced: `iproofs serving check-mirror RECORD` and `iproofs serving pin RECORD` (RFC-0014 SM-3). The manifest gains `workload.load_point`, `workload.batch_size_run`, `workload.batches_per_session_run`, `workload.prompt_count_run`, `workload.prompt_prefix_digest`, `engine {name, version, image, interface}`, and `serving_model {id, version, digest, source {repo, revision}, publisher {repo, revision}}` (where `serving_model.digest` and `engine.image` act as join keys, while `id` and `version` are for display), and `run.json` `inputs` gains `gpu_count`. Release configuration grouping adds `load_point` (defaulting to `matched` when absent, so existing runs group as before). Before `info`, the runner raises a `config` error if the profile's GPU count is missing or 0, if the bound GPU count disagrees with it, if a serve-role system runs on a non-serving profile (or vice versa), or if a larger-GPU-count serving job is attempted after a smaller-count run of the same workload has already succeeded (RFC-0015 SRV-6).

Amendment of 2026-11-09 (RFC-0015 SRV-1 sizing): Adds the CPU-only, offline command `iproofs serving size-session RUN_DIR`. It reads a stored matched serving run (`run.json` and `manifest.json`) together with the workload record, outputs the computed `batches_per_session_run` and its inputs as JSON, and rejects (`config`, exit 2) any failed run, high-load run, or run lacking a steady scope.

## Testing Strategy

- `test_state_machine_happy_path`: runs `InProcessRunner` with the fake adapter and verifies that every state is visited in order with one `job.state` event emitted per transition.
- `test_controls_skipped_without_flag`: verifies the direct `verify -> written` transition when `control_suite` is false.
- `test_failure_at_each_step`: parametrised across `info`, `setup`, `commit`, `prove`, and `verify`; confirms that a fake adapter exiting 1 produces a run directory with `failure.step` set to that step and CLI exit code 4.
- `test_no_retry_of_timed_steps`: confirms that a fake adapter configured to fail once and then succeed is invoked exactly once per job on the failing step.
- `test_fetch_retries_three_times_with_backoff`: verifies that an injected fetcher failing twice before succeeding is called three times, requesting sleeps of 2 s and 8 s from an injected sleeper.
- `test_timeout_kills_container`: confirms that a fake step sleeping past a 1 s timeout produces a `timeout` failure and records a stubbed `docker kill` call.
- `test_oom_is_resource`: verifies that a stubbed `docker inspect` reporting `OOMKilled: true` classifies the failure as `resource`.
- `test_crash_recovery_records_internal_failure`: confirms that a staging directory with a dead PID becomes a failed run directory with `failure.kind == "internal"` and the last reached step, without invoking any adapter.
- `test_live_staging_blocks_runner`: verifies that a staging directory with a live PID and matching boot id causes `iproofs run` to exit 3.
- `test_run_dir_atomic`: simulates killing the runner between file writes and verifies that no directory under `results/` is left without `run.json`.
- `test_run_id_increments`: verifies that two runs started on the same UTC date receive suffixes 1 and 2.
- `test_exit_codes`: exercises minimal scenarios for every documented exit code (bad argument -> 2, cgroup v1 stub -> 3, failed job -> 4, injected exception -> 5, `derive --check` mismatch -> 1).
- `test_derived_from_stored_raw`: confirms that mutating a raw value in a written `run.json` causes `iproofs derive --check` to fail.
- `test_repetitions_below_minimum_marked`: verifies that `--repetitions 1` records `repetitions_below_minimum: true`.

## Decisions

- Q1. Controls run once per configuration, on the first successful repetition ([RFC-0008](0008-negative-controls.md#where-controls-run)).
- Q2. Single-thread verification runs on the first proof only.
- Q3. `io/` directories kept via `--keep-io` have no hard size cap, though the runner warns if free disk space drops below the profile's 500 GB requirement.

## References

- [PRD Section 7, F9 and N3](../docs/PRD.md#7-requirements).
- [RFC-0004](0004-metrics-timing-grades.md), [RFC-0005](0005-adapter-contract.md), [RFC-0006](0006-reference-hardware-and-cost.md), [RFC-0007](0007-evidence-tiers-and-reproduction.md), [RFC-0008](0008-negative-controls.md), [RFC-0009](0009-results-and-publication.md), [RFC-0011](0011-measurement-and-sampling.md), [RFC-0012](0012-schemas-and-serialization.md), [RFC-0013](0013-validation-and-ci.md), [RFC-0014](0014-provenance-and-integrity.md).
- [docs/spec/04-error-model.md](../docs/spec/04-error-model.md), [docs/spec/05-observability.md](../docs/spec/05-observability.md).
- Linux `rename(2)`, `fsync(2)`, `flock(2)`.
