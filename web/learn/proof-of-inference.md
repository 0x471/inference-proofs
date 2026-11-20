An [[operator]] says which model wrote a reply, but nothing in the reply shows it. [Gao, Liang and Guestrin](https://arxiv.org/abs/2410.20247) tested commercial APIs serving four Llama models in summer 2024 and found that "11 out of 31 endpoints serve different distributions than reference weights released by Meta".

A proof of inference proves a narrower claim, one reply at a time. First the operator computes a value that fixes the model's [[weights]] without publishing them. This value is called a [[commitment]]. Then the [[verifier]] checks the operator's proof of a reply against the commitment and the prompt, and accepts or refuses it.

But the commitment does not say which model it fixes, so a release, an evaluation report or a register has to tie it to a known model.

:::figure parties
:::

Whoever acts on the verdict (a customer, an auditor, a regulator or an inspectorate) judges what an accepted proof is worth. This party is called the [[relying party]]. Policy writing calls the inspectorate or auditor in that role the verifier, but here the verifier is the program that checks the proof.

## Outside the proof

- What an operator proves in its own deployment. Our runs show what each system's own prover and verifier did on our request, with the commitment we recorded. But they show nothing about the proofs an operator makes of its own traffic, where it runs whatever code it chooses, outside our tests. A relying party checks each proof itself ([what it supplies](/deployment#what-a-relying-party-supplies)).
- When, or whether, the reply was served. A proof made later shows the operator holds a model that gives this reply, "not that it necessarily served it earlier" ([South and others, 2024](https://arxiv.org/html/2402.02675v2#A1.SS1)).
- The model as released. The verifiers on the [ladder](/) check a [[quantization|quantized]] copy ([why](/statement#integer-arithmetic)), and no proof says how far its replies drift from the original's. We measure that drift, and the [Fidelity check](/checks#fidelity) stops a copy quantized far from the original.
- A reply with tokens chosen at random. The ladder's proofs cover the [[greedy decoding|greedy]] reply.
- What else the machines ran. [Anthropic](https://www.anthropic.com/research/provable-inference), which publishes FlashProve, writes that a proof "does not establish that the hardware is not, e.g., training on the side".
- That the model is safe, or how it was trained.
- What surrounds the model. A router, an output filter or a system prompt the verifier is not given can change what a user gets.
- That the prompt and the reply stay private. The verifier reads them and other values, such as the model's sizes.
- That the weights stay hidden. The verifier is not given them, but that is not the same as hiding them, and each system's [Confidentiality](/checks#weights_hidden) petal reads what its publisher states and proves.
- That a proof will arrive. An operator can refuse or stall, and a contract or a treaty has to say what follows.
- That nobody can forge one. [[Soundness]] rests on cryptographic assumptions, some of them conjectures, on code without bugs and, in some systems, on a trusted third party. [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) writes that "bugs in deployed proof systems have let provers prove false statements before".

## Today's systems

Proving a reply costs a [large multiple](/) of serving it, and checking a proof is not always faster than rerunning the model on a GPU. The ladder prints that cost and the verify time of every system we ran, and the reason each other system was not run.

[FlashProve's README](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/README.md?plain=1#L3) calls it "A research artifact: not maintained, not accepting contributions." [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) calls it an "open-source ZKP prover measurement prototype". Nobody else has rerun any of our runs ([how to check us](/mandate#how-to-check-us)).

All the ladder's models have open weights, so nothing here measures a closed model.

## Passed

Passed means all six of our [checks](/checks#passed) passed. But [no check](/checks#not-tested) attempts a forged proof or tests whether the weights stay hidden, and the [[glyph]] grades the publisher's statements on both.

For the [Model](/checks#model) check, we change one weight. For [Prompt](/checks#prompt) we change one prompt token, and for [Reply](/checks#reply) one reply token. No change may end in an accepted proof, and a trial counts only if the same run, unchanged, is accepted. A passed check shows that these changes were refused, and no more. Each counted proof must also be verified with no GPU visible and no model file on the machine ([Verify without weights](/checks#no_weight_file)).
