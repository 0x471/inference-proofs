# RFC-0008: Negative controls

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0005, RFC-0010, RFC-0012

## Summary

After an honest run, every system's verifier is subjected to a shared suite of tampering tests alongside any system-specific controls registered from upstream. The harness generates all tampered inputs itself rather than delegating mutation to the adapter. Each control runs alongside an unmodified honest twin that must be accepted; if the twin fails verification, the control is recorded as `void` so a broken harness or broken run cannot look like a rejecting verifier. Every published row tracks counts of controls run, rejected, accepted, `no_verdict`, `invalid_call`, void, not applicable, and errored. When a verifier unexpectedly accepts a tampered control, the finding goes through private disclosure to the system maintainers before publication.

## Motivation

Proving speed tells only half the story: a proof system is only meaningful when its verifier rejects invalid inputs ([PRD G4](../docs/PRD.md#4-goals)). Both initial systems include rejection tests of their own, such as FlashProve's `examples/rejected-proofs` and SASH's `--unsound-skip-*` switches that disable individual edge bindings to demonstrate what each check enforces (PRD, Section 1). Running a shared tampering suite applies identical checks across every system and guards against a buggy or dishonest adapter, since an adapter that blindly maps every verification to `accept` will fail every shared control ([06-security](../docs/spec/06-security.md)).

## Goals

- Define a fixed shared control suite (verifier-side C1 to C8 and prover-side P1 and P2) with exact, seeded, deterministic mutation algorithms.
- Apply all mutations in the harness over opaque proof bytes and request fields, requiring nothing from adapters beyond `adapter/1`.
- Pair every control with an honest twin and record any failed-twin control as `void`.
- Use a closed outcome vocabulary and per-control expected sets so pass/fail classification is mechanical.
- Support registering system-specific controls, including weakened-prover controls that expect `accept` (such as SASH's unsound switches).
- Define a disclosure workflow for unexpectedly accepted controls.

## Non-Goals

- Format-aware fuzzing of proof internals, which requires per-system format specifications and belongs in a later RFC.
- Certifying cryptographic soundness; passing this suite shows only that these specific tamperings were rejected ([PRD Section 5](../docs/PRD.md#5-non-goals)).
- Testing bindings between a proof and live served traffic, which no v0.1 system claims.
- Publishing control verification timings as benchmark rows; trial durations are saved in `controls.json` but never published as performance metrics.

## Proposed Design

### Where controls run

Running `iproofs run ... --control-suite` executes the suite once per configuration right after the honest `verify` step of the first successful repetition (controls check verifier behaviour rather than run-to-run variance, and prover-side controls require full proving runs). Alternatively, `iproofs controls RUN_DIR` runs the suite against an existing completed run ([RFC-0010](0010-harness-runner.md)), either all at once or split across multiple hosts (§Split suites). The suite takes the run's honest proofs, requests, claimed outputs, and the harness's saved commit record. The harness writes each mutated input into a fresh verify I/O directory and calls the adapter's `verify` subcommand unchanged (INV-CTRL-1).

### Seeds

Every control suite draws a single 64-bit `control_seed` from `os.urandom` at startup (or once before the first part in a split suite, per SPLIT-1) and stores it in `controls.json`. Operators cannot pick the seed manually: `iproofs controls` accepts no `--seed` flag for a full suite run. Individual controls draw randomness from `random.Random(f"{control_seed}:{control_id}:{k}")` using only `.random()`, the one method CPython guarantees stable across versions, choosing an index in `[0, m)` via `floor(r * m)`. Replaying with the recorded seed reproduces every mutation byte for byte (INV-CTRL-3).

### Split suites

Amendment of 2026-11-09 (enabling parallel control collection). A control suite may be partitioned into parts, executed across multiple hosts concurrently, and merged into the single `controls.json` associated with a run. Every other rule in this RFC applies unchanged to each control inside each part.

- SPLIT-1. One seed, drawn once. `iproofs controls RUN_DIR --draw-seed` draws `control_seed` from `os.urandom` and writes it, along with the UTC timestamp, run ID, and SHA-256 of the run's `manifest.json`, to `RUN_DIR/controls-seed.json` (`controls-seed/1`, [RFC-0012](0012-schemas-and-serialization.md)). The command refuses to run if `controls-seed.json` or `controls.json` already exists, ensuring each run has a single seed record and one suite. Each part reads its seed from that file (`iproofs controls RUN_DIR --only ID[,ID...]`); passing `--seed SEED` (hex or decimal) only cross-checks the recorded seed, failing if it differs or if used without `--only`. Running a whole unsplit suite is refused once a seed record exists. Every part execution attempt, whether finished or interrupted, is recorded in the campaign log.
- SPLIT-2. Whole controls. Every part executes complete controls, keeping each control's honest twin in the same part (INV-CTRL-2) and deriving all mutations from `control_seed` and the control ID (INV-CTRL-3). All five trials of C6 and its twin remain together, so a control's result never depends on which other controls ran alongside it. Any part that would behave differently from a single-host run is refused before making a call (for instance, running P1 when a perturbed commitment exists but its perturbed weights are missing from the local cache).
- SPLIT-3. One run, one image, matching profiles. Every part must target the same run directory (matching run ID and `manifest.json` SHA-256), run inside the same adapter image, and use the same harness version and commit with a clean checkout across `harness/`, `systems/<system>/`, `schema/`, and `reference/`. Verifier-side controls run on hosts matching the run's verifier profile, prover-side controls (P1, P2, and `weakened_prover`) run on hosts matching the run's prover profile, and every part binds `verify` calls to `verifier-cpu`'s CPU count (`cpu.logical_cpus`) regardless of GPU presence. Running a prover-side part on a GPU model different from the run's machine record is refused. A host unable to prove (lacking a GPU on a GPU profile, or configured as verifier-only) rejects prover-side controls before any call so an impossible prove step is never misclassified as `prover_failed`. Any other profile conformance failures ([RFC-0006](0006-reference-hardware-and-cost.md), including `verifier-cpu` memory on a verifier-only host) are recorded in the part file rather than blocking execution.
- SPLIT-4. Parts. Each part is saved as a `controls-part/1` document ([RFC-0012](0012-schemas-and-serialization.md)) named `controls-part-<16 hex of the seed>-<12 hex of the sha256 of the subset>.json`. It records the control subset, the complete suite order expected by `controls.json`, all provenance fields required by SPLIT-1 and SPLIT-3 (seed and seed-record SHA-256, run ID and manifest digest, image digest, verifier and run profiles, verifier CPU count, perturbed commitment, and harness version, commit, and dirty flag), the executing host's RFC-0006 machine record and any profile conformance failures (which may differ across parts), and the subset's control records. Part files are working artifacts archived alongside the run's evidence and never committed under `results/`; the merged `controls.json` preserves every trial's `seconds`, while the part files trace which host produced each measurement. Whenever a control call finishes, the runner appends a `control.call` entry (`control`, `trial`, `subcommand`, `exit_code`, `seconds`) to `harness.jsonl` so progress is visible and interrupted parts leave timing spans for completed calls.
- SPLIT-5. Merge. `iproofs controls RUN_DIR --merge PART...` requires `run.json`, `manifest.json`, and `controls-seed.json` in `RUN_DIR`. It aborts with a `config` error (writing nothing) if any part fails `controls-part/1` validation, targets a different run or seed record, disagrees on any pre-host SPLIT-4 field, contains records outside its declared subset, duplicates or omits any control in the suite, includes a control outside the suite, or if `controls.json` already exists. On success, it emits records in suite order, recomputes `summary` (INV-CTRL-5) and `disclosure_pending`, validates the result against `controls/1`, and writes `controls.json` beside the stored run. Running `iproofs controls --only` against a run that already has `controls.json` is likewise refused.
- SPLIT-6. Interrupted parts. A part terminated early (by deadline, job cancellation, or host failure) writes no part file. Its controls are rerun in a fresh part using the same seed record, reproducing all mutations byte for byte, with a deadline informed by the interrupted run's `control.call` spans; the interrupted job's log stays in the campaign record (AGENTS.md rule 5). A control whose call completed with an error is not rerun; its `error` outcome remains in its part.

### Proof selection

Controls operate on honest proofs accepted during the run's own `verify` step. The harness selects `target` as the first accepted proof in release order, and for two-request controls selects `other` as the next accepted proof in release order with a distinct request. If the run has no accepted proofs, every control is recorded as `void`.

### Shared controls, verifier side

All verifier-side controls operate on honest proofs, reading `vocab_size` from the workload's model record ([RFC-0003](0003-workloads.md)).

The harness submits every verifier-side control trial to the adapter as a normal verification call: `job.json` sets `control: false` and uses the exact same schema and fields as a counted `verify` call. Because the job file does not advertise that a call is a control, a verifier that behaves honestly only when `control: true` is caught when it accepts a tampered proof. This hides the explicit flag, though not every possible side channel: in a level run, counted verifications execute under the trace wrapper ([RFC-0018](0018-level-1-ladder.md)) while control verifications do not, so a verifier probing for a tracer could still distinguish them (closing that gap remains open work). The harness still tracks the trial internally as a control and keeps it out of measured rows based on its own state (INV-CTRL-4), not on `job.json`. This rule applies strictly to `verify`; prover-side controls (P1, P2, `weakened_prover`) still pass `control: true` so the adapter allows perturbed weights W' and weakening flags that rule 4 otherwise forbids.

| ID | Control | Expected set |
|---|---|---|
| C1 | Change the claimed output token | {`reject`} |
| C2 | Change one prompt token in the request | {`reject`} |
| C3 | Verify against the commitment of perturbed weights | {`reject`} |
| C4 | Replay a valid proof for a different request | {`reject`} |
| C5 | Truncate the largest part the verifier reads | {`reject`, `invalid_call`} |
| C6 | Flip one bit at a seeded offset in a seeded part the verifier reads, 5 seeds | {`reject`, `invalid_call`} for each seed |
| C7 | Swap the proofs of two requests in one batch | {`reject`} |
| C8 | Drop one part the verifier reads | {`reject`, `invalid_call`} |

Algorithms (pseudo-code, where `rng(cid, k)` is the seeded generator above and `read(target.parts)` denotes the subset of `target.parts` that the adapter declares its `verify` step reads; see §Parts the verifier reads):

```
C1: out = target.claimed_output.copy(); i = len(out) - 1
    out[i] = (out[i] + 1) mod vocab_size
    verify(commit, request=target.request, claimed_output=out, proof=target.proof)

C2: req = target.request.copy(); p = floor(rng("C2",0).random() * len(req))
    req[p] = (req[p] + 1) mod vocab_size
    verify(commit, request=req, claimed_output=target.claimed_output, proof=target.proof)

C3: verify(commit_perturbed, request=target.request,
           claimed_output=target.claimed_output, proof=target.proof)

C4: verify(commit, request=other.request, claimed_output=other.claimed_output, proof=target.proof)
    # applicable iff other exists and other.request != target.request

C5: part = argmax_by(size, then name) over read(target.parts)
    write part truncated to floor(size/2) bytes; other parts unchanged; verify(commit, target fields, mutated proof)

C6: for s in 0..4:
      parts = sorted(read(target.parts) by name)
      part = parts[floor(rng("C6",2s).random() * len(parts))]
      off  = floor(rng("C6",2s+1).random() * size(part) * 8)   # bit offset
      flip bit (off mod 8) of byte (off div 8); verify(commit, target fields, mutated proof)
    # one outcome per seed; C6 passes iff all five outcomes are in the expected set

C7: pick two accepted proofs a, b from the same batch with a.request != b.request
    verify(commit, request=a.request, claimed_output=a.claimed_output, proof=b.proof)
    # applicable iff batch_size >= 2

C8: parts = sorted(read(target.parts) by name); q = parts[floor(rng("C8",0).random() * len(parts))]
    proof directory without q; out.json parts list without q; verify(commit, target fields, mutated proof)
    # applicable iff len(target.parts) >= 2 (every part, read or not)
```

For C3, `commit_perturbed` commits to a copy of the workload's weights with one tensor modified: the harness copies the model directory, finds the lexicographically first weight tensor containing at least 1,024 elements, and adds one unit in the last place to element 0 at its stored precision. Because committing an entire model is expensive (FlashProve's full-size route needs roughly 330 GB of host memory just to start committing; [RFC-0006](0006-reference-hardware-and-cost.md)), the perturbed commitment is generated once per workload per release via `iproofs controls --prepare-perturbed WORKLOAD` and reused thereafter. Its commit record carries its own digest and lives under `results/<release>/<system>/_controls/<workload>/`, while the perturbed weight files stay on the runner host. If a system cannot commit the perturbed weights (for example, due to a fixed-architecture loader rejecting them), C3 is recorded as `not_applicable` along with the reason.

### Parts the verifier reads

Amendment of 2026-11-09 (prompted by a development run on Hugging Face Jobs on 2026-11-09). Mutating a proof file that the adapter's `verify` step never opens tests nothing: the altered bytes never reach the verifier, so an `accepted` verdict reveals nothing about the system. During that development run (FlashProve on `fp-maverick-w1024-b1`, recorded in the campaign's working `controls.json` outside `results/`), C6 seeds 0 and 3 flipped bits inside `response.proof` and were rejected (`NO: proof-refused`), whereas seeds 1, 2, and 4 flipped bits 9, 16, and 28 of `response.y` (the 4-byte next-token file written by `cp_prove`) and were accepted, causing C6 to report `accepted`. Because the FlashProve adapter reconstructs the token file passed to `cp_verify` from the job's `claimed_output` in the harness record (INV-CTRL-6) and passes only `response.proof`, `response.y` is never read by `verify` ([`systems/flashprove/README.md`](../systems/flashprove/README.md#values-for-systemyaml)). Control C1 already covers tampering with the claimed output token. This revealed a flaw in the control specification rather than a bug in FlashProve, so it does not trigger disclosure (§Disclosure) and is not reported as a FlashProve failure.

- READ-1. Declaration. `proofs.verify_reads` in `system.yaml` (optional in `system/1`, [RFC-0005](0005-adapter-contract.md#systemyaml)) declares which proof parts the adapter's `verify` step actually reads: either `"all"`, or `{read: [part, ...], not_read: [{part, reason}, ...]}` where both lists are non-empty and every entry names a file from `out.json` `parts[]`. Omitting the field defaults to `"all"`, matching prior behaviour. The declaration is static, reviewed alongside the adapter code, and loaded by the harness from the repository checkout without invoking a container, ensuring every part of a split suite uses the same declaration (SPLIT-3). Each adapter README must explain, with links to the pinned upstream commit, why any unread part is skipped. Prover adapters should populate this field explicitly even when reading all parts (enforced during review, while `system/1` keeps it optional for backwards compatibility).
- READ-2. Fit. Before executing any calls in a full suite or split part, the harness verifies that `proofs.verify_reads` matches the target proof (§Proof selection). If a declared part is missing from the proof, a proof part is omitted from the declaration, or a part is listed twice, the harness aborts with a `config` error and writes nothing.
- READ-3. Candidates. Controls C5, C6, and C8 draw candidate parts exclusively from `read(target.parts)`, sorted by filename as before. Seeds, RNG calls, bit offsets, applicability checks, and expected sets remain identical, and C8's precondition still counts all parts in `target.parts` so a mutated proof retains at least one file. When `verify_reads` is `"all"`, every mutation is byte-for-byte identical to the pre-amendment specification.
- READ-4. Record. In `controls.json`, the records for C5, C6, and C8 include every unread part and its declared reason under `parts_not_read` (an optional `controls/1` field omitted when all parts are read). Controls C1 through C4 and C7 do not mutate proof parts and omit this field.
- READ-5. Stored files. Any `controls.json`, part file, or seed record created before this amendment remains untouched; past records are never edited or recomputed under updated candidate lists (append-only rule, [RFC-0009](0009-results-and-publication.md)). Rerunning the suite produces a separate record with a fresh seed rather than overwriting earlier results. No `controls.json` under `results/` predates this amendment.

### Shared controls, prover side

| ID | Control | Expected set |
|---|---|---|
| P1 | Commit W, prove with W' (the C3 perturbation) | {`prover_failed`, `reject`} |
| P2 | Prove with a precision other than the committed one | {`prover_failed`, `reject`}; `not_applicable` when the system supports one precision |

P1 invokes `prove` using `model_dir` pointed at W' alongside the `commitment_id` computed from W, at the workload's smallest batch size and `batches: 1`. If `prove` exits non-zero, the outcome is `prover_failed`; if it emits a proof, the harness runs `verify` against the commitment of W, expecting `reject`. P2 follows the same procedure using weights converted to an alternative precision whenever the workload declares one; otherwise it is `not_applicable`. Prover-side controls run with `control: true` and never appear as measured rows.

### Honest twins

Every verifier-side control runs its honest twin immediately beforehand: `verify(commit, target.request, target.claimed_output, target.proof)` on the unmodified bytes, inside the same control batch, using the same image digest and verifier profile. Controls C4 and C7 run twins for both proofs involved. If any twin does not return `accept`, the control's outcome is `void` (INV-CTRL-2). For P1, the honest twin is the original run's honest `prove` and `verify`.

### Outcomes

Each control records an `outcome` from the closed set: `rejected` (verdict `reject`), `accepted` (verdict `accept`), `no_verdict`, `invalid_call`, `void`, `not_applicable`, `error` (an adapter or harness failure during the control, saved with its failure record), or `prover_failed` (for prover-side controls). A control **passes** if and only if its outcome (or, for C6, all five per-seed outcomes) falls within its expected set (mapping `reject` to `rejected`). Outcomes of `void`, `not_applicable`, and `error` neither pass nor fail and are tallied separately.

### controls.json

Generated JSON validated against schema `controls/1` ([RFC-0012](0012-schemas-and-serialization.md)):

```json
{
  "schema": "controls/1",
  "run_id": "2026-11-03-fake-fake-tiny-ci-ci-cpu-1",
  "control_seed": "0x5f3c9a12d4e6b780",
  "image": "ghcr.io/<org>/iproofs-fake@sha256:<64 hex>",
  "verifier_profile": "verifier-cpu",
  "perturbed_commitment": {"commitment_id": "...", "model_digest": "sha256:..."},
  "controls": [
    {
      "id": "C6", "side": "verifier", "source": "shared",
      "expected": ["rejected", "invalid_call"],
      "twin": {"verdict": "accept", "raw_exit_code": 0},
      "trials": [
        {"seed_index": 0, "mutation": {"part": "tag.bin", "bit_offset": 117}, "verdict": "reject",
         "outcome": "rejected", "raw_exit_code": 1, "raw_last_line": "...", "seconds": 0.012}
      ],
      "outcome": "rejected", "passed": true, "note": null
    }
  ],
  "summary": {"run": 10, "passed": 8, "rejected": 8, "accepted": 0, "no_verdict": 0,
              "invalid_call": 0, "void": 0, "not_applicable": 2, "error": 0, "prover_failed": 0}
}
```

`seconds` captures the adapter-reported verification duration for that trial. `summary` counts are derived from `controls` and verified in CI by `iproofs derive --check` (INV-CTRL-5).

### System-specific controls

An optional `systems/<name>/controls.yaml` file (schema `system-controls/1`) registers additional controls from the upstream system's own test suite:

```yaml
schema: "system-controls/1"
controls:
  - id: "flashprove-rejected-proofs"         # ^[a-z0-9-]{3,64}$, unique per system
    kind: "fixture_proof"                     # fixture_proof | weakened_prover
    description: "upstream examples/rejected-proofs at the pin"
    source: "https://github.com/anthropics/FlashProve/tree/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/examples/rejected-proofs"
    expected: ["rejected"]
  - id: "sash-unsound-skip-<edge>"
    kind: "weakened_prover"
    control_flags: ["--unsound-skip-<edge>"]  # exact flag names copied from upstream docs at the pin
    expected: ["accepted"]
    requires_unbound_edge: "<edge>"           # pass iff the binding report marks this edge unbound
```

- `fixture_proof` controls verify an upstream-provided proof fixture as is, paired against the run's honest proof as its twin.
- `weakened_prover` controls execute `prove` with `control: true` and `control_flags`, followed by `verify`. SASH's unsound switches are registered here with `expected: ["accepted"]`; the control passes only if `out.json`'s `binding_report` marks the corresponding edge unbound. This checks that the switch behaves honestly and that the claim card's binding table is accurate, not that the verifier rejects the weakened proof ([RFC-0002](0002-claim-card.md)).
- The SASH adapter implementation copies the exact edge and flag names from upstream documentation at the pin rather than hardcoding them in this RFC.

### Applicability

A control is marked `not_applicable` (with an explanatory reason) whenever its precondition is unmet: C4 when there is no second distinct request, C7 when `batch_size` is 1 or fewer than two proofs in one batch were accepted, C8 when the proof has only one part, C3 and P1 when the perturbed commitment cannot be produced, and P2 when the workload declares only one precision. Applicability is checked before running the honest twin.

### Reporting

For each row, the site and release index report counts of controls run, passed, rejected, accepted, `no_verdict`, `invalid_call`, void, not applicable, and error ([RFC-0009](0009-results-and-publication.md)). Every unexpected `accepted` outcome (where rejection was expected) is displayed in full with its control ID, mutation details, and raw last line, and every `no_verdict` outcome is listed explicitly.

### Verifier trials (amended 2026-11-15)

A verifier trial is any set of verification calls against stored proofs outside a counted session and its standard control suite, such as running a publisher's alternate verifier on stored proofs, running the C3 null twin (verifying a proof against a commitment from another session on the same weights), or running C1 across every reply token position. Each trial is recorded at `results/<release>/<system>/_trials/<trial id>/trial.json` (`verifier-trial/1`), with individual call outputs stored under `raw/`.

- TR-1. Trials are informational and gate nothing: no check, petal, ranking position, or ordering reads them. A page may display a trial's counts and timing range (computed via `iproofs.trials.summary`) accompanied by the verifier program name, host, sample size `n`, and the label "gates nothing".
- TR-2. Every commitment used by a trial MUST come from a harness record (INV-CTRL-6). Any source tagged `in_results` references a run directory under `results/`; gate G4 (`TRIAL-1`) rejects a trial if its commitment ID disagrees with that run's manifest or its archive digest disagrees with `digests.txt`.
- TR-3. The verifier runs unpatched from the system's pinned upstream commit, and the trial record lists any gaps under `missing` (such as an external job script, unpinned downloads, or proofs whose run directory is outside `results/`). Any duration measured by an external job script is treated as an adapter-reported timing (RFC-0004 INV-GRADE-2) and never feeds a derived metric.
- TR-4. If a tampered call inside a trial is unexpectedly accepted, it follows the §Disclosure workflow.

### Disclosure

An `accepted` outcome on a control expecting rejection signals either an adapter bug or a potential soundness issue in the prover. The harness sets `disclosure_pending: true` in `controls.json` (a computed field stored under that key). First, the runner inspects the adapter: if a verdict-mapping bug caused the result, the adapter is fixed in this repository and the run is repeated (this is not a finding against the upstream system). Otherwise, the runner reports the issue privately to the system maintainers using their published security policy or repository contact, withholding any public pull request containing that run until the embargo window in `SECURITY.md` expires. Once the embargo ends, the run is published in full without softening the outcome ([06-security](../docs/spec/06-security.md)).

### Invariants

- **INV-CTRL-1:** All mutated inputs are created by the harness; adapters are never asked to mutate data.
- **INV-CTRL-2:** Any control whose honest twin fails to return `accept` is recorded as `void`, never `rejected`.
- **INV-CTRL-3:** Every mutation is a deterministic function of `control_seed`, the control ID, and the honest inputs.
- **INV-CTRL-4:** Control jobs never produce measured rows, and no measured row may originate from a job with `control: true`.
- **INV-CTRL-5:** `summary` in `controls.json` matches the counts recomputed from `controls`.
- **INV-CTRL-6:** Every verification commitment in a control call comes from the harness's own commit records (either the run's original commitment or the perturbed commitment), never from proof files.
- **INV-CTRL-7:** Merging split parts into `controls.json` (§Split suites) produces bytes identical to running the entire suite in one shot with the same `control_seed` and identical verify outcomes.
- **INV-CTRL-8:** Controls C5, C6, and C8 never mutate a proof part declared unread by the adapter's `verify` step, and their records list each unread part along with its reason (§Parts the verifier reads).
- **INV-CTRL-9:** `job.json` for a verifier-side control call does not signal that it is a control: it sets `control: false` and uses the exact fields of a measured `verify` call (§Shared controls, verifier side).

### Failure modes

| Failure | Response |
|---|---|
| Honest twin not accepted | Control marked `void`; the harness cross-checks the original run's honest verify verdict and logs a `control.twin_mismatch` event on discrepancy |
| Adapter exits non-zero during a trial | Outcome recorded as `error` with the failure record; remaining controls continue |
| Perturbed commitment cannot be built | C3 and P1 recorded as `not_applicable` with the reason |
| Mutation leaves bytes identical to original (e.g. C1 with `vocab_size` 1) | Harness asserts the mutated input differs; if not, records `error` with kind `internal` |
| Verify call times out during a trial | Outcome recorded as `error` with kind `timeout` |
| `proofs.verify_reads` disagrees with the target proof (READ-2) | `config` error before any container call; nothing written |
| Control accepted where rejection was expected | `disclosure_pending: true`; private report sent to upstream maintainers |

## Alternatives Considered

1. **Having adapters implement tampering themselves.** Adapters know internal proof formats and could construct targeted semantic mutations, but letting the measured party author its own negative tests creates a conflict of interest and allows a verdict-mapping bug to hide behind a matching mutation bug. Harness-side byte and field mutations are narrower in scope, yet apply uniformly across every system without adapter cooperation.
2. **Omitting honest twins and relying on the original run's verify verdict.** Cuts verify calls in half, but a control suite can execute later in a different container or on corrupted files; running a twin in the same batch is the only way to confirm the verify pipeline works for unmodified inputs.
3. **High-volume random fuzzing across many seeds.** Increases coverage, but rejected for v0.1 because FlashProve's verification takes roughly 21 s per proof on one CPU thread (grade external, tier reported, source FlashProve docs at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`), making hundreds of trials prohibitively expensive. Five seeded bit flips plus truncation catch gross verification failures, while structured fuzzing is left for a later RFC.
4. **Binary pass/fail outcomes without `void`, `not_applicable`, or `error`.** Rejected because collapsing those states obscures whether a control actually tested the verifier.
5. **Reading `verify_reads` from the adapter's `info` output** (§Parts the verifier reads). Considered because `info` already reports image metadata, but rejected because `info` is emitted by the measured container at runtime, whereas `system.yaml` is reviewed alongside the adapter README, read by the harness before any call, and identical across all split parts at one commit.
6. **Modifying the adapter's `verify` step to check unread files** (for example, comparing `response.y` against `claimed_output`). Rejected because adding checks in the adapter would test adapter code rather than the upstream verifier, and C1 already tests tampering with the claimed token.
7. **Immediate public disclosure of accepted controls.** Considered for openness, but rejected because an accepted control may reflect a real soundness vulnerability in a deployed prover; a time-bounded embargo follows standard security practice while still guaranteeing full publication afterward.

## Drawbacks

- Opaque byte mutations cannot test semantic attacks that a format-aware adversary might craft; passing C5 and C6 demonstrates basic integrity checking, not cryptographic soundness.
- C3 and P1 require committing a second, perturbed copy of the weights once per workload per release, which is heavy on host memory and wall time for Maverick-sized models.
- Running the shared suite adds roughly 22 `verify` calls per configuration (trials plus twins; a count of calls, not a measurement), multiplying verifier CPU time accordingly.
- System-specific control coverage varies depending on what each upstream project ships; each row indicates which controls ran.
- `proofs.verify_reads` matches parts by exact filename. A system with varying part names per proof that leaves some parts unread would need pattern matching in a future amendment (neither SASH nor FlashProve needs this).
- `verify_reads` relies on adapter authors and code review rather than automated enforcement by the harness. If a part is misclassified as unread, it will never be mutated, though its name and stated reason appear in every C5, C6, and C8 record so reviewers can catch mistakes.

## Migration / Rollout

- Supersedes the control list from the initial design commit, retaining IDs C1 to C8, P1, and P2 while fixing C6 at five seeds and specifying exact algorithms.
- Harness mutation and classification logic is verified against `systems/fake` (every applicable shared control passes) and `systems/fake-broken` (every applicable verifier-side control records `accepted`).
- The full suite runs against SASH and FlashProve rows along with their registered system-specific controls.
- Split suites (amendment of 2026-11-09) preserve all existing controls, algorithms, expected sets, and `controls/1` fields, while adding `controls-seed/1`, `controls-part/1`, the `control.call` log event, and the `--draw-seed`, `--only`, `--seed`, `--merge`, `--hosted`, `--gpu`, and `--provider` flags on `iproofs controls`. Merged outputs are identical to standard `controls.json` files (INV-CTRL-7).
- Parts the verifier reads (amendment of 2026-11-09) preserves all control IDs, applicability rules, expected sets, and required fields, restricting C5, C6, and C8 candidates to declared read parts and adding optional `proofs.verify_reads` (`system/1`) and `parts_not_read` (`controls/1`). With `"all"` or no declaration, mutations are unchanged, and existing stored records remain untouched (READ-5).
- Adding a new control or modifying an algorithm or expected set requires amending this RFC (and bumping `controls/<major>` if the schema breaks). Past `controls.json` files are never edited and record which RFC version produced them.

## Testing Strategy

- `test_c1_changes_last_token_mod_vocab`: with `vocab_size = 10` and last token 9, verifies the mutated token wraps to 0.
- `test_c2_seeded_position_stable`: confirms identical `control_seed` produces the same position across separate processes, and that different seeds vary the position on a 1,024-token request across ten fixed seeds.
- `test_c5_truncates_largest_part_tiebreak_by_name`: given two equal-sized parts, verifies the lexicographically first part is truncated to `floor(size/2)` bytes.
- `test_c6_five_trials_flip_one_bit`: confirms each trial differs by exactly one bit from the original and reproduces identically from the seed.
- `test_c7_not_applicable_batch_one` and `test_c8_not_applicable_single_part`: confirm applicability checks.
- `test_c6_chooses_only_read_parts`, `test_c5_truncates_largest_read_part`, `test_c8_drops_only_read_parts` (READ-3): when one part is declared unread, verifies all trials target read parts sorted by name, and `"all"` matches pre-amendment mutations.
- `test_declaration_that_does_not_fit_is_refused_before_any_call` (covers a declared part missing from the proof and an undeclared proof part, across both a full suite and a part omitting C5, C6, C8), `test_part_placed_twice_refused`, and `test_controls_refused_when_a_declared_part_does_not_exist` (invoked through `iproofs controls`, verifying nothing is written) (READ-2).
- `test_unread_part_finding_reproduced_then_closed` (READ-3, READ-4, INV-CTRL-8): on a fixture system whose verifier skips one part, verifies the undeclared suite yields an accepted C6 trial on that part, while adding the declaration restricts C5, C6, and C8 to read parts, eliminates the accepted outcome, records `parts_not_read` with the reason, and leaves C1 through C4 and C7 identical. `test_controls_on_a_stored_run_read_the_declaration`: verifies controlling a stored run created prior to adding the declaration reads the updated declaration.
- `test_twin_failure_voids_control`: a fake verifier rejecting all inputs yields `void` for every control rather than `rejected`.
- `test_fake_all_shared_controls_pass`: on `systems/fake`, every applicable control passes with `summary.accepted == 0`.
- `test_fake_broken_all_accepted`: on `systems/fake-broken`, every applicable verifier-side control records `accepted` and `disclosure_pending` is `true`.
- `test_summary_recomputed`: altering a single outcome in a stored `controls.json` causes `iproofs derive --check` to fail.
- `test_weakened_prover_requires_unbound_edge`: a `weakened_prover` control returning `accepted` fails if its binding report still marks the edge bound.
- `test_control_job_never_measured_row`: a run directory carrying `control: true` fails `iproofs validate` if listed among a release's measured rows ([RFC-0013](0013-validation-and-ci.md)).
- `test_commitment_never_from_proof`: planting a forged commitment file inside a proof directory does not alter the commitment passed to `verify`.
- `test_merged_parts_equal_one_run_byte_for_byte` (INV-CTRL-7): on `systems/fake` with a perturbed commitment (C3, P1) and three system controls, confirms running the suite in one shot and running it across three split parts on separate copies of the run, then merging in a directory holding only `run.json`, `manifest.json`, and `controls-seed.json` under the same seed, produces byte-identical output.
- `test_split_runs_with_one_drawn_seed`: verifies parts require a seed record, the seed record can only be drawn once, a mismatched `--seed` is rejected, and running a whole suite after drawing a seed is rejected (SPLIT-1).
- `test_merge_refuses_*`: verifies merge rejects parts from a different run, seed record, or SPLIT-4 provenance field, as well as overlapping, missing, or mismatched subset records (SPLIT-5).
- `test_prover_side_refused_where_no_prove_can_run`: verifies prover-side controls abort before any call on a verifier host or on a GPU profile without `--gpu` (SPLIT-3); `test_prover_part_records_its_host_and_refuses_another_gpu` and `test_p1_part_refused_without_the_perturbed_weights` (SPLIT-2, SPLIT-3).

## Decisions

- Q1. No controls test binding between proofs and served traffic because no v0.1 system makes that claim.
- Q2. C3 and P1 run on SASH workloads, and on FlashProve's smallest supported synthetic shape whenever committing a full-size perturbed Maverick model exceeds the release compute budget (with the substitution noted in the row); otherwise they are recorded as `not_applicable`.
- Q4. Upstream rejected-proof examples bundled with their own commitments (such as FlashProve's `examples/rejected-proofs`) are registered as controls only if the harness can regenerate their commitments via `commit`, since commitments always come from harness records (INV-CTRL-6); otherwise they are documented in the adapter README and not executed as controls.
- Q5. `fixture_proof` controls are recorded as `not_applicable` with that reason because `system-controls/1` specifies only an upstream `source` URL and adapters see only `/io` and `/models`, leaving no channel to supply the fixture bytes to the harness. `weakened_prover` controls execute as specified.
- Q6 (2026-11-15). Verification calls outside a session's standard suite are recorded as verifier trials that gate nothing (§Verifier trials), providing supplemental evidence alongside the six checks without affecting check states.

## References

- [RFC-0002 Claim card](0002-claim-card.md), [RFC-0003 Workloads](0003-workloads.md), [RFC-0005 Adapter contract](0005-adapter-contract.md), [RFC-0009 Results](0009-results-and-publication.md), [RFC-0010 Harness runner](0010-harness-runner.md), [RFC-0012 Schemas](0012-schemas-and-serialization.md), [RFC-0013 CI gates](0013-validation-and-ci.md).
- FlashProve `examples/rejected-proofs` at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`; SASH `--unsound-skip-*` switches at `eb95bfa887299d1637550228d42086c27cbb2b3b`.
- Python `random` module reproducibility guarantee (CPython documentation, "Notes on Reproducibility").
