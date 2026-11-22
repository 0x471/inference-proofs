# RFC-0014: Provenance, pinning and artifact integrity

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0003, RFC-0005, RFC-0006, RFC-0012

## Summary

Every row published by the benchmark must be rerunnable by an outside party and verifiable against the exact inputs that produced it. This RFC specifies how all inputs are pinned (commits, container images, models, prompt corpora, and toolchains), how adapter images are built, how weights are fetched and verified before any container sees them, what `manifest.json` records, how the harness stores the commitment passed to verifiers (AGENTS.md rule 6), how proofs are digested, and which supply-chain threats this design mitigates. Result files themselves are unsigned (Q1).

## Motivation

[RFC-0007 §Motivation](0007-evidence-tiers-and-reproduction.md#motivation) illustrates why strict provenance matters using the first two benchmarked systems: FlashProve's performance page notes that its measurement scripts are not in the repository, leaving readers unable to reconcile the published figures against run records; SASH publishes run manifests, but its headline manifest shows the producing prover tree was dirty. The benchmark's own runs must do better than both.

The initial specification stated "pin everything" and "the commitment the verifier checks against comes from the harness's own record", without specifying the mechanisms. Concrete failure cases this RFC prevents include:

- An adapter Dockerfile clones `main` of an upstream repository, so rebuilding a month later measures different code under the same row label.
- A weight file on the model host is overwritten under the same revision name, causing a run to silently prove a different model.
- A prover writes a commitment file alongside its proof and a buggy adapter hands that file to the verifier, allowing a forged proof paired with a matching forged commitment to pass.
- An outside party cannot rerun a row because the image digest recorded in the manifest was never pushed to a public registry.

## Goals

- Identify every input to a measured job by an immutable reference: a 40-hex commit hash, an OCI image digest, or a SHA-256 file or tree digest (RFC-0012 §Digests).
- Verify all weight, prompt, and verifier-key digests inside the harness before any container ever receives them.
- Record enough information in `manifest.json` that it, together with public sources, suffices to rerun the job.
- Ensure the verifier always checks against the commitment captured by the harness during `commit`, never against files emitted by `prove`.
- Ensure anyone can pull every container image referenced by a release.

## Non-Goals

- Bit-reproducible container image builds. Reruns pull the exact pinned image digest rather than rebuilding from scratch. Rebuild reproducibility is welcome and recorded when achieved, but is not required in v0.1.
- Cryptographic hardware attestation of the runner host (such as TEE attestation or measured boot); see Q1.
- Auditing upstream code for backdoors. The benchmark pins and records inputs rather than certifying systems (PRD §5).
- Hosting or redistributing model weights (AGENTS.md rule 8).

## Proposed Design

### Pin rules

| Input | Pin form | Where recorded | Checked by |
|---|---|---|---|
| Upstream source | Full 40-hex commit hash | `system.yaml` `upstream.commit`, Dockerfile `ARG UPSTREAM_COMMIT`, `claim.yaml` | G7 `PIN-1` |
| Upstream source archive | `sha256:` digest of the source tarball fetched at build time | `info` output `image_inputs`, manifest | Harness during `info` |
| Base images | `<repo>@sha256:<digest>` | Dockerfile `FROM` | G7 `PIN-2` |
| Adapter image | `<registry>/<repo>@sha256:<manifest digest>` | `system.yaml` `image`, manifest | Harness before every job |
| Toolchains | Exact versions | Dockerfile, adapter README | G7 `PIN-5` |
| Language dependencies | Hash-bearing lockfile (`Cargo.lock` with `--locked`, pip `--require-hashes`, `uv.lock`) | Inside the image, digest in `image_inputs` | Build fails on mismatch |
| Model | Source, 40-hex revision, per-file digests, model digest | `workloads/<id>.yaml` | Harness at resolve, G7 `PIN-3` |
| Tokenizer | Included in the model file set | As above | As above |
| Prompt corpus | Per-file digest and corpus digest | `workloads/prompts/corpus.yaml` | Harness at resolve |
| Prompt set | Prompt seed and prompt set digest | Manifest | Harness after materialisation |
| Harness | Version, git commit, dirty flag, `uv.lock` digest | Manifest | Harness at start |
| Host software | Driver, CUDA runtime, container runtime, and NVIDIA Container Toolkit versions | Machine record (RFC-0006), reference file | Harness against `reference/<release>.yaml` |
| CI actions | Full commit hash | Workflow files | G7 |

Abbreviated hashes, branch names, bare tags without digests, and version ranges are rejected wherever a pin is required. Tags MAY accompany a digest as human-readable context.

### Adapter image build

Each `systems/<name>/Dockerfile` follows seven build rules (RFC-0005 owns the adapter directory layout, while this RFC owns build provenance):

1. **B1 Base by digest.** Every `FROM` instruction references an image digest.
2. **B2 Fetch stage.** A single `fetch` stage downloads all external inputs: the upstream source at its pinned commit (`ADD https://github.com/<org>/<repo>.git#<commit>` or a tarball with `ADD --checksum=sha256:<hex>`) and dependency sources via hash-checked lockfiles. Every download is verified against digests stored in `systems/<name>/inputs.lock` (one tab-separated line per input: `<name>\t<url>\tsha256:<hex>`).
3. **B3 Offline after fetch.** Every `RUN` instruction outside the `fetch` stage runs with `RUN --network=none`. Requiring network access in a later stage is an adapter bug.
4. **B4 No source changes.** Builds apply no patches, `sed` edits, or equivalent modifications to upstream source (AGENTS.md rule 1), using only build flags documented upstream.
5. **B5 Inputs record.** The final image includes `/opt/iproofs/inputs.json`, generated during the build, listing every `{name, url, digest}` input and all toolchain versions. The `info` subcommand returns this file as `image_inputs`.
6. **B6 Clean tree.** Images are built from a clean git checkout of this repository, baking in `adapter_commit` (this repository's commit hash) via a build argument reported by `info`. Building from a dirty working tree sets `adapter_dirty: true`, making the image ineligible for releases (see §Eligibility).
7. **B7 Publication.** Images pulled by hosted providers are pushed to the project registry at `ghcr.io/ai-verification-observatory/` (Q2) and referenced by manifest digest.

Unpushed local images (such as the fake systems in CI or local development builds) are referenced by image ID with `image.digest_kind: "config"`, whereas pushed registry images record `image.digest_kind: "manifest"`. Both kinds may enter a release where applicable.

Development install, generic form (amendment of 2026-11-09; originally drafted for the unmerged `ref-serve-gguf` branch at commit `d842275`): When an adapter's own image is not yet pullable from a registry by a hosted provider, a development run may start from the public engine image named in the Dockerfile's `FROM` line and install the adapter inside that container from the job's repository checkout. Specifically, it copies the files listed in the Dockerfile to their target paths and fetches every entry in `inputs.lock` after verifying each digest (`systems/<name>/dev_install.py` built on `systems/_dev/install.py`; `ref-serve` is the first user, documented in `docs/runbooks/hf-jobs.md`). Such runs record `image.ref` as `local/<the engine image's pull reference>` with that reference's registry digest and `image.digest_kind: "config"`. In this case the digest identifies the underlying engine image rather than a local build's image ID; because the container cannot inspect its own pull reference, the installer verifies everything it can (the Dockerfile's `FROM`, engine version, bound GPUs, and engine environment variables against the image's `ENV`). The adapter code itself is identified by `system.adapter_commit` (the checkout commit) and by `image_inputs`, which lists the engine image digest plus the SHA-256 of every installed adapter file. Because `digest_kind` is `"config"`, a development install is never eligible for a release and never claims to be the digest of a built adapter image. RFC-0006 §Hosted execution permits it alongside local builds supplied via `--image`.

### Model fetch and verification

Both `iproofs fetch-model WORKLOAD` and the `resolved` state of every job (RFC-0010) execute the same verification flow:

```python
def ensure_model(workload: Workload, cache: Path) -> VerifiedModel:
    """Return a read-only directory whose file set and digests equal workload.model.
    Raises IProofsError(kind=integrity) on any mismatch, kind=fetch after 3 failed attempts."""
```

1. Target directory: `$IPROOFS_CACHE/models/<model digest hex>/`, where `IPROOFS_CACHE` defaults to `~/.cache/iproofs`.
2. If the directory is absent, download into a temporary sibling directory via `huggingface_hub.snapshot_download(repo_id=source, revision=<40-hex>, allow_patterns=<exact file list>)`, retrying transient fetch errors per RFC-0010 (up to 3 attempts with 2 s, 8 s, and 32 s backoff).
3. Hash every downloaded file. The file set MUST match the workload's list exactly; any missing file, unexpected extra file, or hash mismatch deletes the temporary directory and raises `ErrorKind.integrity`.
4. Compute the overall model digest (RFC-0012) and verify that it matches `workload.model.digest`.
5. Atomically rename the directory into place and strip write permissions from all files and directories inside it.
6. At the beginning of every job, rehash every file in the cached model directory and verify the digests again. Each file is read once (reusing the per-file hashes to compute the model digest), hashing up to 8 files concurrently. Before 2026-11-10, files were read twice sequentially, which took 359 s to 694 s per job on the Maverick models during v0.1 runs (`integrity.model_rehash` in harness logs under `results/v0.1/`, 32 jobs, tier `reported`). This check occurs outside every timed scope; its duration is logged as the diagnostic event `integrity.model_rehash` in `logs/harness.jsonl` and is never published as a benchmark metric. If a cached directory fails rehashing, the harness moves it to `$IPROOFS_CACHE/quarantine/` and fails the job with `ErrorKind.integrity` rather than silently redownloading, because unexpected on-disk modification is an incident the operator needs to investigate.

For gated models, the operator accepts the model licence under their own account and provides `HF_TOKEN` via the environment. The harness passes this token strictly to the fetch call, never writes it to any file, log, or record, and never exposes it to adapter containers (`docs/spec/06-security.md`).

The verified model directory is mounted read-only at `/models` inside `commit` and `prove` containers, and is never mounted inside `verify` containers. Reference systems ([RFC-0015](0015-reference-rows.md)) skip `commit` and `verify`; `ref-recompute` reads the weights during `prove`, where its recomputation is timed.

Production-serving weights (amendment of 2026-11-09, RFC-0015 SRV-6): A serving record at `workloads/serving/<id>.yaml` (`serving-model/1`) pins an ungated copy of the publisher's release. It specifies the source repository and revision along with each file's path, SHA-256, byte size, storage mode (`git` or `lfs`), and the publisher's git blob id at the pinned revision. Equal git blob ids guarantee byte-for-byte identity: for regular git objects the blob id hashes the file bytes directly, while for LFS files it hashes the LFS pointer containing the SHA-256 and byte length. The model digest follows RFC-0012 over the pinned file list.

- SM-1 (offline, CI, CPU): For every `storage: lfs` entry, the git blob id of the pointer constructed from `sha256` and `bytes` must match `publisher_blob`. Any discrepancy fails G1.
- SM-2 (`iproofs fetch-model --serving RECORD`): Runs the fetch-and-verify workflow above for the serving record into `$IPROOFS_CACHE/models/<model digest hex>/`. Every downloaded file's SHA-256 and size must match the record, every `storage: git` file's git blob id (`sha1("blob <n>\0" + bytes)`) must match `publisher_blob`, and the recomputed model digest must match. Any mismatch raises `config` and prevents jobs from starting. Entries marked `source: publisher` are downloaded from the publisher's repository using `HF_TOKEN` scoped to that single command. Passing `--no-weights DIR` downloads and verifies every file except `.safetensors` weights into `DIR`, letting operators verify tokenizer loading before downloading full weights (RFC-0015 Q7).
- SM-3 (`iproofs serving check-mirror RECORD`, network command run when adding a record and before each campaign): Queries both repository tree listings at their pinned revisions, verifies that the mirror's blob id, the publisher's blob id, and `publisher_blob` agree for every pinned file, and prints the verification summary for the campaign log. `iproofs serving pin RECORD` populates the file list from those two listings and rejects any file whose blob ids differ.

In `reference_role: serve` jobs, the verified serving model is mounted read-only at `/models` inside the `prove` container in place of the workload's own files.

### Corpus fetch

`workloads/prompts/corpus.yaml` specifies every corpus file with its `id`, `source_url`, `licence`, and `sha256` (RFC-0003). The harness downloads each file into `$IPROOFS_CACHE/corpus/<digest hex>`, verifies its SHA-256, and computes the overall corpus digest, raising `ErrorKind.integrity` on any mismatch. Prompt materialisation (RFC-0003) reads exclusively from verified corpus files.

### The commitment record

Under AGENTS.md rule 6, the commitment checked by the verifier always comes from the harness record rather than from files emitted alongside a proof:

1. When `commit` exits 0, the harness validates `out.json` and copies every file listed in `verifier_files[]` and `prover_files[]` out of the commit container's `/io` into a harness-controlled directory `<job tmp>/commitment/`, which no subsequent container ever mounts read-write.
2. It writes `commitment` into `manifest.json`, recording `commitment_id` (as returned by the adapter) along with `{name, digest, bytes}` for every verifier and prover file.
3. For `prove`, the harness mounts `commitment/prover/` read-only and passes `commitment_id` and the prover file names through `job.json`.
4. For every `verify` call, the harness constructs a clean `/io` directory containing only `job.json`, a read-only copy of `commitment/verifier/` (whose file digests are reverified against the manifest right before launch), the request, the claimed output, and the proof part files. The `commitment_id` inside `job.json` comes strictly from the manifest, never from `prove` output.
5. If `prove`'s `out.json` contains a `commitment_id` key or emits a file matching the digest of a recorded verifier file, the harness logs a `policy` warning in the run log and adds it to `run.json` `warnings[]`. It does not fail the job, since some systems legitimately echo the identifier, and the verifier still receives only the harness-recorded commitment.
6. Control C3 (RFC-0008) injects an alternate recorded commitment through this same mechanism, which is the only way a non-matching commitment ever reaches a verifier.

### manifest.json

Defined by `schema/manifest/1.schema.json`, the manifest captures everything required to rerun a job while omitting host-identifying details outside RFC-0006's machine record:

```json
{
  "schema": "manifest/1",
  "run_id": "2026-12-02-sash-sash-l31-8b-c4096-prover-h100-1",
  "release": "v0.1",
  "control": false,
  "harness": {"version": "0.1.0", "git_commit": "<40 hex>", "git_dirty": false, "lock_digest": "sha256:...", "nonconforming": false},
  "runner": {"handle": "<declared handle>", "organisation": "<organisation>", "affiliated_systems": []},
  "claim": {"system": "sash", "configuration": "default", "card_version": 1},
  "provider": "<declared provider name>",
  "system": {
    "name": "sash",
    "system_manifest_digest": "sha256:...", "claim_digest": "sha256:...",
    "upstream": {"repo": "sg-ai-safety-hub/zk-inference-prover", "commit": "eb95bfa887299d1637550228d42086c27cbb2b3b"},
    "adapter_commit": "<40 hex>", "adapter_dirty": false,
    "image": {"ref": "<registry>/<repo>@sha256:...", "digest_kind": "manifest"},
    "image_inputs": [{"name": "upstream-source", "url": "...", "digest": "sha256:..."}]
  },
  "workload": {
    "id": "sash-l31-8b-c4096", "version": 1, "file_digest": "sha256:...",
    "model": {"source": "...", "revision": "<40 hex>", "digest": "sha256:..."},
    "corpus_digest": "sha256:...", "prompt_seed": "0x1f2e3d4c5b6a7988", "prompt_set_digest": "sha256:..."
  },
  "profile": {"prover": "prover-h100", "verifier": "verifier-cpu", "verifier_host": "same_as_prover",
              "reference_file": "reference/v0.1.yaml", "reference_digest": "sha256:..."},
  "machine": {"...": "RFC-0006 machine record"},
  "self_test": {"passed": true, "checks": [{"name": "ST-SAMPLER", "passed": true}, {"name": "ST-CGROUP", "passed": true}, {"name": "ST-WATCH", "passed": true}, {"name": "ST-NVML", "passed": true}]},
  "commands": [
    {"step": "commit", "argv": ["docker", "run", "..."], "cpuset": "0-23", "mems": "0", "gpus": "device=0",
     "network": "none", "started_at": "2026-12-02T09:14:03Z", "exit_code": 0}
  ],
  "commitment": {"commitment_id": "...", "verifier_files": [{"name": "...", "digest": "sha256:...", "bytes": 0}],
                 "prover_files": [{"name": "...", "digest": "sha256:...", "bytes": 0}]},
  "proofs": [{"proof_id": "...", "digest": "sha256:...", "parts": [{"name": "...", "digest": "sha256:...", "bytes": 0}],
              "archive": null}],
  "warnings": []
}
```

`runner.affiliated_systems` declares any systems whose authors the runner is affiliated with. `self_test` carries the host's calibration self-test result, run before the host's first run of a release and before each run campaign (RFC-0011) rather than before every individual job: `iproofs machine-record --selftest` saves the latest result in `results/.selftest.json`, and the runner copies it into each manifest if it was produced by the matching harness version (otherwise `self_test` defaults to `{passed: false, checks: []}`, making the run ineligible). Check names use the RFC-0011 identifiers (`ST-CLOCK` through `ST-OOM`). Failing a self-test or profile check sets `harness.nonconforming: true` without blocking execution (so `--allow-nonconforming` is accepted as a no-op), though a failed self-test makes the run ineligible for any release. `claim` identifies the active claim card by `card_version`. On reference systems, `commitment` is `null` and `proofs` lists their outputs as defined in RFC-0015. All `bytes` values inside the manifest are plain structural integers, while byte sizes used as benchmark metrics are labelled quantities in `run.json`. `prompt_seed` is serialised as a 64-bit hex string (`0x` followed by 16 lowercase hex digits) so JSON parsers lacking 64-bit integer precision cannot corrupt it. `argv` is saved after redaction (secrets never appear in `argv`, as tokens are passed only inside the harness's own fetch call).

### Proof digests

- As soon as the release watcher detects a renamed proof directory, the harness computes its proof digest (RFC-0012) and writes it to both `manifest.proofs[]` and `digests.txt` (formatted as `<proof_id>\t<digest>`, sorted by proof id bytes).
- Immediately before every `verify` call and every negative control mutation, the harness recomputes the proof digest so any unexpected on-disk alteration between proving and verifying triggers `ErrorKind.integrity`.
- Proof bytes are never committed to git (RFC-0009 §Storage). Proofs are tracked by digest and MAY be removed from the runner's disk once controls finish. The optional `manifest.proofs[].archive` field (`{uri, digest, bytes}` or `null`) remains supported in `manifest/1`, though no external proof archive is required (RFC-0009 Q1).

### Eligibility

A run is eligible for inclusion in a release (RFC-0009 freeze) only when all six conditions hold: it belongs to that release, every pin in its manifest is complete (valid `manifest/1`), `self_test.passed` is true, its `claim` matches the claim card listed by the release (for prover runs), `harness.git_dirty` is false, and `system.adapter_dirty` is false. Violations produce the reason codes `other_release`, `manifest_invalid`, `self_test_failed`, `claim_card_not_listed`, `harness_dirty`, and `adapter_dirty`. Ineligible runs remain in `results/` under the append-only rule and, if displayed at all, are explicitly marked ineligible with their reason codes. The Level 1 board applies the exact same check to every session, control run, and replacement before any release record exists (RFC-0018 SE-3b, amended 2026-11-15), using the shared helper `iproofs.release.ineligible`. Upstream measurements taken on dirty or unverified trees enter only as `external` quantities.

### Supply-chain threats and responses

| Threat | Response |
|---|---|
| Upstream force-push or repository deletion removes the pinned commit | The upstream source archive SHA-256 digest is recorded at image build time |
| Base image tag is moved | All `FROM` instructions pin images by digest (B1) |
| Package registry serves altered bytes | Hash-verified lockfiles cause the build to fail on any mismatch |
| Harness dependency is compromised | `uv.lock` pins hashes enforced via `uv sync --frozen`; dependency bumps arrive in dedicated pull requests with reviewed lock diffs |
| Malicious or buggy adapter change | Code review plus container hardening (`docs/spec/06-security.md`); negative controls catch verifiers that accept altered inputs (RFC-0008) |
| Model host silently replaces a file under an existing revision | Per-file SHA-256 digests are verified on download and rehashed before every job |
| Compromised CI action | Actions are pinned by full commit hash with `contents: read` permissions (RFC-0013) |
| Container registry loses an image | Manifests record exact digests and registry retention rules keep release images indefinitely |
| Prover smuggles a forged commitment into `verify` | Harness-owned commitment store (§The commitment record) |

### Failure modes

| Failure | Response |
|---|---|
| Pinned upstream commit cannot be fetched during build | Build fails in the `fetch` stage; an adapter issue is opened and no row is produced |
| Model digest mismatch | `integrity` failure; job stops before launching any container and quarantines the cache entry |
| Verifier commitment file digest changes before `verify` | `integrity` failure; the `verify` call is skipped and the step fails |
| Adapter image digest cannot be pulled | `fetch` failure after retries; job fails at `image_ready` |
| `info` reports an `upstream_commit` differing from `system.yaml` | `integrity` failure; job stops at `info` |
| Dirty harness git tree | Job still runs and records `git_dirty: true`, making it ineligible for releases |

## Alternatives Considered

**Rebuild adapter images for every rerun instead of pulling pinned digests.** Rebuilding would test the build pipeline alongside the run, but GPU toolchains rarely produce bit-identical binaries due to timestamps and compiler nondeterminism, meaning benign rebuild drift would block reruns for reasons unrelated to benchmark measurements.

**Trust the local model cache after the initial download check.** Rehashing roughly 200 GB of weights before every job takes several minutes, yet that overhead sits completely outside timed scopes, is small compared to proving times, and prevents silent disk corruption from invalidating every subsequent run.

**Let each adapter pass its own commit output directly to `verify`.** While simpler for adapter authors, this would make AGENTS.md rule 6 depend on every individual adapter getting it right. Managing commitments in a harness-owned store enforces the rule structurally.

**Require cryptographically signed result files from v0.1.** Signatures can simplify result attribution (PRD §12), but a signature only proves who generated a file, not that the measurements are honest, and key management for volunteer runners requires its own design. Deferred per Q1.

## Drawbacks

- Publishing release images requires operating and funding a container registry before permanent governance is finalised.
- Rehashing large weight directories adds minutes of untimed wall time before each job.
- Separating a `fetch` stage from offline build stages (B2, B3) makes adapter Dockerfiles more verbose than a plain `git clone && make`.
- Without signed records or host attestation, a runner intentionally fabricating results is not cryptographically caught (see residual risks in `docs/spec/06-security.md`).

## Migration / Rollout

Rollout proceeds in stages: first land the manifest schema and commitment store alongside the fake systems (immediately exercised by G10), then add model fetch and verification, enforce build rules B1 through B7 across the SASH and FlashProve adapters, and publish images to the registry. Eligibility checks take effect with the first release freeze.

Amendment of 2026-11-09 (RFC-0015 SRV-6 production serving): Adds rules SM-1 through SM-3 and the serving-model mount under §Model fetch and verification, plus the generic development-install specification. Unit tests in `harness/tests/unit/test_serving.py` verify SM-1 and SM-2 against fixtures.

## Testing Strategy

- `harness/tests/unit/test_fetch.py::test_extra_file_rejected`, `::test_missing_file_rejected`, `::test_digest_mismatch_quarantines`, `::test_cache_rehash_detects_change` (flips one byte in a cached fixture model and expects `integrity` plus quarantine), and `::test_token_never_logged` (sets `HF_TOKEN`, fetches from a local fake hub, and verifies the token never appears in any written file).
- `test_commitment.py::test_verify_io_contains_only_recorded_commitment` (runs a fake adapter whose `prove` writes a forged `commitment_id` and forged key file, asserting that `verify` receives only the harness-recorded commitment and logs a warning) and `::test_verifier_file_changed_before_verify_fails`.
- `test_manifest.py::test_manifest_round_trip_valid` against `manifest/1`, `::test_failed_self_test_ineligible`, `::test_reference_run_has_null_commitment`, `::test_prompt_seed_is_hex_string`, and `::test_dirty_harness_marks_ineligible`.
- `test_proof_digest.py::test_changed_part_detected_before_control`.
- Per-system CPU-only Dockerfile checks (`systems/<name>/tests/test_dockerfile_rules.py`) that parse the Dockerfile and verify B1, B3 (every `RUN` outside `fetch` sets `--network=none`), and full `inputs.lock` coverage for every `ADD` in `fetch`.
- G10 end-to-end validation confirming that every fake run produces a valid manifest whose recorded commitment digests match the files given to `verify`.

## Decisions

- Q1. Runners do not cryptographically sign `run.json` or `manifest.json`, and no host hardware attestation is recorded.
- Q2. Release images are published to `ghcr.io/ai-verification-observatory/`, under the same organisation that hosts the repository. Retention is indefinite: digests referenced by any release are never deleted or overwritten, and pulls never resolve by tag. Base engine images used by reference adapters (RFC-0015) are pinned by digest directly from their upstream registry (B1) like any other `FROM` image and are not mirrored again.

## References

- AGENTS.md hard rules 1, 6, 7, and 8, plus working practice ("Pin everything").
- [RFC-0003](0003-workloads.md), [RFC-0005](0005-adapter-contract.md), [RFC-0006](0006-reference-hardware-and-cost.md), [RFC-0007](0007-evidence-tiers-and-reproduction.md), [RFC-0008](0008-negative-controls.md), [RFC-0009](0009-results-and-publication.md), [RFC-0012](0012-schemas-and-serialization.md), [RFC-0013](0013-validation-and-ci.md).
- OCI Image Specification (image manifests and digests).
- Docker BuildKit `ADD --checksum` and `RUN --network`.
- SLSA build provenance levels (background for the build inputs record).
