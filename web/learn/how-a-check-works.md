Every system on the ladder gets the same request, the same six checks and one figure. We draw each step below, and the [Checks](/checks) page holds the rules word for word.

## The request

:::figure request
The prompts are windows of public-domain books, cut with a seed from a [public randomness beacon](https://docs.drand.love/) drawn after the [level](/mandate#level) was frozen, so no one chose them. At each step of the reply, the next token is the model's top token. This is called [[greedy decoding]], and it gives a prompt one right reply.
:::

## Commit, prove, verify

:::figure flow
The prover keeps the [[weights]], and the [[verifier]] gets the [[commitment]], the prompt, the reply and the proof, never the weights. But not being given the weights is not the same as the weights staying hidden, since SASH states no hiding property and FlashProve proves [[zero knowledge]] for its protocol, not for the programs we run ([Confidentiality](/checks#weights_hidden)). An accepted proof says that the reply is the greedy reply of the copy the prover committed to. That claim is called [the statement](/statement).
:::

## Six checks

In each check we run the publisher's own prover, honestly, at its [[pinned commit]]. In three of them we change one thing a verifier must refuse. But each change starts from a run of that same prover, and none is an attempt to forge a proof, so they cannot show that no forged proof exists. That rests on the [[soundness]] the publisher states, which the [Integrity](/checks#unforgeable) petal grades.

:::figure checks
A system passes on a model when all six checks pass there. A check that has not run, or ran without a result that counts yet, is not decided: neither passed nor failed.
:::

## The figure

On one model, the ladder ranks by one figure the systems that passed. That figure divides the GPU time of a proved reply by the GPU time of serving the same reply without a proof. This is called cost vs serving.

:::measured fraction
Both sides are GPU-seconds per reply on the same type of GPU. For a proved reply, we count its whole [[session]], from the start of the commit call to the last proof, and divide by the replies it proved. We do not count loading the model before the commit call. For serving, we run the model publisher's own release at full load. Systems on different models are never ranked against each other.
:::
