Every system on the ladder faces the same request, passes through the same six checks, and is ranked by one cost figure. Here is how each step works in visual form; the full rules live on the [Checks](/checks) page.

## The request

:::figure request
Prompts are taken from public-domain books using a seed from a [public randomness beacon](https://docs.drand.love/) published after the [level](/mandate#level) was frozen, so nobody hand-picked them. At each step of generation, the model selects its single highest-scoring token. This is [[greedy decoding]], which gives each prompt one deterministic reply.
:::

## Commit, prove, verify

:::figure flow
The prover keeps the [[weights]]. The [[verifier]] receives only the [[commitment]], the prompt, the reply, and the proof. Keeping the weights off the verifier does not by itself guarantee they stay secret: SASH makes no weight-hiding claim, and FlashProve proves [[zero knowledge]] for its abstract protocol rather than for the C++ and CUDA programs we run ([Confidentiality](/checks#weights_hidden)). When a proof is accepted, it asserts that the reply is the greedy output of the committed copy of the model. That claim is [the statement](/statement).
:::

## Six checks

Every check runs the publisher's own prover honestly at its [[pinned commit]]. Three of the checks tamper with one input and check that the verifier rejects it. Because each tampered test starts from an honest prover run rather than an adversarial forgery attempt, passing them does not prove that forgery is impossible. That guarantee rests on the [[soundness]] bound the publisher states, which the [Integrity](/checks#unforgeable) petal grades.

:::figure checks
A system passes on a model when all six checks pass. A check that has not run yet, or whose run did not produce a countable result, stays not decided rather than passing or failing.
:::

## The figure

Within a model rung, the ladder ranks systems that passed by a single number: **cost vs serving**. It divides the GPU time required to generate and prove one reply by the GPU time required to serve the same reply without a proof.

:::measured fraction
Both sides are measured in GPU-seconds per reply on the same type of GPU. On the proving side, we count the whole [[session]], from the start of the commit call to the release of the last proof (excluding model loading before commit), and divide by the number of replies proved. On the serving side, we run the model publisher's own release at full load. Systems on different models are never ranked against each other.
:::
