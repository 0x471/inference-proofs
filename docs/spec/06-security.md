# 06. Security

This section defines the threat model for the benchmark infrastructure itself: the harness, system adapters, results repository, and static website. It does not evaluate the cryptographic security of any measured prover; those statements belong in claim cards and negative-control outcomes (PRD §5: the benchmark does not certify security). Normative controls live in [RFC-0005](../../rfcs/0005-adapter-contract.md), [RFC-0008](../../rfcs/0008-negative-controls.md), [RFC-0013](../../rfcs/0013-validation-and-ci.md), and [RFC-0014](../../rfcs/0014-provenance-and-integrity.md).

## Assets

| Asset | Why it matters |
|---|---|
| A1 Integrity of published numbers | Measurements are the benchmark's core output; an inaccurate figure with valid labels misleads relying parties |
| A2 Integrity of verdicts and control outcomes | Reporting that a verifier rejects tampering when it does not creates a false security impression |
| A3 Commitment provenance | If a verifier checks against a commitment supplied by the prover rather than the harness, acceptance proves nothing (AGENTS.md rule 6) |
| A4 Runner secrets | `HF_TOKEN`, container registry credentials, provider tokens, and SSH keys on the runner host |
| A5 Runner privacy | Host identifiers and personal details must never appear in published records (AGENTS.md rule 7) |
| A6 Undisclosed weaknesses | A negative control unexpectedly accepted by a verifier represents an active vulnerability until upstream can investigate and respond |
| A7 Impartiality | Both the reality and the public confidence that no single party controls benchmark results |

## Adversaries

| Id | Adversary | Goal | Capabilities assumed |
|---|---|---|---|
| T1 | System team gaming its numbers | Inflate throughput, shrink proofs, or pass more negative controls | Authors or reviews its adapter, controls upstream code at the pinned commit, and knows the benchmark workloads |
| T2 | Malicious or careless adapter | Escape container isolation, read host secrets, exfiltrate data, or forge verdicts | Executes arbitrary code inside the adapter container |
| T3 | Supply chain attacker | Substitute code, weights, or dependencies | Compromises an upstream repository, container registry, model host, or package dependency |
| T4 | Fabricating runner | Publish plausible numbers that were never actually measured | Submits forged run directories via pull request |
| T5 | Contributor weakening the methodology | Slip a weakened prover configuration in as a measured row, or alter rules without an RFC | Opens pull requests |
| T6 | Reader of published logs | Extract host identifiers, network topology, or leaked credentials | Inspects all public repository files and site artifacts |

## Trust boundaries

1. **Runner host.** Trusted by the person or organisation operating it. The harness executes here with the runner's privileges and reads `HF_TOKEN` from its environment. Other processes on the host are not assumed absent; before each job, the harness checks whether another compute process occupies the bound GPU.
2. **Adapter container.** Untrusted. The container receives only `/io` (job I/O, read-write), `/models` (read-only during prover steps only), and the harness-stored commitment files (read-only). It has no network access, no injected secrets, and no other host mounts.
3. **Upstream code inside the container.** Untrusted for the same reasons, pinned to a full commit hash and identified by image digest.
4. **Results repository.** All updates arrive via pull requests guarded by CI gates and human review; once merged, `results/` is append-only.
5. **Static site.** Built purely from repository files and executes no submission-supplied code.

## Mechanisms

### Container hardening (T2)

Every adapter container runs with `--network none`, a `--read-only` root filesystem, `--cap-drop ALL`, `--security-opt no-new-privileges`, a non-root user defined in the Dockerfile, `--pids-limit 4096`, the profile's `--cpuset-cpus` and `--cpuset-mems`, a 32 GiB memory cap for `verify` steps, and `--gpus device=<index>` granted only to prover steps (see RFC-0005 for the exact argument list). Writable scratch space is limited to a profile-sized `--tmpfs /tmp` (RFC-0005). Containers never receive the Docker socket, `--privileged`, host PID or IPC namespaces, or any device nodes other than the bound GPU.

### Untrusted input handling (T2, T1)

The harness treats all files written by an adapter as untrusted input:

