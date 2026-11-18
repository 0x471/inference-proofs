Checking one reply on Llama 3.1 8B Instruct means checking a pass of a [quantized copy](/statement#integer-arithmetic) over the 1,024 tokens of prompt and reply. At two operations per parameter per token, attention aside ([Kaplan and others](https://arxiv.org/abs/2001.08361)), that is about 1.6 × 10^13 operations. A verifier on a CPU does not redo them.

The prover commits to the weights once and, for each proof, to values of the pass. The verifier draws each test point after the values it tests are committed. Read as polynomials, a pass with one wrong value differs from the honest pass almost everywhere ([Schwartz-Zippel](https://doi.org/10.1145/322217.322225)), so a few points catch it, except with a probability the [[security level]] bounds.

:::figure pipeline
:::

The three weight products hold most of the arithmetic. Inside SASH's proofs, "each matmul is a Freivalds check against the committed weights" ([its statement](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L113-L115)). In FlashProve, [[sumcheck]] and [[lookup argument|lookup arguments]] are designed to reduce the claim of a correct run to a few linear claims, inside a hash-based proof ([its guide](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L108-L111)).

## Testing a product at random

To test a claimed n × n product C = A·B, draw a random vector r and compare A·(B·r) with C·r: three matrix-vector products of n² each, where the schoolbook product takes n³ ([Freivalds' algorithm](https://en.wikipedia.org/w/index.php?title=Freivalds%27_algorithm&oldid=1371362986)).

:::explore random-check
A draw misses the wrong entry only when r is 0 in that entry's column.
:::

The test runs in a [[field]]. Modulo 2^64, an even entry of r times an error of 2^63 is 0.

## Fiat-Shamir

[[Fiat-Shamir]] replaces the verifier's draws with a hash of the statement and the prover's messages. A value left out of the hash can then be changed after the draw. Trail of Bits disclosed this bug in [seven repositories](https://blog.trailofbits.com/2022/04/13/part-1-coordinated-disclosure-of-vulnerabilities-affecting-girault-bulletproofs-and-plonk/) in 2022, OtterSec in [six zkVMs](https://osec.io/blog/zkvms-unfaithful-claims/) in 2026.

## From one product to a layer

A sumcheck tests an inner product in one round per halving of its vectors ([Thaler's book](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html), chapter 4). Each round, the prover sends s, the sum with the next index bit as a variable: a degree-2 polynomial.

:::explore sumcheck
This lie survives 384 of 9,409 pairs of challenges, under the bound 2·2/97.
:::

The verifier reads [[multilinear extension|a(r)]] from an opening of the [[polynomial commitment|weight commitment]], and b(r) is a claim on the layer before, reduced the same way down to the input tokens it holds ([GKR](https://doi.org/10.1145/1374376.1374396)). A whole matrix product takes one sumcheck: n² prover work on top of the product's n³ ([Thaler, 2013](https://eprint.iacr.org/2013/351)).

## Lookups

Provers check steps such as the softmax and the activation curve against public tables of valid input-output pairs, with a [lookup argument](https://eprint.iacr.org/2026/1112).

On GPT-2 (BaseFold, sequence length 512, 48 threads), [DeepProve](https://eprint.iacr.org/2026/1112)'s authors find that "more than 50% of the prover cost comes from activation functions, Softmax, and requantization", in both the interactive proof and the commitments. We did not measure this: the harness [times each prover from outside](/method).

## One pass for a whole reply

Generating a 512-token reply takes 512 passes in a row. Proving it can take one. DeepProve runs the model once on prompt and claimed reply: with the causal mask and a deterministic argmax, "the model's prediction at position `t` certifies the token at position `t+1`" ([its README](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md?plain=1#L21)). FlashProve proves [a window of tokens](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L45) in one pass, SASH a grid of [segments](/statement#each-system-s-statement) joined at [the seams](/statement#the-seams).

## Zero knowledge

An opening does not hide the weights: it reveals a linear equation over them. The [Confidentiality](/checks#weights_hidden) petal reads what publishers state and prove.

## What an accepted proof rests on

If a proof is accepted, the statement holds, the draws hit a point where two different polynomials agree, an assumption broke, or the verifier has a bug.

[The Ethereum Foundation writes](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations) that many STARK-based zkEVMs rely on [[conjectured|conjectures]]: "Each conjecture that falls takes bits of security with it: what was advertised as 100 bits might actually be 80." No test tells 60 bits from 128 short of a 2^60 search, so the [Integrity](/checks#unforgeable) petal reads [the bound each publisher states](/statement#the-error-bound).
