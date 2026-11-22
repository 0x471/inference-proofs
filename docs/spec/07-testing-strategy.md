# 07. Testing strategy

The CI gates executing these suites are specified in [RFC-0013](../../rfcs/0013-validation-and-ci.md), and mechanism-specific test cases appear in each RFC's Testing Strategy section. This document defines where each test layer lives, what it verifies, and the conventions all tests follow.

## Principles

1. **CPU first.** Everything except the GPU measurement path must be testable on an ordinary laptop with no GPU (AGENTS.md working practice). GPU-specific code stays thin and sits behind interfaces backed by CPU fakes.
2. **Hand-computed truth.** Every derived metric has at least one test whose expected value was calculated by hand, with the arithmetic documented in a comment (AGENTS.md working practice). Derivation functions must never be used to generate their own test expectations.
3. **Valid and invalid examples.** Every schema includes both valid examples that must pass and invalid examples that must fail, with each invalid case identifying the rule it violates (RFC-0012).
4. **Every gate has a bad fixture.** A gate that accepts everything is broken; every CI gate ships with at least one known-bad fixture it must reject (RFC-0013).
5. **Determinism.** No test may depend on wall-clock time, network access, locale, hash seed, or execution order. Hypothesis runs in derandomized mode in CI.
6. **Failures are data.** Failure-path tests assert the complete failure record (kind, step, exit code, and trailing lines), not merely that an exception was raised.

## Layers

| Layer | Location | Runs where | Gate | What it proves |
|---|---|---|---|---|
| Unit | `harness/tests/unit/` | Anywhere | G1 | Pure functions: serialization, digests, quantities, derivations, statistics, mutations, redaction, and CLI argument handling |
| Property | `harness/tests/property/` | Anywhere | G1 | Invariants across generated inputs |
| Schema examples | `schema/*/examples/{valid,invalid}/` | Anywhere | G2 | Schemas accept valid documents and reject invalid ones per the RFCs |
| Gate fixtures | `harness/tests/fixtures/gates/<gate>/` | Anywhere | G1 | Each CI gate catches its known-bad inputs |
| Adapter fixtures | `systems/<name>/tests/` | Anywhere | G1 | Each adapter translates stored upstream outputs into valid `adapter-out/1` JSON and maps documented exit codes to the right verdicts |
| Golden | `harness/tests/golden/` | Anywhere | G1 | Exact bytes of generated site files and release indexes for fixture releases |
| Fake-system integration | `systems/fake`, `systems/fake-broken`, `harness/tests/integration/` | Anywhere with Docker | G10 | Full job lifecycle, negative controls, and run directory serialization end to end |
| GPU runbook tests | `docs/runbooks/gpu-run.md`, `harness/tests/gpu/` | GPU host, run manually | None (pre-campaign checklist) | NVML sampling, cgroup accounting, NUMA binding, and real adapters on real hardware |

## Named suites and minimum cases

The suites below represent the baseline floor; individual RFC Testing Strategy sections add further cases.

### Unit

