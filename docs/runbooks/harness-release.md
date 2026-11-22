# Harness release

Use this checklist to cut a harness version (`harness-v<version>`), following [docs/spec/09-release-and-versioning.md §Release checklists](../spec/09-release-and-versioning.md#release-checklists). Harness versions are released separately from benchmark releases. Complete the steps in order; if any step fails, stop the release until it is resolved.

1. Confirm that all required checks are green on `main` and that no quarantined test is older than 30 days ([07-testing-strategy.md §Flaky-test policy](../spec/07-testing-strategy.md#flaky-test-policy); verified by `harness/tests/repo/test_quarantine.py`).
2. Bump the version in `pyproject.toml`, and move the `Unreleased` entries in [CHANGELOG.md](../../CHANGELOG.md) under the new version heading with the release date.
3. Run `uv build` to produce the wheel and sdist, then verify that `uv run --isolated --with dist/*.whl iproofs --version` succeeds in a clean environment.
4. Tag the release commit as `harness-v<version>`.
5. Attach the built wheel to the release notes for that tag. The harness is not published to a package index ([09 §Decisions](../spec/09-release-and-versioning.md#decisions), Q1).
