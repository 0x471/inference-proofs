# 05. Observability

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). The logging and redaction rules here are normative for the harness; measurement methods and sampling live in [RFC-0011](../../rfcs/0011-measurement-and-sampling.md).

## Scope

The benchmark's primary output is its measurement data, specified in RFC-0004 and RFC-0011. This section covers the surrounding diagnostic artifacts: what the harness logs, in what format, what it redacts, what progress it prints to the terminal, and how a reader can debug a failed or unexpected run using the run directory alone. There is no external tracing backend or metrics server; a job's steps act as its spans, and the run directory is the sole output sink.

## Log files

Every job writes the following files inside its run directory:

| File | Content | Writer |
|---|---|---|
| `logs/harness.jsonl` | Structured harness events, one JSON object per line | Harness |
| `logs/<step>.stdout`, `logs/<step>.stderr` | Redacted container stdout and stderr for each step | Harness (captured) |
| `logs/commands.jsonl` | Upstream command lines invoked by the adapter ([RFC-0005 §Command log](../../rfcs/0005-adapter-contract.md#command-log)) | Adapter, copied by harness |
| `logs/invalid/` | Documents that failed schema validation, preserved for debugging | Harness |

Size caps (INV-OBS-1): each individual log file is capped at 1 MiB. When a file exceeds that limit, the harness retains the first 256 KiB and the last 768 KiB, inserting `[iproofs: <k> bytes omitted, full digest in digests.txt]` between them. The entire run directory is capped at 10 MiB; if needed, the harness trims the largest adapter output files further first ([RFC-0009 §Storage](../../rfcs/0009-results-and-publication.md#storage)). Adapter output is captured through bounded buffers (`iproofs.measure.Capture`) so a runaway adapter cannot exhaust memory or disk. The SHA-256 digest of each complete stream (before redaction and truncation) is recorded in `digests.txt` under `logs/<step>.<stream>`, and every other log file is hashed before any truncation. Whenever truncation occurs, the harness emits a `log.truncated` event recording how many bytes were omitted. Running `iproofs controls RUN_DIR` appends its verification output as `logs/controls-verify.*`.

## Event format

Structured logging is implemented in `harness/src/iproofs/log.py` (`JsonlLogger`, `Event`), and a unit test verifies that its `Event` constants match the catalogue below.

Each line in `logs/harness.jsonl` is serialized through the single canonical JSON writer ([RFC-0012](../../rfcs/0012-schemas-and-serialization.md)) as a compact single-line object (no indentation):

```json
{"ts": "2026-11-03T10:15:02.118Z", "mono_ns": 81234567890123, "level": "info",
 "event": "step.end", "job": "2026-11-03-fake-fake-tiny-ci-ci-cpu-1", "step": "prove",
 "exit_code": 0, "seconds": 4.812}
```

| Field | Type | Meaning |
|---|---|---|
| `ts` | String, RFC 3339 UTC, millisecond precision | Wall-clock timestamp for human readers and cross-file correlation only |
| `mono_ns` | Integer | `time.monotonic_ns()`, the sole clock used for computing durations |
| `level` | `debug`, `info`, `warning`, `error` | Log severity |
| `event` | String from the catalogue below | Event identifier |
| `job` | Run ID or null | Job that emitted the event |
| `step` | State name or null | Current job state |
| Additional fields | Event-specific | Event payload |

Rules:

- **INV-OBS-2:** Durations printed in logs are diagnostic only; all published metrics come strictly from `run.json`.
- **INV-OBS-3:** Event names remain stable within a harness minor version, and any renamed event is noted in `CHANGELOG.md`.
- **INV-OBS-4:** Every log line passes through the redactor before being written to disk.

## Events catalogue

| Event | Level | Fields | Emitted when |
|---|---|---|---|
| `runner.start` | info | `harness_version`, `argv` (redacted) | `iproofs run` begins |
| `runner.recovered` | warning | `run_id`, `last_state` | A stale staging directory is finalized as a failed run |
| `job.state` | info | `from`, `to` | Every job state transition |
| `job.failed` | error | `kind`, `message`, `exit_code` | A job failure is recorded |
| `job.written` | info | `run_dir`, `outcome` | The run directory is atomically renamed into place |
| `fetch.attempt` | info | `what`, `attempt`, `backoff_s` | Each network download attempt |
| `fetch.failed` | error | `what`, `attempts` | All fetch retries have been exhausted |
| `integrity.ok` | debug | `what`, `digest` | A hash verification succeeds |
| `integrity.model_rehash` | info | `what`, `seconds` | Cached weights are rehashed at job start outside all timed scopes (diagnostic only, never published; RFC-0014) |
| `integrity.mismatch` | error | `what`, `expected`, `actual` | A hash verification fails |
| `env.probe` | info | `kernel`, `cgroup`, `docker`, `toolkit` | Host environment prerequisites are probed |
| `env.gpu_busy` | error | `process_count` | Another compute process is detected on the bound GPU |
| `gpu.foreign_process` | warning | `process_count` | Another compute process appears on the bound GPU during a GPU step, marking that step's GPU metrics `degraded: true` (RFC-0011 S-7) |
| `cpuset.selected` | info | `cpus`, `mems`, `smt` | A CPU set is chosen for a step |
| `step.start` | info | `subcommand`, `image`, `timeout_s` | Immediately before invoking `docker run` |
| `step.end` | info | `exit_code`, `seconds` | Immediately after the container exits |
| `step.timeout` | error | `timeout_s` | A step hits its wall-clock timeout and the container is killed |
| `step.oom` | error | | Container termination was caused by an OOM kill |
| `proof.released` | debug | `proof_id`, `release_mono_ns`, `index`, `of` | The release watcher detects an atomic proof directory rename |
| `proof.tmp_left` | warning | `name` | A leftover `.tmp-*` directory remains after `prove` finishes |
| `sampler.start` | debug | `kind`, `hz` | A resource sampler thread starts |
| `sampler.gap` | warning | `kind`, `gap_ms` | The interval between consecutive samples exceeds 150 ms |
| `sampler.cgroup_unavailable` | warning | `path` | Container cgroup counter files cannot be read |
| `policy.warning` | warning | `detail` | `prove` output echoes the commitment ([RFC-0014 §The commitment record](../../rfcs/0014-provenance-and-integrity.md#the-commitment-record) rule 5); the run continues |
| `cgroup.stale_cleanup` | warning | `units` | Leftover placeholder scopes from a crashed runner are stopped before conformance checks (RFC-0011 §Cgroup accounting) |
| `verify.result` | info | `proof_id`, `verdict`, `raw_exit_code`, `cpus`, `index`, `of` | After each `verify` call completes |
| `control.call` | info | `control` (`twin` for an honest twin), `trial` (null for a prove), `subcommand`, `exit_code`, `seconds` | After each control `verify` or `prove` call finishes, giving progress on long suites and preserving timing if a split part is interrupted (RFC-0008 §Split suites) |
| `control.trial` | info | `control`, `trial`, `outcome` | After each control trial finishes |
| `control.twin_mismatch` | warning | `control`, `twin_verdict` | An honest twin is not accepted, marking the control `void` (`iproofs.controls.control_record`) |
| `control.disclosure_pending` | warning | `control` | A control is accepted when rejection was expected |
| `log.truncated` | info | `file`, `elided_bytes` | A log file hits its size cap and is truncated |
| `validate.fail` | error | `check`, `path`, `message` | A CI validation check fails during `iproofs validate` |

## Redaction

Redaction runs on every log line, every captured adapter stream, every failure message, and every `last_lines` entry before anything is written to disk (INV-OBS-4). It is implemented in `iproofs.log.redact.Redactor`, sharing the compiled pattern list in `iproofs.log.patterns` with CI gate G9. Matched text is replaced with a fixed class marker such as `<redacted:token>`.

| Class | Rule |
|---|---|
| Secrets in environment | Values at least 8 characters long from `HF_TOKEN` or any environment variable matching `(?i)(token\|key\|secret\|password\|credential)` are replaced wherever they appear |
| IP addresses | Dotted-quad IPv4 addresses and RFC 4291 text-form IPv6 literals |
| Host name | Both `socket.gethostname()` and its leading hostname label |
| Home paths | The absolute path of the current user's home directory is replaced with `~` |
| MAC addresses | Six hex octets separated by colons or hyphens |
| GPU identifiers | NVIDIA GPU UUIDs (`GPU-` followed by a UUID) and board serial numbers queried from NVML at startup |

The harness never dumps the full process environment or raw `docker inspect` JSON, and never records account names, SSH configuration, or cloud instance IDs. Host details are limited strictly to the machine record fields listed in [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md). As a second layer of protection, CI gate G9 ([RFC-0013](../../rfcs/0013-validation-and-ci.md)) scans every committed file with the same patterns.

## Progress output

While a job runs, human-readable progress updates are printed to stderr at each state transition and proof release, for example:

```
[rep 2/3] prove   running   00:41:12  proofs 61/120
[rep 2/3] prove   done      01:22:40  exit 0
[rep 2/3] verify  proof 7/120 accept
[rep 1/1] controls verify C2 trial 0  01:02:13  exit 0  3732 s
```

Passing `--quiet` suppresses stderr progress. Progress output is purely a formatted view of events already written to `harness.jsonl`: `iproofs.log.Progress` renders lines from `job.state`, `proof.released`, `verify.result`, `control.call`, `job.failed`, and `job.written`. Consequently, any event filtered out by `--log-level` (such as `proof.released`, which logs at `debug`) also omits its progress line.

## No telemetry

The harness transmits no telemetry off the host: there is no usage tracking, crash reporting, or update checking. Network requests occur only during explicit fetch steps (downloading model weights, prompt corpora, or pinned container images) against the public sources listed in workload and system files.

## Diagnosing a run

Anyone inspecting a run directory on its own can trace what happened in six steps:

1. **Did the run fail, where, and why?** Check `status` and `failure` (kind, step, exit code, and `last_lines`) in `run.json`.
2. **What exact configuration ran?** Check `manifest.json` for the container image digest, upstream commit, workload and prompt digests, job seed, machine record, and command lines.
3. **What did the adapter do?** Read `logs/<step>.stderr` and `logs/commands.jsonl`.
4. **When did each step and proof occur?** Inspect `step.start`, `step.end`, and `proof.released` events in `harness.jsonl`.
5. **Are the measurements intact?** Look for `sampler.gap` events, `degraded` flags on GPU metrics, and `null_reason` fields on null quantities.
6. **What did the verifier report?** Inspect `verifier/<proof_id>.json` for each verdict, raw exit code, and trailing line, and check `controls.json` for negative-control results.

If a run failure cannot be diagnosed from these files alone, treat the gap as a logging bug in the harness and open an issue.
