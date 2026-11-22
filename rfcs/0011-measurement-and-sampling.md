# RFC-0011: External measurement and resource sampling

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0004, RFC-0005, RFC-0006, RFC-0010

## Summary

This RFC defines how the harness measures a job from outside the adapter container: the clock source, container call timing, proof release observation, GPU and host resource sampling, proof size accounting, and the calibration self-test a host must pass before its results are accepted. Every recorded metric in RFC-0004 maps to exactly one measurement mechanism specified here.

## Motivation

Benchmark numbers are only as trustworthy as the instrumentation behind them. PRD F9 calls for a harness that "measures externally": because upstream figures often come from scripts and logs that readers cannot inspect (for example, FlashProve's performance page notes that its measurement scripts are not in the repository, RFC-0007), this project cannot rely on code running inside the adapter container for its headline metrics. The initial SPEC listed the target quantities (wall time, GPU memory peak sampled at 10 Hz or faster, host memory from cgroups excluding file cache, CPU time, energy, and proof size), but left out how to collect them reliably. Three practical subtleties determine whether those readings are accurate: cgroup files disappear as soon as a container exits, page cache inflates `memory.peak`, and proof release times cannot be observed externally unless the adapter follows an explicit filesystem protocol. This RFC solves all three.

## Goals

- Derive all durations from a single monotonic clock in the harness process; never compute durations from wall-clock timestamps.
- Observe proof release times directly in the harness rather than trusting timestamps reported by the adapter.
- Sample GPU metrics at 10 Hz minimum (20 Hz target), detecting and reporting any sampling gaps.
- Read exact final cgroup counters (`memory.peak`, `cpu.stat`) after the container exits.
- Keep the harness's own measurement overhead within a documented budget and isolate it onto CPUs not used by the job.
- Require every host to pass a calibration self-test before any measurements taken on it are accepted.

## Non-Goals

- Internal prover profiling (such as kernel timings or NVTX ranges). Adapters may still report internal phases, provided they are clearly labelled and never feed derived metrics (RFC-0004 INV-GRADE-2).
- Network and disk I/O accounting (containers run with `--network none`, and disk I/O is not a v0.1 metric).
- Supporting non-Linux hosts for GPU runs. CPU-only operations (validation, derivation, and fake-system runs) work on any platform, while the Linux-specific cgroup and inotify code falls back to portable equivalents or is disabled elsewhere (§Portability).

## Proposed Design

### Clock

- C-1. All durations are measured with `time.monotonic_ns()` (`CLOCK_MONOTONIC` on Linux). Records also include RFC 3339 UTC wall-clock timestamps from `datetime.now(UTC)` for human readers, but wall-clock values never enter arithmetic.
- C-2. Every boundary event from RFC-0004 §Timing scopes is stored as a `mono_ns` integer in `run.json` under `events` (`{"event": "prove.start", "mono_ns": ...}`, RFC-0012), allowing every duration to be recomputed from stored events. Second-denominated metrics are computed by `iproofs.measure.span_seconds(start_ns, end_ns) -> float` = `(end_ns - start_ns) / 1e9`.
- C-3. The harness pins itself via `os.sched_setaffinity` to a single logical CPU outside `cpu.bound_prover` and `cpu.bound_verifier` (RFC-0006), preventing harness threads from competing with the workload.

### Timing a container call

Each adapter invocation splits into two Docker CLI commands: `docker create` (untimed, returning the container id) followed by `docker start --attach <id>` (timed).

```python
@dataclass(frozen=True, slots=True)
class CallTiming:
    start_ns: int        # immediately before spawning `docker start --attach`
    end_ns: int          # immediately after the subprocess is reaped
    exit_code: int
    container_id: str    # kept in memory only; never written to records

def timed_call(argv_create: Sequence[str], timeout_s: float, on_started: Callable[[str], None]) -> CallTiming: ...
```

- T-1. `start_ns` is recorded after `docker create` finishes and immediately before spawning `docker start`. Container start-up overhead (namespace creation and GPU device injection) falls inside the timed window and is not subtracted (RFC-0004).
- T-2. Step timeouts come from `system.yaml` (RFC-0010). When a call times out, the harness runs `docker kill`, classifies the failure as `timeout`, and still collects the final cgroup counters.
- T-3. The container id is kept strictly in memory for cgroup lookups and `docker kill`; because it is a host-local identifier, it is never logged or written to disk (RFC-0006 exclusion list).

### Cgroup accounting

Because the container runtime deletes a container's own cgroup upon exit, its final counters vanish before the harness can read them. To avoid losing the tail of the run, the harness runs each container inside a parent systemd slice that it controls:

- G-1. Before starting a container call, the harness launches a lightweight placeholder scope: `systemd-run --scope --slice=iproofs-<job_hash>-<step>.slice --unit=iproofs-<job_hash>-<step>-hold sleep infinity`, where `job_hash` is the first 12 hex characters of the run id's SHA-256 digest. This placeholder keeps the parent slice alive after the container terminates.
- G-2. The container is created with `--cgroup-parent=iproofs-<job_hash>-<step>.slice`, placing its cgroup as a child of the slice so cgroup v2 hierarchical accounting rolls `memory.peak` and `cpu.stat` up into the slice.
- G-3. Before launching the container, the harness records the slice's `memory.peak` (covering only the placeholder) as `baseline_bytes` and `cpu.stat` `usage_usec` as `cpu_baseline_usec`. After the container exits, it reads both counters again and then tears down the placeholder unit.
- G-4. `<step>_host_memory_peak_kernel` equals the slice's post-call `memory.peak` in bytes (which includes page cache, is exact for the slice, and is biased upward by at most the recorded `baseline_bytes`). `<step>_cpu_seconds` equals (`usage_usec` after − `cpu_baseline_usec`) / 1e6.
- G-5. `<step>_host_memory_peak_anon` is the maximum value of `memory.stat` `anon` observed across 10 Hz samples taken by the sampler thread. It excludes file cache, though because it is sampled, a transient spike shorter than one sampling interval can be missed.

RISK: Cgroup v2 does not expose an exact kernel high-water mark for anonymous memory alone, so the anonymous peak has to be sampled. To stay transparent, the benchmark publishes both metrics with their exact definitions (`kernel` exact including page cache, `anon` sampled excluding cache) and never substitutes one for the other. If review shows the two values diverging by more than page cache can explain, a future revision MAY introduce an eBPF-based peak tracker.

```python
class CgroupReader:
    def __init__(self, slice_path: Path) -> None: ...         # /sys/fs/cgroup/iproofs.slice/... resolved via `systemctl show -p ControlGroup`
    def memory_peak(self) -> int: ...                          # bytes, memory.peak
    def memory_anon(self) -> int: ...                          # bytes, memory.stat "anon"
    def cpu_usage_usec(self) -> int: ...                       # cpu.stat "usage_usec"
    def oom_kills(self) -> int: ...                            # memory.events "oom_kill"
```

- G-6. Any positive `oom_kill` delta during a call fails the step with error kind `resource`, regardless of the container's exit code.
- G-7. If `memory.peak` is unavailable (indicating a kernel older than 5.19) or the slice cannot be created, host conformance fails (RFC-0006 PC-KERNEL, PC-CGROUP) before any timed step begins.

### Proof release watcher

Adapters write each proof into `/io/proofs/.tmp-<proof_id>/` and then atomically `rename(2)` it to `/io/proofs/<proof_id>/` (RFC-0005). Because `/io` is a host bind mount, the harness observes the rename directly from the host.

```python
@dataclass(frozen=True, slots=True)
class Release:
    proof_id: str
    mono_ns: int

class ReleaseWatcher:
    def __init__(self, proofs_dir: Path, poll_interval_s: float = 0.010) -> None: ...
    def start(self) -> None: ...              # before the prove call starts
    def stop(self) -> list[Release]: ...      # after the prove call ends; ordered by mono_ns
    @property
    def mechanism(self) -> Literal["inotify", "poll"]: ...
    @property
    def observable(self) -> bool: ...         # false when releases are not distinguishable (W-4)
```

- W-1. On Linux, the watcher uses `inotify` via `ctypes` (`inotify_init1` and `inotify_add_watch` with `IN_MOVED_TO | IN_ONLYDIR`) in a dedicated thread, avoiding any third-party package dependency. Each release is timestamped with `monotonic_ns()` as soon as the event is read.
- W-2. Where `inotify` is unavailable, the watcher falls back to polling `os.scandir` every 10 ms and timestamps each newly appearing non-`.tmp-` directory on the first poll that sees it. `mechanism` records which mode was active; under polling, release timing error is bounded by one poll interval plus OS scheduling delay.
- W-3. If a proof directory appears directly without going through `.tmp-`, the watcher still accepts it but logs a `release.nonatomic` event. If any proof file changes size between release and the end of the `prove` call, the job fails with kind `adapter`.
- W-4. `observable` is false if `system.yaml` sets `incremental_proofs: false`, or if all k releases arrive in a single `inotify` read batch or a single poll interval. In that case `prove.steady` is recorded as null with `not_externally_observable` (RFC-0004 INV-SCOPE-3).
- W-5. Any proof released after the `prove` container has exited is treated as an `adapter` error, since the adapter must finish writing all proofs before exiting.

### GPU sampler

```python
@dataclass(frozen=True, slots=True)
class GpuSample:
    mono_ns: int
    memory_used_mib: float
    util_gpu_pct: int
    energy_mj: int | None

@dataclass(frozen=True, slots=True)
class SamplerSummary:
    samples: int
    target_hz: float
    achieved_hz: float
    gaps_over_150ms: int
    gap_fraction: float            # time in gaps / call duration
    max_gap_ms: float
    degraded: bool                 # gap_fraction > 0.05
    memory_peak_mib: float
    memory_baseline_mib: float
    util_mean_pct: float
    util_p95_pct: float
    energy_j: float | None
    anon_peak_bytes: int           # from CgroupReader.memory_anon, same thread

class Sampler:
    def __init__(self, gpu_index: int | None, cgroup: CgroupReader, target_hz: float = 20.0) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> SamplerSummary: ...
    def write_trace(self, path: Path) -> None: ...   # 1 Hz downsampled trace (max per second), CSV
```

- S-1. Each call uses one sampler thread started before `start_ns` and stopped after `end_ns`. Any samples falling outside `[start_ns, end_ns]` are excluded from the summary.
- S-2. Sampling follows absolute deadlines `t0 + i × period`. If a deadline is missed, the sampler skips ahead rather than bursting to catch up, so stalls appear honestly as gaps.
- S-3. On each tick, the sampler queries only the bound GPU (`nvmlDeviceGetHandleByIndex(bound_index)`) for `nvmlDeviceGetMemoryInfo().used` and `nvmlDeviceGetUtilizationRates().gpu`, and reads `nvmlDeviceGetTotalEnergyConsumption()` (in mJ) once at the start and once at the end. On every second tick (10 Hz), the same loop reads `anon` memory from the cgroup reader.
- S-4. `memory_peak_mib` is the maximum `used` value recorded during the call; the pre-call `used` reading is saved as `memory_baseline_mib` and is not subtracted. Mean GPU utilisation is time-weighted over the sample intervals, and `util_p95_pct` is the 95th percentile computed via the nearest-rank method.
- S-5. Any interval longer than 150 ms between consecutive samples counts as a gap. If gaps account for more than 5 % of the call duration, the step's GPU metrics are flagged with `degraded: true` inside the quantity's `quality` object (RFC-0012), and the site displays that flag.
- S-6. Energy reporting is optional: if `nvmlDeviceGetTotalEnergyConsumption` returns `NVML_ERROR_NOT_SUPPORTED`, energy metrics are stored as null with `null_reason: not_applicable`.
- S-7. Foreign-process check: before `info` and before every GPU step, `nvmlDeviceGetComputeRunningProcesses` on the bound GPU MUST return an empty list; otherwise the job fails with kind `environment` (RFC-0006 PC-GPU-BUSY). The check runs again after each GPU step, and if a foreign process appears during the step, the harness marks the step's GPU metrics `degraded: true` and logs `gpu.foreign_process`.
- S-8. Because `verify` runs without a GPU, its sampler starts with `gpu_index=None` and tracks only the cgroup anonymous memory peak.

### Proof size accounting

```python
def proof_bytes(proof_dir: Path, io_root: Path) -> int: ...
def files_bytes(paths: Sequence[str], io_root: Path) -> int: ...
```

- Z-1. `proof_bytes` sums `st_size` across all regular files inside `/io/proofs/<proof_id>/`. Encountering symlinks, device nodes, or paths resolving outside `io_root` immediately fails the job with kind `adapter` (see trust boundaries in `docs/spec/06-security.md`).
- Z-2. `verifier_download_bytes` equals `files_bytes(commit.out.verifier_files)`, representing the per-commitment data a verifier fetches once, while `prover_keep_bytes` equals `files_bytes(commit.out.prover_files)`.
- Z-3. All sizes are measured in uncompressed on-disk bytes. Each part file's SHA-256 digest is computed during the same pass for both the proof digest (RFC-0012) and `digests.txt` (RFC-0009).

### Measurement overhead budget

The following operational targets (not benchmark results) are verified by the calibration self-test and by GPU-host test GH-OVERHEAD:

| Item | Target |
|---|---|
| Combined sampler and watcher CPU use | At most 1 % of one logical CPU at 20 Hz, pinned to the harness CPU (C-3) |
| Sampling jitter | p99 deadline lateness at most 10 ms |
| Harness resident memory | At most 256 MiB during a container call |
| Trace file size | 1 Hz downsampled CSV trace staying within the 1 MiB per-file log cap (RFC-0009) for calls up to 6 hours |

Because the harness is pinned off the prover and verifier CPUs (C-3), its CPU and memory footprint stays out of the job's cgroup counters.

### Calibration self-test

A host runs `iproofs machine-record --selftest` before its first run of a release and before each run campaign, storing the resulting JSON in `manifest.json` under `self_test`. Any run whose manifest lacks a passing self-test from the same harness version is ineligible for release publication (RFC-0014 §Eligibility). The self-test executes seven checks:

| Check id | Procedure | Pass when |
|---|---|---|
| ST-CLOCK | Perform 100,000 consecutive `monotonic_ns()` reads | Readings never decrease and the median step is at most 1 µs |
| ST-SAMPLER | Run the GPU sampler for 5 s at 20 Hz on the bound GPU | Achieved rate is at least 10 Hz with no gap over 150 ms |
| ST-JITTER | Evaluated on the same 5 s run | p99 deadline lateness is at most 10 ms |
| ST-CGROUP | Launch the pinned `systems/fake` probe container (`probe` subcommand, reserved for the self-test) inside a harness slice; it allocates and touches 256 MiB of anonymous memory | Both the slice's `memory.peak` and the sampled anonymous peak are at least 256 MiB, and `cpu.stat` increases |
| ST-WATCH | Probe container renames 3 directories 200 ms apart inside a bind mount | All 3 releases are observed via `inotify`, with consecutive intervals within 200 ms ± 20 ms |
| ST-NVML | Initialise NVML, acquire the bound GPU handle, and run the busy check | No foreign compute process is present; energy-counter support is recorded |
| ST-OOM | Probe container allocates past a 64 MiB memory limit | An `oom_kill` delta is detected in the slice |

If any check fails, the command exits 3 (`environment`) and reports the failing check id.

Under hosted execution (RFC-0006 §Hosted execution), `iproofs machine-record --selftest --hosted` runs the `systems/fake` `probe` entrypoint as a regular child process inside the harness container rather than in a nested Docker container. ST-CLOCK, ST-NVML, ST-SAMPLER, and ST-JITTER behave identically. ST-CGROUP passes if the container's sampled `memory.stat` `anon` rises by at least 256 MiB above its pre-probe baseline and `cpu.stat` increases; the container's `memory.peak` spans the container's full lifetime and is not read. ST-WATCH also runs against the child process. ST-OOM is skipped and omitted from the record because the container cannot impose a sub-container memory limit on a child process, though OOM kills during actual hosted jobs are still read from the container's `memory.events` (RFC-0006).

### Portability

On non-Linux machines and in hosted CPU CI (fake system only), the watcher uses polling, the sampler runs with `gpu_index=None` (no NVML), and a null cgroup reader emits `null` host-memory and CPU metrics with `null_reason: not_applicable`. Runs produced this way are useful for development and testing, but cannot enter `results/` for a release because validation requires a passing Linux-plus-NVML self-test.

### Failure modes

| Failure | Response |
|---|---|
| Slice cannot be created (no systemd or insufficient privileges) | Conformance check fails with `environment`, exit 3 |
| Container exits before the sampler collects its first sample | Summary records `samples: 0`; GPU metrics are null with `step_failed` if the call failed, or marked `degraded: true` otherwise |
| NVML call fails mid-step | Sample is skipped and counted as a gap; after 10 consecutive errors the sampler stops and marks GPU metrics `degraded: true` |
| OOM kill | Step fails with kind `resource` (G-6) |
| Timeout | Harness calls `docker kill`, records `timeout`, and still reads final counters (T-2) |
| Proof symlink or path traversal outside `io_root` | Job fails with kind `adapter` (Z-1) |
| Release after container exit, or proof file mutated after release | Job fails with kind `adapter` (W-3, W-5) |
| Foreign GPU process detected before a step | Job fails with kind `environment` (S-7) |
| Orphaned placeholder unit left behind after a crash | The next `iproofs run` stops stale `iproofs-*-hold` units prior to conformance and logs `cgroup.stale_cleanup` |

## Alternatives Considered

- **Use `docker stats` for memory and CPU.** While this would eliminate custom cgroup code, `docker stats` samples at roughly 1 Hz, bundles page cache into memory usage, does not report a true peak, and stops reporting as soon as the container exits.
- **Sample `memory.peak` directly from the container's own cgroup until exit.** Skipping the placeholder slice would be simpler, but both the final peak memory and the final CPU time slice would be lost when the container's cgroup vanishes on exit. Keeping a parent slice alive costs only one `sleep` process, whose tiny footprint is recorded in `baseline_bytes`.
- **Use `--cgroupns` with a cgroupfs driver and harness-managed directories.** Although lighter than systemd, most Linux Docker hosts default to the systemd cgroup driver, and mixing drivers on one host is unsupported. Standardising on a single tested mechanism avoids host-specific divergence.
- **Trust per-proof timestamps reported by the adapter.** Doing so would avoid writing a watcher, but it would make release times depend on code inside the container, conflicting with PRD F9. The atomic rename contract adds just one `rename` call to each adapter.
- **Run the sampler in a separate subprocess instead of a thread.** A subprocess would sidestep Python's GIL completely, yet in v0.1 the main thread spends its time blocked in `wait` and NVML calls release the GIL. ST-JITTER catches any host where that assumption breaks, and moving to a subprocess later would not change any record format.
- **Use DCGM instead of NVML.** DCGM provides richer telemetry, but running an extra host daemon is unnecessary when NVML already supplies every counter v0.1 needs.

## Drawbacks

- Running `systemd-run` and Docker requires root or equivalent host privileges on the GPU machine.
- Container start-up time is included in every timed step, which can be a noticeable fraction of short `verify` calls (made visible via `info_seconds`).
- Anonymous host memory peak is sampled and can therefore miss spikes shorter than 100 ms (see RISK above).
- Under fallback polling, release timestamps carry up to 10 ms of uncertainty, recorded via `mechanism`.

## Migration / Rollout

This RFC replaces the high-level measurement table in Section 4 of the initial SPEC with concrete mechanisms, splitting "host memory peak, file cache excluded" into two explicitly labelled metrics. It adds `events`, per-step `sampler` summaries, `watcher.mechanism`, `selftest`, and quantity `quality.degraded` to `run/1` and `manifest/1` (RFC-0012). Adapters take on one new requirement, atomic proof directory renames (RFC-0005), implemented first in `systems/fake`.

Amendment of 2026-11-09 (RFC-0015 SRV-6 production serving): When multiple GPUs are bound, the sampler aggregates them via `iproofs.measure.ManyGpus`. At each tick, memory used is the maximum across the bound GPUs and utilisation is their mean, so `<step>_gpu_memory_peak` is the maximum over both GPUs and samples, `<step>_gpu_util_mean` and `_p95` summarise the per-sample means, and `<step>_gpu_energy` sums energy across all bound GPUs. Storing per-GPU readings in `raw` is deferred to a later change. Unbound visible GPUs are queried solely for RFC-0006 PC-GPU-IDLE when capturing the machine record and contribute to no metric. Production-serving runs require `mechanism: inotify` from the release watcher (RFC-0015 SRV-1); falling back to polling fails the job with `environment`.

## Testing Strategy

CPU-only tests (hosted CI):

- TC-SPAN: verifies exact integer-to-second conversion in `span_seconds`.
- TC-WATCH-POLL: renames 5 `.tmp-` directories 50 ms apart in a temporary directory and asserts that the polling watcher returns 5 ordered releases, each within 50 ms ± 15 ms of the previous one.
- TC-WATCH-INOTIFY (Linux runners): runs the same test using `inotify` with a ± 5 ms tolerance.
- TC-WATCH-BURST: performs 5 renames within 1 ms and asserts `observable` is false.
- TC-WATCH-DECLARED: verifies that `incremental_proofs: false` forces `observable` to false regardless of actual release spacing.
- TC-WATCH-NONATOMIC: creates a proof directory directly with `mkdir` and verifies that the release is accepted while logging `release.nonatomic`.
- TC-WATCH-MUTATED: appends bytes to a proof part after release and verifies an `adapter` failure.
- TC-SAMPLER-GAPS: uses a fake NVML backend that stalls for 400 ms twice during a 20 s call (4 % gap fraction) to assert `gaps_over_150ms == 2` and `degraded == False`, then stalls 10 times to assert `degraded == True`. (Note that two 400 ms stalls in a 5 s call would equal 16 %, exceeding the S-5 threshold.)
- TC-SAMPLER-P95: feeds a synthetic utilisation series 1..100 and asserts that nearest-rank p95 equals 95.
- TC-SAMPLER-ENERGY-UNSUPPORTED: stubs NVML to raise not-supported and verifies null energy with `not_applicable`.
- TC-CGROUP-PARSE: parses fixture `memory.stat`, `cpu.stat`, and `memory.events` files into exact integers.
- TC-PROOF-BYTES: tests fixture proof directories, asserting exact byte totals and verifying that symlinks and `..` traversals fail with `adapter`.
- TC-FOREIGN-PROC: stubs NVML to report one active compute process and verifies an `environment` failure before `info`.

GPU-host tests (runbook, outside hosted CI):

- GH-SELFTEST: verifies that `iproofs machine-record --selftest` passes on `prover-h100`.
- GH-CGROUP-EXACT: runs a probe container that allocates 1 GiB of anonymous memory and exits immediately, confirming that the slice's `memory.peak` remains at least 1 GiB after exit.
- GH-OVERHEAD: runs a 30-minute fake `prove` call and confirms harness CPU stays at or below 1 % of one logical CPU with p99 lateness at or below 10 ms.
- GH-NVML-PEAK: runs a CUDA probe allocating 40 GiB on the bound GPU for 2 s and confirms `memory_peak_mib` is at least 40,960.

## Decisions

- Q1. Verification calls executed on a separate verifier host use the exact same systemd slice mechanism, and that host must pass the same calibration self-test.
- Q2. Each adapter declares `incremental_proofs` from upstream documentation; the first GPU-host run confirms the setting, and a pull request updates it if observed behaviour differs.

## References

- `docs/PRD.md` §7 (F9), §11.
- [RFC-0004](0004-metrics-timing-grades.md) for metric ids and scopes; [RFC-0005](0005-adapter-contract.md) for the proof directory contract; [RFC-0006](0006-reference-hardware-and-cost.md) for CPU binding and conformance; [RFC-0009](0009-results-and-publication.md) for log caps; [RFC-0010](0010-harness-runner.md) for steps, timeouts, and error kinds; [RFC-0012](0012-schemas-and-serialization.md) for `run/1` fields.
- Linux kernel documentation for cgroup v2 (`memory.peak`, `memory.stat`, `cpu.stat`, `memory.events`) and `inotify(7)`.
- NVIDIA Management Library API reference (`nvmlDeviceGetMemoryInfo`, `nvmlDeviceGetUtilizationRates`, `nvmlDeviceGetTotalEnergyConsumption`, `nvmlDeviceGetComputeRunningProcesses`).
