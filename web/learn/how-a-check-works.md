Every system on the ladder gets the same request, the same six checks and one figure. This page draws each step. The [Checks](/checks) page holds the rules word for word.

## The request

:::figure request
The prompts are windows of public-domain books, cut with a seed from a [public randomness beacon](https://docs.drand.love/) drawn after the [level](/mandate#level) was frozen, so no one chose them. [[Greedy decoding]] takes the model's top token at each step, so a prompt has one right reply.
:::

## Commit, prove, verify

:::figure flow
The prover keeps the [[weights]]. The [[verifier]] gets the [[commitment]], the prompt, the reply and the proof, never the weights. An accepted proof says the reply is the greedy reply of the copy the prover committed to ([the statement](/statement)).
:::

## Six checks

Each check runs the publisher's own prover, honestly, at its [[pinned commit]]. Three of them change one thing a verifier must refuse. These are refused changes with the publisher's own prover, not an attempt to forge a proof, so they cannot show that no forged proof exists. That rests on the [[soundness]] the publisher states, which the [Integrity](/checks#unforgeable) petal grades.

:::figure checks
A system passes on a model when all six checks pass there. A check that has not run, or ran and decided nothing, is not decided: neither passed nor failed.
:::

## The figure

The ladder ranks the systems that passed on one model by one figure, cost vs serving: the GPU time of a proved reply over the GPU time of serving the same reply without a proof.

:::measured fraction
Both sides are GPU-seconds per reply on the same type of GPU. A proved reply counts its whole [[session]], from the commitment to the last proof, start-up included, over the replies it proved. Serving runs the model publisher's own release at full load. Systems on different models are never ranked against each other.
:::
