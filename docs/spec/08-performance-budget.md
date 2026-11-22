# 08. Performance budget

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). Normative decisions live in the RFCs under [rfcs/](../../rfcs/README.md); if this section disagrees with an RFC, the RFC takes precedence.

This section establishes performance targets for the benchmark's own tooling: harness measurement overhead, CPU-only utilities (validation, derivation, site generation, and CI), and the method for projecting GPU budgets before a run campaign. It does not define performance targets for measured provers, as the project publishes no system targets (RFC-0009 §Targets). Every figure below is a software **target** rather than an empirical measurement, so it carries no grade or evidence tier.

## Why budgets exist here

Two kinds of overhead matter. First, measurement interference: if the harness consumes noticeable CPU time, memory bandwidth, or scheduling slots during a timed step, it distorts the metrics it reports. Second, contributor friction: if local validation or CI grows slow, contributors skip running checks locally and broken files reach `results/`. Both concerns are bounded below, with a concrete check attached to each budget.

## Harness measurement overhead

Owner: [RFC-0011 §Measurement overhead budget](../../rfcs/0011-measurement-and-sampling.md#measurement-overhead-budget).

| Budget id | Item | Target | Checked by |
|---|---|---|---|
| B-OVH-CPU | Combined sampler and release-watcher CPU usage at 20 Hz | At most 1 % of one logical CPU | GH-OVERHEAD (GPU host) |
| B-OVH-JITTER | Sampler scheduling lateness, p99 | At most 10 ms | ST-JITTER (self-test), GH-OVERHEAD |
| B-OVH-RATE | Achieved sampling rate | At least 10 Hz, with gaps over 150 ms covering at most 5 % of a call | ST-SAMPLER; per-call `degraded` flag |
| B-OVH-RSS | Harness resident memory during a step | At most 256 MiB | GH-OVERHEAD |
| B-OVH-WATCH | Proof release timestamp error | At most 5 ms via inotify; at most 10 ms plus scheduler delay via poll fallback | TC-WATCH-INOTIFY, TC-WATCH-POLL |
| B-OVH-TRACE | 1 Hz downsampled resource trace per call | Fits inside the 1 MiB per-file log cap for calls up to 6 hours | Unit test on trace writer size |

Isolation rule: the harness pins itself to a single logical CPU outside both the prover and verifier CPU sets (RFC-0011 C-3, RFC-0006 §CPU and memory selection). As a result, harness CPU time never enters a job's cgroup counters, and B-OVH-CPU bounds indirect interference through shared caches and memory bandwidth.

Container start-up time is part of every adapter invocation rather than harness overhead; it is measured and reported (`info_seconds`, RFC-0004) rather than subtracted.

## CPU-only tooling

All CPU-only operations must run comfortably on any developer laptop and on hosted CI (AGENTS.md working practice). The targets below assume a 4-vCPU, 16 GB CI runner or a comparable laptop.

| Budget id | Operation | Target |
|---|---|---|
| B-CI-TOTAL | Wall-clock time for all RFC-0013 pull request gates | At most 10 minutes |
| B-CI-UNIT | Unit, property, and schema-example tests per shard on hosted CI ([07 §Sharding](07-testing-strategy.md#sharding)) | At most 3 minutes |
| B-CI-E2E | Fake-system end-to-end run, controls, and `fake-broken` check | At most 2 minutes |
| B-VAL-TREE | `iproofs validate` across 1,000 run directories | At most 60 seconds |
| B-DERIVE-RUN | `iproofs derive --check` on a single run directory | At most 50 ms |
| B-SITE | `iproofs site build` across 1,000 run directories | At most 60 seconds |
| B-FREEZE | `iproofs release freeze` across 1,000 run directories | At most 60 seconds |
| B-CLI-START | `iproofs --help` cold start | At most 500 ms (optional extras loaded lazily) |

These targets drive three architectural choices:

- Optional extras (`nvidia-ml-py`, `huggingface_hub`, `tokenizers`) are imported lazily inside the functions that require them so CPU-only commands never pay their import cost (B-CLI-START).
- JSON schemas are compiled once per process and cached by `$id` rather than recompiled for each file (B-VAL-TREE).
- Because `results/` grows append-only, pull request CI validates changed files along with the cross-file invariants they touch, while full-tree validation runs on the default branch (RFC-0013), keeping PR latency flat as history grows.

## Run-campaign compute budget

Cutting a benchmark release requires GPU hours for every configuration, repetition, negative control, and reference row. Runners need a reliable time estimate before renting hardware (PRD §11: "proving runs are expensive").

Projection method (following AGENTS.md rule 3, derived values are computed rather than typed by hand):

1. Inputs come from the `external` quantities in `systems/<name>/external.yaml` (upstream timings in their upstream scopes, RFC-0004 §Mapping from upstream scopes) together with workload shapes (RFC-0003).
2. `iproofs.derive.project_campaign(release: str, root: Path) -> CampaignProjection` calculates projected GPU-seconds per configuration as: `repetitions` × (projected `whole_wall` seconds for the shape) + projected commit seconds for one perturbed-weights commitment (control C3, once per workload) + projected prove seconds for prover-side controls P1 and P2 + projected reference-row seconds (RFC-0015). Setup is counted once per image per host.
3. Every projected quantity is tagged with `grade: projected`, formula ID `P-CAMPAIGN`, and its external input references in `source.inputs`. If any input is absent (for example, upstream did not publish `whole_wall`), that configuration's projection is null with `null_reason: missing_input` and the missing input is listed rather than filled in manually.
4. `iproofs release plan RELEASE` prints the projection for campaign planning; projections are never published as benchmark results.

The CLI entry point is [`iproofs release plan RELEASE [--repetitions N]`](../../harness/src/iproofs/cli.py) (default and minimum 3), backed by `project_campaign` in [`derive.py`](../../harness/src/iproofs/derive.py). It reads `whole_wall_seconds`, `commit_seconds`, and `prove_session_seconds` from each system's `external.yaml`, plus `prove_session_seconds` for `ref-serve` on the same workload. Each configuration also reports `missing` (any absent inputs) and `verify_seconds_per_proof_external` (the upstream `verify_single_thread_seconds` value, or null).

Verifier-side controls C1 through C8 execute on the CPU verifier profile (RFC-0008) and consume no GPU hours; their expected CPU verification time is reported separately from `external` verify figures.

## Profiling plan

- Hot paths in CPU tooling (validation, derivation, site generation, and release freeze) are profiled using Python's built-in `cProfile` against the 1,000-run synthetic tree produced by `harness/tests/fixtures/synthetic_tree.py`, adding no external profiling dependencies.
- Because the synthetic tree generator uses a fixed seed, profiles can be compared cleanly across commits.
- Measurement overhead is profiled exclusively on a GPU host via GH-OVERHEAD (RFC-0011 §Testing Strategy), since it depends on NVML and real OS scheduling.
- CI writes each gate's wall-clock duration to the job summary so regressions are spotted before a budget breaks. Every job in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) sets a hard timeout at twice its target (or twice B-CI-TOTAL if no gate-specific target exists).
- Tooling benchmarks live in [`harness/tests/bench/test_budgets.py`](../../harness/tests/bench/test_budgets.py) (covering B-VAL-TREE, B-DERIVE-RUN, and B-CLI-START) over [`harness/tests/fixtures/synthetic_tree.py`](../../harness/tests/fixtures/synthetic_tree.py). They execute on the default branch with `IPROOFS_BENCH=1`, fail at twice the target, and log every measured time alongside its target in the job summary.

## When a budget is exceeded

| Budget class | Response |
|---|---|
| Measurement overhead (B-OVH-*) on a host | Failing B-OVH-JITTER or B-OVH-RATE fails the self-test and rejects the host (`environment`, exit 3); failing B-OVH-CPU or B-OVH-RSS in GH-OVERHEAD blocks the release until resolved; per-call sampling gaps flag that call's GPU metrics as `degraded: true` rather than failing the run |
| CI gates (B-CI-*) | Each job times out hard at twice its target, failing the pull request. Runs finishing between 1x and 2x the target pass, log their duration in the job summary, and trigger a `type:perf` issue |
| Tooling operations (B-VAL-TREE, B-DERIVE-RUN, B-SITE, B-FREEZE, B-CLI-START) | Default-branch benchmarks over the synthetic tree fail at twice the target, while timings between 1x and 2x are highlighted in the job summary |
| Campaign projection | If projected GPU usage exceeds the available budget, repetitions may be reduced no lower than the minimum of three (RFC-0004 §Statistics); below that, the configuration is deferred and noted in the release report |

Adjusting a performance target requires a pull request updating this document; changing a measurement mechanism to hit a target requires updating RFC-0011.

## Cross-references

- [RFC-0004 §Statistics](../../rfcs/0004-metrics-timing-grades.md#statistics) for the repetition minimum.
- [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md) for hardware profiles and CPU binding.
- [RFC-0011](../../rfcs/0011-measurement-and-sampling.md) for the resource sampler, release watcher, and self-test.
- [RFC-0013](../../rfcs/0013-validation-and-ci.md) for the CI gates timed here.
- [RFC-0015](../../rfcs/0015-reference-rows.md) for reference rows included in campaign projections.
