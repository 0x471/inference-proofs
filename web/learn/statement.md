Level 1 holds every row to the same claim: the reply is the committed model's own [[greedy decoding|greedy]] output for the prompt given to the verifier ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#site)). That claim is the level's [[statement]]. Systems that prove a different statement, such as VerInf, are listed under "a different statement" instead of getting a row on the ladder.

Together, the model's weights and all intermediate activations form the [[witness]], which the verifier never receives. What the verifier does receive varies by system, and each system's Statement section lists every input alongside the publisher's own wording ([FlashProve](/flashprove#statement), [SASH](/sash#statement)). FlashProve's `cp_verify` reads the [[commitment]] and public setup files from our commit record, plus the prompt and reply from the request. SASH's `boundary-grid --verify` reads the model roots and grid link counts from our commit record and the prompt from the request. It extracts the reply, segment shapes, and check switches from the proof file itself, where the proof's `Fixed` statement is "[produced at setup, trusted by the verifier](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/compose.rs#L5-L11)". On weight secrecy, FlashProve claims [[zero knowledge]] [proved for its protocol only, not stated for its programs](/flashprove#glyph), while SASH makes no weight-hiding claim.

## Each system's statement

A single [FlashProve](/flashprove) proof covers one forward pass across all 1,024 tokens of the prompt and reply. Under exact match, a `YES` verdict "[is meant to show that each checked token is the committed integer model's top choice at its position, up to the error bound](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L57-L59)".

A single [SASH](/sash) proof covers one segment of a two-dimensional grid: one transformer layer, or the output head, over one block of 512 token positions. `boundary-grid --verify` exits 0 only when every segment proof verifies, every implied link "[ran and chained on its own axis](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/boundary.rs#L1120-L1124)", and "[every position's id is the prompt's or the previous position's proved argmax](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/boundary.rs#L1120-L1124)".

## The committed weights

Neither system's proof tells you whose weights were committed.

:::quote https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L29-L32 FlashProve, guide/known-limits.md at 9e2bdd8
A yes does not say whose weights they are, that the shipped committer made the commitment, or which real model it is. A provider can commit to any model it likes, a small or degenerate one included, and a scale file within the admitted range can switch off model blocks, up to all of them (worked out by hand).
:::

FlashProve's README warns users to get the commitment ID from "[a party your user trusts, never from the server being checked or from files sent with the proof](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/README.md?plain=1#L147-L148)". Our [[harness]] enforces that rule directly by passing each verification call the commitment it recorded during `commit`.

## Integer arithmetic

Both systems prove a [[quantization|quantized]] copy of the model rather than the original floating-point release. FlashProve summarizes why: "[A proof needs exact arithmetic](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L78-L79)".

In SASH, "[Every matmul consumes an int8 activation](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L65-L76)", values flowing between components are `bf16`, and nonlinear functions use [lookup tables keyed by a bf16 value](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/decisions/2026-09-03-bf16-keyed-tables-stay-bf16-keyed.md?plain=1#L1-L10).

Standard floating-point serving can shift outputs when batch size, GPU count, or GPU model changes ([Yuan and others, 2025](https://arxiv.org/abs/2506.09501v2)). With the full configuration pinned, unmodified vLLM and Hugging Face Transformers on NVIDIA GPUs can reproduce outputs bit for bit except where kernels use atomic operations ([Cankaya, 2026](https://arxiv.org/abs/2606.00279v2), a workshop paper).

Under exact match, a served reply can be proved only if every single token matches the quantized copy's greedy choice. FlashProve's own benchmarks [found zero matching replies](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/performance.md?plain=1#L35) among 96 outputs from stock 16-bit vLLM and 96 from FP8 vLLM (checked using a Python implementation of its integer model rather than full proofs).

## Checked tokens

A proof certifies only the token positions it checks. In FlashProve, "[a reply stopped short verifies as a shorter one](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L51-L52)". Level 1's [request](/checks#passed) requires all 512 reply tokens to be checked, and both systems run under [[exact match]]. Allowing a logit tolerance would let a dishonest prover [choose freely among any tokens inside that margin](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L37-L43).

## The seams

Because SASH splits a forward pass into segments, it binds the seams between them: "[The residual stream leaving a segment and the keys and values a block writes are committed as their own trees, and `boundary-grid` compares each such root with the root the consuming segment committed for its input.](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L138-L141)"

Fourteen of the [sixteen edges](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L19-L36) SASH lists can be disabled with `--unsound-skip-` flags. Our adapter refuses to pass those flags outside control jobs, and the [Run check](/checks#run) fails if any counted session's command line used one. However, an external prover could still build a proof with a skip flag enabled. Because the proof's `Fixed` statement carries those switches, we expect the pinned verifier to accept such a proof while reporting the skip, and our adapter's verdict check does not yet reject that metadata. We have not yet run a trial to test whether SASH's verifier rejects a skipped proof when invoked the way our row calls it.

## The error bound

FlashProve states an error bound of "[about q/2^124 + 2^-101 after q hash queries](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L46-L47)" for its Lean verifier at exact match on a single proof, subject to additional assumptions. It adds: "[N proofs handed in at once under one commitment, or N members of a batch, cost N times that error, taken at the whole list's hash queries; for proofs checked one after another, or members checked in separate sessions, no bound is stated.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L66-L68)"

In our benchmark, FlashProve proves batches of 24 replies and the harness verifies each proof individually, so [the stated bound does not cover the run](/flashprove#glyph). Our row also runs the C++ verifier rather than the Lean verifier, and FlashProve explicitly states: "[Neither figure, 124 bits per query or 128 bits per round, is claimed for the C++ programs.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/what-is-proved.md?plain=1#L70)"

SASH states a [[security level]] of "[100 conjectured bits](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/prover/src/util.rs#L11)" for each individual segment proof, with no combined bound stated for the full segment grid.

## Claim cards

Neither system's maintainers have reviewed its [[claim card]] yet ([FlashProve](repo:systems/flashprove/claim.yaml), [SASH](repo:systems/sash/claim.yaml)). Under [[residual]], SASH's card records "not stated", while FlashProve's card lists six documented limits, including "[A proof names no client or time.](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/known-limits.md?plain=1#L54-L55)"