- `test_serialize.py`, `test_digest.py`, `test_yaml.py`, `test_quantity.py`, `test_ids.py`, and `test_model_drift.py`: covered in [RFC-0012 §Testing Strategy](../../rfcs/0012-schemas-and-serialization.md#testing-strategy).
- `test_derive_formulas.py`: at least one hand-computed test case per RFC-0004 formula, formatted like this:

  ```python
  def test_cost_per_1k_tokens_hand_computed() -> None:
      # 2.0 s/token * 1000 tokens * 1 GPU * 3.60 USD/gpu_hour / 3600 s/h = 2.0 USD per 1k tokens
      assert derive.cost_per_1k_tokens(s_per_token=2.0, gpus=1, usd_per_gpu_hour=3.60) == 2.0
  ```

  Inputs are chosen so the expected result is exact in IEEE 754 binary64, with the arithmetic written out in a comment. These values are synthetic test fixtures, not measurements, and are never published.
- `test_derive_nulls.py`: verifies that any formula given a null or zero denominator returns `value: null` with the appropriate RFC-0004 `null_reason`, never `NaN` or `Infinity`.
- `test_stats.py`: tests `n = 0, 1, 2, 3`, verifying that failed repetitions are excluded from the mean and tallied in `n_failed`, that `stdev` is null when `n < 2`, and that inputs are ordered by repetition.
- `test_scopes.py`: verifies that `prove.steady` over release times `[10 s, 12 s, 15 s]` with token counts `[100, 100, 100]` yields 200 tokens over 5 s, that a single proof returns null with `fewer_than_two_proofs`, and that `whole_wall` starts at `commit` rather than `setup`.
- `test_mutations.py`: verifies that each control C1 to C8 applies the exact RFC-0008 mutation (C1 replaces token `t` with `(t+1) mod vocab_size`; C5 truncates the largest part in half; C6 flips a single bit at the seeded offset; C7 swaps two proofs; C8 drops one part; and C5, C6, and C8 only touch parts declared in `verify_reads`) deterministically for a given seed.
- `test_redact.py`: verifies that every Gate G9 pattern is stripped from log output, plus `test_redactor_and_scanner_share_patterns`.
- `test_errors.py`: verifies that every `ErrorKind` maps to its RFC-0010 exit code and that failure records cap redacted `last_lines` at 50 lines.
- `test_machine_record.py`: verifies against a fixture `/proc` and `/sys` tree that the collected machine record contains only RFC-0006 fields and omits all excluded identifiers.

### Property (Hypothesis)

- `test_roundtrip`, `test_digest_order_independent`, and `test_fsum_order_independent` (RFC-0012).
- `test_rate_inverse`: rather than asserting bitwise equality for `seconds_per_token == 1 / tokens_per_second` (which floating-point rounding can violate), confirms both metrics are computed directly from raw inputs via their own formulas, preventing derived metrics from chaining off other derived metrics.
- `test_target_least_favourable_case`: verifies that for any set of repetitions and a `<=` threshold, an evaluation of `meets` holds only when every repetition is at or below the threshold.
- `test_mutation_changes_digest`: confirms that every byte-level control mutation alters the proof digest.

### Adapter fixtures

Each adapter directory `systems/<name>/tests/` stores small captured upstream outputs from a GPU host (text output, exit codes, and trailing lines, never model weights or large proofs) and verifies four properties:

- `test_verdict_mapping`: every documented upstream exit code and final output line at the pinned commit maps to the verdict specified in the adapter README (such as the FlashProve mapping in [RFC-0005](../../rfcs/0005-adapter-contract.md) or SASH's segment and grid verdicts).
- `test_out_json_valid`: the adapter's output serializer produces schema-valid `adapter-out/1` JSON for every stored case.
- `test_forbidden_flags_guarded`: measured `prove` commands never include any forbidden flag, while control commands include only the specific flag declared by that control.
- `test_dockerfile_rules`: the adapter Dockerfile complies with build rules B1 to B7 of [RFC-0014](../../rfcs/0014-provenance-and-integrity.md#adapter-image-build).

### Golden

- `golden/site/`: snapshots every generated file written by `iproofs site build` (HTML pages, `search.json`, `vercel.json`, and preview-card sources, excluding copied static assets) for the placeholder release with test-only edge cases (`harness/tests/fixtures/placeholder_release.py`, `extras=True`): two systems across two workloads (one with two claim cards), two reference rows whose runs all failed, a failed run, a superseded run, an ineligible run, a withdrawn run, an override, an unexpected control outcome, and one relying-party target. `test_site_golden.py` also verifies reproducibility across repeated builds, a depth-1 clone, and a copy without `.git` (CLI-4), checking all assertions in [RFC-0009 §Testing Strategy](../../rfcs/0009-results-and-publication.md#testing-strategy). Regenerate golden files only with `uv run pytest --update-golden` in a pull request that explains the diff.
- `golden/index/`: byte-exact snapshot of `index.json` for the fixture release built by `harness/tests/fixtures/release_tree.py`.
- End-to-end site test (`integration/test_site_e2e.py`): runs `iproofs derive --check` on the placeholder release's synthetic runs, executes `iproofs release freeze` and `iproofs site build` through the CLI, and verifies that every rendered figure points to an `index.json` statistic and prints its exact value. In addition, `web/test_*.py` (`uv run pytest web -q`, run by the `site` workflow) validates sort keys, preview cards, and search results against hand-computed cases.

### Fake-system integration

On hosts lacking NVML or cgroup v2 (such as macOS laptops or hosted CI runners), the `ci-cpu` profile activates null readers ([RFC-0011 §Portability](../../rfcs/0011-measurement-and-sampling.md#portability), `iproofs.measure.NullCgroupReader`): GPU, host-memory, and CPU metrics for fake runs are recorded as null with `null_reason: not_applicable`, and the proof release watcher falls back from inotify to polling. GPU profiles never fall back to null readers; missing NVML fails immediately with `ErrorKind.environment` (`harness/tests/unit/test_portable_readers.py`).

Gate G10 ([RFC-0013 §G10](../../rfcs/0013-validation-and-ci.md#g10-fake-system-end-to-end)) is implemented in `harness/tests/integration/test_fake_e2e.py` and executed by the `fake-e2e` job in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml). When `IPROOFS_REAL_DOCKER=1` is set (`make e2e` and the CI `fake-e2e` job), the suite builds the fake Docker images and runs real containers; otherwise it uses the stand-in `docker` shim at `harness/tests/fixtures/fake-docker` so the same tests run anywhere in the regular test job. Fault injection uses `IPROOFS_FAKE_FAULT` inside the fake image (`exit`, `sleep`, `escape`, `network`). Alongside `test_e2e_fake_and_fake_broken` (rule `E2E-1`), the module covers:

- `test_failed_step_recorded`: injects exit code 3 during `prove` and asserts the run is written as `failed` at step `prove` with exit code 3 and trailing log lines, and passes `iproofs validate`.
- `test_timeout_recorded`: forces `prove` to sleep past its timeout and asserts the container is killed and recorded as `ErrorKind.timeout`.
- `test_path_traversal_rejected`: emits `../../etc/passwd` as a proof part in `out.json` and asserts rejection with `ErrorKind.adapter`.
- `test_commitment_from_record`: verifies RFC-0014 commitment isolation.
- `test_network_none`: attempts to open a network socket during `prove` and verifies the attempt fails (real Docker containers only).

### GPU runbook tests

Executed manually on the GPU host before every measurement campaign and logged in the campaign checklist (not run in CI):

- `harness/tests/gpu/test_nvml_sampler.py`: confirms at least 10 Hz sampling over 60 s, accurate gap accounting, and accurate peak memory reporting for a known fixed-size CUDA allocation.
- `test_cgroup_reader.py`: confirms `memory.peak` and sampled `anon` memory match a known container allocation.
- `test_numa_binding.py`: confirms the selected CPU set sits on the GPU's NUMA node and prefers distinct physical cores.
- One full `fake` run on `prover-h200`, plus one short real job per adapter on its smallest workload with controls enabled.

## Determinism tests

- Byte-identical `index.json` and generated site output across two independent freezes in different working directories (RFC-0009).
- Byte-identical prompt sets for a given seed and corpus across hosts (`test_prompts_deterministic` runs in CI using a small fixture corpus and tokenizer).
- Identical proof digests for `systems/fake` across repeated runs with the same seed (`deterministic_proofs: true` in `system.yaml`).

## Sharding

On hosted CI, the unit, property, and schema-example suites split across three shards per Python version (job `test-shard`). The job temporarily used six shards starting on 2026-11-08 when three shards grew to 5 to 6 minutes; on 2026-11-10 caching the schema registry once per process rather than once per call cut development-machine CPU time from 455 s to 177 s (one run each, 8 workers), allowing CI to return to three shards while staying within B-CI-UNIT ([08](08-performance-budget.md)) on 2-vCPU runners.

Setting `IPROOFS_SHARD=i/n` selects the `i`-th of `n` file partitions (`harness/tests/conftest.py`). Files are assigned whole using greedy balancing, placing the file with the most tests first (breaking ties by path) into whichever shard currently has the fewest tests. That guarantees every test runs in exactly one shard, all tests in a file stay together, module fixtures build once per shard instead of across all shards, and shard sizes differ by at most one file. Inside each shard, `pytest-xdist` distributes whole files per worker (`--dist loadfile`) so module fixtures build once per worker as well. The two shared placeholder release builds (the deployed fixture and the test-only edge-case fixture, each containing a frozen tree and built site) are exposed as read-only session fixtures (`harness/tests/fixtures/builds.py`); each worker builds them at most once and verifies both file digests and permissions at session teardown so even root writes or `chmod` changes are caught. Any test that mutates a release tree copies it first. Running `make ci` executes the same commands locally without sharding.

## Flaky-test policy

Any intermittent test failure is treated as a bug. On the first occurrence, open an issue with the failing log; within 7 days, either fix the test or quarantine it with `@pytest.mark.quarantine` citing the issue number (quarantined tests still execute in CI but do not block merges). Any quarantined test older than 30 days blocks the next harness release ([docs/spec/09-release-and-versioning.md](09-release-and-versioning.md)). Automatic test retries in CI are not permitted.
