# GPU run

This runbook covers running measured jobs on a `prover-h200` host, the v0.1 reference profile ([RFC-0006 §H200 profiles](../../rfcs/0006-reference-hardware-and-cost.md#h200-profiles)): host prerequisites, the GPU-host test suite required before every campaign, and the campaign workflow itself. For a `prover-h100` host, follow the same steps with `--profile prover-h100 --gpu $IPROOFS_GPU`.

For initial bring-up of a bare-metal H200 node (from provider specs through the first two runs), see [`h200-host.md`](h200-host.md) and the probe script [`host-probe.py`](host-probe.py). For development runs on Hugging Face Jobs (`prover-h200-hosted`), see [`hf-jobs.md`](hf-jobs.md). GPU jobs do not run as CI gates ([RFC-0013 §What runs on GPU hosts instead](../../rfcs/0013-validation-and-ci.md#what-runs-on-gpu-hosts-instead)); instead, their run records are submitted by pull request, where CI gates validate them. Adapter-specific instructions live in each adapter's README ([`systems/README.md`](../../systems/README.md)).

## Host prerequisites

Minimum software versions come from the release's reference file, such as [`reference/v0.1.yaml`](../../reference/v0.1.yaml) (`kernel_min`, `container_runtime`, `driver`):

| Item | Requirement | Check |
|---|---|---|
| Linux kernel | at least 5.19 | `uname -r` |
| cgroup | v2, unified hierarchy at `/sys/fs/cgroup` | `stat -fc %T /sys/fs/cgroup` prints `cgroup2fs` |
| Docker Engine | at least 25.0, `cgroup_driver: systemd` | `docker info --format '{{.CgroupDriver}} {{.CgroupVersion}}'` prints `systemd 2` |
| NVIDIA Container Toolkit | at least 1.17 | `nvidia-ctk --version` |
| NVIDIA driver | matches the `driver` field in `reference/<release>.yaml` (`unpinned` until a host of the profile is read); `nvidia-smi` reports CUDA 13.2 or later (FlashProve's image; SASH requires 12.9) | `nvidia-smi --query-gpu=driver_version --format=csv,noheader` |
| NVIDIA Confidential Computing | disabled on the bound GPU (H200 profiles, RFC-0006 Q4) | `nvidia-smi conf-compute -f` prints `CC status: OFF` |
| Harness | checkout at the release's harness commit, `uv sync --frozen --extra gpu --extra fetch --extra prompts` | `uv run iproofs --version` |

`iproofs run` checks all of these items automatically during conformance before any timed step. It logs every failure (`harness.nonconforming` in the manifest and a warning in `run.json`) without aborting the run, so treat this table as a setup guide rather than a replacement for conformance checks. For gated models, accept the licence on your own account and provide `HF_TOKEN` only through the environment (see below).

### NVML (RFC-0011 §GPU sampler)

- Install both the NVIDIA driver and the harness `[gpu]` extra (`uv sync --frozen --extra gpu`), which pulls in `nvidia-ml-py`. Without it, any GPU profile fails with kind `environment`; null readers are restricted to non-GPU profiles.
- Keep the bound GPU free of other compute processes. If another compute process is found before `info` or a GPU step, the job fails with `PC-GPU-BUSY`; if one appears after a GPU step, that step's GPU metrics are marked `degraded: true` and logged as `gpu.foreign_process`.

### systemd and cgroup v2 (RFC-0011 §Cgroup accounting)

- The host must run cgroup v2 (unified hierarchy at `/sys/fs/cgroup`) with Docker configured to use `cgroup_driver: systemd` (`docker info --format '{{.CgroupDriver}} {{.CgroupVersion}}'` prints `systemd 2`).
- Kernel 5.19 or newer is required so every slice exposes `memory.peak` (G-7). Earlier kernels fail conformance before any timed step.
- `systemd-run` and `systemctl` must be on `PATH`. For each step, the harness starts a placeholder scope (`systemd-run --scope --slice=iproofs-<job_hash>-<step>.slice --unit=iproofs-<job_hash>-<step>-hold sleep infinity`), launches the container with `--cgroup-parent` pointing at that slice, reads the counters after exit, and stops the scope (G-1 to G-4).
- Run the harness as root, or as a user permitted to start transient systemd scopes and read `memory.peak`, `memory.stat`, `cpu.stat`, and `memory.events` on those slices.
- Any leftover `iproofs-*-hold.scope` units from a crashed runner are stopped before conformance and logged as `cgroup.stale_cleanup`.

## Hosted execution (`prover-h100-hosted`, `prover-h200-hosted`)

When a provider only rents GPUs as pre-started containers from a specified image, use that GPU's hosted profile ([RFC-0006 §Hosted execution](../../rfcs/0006-reference-hardware-and-cost.md#hosted-execution)). Note that `prover-h200-hosted` is a minimum floor: it binds 15 prover CPUs instead of 24, and FlashProve needs more host memory than the profile minimum ([RFC-0006 §H200 profiles](../../rfcs/0006-reference-hardware-and-cost.md#h200-profiles)). For Hugging Face Jobs specifically (using [`hf-job.sh`](hf-job.sh)), see [`hf-jobs.md`](hf-jobs.md). Docker and systemd scope requirements do not apply in hosted mode, and the calibration self-test uses a hosted variant:

1. Start the container from the system's pinned image (`<repository>@<digest>` in `systems/<name>/system.yaml`) with the profile's GPU and at least 500 GiB of container disk. Before installing anything, verify the container with `python3 docs/runbooks/host-probe.py --profile prover-h200-hosted` (or check the equivalent items manually on an H100). Development builds also run by digest via `--image <id>`, and are never eligible for a release.
2. Inside the container, as root if the provider allows it (RFC-0006 Q6), clone the harness at the release's harness commit and run `uv sync --frozen --extra gpu --extra fetch --extra prompts` (the image's `python3` is sufficient). Point `IPROOFS_CACHE` at a directory on the container disk.
3. Run `uv run iproofs machine-record --hosted --gpu <index> --provider <name> --selftest` to execute the hosted calibration self-test (RFC-0011) and write it under `results/`. Later runs copy this record into their manifests, and runs without a passing self-test are ineligible for release. In the printed machine record, verify that `container.execution` is `hosted`, `cpu.cgroup_quota_cpus` and `memory.cgroup_limit_bytes` reflect the provider's actual limits, and `gpu.driver_version` matches the profile's `driver`.
4. Fetch weights with `uv run iproofs fetch-model <workload>`, then run `uv run iproofs run --system <name> --workload <workload> --profile <hosted profile> --hosted --gpu <index> --provider <name>`. On a dual-GPU host, bind the GPU whose NUMA node offers the most usable CPUs (`suggested_gpu_index` in the probe output). Always execute from the repository root with the default `--results results`, because `run.json` metric sources only resolve to `results/<release>/...` inside the checkout and CI gate G4 rejects external paths. Keep harness caches (`UV_CACHE_DIR`, `IPROOFS_CACHE`) outside `/tmp`, which is reserved for the adapter.

Check these points before renting a container or downloading weights:

- **Verify cgroup limits, not storefront specs.** `PC-CPU-QUOTA` checks the container's CPU quota (`/sys/fs/cgroup/cpu.max`, quota divided by period) against the profile's 24 CPUs, and `PC-MEM` checks `/sys/fs/cgroup/memory.max` against 330 GiB. Provider listings often differ from actual cgroup limits: during the v0.1 campaign, one provider set CPU quotas to roughly 96% of the listed vCPU count (26.0 listed yielded 24.96, while 24.0 listed yielded 23.04 and failed), and a machine advertised with 221 GiB of RAM had a 601 GiB cgroup limit. Inspect both cgroup files immediately on a new rental and release the host if either falls short.
- **One container per system.** Because the container itself is the adapter image, each system in a campaign requires its own rental. If pulling a private image, supply a short-lived read-only registry token, as providers retain rental credentials.
- **Copy each run directory off the host as soon as it finishes** (`results/<release>/<system>/<run-id>/`, excluding `results/.archive/`). Hosted containers are tied to a single machine; if that machine goes offline, local runs become unreachable until it recovers. Wait until the final repetition completes before uploading proof archives so network and disk traffic do not overlap with timed steps.

The hosted runner reads the image environment from PID 1 and strips provider-injected variables, so provider keys, ports, and addresses are never forwarded to the adapter. Even so, do not store credentials inside the container, since the provider's operator can inspect it.

## The calibration self-test (RFC-0011)

Run the calibration self-test before a host's first run of a release, before each campaign, after any driver, kernel, or Docker update, and whenever a run fails with `environment`:

```sh
docker build -q --build-arg IPROOFS_FAKE_UPSTREAM=<commit in systems/fake/system.yaml> -f systems/fake/Dockerfile systems
sudo .venv/bin/iproofs machine-record --selftest --gpu 0 --probe-image <the image ID printed above>
```

This runs ST-CLOCK, ST-NVML, ST-SAMPLER, and ST-JITTER (5 s on the bound GPU), plus ST-CGROUP, ST-WATCH, and ST-OOM using the fake image's `probe` subcommand inside a harness slice. It prints the machine record and check results as JSON, writes the results to `results/.selftest.json`, and exits 3 while naming every failed check if anything fails. Subsequent runs copy the saved self-test into their manifests; a run without a passing self-test from the same harness version is not eligible for a release.

## Model weights and `HF_TOKEN` (RFC-0014 §Model fetch and verification)

- Download weights once per host after running `uv sync --frozen --extra fetch`, using `uv run iproofs fetch-model <workload>`. Files are stored in `$IPROOFS_CACHE/models/<model digest>/` (`IPROOFS_CACHE` defaults to `~/.cache/iproofs`). The command fetches only the workload's listed files at the pinned revision, verifies every file's sha256 and the overall model digest, and marks the directory read-only.
- For gated models, accept the licence on your own account and export `HF_TOKEN` in the shell running the harness. The harness reads `HF_TOKEN` only from the environment and passes it only to the download call; it is never written to files, logs, or records, and never passed into containers.
- Before starting any timed step, every job rehashes the cached weights and records the duration as `integrity.model_rehash`. If any file has changed on disk, the job fails with `integrity` and moves the directory to `$IPROOFS_CACHE/quarantine/`. Investigate the cause before re-fetching.
- Weights are mounted read-only at `/models` during `commit` and `prove`, and are never mounted during `verify`.

## Prompt corpus cache (RFC-0014 §Corpus fetch)

Either the first job or an explicit `iproofs prompts build` downloads every text listed in `workloads/prompts/corpus.yaml` into `$IPROOFS_CACHE/corpus/<sha256>`. Any download whose sha256 mismatches the listing, or any cached file that has changed on disk, fails with `integrity` and is discarded. Prompts are always constructed from the verified cache after NFC, LF, and BOM normalization. Downloads retry three times, outside any timed scope.

## GPU-host tests

Execute every test below on the host in order before starting a campaign, and record each result in the campaign log (see next section). Stop the campaign if any test fails until the issue is fixed. Record failures with their exit code and trailing log lines (AGENTS.md rule 5); never retry a failure away. Because [`harness/tests/gpu/`](../../harness/tests/gpu/) skips tests when NVML is absent, CI and laptops report only skips.

After building the fake image (see the self-test section above), export these variables once per shell:

```sh
export IPROOFS_GPU=0                                 # the bound GPU index (the probe suggests one)
export IPROOFS_PROBE_IMAGE=<image ID of systems/fake>  # sha256:...
export IPROOFS_CUDA_PROBE_IMAGE=<image>@sha256:<digest>  # any pinned image with python3 and torch
```

| Test | Procedure | Pass criterion |
|---|---|---|
| GH-SELFTEST ([RFC-0011](../../rfcs/0011-measurement-and-sampling.md#testing-strategy)) | `sudo .venv/bin/iproofs machine-record --selftest --gpu $IPROOFS_GPU --probe-image $IPROOFS_PROBE_IMAGE > selftest.json` | exit 0; every check prints `pass` on stderr; `results/.selftest.json` is written |
| GH-MR-H200 ([RFC-0006](../../rfcs/0006-reference-hardware-and-cost.md#testing-strategy); GH-MR-H100 on a `prover-h100` host) | Run GH-SELFTEST, then `sudo -E .venv/bin/python -m pytest harness/tests/gpu/test_numa_binding.py`. The test binds according to `IPROOFS_PROFILE` (default `prover-h200`; set `IPROOFS_PROFILE=prover-h100` on an H100). Inside a hosted container after the hosted self-test, run `IPROOFS_PROFILE=prover-h200-hosted IPROOFS_GPU=<index> .venv/bin/python -m pytest harness/tests/gpu/test_numa_binding.py` to bind 15 prover CPUs from the container's CPU set | GH-SELFTEST passes; both tests pass (the record validates against `manifest/1` `$defs/machine` and identifies an H200, or an H100 on `prover-h100`) |
| NUMA binding (docs/spec/07) | Included in GH-MR-H200's `test_numa_binding.py` | prover cpuset lies on the GPU's NUMA node, uses distinct physical cores, and stays disjoint from the verifier sets |
| Sampler rate (docs/spec/07) | `uv run pytest harness/tests/gpu/test_nvml_sampler.py -k rate` | at least 10 Hz over 60 s; gaps exceeding 150 ms on at most 5% of samples; ST-JITTER passes |
| GH-NVML-PEAK | `uv run pytest harness/tests/gpu/test_nvml_sampler.py -k peak` | `memory_peak_mib` is at least 40,960 while a CUDA probe holds 40 GiB for 2 s |
| Cgroup reader (docs/spec/07) | `sudo -E .venv/bin/python -m pytest harness/tests/gpu/test_cgroup_reader.py -k known` | ST-CGROUP passes: both `memory.peak` and sampled `anon` are at least 256 MiB |
| GH-CGROUP-EXACT | `sudo -E .venv/bin/python -m pytest harness/tests/gpu/test_cgroup_reader.py -k exact` | slice `memory.peak` is at least 1 GiB after a probe allocates and touches 1 GiB and exits immediately |
| GH-OVERHEAD ([RFC-0011](../../rfcs/0011-measurement-and-sampling.md#measurement-overhead-budget), docs/spec/08 B-OVH-*) | `IPROOFS_GH_OVERHEAD=1 uv run pytest harness/tests/gpu/test_nvml_sampler.py -k overhead` (30 minutes) | sampler and release watcher CPU is at most 1% of one CPU; p99 lateness is at most 10 ms; resident memory is at most 256 MiB |
| Fake run | `sudo -E .venv/bin/iproofs run --system fake --workload fake-tiny-ci --profile prover-h200 --gpu $IPROOFS_GPU --image $IPROOFS_PROBE_IMAGE --control-suite` | exit 0; run directory passes `uv run iproofs validate <run dir>` |
| Adapter smoke job | Per adapter, run the shortest job on the smallest workload listed in its README with `--control-suite` | exit 0 and a valid run directory; every control outcome matches its expected verdict |
| GH-REF-SERVE-L31 ([RFC-0015](../../rfcs/0015-reference-rows.md#testing-strategy)) | `sudo -E .venv/bin/iproofs run --system ref-serve --workload sash-l31-8b-c1024 --profile prover-h200 --gpu $IPROOFS_GPU --repetitions 3` | three repetitions, schema-valid, `rate_prove.steady` non-null |
| GH-REF-RECOMPUTE-L31 | `sudo -E .venv/bin/iproofs run --system ref-recompute --workload sash-l31-8b-c1024 --profile prover-h200 --gpu $IPROOFS_GPU --prompts-from <a completed SASH run dir>` | completed; agreement block present |
| GH-REF-MAVERICK-ATTEMPT | `sudo -E .venv/bin/iproofs run --system ref-serve --workload fp-maverick-w1024-b1 --profile prover-h200 --gpu $IPROOFS_GPU` | either a valid row, or a recorded failure (`resource` or `adapter`) |

GH-OVERHEAD runs the 20 Hz sampler and the release watcher inside the test process for 30 minutes and measures that process directly. Because the container executes outside the harness process, this measurement bounds the harness's overhead for a single call. The reference-row tests require the reference systems and the adapter tests require the adapters; if a test cannot be run, log it as `not run` in the campaign log with the reason.

## Campaign procedure

1. Run the host probe ([`h200-host.md`](h200-host.md#1-probe-the-host)), verify the host prerequisites, and fetch model weights (`iproofs fetch-model WORKLOAD`) for every workload in the campaign.
   Next, once per workload per release and system, generate the perturbed commitment for controls C3 and P1: `sudo -E .venv/bin/iproofs controls --prepare-perturbed WORKLOAD --system S --profile prover-h200`. This writes `results/<release>/<system>/_controls/<workload>/` (commit this directory in the results pull request) and keeps the perturbed weights locally in `$IPROOFS_CACHE/perturbed/`.
2. Run the GPU-host tests above in order and start the campaign log.
3. Estimate total GPU time with `uv run iproofs release plan RELEASE` ([docs/spec/08](../spec/08-performance-budget.md#run-campaign-compute-budget)) and confirm it fits within budget.
4. Execute the campaign matrix. For each configuration, run `sudo -E .venv/bin/iproofs run --system S --workload W --profile prover-h200 --gpu $IPROOFS_GPU --repetitions N --control-suite` with N at least 3 (RFC-0004). Keep any failed job (exit 4) as recorded; rerun only as new repetitions and never delete the failed record.
5. Validate the entire results tree with `uv run iproofs validate results/`.
6. Open one pull request per campaign containing only the new run directories under `results/`, and paste the campaign log into the pull request description.

The harness also rechecks every proof's digest immediately before each verify call and each control mutation; if a proof changes on disk after release, the job fails with kind `integrity`.

Include the campaign log as a checklist in the results pull request description:

```
Release: v0.1   Harness commit: <full hash>   Host: prover-h200 (provider <name>)
| Test | Date (UTC) | Outcome | Evidence |
| host probe | 2026-11-20 | pass | requirements block of host-probe.py, cc_mode_off pass |
| GH-SELFTEST | 2026-11-20 | pass | results/.selftest.json copied into every manifest |
| GH-OVERHEAD | 2026-11-20 | fail, exit 1 | <last lines of the pytest output> |
| GH-REF-MAVERICK-ATTEMPT | | not run | <reason> |
```

Do not include host names, IP addresses, account names, or tokens (AGENTS.md rule 7); the machine record inside each manifest is the host's sole description.
