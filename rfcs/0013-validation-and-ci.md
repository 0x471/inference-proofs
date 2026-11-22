# RFC-0013: Validation pipeline and CI gates

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0002, RFC-0004, RFC-0005, RFC-0008, RFC-0012

## Summary

This RFC defines the automated checks that protect the default branch and the local CLI command that runs the exact same suite. There are nine active gates: G1 through G7, G9, and G10 (G8 and G12 were withdrawn on 2026-11-10). Every gate specifies its rule, its exact set of input files, a standard failure message format, and whether it is required for merge. All gates execute on CPU in hosted CI with no GPU needed; GPU work is checked indirectly through the structured records it produces.

## Motivation

The benchmark relies on invariants that human reviewers cannot reliably verify by eye at scale: every published number must carry its labels (AGENTS.md rule 2), derived numbers must be computed rather than hand-typed (rule 3), weakening flags are banned from measured runs (rule 4), verifier commitments must come from the harness record (rule 6), secrets and host identifiers must never be committed (rule 7), prose must stay factual (rule 10), and every dependency must be fully pinned (working practice). Section 12 of the initial specification summarised five CI checks in a single sentence, which was too thin to guide implementation, specify merge-blocking status, or let contributors run the checks locally before pushing.

Concrete mistakes the pipeline must catch automatically:

- A contributor edits `run.json` by hand to change a mean from `103.6` to `111.2` without changing the raw samples. G4 catches the discrepancy.
- An adapter change passes `--unsound-skip-lookup` to the SASH prove command during a measured job. G6 blocks it.
- A results pull request includes a log line exposing a host's IP address. G9 catches it.
- A system manifest pins an upstream commit using an abbreviated hash like `eb95bfa`. G7 rejects it.

## Goals

- Enforce every mechanically checkable rule in AGENTS.md through a dedicated, named gate.
- Run G2 through G9 locally via `uv run iproofs validate` on a clean checkout in under 60 s for a tree containing 1,000 run directories (a performance target rather than a measurement; see [docs/spec/08-performance-budget.md](../docs/spec/08-performance-budget.md)).
- Format every failure message with the file path, in-file location (JSON Pointer or line number), gate id, rule id, and a suggested fix where possible.
- Keep all gates deterministic so the same repository tree produces the same verdict on every machine.

## Non-Goals

- Auditing the cryptographic soundness of a prover or verifying that a claim card's statements are true; claim cards are verified by reviewers reading the cited upstream sources (RFC-0002).
- Running GPU workloads inside CI. Hosted CI runners lack H100 GPUs, and running dedicated GPU runners continuously conflicts with the cost model.
- Enforcing Python style conventions beyond what `ruff` and `mypy` check.
- Parsing free-form Markdown prose to verify that every number carries labels. Text heuristics for that are fragile, so reviewers check prose directly while generated reports pull numbers from structured records via templates (RFC-0009 §Reports).

## Proposed Design

### Overview

```
pull request
  -> job lint-and-types      G1 (ruff, mypy strict)
  -> job tests               G1 (pytest unit + property)
  -> job validate            G2 G3 G4 G5 G6 G7 G9   (iproofs validate --all)
  -> job fake-e2e            G10 (docker on the hosted runner, CPU only)
```

If a gate has a bug, it is fixed via a pull request modifying the gate itself. There is no G8, G11 (DCO sign-off), or G12.

The `iproofs validate [PATH ...]` command executes the repository tree gates. With no arguments it validates the tree rooted at the current working directory; `--all` ignores git state and checks every matching file; `--changed-since <ref>` scopes G2 through G9 to files changed since `<ref>` plus any files that depend on them (such as run directories referencing a modified workload or system manifest). On pull requests, CI runs `--all --changed-since origin/<base>` once so every file is checked alongside the append-only check against the base branch; on the default branch, CI runs `--all`.

