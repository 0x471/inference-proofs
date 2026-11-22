# 04. Error model

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). The normative error taxonomy is defined in [RFC-0010 §Error taxonomy](../../rfcs/0010-harness-runner.md#error-taxonomy) and implemented in `harness/src/iproofs/errors.py`; this section summarises the taxonomy and catalogues failure modes across the system.

## Principles

1. **A failure is a result.** Every failed job is written to a run directory with its failure record and counted in `n_failed`. Failed runs are never deleted or retried until they succeed ([AGENTS.md hard rule 5](../../AGENTS.md#hard-rules), PRD N3).
2. **Fail before measuring, not during.** Preconditions that can be checked ahead of time (schemas, file hashes, and image digests) are validated before any timed step begins, avoiding wasted GPU time and partial measurements. Profile conformance is checked and logged, but never blocks execution.
3. **Verdicts are not errors.** `accept`, `reject`, `no_verdict`, and `invalid_call` are valid outcomes of a `verify` call. An adapter error occurs only when the adapter fails to return one of these verdicts.
4. **One closed taxonomy.** Every failure maps to a single `ErrorKind`. Adding a new kind requires updating both RFC-0010 and `errors.py` together.
5. **No silent degradation.** When a measurement is incomplete (such as sampler gaps or an unobservable proof release), the resulting quantity is marked `degraded` or set to null with an explicit `null_reason`, never interpolated or guessed.

## Error kinds

| Kind | Meaning | Typical step | CLI exit |
|---|---|---|---|
| `config` | An input file or CLI argument is invalid | Before jobs, `resolved` | 1 or 2 |
| `environment` | A required runtime dependency is missing (for example NVML on a GPU profile, or a lock held by another runner). RFC-0006 profile conformance checks PC-* (`iproofs.provenance.check_profile`) are recorded in the manifest and never raise this error | Before jobs, `machine_recorded` | 3 |
| `integrity` | A file hash, image digest, or commit pin does not match | `resolved`, `image_ready`, `info` | 4 (during a job), 1 (in `validate`) |
| `fetch` | A network download failed after 3 attempts | `resolved`, `image_ready` | 4 |
| `adapter` | The adapter exited non-zero or violated the adapter contract | Any adapter step | 4 |
| `timeout` | A step exceeded its wall-clock limit | Any adapter step | 4 |
| `resource` | The container was OOM-killed or the disk filled up | Any adapter step | 4 |
| `policy` | A weakening flag or control configuration appeared outside a control job | `prove`, `validate` | 4 (in `run`), 1 (in `validate`) |
| `internal` | A harness bug occurred or the runner process was interrupted | Any | 5 |

Every failure record has the structure `{kind, step, message, exit_code, last_lines[], at}` ([RFC-0010 §Failure record](../../rfcs/0010-harness-runner.md#failure-record)), where `last_lines` contains up to the last 50 redacted lines of adapter stderr ([05-observability §Redaction](05-observability.md#redaction)).

## Failure-mode catalogue

Each row describes a failure condition, how the system detects and handles it, and how it is recorded. "Run failed" means the job reaches the `written` state with `status: "failed"` and the specified error kind.

| # | Failure | Detection | Response | Recorded as |
|---|---|---|---|---|
| 1 | Workload, system, reference, or target file fails schema validation | `iproofs.schema` check on load | Abort before starting any job | `config`, exit 1 (`validate`) or 2 (`run`) |
| 2 | Workload is not listed in `system.yaml` `workloads` | Runner check at `resolved` | Abort before starting any job | `config`, exit 2 |
| 3 | Unquoted YAML date or ambiguous scalar | Schema type check | Reject the file | `config` |
| 4 | Model download fails (network error, 5xx, rate limit) | Exception in fetcher | Retry 3 times with backoff of 2 s, 8 s, and 32 s, then fail | `fetch`, run failed at `resolved` |
| 5 | Gated model licence not accepted or `HF_TOKEN` missing | HTTP 401 or 403 from source | Do not retry | `fetch` naming the model; token is never logged |
| 6 | Weight file hash does not match the workload definition | SHA-256 check before mounting into any container | Delete the downloaded file and fail | `integrity` at `resolved` |
| 7 | Prompt corpus bytes do not match `corpus.yaml` digest | SHA-256 check | Fail | `integrity` at `resolved` |
| 8 | Container image digest does not match `system.yaml` | `docker image inspect` | Fail | `integrity` at `image_ready` |
| 9 | `info` subcommand reports an upstream commit different from `system.yaml` | Field comparison | Fail | `integrity` at `info` |
| 10 | Unpinned reference (abbreviated commit hash or mutable tag) | Pin validation | Reject in CI and refuse to run | `integrity`, exit 1 |
| 11 | cgroup v1, kernel below 5.19, Docker below 25.0, or toolkit below 1.17 | Environment probe | Record nonconformance and continue | Manifest `harness.nonconforming: true` |
| 12 | Host falls short of profile requirements (GPU model, NUMA CPUs, memory, disk) | Machine record check against profile | Record nonconformance and continue | Manifest `harness.nonconforming: true` |
| 13 | Another compute process is running on the bound GPU | NVML process list check before each job | Record nonconformance and continue | Manifest profile checks |
| 14 | Another runner holds the lock on the results tree | `flock` on `results/.runner.lock` or active staging directory | Abort | `environment`, exit 3 |
| 15 | Adapter subcommand exits non-zero | Container exit code | Mark run failed and proceed to the next repetition | `adapter` with exit code and trailing stderr lines |
| 16 | `out.json` is missing, malformed JSON, or invalid under `adapter-out/1` | Parse and schema validation | Mark run failed | `adapter`; raw file preserved in `logs/` |
| 17 | `out.json` `contract` or `subcommand` does not match the job | Field check | Mark run failed | `adapter` |
| 18 | Proof listed in `out.json` was not released, or a released proof was not listed | INV-ADAPTER-6 check | Mark run failed; digest any released proofs anyway | `adapter` |
| 19 | Path in `out.json` escapes `/io`, or a proof contains a symlink or device file | Host-side path resolution | Mark run failed | `adapter` naming the offending path |
| 20 | Proof part exceeds 64 GiB or total parts exceed 10,000 | Size and count validation | Mark run failed | `adapter` |
| 21 | Declared tokens covered do not match workload shape | INV-ADAPTER-7 check | Mark run failed | `adapter` |
| 22 | Leftover `.tmp-*` directory remains in proofs after `prove` | Directory scan | Ignore and exclude from proof count | Warning event `proof.tmp_left` |
| 23 | Step exceeds its wall-clock timeout | Harness timer (`iproofs.measure.timed_call`) | Send `docker kill --signal KILL`, wait up to 30 s, remove container, mark run failed, emit `step.timeout`, and do not retry | `timeout` |
| 24 | Container killed by OOM killer | `docker inspect` `State.OOMKilled` after non-zero exit (`timed_call`) | Mark run failed and emit `step.oom` | `resource` |
| 25 | Disk runs out of space while writing proofs or records | `OSError` with `ENOSPC` during a job state (`Runner.run`) | Mark run failed and retain staging directory for inspection | `resource` |
| 26 | NVML sampling gap exceeds 150 ms | Sampler timestamps | Tally gap duration; if gaps exceed 5 %, mark GPU metrics `degraded: true` | Quantity `degraded` flag and `sampler.gap` event |
| 27 | NVML is unavailable on a GPU profile | NVML initialisation error | Abort before starting the job | `environment` |
| 28 | Container cgroup files cannot be read | File read error | Set host memory and CPU time to null with `null_reason: "missing_input"` | Event `sampler.cgroup_unavailable` |
| 29 | All proofs are released together with no observable steady window | Release timestamps fall within one poll interval, or `steady_boundary: not_observable` | Set `prove.steady` to null | `null_reason: "not_externally_observable"` |
| 30 | Session contains fewer than two proofs | Proof count check | Set `prove.steady` to null | `null_reason: "fewer_than_two_proofs"` |
| 31 | `verify` returns a verdict outside the four allowed values | Schema validation | Mark that verify call failed | `adapter`; row or control outcome recorded as `error` |
| 32 | Honest `verify` call returns `reject` or `no_verdict` | Per-proof verdict | Record in the run and reflect in acceptance counts | Verdict counts in `run.json` |
| 33 | Forbidden flag used outside a control job | Adapter refusal or CI policy scan of `commands.jsonl` | Mark run failed or block pull request | `policy` |
| 34 | Control job appears among a release's measured rows | CI check on manifest `control` flag | Block pull request | `policy`, exit 1 |
| 35 | Honest twin of a negative control is not accepted | Twin verdict check | Mark control `void` | Control outcome `void` |
| 36 | Negative control accepted when rejection was expected | Outcome classification | Follow private disclosure and embargo process | `disclosure_pending: true` in `controls.json` |
| 37 | Control mutation produces bytes identical to original input | Assertion in `iproofs.controls` | Mark control `error` | `internal` |
| 38 | Stored derived quantity differs from recomputed value | `iproofs derive --check` | Block pull request | Exit 1 |
| 39 | Quantity omits unit, grade, tier, source, or required timing scope | Label validation | Block pull request | Exit 1 |
| 40 | Committed JSON is not byte-identical to canonical re-serialization | Format check | Block pull request | Exit 1 |
| 41 | Merged run directory is modified or deleted | CI diff check on `results/` | Block pull request | Exit 1 |
| 42 | Secret or host identifier detected in a committed file | Secrets scan | Block pull request | Exit 1 |
| 43 | Runner killed or host loses power mid-job | Stale staging directory found on next startup | Write incomplete job as failed and never resume it | `internal` at the last reached step |
| 44 | Harness generates a document that fails its own schema | Validation at `written` | Mark run failed and keep invalid file in `logs/invalid/` | `internal`, exit 5 |
| 48 | Reference row cannot run on the profile (for example, model does not fit in memory) | Adapter failure or declared infeasibility | Record run as failed and set overhead to null | Failed run record; overhead `null_reason: "missing_input"` |
| 49 | No perturbed commitment is available for the workload (no tensor with at least 1,024 elements, adapter cannot commit the perturbed copy, or weights are absent on this host) | `iproofs controls --prepare-perturbed`; `_perturbed` lookup at control time | Mark C3 and P1 `not_applicable` with the reason | `config` exit 2 from `--prepare-perturbed`; control note |

## Recovery rules

- **Before measurement:** Network `fetch` failures retry up to three times; all other precondition failures stop the job or invocation immediately.
- **During measurement:** Steps are never retried. The runner records the failure and continues with the next repetition ([RFC-0010 §Retry policy](../../rfcs/0010-harness-runner.md#retry-policy)).
- **After a crash:** On startup, `iproofs run` calls `Runner.recover` to convert any stale staging directory into a failed run (`ErrorKind.internal`, recording the last reached state, message `runner terminated before completion`, and event `runner.recovered`) rather than resuming it ([RFC-0010 §Crash recovery](../../rfcs/0010-harness-runner.md#crash-recovery)). If a staging directory belongs to a runner still alive on the current boot, `iproofs run` exits with code 3.
- **In CI:** Every check failure blocks merge with no override flag. If a maintainer believes a check is wrong, they update the check via pull request.

## Error messages

Error messages should be a single clear sentence identifying the file, field, or step along with expected and actual values whenever safe to print (such as hashes, versions, or counts). They never expose secrets, hostnames, IP addresses, or absolute home paths; the same redaction pipeline applies to error messages as to log output.
