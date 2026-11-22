# Writing an adapter

This guide is for anyone adding a system to the benchmark. An adapter is a thin wrapper around upstream tools pinned to a full commit hash. It must never patch upstream source code or pass undocumented options (AGENTS.md rule 1, INV-ADAPTER-1). The authoritative specifications live in the RFCs linked from each section; if anything here conflicts with an RFC, the RFC takes precedence.

`systems/fake` provides a complete worked example in a single standard-library Python file that CI runs end to end (see [Walkthrough](#walkthrough-systemsfake)).

## 1. Ask first

Start by opening an issue that specifies the upstream repository, the full commit hash, and the workloads the system supports. The adapter, `system.yaml`, and `claim.yaml` are then submitted via pull request.

## 1a. From an adapter to a row on Level 1

Merging an adapter does not automatically create a row on the Level 1 ladder. The full rules are in [RFC-0018](../rfcs/0018-level-1-ladder.md) and [`levels/L1.yaml`](../levels/L1.yaml); the summary below points to the key requirements without modifying them.

- **Rungs.** The level specification chooses each rung, not the entrant ([LV-2](../rfcs/0018-level-1-ladder.md#levels)). Level 1's rungs are listed under `rungs` in [`L1.yaml`](../levels/L1.yaml#L51-L126), ordered from largest model to smallest.
- **The request.** Every rung uses the same fixed request ([`request`](../levels/L1.yaml#L9-L14), [§Terms](../rfcs/0018-level-1-ladder.md#terms)), while each rung defines how many requests are proved per session (`requests_per_session`).
- **Who runs.** Only the benchmark operator executes counted sessions. Level 1 does not accept external lab-run submissions or third-party reruns ([§Non-Goals](../rfcs/0018-level-1-ladder.md#non-goals)), so while you can share your own run in an issue as supporting evidence, it will not count as an official session.
- **Adapter duties.** Level 1 extends the adapter contract with requirements AD-1 through AD-7 ([§Adapter contract amendment](../rfcs/0018-level-1-ladder.md#adapter-contract-amendment-rfc-0005)):

  ```
  - [ ] AD-1. verify passes upstream the range that checks every reply token
  - [ ] AD-2. optional `logprobs`: full next-token distributions for the KL figure (FI-7)
  - [ ] AD-3. under exact match, each reply is the committed model's own greedy reply, made with what upstream ships at the pin
  - [ ] AD-4. a separate generation phase writes /io/marks/generation.start and generation.end
  - [ ] AD-5. optional `perturb`: writes W′, the Model check's weight change (CH-2), on CPU
  - [ ] AD-6. `mutate_reply`, needed for REPLY when the verifier reads the reply from the proof
  - [ ] AD-7. optional `score`: the system's own top token at each reply position (FI-10 to FI-13)
  ```

- **Required files for a row:**
  - `systems/<name>/claim.yaml`, the claim card ([RFC-0002](../rfcs/0002-claim-card.md)).
  - `systems/<name>/properties.yaml` (schema `properties/2`), recording the publisher's stated facts at the pinned commit ([GL-1](../rfcs/0018-level-1-ladder.md#the-glyph), [SI-4a](../rfcs/0018-level-1-ladder.md#site)).
  - Entries in `levels/L1.yaml`: the system's workload under its rung's `workloads` ([L59](../levels/L1.yaml#L59), [L85](../levels/L1.yaml#L85), [L109](../levels/L1.yaml#L109)), plus a `systems.<name>` block containing `security`, `model_change`, and any `limits` ([L130-L148](../levels/L1.yaml#L130-L148), [§The level file](../rfcs/0018-level-1-ladder.md#the-level-file), CH-2, CH-5).
  - The workload definition in `workloads/`, including the system in its `systems` list ([example](../workloads/l1-l31-8b-p512-o512.yaml#L47)). Running `uv run iproofs level check` flags any rung workload whose prompts, shape, or decoding differ from the level specification, or whose `systems` list omits the system.
- **Sessions and checks.** Each rung runs three session slots with up to five attempts per slot ([`sessions`](../levels/L1.yaml#L23-L26), [SE-3](../rfcs/0018-level-1-ladder.md#sessions-and-what-is-recorded)). All six checks are computed exclusively from stored records ([§The six checks](../rfcs/0018-level-1-ladder.md#the-six-checks), CH-6).
- **Ordering.** Only rows that pass all six checks are ranked, and ranking applies strictly within a single rung ([OR-1](../rfcs/0018-level-1-ladder.md#order)). A passing row receives a ranked position only if `systems.<name>.security.stated` is true in `L1.yaml` with supporting wording and source (OR-2) and `properties.yaml` records `level_statement.accept_is_model_reply` as true with quotes from the pinned commit ([SI-4a](../rfcs/0018-level-1-ladder.md#site)). Otherwise, it appears as passed but unranked, accompanied by the reason.
- **Before a run.** Systems that have not been run are listed below the ladder with a single reason from `web/_data/facts.json` (such as `not yet run`), selected according to the precedence order in [SI-4b](../rfcs/0018-level-1-ladder.md#site).

Because the Level 1 roster (`rungs[].workloads` and `systems`) lives inside `levels/L1.yaml`, every counted run records the SHA-256 digest of that file, and `iproofs release freeze` rejects any release whose runs reference a different digest ([§The level file](../rfcs/0018-level-1-ladder.md#the-level-file)). Level 1 is currently frozen ([L8](../levels/L1.yaml#L8)), and frozen level files do not change ([LV-1](../rfcs/0018-level-1-ladder.md#levels)). Adding a new system to Level 1 therefore modifies the level file, so please open an issue before editing it.

## 2. Directory layout

The required files are specified in [RFC-0005 §Layout](../rfcs/0005-adapter-contract.md#layout): `Dockerfile`, `entrypoint`, `system.yaml`, `claim.yaml`, optional `external.yaml` and `controls.yaml`, plus `README.md` and `tests/`. System names must match `^[a-z][a-z0-9-]{1,31}$`.

## 3. `system.yaml`

The structure and validation rules for every field are defined in [RFC-0005 §system.yaml](../rfcs/0005-adapter-contract.md#systemyaml) and [`schema/system/1.schema.json`](../schema/system/1.schema.json). Pay particular attention to these fields:

- `upstream.commit`: A full 40-character lowercase hexadecimal commit hash, which the Dockerfile checks out and verifies (INV-ADAPTER-2).
- `proofs.granularity`, `proofs.tokens_covered`, `proofs.steady_boundary`: Define what each proof directory contains, how tokens are counted, and where `prove.steady` begins. Setting `incremental_proofs: false` requires `steady_boundary: not_observable` (INV-ADAPTER-10).
- `forbidden_flags`: Flag prefixes that weaken the system's statement. These are permitted only inside negative-control jobs ([RFC-0005 §Weakening configurations](../rfcs/0005-adapter-contract.md#weakening-configurations), [RFC-0008](../rfcs/0008-negative-controls.md)).
- `timeouts_s`: Specify a step timeout only when it needs to exceed the defaults; reviewers inspect custom timeouts.

Run `uv run iproofs validate systems/<name>` to validate the file against its schema.

## 4. What the container may do

The harness is the sole caller of your container and invokes every subcommand with the restrictions in [RFC-0005 §Container invocation](../rfcs/0005-adapter-contract.md#container-invocation). As an adapter author, design for the following constraints:

- **No network access** during any subcommand, including `setup`. Everything required at runtime must already be baked into the image or mounted under `/models` (INV-ADAPTER-4).
- **Read-only root filesystem.** Write only to `/io` and `/tmp`. Any state that must persist across steps within a single job goes in `/io/state/`.
- **Non-root user**, uid 10001 by convention, configured with `USER` in the Dockerfile.
- **Isolated verification:** `verify` runs with no GPU, no `/models` mount, and a memory limit, ensuring the verifier never has access to model weights.
- **Read-only commitments:** Recorded commitment files are mounted read-only. The commitment passed to `verify` always comes from the harness's record of `commit`, never from files emitted by `prove` (AGENTS.md rule 6, INV-ADAPTER-5, [RFC-0014 §The commitment record](../rfcs/0014-provenance-and-integrity.md#the-commitment-record)).

## 5. Subcommands, `job.json` and `out.json`

The harness invokes your adapter as `entrypoint <info|setup|commit|prove|verify> /io/job.json /io/out.json`. Common and per-subcommand fields are specified in [RFC-0005 §Subcommands and file shapes](../rfcs/0005-adapter-contract.md#subcommands-and-file-shapes), with schemas [`adapter-job/1`](../schema/adapter-job/1.schema.json) and [`adapter-out/1`](../schema/adapter-out/1.schema.json). Always exit 0 when the subcommand completed normally, regardless of the verification outcome; a rejected proof still exits 0 with `verdict: "reject"`.

All paths written to `out.json` must be absolute paths under `/io` or `/models`, or plain filenames inside a named directory. Any path escaping the job I/O directory, any symlink or device file under `/io/proofs/`, or any proof exceeding the part limits triggers an `adapter` failure ([RFC-0005 §Path safety](../rfcs/0005-adapter-contract.md#path-safety)).

## 6. Releasing proofs

The harness measures proof release timing by watching the filesystem ([RFC-0005 §Proof release protocol](../rfcs/0005-adapter-contract.md#proof-release-protocol)). Write all parts of a proof into `/io/proofs/.tmp-<proof_id>/`, then atomically `rename` that directory to `/io/proofs/<proof_id>`. Never modify a proof directory after renaming it. The `proof_id` entries in `out.json` must match the released directories one-to-one (INV-ADAPTER-6).

## 7. The command log

For every upstream subprocess your adapter launches, append one JSON line to `/io/commands.jsonl` containing `argv`, `cwd`, `started_mono_ns`, and `exit_code`, omitting environment variables ([RFC-0005 §Command log](../rfcs/0005-adapter-contract.md#command-log)). The policy gate inspects this log to verify that no forbidden flags were passed during a measured run ([RFC-0013 §G6](../rfcs/0013-validation-and-ci.md#g6-policy-check)). Any line of adapter source code that mentions a forbidden flag must be guarded by a `control` check and listed in `systems/<name>/policy-allow.txt` (rule POL-3).

## 8. Verdicts

Map the upstream verifier's documented exit codes and output signals onto `accept`, `reject`, `no_verdict`, and `invalid_call`, exiting non-zero for any unmapped signal; never guess a verdict ([RFC-0005 §Verdict normalisation](../rfcs/0005-adapter-contract.md#verdict-normalisation)). Document the full mapping table in your adapter README with links to the pinned upstream commit.

## 9. The Dockerfile

Follow rules B1 through B7 in [RFC-0014 §Adapter image build](../rfcs/0014-provenance-and-integrity.md#adapter-image-build): pin base images by digest, isolate all downloads into a single `fetch` stage verified against `systems/<name>/inputs.lock`, build offline using `RUN --network=none` afterwards, never patch or `sed` upstream source code, emit `/opt/iproofs/inputs.json` for `info` to return, bake in the adapter commit from a clean working tree, and push release images to `ghcr.io/ai-verification-observatory/` referenced by manifest digest. Only runs using clean builds are eligible for a release ([RFC-0014 §Eligibility](../rfcs/0014-provenance-and-integrity.md#eligibility)); local builds record `digest_kind: config`. The `images` workflow (`.github/workflows/images.yml`, triggered manually on `main`) builds `systems/<name>` from a clean checkout, pushes it, and outputs the manifest digest to pin in `system.yaml`.

List every downloaded input in `systems/<name>/inputs.lock`, one per line in `<name>\t<url>\tsha256:<hex>` format, and fetch each with `ADD --checksum=sha256:<hex> <url>` in the `fetch` stage. Pass the adapter commit and dirty flag as Docker build arguments so `info` can report `adapter_commit` and `adapter_dirty`, reading `image_inputs` from `/opt/iproofs/inputs.json`. See `systems/fake/Dockerfile`, `systems/fake/inputs.lock`, and `systems/fake/write_inputs.py` for the reference implementation. Each adapter's `tests/test_dockerfile_rules.py` calls `iproofs.provenance.dockerfile_problems(dockerfile, inputs_lock)` to verify rules B1 through B3.

Gate G7 automatically checks pins across every Dockerfile ([RFC-0013 §G7](../rfcs/0013-validation-and-ci.md#g7-pin-check)).

## 9a. System-specific controls

You can register controls from an upstream test suite in `systems/<name>/controls.yaml` (schema `system-controls/1`, [RFC-0008 §System-specific controls](../rfcs/0008-negative-controls.md#system-specific-controls)). The harness runs these after the shared controls and tags them with `source: system`:

- `weakened_prover`: Runs `prove` in a separate I/O directory with `control: true` and explicit `control_flags`, then verifies each proof against the run's recorded commitment. When `requires_unbound_edge` is specified, the control passes only if `out.json`'s `binding_report` marks that edge as unbound (encoded as a JSON object with `edges` formatted either as `{"<edge>": "bound" | "unbound"}` or as a list of `{edge, state}` objects). This confirms both that the weakening switch works as documented and that the claim card's binding table is accurate.
- `fixture_proof`: Verifies an upstream-supplied proof as is, recorded as `not_applicable` with that reason (RFC-0008 Q5).

See `harness/tests/fixtures/controls/fake-broken-controls.yaml` for an example containing both control types.

## 10. Fixture tests

Every adapter must include CPU-only tests in `systems/<name>/tests/` that exercise the entrypoint logic against stored fixtures, covering the verdict mapping for every documented exit code (INV-ADAPTER-9). Capture fixtures once on a GPU host following these rules:

- Store small text artifacts: upstream verifier stdout/stderr lines, exit codes, last output lines, and the structure of any JSON or log file parsed by the adapter.
- Never commit model weights, prompts beyond the workload's test prompts, or large proofs. Keep fixtures compact, as any file over 5 MiB fails gate G2 (SIZE-1).
- Redact sensitive information before committing: remove hostnames, IP addresses, usernames, and home paths (AGENTS.md rule 7), which gate G9 will reject.
- Document the upstream commit, image digest, and exact command used to generate each fixture alongside it.

`uv run pytest systems/<name>/tests` must pass on any laptop without a GPU; CI runs this as gate G1.

## 11. The adapter README

`systems/<name>/README.md` must document all seven items from [RFC-0005 §Adapter README requirements](../rfcs/0005-adapter-contract.md#adapter-readme-requirements), linking each to upstream documentation at the pinned commit. Copy the checklist below into your pull request description and note which README section satisfies each item:

```
- [ ] 1. Upstream tools each subcommand calls, and every argument passed
- [ ] 2. Verdict mapping table
- [ ] 3. How commitment_id, verifier_files and prover_files map onto upstream artefacts
- [ ] 4. The values under `proofs` in system.yaml, and why
- [ ] 5. Toolchain versions, and why they match upstream
- [ ] 6. Upstream CPU binding advice, and how the harness binding satisfies it
- [ ] 7. Known deviations from upstream's own measuring setup
```

For run instructions, follow the host prerequisites, GPU-host checks, and campaign workflow in [`docs/runbooks/gpu-run.md`](../docs/runbooks/gpu-run.md), adding only details specific to your adapter (such as its smallest workload, setup time, and resource requirements).

Your claim card must reflect what upstream documentation explicitly states at the pinned commit and record "not stated" wherever documentation is silent ([RFC-0002 §Rules](../rfcs/0002-claim-card.md#rules), AGENTS.md rule 9).

## Walkthrough: `systems/fake`

The `fake` system implements the entire adapter contract on CPU using a keyed hash in place of a real proof system. Reading its files alongside the sections above is the quickest way to see how the contract fits together:

| File | What it shows |
|---|---|
| [`fake/system.yaml`](fake/system.yaml) | A minimal manifest: `kind: test`, one workload, `proofs` settings, `forbidden_flags`, and short `timeouts_s`. |
| [`fake/entrypoint`](fake/entrypoint) | All five subcommands: `prove` releases proofs atomically via `.tmp-<id>`, logs to `/io/commands.jsonl`, and rejects forbidden flags outside control jobs; `verify` maps outcomes onto the four verdicts. |
| [`fake/Dockerfile`](fake/Dockerfile) | Digest-pinned base image, upstream commit passed as a build arg, and `USER 10001`. |
| [`fake/policy-allow.txt`](fake/policy-allow.txt) | The single source line mentioning a forbidden flag, paired with its guard. |
| [`fake/tests/test_fake.py`](fake/tests/test_fake.py) | CPU unit tests covering the entrypoint. |
| [`fake/README.md`](fake/README.md) | Subcommand mapping table and rationale for `proofs` settings. |

Because `fake` downloads nothing at build time, its Dockerfile illustrates rule B1 but not the `fetch` stage required by B2 through B5. Its proofs do not attest to any real model computation.

To run it locally without Docker, execute `uv run iproofs run --system fake --workload fake-tiny-ci --profile ci-cpu --repetitions 1 --results "$(mktemp -d)" --in-process`, which invokes the entrypoint in-process and writes results outside the repository. With Docker, `make e2e` builds the image and runs every step inside a hardened container, including the negative-control suite (gate G10). Run the same end-to-end check for your adapter on a GPU host before opening a pull request. See [`fake-broken`](fake-broken/README.md) for an example of what the control suite reports when a verifier accepts every proof.
