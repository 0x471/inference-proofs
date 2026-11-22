# Contributing

Thank you for helping with this project. We run provers and rank the systems that pass six checks within each model's rung ([RFC-0018](rfcs/0018-level-1-ladder.md)); we do not build or certify provers ourselves. Before opening a pull request, read [AGENTS.md](AGENTS.md) (which applies to both human contributors and coding agents), [docs/SPEC.md](docs/SPEC.md), and the RFCs relevant to your change.

## Issues

- Open an issue to report a bug, ask a question, or make a proposal. Include what you observed, what you expected, and the relevant commit, image digest, or run ID.
- Do not report a security vulnerability or a verifier that accepts a tampered proof in a public issue. Follow [SECURITY.md](SECURITY.md) instead.

## Pull requests

- Explain clearly what changed and why.
- Any change to the benchmark methodology must also update the corresponding RFC ([rfcs/](rfcs/README.md)).

## Running jobs

A run can record who executed it, as self-declared by the runner, via `iproofs run ... --runner HANDLE --runner-org ORG --affiliated SYSTEM` or the environment variables `IPROOFS_RUNNER`, `IPROOFS_RUNNER_ORG`, and `IPROOFS_RUNNER_SYSTEMS` (comma-separated). Only the handle, organisation, and system IDs are stored; never include an account name or host identifier (AGENTS.md rule 7).

## Editing claim cards

A claim card records what a system's documentation states at the pinned commit, with a source link for every stated field and "not stated" wherever the documentation is silent ([RFC-0002 §Rules](rfcs/0002-claim-card.md#rules)). Running `uv run iproofs validate` checks every card against its schema, its cited sources, and the commit pin in `system.yaml`.

## Tests and CI

- Every adapter must include a CPU-only test against stored fixtures, every schema must include valid and invalid examples, and every derived metric must include a test against a hand-computed case ([docs/spec/07-testing-strategy.md](docs/spec/07-testing-strategy.md)).
- Run the full check suite locally before pushing: `make ci` runs the same commands as `.github/workflows/ci.yml`. See [RFC-0013](rfcs/0013-validation-and-ci.md) for the complete gate list.
- `uv run iproofs validate` runs the repository tree gates (schemas, cross-references, append-only results, file sizes, canonical JSON, derived recomputation, labels, policy, pins, and secrets) and outputs one line per failure. Pass `--format json` for machine-readable output, and `--changed-since origin/main` to include the append-only check against a base branch.
- Treat any intermittent test failure as a bug: open an issue with the failure log, then either fix the test or quarantine it within 7 days using `@pytest.mark.quarantine(issue=<n>)` ([docs/spec/07-testing-strategy.md §Flaky-test policy](docs/spec/07-testing-strategy.md#flaky-test-policy)). Failing tests are never retried automatically.
- Neutral language (AGENTS.md rule 10) is enforced by authors and reviewers rather than an automated gate.
- GPU workloads run on dedicated GPU hosts, never in hosted CI.

## Licences

Code is licensed under Apache-2.0, while specifications, data, results, and reports are licensed under CC BY 4.0 (see the licence section of [README.md](README.md)). By contributing, you agree to license your contribution under these terms.

## Conduct

Everyone participating in this project is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
