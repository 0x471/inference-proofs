# RFC-0005: Adapter contract

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0003, RFC-0004, RFC-0012

## Summary

Each proving system joins the benchmark through an adapter: a single OCI image built from this repository that wraps the upstream prover unmodified at a pinned 40-character commit hash and exposes five subcommands (`info`, `setup`, `commit`, `prove`, `verify`) communicating via JSON files inside a mounted `/io` directory. This RFC defines contract version `adapter/1`, covering the adapter directory layout, the `system.yaml` manifest, the exact container invocation, the typed schemas of all job and result files, the proof-release protocol used for external timing, path safety rules, verdict normalisation, and expected failure handling. Because every benchmark measurement crosses this boundary, a tight contract prevents adapters from altering what gets measured.

## Motivation

Proving systems vary widely in implementation language, build tooling, CLI design, and output formats. Some projects do not accept upstream changes: FlashProve explicitly states that it is "a research artifact: not maintained, not accepting contributions" (upstream README at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`). The harness must therefore integrate every system as published, without asking authors to modify their code (PRD G6, [AGENTS.md hard rule 1](../AGENTS.md#hard-rules)).

The first two v0.1 systems also differ in their toolchains (FlashProve documents CUDA 13.2 Update 2 and gcc 13, whereas SASH documents a pinned Rust toolchain and CUDA 12.9), in proof granularity (FlashProve emits one proof per request, while SASH emits a grid of segment proofs per sequence; see [RFC-0004](0004-metrics-timing-grades.md)), and in how verification reports results (exit codes for FlashProve; per-segment results plus a `boundary-grid` check for SASH). Because the harness takes all measurements from outside the container ([RFC-0011](0011-measurement-and-sampling.md)), the contract also needs a precise definition of *when* a proof counts as produced so `prove.steady` can be timed externally.

Scenarios this contract must support:

1. A CI job executes the full pipeline against `systems/fake` on a laptop CPU with no GPU and no network access.
2. A runner on an H100 host runs `sash-l31-8b-c4096` three times while the harness timestamps each segment proof as it is released.
3. A negative-control job ([RFC-0008](0008-negative-controls.md)) hands mutated proofs to `verify`, and the adapter cannot distinguish a mutated proof from an honest one except by running the upstream verifier.
4. A SASH negative-control job invokes an `--unsound-skip-*` flag, whereas outside a control job the adapter refuses the flag.

## Goals

- Provide a single contract, `adapter/1`, that both v0.1 provers, the two reference systems ([RFC-0015](0015-reference-rows.md)), and the test fake systems implement without patching upstream source.
- Specify JSON Schemas for every job and output file in `schema/adapter-job/1.schema.json` and `schema/adapter-out/1.schema.json`, rejecting any `out.json` that fails validation.
- Make proof release atomic and externally observable so the harness can time each proof without relying on adapter-reported clocks.
- Prevent an adapter from reading the verification commitment out of its own prover outputs.
- Prevent an adapter from running a claim-weakening configuration outside a control job.
- Ensure every adapter can be tested on CPU against stored fixtures.

## Non-Goals

- Defining a Python or Rust in-process plugin API; adapters are always containers.
- Multi-GPU or multi-node proving; v0.1 prover profiles use a single GPU ([RFC-0006](0006-reference-hardware-and-cost.md)).
- Specifying proof serialization formats; the harness treats proof files as opaque bytes.
- Streaming results over sockets; files in `/io` are the sole communication channel.
- Deciding which upstream flags are valid; upstream documentation at the pinned commit governs that, and this RFC simply requires adapters to stay within documented options.

## Proposed Design

### Layout

```
systems/<name>/
  Dockerfile        pins the upstream repository by full commit hash and every toolchain by version
  entrypoint        executable implementing the five subcommands
  system.yaml       manifest (schema system/1), below
  claim.yaml        claim card (RFC-0002)
  external.yaml     upstream figures, grade external (RFC-0004), optional
  controls.yaml     system-specific negative controls (RFC-0008), optional
  README.md         mapping of each subcommand onto upstream tools, with links at the pin
  tests/            CPU-only fixture tests (INV-ADAPTER-9)
```

`<name>` must match `^[a-z][a-z0-9-]{1,31}$` ([RFC-0012](0012-schemas-and-serialization.md)).

### system.yaml

Authored YAML validated against `schema/system/1.schema.json`:

```yaml
schema: "system/1"
name: "flashprove"                    # system id
kind: "prover"                        # prover | reference | test
contract: "adapter/1"
upstream:
  repo: "anthropics/FlashProve"       # owner/name on its public host
  url: "https://github.com/anthropics/FlashProve"
  commit: "9e2bdd8ff5bf9c62f18263d7dac189b0400b260c"   # 40 lowercase hex, INV-ADAPTER-2
  tag: "v0.16.0"                      # optional, informative only
image:
  repository: "ghcr.io/<org>/iproofs-flashprove"        # where the built image is pushed
  digest: "sha256:<64 hex>"           # set by the build job, INV-ADAPTER-3
maintainers:                           # optional; handles only
  - handle: "<github handle>"
    organisation: "<organisation>"
workloads: ["fp-maverick-w1024-b1", "fp-maverick-w1024-b24"]
profile: "prover-h100"                # required prover profile (RFC-0006)
deterministic_proofs: false           # true only if upstream documents byte-identical proofs for identical inputs and seed
incremental_proofs: true             # true when upstream releases proofs one by one during the prove call (RFC-0011)
max_proof_parts: 10000                # cap on part files per proof directory; may only be lowered
max_proof_bytes: 68719476736          # cap on bytes per part (64 GiB); may only be lowered
proofs:
  granularity: "request"              # request | sequence | segment_grid
  tokens_covered: "window"            # window | prompt_plus_output | declared_per_proof
  steady_boundary: "first_proof"      # first_proof | first_complete_sequence | not_observable
  steady_approximate: false           # true when the mapping to the upstream scope is approximate (RFC-0004)
  verify_reads:                       # optional; absent or "all": verify reads every part (RFC-0008)
    read: ["response.proof"]
    not_read: [{part: "response.y", reason: "<why verify never reads it>"}]
forbidden_flags: []                   # literal argument prefixes the adapter must refuse outside control jobs
timeouts_s:                           # per-step wall limits; defaults below apply when absent
  info: 60
  setup: 3600
  commit: 14400
  prove: 43200
  verify: 3600
```

Field rules:

- Reference systems (`kind: reference`) add `reference_role`, `engine`, and the object form of `workloads` (entries of `{id, precision_used, precision_substitution, engine_args}`) specified in [RFC-0015](0015-reference-rows.md#reference-systems). The `system/1` schema permits the object form only when `kind` is `reference`.
- `kind: test` is reserved for `systems/fake` and `systems/fake-broken`. CI uses them for pipeline testing, and results with `kind: test` never enter `results/<release>/`.
- `proofs.granularity` specifies what a single proof directory represents: `request` means one proof per request, `sequence` means one proof per sequence, and `segment_grid` means one proof directory per sequence containing segment proofs plus a grid-check record, released once the full grid is written (as used by SASH below).
- `proofs.tokens_covered` specifies how the harness counts tokens covered by a single proof ([RFC-0004](0004-metrics-timing-grades.md)): `window` counts the positions in the input window, `prompt_plus_output` counts prompt tokens plus generated tokens for the sequence, and `declared_per_proof` lets the adapter report `tokens_covered` per proof in `out.json`, which the harness validates against the workload shape (INV-ADAPTER-7).
- `proofs.steady_boundary` declares where `prove.steady` begins. For batch size `b > 1`, `first_proof` means the last release of the first batch (RFC-0004 INV-SCOPE-5, amendment of 2026-11-09). Setting `not_observable` causes the harness to record `prove.steady` as null with `null_reason: "not_externally_observable"`.
- `proofs.verify_reads` (optional; omitting it means `"all"`) lists which proof parts `verify` actually reads and explains why any remaining parts are unread. Controls C5, C6, and C8 mutate only the read parts ([RFC-0008 §Parts the verifier reads](0008-negative-controls.md#parts-the-verifier-reads), amendment of 2026-11-09).
- Setting `incremental_proofs: false` requires `proofs.steady_boundary: not_observable` (INV-ADAPTER-10): if the upstream prover writes all proofs only at the end of the call, file release times carry no steady-state timing information ([RFC-0011](0011-measurement-and-sampling.md#proof-release-watcher)).
- `max_proof_parts` and `max_proof_bytes` default to 10,000 parts and 64 GiB per part (safety caps rather than measurements). A system may lower these caps but never raise them; exceeding either cap triggers an `adapter` failure ([Path safety](#path-safety)).
- `forbidden_flags` is checked by prefix against every argument the adapter passes to upstream binaries. The adapter records every invoked command line in `/io/commands.jsonl` (described below) so CI can audit it separately ([RFC-0013](0013-validation-and-ci.md)).
- Default wall-clock timeouts (applied whenever `timeouts_s` omits a step) are 60 s for `info`, 3,600 s for `setup`, 14,400 s for `commit`, 43,200 s for `prove`, and 3,600 s for `verify`. These are harness execution limits rather than measurements; any system needing longer limits declares them in `system.yaml`, where reviewers can inspect them.

### Container invocation

Only the harness invokes adapter containers. For each subcommand, it runs the equivalent of the `docker run` invocation below. In practice, it calls `docker create` with these flags (untimed) followed by `docker start --attach` (timed; see [RFC-0011](0011-measurement-and-sampling.md#timing-a-container-call)). The container is also assigned `--cgroup-parent` under a harness-owned slice so cgroup resource counters remain readable after exit ([RFC-0011](0011-measurement-and-sampling.md#cgroup-accounting)).

```
docker run --rm \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 4096 \
  --cpuset-cpus <cpu list> --cpuset-mems <numa node> \
  [--gpus device=<index>]            # info, setup, commit, prove only; never verify
  [--memory 32g]                     # verify on the verifier profile
  --tmpfs /tmp:rw,size=<profile tmp>,mode=1777 \
  [-v <model_dir>:/models:ro]       # every step except verify; a verifier never sees the weights
  -v <job io dir>:/io:rw \
  --name iproofs-<run-id>-<step> \
  <image repository>@sha256:<digest> <subcommand> /io/job.json /io/out.json
```

- Containers are always invoked by immutable image digest (INV-ADAPTER-3); mutable tags are never used.
- `--network none` applies to every subcommand, including `setup`. Everything an adapter needs at runtime must already live inside the image or under `/models` (INV-ADAPTER-4).
- `verify` runs without `--gpus`, constrained to the verifier profile's cpuset (8 CPUs, or 1 CPU for `verify.single_thread`) and `--memory 32g` ([RFC-0006](0006-reference-hardware-and-cost.md)).
- Writable prover state that needs to persist across steps of the same job (such as prover keys or commitment state) is stored under `/io/state/`. The harness allocates one job I/O directory per job and mounts it for each step of that job, never sharing `/io` across different jobs.
- Containers execute as a non-root user declared in the Dockerfile (`USER`), uid 10001 by convention. The harness creates the job I/O directory owned by that uid.

### Subcommands and file shapes

Every subcommand reads `/io/job.json` (generated by the harness, schema `adapter-job/1`) and writes `/io/out.json` (schema `adapter-out/1`). Common fields in `job.json`:

```json
{
  "schema": "adapter-job/1",
  "contract": "adapter/1",
  "subcommand": "prove",
  "run_id": "2026-11-03-flashprove-fp-maverick-w1024-b24-prover-h100-1",
  "workload": {"id": "fp-maverick-w1024-b24", "version": 1},
  "shape": {"prompt_tokens": 1024, "output_tokens": 1, "batch_size": 24, "batches_per_session": 5, "context_window": 1024},
  "control": false
}
```

Common fields in `out.json`:

```json
{
  "schema": "adapter-out/1",
  "contract": "adapter/1",
  "subcommand": "prove",
  "phases": [{"name": "witness", "seconds": 12.5}],
  "warnings": []
}
```

`phases` records optional adapter-reported internal timings. The harness preserves them as quantities with `source.kind: "adapter"` ([RFC-0004](0004-metrics-timing-grades.md)), and they never replace external harness measurements.

Additional fields per subcommand:

| Subcommand | job.json | out.json |
|---|---|---|
| `info` | none | `system`, `upstream_commit`, `image_inputs[]` (`{name, url, digest}` for every input fetched at build time), `workloads[]`, `profile`, `contract_versions[]` |
| `setup` | none | `ready: true`, `log_files[]` |
| `commit` | `model_dir` (`"/models"`) | `commitment_id` (string), `verifier_files[]`, `prover_files[]` (paths under `/io/state/`), `sizes` (`{verifier_bytes, prover_bytes}`) |
| `prove` | `commitment_id`, `prover_files[]`, `model_dir`, `prompts_file` (JSONL of token id arrays under `/io/`), `batch_size`, `batches` | `proofs[]`: `{proof_id, request_index, parts[], claimed_output, tokens_covered?}`, `binding_report?` (path) |
| `verify` | `commitment_id`, `verifier_files[]`, `request` (token ids), `claimed_output` (token ids), `proof_dir` | `verdict`, `policy?`, `raw_exit_code`, `raw_last_line`, `seconds` |

Python view (informative; the JSON Schemas are normative):

```python
from typing import Literal, TypedDict

Verdict = Literal["accept", "reject", "no_verdict", "invalid_call"]

class ProofEntry(TypedDict, total=False):
    proof_id: str              # ^[a-z0-9][a-z0-9._-]{0,127}$ (RFC-0012 identifiers)
    request_index: int         # index into prompts_file, 0-based
    parts: list[str]           # file names inside /io/proofs/<proof_id>/, order significant
    claimed_output: list[int]  # token ids
    tokens_covered: int        # required iff proofs.tokens_covered == "declared_per_proof"

class VerifyOut(TypedDict):
    verdict: Verdict
    raw_exit_code: int
    raw_last_line: str         # last non-empty line of upstream verifier output, redacted, <= 4096 bytes
    seconds: float             # adapter-reported, stored as source.kind "adapter"
```

When invoking `verify`, the harness supplies `commitment_id` and `verifier_files` strictly from its own saved record of the `commit` step, never from files produced by `prove` (INV-ADAPTER-5, [AGENTS.md hard rule 6](../AGENTS.md#hard-rules)). The harness copies `verifier_files` from the `commit` I/O directory into a clean `verify` I/O directory so the verifier container never has access to `/io/state/`.

Exit codes: every subcommand exits `0` whenever it finishes normally, regardless of the verification outcome, and non-zero if it fails to execute. A rejected proof therefore exits `0` with `verdict: "reject"`.

### Proof release protocol

The harness determines proof completion times by observing the filesystem rather than trusting adapter timestamps.

1. For each proof, the adapter writes all proof files into `/io/proofs/.tmp-<proof_id>/`.
2. Once every part is written, the adapter calls `rename("/io/proofs/.tmp-<proof_id>", "/io/proofs/<proof_id>")`, which is atomic on a single filesystem.
3. The harness monitors `/io/proofs/` via inotify (`IN_MOVED_TO`), falling back to 10 ms polling if inotify is unavailable, and records `release_time = time.monotonic_ns()` when each directory appears ([RFC-0011](0011-measurement-and-sampling.md)).
4. After `prove` exits, the harness parses `out.json`, verifies that the set of `proof_id` entries matches the set of released directories one-to-one (INV-ADAPTER-6), and computes digests of every proof part ([RFC-0012](0012-schemas-and-serialization.md)).

If an upstream prover only writes its proofs at process exit, the adapter still releases each directory atomically, and `system.yaml` sets `steady_boundary: not_observable` unless release times carry real separation; the harness then records `prove.steady` as null (see RISK below).

### Command log

For every upstream subprocess it spawns, the adapter appends a JSON line to `/io/commands.jsonl` with the fields `{"argv": [...], "cwd": "...", "started_mono_ns": int, "exit_code": int}`. Environment variables are omitted. The harness copies this file into `logs/commands.jsonl` inside the run directory and records its digest in `manifest.json` ([RFC-0014](0014-provenance-and-integrity.md#manifestjson)) so CI can enforce the policy gate ([RFC-0013](0013-validation-and-ci.md)).

### Path safety

All paths in `job.json` and `out.json` must be either absolute paths inside `/io` or `/models`, or filenames relative to a known directory (such as entries in `parts[]`). On the host side, the harness resolves every path after symlink expansion, rejecting any path that escapes the job I/O directory, any symlinks or device files inside `/io/proofs/`, any part larger than 64 GiB, and any proof directory containing more than 10,000 parts. Any violation fails the step with kind `adapter` and logs the offending path (INV-ADAPTER-8).

### Verdict normalisation

`verdict` must be one of `accept`, `reject`, `no_verdict`, or `invalid_call`. Each adapter maps the upstream verifier's exit codes and output onto these four values and documents that mapping in its README with links to the pinned upstream commit.

- **FlashProve:** exit 0 with `YES` or `WITHIN LIMITS` maps to `accept`, with `policy` set to `"exact-match"` or `"clipped-gap"` respectively; exit 1 maps to `reject`; exit 5 maps to `no_verdict`; exits 2, 3, 4, 14, and 15 map to `invalid_call`. Any other exit code causes the adapter to exit non-zero (an `adapter` failure) rather than guessing a verdict.
- **SASH:** one proof covers the complete set of segment proofs for a sequence together with the `boundary-grid` check. If every segment proof is accepted and the grid check succeeds, the verdict is `accept`; if any segment is rejected or the grid check fails, the verdict is `reject`. Any other upstream outcome maps to `no_verdict` with the raw output line preserved. The adapter README documents the exact segment-verifier and grid-check commands from upstream documentation at the pin.

### Weakening configurations

Unless `job.json` has `control: true`, the adapter MUST exit non-zero before spawning any upstream process if any argument matches a prefix in `forbidden_flags`. For SASH, `forbidden_flags` includes `--unsound-skip-` (prefix match). Inside a control job, the harness passes the flag explicitly via `control_flags[]`, and the adapter adds no extra flags. Control runs never become measured rows ([RFC-0008](0008-negative-controls.md), [RFC-0002](0002-claim-card.md)).

### Adapter README requirements

Every `systems/<name>/README.md` MUST document the following items, linking each to upstream documentation at the pinned commit:

1. The upstream tools invoked by each subcommand and all arguments passed to them.
2. The complete verdict mapping table.
3. How `commitment_id`, `verifier_files`, and `prover_files` correspond to upstream files and identifiers.
4. The values chosen under `proofs` in `system.yaml` and the reasoning behind them.
5. The pinned toolchain versions and why they match upstream (for example, CUDA 13.2 Update 2 and gcc 13 for FlashProve; a pinned Rust toolchain and CUDA 12.9 for SASH).
6. Upstream CPU-binding guidance and how the harness binding satisfies it (for instance, FlashProve pins its threads only to CPUs in its allowed mask).
7. Any known differences from upstream's own benchmarking setup (such as FlashProve committing fresh per run with `-M 1` because each run consumes batches from a leaf table).

### Reference implementations

- `systems/fake` (`kind: test`): a pure-Python, CPU-only adapter requiring no GPU. `commit` produces `commitment_id = sha256(model digest)`; `prove` creates one proof per request containing two parts (`body.bin` and `tag.bin`) where `tag = HMAC-SHA256(key=commitment_id, msg=request || claimed_output || body)` and `claimed_output` is deterministically derived from the request; `verify` recomputes the tag and returns `accept` or `reject`, or `invalid_call` if a part is missing or shorter than 32 bytes. It releases proofs sequentially with a configurable delay so `prove.steady` is externally observable. Because every shared mutation alters an HMAC input, it passes the shared control suite by construction and serves as the positive end-to-end test target.
- `systems/fake-broken` (`kind: test`): identical to `systems/fake`, except `verify` unconditionally returns `accept`. CI verifies that the control suite flags accepted controls against it ([RFC-0013](0013-validation-and-ci.md)).

### Invariants

- **INV-ADAPTER-1:** Adapters never patch upstream source code and never pass flags undocumented at the pinned commit.
- **INV-ADAPTER-2:** `upstream.commit` is a 40-character lowercase hexadecimal hash; the Dockerfile checks out that exact commit and verifies it with `git rev-parse HEAD`.
- **INV-ADAPTER-3:** Images are always invoked by digest, and that digest is recorded in every run manifest.
- **INV-ADAPTER-4:** No subcommand has network access.
- **INV-ADAPTER-5:** The commitment passed to `verify` always originates from the harness's record of `commit`.
- **INV-ADAPTER-6:** The proofs listed in `out.json` match the released proof directories one-to-one.
- **INV-ADAPTER-7:** Tokens covered per proof match what the workload shape and `proofs.tokens_covered` specify; when declared per proof, the harness validates the adapter's count against the shape and fails the job with kind `adapter` on any mismatch.
- **INV-ADAPTER-8:** No path returned by an adapter can escape the job I/O directory.
- **INV-ADAPTER-9:** Every adapter includes CPU-only unit tests in `systems/<name>/tests/` that exercise its entrypoint against stored upstream output fixtures (captured once on a GPU host), covering verdict mapping for every documented exit code.
- **INV-ADAPTER-10:** `incremental_proofs: false` requires `proofs.steady_boundary: not_observable`, enforced in `system/1` via an `if`/`then` schema rule.
- **INV-ADAPTER-10:** Passing a forbidden flag outside a control job causes the adapter to exit non-zero before starting any upstream process.

### Failure modes

| Failure | Detection | Harness response |
|---|---|---|
| Subcommand exits non-zero | Exit status | Step marked `failed` with kind `adapter`, recording exit code and the last 50 lines of stderr; job recorded as failed |
| `out.json` missing, malformed JSON, or fails `adapter-out/1` | Parse and schema check | `adapter` failure; `out.json` archived in `logs/` if present |
| `out.json` `contract` or `subcommand` mismatch | Field check | `adapter` failure |
| Proof listed in `out.json` but unreleased, or released but unlisted | INV-ADAPTER-6 check | `adapter` failure; any released proofs are still hashed and recorded by digest |
| Leftover `.tmp-*` directory after exit | Directory scan | Warning logged; directory is ignored and excluded from counts |
| Path escape, symlink, device file, or oversized part | INV-ADAPTER-8 check | `adapter` failure with offending path recorded |
| Step exceeds its timeout | Harness timer | `docker kill` followed by a `timeout` failure; no retry |
| Container killed by OOM killer | `docker inspect` `OOMKilled` | `resource` failure |
| Verdict outside the four allowed values | Schema validation | `adapter` failure for that `verify` call; control or row records `error` |
| Forbidden flag used outside a control job | Adapter pre-flight exit and CI check on `commands.jsonl` | `policy` failure; run is disqualified from becoming a measured row |
| `tokens_covered` disagrees with workload shape | INV-ADAPTER-7 | `adapter` failure |
| Running image digest disagrees with `system.yaml` | `docker image inspect` before run | `integrity` failure before any step executes |

## Alternatives Considered

1. **In-process Python plugin API (`class Adapter: def prove(...)`).** Lowest friction for Python projects and eliminates container startup time, but rejected because it forces all systems into one language and process, creates toolchain conflicts (the two v0.1 provers require different CUDA versions), and places adapter code inside the harness's trust boundary where it could interfere with timing.
2. **Long-running gRPC or HTTP service per system.** Would support per-request latency measurement and streaming, but rejected for v0.1 because it requires container networking (violating INV-ADAPTER-4), adds another RPC protocol for every adapter to implement, and file-based JSON combined with atomic renames already supports per-proof external timing.
3. **Using adapter-reported timings as primary measurements.** Adapters know their internal phase boundaries, but relying on them would mean primary benchmark numbers depend on code written by the measured party. Adapter timings are retained under `source.kind: "adapter"` and never replace external harness measurements.
4. **Invoking upstream binaries directly without an adapter layer.** Removes a wrapper layer, but rejected because upstream CLIs vary widely in flags, outputs, and verdict conventions, which would push system-specific branching into the harness and break uniform verdict handling.
5. **Allowing adapters to generate mutated proofs for negative controls.** Rejected in [RFC-0008](0008-negative-controls.md) because the measured party would be generating its own tests.

## Drawbacks

- Container startup adds wall-clock overhead to every step. That overhead is logged via the `info` call time ([RFC-0011](0011-measurement-and-sampling.md)) and never subtracted; it is negligible for multi-minute steps, though it dominates short calls such as `verify` on `systems/fake`.
- Enforcing `--network none` during `setup` prevents runtime downloads, so large upstream dependencies must be baked into the OCI image or supplied as pinned model files, increasing image sizes.
- The atomic release protocol requires staging proofs in a temporary directory even when an upstream prover writes elsewhere, which can entail copying tens of gigabytes on SASH-scale runs (RISK: proof storage volume is roughly 19.8 GB for SASH's 4,096-position run, grade external, tier reported, source `sg-ai-safety-hub/zk-inference-results` at `11decec3c0b62c707618aab5deb82750b355d202`). Adapters SHOULD point upstream output directly into `/io` and use `rename` rather than copying whenever possible.
- Limiting each container to one GPU does not cover multi-GPU provers, which will be addressed in a future contract major version.

## Migration / Rollout

- This RFC supersedes the adapter contract from the initial design commit; no adapters or results existed at that time, so no migration was needed.
- `adapter/1` ships first with `systems/fake` and `systems/fake-broken`, followed by the SASH and FlashProve adapters.
- Any breaking change to `job.json`, `out.json`, container invocation, or the release protocol requires a new RFC introducing `adapter/2`. The harness supports both the current and previous contract major versions for one benchmark release ([09-release-and-versioning](../docs/spec/09-release-and-versioning.md)).
- Additive optional fields in `adapter-out/1` (such as new `phases` entries) do not increment the contract version.

RISK: SASH proves a grid of segments, so whether one proof directory per sequence (`segment_grid`) is the right unit and where `prove.steady` should start depends on how upstream releases segment proofs. Resolution: the SASH adapter implementation verifies upstream behaviour at the pinned commit and sets `steady_boundary`; if segment release times cannot be observed externally, `not_observable` applies.

Amendment of 2026-11-09 (RFC-0015 SRV-6 production serving): for serving jobs, `job.json` adds `load_point` (`matched` or `high`) and `gpus` (bound GPU count), while `batch_size` and `batches` reflect the actual run settings (`batch_size_run`, `batches_per_session_run`). For `b > 1`, `steady_boundary: first_proof` means the last release of the first batch (RFC-0004 INV-SCOPE-5). Docker serving container settings will be specified alongside docker serving profiles (RFC-0006 R6). When a reference adapter exits non-zero, it may write `/io/failure.json` (`{kind, message, evidence}`) to report why: `config` for pre-launch refusals (such as an unset engine environment variable or a mismatch between GPU count and tensor-parallel size; RFC-0015 SRV-3) or `resource` when the KV cache cannot fit the matched load or the engine exits at startup out of GPU memory, attaching the engine's error line as evidence (SRV-6). The runner records that failure kind and appends the evidence after the stderr tail in `last_lines`; any other kind, a missing or unreadable file, or a failure file written by a prover system falls back to `adapter`.

## Testing Strategy

Contract tests (CPU, CI):

- `test_job_schema_examples`: every file in `schema/adapter-job/examples/valid/` passes validation and every file in `invalid/` fails, including a job missing `contract`, a `prove` job missing `commitment_id`, and a job containing an absolute path outside `/io`.
- `test_out_schema_examples`: equivalent checks for `adapter-out/1`, including `verdict: "maybe"` (invalid) and a proof entry with an empty `parts` list (invalid).
- `test_docker_argv_flags`: confirms the invocation builder emits the exact flags specified above for each subcommand, that `verify` omits `--gpus` and includes `--memory 32g`, and that every invocation includes `--network none` and an `@sha256:` image reference.
- `test_release_watch_orders_proofs`: a writer thread renames five `.tmp-*` directories spaced 50 ms apart; the watcher captures all five release times in order within 20 ms of each rename (inotify) or 30 ms (polling fallback).
- `test_unlisted_proof_is_adapter_failure` and `test_listed_but_unreleased_is_adapter_failure`: verify INV-ADAPTER-6.
- `test_path_escape_rejected`: `out.json` containing `../../etc/passwd`, an absolute path outside `/io`, or a symlinked part each trigger an `adapter` failure naming the offending path.
- `test_forbidden_flag_refused`: the fake adapter configured with `forbidden_flags: ["--unsound-skip-"]` exits non-zero when `control: false`, and succeeds when `control: true`.
- `test_commitment_from_harness_record`: even if a fake `prove` step writes a forged `commitment_id` into its proof directory, `verify` receives the original value recorded at `commit`.
- `test_fake_end_to_end`: `iproofs run --system fake` produces a schema-valid run directory with a non-null `prove.steady`.
- `test_fake_broken_flagged`: the control suite records applicable controls C1 to C8 as `accepted` against `fake-broken`.

Per-adapter tests (INV-ADAPTER-9, CPU, CI):

- `systems/flashprove/tests/test_verdict_map.py`: confirms exit codes 0 (both `YES` and `WITHIN LIMITS`), 1, 2, 3, 4, 5, 14, and 15 map as documented, while undocumented exit code 7 causes the adapter to exit non-zero.
- `systems/sash/tests/test_verdict_map.py`: confirms all segments accepted plus passing grid check maps to `accept`, any rejected segment maps to `reject`, and a failed grid check maps to `reject`.
- `systems/*/tests/test_out_json_fixture.py`: runs each adapter's entrypoint logic over stored upstream output fixtures and validates the resulting `out.json`.

GPU tests (manual runbook on a GPU host, outside CI): execute one `prove` and `verify` pass on each v0.1 workload at its smallest shape and confirm `out.json` matches the structure of the CPU fixtures.

## Decisions

- Q1. Although SASH writes each segment's files as soon as that segment finishes, it verifies segments only after the loop completes, and `boundary-grid` checks the entire grid for a sequence. Because each job proves a single sequence, the benchmark observes one proof release per job: `granularity: segment_grid`, `incremental_proofs: false`, `steady_boundary: not_observable`, leaving `prove.steady` null on SASH rows. Sources: [`systems/sash/README.md`](../systems/sash/README.md#grid-geometry-and-proof-release).
- Q3. Adapter-reported timing phases use free-form names matching `^[a-z][a-z0-9_]{0,31}$`, documented in each adapter's README, with no global vocabulary.
- Q4. FlashProve's `verify` subcommand invokes the C++ verifier, and the claim card configuration names it accordingly; using the Lean verifier would require a separate configuration with its own claim card. The PRD cites roughly 21 s per proof on one CPU thread for the C++ verifier versus roughly 24 minutes for the Lean verifier (grade external, tier reported, source FlashProve at 9e2bdd8f), while the claim card notes that formal soundness is stated for the Lean verifier.

## References

- [RFC-0002 Claim card](0002-claim-card.md), [RFC-0003 Workloads](0003-workloads.md), [RFC-0004 Metrics](0004-metrics-timing-grades.md), [RFC-0006 Reference hardware](0006-reference-hardware-and-cost.md), [RFC-0008 Negative controls](0008-negative-controls.md), [RFC-0010 Harness runner](0010-harness-runner.md), [RFC-0011 Measurement](0011-measurement-and-sampling.md), [RFC-0012 Schemas](0012-schemas-and-serialization.md), [RFC-0013 CI gates](0013-validation-and-ci.md), [RFC-0015 Reference rows](0015-reference-rows.md).
- [docs/spec/02-public-api.md](../docs/spec/02-public-api.md#adapter-contract).
- FlashProve at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`; SASH zk-inference-prover at `eb95bfa887299d1637550228d42086c27cbb2b3b`.
- OCI Image Specification v1.1; Linux `rename(2)` and `inotify(7)`.
