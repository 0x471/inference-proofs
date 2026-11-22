# RFC-0003: Workloads, prompt sets and divisions

- Authors: AbdelStark
- Created: 2026-11-03
- Requires: RFC-0002, RFC-0012

## Summary

A workload pins down everything that gets proved: the model weights by content hash, the numerical precision, the prompt set via generator and corpus hash, the tensor and batch shape, the decoding rule, and the inference phase. This RFC defines the workload file schema and types, the four v0.1 native workloads for SASH and FlashProve, the single closed workload on Llama 3.1 8B, the deterministic prompt generator and its seed policy, the model fetch and hash verification workflow, how systems declare tokens covered per proof, and the three benchmark divisions (native, closed, and open). It also specifies the criteria for adopting a common workload and when rows from a closed workload may be published.

## Motivation

Fixed workloads are what made Ethproofs results comparable ([PRD §2](../docs/PRD.md#2-vision)). Provable inference does not yet have a single shared workload: at their pinned commits, SASH supports Llama-3.1-8B (W8A8) while FlashProve supports Llama 4 Maverick at full size alongside small synthetic shapes, and neither system can run the other's model ([PRD §6](../docs/PRD.md#6-scope-of-v01)). The benchmark needs to represent that reality honestly from its first release while keeping every published row reproducible.

Concrete scenarios:

1. Six months after a run, someone reproducing it must be able to regenerate the exact prompts from the saved run record alone.
2. If prompts were fixed and public in advance, a team could precompute proofs ahead of time; measured runs must prevent caching.
3. If a model host silently swaps a weight file under the same revision, the run must abort before any container accesses the file.
4. When two rows from different native workloads appear on the same page, readers must not see them framed as a head-to-head comparison.

## Goals

- Validate every workload file against `schema/workload/1.schema.json` so that it fully determines all job inputs apart from the per-job seed.
- Ensure that given a workload, a seed, and the pinned tokenizer, the prompt set is bit-for-bit reproducible across machines on the supported Python versions (INV-WL-2).
- Verify the SHA-256 hash of every weight file before use (INV-WL-1).
- Draw a fresh seed for every measured job and record it in the manifest (INV-WL-3).
- Label every row with its division and never present rows from distinct native workloads as a direct head-to-head comparison (INV-WL-5).

## Non-Goals

- Defining additional common workloads beyond `l31-8b-c1024` and the general selection criteria (deferred to v0.2).
- Supporting sampled decoding; v0.1 uses greedy decoding exclusively.
- Redistributing model weights or tokenizers; this repository never stores weights ([AGENTS.md](../AGENTS.md) rule 8).
- Measuring model accuracy directly; `quality_gap` figures are copied from upstream documentation (RFC-0002).

## Proposed Design

### Workload file

Each workload lives at `workloads/<id>.yaml` and validates against `schema/workload/1.schema.json`, following the type conventions in RFC-0012.

| Field | Required | Type | Content |
|---|---|---|---|
| `schema` | yes | `"workload/1"` | Schema identifier |
| `id` | yes | `^[a-z0-9][a-z0-9-]{2,63}$` | Workload identifier, e.g. `sash-l31-8b-c4096` |
| `version` | yes | integer >= 1 | Increments on any change that alters job inputs; a new version is treated as a distinct workload for comparisons |
| `division` | yes | enum `native`, `closed`, `open` | Benchmark division |
| `claim_class` | closed only | claim class string (RFC-0002) | The single claim class permitted in a closed workload |
| `model.source` | yes | `{hub: "huggingface", repo: Text}` | Public model source |
| `model.revision` | yes | 40-hex commit of the model repository | Full commit hash only, never a branch or tag |
| `model.files` | yes | list of `{path: Text, sha256: 64-hex, bytes: integer}` | Every file read by the adapter or tokenizer |
| `model.digest` | yes | `sha256:<hex>` | Digest over `<path>\t<sha256>\n` lines sorted by path bytes (RFC-0012) |
| `model.licence` | yes | `{name: Text, url: Text, gated: bool}` | Access and licensing terms |
| `model.parameters` | yes | `{total: integer, active_per_token: integer, source: URL}` | Parameter counts from the model's documentation; used by RFC-0004 |
| `model.tokenizer_file` | yes | path in `model.files`, or `model.tokenizer_source.file.path` | Tokenizer file used by the prompt generator |
| `model.tokenizer_source` | no | `{hub: huggingface, repo, revision, file: {path, sha256, bytes}}` | Optional tokenizer file from a second pinned repository when the weights repository lacks one (such as a GGUF conversion). `model.digest` covers `model.files` only; this file is verified against its own SHA-256 |
| `precision` | yes | `{served: Text, proved: Text}` | Quantisation as served and as proved |
| `precision.weight_bits` | no | `{bits: number > 0 and <= 64, basis: "stated", "file_size" or "computed", covers: "all" or "part", source: URL, files: [path], method: "gguf-active-mean/1", note: Text}`; `bits` present iff `basis` is `stated` or `computed`, `files` present iff `basis` is `file_size` or `computed`, `method` present iff `basis` is `computed`, and `covers` must be `all` for `file_size` and `computed`; `note` optional | Bits per weight at the proved precision along with its source (§Weight bits); used by RFC-0004 D-SPAB-S |
| `prompts.generator` | yes | `"corpus-window/1"` | Generator identifier and version |
| `prompts.corpus_digest` | yes | `sha256:<hex>` | Digest of the `workloads/prompts/corpus.yaml` content set |
| `prompts.count` | yes | integer >= 1 | Number of prompts per job |
| `prompts.length_rule` | yes | `{prompt_tokens: integer}` | Exact token length per prompt |
| `shape.prompt_tokens` | yes | integer >= 1 | Prompt length in tokens |
| `shape.output_tokens` | yes | integer >= 1 | Generated tokens per request (1 for next-token workloads) |
| `shape.batch_size` | yes | integer >= 1 | Requests per batch |
| `shape.batches_per_session` | yes | integer >= 1 | Batches executed per `prove` call |
| `shape.context_window` | yes | integer >= `prompt_tokens + output_tokens - 1` (covering every position the model reads, since the final output token is predicted rather than read) | Context window size |
| `model.vocab_size` | yes | integer > 0, taken from the model's configuration at the pinned revision | Used by control C1 ([RFC-0008](0008-negative-controls.md#shared-controls-verifier-side)) |
| `precision.alternatives` | no | list of precision ids the system can also prove, from its documentation | Used by control P2; omitting it makes P2 `not_applicable` |
| `decoding` | yes | `{rule: "greedy"}` | Sampled decoding rules are rejected by `workload/1` |
| `phase` | yes | enum `prefill`, `decode`, `both` | Inference phase covered |
| `systems` | yes | list of system ids | Systems known to support this workload, including reference systems |
| `notes` | no | `Text` | Free-form notes |

Invariant INV-WL-4: `prompts.count == shape.batch_size * shape.batches_per_session` and `prompts.length_rule.prompt_tokens == shape.prompt_tokens`. The loader checks both equations and raises a `config` error on any violation.

### Weight bits

`precision.weight_bits` records the number of bits used to store a single weight at the proved precision (`precision.proved`). It feeds [RFC-0004](0004-metrics-timing-grades.md#derived-metric-catalogue) D-SPAB-S (prover seconds per bit of active weights per token covered) as an `asserted` input alongside `model.parameters`, always linked to its `source`. Multiplying `weight_bits` by `model.parameters.active_per_token` yields the total bits of active weights per token. The `covers` field indicates whether the width covers `all` weights counted in `active_per_token` or only `part` of them; RFC-0004 INV-DERIVE-7 excludes `part` widths from column sorting. Whenever the pinned model files already store weights at the proved precision, the width is derived from those files, either computed from their tensor headers (WB-5) or from file size when all weights share one width (WB-2). Documentation is used only when the files are stored in a different precision than the one proved (WB-1).

The five weight-bits rules are:

- WB-1, `stated`: the width stated in documentation at a pinned commit or revision, copied and linked (using the system's documentation when the system quantizes at load time, or the model publisher's documentation when the pinned files are pre-quantized). Whenever the statement does not cover every weight, `note` specifies what it covers. This basis applies when the files cannot supply the width directly:
  - Load-time quantization: the pinned files store a different precision than the proved computation. For SASH workloads, the pinned files contain BF16 weights (2 bytes per parameter across `parameters.total`), while SASH quantizes and proves int8 weight matmuls according to its source code.
  - Mixed precisions in a format lacking a WB-5 reader: tensors are stored at multiple widths, so dividing total file bytes by total parameters does not reflect active weight width. (GGUF files, used by the Maverick workloads, are handled by WB-5 instead.)
  When documentation specifies a width for only a subset of weights, the record uses `covers: part` with an explanatory `note`. SASH documents an 8-bit width for the weight matrices of its weight matmuls (detailed in §v0.1 values below). Applying that width across all active parameters extrapolates beyond what upstream claims, making the number a nominal width rather than a true mean over active weights; RFC-0004 displays the note alongside it and excludes the row from sorting (INV-DERIVE-7).
- WB-2, `file_size`: applies only when the files listed in `files` store every weight of the proved precision at a single uniform width with no extra data, so `covers` is `all`. Because this width is a derived value, it is never typed manually in the YAML file (AGENTS.md rule 3): the loader computes `bits = (sum of listed file bytes) × 8 / model.parameters.total` in binary64 from `model.files` and `model.parameters.total`. Listing a file outside `model.files` raises a `config` error, and supplying a literal `bits` value with `basis: file_size` fails schema validation.
- WB-3: if neither documentation nor the pinned files provide a width (WB-2, WB-5), `precision.weight_bits` is omitted and D-SPAB-S evaluates to null with `missing_input`. Weight widths are never estimated.
- WB-4: because `precision.weight_bits` describes the weights without altering job inputs (model files, prompts, or shape), adding it where it was previously omitted does not bump the workload `version`. At runtime, the runner copies the workload's parameter count and weight bits into `run.json` `inputs` as `asserted` quantities, and D-APT-S and D-SPAB-S reference those copies in `source.inputs` (RFC-0004 INV-DERIVE-7). That ensures RFC-0013 G4 recomputes stored runs solely from their own records, unaffected by later edits to the workload file. Once any run has recorded a workload's weight bits, changing `bits`, `basis`, or `covers` (whether for a correction or to resolve Q5) requires incrementing the workload `version` so runs before and after the change stay in separate configurations rather than pooling over two widths. Release freeze enforces this by halting with an error if repetitions of the same configuration record different workload inputs. Editing the field still changes the workload file's bytes and thus its `file_digest` in subsequent manifests (RFC-0014).
- WB-5, `computed`: when the pinned files store weights at the proved precision in a format supported by a defined computation method, `bits` is the mean storage bits per active weight computed from the headers of the files in `files`. Because this covers every weight counted by `active_per_token`, `covers` is `all`. The workload file records `bits` (formatted as the shortest decimal string that round-trips to the method's binary64 value) because the weight files themselves are not committed to this repository; to enforce AGENTS.md rule 3, three automated checks recompute and verify it: `iproofs fetch-model` reruns the method against the freshly verified files, `iproofs fetch-model --headers-only` reruns it using HTTP range requests against the pinned revision without downloading tensor payloads (while checking that the server reports each file's listed byte size), and CI reruns it against stored header fixtures (`harness/tests/fixtures/gguf/`). Any binary64 mismatch raises a `config` error. Each method also cross-checks its own parameter counts against `model.parameters.active_per_token` and `model.parameters.total`: both counts must fall within half a unit of the last non-zero digit of the stated count (for example, `17,000,000,000` for "17B" allows plus or minus `500,000,000`; `400,000,000,000` for "400B" allows plus or minus `50,000,000,000`; an exact count allows plus or minus `0.5`). The total-parameter check catches dropped or double-counted tensors outside the active margin (though for a single-digit stated total like 400e9, the margin is 12.5 %). Any count outside either bound indicates the reader misunderstood the model layout and raises a `config` error rather than recording a bad value.

  Method `gguf-active-mean/1` (`iproofs.gguf`), targeting GGUF files as defined by llama.cpp at `cd959bae99ff4bed22bef2604f45241c09bbb8c8` (v0.9.0, matching the engine pin in [RFC-0015](0015-reference-rows.md) SRV-6):
  1. Parse each file's little-endian GGUF v2 or v3 header ([`ggml/include/gguf.h`](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/include/gguf.h)), reading metadata plus every tensor's name, dimensions, ggml type, and data offset without reading tensor payloads.
  2. Each ggml type packs a fixed block of weights into a fixed byte count, defined by `blck_size` and `type_size` in `type_traits` ([`ggml/src/ggml.c` L639 onward](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/src/ggml.c#L639)) and checked by the `static_assert(sizeof(block_...))` assertions in [`ggml/src/ggml-common.h`](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/src/ggml-common.h). A tensor's bit count equals `(weights × type_size × 8) / blck_size`, including block scales: Q4_K stores 256 weights in 144 B (4.5 bits/weight), Q5_K in 176 B (5.5), Q6_K in 210 B (6.5625), Q8_0 stores 32 weights in 34 B (8.5), F16 and BF16 use 16, and F32 uses 32. Encountering a type missing from `iproofs.gguf.GGML_TYPES` or a first dimension that is not an integer multiple of `blck_size` aborts the method.
  3. Verify that header offsets tile the data section sequentially just as llama.cpp requires ([`ggml/src/gguf.cpp` L790 to L820](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/src/gguf.cpp#L790-L820)): in header order, each tensor begins where the previous tensor ends, padded up to `general.alignment` (a UINT32 power of two, defaulting to 32; [L622 to L636](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/src/gguf.cpp#L622-L636)). The final tensor must end exactly at EOF, or at EOF once padded to `general.alignment` as llama.cpp's writer pads it ([L1609](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/ggml/src/gguf.cpp#L1609)). This validates the type table's byte size for every tensor against the actual file layout.
  4. Identify active weights: every token uses all tensors except routed expert weights (`blk.N.ffn_gate_exps.weight`, `ffn_up_exps`, `ffn_down_exps`, and `ffn_gate_up_exps`; [`src/llama-arch.cpp` L535 to L538](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/src/llama-arch.cpp#L535-L538)), whose outermost dimension is the total expert count. For routed tensors, each token activates `<arch>.expert_used_count` out of `<arch>.expert_count` experts (read from the file carrying `general.architecture`; [`src/llama-arch.cpp` L230 to L231](https://github.com/ggml-org/llama.cpp/blob/cd959bae99ff4bed22bef2604f45241c09bbb8c8/src/llama-arch.cpp#L230-L231)), so routed tensors are weighted by that fraction. Shared experts (`_shexp`), routers, embeddings, and the output head count at full weight, matching the model card's active parameter count. Any unrecognised tensor name with an `exps` expert layout aborts the method. For split GGUF models, `split.count` must match the file count and `split.tensors.count` must match the total tensors read.
  5. Compute `bits = (bits of other tensors + share × bits of routed tensors) / (weights of other tensors + share × weights of routed tensors)`, where `share = expert_used_count / expert_count`, using exact rational arithmetic and rounding once to binary64.

  This measures the actual storage width in the pinned files including block scales, matching Unsloth's per-quant convention (4.5 for Q4_K). It differs from widths stated purely for integer codes without scales (such as SASH's 8 bits, which excludes per-channel scales). Whenever the pinned files store the proved precision, WB-5 supersedes WB-1 because a summary figure in documentation usually describes only one quant block or layer group, whereas the headers capture every tensor precisely (Q5).

The v0.1 values:

| Workload | `bits` | `basis`, `covers` | Source |
|---|---|---|---|
| `sash-l31-8b-c4096`, `sash-l31-8b-c1024`, `l31-8b-c1024` | 8 | `stated`, `part` | SASH at `eb95bfa887299d1637550228d42086c27cbb2b3b`, [`harness/witness/quant.py` L15 to L19](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/eb95bfa887299d1637550228d42086c27cbb2b3b/harness/witness/quant.py#L15-L19): "weight matmuls are exact int8 x int8 -> int32 accumulations", with one scale per output channel ("per-output-channel for weights", L18). Covers only the weight matrices of the weight matmuls, counting 8 bits for the int8 code alone and omitting the per-output-channel scale. No width is stated for the embedding table or RMSNorm weights counted in `active_per_token` ("not stated"). Because the pinned files are BF16 and quantized at load time, the proved width is absent from the files and WB-5 cannot compute it, so this value remains `stated`. |
| `fp-maverick-w1024-b1`, `fp-maverick-w1024-b24` | 4.83916475612899, computed | `computed`, `all`, method `gguf-active-mean/1` | Headers of the five pinned `UD-Q4_K_XL` files at `41032e5471dd6ea5b349062d978626215d6c5bba` ([folder](https://huggingface.co/unsloth/Llama-4-Maverick-17B-128E-Instruct-GGUF/tree/41032e5471dd6ea5b349062d978626215d6c5bba/UD-Q4_K_XL)), fetched via HTTP range requests on 2026-11-08: 531 tensors stored as Q4_K, Q5_K, Q6_K, and F32 (embedding table Q4_K, output head Q6_K, routed expert down projections Q4_K in 15 layers and Q5_K in 9); `llama4.expert_count` is 128 and `llama4.expert_used_count` is 1. The method counts 17,184,691,200 active weights (within the model card's 17e9 plus or minus 5e8) and 400,711,848,960 total weights (within its 400e9 plus or minus 5e10; [README L138 to L140](https://huggingface.co/unsloth/Llama-4-Maverick-17B-128E-Instruct/blob/86c5ecb6f2fbddf604c60120125fb202e09f2556/README.md#L138-L140)). Replaces Unsloth's stated 4.5 ("MoE Bits" for `Q4_K_XL`, covering one layer group, `covers: part`) per the owner's decision of 2026-11-08 (Q5); because no run had yet recorded weight bits, the workload version stays 1 (WB-4). |
| `fake-tiny-ci` | 8, computed | `file_size`, `all` | `weights.bin`, 64 B across 64 parameters ([`systems/fake/README.md`](https://github.com/ai-verification-observatory/inference-proofs/blob/64168df9fd0706dfd955b6795fa6f535872dff78/systems/fake/README.md)): 64 × 8 / 64 = 8, recomputed automatically by the loader. |

### v0.1 native workloads

| ID | System | Model | Precision | prompt + output tokens | Batch | Batches per session | Prompts per job | Phase | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `sash-l31-8b-c4096` | SASH | Llama-3.1-8B | W8A8 | 4,096 + 512 greedy continuation | 1 | 1 | 1 | both | SASH's published headline shape |
| `sash-l31-8b-c1024` | SASH | Llama-3.1-8B | W8A8 | 1,024 + 64 greedy continuation | 1 | 1 | 1 | both | Comparable to FlashProve's window length |
| `fp-maverick-w1024-b1` | FlashProve | Llama 4 Maverick, public 4-bit conversion | 4-bit | 1,024 + 1 (next token) | 1 | 5 | 5 | prefill | |
| `fp-maverick-w1024-b24` | FlashProve | same | 4-bit | 1,024 + 1 (next token) | 24 | 5 | 120 | prefill | FlashProve's published steady-state shape |

Reference rows are executed by the reference systems `ref-serve` and `ref-recompute` (RFC-0015) against these exact workload IDs. Tables display them as `ref-serve-<workload-id>` and `ref-recompute-<workload-id>`; they do not use separate workload files, and each workload's `systems` list includes both reference systems.

Model revisions, file hashes, and parameter counts are populated from the public repositories during implementation; the schema rejects any workload missing them so unpinned workloads can never execute.

### Closed workloads

| ID | Model | Precision | prompt + output tokens | Batch | Batches per session | Prompts per job | Phase | Claim class |
|---|---|---|---|---|---|---|---|---|
| `l31-8b-c1024` | Llama-3.1-8B, using the files and `model.digest` of `sash-l31-8b-c1024` | W8A8 | 1,024 + 64 greedy continuation | 1 | 1 | 1 | both | `greedy-continuation/exact-match/committed-weights` |

On 2026-11-08, the project owner decided that v0.1 should define one shared closed-division workload on Llama 3.1 8B so systems running the same model can be compared directly. Its inputs match `sash-l31-8b-c1024` identically (same repository, revision, files, digest, tokenizer, corpus, precision, and shape). Multiple workloads may reference the same pinned files because `model.digest` identifies the file set rather than the workload, and model fetch verifies it identically. Even with matching inputs, a closed workload is distinct from its native counterpart: its rows are compared only within the closed workload and never mixed with native rows (INV-WL-5).

Rationale for these defaults (Q8 and Q9):

- **Claim class.** Uses SASH's claim class because SASH is currently the only system with an adapter running Llama 3.1 8B. Systems with a different claim class can still run this model in an open workload (FlashProve's class, for instance, is `next-token/exact-match/committed-weights`).
- **Precision.** Uses W8A8, the precision SASH proves. None of the other systems surveyed for this decision states W8A8 support for Llama 3.1 8B ([`workloads/README.md`](../workloads/README.md#which-systems-sources-name-the-model)).
- **Shape.** Uses the shorter of SASH's two native shapes. Upstream SASH does not publish a run at this shape ([`systems/sash/README.md`](../systems/sash/README.md#the-two-v01-shapes)), so the adapter derives the segment grid from the shape.

For each system listed on the site, `workloads/README.md` documents the sources checked at a full commit and notes what they state (or leave `"not stated"`) regarding Llama 3.1 8B, precision, and claim class. Additional systems join via pull requests to this repository, never by patching upstream code (RFC-0005).

### Prompt corpus

`workloads/prompts/corpus.yaml`, validated against `schema/corpus/1.schema.json`:

```yaml
schema: corpus/1
normalisation: {unicode: NFC, newlines: LF, strip_bom: true}
texts:
  - id: <short id>
    source_url: <URL of the plain-text file>
    licence: <statement, e.g. "public domain in the United States">
    sha256: <64-hex of the downloaded bytes>
    bytes: <integer>
```

The corpus digest is the SHA-256 over `<id>\t<sha256>\n` lines sorted by `id` bytes. Running `iproofs prompts build` downloads the source texts once, checks their hashes, applies normalisation, and caches them outside the repository. Because every workload draws from the same corpus, prompt token lengths vary only according to each model's tokenizer.

### Prompt generator `corpus-window/1`

Inputs: the normalised corpus texts ordered by `id`, the workload's tokenizer file, `count`, `L = prompt_tokens`, and a 64-bit unsigned integer `seed`.

```python
def corpus_window_v1(texts: list[str], tokenizer: Tokenizer, count: int, L: int, seed: int) -> list[list[int]]:
    # Concatenate with a single LF between texts, then tokenise once without special tokens.
    ids = tokenizer.encode("\n".join(texts), add_special_tokens=False).ids
    N = len(ids)
    if N < L:
        raise ConfigError("corpus shorter than prompt length")
    rng = random.Random(seed)            # Mersenne Twister, seeded from the integer
    prompts = []
    for _ in range(count):
        r = rng.random()                 # the only method CPython guarantees stable across versions
        offset = math.floor(r * (N - L + 1))
        prompts.append(ids[offset:offset + L])
    return prompts
```

Generator rules:

1. Call `random.Random(seed).random()` exclusively. Methods such as `randrange`, `choice`, and `shuffle` are avoided because CPython does not guarantee their output sequences across Python releases.
2. The generator inserts no special tokens (such as BOS tokens or chat templates). If an upstream prover requires a BOS token, its adapter prepends one and documents the behaviour in its README; `prompt_tokens` counts only the generator's tokens, while the adapter accounts for any added tokens in `tokens_covered` (RFC-0004).
3. The generated prompts are serialized to `prompts.jsonl` (one JSON array of token IDs per line in generation order) using the canonical JSON writer (RFC-0012), with the prompt set digest computed as `sha256:` over the file bytes.
4. The generator identifier is versioned; any algorithmic change requires bumping to `corpus-window/2` and incrementing the workload version.

INV-WL-2: given the same corpus digest, tokenizer hash, `count`, `L`, and `seed`, `prompts.jsonl` is byte-for-byte identical across machines and across Python 3.12 and 3.13.

### Seed policy

- **Measured jobs (INV-WL-3).** At job startup, during the `resolved` state prior to `info` (RFC-0010), the harness draws `seed = int.from_bytes(os.urandom(8), "big")` and logs both the seed and the resulting prompt set digest (`workload.prompt_seed`, `workload.prompt_set_digest`, RFC-0014). Drawing a fresh seed for every job ensures provers cannot precompute proofs.
- **Replay jobs.** Invoking a rerun with `--prompts-from` replays the original run's recorded seeds (RFC-0010), allowing direct comparison of proof digests and verification outcomes.
- **Control jobs.** Negative controls reuse the honest run's prompts, deriving any control-specific positions or bit offsets from the suite's own recorded `control_seed` (RFC-0008).
- Running `iproofs prompts build WORKLOAD --seed SEED` outputs the prompt digest so anyone can verify a recorded prompt set without running a prover.

### Model fetch and hash rule

1. `iproofs fetch-model WORKLOAD` downloads every file listed in `model.files` from `model.source` at `model.revision` into an external cache directory outside the repository.
2. Each downloaded file's SHA-256 hash and byte size are verified against the workload definition, after which `model.digest` is recomputed and verified (INV-WL-1).
3. Any hash or size mismatch raises an `integrity` error before `info` runs; no container sees the files, and the failure is recorded.
4. Network fetch failures retry up to 3 times with backoff intervals of 2 s, 8 s, and 32 s (RFC-0010), always outside timed scopes.
5. For gated models, runners accept the model licence using their own account and supply credentials via `HF_TOKEN`, which is never logged or written to any artifact (RFC-0010 redaction).
6. The verified model directory is mounted read-only at `/models` inside every prover container.

For prover-side negative controls requiring perturbed weights (RFC-0008), the harness creates the perturbed copy locally from the verified files, assigns it its own digest, and keeps it strictly separate from the workload's `model.digest`.

### Tokens covered

Each system declares in both `system.yaml` (RFC-0005) and its claim card (`coverage.tokens_covered`) how many tokens one proof covers as a function of the workload shape. The harness calculates the expected `tokens_covered` per proof from that declaration and cross-checks it against the adapter's reported `tokens_covered` in `prove`'s `out.json` (RFC-0005); any discrepancy fails the job with kind `adapter`.

- Next-token prefill proofs (FlashProve): covers the input window positions, `prompt_tokens` per request.
- Segment grids (SASH): covers all positions in the grid, `prompt_tokens + output_tokens` per sequence, as declared by the adapter from upstream documentation.

RISK: SASH's segment grid does not map cleanly onto per-request proofs. If an adapter cannot determine tokens covered as a function of the shape from upstream documentation, `tokens_covered` is recorded as null with `null_reason: missing_input` and per-token metrics are omitted. For SASH, the adapter confirmed the grid geometry from upstream documentation at the pin (Q4).

### Divisions

- **Native.** Runs on each system's own supported model and shape. Rows from different native workloads appear side by side with normalised metrics (RFC-0004) but are never presented as head-to-head comparisons (INV-WL-5); the site places different native workloads in separate tables with claim cards preceding them.
- **Closed.** A shared workload tied to a single `claim_class`. Only systems whose claim card matches that exact class may compete. At job resolution, the runner loads the card referenced by the manifest (`claims/default.yaml`, falling back to `claim.yaml`; because v0.1 jobs do not specify a configuration name, cards under other configuration names are not consulted), raising a `config` error before starting any container if the class mismatches or no card exists. Release freeze checks the class again and verifies the system count (§Choosing common workloads). Reference systems have no claim card (RFC-0015) and run on every workload. Rows within a single closed workload are directly comparable. On the site, a closed workload appears in its own table after the model's native tables under a heading naming the workload, division, and profile, without the native banner (RFC-0009 S6).
- **Open.** Any declared workload outside the registry or any system running a closed workload under a different claim class. Open workloads appear in their own tables, mirroring closed tables.

v0.1 defines native workloads plus one closed workload (`l31-8b-c1024`, §Closed workloads) and no open workloads.

### Choosing common workloads

A common workload's results enter a release once at least two proving systems run it through their adapters without patching upstream code. When selecting common workloads, the project prefers: first, a small dense standard-architecture transformer with public weights that every prover can run; second, a mid-size open model in the 7B to 9B range supported by at least two provers; third, a mixture-of-experts model once at least two provers support one. Every common workload specifies a single `claim_class`.

A common workload file may be merged into the repository ahead of time (as with `l31-8b-c1024`), but its rows remain excluded from releases and the site until a second matching system runs it (Q7). `iproofs release freeze` enforces this gate: if the kept runs for a closed workload contain completed runs from fewer than two distinct proving systems matching the workload's exact `claim_class`, or include any proving configuration with a different class, the freeze exits with a `config` error naming the workload (RFC-0009 §Freeze algorithm, step 4). Future common workloads follow the same rule.

### Failure modes

| Failure | Response |
|---|---|
| Weight file hash mismatch | `integrity` error before `info`; job recorded as failed with no retry |
| Model revision removed upstream | `fetch` error after 3 retries; workload marked unavailable in the release report; moving to a new revision requires a new workload version |
| Corpus text hash mismatch | `integrity` error in `prompts build`; no job starts |
| Corpus shorter than `prompt_tokens` | `config` error at load |
| INV-WL-4 violated | `config` error at load |
| `precision.weight_bits` with `basis: file_size` naming a file outside `model.files`, or supplying a literal `bits` value (WB-2) | `config` error at load |
| Repetitions of the same configuration record different weight bits or parameter counts (WB-4) | Release freeze aborts with an error naming the conflicting runs; changing inputs requires a new workload version |
| `precision.weight_bits` omitted (WB-3) | Workload loads normally; RFC-0004 D-SPAB-S evaluates to null with `missing_input` |
| A `computed` weight width fails to reproduce in binary64 from verified files/headers, or counted active/total weights fall outside stated precision bounds (WB-5) | `config` error in `fetch-model` (with or without `--headers-only`) and in CI recomputation; verified files remain cached since their digests matched |
| A GGUF tensor uses an unknown ggml type or an unrecognised expert layout (WB-5) | `config` error; width is not computed, and the workload retains its previous basis until an amendment adds support |
| A GGUF header fails offset tiling, leaves trailing bytes past aligned EOF, or has a non-power-of-two UINT32 `general.alignment` (WB-5) | `integrity` error |
| Tokenizer produces different IDs under a different library version | Prompt digest mismatches the recorded digest; reproduction fails the digest check and reports it; the `tokenizers` version is recorded in the manifest |
| Adapter's reported `tokens_covered` disagrees with the workload declaration | `adapter` failure; no per-token metrics emitted |
| Closed workload invoked with a mismatched claim class or a prover lacking a card | `config` error at job resolution before any container starts; run is rejected or moved to the open division by its submitter |
| Release includes completed runs on a closed workload from fewer than two matching proving systems (Q7) | `config` error at release freeze naming the workload; the release PR must either drop those runs or wait for a second system |

## Alternatives Considered

- **A single fixed public prompt file per workload.** Simplest for reproduction, but rejected because it lets provers precompute proofs ahead of time. Pairing a pinned corpus with a fresh recorded seed preserves exact replayability while preventing precomputation.
- **Secret prompts held privately by maintainers.** Strongest anti-caching defence, but rejected because outside runners could not regenerate inputs, conflicting with N1 reproducibility.
- **Random synthetic token IDs.** Requires no corpus, but rejected because random token sequences produce unrealistic attention and activation distributions that can skew data-dependent provers.
- **Forcing both systems onto one shared model immediately.** Rejected because doing so would require modifying prover source code, violating RFC-0005.
- **Using NumPy or PCG64 to sample offsets.** Offers stronger statistical stream properties, but rejected to avoid adding a dependency for a single RNG call when CPython already guarantees stability for `random.Random.random()`.
- **Hashing the model directory only as one archive.** Rejected because per-file hashes pinpoint corrupted files and allow adapters to read subsets of files while still verifying every file.

## Drawbacks

- Drawing fresh seeds means consecutive runs prove different prompts, folding prompt-to-prompt variance into run-to-run variance. For fixed-length workloads this variance should be small and is captured by the summary statistics.
- Gated model licences require every reproducer to accept upstream terms on their own account.
- Downloading and hashing full-size Maverick weights takes significant bandwidth and disk space on every new host.
- Selecting a specific text corpus is inherently a judgement call, and a different corpus could slightly shift runtimes for data-dependent provers.

## Migration / Rollout

1. Land `workload/1` and `corpus/1` schemas with examples, the loader enforcing INV-WL-4, and prompt generator tests against a toy tokenizer fixture.
2. Add the four v0.1 workload files with pinned revisions and hashes, create `corpus.yaml`, and verify `fetch-model` and `prompts build` on real models.
3. Preserve earlier shape fields (prompt length, output length, batch size, context window) and add `batches_per_session`. Because no results existed yet, no relabelling was necessary.
4. The 2026-11-08 amendment adds `precision.weight_bits` (§Weight bits) to supply RFC-0004 D-SPAB-S (following the owner's 2026-11-08 decision that prover time per bit of active weights and overhead against plain serving are the two cross-model comparison figures). Because the field is optional, `workload/1` stays at major version 1 (RFC-0012); every file in `workloads/` gains the field with its source without bumping workload versions (WB-4). Existing stored runs in `results/v0.1` remain untouched (APP-1): they lack `run.json` `inputs`, so releases resolve their D-SPAB-S from the workload file at the release commit (RFC-0004 Q3). Following review, the amendment also adds `covers`, makes the loader compute `file_size` widths dynamically instead of validating a typed value, adds optional `run.json` `inputs` (`run/1`, RFC-0012) along with the WB-4 versioning rule, and resolves Q6 via RFC-0007 rule 1.
5. Issue #334 introduces `l31-8b-c1024` as a closed workload, enforces claim-class checks at job resolution, and blocks release freeze for closed workloads with fewer than two matching systems. No system lists it in `system.yaml` initially; SASH adds it with an updated adapter image, and additional systems join through their own pull requests.
6. The second 2026-11-08 amendment resolves Q5 by introducing `basis: computed` (WB-5), the pure-Python `gguf-active-mean/1` reader (`iproofs.gguf`, requiring no new dependencies), the optional `method` field in `precision.weight_bits` (keeping `workload/1` at major version 1), verification hooks in `iproofs fetch-model` and `--headers-only` (RFC-0010), and stored Maverick GGUF headers for CI. The Maverick workloads update from `4.5` (`stated`, `part`) to `4.83916475612899` (`computed`, `all`) while remaining at version 1 since no run had recorded weight bits yet (WB-4); SASH workloads and `l31-8b-c1024` remain unchanged.

Amendment of 2026-11-09 (RFC-0015 SRV-6 production serving): leaves all rules and workload versions in this RFC unchanged. Production-serving weights are pinned separately under `workloads/serving/<id>.yaml` (`serving-model/1`), leaving existing workload digests and stored run inputs intact.

## Testing Strategy

- `test_generator_golden`: given a tiny fixed corpus, stored toy `tokenizer.json`, `seed=0`, `count=3`, and `L=8`, verifies output matches the committed golden `prompts.jsonl` and digest.
- `test_generator_stable_across_python`: runs the golden test in CI on both Python 3.12 and 3.13.
- `test_generator_offset_bounds` (Hypothesis property test): across arbitrary `N >= L >= 1` and seeds, checks that every sampled offset lies in `[0, N - L]` and every prompt has exact length `L`.
- `test_generator_seed_sensitivity`: confirms seeds 0 and 1 produce distinct prompt sets on the fixture.
- `test_generator_only_random_method`: AST check confirming the generator module imports only `Random` from `random` and calls only `.random()`.
- `test_corpus_too_short`: confirms `L > N` raises `config`.
- `test_inv_wl4`: confirms `count != batch_size * batches_per_session` fails at load time.
- `test_model_hash_mismatch`: flips one byte in a fixture model directory and confirms `integrity` is raised without invoking the container runner (verified via mock).
- `test_model_digest_order`: confirms the computed model digest does not depend on filesystem directory listing order.
- `test_fresh_seed_recorded`: verifies two fake-system jobs draw distinct seeds and that replaying one seed reproduces its exact prompt digest.
- Weight bits (`test_workload.py`): `test_weight_bits_stated` (WB-1 loads verbatim with `covers: part`), `test_weight_bits_absent` (valid when omitted; run input becomes null `missing_input`), `test_weight_bits_file_size` (hand-computed fixture: 64 B across 16 parameters computes 64 × 8 / 16 = 32), `test_weight_bits_file_size_typed`, `test_weight_bits_file_size_unknown_file`, `test_weight_bits_file_size_needs_files` (WB-2), and `test_asserted_inputs` (WB-4 confirms run inputs are schema-valid asserted quantities pointing at the workload record).
- WB-5 (`test_gguf.py`): `test_read_header` and `test_active_mean_bits_hand_computed` on a synthetic 5-tensor GGUF (Q4_K, Q8_0, a 4-expert Q4_K routed tensor with 1 active expert, Q6_K shared expert, and F32, giving 7,248 bits / 1,184 active weights = 453 / 74 by hand); `test_dense_model_counts_every_tensor`, `test_split_model_across_files`, `test_small_chunks_read_the_same`, `test_custom_alignment`, `test_malformed_header`, `test_truncated_header`, `test_layout_checks_the_type_table`, `test_unknown_type_and_block_multiple`, `test_method_refuses_what_it_does_not_define`, `test_http_source` (valid HTTP 206 matching listed size, wrong status or size, unreachable host, short read); `test_maverick_record_recomputes_from_stored_headers` (both Maverick records match recomputation over stored headers with active weights within 17e9 plus or minus 5e8); `test_stated_tolerance`; `test_computed_bits_mismatch_is_config`; `test_fetch_model_rechecks_a_computed_width` (both fresh download and cached, verifying a mismatched record raises `config` without quarantining valid files); `test_cli_headers_only`. Loader tests: `test_workload.py::test_weight_bits_computed`, `test_weight_bits_computed_unknown_file`. Schema examples: `valid/weight-bits-computed.yaml`; `invalid/weight-bits-computed-no-method.yaml`, `invalid/weight-bits-computed-part.yaml`, `invalid/weight-bits-computed-unknown-method.yaml`, `invalid/weight-bits-stated-with-method.yaml`.
- WB-4 (`test_runner.py::test_g4_survives_a_weight_bits_correction`): executes a fake run, changes the workload's weight bits from 8 (`file_size`) to 4 (`stated`), and verifies G4 still passes on the stored run. `test_freeze.py::test_freeze_stops_on_different_workload_inputs`: verifies two repetitions with differing recorded inputs abort freeze.
- `test_closed_workload_loads`: confirms `l31-8b-c1024` loads as closed with its claim class and matches `sash-l31-8b-c1024`'s model, shape, and precision; `test_closed_workload_needs_class` confirms a closed workload without `claim_class` fails at load.
- `test_closed_workload_class_mismatch` (runner): verifies a job with a mismatched card class or missing card aborts at resolution with `config` before starting a container, a matching card runs, and reference systems bypass the check; `test_closed_workload_reads_the_card_a_job_records` confirms `claims/default.yaml` is read while a system offering only `claims/<other>.yaml` is rejected.
- `test_freeze.py::test_closed_workload_needs_two_systems` (hand-constructed counts: two systems, one system twice, zero systems, mismatched card class, missing card) and `::test_closed_workload_of_one_system_stops_freeze` (confirms a site test release missing its second prover fails freeze).
- Schema examples: `valid/sash-l31-8b-c4096.yaml`, `valid/closed-with-class.yaml`, `valid/weight-bits-file-size.yaml`; `invalid/branch-revision.yaml` (`revision: main`), `invalid/sampled-decoding.yaml`, `invalid/closed-without-class.yaml`, `invalid/weight-bits-zero.yaml`, `invalid/weight-bits-over-64.yaml`, `invalid/weight-bits-unknown-basis.yaml`, `invalid/weight-bits-no-source.yaml`, `invalid/weight-bits-no-covers.yaml`, `invalid/weight-bits-file-size-without-files.yaml`, `invalid/weight-bits-file-size-typed.yaml`, `invalid/weight-bits-file-size-part.yaml`, `invalid/weight-bits-stated-with-files.yaml`, `invalid/context-too-small.yaml` (not expressible in JSON Schema, verified by loader test `test_context_window_check`).

## Decisions

- Q1. The prompt corpus consists of eight Project Gutenberg plain-text eBooks in the public domain in the United States, listed with URLs and SHA-256 hashes in [`workloads/prompts/corpus.yaml`](../workloads/prompts/corpus.yaml), with selection criteria and licensing documented in [`workloads/prompts/README.md`](../workloads/prompts/README.md). Corpus digest: `sha256:cedd5c414e7c70b99348140c4ddfde8754446c3d3085f77d5d29a4e7324f639a`.
- Q2. The mid-size common model is Llama 3.1 8B, defined in the closed workload `l31-8b-c1024` (§Closed workloads). Among systems listed on the site, only SASH currently has an adapter running it at the reviewed pins. Four other systems mention it in their sources: TOPLOC's paper and experiments (bfloat16), Verde's paper (FP32), Private ML SDK's vLLM service and end-to-end test at its pin (precision not stated), and zkPyTorch's paper, which mentions "Llama-3 (8B parameters)" without public code ([`workloads/README.md`](../workloads/README.md#which-systems-sources-name-the-model)). None of those four yet has a claim card matching the workload's class.
- Q3. Decode-heavy workloads (long generated outputs) do not receive a separate workload family in v0.1.
- Q4. Each SASH segment grid proves every prompt and continuation position in its sequence (the published 4,096 + 512 run consists of 9 blocks of 512 positions across 32 layers plus 2 head segments, totalling 290 segments), making `tokens_covered` equal to `prompt_tokens + output_tokens` per sequence for both shapes. Upstream does not specify a grid geometry for 1,024 + 64, and the token count does not depend on it. Sources at the pinned commits: [`systems/sash/README.md`](../systems/sash/README.md#grid-geometry-and-proof-release).
- Q5. Whenever pinned model files store weights at the proved precision, the workload records a width computed directly from the files so RFC-0004 D-SPAB-S uses one consistent convention and can be sorted. This uses `basis: computed` (WB-5) with `gguf-active-mean/1`: the mean storage bits per active weight across the pinned GGUF files including block scales, with routed experts weighted by `expert_used_count / expert_count` and cross-checked against the model card's active count. The Maverick workloads record `4.83916475612899` bits with `covers: all` (§v0.1 values), superseding Unsloth's stated `4.5` (`covers: part`), while staying at version 1 because no prior `results/v0.1` run recorded `inputs` (WB-4). SASH workloads and `l31-8b-c1024` retain `8` (`stated`, `covers: part`) because their pinned files are BF16 quantized at load time rather than int8 on disk. Their D-SPAB-S rows remain excluded from sorting (RFC-0004 INV-DERIVE-7) for three reasons: SASH's documentation covers weight matmuls only and states no width for embeddings or RMSNorm weights; its `8` omits per-channel scales whereas WB-5 includes block scales, so sorting them together would compare mismatched conventions; and no file-header reader can compute a proved width absent from the stored files. Computing a width from SASH's quantizer inside the harness would infer an unstated property, violating AGENTS.md rule 9.
- Q6. Adding `precision.weight_bits` changes a workload file's `file_digest` (WB-4), which manifests continue to record. Only changes that alter actual job inputs increment the workload version (§Workload file).
- Q7. `l31-8b-c1024` follows the two-system publication rule: its rows are withheld from releases until a second system matching its claim class runs it via an unpatched adapter. `iproofs release freeze` enforces this gate (§Choosing common workloads); site layout tests include a second fixture-only prover with the matching class so their test release passes freeze.
- Q8. `l31-8b-c1024` pins the claim class `greedy-continuation/exact-match/committed-weights`, matching SASH's claim card.
- Q9. `l31-8b-c1024` inherits the precision and shape of `sash-l31-8b-c1024` (W8A8; 1,024 + 64 tokens, batch size 1). Its `precision.weight_bits` likewise uses `8` from SASH's quantizer (WB-1, `covers: part`) until a second system running `l31-8b-c1024` documents a different W8A8 weight width, at which point updating it will increment the workload version (WB-4).

## References

- [docs/PRD.md](../docs/PRD.md), sections 2, 6, 7 (F2) and 10.
- Python `random` module documentation, reproducibility notes (stability of `random()` across versions).
- Unicode Standard Annex 15, normalisation form C.
- [RFC-0002](0002-claim-card.md) (claim class), [RFC-0004](0004-metrics-timing-grades.md) (tokens covered in metrics), [RFC-0005](0005-adapter-contract.md) (adapter declarations), [RFC-0007](0007-evidence-tiers-and-reproduction.md) (seed replay), [RFC-0008](0008-negative-controls.md) (perturbed weights), [RFC-0012](0012-schemas-and-serialization.md) (digests, canonical JSON), [RFC-0015](0015-reference-rows.md) (reference systems; production-serving weights: SRV-6, `workloads/serving/`).