On a developer's machine, single-file checks that have no cross-file dependencies (G2 schema validation of individual documents, G3, and G9) reuse cached verdicts whenever the file's bytes, this package's source, the schema tree, and parser versions are unchanged (`iproofs.validate.memo`). Because that cache lives in the user's cache directory rather than in the repository, CI always starts cold and evaluates every check fresh. Passing `--no-cache` forces a cold run locally, and `iproofs release freeze` never consults the cache.

### Failure message format

Each gate failure writes one line to stdout in the following format:

```
<gate> <path>[#<json-pointer> | :<line>] <rule-id>: <message>[ (fix: <hint>)]
```

For example: `G5 results/v0.1/sash/2026-12-02-sash-sash-l31-8b-c4096-prover-h100-1/run.json#/metrics/rate_prove.steady INV-QTY-3: unit token/s requires a scope (fix: set scope to one of setup, commit, ...)`.

Failures are sorted by gate id, then path bytes, then JSON Pointer. After printing the list, the tool writes a summary line `validate: <n> failures in <m> files` to stderr. The process exits 1 if any check failed, 0 if all passed, and 2 on invalid CLI usage. Passing `--format json` outputs a JSON array of `{gate, path, pointer, line, rule, message, hint}` objects for programmatic consumption.

### G1 Lint, types and tests

