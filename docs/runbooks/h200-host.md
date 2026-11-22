# H200 host

This runbook documents the v0.1 bring-up of a bare-metal NVIDIA H200 node in Docker mode for the v0.1 workloads `sash-l31-8b-c1024` and `fp-maverick-w1024-b1`. Note that v1.0 runs instead used hosted containers on Hugging Face Jobs (each `manifest.json` records `machine.container.execution: hosted`); for that workflow, see [`gpu-run.md` §Hosted execution](gpu-run.md#hosted-execution-prover-h100-hosted-prover-h200-hosted) and [`hf-jobs.md`](hf-jobs.md).

Use this guide to provision a bare-metal H200 node for the v0.1 reference profile `prover-h200` ([RFC-0006 §H200 profiles](../../rfcs/0006-reference-hardware-and-cost.md#h200-profiles)) in Docker mode and execute the initial verification runs. The v0.1 node runs on Lucid Computing's research cluster, while pre-bring-up development runs go to Hugging Face Jobs on `prover-h200-hosted` ([`hf-jobs.md`](hf-jobs.md)). This page covers day one: provider requirements, the host probe, calibration self-test, container images, model weights, and the first two runs. For the full GPU-host test suite and campaign procedure, see [`gpu-run.md`](gpu-run.md); for adapter-specific details, see [`systems/sash/README.md`](../../systems/sash/README.md) and [`systems/flashprove/README.md`](../../systems/flashprove/README.md).

## What to ask the provider for

Every requirement below traces back to `prover-h200` in [`reference/v0.1.yaml`](../../reference/v0.1.yaml), a v0.1 system's documented needs, or how the harness binds resources. The host probe in step 1 verifies every item it can inspect.

| Item | Need | Why |
|---|---|---|
| Access | root (`sudo`) on the node | the harness invokes Docker, starts transient systemd scopes, and reads their cgroup counters ([gpu-run.md §systemd and cgroup v2](gpu-run.md#systemd-and-cgroup-v2-rfc-0011-cgroup-accounting)) |
| OS | Ubuntu 24.04, kernel 5.19 or later | `os`, `kernel_min`; kernel 5.19 exposes `memory.peak` |
| cgroup and init | cgroup v2 unified hierarchy, systemd as init | required for per-step slices (RFC-0011) |
| Docker | Docker Engine 25.0 or later with the systemd cgroup driver | `container_runtime`; adapters execute via `docker run` (RFC-0005) |
| NVIDIA Container Toolkit | 1.17 or later, configured for Docker (`nvidia-ctk runtime configure --runtime=docker`) | required for `--gpus device=<index>` |
| GPU | one H200 SXM 141 GB dedicated for the campaign, with no other compute processes running | `gpu`; any foreign process on the bound GPU fails the job (`PC-GPU-BUSY`) |
| Confidential Computing | CC mode disabled on that GPU for every prover run and kept off throughout the campaign | §H200 profiles; CC is enabled by default on the cluster (Q4) |
| CPUs | at least 24 logical CPUs on the GPU's NUMA node, at least 32 total, idle | `cpu`; the prover cpuset must sit on the GPU's NUMA node (§CPU and memory selection) |
| Memory | at least 330 GiB available | `host_memory_gib_min`; FlashProve's `run.sh` refuses to start `commit` with less than 330 GB available (external, reported, FlashProve README §Machine needs) |
| Disk | local NVMe with at least 500 GiB free for the work directory (results, `IPROOFS_CACHE`, and Docker's data root) | `disk`; see the disk note below |
| Driver | installed driver held constant for the campaign, reporting CUDA 13.2 or later | R3 and Q3: the driver pin is read from this host; FlashProve's image requires CUDA 13.2 Update 2 |
| Network | outbound HTTPS to `github.com`, `ghcr.io`, `huggingface.co`, and PyPI | repository clone, image pulls, weights, and `uv sync` |
| Kernel calls | no sandbox layer between jobs and the host kernel | FlashProve's `cp_commit` and `cp_prove` exit at startup without `madvise(MADV_WIPEONFORK)` and CPU SHA extensions (FlashProve README §Machine needs; gVisor rejected this syscall, #68) |

Request exclusive access to the entire node during measured runs rather than a single GPU slice: co-tenants share memory bandwidth, PCIe links, and CPUs on the GPU's NUMA node in ways the samplers cannot observe.

**Disk note:** FlashProve's weights total 232.1 GB, and `commit` requires an extra 10 GB plus 1 GB for `prove` (external, reported, FlashProve README §Machine needs). The adapter clones the five weight files into the job's `io` directory using `FICLONE`, falling back to a full file copy when the filesystem does not support reflinks (FlashProve README §What `commit` needs). On ext4, each FlashProve job therefore consumes a second full copy of the weights alongside the cache. Ask whether the work directory can be formatted as XFS with `reflink=1` or btrfs; otherwise budget disk space for the copy and run only one FlashProve job at a time.

## 1. Probe the host

Before installing any packages, clone the repository on the node and run the host probe:

```sh
export WORK=<a directory on the local NVMe>
git clone https://github.com/ai-verification-observatory/inference-proofs "$WORK/inference-proofs"
cd "$WORK/inference-proofs"
sudo python3 docs/runbooks/host-probe.py --work "$WORK" > "$WORK/probe.json"
```

[`host-probe.py`](host-probe.py) depends only on the Python 3 standard library. It writes a single JSON object to stdout and a line-by-line status summary to stderr (`PASS`, `FAIL`, `UNKNOWN`, `RECORD` for the unpinned driver, `LOGIN` for images requiring `docker login`, `INFO` for the suggested GPU, and `N/A` for inapplicable rows). Rows tagged `[flashprove]` check FlashProve-specific needs (CUDA 13.2, SHA extensions, `madvise(MADV_WIPEONFORK)`, and 330 GB available for `commit`); the rest check `prover-h200` requirements. In the JSON output, `failed` lists profile failures and `failed_flashprove` lists FlashProve failures; the script exits 1 only when `failed` is non-empty. Run it as root so it can query Docker. It inspects GPUs, CC mode, CPU and NUMA topology, memory, work directory free space and device type, OS, kernel, cgroups, systemd, Docker, the container toolkit, `madvise(MADV_WIPEONFORK)`, and anonymous pull access to each pinned image on `ghcr.io`. It emits no host names, addresses, serials, user names, or paths.

- **Any `FAIL` in either list stops bring-up:** Send the failing rows to the provider. Never work around a host failure with a weakening flag (AGENTS.md rule 4).
- **`cc_mode_off` must pass:** An `UNKNOWN` result means `nvidia-smi conf-compute` did not answer. Confirm with the provider that CC mode is disabled before running any campaign job (RFC-0006 Q4).
- **`suggested_gpu_index`:** Identifies the idle H200 with the most CPUs on its NUMA node. Pass this value to `--gpu` below.
- **`driver` (`RECORD`):** Note this version string so you can pin it in step 3.

Keep `probe.json` on the node, and copy its `requirements` block into the campaign log in step 6.

## 2. Install the harness

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh     # if uv is missing
export UV_CACHE_DIR="$WORK/uv-cache" IPROOFS_CACHE="$WORK/cache"
uv sync --frozen --extra gpu --extra fetch --extra prompts   # NVML, fetch-model, tokenizers
uv run iproofs --version
```

Check out the exact harness commit chosen for the campaign and stay on it for every run. Also make sure Docker's data root lives on the local NVMe (`docker info --format '{{.DockerRootDir}}'`; the probe reports its available space under `docker_root`).

## 3. Self-test and the driver pin

```sh
IMG=$(docker build -q --build-arg IPROOFS_FAKE_UPSTREAM=64168df9fd0706dfd955b6795fa6f535872dff78 \
      -f systems/fake/Dockerfile systems)            # the commit in systems/fake/system.yaml
export GPU=<suggested_gpu_index>
sudo -E .venv/bin/iproofs machine-record --selftest --gpu "$GPU" --probe-image "$IMG" \
     --provider "Lucid Computing" > "$WORK/selftest.json"
```

The calibration self-test (RFC-0011, GH-SELFTEST in [gpu-run.md](gpu-run.md#gpu-host-tests)) saves its output to `results/.selftest.json`, which subsequent runs copy into their manifests. Until `prover-h200` has a pinned driver, every H200 host will fail `PC-DRIVER`, though the self-test itself must still pass.

To pin the driver (RFC-0006 Q3), read `gpu.driver_version` and `gpu.cuda_driver_api` from the self-test record and open a pull request setting `profiles.prover-h200.driver` in `reference/v0.1.yaml` (along with `PROFILE["driver"]` in `host-probe.py`, which unit tests keep in sync with the reference file). Any run executed before that pull request merges counts as a development run (step 6).

## 4. Pull the pinned images

Each adapter image is pinned as `<repository>@<digest>` in `systems/<name>/system.yaml`. On 2026-11-08, `ghcr.io` rejected anonymous pull tokens for `ai-verification-observatory/sash` and `ai-verification-observatory/flashprove`, indicating those packages were not public; check the probe's `pull_*` rows to see if that is still true. Either have a maintainer make the packages public, or log in temporarily with a personal GitHub token carrying `read:packages`:

```sh
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github user> --password-stdin   # only if needed
for s in sash flashprove ref-serve ref-recompute; do
  repo=$(sed -n 's/^ *repository: *"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' systems/$s/system.yaml)
  digest=$(sed -n 's/^ *digest: *"\{0,1\}\(sha256:[0-9a-f]*\)"\{0,1\}$/\1/p' systems/$s/system.yaml)
  docker pull "$repo@$digest"
done
docker logout ghcr.io
```

Always run `docker logout` immediately afterward so no credentials linger on a shared node, and never save tokens inside the checkout.

## 5. Fetch the weights

```sh
uv run iproofs fetch-model sash-l31-8b-c1024
uv run iproofs fetch-model fp-maverick-w1024-b1      # b24 uses the same files and model digest
```

Both models are ungated (`licence.gated: false` in the workload files), so no `HF_TOKEN` is required. `fetch-model` downloads each workload's exact file list at its pinned revision into `$IPROOFS_CACHE/models/<model digest>/`, verifies every file sha256 and the overall model digest, and sets the directory read-only (RFC-0014). SASH's model consists of four safetensors files plus the tokenizer (file sizes are in `workloads/sash-l31-8b-c1024.yaml` under `bytes`); FlashProve's model consists of five GGUF files totaling 232.1 GB (external, reported, FlashProve README).

## 6. The first runs, in order

Until the driver pin merges, every run on this host records `harness.nonconforming: true` in its manifest (`--allow-nonconforming` is accepted as a no-op). Store development runs outside the repository checkout, using their own self-test record:

```sh
export DEV="$WORK/dev-results"
sudo -E .venv/bin/iproofs machine-record --selftest --gpu "$GPU" --probe-image "$IMG" \
     --provider "Lucid Computing" --results "$DEV" > /dev/null
```

1. **SASH, `sash-l31-8b-c1024`, one repetition.**

   ```sh
   sudo -E .venv/bin/iproofs run --system sash --workload sash-l31-8b-c1024 --profile prover-h200 \
        --gpu "$GPU" --provider "Lucid Computing" --repetitions 1 --allow-nonconforming --results "$DEV"
   ```

   Expect this run to take several hours. Upstream does not report timing for the 1,024 + 64 shape (SASH README §Expected run times). On a hosted H100 container (`prover-h100-hosted`), one run of this workload took 6,370 s for `commit` and 5,728 s for `prove` between step events before hitting that day's 3,600 s `verify` timeout (measured, tier reported, n = 1, `results/v0.1/sash/2026-11-05-sash-sash-l31-8b-c1024-prover-h100-hosted-1`). In a separate development call on an H100, `boundary-grid --verify` on a single grid took 3,381 s at roughly 3.9 CPUs (n = 1, not a recorded run; `systems/sash/system.yaml`). The harness also measures single-threaded verification (`verify.single_thread`), and the `verify` timeout is now 21,600 s. Issue #142 estimates roughly 7 h for a self-tested H100 job, and no H200 measurement exists yet. Note that `prove` also compiles CUDA kernels for the plan's shapes with the GPU visible (SASH README §Backend).

2. **FlashProve, `fp-maverick-w1024-b1`, one repetition.**

   ```sh
   sudo -E .venv/bin/iproofs run --system flashprove --workload fp-maverick-w1024-b1 --profile prover-h200 \
        --gpu "$GPU" --provider "Lucid Computing" --repetitions 1 --allow-nonconforming --results "$DEV"
   ```

   Before invoking `cp_commit`, the adapter checksums the weights ("5 to 6 minutes" upstream) and fits scales on the GPU (127 s upstream), followed by roughly 39 minutes for committing (all external, reported, single H100, FlashProve README). On a hosted H100 container (`prover-h100-hosted`), three b1 runs recorded `prove.session` between 318.3 and 376.7 s (measured, tier reported, n = 3; pull request #297). `commit` requires 330 GB of available memory and peaked at 299.6 GB upstream (external, reported).

   **RISK (RFC-0006 §H200 profiles):** The adapter compares `KL.bin` (fitted in float32 on the GPU) against upstream's reference digest, and upstream notes that "its rounding can differ between GPU models, drivers and torch's CUDA libraries". If the job fails at this check on the H200, treat it as a failed run: preserve the exit code and trailing log lines, open an issue, and do not modify either the adapter or the prover (AGENTS.md rules 1 and 5).

3. **Full campaign (after the driver pin merges):** Execute the GPU-host tests and campaign steps from [gpu-run.md](gpu-run.md) using `--profile prover-h200 --gpu "$GPU" --provider "Lucid Computing"` and the default `--results results`. Rerun the calibration self-test into `results/` first. For scheduling reference, a single b24 run on the hosted H100 container took 1,996.6 s for `commit` and 1,200.2 s for `prove.session` (measured, tier reported, n = 1; pull request #297).

Before starting each campaign, rerun the host probe and paste its `requirements` block (including `cc_mode_off`) into the campaign log, since the machine record schema has no Confidential Computing field (RFC-0006 Q4).

## Where run directories go

| Run | `--results` | Enters the repository |
|---|---|---|
| development (before the driver pin, or on a host failing any check) | `$WORK/dev-results`, outside the checkout | only via a results pull request that explicitly names it |
| campaign (conforming, self-tested) | `results` (default), from the checkout root | yes, via one results pull request per campaign ([gpu-run.md §Campaign procedure](gpu-run.md#campaign-procedure)) |

`results/` is strictly append-only (RFC-0009, APP-1): never edit or delete a merged run directory, and keep every failed repetition with its exit code and trailing log lines (AGENTS.md rule 5). Proof bytes stay out of git, and `--keep-io` directories are git-ignored.

## What never to commit or post

- **Host and account identifiers:** Never post or commit host names, IP addresses, MAC addresses, cluster/partition/queue names, job or allocation IDs, account or user names, SSH aliases, or absolute home paths (AGENTS.md rule 7; see RFC-0006 §Machine record for the full exclusion list). The machine record in each manifest is the host's only description, with `--provider "Lucid Computing"` as the declared provider.
- **Credentials:** `HF_TOKEN` and `ghcr.io` tokens come strictly from environment variables, are never written to disk, and are never passed into containers.
- **Pre-publish checks:** Review probe and self-test output carefully before pasting it into an issue or pull request, and run `uv run iproofs validate` on the tree so gate G9 catches any disallowed identifiers (RFC-0013).
- **Large or temporary artifacts:** Never commit model weights, proof bytes, or development run directories.
