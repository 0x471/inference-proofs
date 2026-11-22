When an [[operator]] tells you which model generated a reply, nothing in the text itself proves it. In summer 2024, [Gao, Liang and Guestrin](https://arxiv.org/abs/2410.20247) tested commercial APIs serving four Llama models and found that "11 out of 31 endpoints serve different distributions than reference weights released by Meta".

A proof of inference narrows that trust gap, one reply at a time. First, the operator computes a short value called a [[commitment]] that locks in the model's [[weights]] without revealing them. Later, when the operator returns a reply along with a proof, a [[verifier]] checks that proof against the commitment and the prompt, then accepts or rejects it.

A commitment alone does not tell you which model it locks in. You still need a model release, an evaluation report, or a public register to connect that commitment to a known model.

:::figure parties
:::

Whoever acts on the verifier's verdict (a customer, an auditor, a regulator, or an inspectorate) decides what an accepted proof is worth. We call that person or organisation the [[relying party]]. Policy documents often call an inspectorate or auditor "the verifier", whereas here the verifier is strictly the software that checks the proof.

## Outside the proof

Even a valid proof leaves important questions unanswered:

- What an operator actually proves in production. Our runs show what each system's prover and verifier did on our benchmark request with the commitment we recorded. They say nothing about what an operator runs on live traffic, where it can execute whatever code it chooses. A relying party has to verify each proof itself ([what a relying party supplies](/deployment#what-a-relying-party-supplies)).
- When, or even whether, the reply was served. A proof generated after the fact shows that the operator holds a model capable of producing that reply, "not that it necessarily served it earlier" ([South and others, 2024](https://arxiv.org/html/2402.02675v2#A1.SS1)).
- Whether the proved model matches the original release. The verifiers on the [ladder](/) check a [[quantization|quantized]] copy of the model ([why](/statement#integer-arithmetic)), and a proof does not tell you how far that copy drifts from the original weights. We measure that drift directly, and the [Fidelity check](/checks#fidelity) filters out copies that degrade too far.
- Replies sampled with randomness. Every proof on the ladder covers [[greedy decoding|greedy]] output, not random sampling.
- What else the hardware did. [Anthropic](https://www.anthropic.com/research/provable-inference), which publishes FlashProve, notes that a proof "does not establish that the hardware is not, e.g., training on the side".
- Whether the model is safe, or how it was trained.
- Everything around the model. A router, an output filter, or a hidden system prompt that the verifier never sees can still alter what the user receives.
- Privacy of the prompt and reply. The verifier has to see both, along with public metadata such as the model's dimensions.
- Secrecy of the weights. Not handing the weights to the verifier does not automatically mean the proof hides them. Each system's [Confidentiality](/checks#weights_hidden) petal tracks what its publisher actually states and proves about weight hiding.
- Whether a proof will show up at all. An operator can stall or refuse to produce one, so a contract or treaty has to specify what happens next.
- Whether anyone can forge a proof. [[Soundness]] depends on cryptographic assumptions (some of them unproven conjectures), bug-free code, and sometimes a trusted setup or party. As [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) notes, "bugs in deployed proof systems have let provers prove false statements before".

## Today's systems

Proving a reply still costs a [large multiple](/) of simply serving it, and verifying a proof is not always faster than rerunning the model on a GPU. The ladder reports both the proving cost and the verification time for every system we ran, along with the reason each other catalogued system was not run.

Both systems currently on the ladder are early prototypes. [FlashProve's README](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/README.md?plain=1#L3) calls it "A research artifact: not maintained, not accepting contributions." [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) describes SASH as an "open-source ZKP prover measurement prototype". Nobody outside this project has rerun our benchmarks yet ([how to check us](/mandate#how-to-check-us)).

Every model on the ladder has open weights, so none of these results measure a closed model.

## Passed

A system is marked Passed when it clears all six of our [checks](/checks#passed). Because [no test](/checks#not-tested) tries to forge a proof or extract weights from one, the [[glyph]] records what each publisher states and proves on those properties.

In our tampering checks, we change one weight for the [Model](/checks#model) check, one prompt token for [Prompt](/checks#prompt), and one reply token for [Reply](/checks#reply). None of those modified inputs may produce an accepted proof, and a trial counts only if the unmodified twin proof is accepted in the same batch. Passing these checks confirms that the verifier caught those specific edits, nothing more. Every counted proof must also be verified with no GPU visible and no model file on the machine ([Verify without weights](/checks#no_weight_file)).
