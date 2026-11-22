# 02. Public API

This document is part of the specification corpus indexed in [docs/SPEC.md](../SPEC.md). Normative details live in the linked RFCs.

## What is public

The benchmark's public API covers every interface a third party can rely on without reading harness source code: runners submitting results, prover teams building adapters, readers inspecting published data, and downstream tools parsing files. Four surfaces are public; the internal Python modules of `iproofs` are not.

| Surface | Who depends on it | Contract | Version identifier |
|---|---|---|---|
| Command line `iproofs` | Runners, CI | Subcommands, flags, exit codes, and output files | Harness version (SemVer) |
| File schemas | Submitters, readers, downstream tools | `schema/<name>/<major>.schema.json` | `schema: "<name>/<major>"` in every document |
| Adapter contract | Prover teams implementing adapters | Container invocation, `job.json`, `out.json`, and proof release protocol | `contract: "adapter/<major>"` |
| Repository layout | All users and tools | Paths of authored and generated files | Benchmark release |

## Command line

The full CLI specification lives in [RFC-0010 §Command line](../../rfcs/0010-harness-runner.md#command-line). Summary of subcommands:

```
iproofs validate [PATH ...]
iproofs derive RUN_DIR [--check]
iproofs run --system S --workload W --profile P [--repetitions N] [--results DIR] [--control-suite]
            [--provider NAME] [--prompts-from RUN_DIR] [--allow-nonconforming]   # a no-op: conformance is recorded, never refuses
                                            # --prompts-from: replay a completed run's prompt
                                            # seeds; its run id is recorded as prompts_from
                                            # (RFC-0015 RC-1); a kind: reference system skips
                                            # commit, verify and controls (§Steps per job)
            [--keep-io]                     # keep io/ with proofs, for `iproofs controls RUN_DIR`
            [--in-process]                  # test systems only: run the entrypoint as a local process
            [--image IMAGE_ID]              # a local image by ID, digest_kind config (RFC-0014)
            [--runner HANDLE] [--runner-org ORG] [--affiliated SYSTEM ...]   # declared runner
iproofs controls RUN_DIR [--hosted] [--gpu INDEX] [--provider NAME]   # the whole suite; --hosted: in the run's pinned image
iproofs controls RUN_DIR --draw-seed                # the split suite's one seed, into RUN_DIR/controls-seed.json, once (RFC-0008 §Split suites)
iproofs controls RUN_DIR --only ID[,ID...] [--seed SEED] [--hosted] [--gpu INDEX] [--provider NAME]
                                                    # a part, with the recorded seed (--seed only confirms it); --gpu for prover-side ids
iproofs controls RUN_DIR --merge PART [PART...]     # controls.json from parts that cover the suite once
iproofs controls --prepare-perturbed WORKLOAD --system S --profile P [--image IMAGE_ID | --in-process] [--results DIR]
iproofs machine-record [--selftest]
iproofs fetch-model WORKLOAD [--headers-only]      # --headers-only: no weights; recompute a computed weight width from the GGUF headers (RFC-0003 WB-5), JSON on stdout
iproofs prompts build WORKLOAD --seed SEED [--out FILE]
iproofs release freeze RELEASE
iproofs release plan RELEASE
iproofs site build [--out DIR]                     # writes web/ (default) from the newest frozen release (RFC-0009 §Site)
```

CLI guarantees:

- **CLI-1 Exit codes.** Exit code 0 means success; 1 means a check failed; 2 means a usage error; 3 means the environment does not satisfy the profile; 4 means a job executed and was recorded as failed; 5 means an internal error. These meanings stay fixed within a harness major version.
- **CLI-2 No measurement flags.** No CLI flag alters what is measured or how timing works. Workloads, shapes, profiles, timeouts, and forbidden flags always come from reviewed files in the repository.
- **CLI-3 Machine-readable output.** Data-emitting commands (`machine-record`, `prompts build`, and `fetch-model --headers-only`) write canonical JSON to stdout. Human progress lines go to stderr and can be muted with `--quiet`.
- **CLI-4 Determinism.** `validate`, `derive`, `release freeze`, and `site build` produce byte-identical output for identical inputs across all supported platforms.
- **CLI-5 Offline checks.** `validate`, `derive`, `release freeze`, and `site build` require neither network access nor a GPU, and work using only the base Python installation without optional extras.

## File schemas

Specified in [RFC-0012](../../rfcs/0012-schemas-and-serialization.md). Every document read or written by the benchmark has a JSON Schema (Draft 2020-12) and embeds its schema identifier:

| Document | File | Authored or generated | Schema id |
|---|---|---|---|
| Claim card | `systems/<name>/claim.yaml` | Authored | `claim/1` |
| System manifest | `systems/<name>/system.yaml` | Authored | `system/1` |
| System-specific controls | `systems/<name>/controls.yaml` | Authored | `system-controls/1` |
| Workload | `workloads/<id>.yaml` | Authored | `workload/1` |
| Prompt corpus | `workloads/prompts/corpus.yaml` | Authored | `corpus/1` |
| Reference hardware and cost | `reference/<release>.yaml` | Authored | `reference/1` |
| CI profile (never released) | `reference/ci.yaml` | Authored | `reference/1` |
| Target | `targets/<author>/<id>.yaml` | Authored | `target/1` |
| Release record | `releases/<release>/release.yaml` | Authored | `release/1` |
| Run result | `results/.../run.json` | Generated | `run/1` |
| Run manifest | `results/.../manifest.json` | Generated | `manifest/1` |
| Control verdicts | `results/.../controls.json` | Generated | `controls/1` |
| Perturbed commitment | `results/<release>/<system>/_controls/<workload>/perturbed.json` | Generated | `perturbed-commitment/1` |
| Release index | `releases/<release>/index.json` | Generated | `release-index/1` |
| Adapter job | `/io/job.json` | Generated | `adapter-job/1` |
| Adapter output | `/io/out.json` | Generated by adapters | `adapter-out/1` |

Schema guarantees:

- **SCHEMA-1:** Any document can be validated using a standard JSON Schema Draft 2020-12 validator and the files under `schema/`, without running harness code.
- **SCHEMA-2:** Within a major version, only additive optional changes are permitted. Removing or renaming a field, changing its type or meaning, or adding a required field requires a new major version introduced by an RFC.
- **SCHEMA-3:** Every measurement in a generated document is stored as a labelled quantity (`value`, `unit`, `scope`, `grade`, `tier`, `source`, `null_reason`) rather than a bare number ([RFC-0012 §Quantity](../../rfcs/0012-schemas-and-serialization.md)).
- **SCHEMA-4:** Generated JSON is byte-stable: sorted keys, two-space indentation, UTF-8 encoding, LF line endings, a single trailing newline, and no `NaN` or `Infinity` literals.

## Adapter contract

Specified in [RFC-0005](../../rfcs/0005-adapter-contract.md). Every system team implementing an adapter conforms to the following interface:

- Package the adapter as an OCI image built from `systems/<name>/Dockerfile`, pinning upstream source at a full commit hash.
- Expose an entrypoint supporting five subcommands (`info`, `setup`, `commit`, `prove`, and `verify`), each invoked as `<subcommand> /io/job.json /io/out.json` and exiting 0 whenever the subcommand completed normally, regardless of the verification verdict.
- Release proofs atomically into `/io/proofs/` via directory `rename`.
- Map upstream verification outcomes to the four normalised verdicts: `accept`, `reject`, `no_verdict`, and `invalid_call`.
- Run with no network access, a read-only root filesystem, no Linux capabilities, and model weights mounted read-only.

Adapter contract guarantees:

- **ADAPTER-1:** The harness never sends fields unknown to adapters on the same contract major, and adapters MUST ignore unknown optional fields in `job.json`.
- **ADAPTER-2:** The harness strictly rejects any `out.json` that fails `adapter-out/<major>` validation; there is no lenient mode.
- **ADAPTER-3:** The commitment passed to `verify` always comes from the harness's stored record of the `commit` step.

## Repository layout

Downstream tools and contributors rely on the paths below. Moving any of them is a breaking change that must be announced at least one benchmark release in advance.

```
schema/<name>/<major>.schema.json          schema/<name>/examples/{valid,invalid}/
systems/<name>/{Dockerfile,entrypoint,system.yaml,claim.yaml,external.yaml,controls.yaml,README.md,tests/}
workloads/<id>.yaml                        workloads/prompts/corpus.yaml
reference/<release>.yaml
results/<release>/<system>/<run-id>/{run.json,manifest.json,controls.json,verifier/,logs/,digests.txt}
releases/<release>/{release.yaml,index.json}
targets/<author>/<id>.yaml
reports/<release>.md
```

Layout guarantees:

- **LAYOUT-1:** `results/` is strictly append-only. Merged files are never modified or deleted; corrections are submitted as new runs referencing the run they supersede.
- **LAYOUT-2:** Model weights, raw proof bytes, and secrets are never committed to the repository.

## What is not public

- Internal Python modules, classes, and functions under `iproofs` may change in any release. Function signatures shown in RFCs serve as contributor design notes rather than an external SDK; downstream tools should read the public JSON and YAML files instead.
- Event names and payload fields in `logs/harness.jsonl` ([05-observability](05-observability.md)) are kept stable within a harness minor version as a courtesy, not as a formal API contract.
- The HTML structure of the generated website is internal; all underlying data is publicly available through `index.json` and the run files.

## Stability and versioning

Full details on version lines, deprecation periods, and changelog rules are in [09-release-and-versioning](09-release-and-versioning.md). Briefly: the harness follows SemVer 2.0 with the CLI, schemas, adapter contract, and repository layout as its public API; schemas and the adapter contract maintain separate major numbers; and the harness reads both the current and previous major version of every schema and contract for at least one benchmark release.