- `uv run ruff check .` and `uv run ruff format --check .` using the configuration in `pyproject.toml`.
- `uv run mypy --strict harness/src/iproofs`.
- `uv run pytest harness/tests/unit harness/tests/property -q` under the Hypothesis `ci` profile (`max_examples=200`, `derandomize=True`) so property tests remain deterministic in CI.
- Adapter fixture tests: `uv run pytest systems/*/tests -q` (CPU-only tests against stored fixtures, RFC-0005).
- Repository policy tests: `uv run pytest harness/tests/repo -q`, enforcing module import layers ([01](../docs/spec/01-architecture.md#module-boundaries)) and the flaky-test quarantine rules ([07](../docs/spec/07-testing-strategy.md#flaky-test-policy)).

### G2 Schema validation

Rule: every schema-backed document in the repository must validate against the schema named in its `schema` field (RFC-0012). In addition, every file under `schema/*/examples/valid/*` must pass validation, and every file under `schema/*/examples/invalid/*` must fail with an error message containing the text in its companion `.reason` file.

Inputs: files matching `systems/*/claim.yaml`, `systems/*/claims/*.yaml`, `systems/*/{system,external,controls}.yaml`, `workloads/**/*.yaml`, `reference/*.yaml`, `targets/**/*.yaml`, `releases/*/release.yaml`, `releases/*/index.json`, `results/**/{run,manifest,controls}.json`, `web/_data/facts.json`, and `schema/*/examples/**` (`web/_data/criteria.json` was included until 2026-11-15).

G2 also runs cross-document checks (`XREF-n` and `PM-n`):

- `XREF-1`: every `run.json` references a workload id and version present in `workloads/`, a system present in `systems/`, and a profile present in the release's reference file.
- `XREF-2`: every `manifest.json` image digest matches the image digest recorded in its sibling `run.json`.
- `XREF-4`: every `releases/<r>/release.yaml` references only existing run directories and an existing reference file.
- `XREF-5`: every target references a metric id defined in the RFC-0004 formula registry or raw metric list.
- `PM-1` and `PM-2` ([RFC-0015 §Precision matching](0015-reference-rows.md#precision-matching)): a reference system running at a different precision than the workload's served precision must declare a substitution (`PM-1`); substitutions may never lower the bit width, and every quantity in a substituted reference row must carry `quality.precision_substituted: true` (`PM-2`).
- `web/_data/criteria.json` was previously validated against `criteria/1` alone (amended 2026-11-15: the file was deleted on 2026-11-15 because it used RFC-0016's vocabulary, such as Formally verified "yes" from documents, which no page reads; the v0.1 version remains in git history at `b9dfa3e`, and it is no longer a G2 input).

G2 also enforces two repository-shape rules:

- `APP-1`: on pull requests, no path under `results/` that already exists on the base branch may be modified or deleted, and no new file may be added inside an existing run directory ([RFC-0009 §Append-only rule and corrections](0009-results-and-publication.md#append-only-rule-and-corrections)).
- `SIZE-1`: no committed file outside `results/*/*/*/logs/` may exceed 5 MiB, and no run directory may exceed 10 MiB, keeping weights and proofs out of git (AGENTS.md rule 8). Because a serving ladder run (RFC-0018 CO-4) answers roughly 8,000 requests whose 512-token replies would add about 60 MB to `run.json`, the runner instead writes those token ids to an adjacent `replies.jsonl` file, retains `claimed_tokens` on each output, and records the file's SHA-256 digest in `run.json`. `replies.jsonl` is uploaded to the storage bucket alongside the run and excluded via `.gitignore`; `iproofs serving split-replies RUN_DIR` applies the same split retroactively to older runs (owner decision, 2026-11-12).

### G3 JSON format check

Rule (`FMT-1`): every committed `*.json` file outside `schema/` (schema files are hand-authored) must satisfy `bytes == dumps(json.loads(bytes))` under the canonical writer from RFC-0012. Failures suggest running `iproofs fmt <path>`, an internal maintenance subcommand that rewrites files canonically and is not part of the public CLI.

### G4 Derived recompute

Rule: for every run directory, `iproofs derive <run-dir> --check` recomputes every quantity with `grade: derived` from the stored raw quantities and the release's reference file, requiring exact `==` equality (or `null` with the identical `null_reason` when the formula yields null). Rule `DER-1` fires on value mismatches, `DER-2` on unknown formula ids, and `DER-3` on missing formula inputs. Failure messages include the formula id, the input JSON Pointers, and both values formatted with `repr`. The same check runs on aggregate statistics across repetitions inside `releases/*/index.json`.

### G5 Label check

Rule: every quantity must satisfy INV-QTY-1 through INV-QTY-8 from [RFC-0012 §Invariants](0012-schemas-and-serialization.md#invariants). While most of those constraints live in the JSON Schema and fire in G2, G5 enforces the graph-level checks that JSON Schema cannot express:

- `LBL-1` (second half of INV-QTY-3): any `ratio` derived from a rate carries the scope of the denominator rate.
- `LBL-2` (INV-QTY-6): the derivation formula id exists at the specified harness version, and every pointer in `source.inputs` resolves to a valid quantity.
- `LBL-5` (INV-QTY-6a, INV-QTY-9): a derived quantity's tier equals the lowest tier among its inputs, and its `quality` flags equal the logical OR of its inputs' flags.
- `LBL-3` (INV-QTY-4): every quantity inside `run.json` or `controls.json` has tier `reported`.

### G6 Policy check

Rule: no measured run may use a configuration that weakens the system's statement.

- Input: the `forbidden_flags: [string]` field in each `systems/<name>/system.yaml` (for SASH, this includes the glob `--unsound-skip-*`; exact entries come from upstream documentation at the pinned commit and are confirmed in the adapter issue).
- `POL-1`: in every `manifest.json` with `control: false`, no token in any recorded command line (`manifest.commands[].argv`) may match a forbidden glob (case-sensitive `fnmatch`).
- `POL-2`: every run with `control: true` may contain only verdict counts as measured quantities and must be excluded from all release tables other than the controls table (verified against `release.yaml`).
- `POL-3`: no adapter entrypoint source file (`systems/<name>/entrypoint*`) may contain a literal matching a forbidden glob outside a branch guarded by the job's `control` flag. This text check accepts explicitly listed lines in `systems/<name>/policy-allow.txt` (file and line content), which must also be documented with their guards in the adapter README and verified by reviewers.

### G7 Pin check

- `PIN-1`: every commit reference in `system.yaml`, `claim.yaml`, `claims/*.yaml` (`upstream.commit`), `external.yaml` source URLs, Dockerfile `ARG UPSTREAM_COMMIT=` declarations, and `git checkout` lines must be a full 40-character lowercase hex hash.
- `PIN-2`: every container image reference in Dockerfiles (`FROM`), `system.yaml`, and manifests must use `<repo>@sha256:<64 hex>`. Bare tags fail; `<repo>:<tag>@sha256:...` is permitted with the tag treated as informational.
- `PIN-3`: every workload must specify `model.digest`, per-file digests, `prompts.corpus_digest`, and a 40-hex `model.revision`.
- `PIN-4`: every `reference/<release>.yaml` must pin the NVIDIA driver, CUDA runtime, and container runtime versions as exact strings without ranges.
- `PIN-5`: every toolchain version in an adapter Dockerfile must be exact (no `latest`, no `^` or `~` ranges in pip or cargo installs, and `apt-get install` packages pinned via `=` or anchored by the base image digest as documented in the adapter README).

### G8 Neutral-language lint

Withdrawn on 2026-11-10: the word list and emoji check (`LANG-1`, `LANG-2`) caught no factual errors. Factual, restrained wording remains an author and reviewer responsibility (AGENTS.md rule 10), without an automated gate.

### G9 Secrets and identifiers scan

Rule `SEC-n`: no committed text file, including logs under `results/`, may match any of the patterns below. The compiled regular expressions live in `iproofs.log.patterns` (layer 0, respecting the module boundaries in [01](../docs/spec/01-architecture.md#module-boundaries)) and are shared by both `iproofs.validate` and the log redactor (`docs/spec/05-observability.md`), ensuring the scanner searches for the exact same patterns the redactor strips.

| Rule | Pattern (Python `re`) | Target |
|---|---|---|
| `SEC-1` | `hf_[A-Za-z0-9]{30,}` | Hugging Face tokens |
| `SEC-2` | `gh[pousr]_[A-Za-z0-9]{36,}` | GitHub tokens |
| `SEC-3` | `AKIA[0-9A-Z]{16}` | AWS access key ids |
| `SEC-4` | `-----BEGIN [A-Z ]*PRIVATE KEY-----` | Private keys |
| `SEC-5` | `(?<![\d.])(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?![\d.])` excluding `127.0.0.1`, `0.0.0.0` and version-like strings in a `version` field | IPv4 literals |
| `SEC-6` | IPv6 literals with at least two `:` groups of hex, excluding `::1` | IPv6 literals |
| `SEC-7` | `(?i)\b([0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b` | MAC addresses |
| `SEC-8` | `GPU-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` | NVIDIA GPU UUIDs |
| `SEC-9` | `(?m)^\s*(Host|HostName|IdentityFile)\s+\S+` in any file | SSH config fragments |
| `SEC-10` | `/home/[a-z_][a-z0-9_-]*/`, `[/]Users/[^/\s]+/` | Absolute home paths |
| `SEC-11` | `(?i)(token|secret|password|api[_-]?key|credential)\s*[:=]\s*['"]?[A-Za-z0-9/+_\-]{16,}` | Assignments of secret-like values |

Allowlist: `schema/*/examples/invalid/` and `harness/tests/fixtures/secrets/` contain intentional test matches for the scanner itself and are skipped. False positives anywhere else are resolved by editing the text rather than expanding the allowlist.

None of the machine-record fields allowed by RFC-0006 (GPU model, driver version, kernel version) trigger these patterns, so `manifest.json` requires no scanning exceptions.

### G10 Fake-system end-to-end

The fake systems (`systems/fake` and `systems/fake-broken`) are small Python programs packaged in CPU-only container images. `systems/fake` commits to toy weights by hashing them, proves by emitting a body part and an HMAC-SHA256 tag keyed by the commitment over the request, claimed output, and body ([RFC-0005](0005-adapter-contract.md#reference-implementations)), and verifies by recomputing the tag. Because it is sound for this toy relation, every applicable shared negative control must be rejected. `systems/fake-broken` pairs the same prover with a verifier that accepts unconditionally.

Rule `E2E-1`: on the hosted runner, using workload `fake-tiny-ci` (a toy workload with 8 prompt tokens, 1 output token, batch size 2, and 3 batches per session in `workloads/fake-tiny-ci.yaml`) and profile `ci-cpu` (a CPU-only profile in `reference/ci.yaml`), the job executes:

```
uv run iproofs run --system fake --workload fake-tiny-ci --profile ci-cpu --repetitions 3 --results "$RUNNER_TEMP/results" --control-suite
uv run iproofs run --system fake-broken --workload fake-tiny-ci --profile ci-cpu --repetitions 1 --results "$RUNNER_TEMP/results" --control-suite
uv run iproofs validate --all "$RUNNER_TEMP/results"
```

The job then asserts that:

- Three `fake` run directories are created and pass G2 through G5.
- Every honest `fake` proof receives `accept`, and every applicable shared control is `rejected` (C5, C6, and C8 may return `invalid_call` per RFC-0008).
- `fake-broken` has every applicable control `accepted` and is marked failed in its controls summary, while `iproofs validate` accepts the record itself as valid (a broken verifier is a valid benchmark result, not a malformed file).
- GPU quantities on `ci-cpu` are `null` with `null_reason: not_applicable`.
- Re-running `iproofs derive --check` passes on every generated run directory.

The fake-system images are built during the job from `systems/fake*/Dockerfile` using digest-pinned base images, cached in Docker's layer cache keyed by Dockerfile digest.

### G12 Link and anchor check

Withdrawn on 2026-11-10 along with its weekly external-link job (`LNK-1`, `LNK-2`): a broken link does not produce an inaccurate result, and reviewers check links directly.

### CI workflow structure

- A single workflow file, `.github/workflows/ci.yml`, runs the jobs shown above on `pull_request` and on `push` to `main`. Because all gates are deterministic, there is no scheduled cron run.
- Runner environment: hosted Ubuntu 24.04, Python installed via `uv python install` from `.python-version` (3.12), and dependencies installed via `uv sync --frozen` so the lockfile is authoritative and stale locks fail immediately.
- Caching: the `uv` cache is keyed by `uv.lock` digest, and the G10 Docker layer cache is keyed by the fake Dockerfiles.
- Third-party GitHub Actions are pinned by full commit hash rather than tag, applying the PIN rules to CI itself.
- Workflow permissions are restricted to `contents: read`. Pull request jobs receive no secrets and upload nothing.
- Wall-time target for the complete workflow on a hosted runner: 10 minutes.

### Local use

```
uv sync
uv run iproofs validate                 # tree gates on the working copy
uv run pytest harness/tests -q          # G1 tests
make ci                                 # all CPU gates in CI order, including G10 if docker is present
```

`make ci` wraps the exact commands run by `.github/workflows/ci.yml` so local checks and CI cannot drift apart. Contributors without Docker installed can still run every gate except G10.

### What runs on GPU hosts instead

GPU jobs (`iproofs run` on `prover-h100`) are executed manually on dedicated GPU hosts using each adapter's README runbook and `docs/runbooks/gpu-run.md`. They are not part of CI. Their output records enter the repository through pull requests, where G2 through G9 (and previously G12) validate them like any other file. Each adapter's CPU fixture tests under G1 cover its parsing and mapping logic without needing a GPU.

### Failure modes of the gates themselves

| Failure | Response |
|---|---|
| A gate produces a false positive that blocks a legitimate change | Fix the gate in its own pull request with a regression test; never bypass it |
| A gate silently passes everything (for example because a glob matches zero files) | Every gate ships with a known-bad fixture under `harness/tests/fixtures/gates/<gate>/`; the test suite fails if the gate lets that fixture pass |
| Validation slows down as `results/` grows | Single-file checks reuse cached results for unchanged bytes on local machines (`iproofs.validate.memo`), while CI runs uncached across every file |

## Alternatives Considered

**Enforce checks via pre-commit hooks.** Pre-commit hooks are helpful for catching issues early, but they are optional and easily skipped. We offer the same commands as an optional pre-commit setup while keeping CI authoritative.

**Use third-party secret-scanning services.** External scanners require no custom code, but they cannot be reproduced locally with identical results, add a third-party dependency to the project, and would not stay in sync with the harness's own log redactor patterns.

**Rely on JSON Schema checks without graph checks.** Schema validation alone is simpler, yet the two most important integrity rules (recomputing derived values and propagating scopes onto ratios) require walking the derivation graph, which JSON Schema cannot express.

**Run a small GPU job in CI on a self-hosted runner.** While that would exercise the GPU measurement code automatically, running untrusted pull-request code on a self-hosted GPU host creates a serious security exposure and ongoing infrastructure cost. Instead, the fake system and stored fixtures test the harness logic in CI, while GPU paths are verified via runbook tests on a project-controlled host.

**Use an LLM or classifier for language checks.** Automated classifiers are non-deterministic and opaque. When a check existed, a simple word list was at least predictable and reviewable.

## Drawbacks

- A keyword list produces occasional false positives and misses paraphrases, leaving reviewers responsible for tone.
- Because POL-3 is a static text scan, dynamically constructed flag strings could evade it. G6 POL-1 on recorded command lines serves as the primary enforcement mechanism, with POL-3 acting as an early warning.
- Eleven originally planned gates (nine active) are a lot of rules for new contributors to absorb, though the uniform failure format and `make ci` ease the onboarding cost.
- IPv4 pattern matching can flag version-like strings outside `version` fields, occasionally forcing authors to rephrase text.

## Migration / Rollout

1. Land G1, G2, and G3 first, as they depend only on the schemas and the canonical JSON writer.
2. Add G4 and G5 alongside the derivation module, G10 with the fake systems, and G7 and G9 with their pattern modules. Each gate becomes active in CI in the pull request that introduces it.
3. G6 is required from the outset (passing vacuously at first) and takes effect once SASH's `system.yaml` populates `forbidden_flags`.
4. Branch protection and repository settings are documented in `docs/runbooks/repository-settings.md`.

## Testing Strategy

- `harness/tests/unit/validate/test_g3_format.py::test_detects_reordered_keys`, `::test_detects_crlf`, `::test_accepts_canonical`.
- `test_g4_derive.py::test_hand_edited_mean_fails` (perturbs a stored mean by one ULP via `math.nextafter` and expects `DER-1`) and `::test_unknown_formula_fails` (`DER-2`).
- `test_g5_labels.py::test_ratio_without_scope_fails` (`LBL-1`) and `::test_run_tier_not_reported_fails` (`LBL-3`).
- `test_g6_policy.py::test_measured_run_with_unsound_flag_fails` (manifest `argv` contains `--unsound-skip-x` with `control: false`, expecting `POL-1`) and `::test_control_run_with_flag_passes`.
- `test_g7_pins.py::test_short_hash_fails` (`eb95bfa`), `::test_tag_only_image_fails` (`python:3.12-slim`), and `::test_tag_and_digest_passes`.
- `test_g9_secrets.py`: one test case per pattern `SEC-1` through `SEC-11` using fixtures under `harness/tests/fixtures/secrets/`, plus `::test_machine_record_example_passes` against the RFC-0006 example record and `::test_redactor_and_scanner_share_patterns` verifying that the redactor and scanner share the exact same pattern list.
- `test_g10_e2e.py`: implements the G10 job itself with the assertions listed in §G10.
- Every gate also carries a known-bad fixture under `harness/tests/fixtures/gates/<gate>/bad/` that must trigger a failure, guarding against silent no-op gates.

## Decisions

- Q1. Withdrawn alongside G8.
- Q2. No GPU job runs on a schedule; runbook tests are executed before each campaign to catch measurement regressions.

## References

- AGENTS.md hard rules 2 to 4, 6, 7, and 10, plus working practice.
- [RFC-0012](0012-schemas-and-serialization.md) for the canonical writer, labelled quantities, and digests.
- [RFC-0004](0004-metrics-timing-grades.md) for formulas, [RFC-0005](0005-adapter-contract.md) for `system.yaml`, and [RFC-0008](0008-negative-controls.md) for negative controls.
- Developer Certificate of Origin 1.1, https://developercertificate.org/
- GitHub Markdown heading anchor rules.
