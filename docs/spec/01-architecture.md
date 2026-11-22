# 01. Architecture

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). Normative requirements live in the RFCs linked from each section; if this document and an RFC disagree, the RFC takes precedence.

## System overview

The benchmark is built around four types of components: authored inputs (workloads, system adapters, reference hardware definitions, and targets), the harness that executes jobs on a host, the append-only results tree written by the harness, and the validation and generation tooling that turns raw results into a frozen release and static site.

```
 authored inputs (git, reviewed)                       host (runner's machine)
 +--------------------------+                 +--------------------------------------------+
 | workloads/<id>.yaml      |                 |  iproofs run                                |
 | workloads/prompts/       |---- resolve --->|   runner state machine (RFC-0010)          |
 | systems/<name>/          |                 |   +-- measure: clock, NVML, cgroup, watcher |
 |   system.yaml claim.yaml |                 |   |        (RFC-0011)                       |
 |   Dockerfile entrypoint  |-- build image ->|   +-- docker run <image@digest> <subcmd>    |
 | reference/<release>.yaml |                 |   |        adapter container (RFC-0005)     |
 +--------------------------+                 |   +-- controls: mutate, twin, classify      |
                                              |            (RFC-0008)                       |
 model weights (public source, by hash) ----->|   /models (ro)   /io (rw)                   |
                                              +---------------------+----------------------+
                                                                    |
                                                                    v
                                     results/<release>/<system>/<run-id>/
                                       run.json manifest.json controls.json
                                       verifier/ logs/ digests.txt
                                                                    |
                           pull request: iproofs validate, derive --check (RFC-0013)
                                                                    |
                                                                    v
                        releases/<release>/release.yaml  -> iproofs release freeze -> index.json
                                                                    |
                                                                    v
                              iproofs site build -> web/ (committed)  reports/<release>.md
```

In practice, the workflow runs from left to right. Authored inputs live in git and change through reviewed pull requests. A runner invokes `iproofs run` on a machine matching a prover profile ([RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md)). The harness resolves the workload by fetching model weights from their public source and checking every file's hash, verifies the adapter image digest, captures the machine record, and drives the adapter container through its five subcommands while measuring execution from outside the container. When requested, it also runs the negative-control suite against the honest proofs. The harness writes one run directory per job under `results/`, which the runner submits in a pull request where CI validates the files and recomputes all derived metrics. To cut a release, maintainers author `releases/<release>/release.yaml`, run `iproofs release freeze` to compute summary statistics and target evaluations into `index.json`, and run `iproofs site build` to generate the static site in `web/`. Release reports are written by hand from the frozen data.

## Components and responsibilities