- `out.json` is capped at 128 MiB (large enough for a Level 1 serving ladder returning roughly 8,200 replies of 512 token IDs), parsed with Python's stdlib JSON parser, and validated against `adapter-out/1` before any field is inspected. Malformed or schema-invalid output raises `ErrorKind.adapter`.
- Every path referenced in `out.json` (proof parts, verifier files, prover files, logs) is resolved on the host relative to the step's `/io` directory. If `os.path.realpath` escapes `/io`, or if the target is a symlink, device, FIFO, or non-regular file, the harness rejects it with `ErrorKind.adapter`.
- Proof IDs must conform to the single-component RFC-0012 identifier pattern.
- Proof part counts and sizes are bounded by `max_proof_parts` and `max_proof_bytes` in `system.yaml`. Exceeding either limit records `ErrorKind.adapter` rather than silently truncating.
- These checks are verified in `harness/tests/unit/test_path_safety.py` (`test_path_escape_rejected`, `test_unlisted_proof_is_adapter_failure`, `test_listed_but_unreleased_is_adapter_failure`, along with part count, byte size, `out.json` cap, symlink, and non-regular file tests). Error messages report only container paths (`/io/...`), never host paths.
- Adapter stdout and stderr pass through bounded capture pipes, are truncated to RFC-0009 caps before touching disk, and are redacted before writing.
- Any adapter string rendered on the website is HTML-escaped automatically by the template engine (autoescape enabled).

### Commitment provenance (A3)

After `commit` completes, the harness copies the verifier and prover files into a harness-controlled directory, hashes them, and constructs every `verify` step's `/io` exclusively from that store ([RFC-0014 §The commitment record](../../rfcs/0014-provenance-and-integrity.md#the-commitment-record)). Files emitted by `prove` never overwrite or supply commitment inputs to `verify`. In [`harness/src/iproofs/runner.py`](../../harness/src/iproofs/runner.py), `Runner._commit`, `Runner._recorded`, and `Runner._commitment_echo` maintain `<job tmp>/commitment/` and re-verify every file digest before each step that reads it. `prove` receives the recorded prover files mounted read-only at their `/io/state/` paths, while every `verify` receives the verifier files mounted read-only at `/io/verifier`. If `prove` echoes `commitment_id` or emits a file matching a recorded verifier file, the harness emits `policy.warning` and adds a warning to `run.json`. This behavior is covered by `harness/tests/unit/test_commitment.py` and `test_commitment_from_record` in Gate G10.

### Gaming resistance (T1)

| Gaming route | Response |
|---|---|
| Precomputing proofs for fixed public prompts | Generate a fresh 64-bit prompt seed from `os.urandom` for every measured job and record it in the manifest (RFC-0003) |
| Verifier that always accepts, or adapter mapping every exit code to `accept` | Shared controls C1 to C8 expect rejection, and CI runs `fake-broken` to confirm the control suite catches it (RFC-0013 G10) |
| Reporting internal timings that exclude setup or proving work | The harness times calls externally; adapter-reported timings are explicitly labelled `source.kind: adapter` |
| Enabling a weakening flag during a measured run | Declare `forbidden_flags` in `system.yaml`, record full upstream argv, and enforce Gate G6 `POL-1` |
| Reusing a cached commitment to skip commit time | Run `commit` inside every job and hash all commitment files per job |
| Cherry-picking favourable repetitions | Record and publish every repetition, including failures (AGENTS.md rule 5) |

### Supply chain (T3)

