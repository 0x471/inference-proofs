# RFC-0006: Reference hardware and cost basis

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0004, RFC-0012

## Summary

This RFC defines the hardware profiles used to measure benchmark rows within each release, the exact machine metadata every run records, the deterministic algorithm for pinning jobs to CPUs and NUMA memory, the conformance checks applied to each host prior to execution, and the GPU pricing basis used to translate GPU-seconds into dollars. It also sets a strict boundary on machine records so they capture enough hardware detail to reproduce a run without leaking host or account identifiers.

## Motivation

A proving rate has little meaning unless you know what hardware produced it. Both initial v0.1 systems publish figures from a single NVIDIA H100 80 GB GPU, yet they differ markedly in host requirements: FlashProve binds 24 of a host's 96 CPUs, uses up to roughly 300 GB of host RAM, and refuses to start committing on its full-size route with less than 330 GB available, whereas SASH's manifest records only the GPU model and CUDA version (PRD §1; both external, reported, from upstream repositories at the RFC-0003 pins). Cloud GPU prices also fluctuate by provider and month. Pinning hardware profiles and a single price basis per release keeps rows comparable within that release (PRD G2, F5).

For v0.1, the reference GPU is the NVIDIA H200 141 GB (§H200 profiles). Because the H200 is a Hopper GPU with compute capability `sm_90` just like the H100, the pinned adapter images run on it without changes. The bare-metal research cluster slated for official runs (Lucid Computing, using Docker) has 5 H200s and 1 H100, and Hugging Face Jobs (used for development runs beforehand) offers H200 instances rather than H100s. The H100 profiles remain declared. Because AGENTS.md rule 7 forbids collecting any machine identifiers beyond what this RFC specifies, the machine record fields must be enumerated exhaustively.

## Goals

- Define all hardware profiles and the pricing basis for each release in a single file, `reference/<release>.yaml`, validated against `schema/reference/1.schema.json`.
- Record an exact, exhaustive set of hardware fields for every run while excluding all identifying host metadata.
- Assign CPU and NUMA memory bindings deterministically from host topology and record the chosen binding.
- Detect host conformance mismatches before any timed step executes, failing with kind `environment` where required.
- Compute all published cost figures solely from the release's asserted GPU price basis.

## Non-Goals

- Multi-GPU prover profiles or GPUs beyond H100 and H200 (neither v0.1 prover requires them; Q2). Multi-GPU serving profiles are covered under R6.
- Pricing CPU time, host RAM, disk storage, or network bandwidth (rule C5).
- Implementing runtime resource sampling (owned by RFC-0011; this RFC defines the static machine record and CPU/memory binding).

## Proposed Design

### Reference file

`reference/<release>.yaml`, authored YAML loaded per RFC-0012:

```yaml
schema: "reference/1"
release: "v0.1"
profiles:
  prover-h200:                  # the v0.1 reference (§H200 profiles); same host needs as prover-h100
    kind: prover
    gpu: {model: "NVIDIA H200", form_factor: "SXM", count: 1, memory_mib_min: 140000}
    cpu: {logical_cpus_on_gpu_numa_node: 24, logical_cpus_total_min: 32}
    host_memory_gib_min: 330
    disk: {type: "local NVMe", free_gib_min: 500}
    os: {id: "ubuntu", version_id: "24.04"}
    kernel_min: "5.19"
    driver: "<pinned NVIDIA driver version string>"
    container_runtime: {docker_engine_min: "25.0", nvidia_container_toolkit_min: "1.17", cgroup_driver: "systemd"}
    cost: "h200"                # its GPU is priced by costs.h200 (C7)
  prover-h200-hosted:           # §H200 profiles: a minimum spec for a hosted H200 container
    kind: prover
    gpu: {model: "NVIDIA H200", form_factor: "SXM", count: 1, memory_mib_min: 140000}
    cpu: {logical_cpus_on_gpu_numa_node: 15, logical_cpus_total_min: 23}
    host_memory_gib_min: 200
    disk: {type: "any", free_gib_min: 500}
    os: {id: "ubuntu", version_id: "24.04"}
    kernel_min: "5.19"
    driver: "<pinned NVIDIA driver version string>"
    container_runtime: {kind: "hosted", cgroup_version: "2"}
    cost: "h200"
  prover-h100:
    kind: prover
    gpu: {model: "NVIDIA H100 80GB HBM3", form_factor: "SXM", count: 1, memory_mib_min: 80000}
    cpu: {logical_cpus_on_gpu_numa_node: 24, logical_cpus_total_min: 32}
    host_memory_gib_min: 330
    disk: {type: "local NVMe", free_gib_min: 500}
    os: {id: "ubuntu", version_id: "24.04"}
    kernel_min: "5.19"
    driver: "<pinned NVIDIA driver version string>"
    container_runtime: {docker_engine_min: "25.0", nvidia_container_toolkit_min: "1.17", cgroup_driver: "systemd"}
  verifier-cpu:
    kind: verifier
    gpu: null
    cpu: {logical_cpus: 8}
    host_memory_gib: 32
    emulation: {allowed_on: ["prover-h200", "prover-h200-hosted", "prover-h100"]}
cost:
  price_per_gpu_hour_usd:
    value: 0.0                  # freeze refuses a release whose value is 0 (C6)
    unit: "USD/gpu_hour"
    scope: null
    grade: "asserted"
    tier: "reported"
    source: {kind: "reference_file", ref: "reference/v0.1.yaml#/cost"}
    null_reason: null
  basis: "median on-demand list price of the named providers on the named date"
  providers: ["<provider name>", "<provider name>", "<provider name>"]
  date: "YYYY-MM-DD"
  priced: ["gpu"]
  not_priced: ["cpu", "host_memory", "disk", "network"]
costs:                          # C7: one more basis per GPU model priced apart from `cost`
  h200: {price_per_gpu_hour_usd: {...}, basis: "...", providers: [...], date: "YYYY-MM-DD", readings: [...], priced: ["gpu"], not_priced: [...]}
```

