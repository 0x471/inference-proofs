# 03. Data model

Normative definitions live in the RFCs listed for each object; if this summary disagrees with an RFC, the RFC takes precedence. Encoding, versioning, digest formats, and identifier rules are defined in [RFC-0012](../../rfcs/0012-schemas-and-serialization.md).

## Purpose

This section maps out every stored object in the benchmark: its identifying key, what it points to, who writes it, and when it can change. Contributors adding a field or file can use this table to trace which downstream objects depend on it.

## Entities

| Object | Schema | File | Key | References | Written by | Mutability | Owner RFC |
|---|---|---|---|---|---|---|---|
| Claim card | `claim/1` | `systems/<name>/claims/<configuration>.yaml` | (system, configuration, `card_version`) | Upstream commit | Adapter author | PR; `card_version` increments on every merged change | [RFC-0002](../../rfcs/0002-claim-card.md) |
| System manifest | `system/1` | `systems/<name>/system.yaml` | system | Upstream commit, image digest, workloads, profiles, and claim cards; declares `kind` (`prover`, `reference`, `test`), `incremental_proofs`, `proofs.{granularity, tokens_covered, steady_boundary, steady_approximate, verify_reads}`, and `forbidden_flags` | Adapter author | PR | [RFC-0005](../../rfcs/0005-adapter-contract.md) |
| External figures | `external/1` | `systems/<name>/external.yaml` | (system, figure id) | Upstream URL at a pinned commit | Adapter author | PR | [RFC-0004](../../rfcs/0004-metrics-timing-grades.md) |
| System controls | `system-controls/1` | `systems/<name>/controls.yaml` | (system, control id) | System manifest | Adapter author | PR | [RFC-0008](../../rfcs/0008-negative-controls.md) |
| Workload | `workload/1` | `workloads/<id>.yaml` | (id, version) | Model source and revision, prompt corpus | Maintainers | New version for any change that affects measurements | [RFC-0003](../../rfcs/0003-workloads.md) |
| Prompt corpus | `corpus/1` | `workloads/prompts/corpus.yaml` | corpus digest | Public source URLs | Maintainers | New digest on any content change | RFC-0003 |
| Reference file | `reference/1` | `reference/<release>.yaml` | release | None | Maintainers | Frozen at release | [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md) |
| Adapter job | `adapter-job/1` | `/io/job.json` (transient) | (run, step) | Commitment record, workload | Harness | Never committed outside run logs | RFC-0005 |
| Adapter output | `adapter-out/1` | `/io/out.json` (transient, copied into the run) | (run, step) | None | Adapter | Copied canonically by the harness | RFC-0005 |
| Run | `run/1` | `results/<release>/<system>/<run-id>/run.json` | run-id | Workload (id, version), system, profile, release, claim card (`card_version`), replaced run; includes the `events` list `{event, mono_ns}` | Harness | Append-only | [RFC-0009](../../rfcs/0009-results-and-publication.md), RFC-0004 |
| Manifest | `manifest/1` | `.../<run-id>/manifest.json` | run-id | Image digest, upstream commit, model digest, corpus digest, prompt seed, reference file digest, claim card, runner `{handle, organisation, affiliated_systems}`, and machine self-test result | Harness | Append-only | [RFC-0014](../../rfcs/0014-provenance-and-integrity.md) |
| Control outcomes | `controls/1` | `.../<run-id>/controls.json` | run-id | Run's proofs, perturbed commitment | Harness | Append-only | RFC-0008 |
| Control suite seed | `controls-seed/1` | `<run-dir>/controls-seed.json` (never committed under `results/`) | run-id | Run's manifest | `iproofs controls --draw-seed` | Written once | [RFC-0008 §Split suites](../../rfcs/0008-negative-controls.md#split-suites) |
| Control suite part | `controls-part/1` | `<run-dir>/controls-part-<seed>-<subset>.json` (never committed under `results/`) | (run-id, seed, subset) | Run's manifest and seed record | `iproofs controls --only` | Working file merged via `--merge` | [RFC-0008 §Split suites](../../rfcs/0008-negative-controls.md#split-suites) |
| Verifier record | part of `run/1` defs | `.../<run-id>/verifier/<proof_id>.json` | (run-id, proof id) | Proof digest | Harness | Append-only | RFC-0009 |
| Perturbed commitment | `perturbed-commitment/1` | `results/<release>/<system>/_controls/<workload>/perturbed.json` | (release, system, workload) | Workload | `iproofs controls --prepare-perturbed` | Write-once per release | [RFC-0008](../../rfcs/0008-negative-controls.md#shared-controls-verifier-side) |
| Release record | `release/1` | `releases/<release>/release.yaml` | release | Runs, reference file, claim card digests, RFC commit | Maintainers | Frozen after freeze | RFC-0009 |
| Release index | `release-index/1` | `releases/<release>/index.json` | release | Everything listed in the release record | `iproofs release freeze` | Generated once per release | RFC-0009 |
| Target | `target/1` | `targets/<author>/<id>.yaml` | (author, id) | Metric id, claim card fields | Relying party | PR; versioned in git history | RFC-0009 |

A configuration is derived at release freeze rather than stored directly; it corresponds to the tuple (system, workload id, workload version, profile, adapter image digest, `control: false`) ([RFC-0009 §Configurations and repetitions](../../rfcs/0009-results-and-publication.md#configurations-and-repetitions)).

## Relations

Each run belongs to one system (whose `kind` is `prover`, `reference`, or `test`; reference systems skip commit and verify, and `test` systems are never included in releases), one workload version, one hardware profile, and one release. Its manifest pins the container image digest, upstream commit, model and corpus digests, prompt seed, and reference file. Its `controls.json` references its own proofs and, for control C3, a perturbed commitment stored under the same release. A release record enumerates the included runs and claim card digests, from which `release freeze` computes configurations, statistics, control summaries, and target evaluations into `index.json`. Targets reference metric IDs and claim card fields and are evaluated against each configuration.

```
claims/*.yaml ┐
system.yaml ─┼─< run.json ──── manifest.json
workload ────┤      │  └────── controls.json
reference ───┘
release.yaml ──< runs ──> index.json <── targets/*.yaml
```

## Cross-object invariants

Each invariant below is enforced by the corresponding CI gate in [RFC-0013](../../rfcs/0013-validation-and-ci.md).

- **INV-DM-1 Referential integrity.** Every run references an existing workload (id and version), system, and profile, and every release entry references existing runs. Checked by Gate G2 (`XREF-1` to `XREF-4`).
- **INV-DM-2 Labelled numbers.** Every numeric field in a run, controls file, external figures file, reference file, or release index is either a labelled quantity, a statistic, or a structural integer (such as a count or index). Checked by Gates G2 and G5.
- **INV-DM-3 Derived means computed.** Every quantity with `grade: derived` matches its recomputed value bit for bit. Checked by Gate G4.
- **INV-DM-4 Image consistency.** The adapter image digest in a run's `manifest.json` matches the digest in its `run.json`. Checked by Gate G2 (`XREF-2`).
- **INV-DM-5 Commitment provenance.** The `commitment_id` and verifier file digests supplied to every `verify` call match those saved in the manifest during `commit`. Enforced structurally by the harness ([RFC-0014 §The commitment record](../../rfcs/0014-provenance-and-integrity.md#the-commitment-record)) and tested by Gate G10.
- **INV-DM-6 Control isolation.** No run marked `control: true` ever contributes to a measured row in a release table. Checked by Gate G6 (`POL-2`).
- **INV-DM-7 Tier location.** All quantities stored under `results/` carry evidence tier `reported`. Checked by Gate G5 (`LBL-3`).
- **INV-DM-8 Append-only.** Merged files under `results/` are never edited or deleted. The only permitted additions to an already-merged run directory are its control records (`controls.json`, `controls-seed.json`, `controls-parts/`), added once ([RFC-0008](../../rfcs/0008-negative-controls.md) `iproofs controls RUN_DIR`), and its CPU re-verification record (`reverify/`), added once ([RFC-0018](../../rfcs/0018-level-1-ladder.md) CH-4a). Checked by Gate G2 (`APP-1`).
- **INV-DM-9 Claim before number.** Every system appearing in a release has a claim card listed by digest in `release.yaml`, and each run's `claim.card_version` matches that listed card. Checked during freeze step 1.
- **INV-DM-11 Self-test passed.** Only runs whose machine self-test passed are eligible for inclusion in a release (freeze step 3). Profile conformance is recorded in `harness.nonconforming` in the manifest and never blocks execution.
- **INV-DM-10 No weights, no proofs in git.** Neither model weights nor proof parts are committed to the repository; runs store digests only. Gate G2 (`SIZE-1`) rejects any file larger than 5 MiB outside `results/*/*/*/logs/` and any run directory exceeding 10 MiB.

## Lifecycles

| Object | States |
|---|---|
| Claim card | Drafted -> frozen in a release by digest |
| Workload | Version 1 -> bumped to a new version whenever a change affects measurements; earlier versions remain in the repository |
| Run | Allocated (directory created) -> written (`completed` or `failed`) -> merged -> optionally superseded by a later run setting `replaces` |
| Release | `release.yaml` drafted -> frozen (`index.json` committed and merged) |
| Target | Proposed via PR -> published; revisions are committed as updates, and each release evaluates the version present at freeze time |

## Schema versioning summary

Every document embeds `schema: "<name>/<major>"`. Additive optional changes remain within the current major version, while breaking changes increment the major. Previous major schemas remain under `schema/`, and readers support both the current and previous major version for at least one benchmark release. See [RFC-0012 §Schema versioning](../../rfcs/0012-schemas-and-serialization.md#schema-versioning) and [09-release-and-versioning.md §Schema majors](09-release-and-versioning.md#schema-majors) for full rules.
