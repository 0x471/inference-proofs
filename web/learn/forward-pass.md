Take one reply on Llama 3.1 8B Instruct. Checking it means checking a pass of a [quantized copy](/statement#integer-arithmetic) over the 1,024 tokens of prompt and reply. At two operations per parameter per token, attention aside ([Kaplan and others](https://arxiv.org/abs/2001.08361)), that is about 1.6 × 10^13 operations. A verifier on a CPU does not redo them.

Instead, the prover commits to the weights once and, for each proof, to values of the pass. Then the verifier draws each test point after the prover has committed the values that point tests. Read as polynomials, a pass with one wrong value differs from the honest pass almost everywhere ([Schwartz-Zippel](https://doi.org/10.1145/322217.322225)). So a few points catch it, except with a probability that the [[security level]] bounds.

:::figure pipeline
:::

The three weight products hold most of the arithmetic. [SASH's statement](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L113-L115) says that inside its proofs, "each matmul is a Freivalds check against the committed weights". [FlashProve's guide](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L108-L111) says its [[sumcheck]] and [[lookup argument|lookup arguments]] are designed to reduce the claim of a correct run to a few linear claims, inside a hash-based proof.

## Testing a product at random

A prover claims that C is the n × n product A·B. To test it, the verifier draws a random vector r and compares A·(B·r) with C·r. That takes three matrix-vector products of n² each, where the schoolbook product takes n³. This test is called [Freivalds' algorithm](https://en.wikipedia.org/w/index.php?title=Freivalds%27_algorithm&oldid=1371362986).

:::explore random-check
A draw misses the wrong entry only when r is 0 in that entry's column.
:::

The test runs in a [[field]]. Arithmetic modulo 2^64 is not a field, and there an even entry of r times an error of 2^63 is 0, so the error drops out of C·r.

## Fiat-Shamir

In place of the verifier's draws, each test point comes from a hash of the statement and the prover's messages. This is called [[Fiat-Shamir]]. The problem is a value left out of the hash, because the prover can then change it after the draw. Trail of Bits disclosed this bug in [seven repositories](https://blog.trailofbits.com/2022/04/13/part-1-coordinated-disclosure-of-vulnerabilities-affecting-girault-bulletproofs-and-plonk/) in 2022, and OtterSec in [six zkVMs](https://osec.io/blog/zkvms-unfaithful-claims/) in 2026.

## From one product to a layer

A sumcheck tests an inner product by halving its vectors, one round per halving ([Thaler's book](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html), chapter 4). Each round, the prover sends a degree-2 polynomial s, the sum with the next index bit left as a variable.

:::explore sumcheck
This lie survives 384 of 9,409 pairs of challenges, under the bound 2·2/97.
:::

After the last round, the verifier reads [[multilinear extension|a(r)]] from an opening of the [[polynomial commitment|weight commitment]]. The other factor, b(r), is a claim on the layer before, and it is reduced the same way, down to the input tokens the verifier holds ([GKR](https://doi.org/10.1145/1374376.1374396)). A whole matrix product takes one sumcheck, which costs the prover n² work on top of the product's n³ ([Thaler, 2013](https://eprint.iacr.org/2013/351)).

## Lookups

Steps such as the softmax and the activation curve are not products with the weights. Provers check them against public tables of valid input-output pairs. This is called a [lookup argument](https://eprint.iacr.org/2026/1112).

On GPT-2 (BaseFold, sequence length 512, 48 threads), [DeepProve](https://eprint.iacr.org/2026/1112)'s authors find that "more than 50% of the prover cost comes from activation functions, Softmax, and requantization", in both the interactive proof and the commitments. We did not measure this, because the harness [times each prover from outside](/method).

## One pass for a whole reply

Generating a 512-token reply takes 512 passes in a row, but proving it can take one. DeepProve runs the model once on the prompt and the claimed reply. With the causal mask and a deterministic argmax, "the model's prediction at position `t` certifies the token at position `t+1`" ([its README](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md?plain=1#L21)). FlashProve proves [a window of tokens](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L45) in one pass, and SASH a grid of [segments](/statement#each-system-s-statement) joined at [the seams](/statement#the-seams).

## Zero knowledge

Each opening reveals a linear equation over the weights, so an opening does not hide them. For the [Confidentiality](/checks#weights_hidden) petal, we read what publishers state and prove.

## What an accepted proof rests on

If the verifier accepts a proof, at least one of four things is true: the statement holds, the draws hit a point where two different polynomials agree, an assumption broke, or the verifier has a bug.

[The Ethereum Foundation writes](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations) that many STARK-based zkEVMs rely on [[conjectured|conjectures]]: "Each conjecture that falls takes bits of security with it: what was advertised as 100 bits might actually be 80." No test tells 60 bits from 128 short of a 2^60 search, so for the [Integrity](/checks#unforgeable) petal we read [the bound each publisher states](/statement#the-error-bound).