Image builds follow the pinning and isolation rules B1 to B7 in [RFC-0014](../../rfcs/0014-provenance-and-integrity.md#adapter-image-build): base images and GitHub Actions are pinned by digest or full commit hash, lockfiles include hashes, builds run offline after a verified fetch stage, model weights are hashed per file on download and before each job, and source archives are retained with each release.

### Fabricating runner (T4)

v0.1 provides no cryptographic defence against a runner submitting a fabricated but internally consistent run directory. Accordingly, every run is labelled `reported` ([RFC-0007](../../rfcs/0007-evidence-tiers-and-reproduction.md)), and run files are not cryptographically signed ([RFC-0014 Q1](../../rfcs/0014-provenance-and-integrity.md#decisions)).

### Methodology weakening (T5)

CI enforces all validation gates with no bypass mechanism (RFC-0013), and Gate G6 `POL-1` checks every recorded upstream command line against `forbidden_flags`.

## Secrets handling (A4)

Both the log redactor (`iproofs.log.redact`) and the CI secrets scanner (Gate G9) share a single compiled pattern registry in `iproofs.log.patterns`.

- `HF_TOKEN` is the only secret the harness reads, pulled from the environment solely to fetch gated model weights. It is passed only to the download call inside the harness process, never placed in argv, never forwarded into containers, and never written to disk.
- Container registry credentials for publishing release images belong to maintainers' build pipelines, not to the harness.
- Pull request CI workflows run with `contents: read` and have access to no secrets.
- The redactor strips values of environment variables matching `(?i)(token|key|secret|password|credential)` wherever they appear in logs, along with all Gate G9 patterns. Gate G9 then scans every committed file with the same rules so any leak fails CI before merge.
- Gate G9 pattern rules in `iproofs.log.patterns` (RFC-0013 §G9): `SEC-1` Hugging Face tokens, `SEC-2` GitHub tokens, `SEC-3` AWS access key IDs, `SEC-4` private key headers, `SEC-5` IPv4 literals and `SEC-6` IPv6 literals (excluding loopback), `SEC-7` MAC addresses, `SEC-8` GPU UUIDs, `SEC-9` SSH config fragments, `SEC-10` absolute home paths, and `SEC-11` secret-like assignments. Every G9 failure reports the file, line number, and rule ID.
- During full-repository scans, Gate G9 skips `harness/tests/fixtures/secrets/` (which holds one synthetic bad sample per rule) and `schema/*/examples/invalid/`, though it still scans them when explicitly targeted (`uv run iproofs validate harness/tests/fixtures/secrets`). Tests load secret-shaped samples exclusively from those fixtures so no other files require exceptions.

## Privacy and identifier exclusion (A5, T6)

The machine record includes only the hardware and software fields enumerated in [RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md): GPU model, count, memory, driver version, CUDA runtime, CPU model, sockets, cores, logical CPUs, the GPU's NUMA node, bound CPU set, SMT state, total host memory, disk type and free space, kernel version, OS release, container runtime and version, NVIDIA Container Toolkit version, and the runner-declared provider name. It excludes hostnames, IP and MAC addresses, GPU UUIDs and serial numbers, usernames, SSH configs, cloud instance IDs, and absolute home paths.

Rather than filtering a raw system dump, `iproofs.provenance.Host` builds the machine record from a strict allowlist of probes (and `manifest/1` sets `additionalProperties: false` across the `machine` schema, INV-MR-1), preventing new probes from leaking fields accidentally. Every string passes through the redactor, and the harness collects the record again after the final step so any drift in driver, kernel, or prover CPU set triggers an `environment` failure (INV-MR-2). These guarantees are tested in [`test_machine_record.py`](../../harness/tests/unit/test_machine_record.py) (TC-MR-FIELDS, TC-MR-NO-IDENTIFIERS, TC-MR-DRIFT) against fixture host files in `harness/tests/fixtures/host/`. The manifest's `runner` block (`handle`, `organisation`, `affiliated_systems`) records optional attribution supplied by the runner; giving only an organisation name is allowed.

## Disclosure

### Accepted controls (A6)

If a real system unexpectedly accepts a negative control whose expected outcomes exclude `accept` ([RFC-0008](../../rfcs/0008-negative-controls.md)):

1. Do not open a public pull request with that run. Report the finding privately to the system's maintainers via their security policy channel and to the benchmark maintainers via `SECURITY.md`.
2. Respect the system's own disclosure embargo; if none is specified, observe a 90-day embargo from the initial report or publish earlier once upstream releases a fix or advisory.
3. Once the embargo ends, publish the full run with the unexpected outcome shown in the row (RFC-0008 §Reporting).
4. Never discard the run or soften the recorded verdict.

### Harness vulnerabilities

`SECURITY.md` lists a private reporting channel for vulnerabilities in the harness, fake test systems, CI workflows, or site generator. Maintainers aim to acknowledge reports within 7 days before releasing a fix and advisory. Any bug that could have affected published numbers is documented in the next release report under "what failed", naming all affected runs.

## Residual risks

- Fabricated run directories cannot be detected while external reproduction remains out of scope (T4).
- Container escapes via GPU drivers or container runtimes sit outside the harness's control; runners should use dedicated or freshly provisioned hosts running the pinned driver and runtime versions.
- Upstream code inside a container could behave differently if it detects it is being benchmarked (for example, skipping work outside observed paths). External timing and negative controls reduce this risk but cannot eliminate it completely.
- Both the language lint and the log redactor rely on pattern matching and may miss paraphrases or novel secret formats.