| Component | Location | Responsibility | Specified in |
|---|---|---|---|
| Schemas | `schema/<name>/<major>.schema.json` | Defines the normative structure of every document | [RFC-0012](../../rfcs/0012-schemas-and-serialization.md) |
| Workload registry | `workloads/` | Defines models by source, revision, and digest, plus prompt corpora, generators, shapes, and divisions | [RFC-0003](../../rfcs/0003-workloads.md) |
| System adapters | `systems/<name>/` | Wraps each upstream prover unchanged behind the `adapter/1` contract | [RFC-0005](../../rfcs/0005-adapter-contract.md) |
| Claim cards | `systems/<name>/claim.yaml` | States what an accepted proof establishes | [RFC-0002](../../rfcs/0002-claim-card.md) |
| Reference systems | `systems/ref-serve/`, `systems/ref-recompute/`, `workloads/serving/` | Produces production-serving and recompute reference rows via the same contract, with serving weights pinned by record (SRV-6) | [RFC-0015](../../rfcs/0015-reference-rows.md) |
| Test systems | `systems/fake/`, `systems/fake-broken/` | Provides a CPU-only toy prover and an always-accept verifier for CI tests | [RFC-0005](../../rfcs/0005-adapter-contract.md#reference-implementations) |
| Reference hardware and cost | `reference/<release>.yaml` | Specifies hardware profiles and fixed reference pricing for each release | [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md) |
| Harness | `harness/src/iproofs/` | Executes jobs, records external measurements, validates results, freezes releases, and builds the site | [RFC-0010](../../rfcs/0010-harness-runner.md), [RFC-0011](../../rfcs/0011-measurement-and-sampling.md) |
| Results | `results/<release>/` | Stores append-only run directories | [RFC-0009](../../rfcs/0009-results-and-publication.md) |
| Releases | `releases/<release>/` | Stores frozen release definitions and computed summary indexes | [RFC-0009](../../rfcs/0009-results-and-publication.md) |
| Targets | `targets/<author>/<id>.yaml` | Stores performance and property thresholds published by relying parties | [RFC-0009](../../rfcs/0009-results-and-publication.md#targets) |
| CI | `.github/workflows/` | Runs the automated validation gates defined in RFC-0013 | [RFC-0013](../../rfcs/0013-validation-and-ci.md) |
| Site and reports | `web/` (generated by `iproofs site build`, renderer in `web/build.py`), `reports/` | Publishes the static benchmark website and written release reports | [RFC-0009](../../rfcs/0009-results-and-publication.md) |

## Module boundaries

The harness is packaged as a single Python package named `iproofs` (distribution `inference-proofs-harness`, located in `harness/src/iproofs/`). Its modules are organized into layers so that each module imports only from lower layers, or from the same layer where explicitly noted, keeping the dependency graph acyclic (INV-ARCH-1). Because the automated module-layer layout test was retired on 2026-11-10, this table serves as an architectural guide enforced during code review. The key practical constraint is INV-ARCH-6: `validate`, `derive`, `release`, and `site` must not import anything requiring a GPU host or an optional dependency.

| Layer | Module | Responsibility | May import |
|---|---|---|---|
| 0 | `iproofs.errors` | `ErrorKind`, `IProofsError`, `Failure` ([RFC-0010](../../rfcs/0010-harness-runner.md#error-taxonomy)) | stdlib |
| 0 | `iproofs.log` | JSON Lines logger, redaction, and progress output ([05](05-observability.md)) | stdlib, `errors` |
| 1 | `iproofs.serialize` | Single canonical JSON writer, safe YAML loader, and byte-format checks | `errors` |
| 1 | `iproofs.quantity` | Labelled quantity and statistic types, plus vocabularies (units, scopes, grades, tiers) | `errors` |
| 1 | `iproofs.gguf` | GGUF header reader (local file or HTTP range requests), ggml type table, and weight-width computation `gguf-active-mean/1` ([RFC-0003](../../rfcs/0003-workloads.md#weight-bits) WB-5) | `errors` |
| 2 | `iproofs.schema` | Schema registry, `$id` resolution, and JSON Schema Draft 2020-12 validation | `errors`, `serialize` |
| 2 | `iproofs.model` | Frozen dataclasses for documents read field by field (authored inputs and adapter output), where loading parses, validates, and constructs; harness-written documents are validated as trees against their schemas ([RFC-0012 §Python loading](../../rfcs/0012-schemas-and-serialization.md#python-loading)) | `errors`, `serialize`, `quantity`, `schema` |
| 3 | `iproofs.provenance` | File, model, and proof digests (hashing each file once, in parallel where possible), pin validation, and machine record collection | layers 0 to 2 |
| 3 | `iproofs.derive` | Derived metrics and summary statistics computed from raw stored quantities ([RFC-0004](../../rfcs/0004-metrics-timing-grades.md)) | layers 0 to 2 |
| 4 | `iproofs.workloads` | Workload resolution, model fetching, and prompt materialisation | layers 0 to 3 |
| 4 | `iproofs.serving` | Production-serving records (SM-1 to SM-3), `serving pin`, and fetching publisher releases from ungated byte-identical mirrors ([RFC-0015](../../rfcs/0015-reference-rows.md) SRV-6, [RFC-0014](../../rfcs/0014-provenance-and-integrity.md#model-fetch-and-verification)) | layers 0 to 3 |
| 4 | `iproofs.adapter` | `job.json` and `out.json` handling, `docker run` argv construction, I/O directories, path safety checks, and `ContainerRunner` implementations | layers 0 to 3, and `iproofs.measure` (container calls are timed where they run, RFC-0011 T-1) |
| 4 | `iproofs.measure` | Monotonic clock timing, NVML and cgroup samplers, proof-release watcher, and proof size accounting ([RFC-0011](../../rfcs/0011-measurement-and-sampling.md)) | layers 0 to 3 |
| 5 | `iproofs.controls` | Control mutations, honest twins, outcome classification, and `controls.json` writing ([RFC-0008](../../rfcs/0008-negative-controls.md)) | layers 0 to 4 |
| 5 | `iproofs.selftest` | RFC-0011 calibration self-test (`machine-record --selftest`) | layers 0 to 4 |
| 6 | `iproofs.runner` | Job state machine, timeouts, retries, and crash recovery ([RFC-0010](../../rfcs/0010-harness-runner.md)) | layers 0 to 5 |
| 7 | `iproofs.validate` | All CI checks ([RFC-0013](../../rfcs/0013-validation-and-ci.md)); `validate.memo` caches single-file check results outside the repository keyed by file SHA-256 | layers 0 to 5 |
| 7 | `iproofs.release` | Release freeze, run eligibility, statistics aggregation, and target evaluation | layers 0 to 5 |
| 8 | `iproofs.site` | Static site generation from a frozen release | layers 0 to 5, `release` |
| 9 | `iproofs.cli` | Argparse CLI entry point translating `IProofsError` instances into process exit codes | every module |

Key boundary invariants:

- **INV-ARCH-1:** No circular dependencies and no upward imports beyond the table above.
- **INV-ARCH-2:** Only `iproofs.serialize` writes JSON or YAML files; all other modules delegate serialization to it.
- **INV-ARCH-3:** Only `iproofs.adapter` constructs container command lines, and `iproofs.measure.timed_call` is the sole place that starts, kills, and removes containers so that every call is timed where it executes (RFC-0011 T-1).
- **INV-ARCH-4:** Only `iproofs.measure` reads duration clocks, NVML counters, or cgroup files; the runner consumes `StepResult` objects.
- **INV-ARCH-5:** `iproofs.derive` is a pure function over stored documents with no clock access, file system writes, or network calls, ensuring CI can recompute derived numbers identically on any host.
- **INV-ARCH-6:** Optional dependencies (`nvidia-ml-py` in `measure`, `huggingface_hub` and `tokenizers` in `workloads`) are imported lazily inside the functions that need them so `iproofs validate`, `derive`, `release`, and `site` work with the base installation alone.

## Data flow

1. **Workload resolution.** `iproofs.workloads` loads `workloads/<id>.yaml`, downloads each weight file from its public source at the pinned revision, and verifies every file's SHA-256 against the workload definition. It draws a fresh 64-bit job seed via `os.urandom`, generates the prompt set from the pinned corpus using that seed, and records the prompt set digest ([RFC-0003](../../rfcs/0003-workloads.md)). The resolved paths and digests are written into the manifest.
2. **Image and machine setup.** `iproofs.provenance` verifies the local container image digest against `system.yaml` and records host details ([RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md)), while `iproofs.measure` selects a CPU set on the GPU's NUMA node.
3. **Adapter steps.** For each subcommand, the runner writes `job.json`, asks `iproofs.adapter` to execute the container, and receives a `StepResult` containing the elapsed window, resource samples, and (for `prove`) proof release timestamps. The `commit` step produces the commitment record managed by the harness, and every subsequent `verify` step receives its commitment strictly from that record ([RFC-0005](../../rfcs/0005-adapter-contract.md)).
4. **Negative controls.** `iproofs.controls` copies and mutates honest proofs and requests, then runs `verify` on each mutated case alongside its honest twin ([RFC-0008](../../rfcs/0008-negative-controls.md)).
5. **Recording results.** The runner converts raw observations into labelled quantities (`grade: measured`, `tier: reported`), invokes `iproofs.derive` on those stored values, validates all outputs, and atomically renames the staging directory into its final run directory ([RFC-0010](../../rfcs/0010-harness-runner.md#writing-the-run-directory)).
6. **Review and CI.** When a pull request lands, CI runs `iproofs validate` and `iproofs derive --check` on every changed run directory.
7. **Release and publication.** `iproofs release freeze` reads `release.yaml`, gathers the listed runs, computes aggregate statistics and target evaluations, and writes `index.json`. `iproofs site build` then renders the static pages into `web/` from `index.json`, the referenced claim cards and run records, the criteria file, and `web/_data/facts.json`. Vercel serves the committed `web/` directory directly ([RFC-0009](../../rfcs/0009-results-and-publication.md#site)).

Data flows strictly forward: nothing downstream of a run directory modifies it (INV-ARCH-7, keeping `results/` append-only).

## Process and deployment model

- The runner executes as a single process per host, running one job per GPU at a time with sequential steps and background sampler threads during timed calls ([RFC-0010](../../rfcs/0010-harness-runner.md#concurrency)).
- CPU-only commands (`validate`, `derive`, `release`, `site`, and the fake-system end-to-end tests) run on any machine with Python 3.12 or 3.13, including hosted CI runners.
- GPU jobs run on a host satisfying `prover-h200` or another declared Docker profile such as `prover-h100`: Linux kernel 5.19 or newer, cgroup v2, Docker Engine 25.0 or newer using the systemd cgroup driver, NVIDIA Container Toolkit 1.17 or newer, and the driver version pinned in `reference/<release>.yaml`. Hosted CI never executes GPU jobs.
- There is no central server, database, or persistent daemon. All canonical state lives as files in git, with large proofs referenced by cryptographic digest.

## Trust boundaries

Three boundaries govern system isolation: the adapter container (untrusted code supplied by the measured system, isolated with no network, a read-only root filesystem, and dropped Linux capabilities), files emitted by adapters (treated as untrusted input and verified for path safety and size limits), and run directories submitted by runners (all numbers labelled `reported`). See [06-security](06-security.md) for the full threat model.

## RISK

- RISK: Strict layering rules can encourage minor code duplication, such as digest helpers needed by both `adapter` and `provenance`. Mitigation: move shared helpers down to layer 1 or layer 3 rather than adding sideways imports.
- RISK: SASH's segment-grid proof layout and FlashProve's per-request proof layout put different pressures on the shared `proofs/<proof_id>/` abstraction. Mitigation: model layout differences explicitly through the `proofs` declaration in `system.yaml` ([RFC-0005](../../rfcs/0005-adapter-contract.md#systemyaml)) and revisit after the first SASH adapter runs.
