Consider a single reply from Llama 3.1 8B Instruct. Verifying it means checking a forward pass of a [quantized copy](/statement#integer-arithmetic) across all 1,024 tokens of prompt and reply. At roughly two operations per parameter per token, setting attention aside ([Kaplan and others](https://arxiv.org/abs/2001.08361)), that comes to about 1.6 × 10^13 arithmetic operations. A CPU verifier cannot simply redo all of that work.

Instead, the prover commits to the model weights once up front, and for each reply it commits to the intermediate values of the forward pass. The verifier then chooses random test points after those values are locked in. When intermediate traces are encoded as polynomials, even a single wrong value makes the cheating polynomial disagree with the honest one almost everywhere ([Schwartz-Zippel](https://doi.org/10.1145/322217.322225)). Testing a handful of random points catches almost every lie, up to the small error probability bounded by the system's [[security level]].

:::figure pipeline
:::

The three linear projections with the model weights account for most of the arithmetic. [SASH's statement](https://github.com/sg-ai-safety-hub/zk-inference-prover/blob/4f41667297430a598165c4a8604258fe37d952ae/docs/statement.md?plain=1#L113-L115) explains that inside its proofs, "each matmul is a Freivalds check against the committed weights". [FlashProve's guide](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L108-L111) describes using [[sumcheck]] and [[lookup argument|lookup arguments]] to reduce an entire inference trace to a few linear claims inside a hash-based proof.

## Testing a product at random

Suppose a prover claims that C equals the n × n matrix product A·B. Rather than multiplying A and B directly (n³ work), the verifier picks a random vector r and checks whether A·(B·r) equals C·r. That requires only three matrix-vector products, or O(n²) work. This classical check is [Freivalds' algorithm](https://en.wikipedia.org/w/index.php?title=Freivalds%27_algorithm&oldid=1371362986).

:::explore random-check
A random draw misses the modified entry only when r happens to be 0 in that entry's column.
:::

For this check to work reliably, the arithmetic must live in a [[field]]. Standard 64-bit integer arithmetic modulo 2^64 is not a field: an even entry of r multiplied by an error of 2^63 wraps around to 0, letting the error vanish from C·r.

## Fiat-Shamir

Real inference proofs are non-interactive: instead of waiting for a live verifier to send random challenges, the prover derives each challenge by hashing the statement and all messages sent so far. This is the [[Fiat-Shamir]] transform. The classic implementation bug is forgetting to include a committed value in the hash transcript, which lets a cheating prover adjust that value after seeing the challenge. Trail of Bits disclosed this class of bug in [seven repositories](https://blog.trailofbits.com/2022/04/13/part-1-coordinated-disclosure-of-vulnerabilities-affecting-girault-bulletproofs-and-plonk/) in 2022, and OtterSec found it in [six zkVMs](https://osec.io/blog/zkvms-unfaithful-claims/) in 2026.

## From one product to a layer

The sumcheck protocol verifies an inner product by cutting the vectors in half over a series of rounds ([Thaler's book](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html), chapter 4). In each round, the prover sends a degree-2 univariate polynomial s representing the partial sum with one index variable left free.

:::explore sumcheck
This lie slips past 384 of the 9,409 challenge pairs, safely within the 2·2/97 error bound.
:::

After the final round, the verifier checks [[multilinear extension|a(r)]] by opening the [[polynomial commitment|weight commitment]] at the random point r. The remaining factor, b(r), becomes a claim about the previous layer and is reduced the same way all the way back to the input tokens the verifier already knows ([GKR](https://doi.org/10.1145/1374376.1374396)). Proving a full matrix product takes a single sumcheck, adding only O(n²) prover overhead on top of the n³ multiplication ([Thaler, 2013](https://eprint.iacr.org/2013/351)).

## Lookups

Operations like softmax, RMSNorm, and activation curves are not simple matrix multiplications. Provers check them against public tables of valid input-output pairs using a [lookup argument](https://eprint.iacr.org/2026/1112).

Even though linear layers dominate raw FLOPs, non-linearities often dominate proving cost. On GPT-2 (BaseFold, sequence length 512, 48 threads), [DeepProve](https://eprint.iacr.org/2026/1112)'s authors report that "more than 50% of the prover cost comes from activation functions, Softmax, and requantization" across both the interactive proof and the commitments. Our benchmark does not break out internal prover stages because the harness [times each prover strictly from outside](/method).

## One pass for a whole reply

Generating a 512-token reply requires 512 sequential forward passes, yet proving that reply can happen in one pass. Once the prover already has the full prompt and reply, it runs the transformer across all tokens together. With causal masking and deterministic argmax, "the model's prediction at position `t` certifies the token at position `t+1`" ([DeepProve's README](https://github.com/Lagrange-Labs/deep-prove/blob/9d1a53e2ef49ffa2c902b8689cd3c58057a4e662/zkml/README.md?plain=1#L21)). FlashProve proves [a window of tokens](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L45) in one pass, while SASH proves a grid of [segments](/statement#each-system-s-statement) chained across [the seams](/statement#the-seams).

## Zero knowledge

Committing to model weights (for instance with a [[Merkle tree]] root) binds the prover to those weights, but binding alone does not keep them secret. Each polynomial opening reveals a linear combination of the weights, so hiding the weights requires adding [[zero knowledge]] masking on top. For the [Confidentiality](/checks#weights_hidden) petal, we record what each publisher explicitly states and proves about weight hiding.

Because the verifier only evaluates random test points and checks openings there rather than replaying the forward pass, verification is much cheaper than proving, though its exact speed varies widely by system ([verify time on the ladder](/)).

## What an accepted proof rests on

Whenever a verifier accepts a proof, at least one of four things happened: the statement is true, the random challenges hit a rare point where two distinct polynomials agree, an underlying cryptographic assumption failed, or the verifier has a bug.

As [the Ethereum Foundation warns](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations), many STARK-based zkEVMs rely on unproven [[conjectured|conjectures]]: "Each conjecture that falls takes bits of security with it: what was advertised as 100 bits might actually be 80." Short of running a 2^60 attack, no black-box test can distinguish 60 bits of security from 128, so the [Integrity](/checks#unforgeable) petal grades [the bound each publisher states](/statement#the-error-bound).
