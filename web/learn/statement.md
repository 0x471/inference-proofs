Level 1's [[statement]] is that the reply is the committed model's own [[greedy decoding|greedy]] reply to a prompt the verifier is given ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#site)). A system that proves another statement, such as VerInf, is listed under "a different statement" and has no row.

The verifier never holds the [[witness]] (the weights and every activation). What it is given differs by system, and each system's Statement block lists it with the publisher's words ([FlashProve](/flashprove#statement), [SASH](/sash#statement)). FlashProve's `cp_verify` takes the [[commitment]] and its files from our commit record, and the prompt and the reply from the request. SASH's `boundary-grid --verify` takes the model roots and the grid's link counts from our commit record and the prompt from the request; it reads the reply, and each segment's shape and the switches of its checks, from the proof itself, whose Fixed statement is "[produced at setup, trusted by the verifier](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/compose.rs#L5-L11)". FlashProve claims [[zero knowledge]], [proved for its protocol only and not stated for its programs](/flashprove#glyph), and SASH states no hiding property.

## Each system's statement

One [FlashProve](/flashprove) proof covers one forward pass over the request's 1,024 tokens. Under exact match, a `YES` "[is meant to show that each checked token is the committed integer model's top choice at its position, up to the error bound](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L57-L59)".

One [SASH](/sash) proof covers one segment of a grid: a transformer layer, or the output head, on one block of 512 token positions. SASH's `boundary-grid --verify` exits 0 only when, among other conditions, every segment proof verifies, every implied link "[ran and chained on its own axis](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/boundary.rs#L1120-L1124)" and "[every position's id is the prompt's or the previous position's proved argmax](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/boundary.rs#L1120-L1124)".

## The committed weights

Neither statement says whose weights the commitment holds.

:::quote https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L29-L32 FlashProve, guide/known-limits.md at 9e2bdd8
A yes does not say whose weights they are, that the shipped committer made the commitment, or which real model it is. A provider can commit to any model it likes, a small or degenerate one included, and a scale file within the admitted range can switch off model blocks, up to all of them (worked out by hand).
:::

FlashProve's README says to get the commitment ID from "[a party your user trusts, never from the server being checked or from files sent with the proof](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/README.md?plain=1#L147-L148)". The [[harness]] gives each verify call the commitment it recorded at the commit step.

## Integer arithmetic

Both systems prove a [[quantization|quantized]] copy. FlashProve gives its reason: "[A proof needs exact arithmetic](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L78-L79)".

In SASH, "[Every matmul consumes an int8 activation](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L65-L76)", values between components are bf16, and non-linear functions are [lookup tables keyed by a bf16 value](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/decisions/2026-09-03-bf16-keyed-tables-stay-bf16-keyed.md?plain=1#L1-L10).

Served in floating point, a reply can change with batch size, GPU count or GPU version ([Yuan and others, 2025](https://arxiv.org/abs/2506.09501v2)). With the full configuration recorded, unmodified vLLM and Hugging Face Transformers on NVIDIA GPUs rerun bit for bit, except where a kernel calls atomic functions ([Cankaya, 2026](https://arxiv.org/abs/2606.00279v2), a workshop paper).

Under exact match, a served reply is provable only if every token is the copy's own choice. FlashProve [finds none](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md?plain=1#L35) among 96 stored replies from stock vLLM at 16 bits and 96 at FP8, scored by a Python implementation of the copy, not by a proof.

## Checked tokens

A proof covers only the positions it checks, and in FlashProve "[a reply stopped short verifies as a shorter one](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L51-L52)". The level's [request](/checks#passed) has all 512 reply tokens checked, and both systems run under [[exact match]]. A tolerance would let a dishonest prover [pick among the tokens it admits](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L37-L43).

## The seams

SASH binds the seams between segments: "[The residual stream leaving a segment and the keys and values a block writes are committed as their own trees, and `boundary-grid` compares each such root with the root the consuming segment committed for its input.](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L138-L141)"

Fourteen of the [sixteen edges](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L19-L36) SASH lists can be turned off by an `--unsound-skip-` switch. Our adapter refuses to pass one outside a control job, and the [Run check](/checks#run) fails if one of our counted sessions used one, as its recorded commands show. A switch made by a prover we did not run is another matter: the proof's own Fixed statement carries the switches, the pinned verifier is expected to accept a proof made with one and report the skip, and our verdict does not yet refuse such a proof. Whether SASH's verifier, called as the row calls it, refuses a proof made with one is not yet run.

## The error bound

FlashProve states "[about q/2^124 + 2^-101 after q hash queries](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L46-L47)" for its verifier written in Lean, at exact match and for one proof, among other conditions. It adds that "[N proofs handed in at once under one commitment, or N members of a batch, cost N times that error, taken at the whole list's hash queries; for proofs checked one after another, or members checked in separate sessions, no bound is stated.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L66-L68)"

FlashProve's row proves 24 replies a batch, and the harness checks each alone, so [the bound does not cover the run](/flashprove#glyph). The row also runs the C++ verifier, and "[Neither figure, 124 bits per query or 128 bits per round, is claimed for the C++ programs.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L70)"

SASH's [[security level]] is "[100 conjectured bits](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/util.rs#L11)" per segment proof, and none is stated for the whole grid.

## Claim cards

No maintainer of either system has reviewed its [[claim card]] ([FlashProve](repo:systems/flashprove/claim.yaml), [SASH](repo:systems/sash/claim.yaml)). Under [[residual]], SASH's card reads "not stated", and FlashProve's lists six, among them "[A proof names no client or time.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L54-L55)"
