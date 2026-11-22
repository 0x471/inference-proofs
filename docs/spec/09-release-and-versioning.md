# 09. Release and versioning

Normative specifications live in [RFC-0009](../../rfcs/0009-results-and-publication.md) for benchmark releases, [RFC-0012](../../rfcs/0012-schemas-and-serialization.md) for schema versions, and [RFC-0005](../../rfcs/0005-adapter-contract.md) for the adapter contract.

## Four version lines

The project versions four artifacts separately. Mixing them up is a frequent source of confusion, so each uses a distinct naming scheme:

| Line | Format | Example | What it versions |
|---|---|---|---|
| Harness | SemVer 2.0 `MAJOR.MINOR.PATCH` | `0.1.0` | The `inference-proofs-harness` package and `iproofs` CLI |
| Schema | `<name>/<major>` | `run/1` | An individual document schema |
| Adapter contract | `adapter/<major>` | `adapter/1` | The OCI container interface between harness and adapters |
| Benchmark release | `v<major>.<minor>` | `v0.1` | A frozen set of runs, reference hardware file, RFCs, and claim cards |

## Harness

### Public API

The harness's public API consists of the `iproofs` CLI (subcommands, options, exit codes, and stdout formats designated machine-readable), the JSON Schemas, the adapter contract, and the repository directory layout read and written by the CLI. Python modules inside `iproofs` are internal; importing them from external code is unsupported and may break in any release.

### SemVer rules

- During `0.x`, a MINOR increment may introduce breaking changes to the public API; the CHANGELOG entry must document what broke and how to migrate. A PATCH increment never alters the public API.
- Starting at `1.0.0`, any breaking change to the public API requires a MAJOR increment and an accompanying RFC.
- Any change that alters a published number for identical inputs (such as a formula, timing boundary, or sampling rule) is a methodology change and must be updated alongside the relevant RFC.
- `1.0.0` will not be tagged earlier than the first benchmark release after v0.1 that runs on the same harness major without breaking changes, ensuring the public API has survived a full real release.

### Version source

The harness version is stored exclusively in `pyproject.toml`. Running `iproofs --version` prints both the version and the harness git commit, and every run manifest records both (RFC-0014).

## Schema majors

- Additive optional fields are added to the current major schema in place; any breaking change creates `schema/<name>/<major+1>.schema.json` ([RFC-0012 §Schema versioning](../../rfcs/0012-schemas-and-serialization.md#schema-versioning)).
- The harness always writes documents using the current major of each schema.
- The harness continues reading both the current and previous major of every schema for at least one benchmark release after a new major lands. Support for older majors is dropped only after a deprecation notice (see below).
- Already-stored documents are never migrated or rewritten to newer majors.

## Adapter contract major

- Every `job.json` declares `contract: "adapter/1"`, and each adapter's `info` subcommand reports the contract majors it supports.
- Breaking changes to the container interface (subcommands, required fields, verdict vocabulary, or `/io` layout) require bumping the contract major.
- The harness supports both the current and previous contract major for at least one benchmark release so adapter maintainers have a full release cycle to upgrade. Adapters targeting a retired major cannot run in subsequent releases.

## Benchmark releases

A benchmark release (such as `v0.1`) is produced by the freeze procedure in [RFC-0009 §Freeze algorithm](../../rfcs/0009-results-and-publication.md#freeze-algorithm). Every release pins:

- The exact list of run directories;
- The reference hardware and cost file (`reference/<release>.yaml`) by path and digest;
- The RFC commit defining the active `rfcs/` tree;
- The harness version used during freeze and recorded in each run's manifest;
- The schema majors of all included documents;
- Every adapter image digest (via the run manifests);
- Every claim card by digest.

Benchmark release numbers are decoupled from harness versions: `v0.1` might be frozen using harness `0.3.2`. Once frozen, a release's data is immutable; any corrections land in the next release.

## Deprecation policy

Every deprecation is announced in `CHANGELOG.md`, identifying both the deprecated feature and its replacement. Deprecated CLI options remain functional until removal and print a warning on stderr naming the replacement.

## CHANGELOG discipline

- `CHANGELOG.md` lives at the repository root in Keep a Changelog 1.1 format using the standard sections (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`), plus a `Methodology` section for methodology changes citing the relevant RFC number.
- Every pull request touching the public API, a schema, or the methodology adds an entry under `Unreleased`.
- Entries state clearly what changed, and any quantitative figure included in an entry carries its full labels (AGENTS.md rule 2).

## Release checklists

### Harness version

1. Confirm all required checks are green on `main` and no quarantined test is older than 30 days ([07-testing-strategy.md §Flaky-test policy](07-testing-strategy.md#flaky-test-policy), checked by `harness/tests/repo/test_quarantine.py`).
2. Bump the version in `pyproject.toml` and move the `Unreleased` entries in `CHANGELOG.md` under the new version and release date.
3. Run `uv build` to generate the wheel and source distribution, then verify `uv run --isolated --with dist/*.whl iproofs --version` succeeds in an isolated environment.
4. Tag the release commit as `harness-v<version>`.
5. Attach the wheel to the GitHub release notes for that tag. The harness is not published to PyPI or any other public package index (see Q1 below).

### Benchmark release

1. Record the RFC commit in `release.yaml`.
2. Merge the reference file with the reference price, pricing date, and pinned driver, CUDA, and runtime versions.
3. Merge all campaign runs, ensuring every run is either eligible or explicitly marked ineligible with a reason.
4. List all claim cards by digest in `release.yaml`.
5. Draft the release report.
6. Run [`iproofs release freeze RELEASE`](../../harness/src/iproofs/release.py) (which halts with exit code 1 on the first failing check), merge the generated `index.json`, and tag that commit as `v<release>`.
7. Run `iproofs site build` and publish the static site from the tagged commit.

## Licence split

- Code (harness, adapters, site generator, and CI workflows) is licensed under Apache-2.0 (`LICENSE`).
- Specifications, RFCs, documentation, data (workloads, results, release indexes, targets), and reports are licensed under CC BY 4.0 (PRD §7 N5). The README documents this split, and `LICENSES/CC-BY-4.0.txt` contains the full licence text.
- There is no contributor licence agreement.
- Upstream provers retain their own licences; adapter images redistribute upstream code only as permitted by those licences (both v0.1 systems are Apache-2.0 per PRD §1).

## Decisions

- Q1. The harness is not published to a public package index. Because it is a runner tool tied directly to this repository rather than a general-purpose library, users install it from a tagged checkout via `uv sync`.