Python view (`iproofs.model`):

```python
@dataclass(frozen=True, slots=True)
class GpuSpec:
    model: str
    form_factor: str
    count: int
    memory_mib_min: int

@dataclass(frozen=True, slots=True)
class ProverProfile:
    id: str
    gpu: GpuSpec
    logical_cpus_on_gpu_numa_node: int
    logical_cpus_total_min: int
    host_memory_gib_min: int
    disk_free_gib_min: int
    os_id: str
    os_version_id: str
    kernel_min: str
    driver: str
    docker_engine_min: str
    nvidia_container_toolkit_min: str
    cost: str | None = None     # a key of ReferenceFile.costs (C7); None: the release's `cost`

@dataclass(frozen=True, slots=True)
class VerifierProfile:
    id: str
    logical_cpus: int
    host_memory_gib: int
    emulation_allowed_on: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ReferenceFile:
    release: str
    profiles: Mapping[str, ProverProfile | VerifierProfile]
    price_per_gpu_hour: Quantity
    cost_basis: str
    providers: tuple[str, ...]
    price_date: str
    costs: Mapping[str, Cost] | None = None   # C7

    def price_pointer(self, profile: str) -> str: ...  # "/cost/..." or "/costs/<basis>/..."

def load_reference(release: str, root: Path) -> ReferenceFile: ...
```

Profile rules:

- R1. Every published row identifies its profile ID. A profile's `gpu.count` specifies both how many GPUs a job binds and how many GPUs are counted in cost calculations. On the host, `gpu.count` acts as a minimum: a multi-GPU host passes PC-GPU-COUNT, the job binds `gpu.count` GPUs by index (`--gpu`), and any remaining GPUs stay idle, unseen by job steps, and unpriced, while `gpu.count_visible` records the host's total GPU count. Any system needing more GPUs than an existing profile provides requires declaring a larger profile in the release file via RFC, and its cost uses that profile's GPU count (v0.1 declares no multi-GPU prover profile). Serving profiles (R6) bind all `gpu.count` GPUs, all of which are used by the server and counted in cost (amendment of 2026-11-09; amended 2026-11-08 to accommodate multi-GPU bare-metal H200 nodes and dual-GPU hosted H200 flavors under `prover-h200-hosted`, §H200 profiles).
- R2. `host_memory_gib_min` is sized to the highest documented memory need among v0.1 systems (330 GB available for FlashProve's full-size commit route, external, reported). Exception (amended 2026-11-08): `prover-h200-hosted` sets a lower floor so the smallest hosted H200 offering qualifies; systems with higher RAM requirements (such as FlashProve) run only on larger hosts within that profile that satisfy their requirement, with the machine record documenting the actual host (§H200 profiles).
- R3. `driver` is pinned to one exact version string per release; running on a different driver fails conformance. Docker Engine and NVIDIA Container Toolkit specify minimum versions only, since they do not affect proving arithmetic.
- R4. Runs from multiple hardware providers may share a single profile. For each configuration, the release index lists all contributing providers and computes cross-provider spread (`max(mean) / min(mean)`, formula D-PROVIDER-SPREAD in `iproofs.derive`, unit `ratio`, sharing the input rate's scope).
- R5. Each release designates its primary reference profile (`prover-h200` in v0.1, amended 2026-11-08). Profiles with different GPU models constitute distinct configurations (RFC-0009 groups rows by profile), are never pooled or compared directly, and display the profile name alongside every figure just like hosted rows.
- R6. Serving profiles (amendment of 2026-11-09). Profiles with `kind: serving` execute only reference systems with `reference_role: serve` (RFC-0015 SRV-6); running any other system on a serving profile fails with `config`. Each GPU count gets its own profile named `serving-<gpu><count>[-hosted]`. `pairs_with` lists which prover profiles may divide against this serving profile for overhead calculations (RFC-0004 INV-DERIVE-2 (c)), and validation enforces matching `gpu.model`, `form_factor`, and runtime kind (`docker` or `hosted`) so overhead ratios never cross GPU generations or execution environments. Hosted serving jobs bind `gpu.count` GPUs by index (`--gpus i,j,k,l` via `CUDA_VISIBLE_DEVICES`) and grant the inference engine and tensor-parallel workers every CPU available to the container (no CPUs are reserved for verification because reference systems skip `verify`). Docker serving container bindings (NUMA cpusets, `--cpuset-mems`, `--shm-size`) will be defined alongside docker serving profiles after Q7.

  In v0.1, `reference/v0.1.yaml` declares only hosted serving profiles; docker serving profiles wait on Q7, and an 8-GPU profile would only be added if every 4-GPU attempt fails with `resource`. Each serving profile uses `gpu.model: "NVIDIA H200"`, form factor SXM, `memory_mib_min: 140000`, and `cost: "h200"`, inheriting driver, OS, and kernel requirements from its paired prover profile (remaining `unpinned` until Q5 is resolved, so runs record `harness.nonconforming: true`).

  | Profile | GPUs | Runtime | CPUs total min | Host memory min | Disk free min | `/dev/shm` min | `pairs_with` |
  |---|---|---|---|---|---|---|---|
  | `serving-h200x1-hosted` | 1 | hosted | 23 | 200 GiB | 500 GiB | 8 GiB | `prover-h200-hosted` |
  | `serving-h200x4-hosted` | 4 | hosted | 92 | 800 GiB | 1,000 GiB | 8 GiB | `prover-h200-hosted` |

  The hosted minimums for total CPUs, host memory, and disk scale `prover-h200-hosted` by `gpu.count`, while CPUs on the first bound GPU's NUMA node stay at 15 (PC-CPU-NUMA). These thresholds admit Hugging Face Jobs' `h200` and `h200x4` flavors (1 and 4 H200 GPUs; 23 and 92 vCPUs; 256 and 1,024 GB RAM; read from `hf jobs hardware` on 2026-11-09). Disk sizing accommodates Meta's FP8 Maverick release (416.8 GB of files on Hugging Face Hub, external, reported). The 8 GiB `/dev/shm` floor is an initial assumption to be revised after the first capture.

### H200 profiles

Amendment of 2026-11-08: the NVIDIA H200 141 GB SXM becomes the v0.1 reference GPU. NVIDIA documents 141 GB of HBM3e memory ([nvidia.com/h200](https://www.nvidia.com/en-us/data-center/h200/), read 2026-11-08). Because it is a Hopper `sm_90` GPU matching the build target of both adapter images (SASH builds with `CUDAARCHS=90`, `systems/sash/README.md`), both pinned images run unchanged. Two H200 profiles are added alongside the existing `prover-h100` and `prover-h100-hosted` profiles and their pricing.

| Profile | Runtime | Host it describes | Differs from `prover-h100` / `prover-h100-hosted` in |
|---|---|---|---|
| `prover-h200` (reference, R5) | docker | Bare metal: 1x NVIDIA H200 141 GB SXM, >= 24 logical CPUs on the GPU's NUMA node and >= 32 total, >= 330 GiB host memory, local NVMe with >= 500 GiB free, Ubuntu 24.04, kernel >= 5.19, Docker Engine >= 25.0 and NVIDIA Container Toolkit >= 1.17 on cgroup v2 with systemd driver | `gpu` and `cost` only |
| `prover-h200-hosted` | hosted (§Hosted execution) | Provider-managed container launched from the adapter image: 1x NVIDIA H200 141 GB SXM bound, >= 15 usable logical CPUs on the GPU's NUMA node and >= 23 total, CPU quota (if set) >= 15, >= 200 GiB available/allowed host memory, >= 500 GiB free disk, kernel >= 5.19, cgroup v2 | `gpu`, `cost`, CPU and memory minimums, and driver pin |

- `gpu.model` is set to `"NVIDIA H200"` (matching NVML's reported string for the SXM SKU), and `memory_mib_min` is 140,000 MiB (slightly below NVIDIA's 141 GB spec, just as `prover-h100` uses 80,000 MiB for 80 GB). `docs/runbooks/host-probe.py` checks both values before running jobs; a different NVML string (such as the PCIe variant) triggers a PC-GPU-MODEL conformance failure rather than widening the profile.
- On multi-GPU H200 hosts, a job binds one GPU via `--gpu <index>` (using `--gpus device=<index>` under Docker, or `CUDA_VISIBLE_DEVICES` for `setup`, `commit`, and `prove` and empty for `verify` under hosted execution), leaving the remaining GPUs idle (R1). PC-GPU-COUNT passes, PC-GPU-BUSY inspects only the bound GPU, and costs count one GPU. The runner binds CPUs from the bound GPU's NUMA node (§CPU and memory selection), and the host probe lists each GPU's NUMA node to help pick the index.
- `prover-h200-hosted` defines a minimum floor rather than a single provider's machine SKU. Its CPU and RAM floors admit the smallest hosted H200 offering surveyed on 2026-11-08: Hugging Face Jobs `h200` (1x H200 141 GB, 23 vCPUs, 256 GB RAM, 3,000 GB disk; [jobs-configuration](https://huggingface.co/docs/hub/jobs-configuration), `hf jobs hardware`, read 2026-11-08). Those 23 vCPUs split into 8 verifier CPUs (`verifier-cpu`, §Verifier profile emulation) plus 15 prover CPUs, so `select_cpus` allocates 15 prover CPUs here rather than 24; SASH normally requests 16 prover threads and 20 extraction threads, which its adapter caps to the allocated CPU count (`systems/sash/README.md` §CPU binding). The 200 GiB memory floor sits safely beneath the ~238 GiB usable out of 256 GB after container overhead. Because SASH does not document a host RAM floor upstream, any SASH job hitting the container limit fails and is recorded with kind `resource`.
- FlashProve has higher host requirements: upstream's `run.sh` refuses to start `commit` below 330 GB free RAM, commit peaked at 299.6 GB, and FlashProve requires `madvise(MADV_WIPEONFORK)` plus CPU SHA extensions (`systems/flashprove/README.md` §Machine needs, external, reported). Running FlashProve on `prover-h200-hosted` therefore requires a larger host flavor such as Hugging Face Jobs `h200x2` (2x H200, 46 vCPUs, 512 GB RAM, 6,000 GB disk), still binding only 1 GPU (R1); the second GPU is billed by the provider but excluded from benchmark cost (C5). Because FlashProve normally binds 24 CPUs (`systems/flashprove/README.md` §CPU binding) rather than the 15 allocated on `prover-h200-hosted`, hosted rows are also non-comparable with `prover-h200` rows on CPU count (R5, §Hosted execution).
- Provider retail rates are separate from the benchmark cost basis: rows on both H200 profiles are priced via `costs.h200` (C7). Hugging Face Jobs prices (5.00 USD/h for `h200` and 10.00 USD/h for `h200x2`, billed per minute, same source) are excluded from `costs.h200` because their form factor is undocumented, failing C3.
- NVIDIA Confidential Computing (CC) mode is controlled by the host operator and is enabled on the Lucid Computing cluster noted above (owner report, 2026-11-08). All H200 benchmark runs require CC mode disabled so every H200 row reflects one consistent GPU configuration (neither v0.1 prover documents whether CC mode was active during its published runs at the RFC-0003 pins). Because the machine record intentionally omits a CC field (INV-MR-1), the host probe verifies CC mode prior to each campaign and records it in the campaign log (Q4); if a hosted container cannot query CC mode, the probe reports it as unread.
- Both H200 profiles start with `driver: unpinned` until real hosts are probed: `prover-h200` pins the driver from the bare-metal campaign host (Q3), while `prover-h200-hosted` pins the driver reported by a hosted H200 container (Q5), matching how `prover-h100-hosted` was handled. While `unpinned`, runs log PC-DRIVER failures in their manifests.
- Verifier emulation is permitted on both H200 profiles (`verifier-cpu` `emulation.allowed_on`).

RISK: FlashProve's build guide (`prover/docs/build.md` at the pin) specifies an H100 and does not document H200 behaviour. During `setup`, FlashProve verifies a digest of float32 scales computed on GPU, and upstream cautions that `"its rounding can differ between GPU models, drivers and torch's CUDA libraries"` (`systems/flashprove/README.md`). Resolution: if an H200 run fails at that digest check, record the failed run with its exit code and stderr tail (AGENTS.md rule 5), open an issue, and do not patch the adapter to work around it (AGENTS.md rule 1).

### Machine record

Generated by `iproofs machine-record` and embedded in `manifest.json` under `machine` (schema `manifest/1`). Exhaustive field list:

| Field | Source on Linux | Example form |
|---|---|---|
| `gpu.model` | NVML `nvmlDeviceGetName` | string |
| `gpu.count_visible` | NVML device count | int |
| `gpu.memory_total_mib` | NVML `nvmlDeviceGetMemoryInfo.total` | int |
| `gpu.bound_index` | harness selection | int |
| `gpu.numa_node` | `/sys/bus/pci/devices/<bdf>/numa_node` | int |
| `gpu.driver_version` | NVML `nvmlSystemGetDriverVersion` | string |
| `gpu.cuda_driver_api` | NVML `nvmlSystemGetCudaDriverVersion_v2` | string |
| `cpu.model` | `/proc/cpuinfo` `model name` | string |
| `cpu.sockets`, `cpu.physical_cores`, `cpu.logical_cpus` | `/sys/devices/system/cpu/*/topology` | int |
| `cpu.smt_active` | `/sys/devices/system/cpu/smt/active` | bool |
| `cpu.bound_prover` | harness selection (§CPU selection) | list of int |
| `cpu.bound_verifier`, `cpu.bound_verifier_single` | harness selection | list of int |
| `numa.nodes` | `/sys/devices/system/node/` | int |
| `numa.bound_mems` | harness selection | list of int |
| `memory.total_bytes`, `memory.available_bytes_at_start` | `/proc/meminfo` | int |
| `disk.type`, `disk.free_bytes_at_start` | `/sys/block/<dev>/queue/rotational`, transport; `statvfs` of results and model directories | string, int |
| `os.id`, `os.version_id` | `/etc/os-release` | string |
| `kernel.release` | `uname -r` | string |
| `container.docker_engine`, `container.cgroup_driver`, `container.cgroup_version` | `docker version`, `docker info` | string |
| `container.nvidia_container_toolkit` | `nvidia-ctk --version` | string |
| `container.execution` | `hosted` under §Hosted execution; absent under Docker | enum |
| `cpu.cgroup_quota_cpus` | `/sys/fs/cgroup/cpu.max` of the harness cgroup (`quota / period`); absent if unlimited | number |
| `memory.cgroup_limit_bytes` | `/sys/fs/cgroup/memory.max`; absent if unlimited | int |
| `gpu.bound_indices` | harness selection: all bound GPUs (amendment of 2026-11-09); `gpu.bound_index` stays as the first | list of int |
| `gpu.numa_nodes` | same as `gpu.numa_node`, one entry per bound GPU | list of int |
| `gpu.nvlink_active_links` | NVML `nvmlDeviceGetNvLinkState` across each bound GPU's links, null when unreported by NVML | list of int or null |
| `gpu.unbound_samples` | per visible unbound GPU: peak compute-process count, memory used, and utilisation across readings (PC-GPU-IDLE; currently one reading per record) | list of objects |
| `container.shm_bytes` | `statvfs` of `/dev/shm` | int |
| `provider` | runner-supplied CLI flag (`--provider`) | string |
| `verifier_host` | `same_as_prover` or `separate` | enum |

Explicitly excluded fields (rejected by the CI secrets and identifiers scan in RFC-0013 if found anywhere in a run directory): hostname, FQDN, IPv4 and IPv6 addresses, MAC addresses, GPU UUIDs, GPU serial numbers, board part serials, CPU microcode serials or PPINs, disk serials and WWNs, cloud instance IDs and region/zone identifiers, account and usernames, SSH configs and aliases, and absolute home directory paths.

INV-MR-1: `machine` contains strictly the fields tabulated above, enforced via `additionalProperties: false` in `manifest/1`.
INV-MR-2: the harness collects the machine record both before `info` and after the final step; any change in `gpu.driver_version`, `kernel.release`, or `cpu.bound_prover` fails the run with kind `environment`.

### CPU and memory selection

Prover containers receive `--cpuset-cpus <bound_prover> --cpuset-mems <bound_mems>`, while verifier containers receive `--cpuset-cpus <bound_verifier>` (or `<bound_verifier_single>`), no GPU device, and `--memory 32g`.

```text
select_cpus(topology, gpu_numa_node, n_prover, n_verifier=8):
    node_cpus   = logical CPUs on gpu_numa_node, ascending id
    cores       = group node_cpus by (package_id, core_id), ordered by smallest cpu id in group
    first_pass  = [min(group) for group in cores]          # one logical CPU per physical core
    second_pass = [remaining cpus of each group, ascending]  # SMT siblings
    ordered     = first_pass + second_pass
    if len(ordered) < n_prover: fail environment("not enough CPUs on GPU NUMA node")
    prover      = ordered[:n_prover]
    others      = all logical CPUs not in prover, same ordering rule, NUMA node of gpu first
    if len(others) < n_verifier: fail environment("not enough CPUs for verifier emulation")
    verifier    = others[:n_verifier]
    verifier_1  = verifier[:1]
    mems        = [gpu_numa_node]
    return prover, verifier, verifier_1, mems
```

`iproofs.provenance.select_cpus(topology: Topology, gpu_numa_node: int, n_prover: int, n_verifier: int) -> CpuBinding` is a pure function tested against stored Linux topologies. `n_prover` comes from the profile's `cpu.logical_cpus_on_gpu_numa_node` (24 on all v0.1 profiles except `prover-h200-hosted`, which uses 15; amended 2026-11-08, §H200 profiles). Under §Hosted execution, the topology is filtered first to the harness process's scheduler affinity mask (which reflects provider cpusets) so no inaccessible CPU is selected, while cgroup CPU quotas are validated separately by PC-CPU-QUOTA. Because prover and verifier CPU sets never overlap, verification timed immediately after proving is isolated from any lingering prover threads. Upstream thread-binding guidance (such as FlashProve pinning threads only within its allowed CPU mask) is followed and documented in each adapter's README (RFC-0005).

### Verifier profile emulation

By default in v0.1, the verifier profile is emulated on the prover host with no GPU attached, 8 pinned logical CPUs (1 for `verify.single_thread`), a 32 GiB memory cap, and `--network none`. Runs record `verifier_host: same_as_prover` along with the host's CPU model. Runners MAY instead verify on a separate CPU-only machine, transferring proofs by digest and recording `verifier_host: separate` with that machine's record stored under `machine_verifier`.

RISK: an emulated verifier runs on server CPUs with larger caches and higher memory bandwidth than a typical 8-core laptop, which may shift verification times. Resolution: every verification figure displays the CPU model alongside it, and the first release report benchmarks one configuration on both an emulated and a separate CPU host to quantify the gap; if the divergence is substantial, a subsequent RFC will mandate a dedicated verifier host.

### Profile conformance check

`iproofs.provenance.check_profile(record: MachineRecord, profile: ProverProfile) -> list[ConformanceFailure]` runs prior to `info`. Any failures are saved in the manifest (`harness.nonconforming: true` plus the list of failed check IDs) without aborting execution.

| Check id | Fails when |
|---|---|
| PC-GPU-MODEL | Bound GPU name does not match `gpu.model` |
| PC-GPU-MEM | `memory_total_mib < memory_mib_min` |
| PC-GPU-COUNT | Fewer visible GPUs than `gpu.count`; on a serving profile, bound GPU count disagrees with `gpu.count` |
| PC-GPU-BUSY | Another compute process is active on any bound GPU (RFC-0011) |
| PC-GPU-IDLE | On any profile, a visible unbound GPU shows a compute process or exceeds the idle baseline (1,024 MiB used or 5 % utilisation, provisional until initial captures calibrate it) before `info`, or shows a compute process after the final step (amendment of 2026-11-09). During every step, `iproofs.measure.IdleWatch` also polls each visible unbound GPU once per second on a dedicated thread and flags any compute process, memory exceeding baseline + 1,024 MiB, or utilisation above 5 % (sub-second spikes can fall between polls) |
| PC-GPU-LINK | Record only: on multi-GPU serving profiles (`gpu.count > 1`), logs each bound GPU's NVLink state without failing until initial `h200x4` captures confirm whether NVML exposes NVLink inside Hugging Face containers; a future amendment will promote this to an active check |
| PC-SHM | Hosted profiles: `container.shm_bytes` is below the profile's `shm_gib_min` |
| PC-DRIVER | Installed driver version differs from pinned `driver` |
| PC-CPU-NUMA | Fewer than `logical_cpus_on_gpu_numa_node` logical CPUs on the GPU's NUMA node (hosted: within the container's affinity mask) |
| PC-CPU-TOTAL | Fewer than `logical_cpus_total_min` total logical CPUs |
| PC-CPU-QUOTA | `cgroup_quota_cpus < logical_cpus_on_gpu_numa_node` |
| PC-MEM | `min(available_bytes_at_start, cgroup_limit_bytes) < host_memory_gib_min` GiB |
| PC-DISK | Free disk space on results or model filesystem `< free_gib_min`, or disk type is not NVMe (when required) |
| PC-OS | OS ID or version disagrees with profile |
| PC-KERNEL | Kernel version is older than `kernel_min` |
| PC-CGROUP | Cgroup version is not 2, or cgroup driver is not systemd (hosted: checks cgroup version 2 only) |
| PC-RUNTIME | Docker Engine or NVIDIA Container Toolkit below minimum, or `container.execution` disagrees with profile runtime kind |

`iproofs run --allow-nonconforming` is accepted as a no-op flag because every run already logs its conformance results directly in `manifest.json` (RFC-0014).

### Hosted execution

Some GPU providers rent H100 or H200 instances strictly as managed containers launched from a user-specified image, without exposing Docker, user namespaces, or a writable cgroup hierarchy inside. Profiles specifying `container_runtime: {kind: "hosted", cgroup_version: "2"}` model these environments. The provider boots the pinned adapter image (or a local build via `--image` for development, ineligible for releases per RFC-0014), the harness is installed inside that container, and `iproofs run --hosted --gpu <index>` executes each step directly via the image's `ENTRYPOINT`:

- CPU pinning uses `taskset -c` with the CPU list from §CPU and memory selection. When running as root, the harness drops privileges to the adapter uid with no Linux capabilities and `no-new-privileges` via `setpriv`, mirroring `docker --user --cap-drop ALL --security-opt no-new-privileges`.
- Recorded commitment files (RFC-0014) are set to root-owned and read-only prior to invocation so `verify` reads the harness's own copies just as under Docker.
- Adapter processes inherit only the image's declared environment (read from PID 1), stripping provider-injected variables such as access keys, ports, or host addresses.
- GPU selection uses `CUDA_VISIBLE_DEVICES` in PCI bus order, with `verify` receiving an empty device list.
- Because `/tmp` persists across calls in a hosted container (unlike Docker's per-container tmpfs), the harness cleans files owned by the adapter uid from `/tmp` before every step so compile or engine caches cannot bleed across repetitions, while keeping harness files outside `/tmp`.

Properties that cannot be isolated in hosted containers are recorded transparently: network access (`commands[].network: "provider"` in `manifest.json`), NUMA memory binding (`numa.bound_mems` records the target node without kernel enforcement because containers lack memory-policy capabilities), per-step memory caps (including the verifier's 32 GiB cap), and a read-only root filesystem. CPUs may also be time-shared with neighbouring tenants under a quota (`cpu.cgroup_quota_cpus`). Because `/etc/os-release` belongs to the image rather than the host, PC-OS is skipped and `os` is omitted; similarly, `disk.type` is omitted on overlay filesystems.

Resource counters (RFC-0011) come from the container's cgroup: `cpu_seconds` measures `cpu.stat usage_usec` deltas across each step, `host_memory_peak_anon` samples `memory.stat anon`, and OOM kills map to `resource` failures (these readings include the mostly-idle harness process). `host_memory_peak_kernel` is recorded as null with `not_measurable_on_profile` because `memory.peak` spans the container's entire lifetime rather than a single step. GPU metrics come from NVML as usual.

Hosted calibration runs via `iproofs machine-record --selftest --hosted` (RFC-0011 §Calibration self-test), probing inside the container, reading container cgroup counters for ST-CGROUP, and skipping ST-OOM.

Hosted rows form separate configurations from Docker rows (RFC-0009 groups by profile); they are never pooled with Docker runs, and every published figure displays the profile name.

RISK: shared host CPUs and non-isolated networking make hosted runs noisier and weaker evidence than dedicated Docker hosts. Resolution: every row displays its profile name, the release report flags hosted rows explicitly, and the v0.1 report compares one configuration across both hosted and Docker machines once a bare-metal Docker host is available.

### Cost basis

- C1. Published costs are derived exclusively from the release's `price_per_gpu_hour_usd`, never from a team's self-reported pricing (which MAY appear only as `external`).
- C2. Each price is stored as an `asserted` quantity with its calculation basis, provider list, and reading date.
- C3. Default basis: the median on-demand public list price for the profile's exact GPU model and form factor across at least three named providers, captured on a single stated date and archived (with provider URLs and date) in the release report.
- C4. Prices remain frozen for the duration of a release. Updating a price requires a new release or an RFC amendment; past derived costs are never overwritten in place.
- C5. CPU cores, host RAM, storage, and networking are unpriced in v0.1, and every page or report displaying a cost figure states this explicitly.
- C6. Release freeze rejects any price basis with `value: 0` or a missing date (`iproofs release freeze` exits 1), applying to every declared basis (C7).
- C7. Per-GPU pricing bases (amended 2026-11-08; serving rows added 2026-11-09). Serving rows price all `gpu.count` GPUs at `costs.h200`; because both prover and serving rows share the same per-GPU-hour rate, their cost ratio equals D-OVERHEAD-S while C5 continues to exclude CPU, host memory, disk, and network. Hugging Face Jobs retail rates (5, 10, 20, and 40 USD/h for 1, 2, 4, and 8 H200 GPUs, read 2026-11-09) do not enter the basis because they omit form factor (C3). `cost` serves as the release's default basis, while profiles using another GPU model name an entry under `costs` via their `cost` field (`ReferenceFile.price_pointer` resolves `costs.<basis>.price_per_gpu_hour_usd`). Each basis obeys C2 through C6; CI recomputes every median from its archived readings (COST-1) and rejects any profile referencing an undefined basis (COST-2). In v0.1, `cost` remains the H100 SXM basis (Q1) so existing `results/` runs still recompute identically (C4), while `costs.h200` prices `prover-h200`, `prover-h200-hosted`, and the H200 serving profiles.

Archived H200 readings for `costs.h200` (rule C3, read 2026-11-08 from each provider's public pricing page and stored in `reference/v0.1.yaml` `costs.h200.readings`, whose median CI recomputes automatically rather than hardcoding here):

| Provider | Page | Offer read | List price | GPUs |
|---|---|---|---|---|
| RunPod | [runpod.io/pricing](https://www.runpod.io/pricing) | H200 SXM 141 GB, Secure Cloud (first-party data centres; Community Cloud marketplace excluded, as in Q1) | 5.29 USD/h | 1 |
| CoreWeave | [coreweave.com/pricing](https://www.coreweave.com/pricing) | NVIDIA HGX H200, on-demand | 50.44 USD/h | 8 |
| Nebius | [nebius.com/prices](https://nebius.com/prices) | NVIDIA HGX H200, on-demand, per GPU | 5.40 USD/h | 1 |
| DigitalOcean | [digitalocean.com/pricing/gpu-droplets](https://www.digitalocean.com/pricing/gpu-droplets) | NVIDIA HGX H200 GPU Droplet, on-demand, per GPU | 4.47 USD/h | 1 |

All four readings represent SXM (HGX) on-demand list prices (grade asserted, tier reported). Excluded: Lambda (which listed no H200 on 2026-11-08), listings that omit GPU form factor (failing C3), and hyperscalers (for the regional pricing variance explained in Q1).

### Failure modes

| Failure | Response |
|---|---|
| Reference file missing or schema-invalid | `config` error at startup (exit 1 in `validate`, exit 2 in `run`) |
| Host fails a conformance check | `environment` error, exit 3, no timed steps execute, no run directory written to `results/` |
| Driver or kernel changes mid-job (INV-MR-2) | Job fails at the detecting step with kind `environment` |
| Excluded host identifier detected in a run directory | CI secrets scan fails; PR blocked |
| Host topology lacks enough CPUs for verifier emulation | `environment` error; runner may offload verification to a separate verifier host |
| Price basis has `value: 0` at release freeze | Freeze exits 1 (C6) across every basis (C7) |
| Profile references a cost basis absent from `costs` | Gate G2 fails with COST-2; `run` aborts with `config` before any timed step |

## Alternatives Considered

- **Letting each team pick arbitrary hardware and normalising results afterward.** Lowers barriers to entry, but rejected because cross-GPU normalisation requires a speculative performance model that the benchmark would have to defend; fixed profiles enable direct within-release comparison without one (PRD G2).
- **Requiring a physically separate verifier host by default.** Most faithfully models a relying party's hardware, but rejected for v0.1 due to transfer overhead and cost (SASH's 4,096-context run produces roughly 19.8 GB of proofs, external, reported, SASH results repo at the pin). Retained as an optional mode and as the mitigation path for the emulation RISK.
- **Pricing CPU cores and host RAM alongside GPUs.** Considered because FlashProve uses roughly 300 GB of host RAM (external, reported), but rejected for v0.1 because cloud providers bundle CPUs and RAM differently per GPU SKU, forcing an arbitrary pricing split. Instead, rule C5 explicitly discloses the omission wherever costs appear.
- **Using spot or committed-use discounts.** Reflects large-scale buyer pricing, but rejected because spot and contract rates fluctuate continuously and cannot be audited by readers, unlike public on-demand list prices.
- **Dumping full `lscpu`, `nvidia-smi -q`, and `dmidecode` outputs.** Thorough, but rejected because raw dumps leak serial numbers and UUIDs (violating AGENTS.md rule 7); the curated field list captures everything needed for reproduction.

## Drawbacks

- Pinning one exact NVIDIA driver version per release can disqualify cloud instances whose images ship another driver unless runners can install the pinned version.
- Emulated verification runs on server-grade CPUs rather than consumer laptops (tracked in RISK above).
- Freezing a single GPU price per release ignores market price swings during the campaign.
- Carrying two GPU generations in one release fragments rows: H100 and H200 runs belong to distinct configurations and cannot be compared directly (R5).
- Because `prover-h200-hosted` defines a minimum spec, qualifying hosts can differ significantly (1 vs 2 GPUs, 23 vs 46 vCPUs, 256 vs 512 GB RAM), and FlashProve requires the larger tier to meet its 330 GB memory floor. Each manifest's machine record identifies the host actually used, hosted runs remain lower-confidence than bare-metal Docker runs (§Hosted execution RISK), and providers bill all GPUs on a multi-GPU flavor even though derived costs count only the single bound GPU (R1, C5).

## Migration / Rollout

2026-11-08 revision: promoted H200 to the v0.1 reference GPU (§H200 profiles), added `prover-h200` and `prover-h200-hosted`, parameterised `select_cpus` by profile prover CPU count and hosted scheduler affinity, clarified multi-GPU host handling in R1, designated the reference profile in R5, and added optional `costs` / profile `cost` in `reference/1` (C7). This revision is strictly additive: prior profiles, prices, and stored `results/v0.1` runs (`prover-h100-hosted`) remain untouched with their original derived costs.

2026-11-09 amendment (RFC-0015 SRV-6): added multi-GPU serving profiles (`kind: serving`, `pairs_with`, `shm_gib_min`, and `gpu.count > 1` restricted to serving profiles) while keeping prover profiles single-GPU. Extended the machine record with `gpu.bound_indices`, `gpu.numa_nodes`, `gpu.nvlink_active_links`, `gpu.unbound_samples`, and `container.shm_bytes` (none identifying a host), and added conformance checks PC-GPU-IDLE, PC-GPU-LINK (record-only), PC-SHM, and exact PC-GPU-COUNT on serving profiles. Docker serving bindings (TC-CPU-SERVING) wait on docker serving profiles. Strictly additive; stored runs are unchanged.

Earlier revisions (from the 2026-11-03 draft, before any results existed): added OS, kernel, runtime, and cgroup specifications, formalised the exhaustive machine record and exclusion list, defined deterministic CPU selection and verifier emulation, converted the cost block to a labelled quantity, and introduced schema `reference/1`. Adding new profiles is additive; altering an existing profile's constraints within a release is forbidden and requires a new release file.

## Testing Strategy

- TC-REF-VALID / TC-REF-INVALID: validates schema examples, rejecting missing `driver`, ungraded `price_per_gpu_hour_usd`, a verifier profile declaring a GPU, and unknown profile fields.
- TC-CPU-2SOCKET-SMT: given a stored 2-socket, 48-physical-core SMT-enabled topology with GPU on NUMA node 1, expects 24 prover CPUs (one per physical core on node 1), disjoint verifier CPUs, and `mems = [1]`.
- TC-CPU-SMALL-NODE: confirms a NUMA node with 16 logical CPUs triggers `environment` failure PC-CPU-NUMA.
- TC-CPU-SMT-OFF: confirms deterministic selection when SMT is disabled (empty second pass).
- TC-CPU-DETERMINISTIC: Hypothesis property test across random topologies confirming deterministic output, disjoint prover/verifier CPU sets, and valid CPU IDs.
- TC-MR-FIELDS: runs `machine-record` on fixture `/sys` and `/proc` trees (`harness/tests/fixtures/host/`) and asserts the exact allowed field set.
- TC-MR-NO-IDENTIFIERS: seeds a fixture tree with a hostname, GPU UUID, and MAC address and verifies none appears in the record or logs.
- TC-MR-DRIFT: supplies mismatched pre-run and post-run kernel strings and confirms an `environment` failure.
- TC-CONFORM-EACH: one test per conformance check ID, toggling a single fixture field each time.
- TC-FREEZE-PRICE-ZERO: confirms `release freeze` exits 1 when any price basis has `value: 0`.
- TC-H200-CONFORM (`harness/tests/unit/test_h200_profiles.py`): verifies bare-metal 8x H200 records (GPU 0 bound) pass `prover-h200` once driver-pinned, fail only PC-DRIVER when unpinned, fail PC-GPU-COUNT with 0 GPUs, fail PC-GPU-MODEL and PC-GPU-MEM on H100 records, and fail PC-RUNTIME on hosted records; verifies Hugging Face `h200` (1 GPU, 23 CPUs) and `h200x2` (2 GPUs, GPU 1 bound) pass `prover-h200-hosted`, while a 14-CPU quota fails PC-CPU-QUOTA and 192 GiB fails PC-MEM.
- TC-CPU-HOSTED (`test_h200_profiles.py`): verifies `select_cpus(n_prover=15)` splits a 23-CPU topology into 15 prover and 8 verifier CPUs, filters hosted topologies by scheduler affinity, and passes the profile's prover CPU count in `iproofs run`.
- TC-COST-BASIS (`test_h200_profiles.py`, `test_cost.py`): verifies H200 profiles resolve `costs.h200`, H100 profiles resolve `cost`, COST-1 checks hand-computed medians on every basis, and COST-2 rejects unknown bases.
- GPU-host test GH-MR-H100: runs `iproofs machine-record --selftest` on a live `prover-h100` host and validates the output. GH-MR-H200 repeats this on `prover-h200` and on `prover-h200-hosted` with `--hosted` (running `test_numa_binding.py` under `IPROOFS_PROFILE=prover-h200-hosted` to test 15-CPU binding from the container affinity mask).
- TC-SERVING-PROFILE (`test_h200_profiles.py`): verifies `h200x4` fixtures (4 bound GPUs, 8 GiB `/dev/shm`) pass `serving-h200x4-hosted` even with null or down NVLink (PC-GPU-LINK record-only), while 3 bound GPUs fail PC-GPU-COUNT and `pairs_with` pointing to an H100 profile fails validation.
- TC-GPU-IDLE (`test_serving_runs.py`): simulates NVML with GPU 0 bound, verifying GPU 1 passes at baseline and triggers `environment` failure if a compute process appears or memory exceeds baseline + 1,024 MiB during a step, and flags pre-existing unbound GPU usage before `info`.
- GPU-host test GH-MR-H200X4: runs `iproofs machine-record --hosted --gpus 0,1,2,3 --selftest` on `h200x4`.

## Decisions

- Q1. The H100 pricing basis follows rule C3 using Lambda, RunPod, and CoreWeave read on 2026-11-04 from public pricing pages: Lambda's 1x H100 SXM 80 GB, RunPod's H100 SXM on Secure Cloud (first-party data centres, excluding Community Cloud marketplace), and CoreWeave's 8-GPU HGX H100 divided by 8. Each reading (provider, URL, offer, list price, GPU count) is archived in `reference/v0.1.yaml` `cost.readings`, and CI recomputes the per-GPU-hour median (COST-1) so no price is entered manually. Hyperscalers were excluded because their 8-GPU H100 list prices vary across regions.
- Q2. H200 is added as a second GPU model and designated the v0.1 reference (§H200 profiles, R5), while H100 profiles remain declared. Prover profiles bind one GPU, leaving extra host GPUs idle and unpriced (R1). Multi-GPU serving profiles are declared under R6 (2026-11-09).
- Q3. The pinned NVIDIA driver is the newest version compatible with both CUDA 13.2 Update 2 (FlashProve) and CUDA 12.9 (SASH) containers, selected in the reference file pull request; `prover-h200` pins the driver from the H200 campaign host.
- Q4. H200 campaigns require Confidential Computing mode turned off. Because the machine record has no CC field, `docs/runbooks/host-probe.py` queries `nvidia-smi conf-compute` before each campaign and the campaign log in the results PR archives the `cc` line; any host reporting CC enabled or unreadable is excluded from campaign runs.
- Q5. `prover-h200-hosted` pins the driver reported by the host probe and `iproofs machine-record --hosted` on a Hugging Face Jobs H200 container via pull request (mirroring `prover-h100-hosted`); adding another hosted provider with a different driver requires its own pin (R3). While `unpinned`, runs log PC-DRIVER failures in their manifests.
- Q6. Providers that start containers directly as the image's non-root user (`USER 10001` in both adapter Dockerfiles) are limited to development runs. Without root inside the container, §Hosted execution cannot drop adapter privileges, wipe `/tmp` owned by the adapter uid between steps, or make commitment copies root-owned (they stay read-only but owned by the adapter uid), and any secret passed to the job is readable via PID 1's environment under the same uid. Because Hugging Face Jobs does not document its container runtime user, the host probe reports whether it is running as root.
- Q7. Serving profiles are hosted-only in v0.1 because Docker serving for Maverick requires four H200 SXM GPUs inside a single NVLink node, which the bare-metal research cluster is not known to have; accordingly, only hosted serving rows (paired with hosted prover rows) are produced.

## References

- docs/PRD.md §4 (G2, G3), §7 (F5), §11.
- AGENTS.md rule 7.
- [RFC-0004](0004-metrics-timing-grades.md) for cost formulas; [RFC-0005](0005-adapter-contract.md) for container invocation; [RFC-0011](0011-measurement-and-sampling.md) for the GPU busy check and sampling; [RFC-0012](0012-schemas-and-serialization.md) for `reference/1` and `manifest/1`; [RFC-0013](0013-validation-and-ci.md) for the identifiers scan.
- Linux sysfs CPU topology and cgroup v2 documentation (kernel.org, `Documentation/admin-guide/cgroup-v2.rst`).
