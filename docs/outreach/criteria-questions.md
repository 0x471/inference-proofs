# Questions to system teams on Not stated criteria

These messages have not been sent yet. Issue #336 asks each team whose public-source row in [`web/_data/criteria.json`](../../web/_data/criteria.json) contains a "Not stated" cell to document the missing properties in its own public sources. Whoever sends a message should record the date and channel in a public issue. No personal contact details appear in this file (AGENTS.md rule 7); every channel listed below is a public repository, a correspondence line printed on a paper, or a team's website.

Each draft lists the cells that were still "Not stated" as of `date` 2026-11-08 in the criteria file, along with the sources we reviewed. Check the current criteria file before sending any message and drop any question whose cell has already been filled.

How replies are handled under [RFC-0016](../../rfcs/0016-glyph-properties-and-states.md#public-source-rows-public_sources):

- A reply changes a cell's state only once the statement appears in one of the team's own public sources: a file at a specific commit in its repository, its paper, or a page on its domain archived when read (SRC-8, SRC-9). A newly published source takes effect once it is added to the row's `own_sources` list with its `how` entry.
- A private reply or issue comment alone does not update any state (SRC-8; for claim card rows, compare OVR-6). Without a public source, the cell remains "Not stated".
- Reviewers copy the team's exact wording and assign the state according to the property's rules. We never infer or test properties from a reply.
- Questions ask about each system's default configuration, since RFC-0016 evaluates public-source rows for default or expected use (SRC-1). Answers describing non-default configurations are noted as asides and do not change the cell state.
- Any question marked "(Partly cell)" refers to a cell graded Partly under RFC-0016 Q10 (a security level stated without specifying whether it is proven or conjectured), rather than a "Not stated" cell.

The teams with claim cards (FlashProve and SASH) are contacted in #42 rather than here.

## Index

| System | Channel | Cells still Not stated | Send |
|---|---|---|---|
| [Attestable prover](#attestable-prover) | The contact channel on attestable.com | Formally verified | yes |
| [DeepProve](#deepprove) | An issue on `Lagrange-Labs/deep-prove` | Weights hidden, Model bound, Formally verified, Security level, No trusted party | yes |
| [EZKL](#ezkl) | A discussion on `zkonduit/ezkl` (its README directs questions there) | Model bound, Whole output checked, Formally verified, Security level | yes |
| [JOLT Atlas](#jolt-atlas) | An issue on `ICME-Lab/jolt-atlas` | Weights hidden, Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [JSTprove](#jstprove) | An issue on `inference-labs-inc/JSTprove` | Weights hidden, Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [LuminAIR](#luminair) | An issue on `gizatechxyz/LuminAIR` | Weights hidden, Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [NanoZK](#nanozk) | The correspondence address printed on arXiv 2603.18046 | Model bound, Whole output checked, Formally verified | yes |
| [opML](#opml) | An issue on `ora-io/opml` | Weights hidden, Model bound, Formally verified, Security level | yes |
| [Private ML SDK](#private-ml-sdk) | None currently available | Weights hidden, Model bound, Whole output checked, Formally verified, Security level | optional |
| [Remainder (Community Edition)](#remainder-community-edition) | An issue on `worldcoin/Remainder_CE` (not a security report, so do not use SECURITY.md) | Weights hidden, Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [Tinfoil](#tinfoil) | The contact channel listed on docs.tinfoil.sh | Weights hidden, Model bound, Whole output checked, Formally verified, Security level | yes |
| [TOPLOC](#toploc) | An issue on `PrimeIntellect-ai/toploc` | Weights hidden, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [Verde (with RepOps)](#verde-with-repops) | The correspondence address printed on arXiv 2502.19405 | Weights hidden, Model bound, Whole output checked, Formally verified, Security level | yes |
| [zkGPT](#zkgpt) | The correspondence address printed on ePrint 2025/1184 | Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [zkLLM](#zkllm) | The correspondence address printed on arXiv 2404.16109 | Model bound, Whole output checked, Formally verified, Security level, No trusted party | optional |
| [ZKML](#zkml) | An issue on `ddkang/zkml` | Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [zkPyTorch](#zkpytorch) | The contact channel on polyhedra.network, or the correspondence address printed on ePrint 2025/535 | Weights hidden, Model bound, Whole output checked, Formally verified, Security level, No trusted party | yes |
| [ZKTorch](#zktorch) | An issue on `uiuc-kang-lab/zk-torch` | Model bound, Whole output checked, Formally verified, Security level | yes |

## Messages

### Attestable prover

- Channel: the contact channel on attestable.com.
- Where an answer counts: a public page on attestable.com.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For Attestable prover, we reviewed the following source:
>
> - https://attestable.com/blog/proving-llms-scale (read 2026-11-07)
>
> We did not find a statement addressing this question:
>
> 1. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
>
> One additional question would clarify a cell currently marked Partly:
>
> 2. Security level (Partly cell): Your post states that you "uphold 100 bits of security". Is that level proven or conjectured, and does it cover the entire prover?
>
> Could you document the answers on a page on attestable.com, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an email or message reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to an archived page or commit without inferring or testing anything ourselves. Thank you.

### DeepProve

- Channel: an issue on `Lagrange-Labs/deep-prove`.
- Where an answer counts: a file in `Lagrange-Labs/deep-prove` or a new version of ePrint 2026/1112.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For DeepProve, we reviewed the following sources:
>
> - `Lagrange-Labs/deep-prove` at commit `9d1a53e2ef49ffa2c902b8689cd3c58057a4e662`: `**/*.md`, `README.md`, `zkml/README.md`, `docs/src/*.md`, `zkml/docs/src/**/*.md`, `**/*.rs`
> - https://eprint.iacr.org/2026/1112 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 5. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `Lagrange-Labs/deep-prove` or a new version of ePrint 2026/1112, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment or message reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### EZKL

- Channel: a discussion on `zkonduit/ezkl` (its README directs questions there).
- Where an answer counts: a file in `zkonduit/ezkl`.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For EZKL, we reviewed the following sources:
>
> - `zkonduit/ezkl` at commit `e196b111c1bafaa61b92ae431cd3c3fe9371da05`: `README.md`, `docs/advanced_security/*.md`, `ezkl.pyi`, `src/pfsys/srs.rs`, `src/**/*.rs`, `examples/notebooks/*.ipynb`
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers in a file in `zkonduit/ezkl`, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that a discussion reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### JOLT Atlas

- Channel: an issue on `ICME-Lab/jolt-atlas`.
- Where an answer counts: a file in `ICME-Lab/jolt-atlas`.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For JOLT Atlas, we reviewed the following sources:
>
> - `ICME-Lab/jolt-atlas` at commit `329b21efa6f6a74355e6096cf27c3e0cc7dfc226`: `README.md`, `specs/**`, `docs/**`, `AGENTS.md`, `jolt-atlas-core/src/onnx_proof/zk.rs`, `joltworks/src/poly/commitment/**/*.rs`, `**/*.rs`, `**/*.lean`, `**/*.md`
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 6. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `ICME-Lab/jolt-atlas`, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### JSTprove

- Channel: an issue on `inference-labs-inc/JSTprove`.
- Where an answer counts: a file in `inference-labs-inc/JSTprove` or a new version of arXiv 2510.21024.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For JSTprove, we reviewed the following sources:
>
> - `inference-labs-inc/JSTprove` at commit `7c3cbbee83aaa01adde700673f00e317a4e902f9`: `README.md`, `docs/*.md`, `prover/poly_commit/src/**/*.rs`, `rust/jstprove_circuits/src/runner/holographic.rs`, `rust/jstprove_circuits/src/proof_config.rs`
> - https://arxiv.org/abs/2510.21024 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Which polynomial commitment does the default `--curve bn254` run use, and is a numeric soundness level stated for it (proven or conjectured)? We found `PCS_SOUNDNESS_BITS = 128` in `prover/poly_commit/src/lib.rs`, which is read by the Basefold and Orion commitments.
> 6. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `inference-labs-inc/JSTprove` or a new version of arXiv 2510.21024, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### LuminAIR

- Channel: an issue on `gizatechxyz/LuminAIR`.
- Where an answer counts: a file in `gizatechxyz/LuminAIR`.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For LuminAIR, we reviewed the following sources:
>
> - `gizatechxyz/LuminAIR` at commit `9026bd3d0934a35479e6b3b76353a6ac5facd9e8`: `README.md`, `docs/**/*.mdx`, `crates/verifiers/wasm/README.md`, `crates/prover/src/prover.rs`, `crates/verifiers/rust/src/verifier.rs`
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 6. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `gizatechxyz/LuminAIR`, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### NanoZK

- Channel: the correspondence address printed on arXiv 2603.18046.
- Where an answer counts: a new version of arXiv 2603.18046.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For NanoZK, we reviewed the following sources:
>
> - https://arxiv.org/pdf/2603.18046v2 (read 2026-11-08)
> - https://arxiv.org/abs/2603.18046 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
>
> Could you document the answers in a new version of arXiv 2603.18046, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an email reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### opML

- Channel: an issue on `ora-io/opml`.
- Where an answer counts: a file in `ora-io/opml`.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For opML, we reviewed the following sources:
>
> - `ora-io/opml` at commit `2fa43311a4a95bcd96f5092d0a3b34e84da49eb0`: `README.md`, `docs/OPML.md`, `docs/tutorial.md`
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers in a file in `ora-io/opml`, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### Private ML SDK

- Channel: none currently works, because `nearai/private-ml-sdk` is archived so issues and commits are disabled. A message could be sent to an active public repository of the same organisation (such as `nearai/cloud-api`).
- Where an answer counts: none of the listed own sources can accept new statements; a new public source will count once added to the row's `own_sources` list with its `how` entry.
- Optional to send, since no update can land in the row's only current source.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For Private ML SDK, we reviewed the following sources:
>
> - `nearai/private-ml-sdk` at commit `25c25025c556ab2f797eeda3bab433f38a8ffb7a`: `README.md`, `docs/how-cvm-boots.md`, `e2e/README.md`, `vllm-proxy/README.md`, `vllm-proxy/verifiers/README.md`
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers in a public source of yours, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that a message reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### Remainder (Community Edition)

- Channel: an issue on `worldcoin/Remainder_CE` (this is not a security vulnerability report, so do not use its SECURITY.md channel).
- Where an answer counts: a file in `worldcoin/Remainder_CE`.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For Remainder (Community Edition), we reviewed the following sources:
>
> - `worldcoin/Remainder_CE` at commit `5687fe7f3a077c75c374422ef79f22e3860de9c1`: `README.md`, `SECURITY.md`, `prover/README.md`, `ligero/src/*.rs`, `hyrax/src/**/*.rs`, `prover/src/**/*.rs`
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 6. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `worldcoin/Remainder_CE`, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### Tinfoil

- Channel: the contact channel listed on docs.tinfoil.sh.
- Where an answer counts: a page on docs.tinfoil.sh.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For Tinfoil, we reviewed the following source:
>
> - https://docs.tinfoil.sh/verification/attestation-architecture (read 2026-11-08)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers on a page on docs.tinfoil.sh, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that a message reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### TOPLOC

- Channel: an issue on `PrimeIntellect-ai/toploc`.
- Where an answer counts: a file in `PrimeIntellect-ai/toploc` or a new version of arXiv 2501.16007.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For TOPLOC, we reviewed the following sources:
>
> - `PrimeIntellect-ai/toploc` at commit `7ab7bcd6a4459ba4400fd41e4636bbeed7438997`: `README.md`, `CONTRIBUTING.md`, `toploc/*.py`, `toploc/C/csrc/*`
> - https://arxiv.org/abs/2501.16007 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 5. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `PrimeIntellect-ai/toploc` or a new version of arXiv 2501.16007, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### Verde (with RepOps)

- Channel: the correspondence address printed on arXiv 2502.19405.
- Where an answer counts: a new version of arXiv 2502.19405.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For Verde (with RepOps), we reviewed the following sources:
>
> - https://arxiv.org/pdf/2502.19405v1 (read 2026-11-08)
> - https://arxiv.org/abs/2502.19405 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: For inference, does the verifying party learn nothing about the model weights? Section 2 states what the referee holds during training ("the initial parameters") and notes that the techniques extend to inference, but it does not specify what the referee holds for inference.
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers in a new version of arXiv 2502.19405, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an email reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### zkGPT

- Channel: the correspondence address printed on ePrint 2025/1184.
- Where an answer counts: a new version of ePrint 2025/1184.
- Note: the paper names the repository `security-Anonymous/zkGPT`; a statement published there will count only once that repository is added to the row's `own_sources` list with its `how` entry.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For zkGPT, we reviewed the following sources:
>
> - https://web.archive.org/web/20250902071715/https://eprint.iacr.org/2025/1184.pdf (read 2026-11-08)
> - https://eprint.iacr.org/2025/1184 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 5. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a new version of ePrint 2025/1184, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an email reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### zkLLM

- Channel: the correspondence address printed on arXiv 2404.16109. The repository `jvhs0706/zkllm-ccs2024` is archived with issues disabled, and its README notes that the author cannot provide ongoing support.
- Where an answer counts: a new version of arXiv 2404.16109.
- Optional to send: because the repository is archived and unmaintained, updates can arrive only through a new version of the paper.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For zkLLM, we reviewed the following sources:
>
> - `jvhs0706/zkllm-ccs2024` at commit `993311ea8e2346b90efacb35337b2e3cfe0d6f8d`: `README.md`, `*.py`, `*.cu`, `*.cuh`
> - https://arxiv.org/abs/2404.16109 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 5. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a new version of arXiv 2404.16109, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an email reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### ZKML

- Channel: an issue on `ddkang/zkml`.
- Where an answer counts: a file in `ddkang/zkml` or a new version of the paper at https://ddkang.github.io/papers/2024/zkml-eurosys.pdf.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For ZKML, we reviewed the following sources:
>
> - `ddkang/zkml` at commit `43789582671f16148dd02cbac5654f462d4fe3e4`: `README.md`, `examples/nlp/*/README.md`, `backwards/README.md`, `src/utils/proving_kzg.rs`, `src/utils/proving_ipa.rs`
> - https://ddkang.github.io/papers/2024/zkml-eurosys.pdf (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 5. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers in a file in `ddkang/zkml` or a new version of the paper at https://ddkang.github.io/papers/2024/zkml-eurosys.pdf, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### zkPyTorch

- Channel: the contact channel on polyhedra.network, or the correspondence address printed on ePrint 2025/535.
- Where an answer counts: a page on polyhedra.network or a new version of ePrint 2025/535.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For zkPyTorch, we reviewed the following sources:
>
> - https://polyhedra.network/zkPyTorch (read 2026-11-08)
> - https://eprint.iacr.org/2025/535 (read 2026-11-07)
> - https://web.archive.org/web/20260825214632/https://eprint.iacr.org/2025/535.pdf (read 2026-11-08)
>
> We did not find statements addressing these questions:
>
> 1. Weights hidden: In default use, does the verifying party learn nothing about the model weights?
> 2. Model bound: In default use, is every verified output token bound to the committed weights?
> 3. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 4. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 5. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
> 6. No trusted party: In default use, does verification hold without trusting a hardware vendor, a trusted setup ceremony, or an honest party?
>
> Could you document the answers on a page on polyhedra.network or in a new version of ePrint 2025/535, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that a message reply alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.

### ZKTorch

- Channel: an issue on `uiuc-kang-lab/zk-torch`.
- Where an answer counts: a file in `uiuc-kang-lab/zk-torch` or a new version of arXiv 2507.07031.

> Hello. We maintain Inference Proofs, an open benchmark for provable inference (https://github.com/ai-verification-observatory/inference-proofs). Our site displays six properties for each system, filled solely from what the system's own public sources state ([RFC-0016](https://github.com/ai-verification-observatory/inference-proofs/blob/main/rfcs/0016-glyph-properties-and-states.md)). When those sources do not address a property, the site marks it as Not stated.
>
> For ZKTorch, we reviewed the following sources:
>
> - `uiuc-kang-lab/zk-torch` at commit `63b9c68960f3ca84026d89428dd6d8129e930d53`: `README.md`, `test_gpu_scripts/README.md`
> - https://arxiv.org/abs/2507.07031 (read 2026-11-07)
>
> We did not find statements addressing these questions:
>
> 1. Model bound: In default use, is every verified output token bound to the committed weights?
> 2. Whole output checked: Does a single verification check, or a linked set of checks, cover both the prompt and every output token of a request?
> 3. Formally verified: Is the security argument for default use checked in a proof assistant (such as Lean, Coq, or Isabelle)?
> 4. Security level: Is a numeric soundness level stated for default use, and is it proven or conjectured?
>
> Could you document the answers in a file in `uiuc-kang-lab/zk-torch` or a new version of arXiv 2507.07031, or point us to where they are already published? Explicit answers such as "Not provided" or "does not hold" are just as helpful as "holds". Please note that an issue comment alone does not update the site; the statement needs to appear in one of your public sources so we can quote your words directly and link to a commit or archived page without inferring or testing anything ourselves. Thank you.
