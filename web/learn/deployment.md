A cloud customer and its operator can trust the GPU's maker, and a company and its auditor can trust a locked server rack. Two states that expect each other to cheat may trust no shared hardware.

## Rerun, enclave or proof

| Way | Needs | Trusts | Cost | Today |
|---|---|---|---|---|
| [[recomputation|Rerun the model]] | The weights and GPUs | The machine running it again | One more run per reply checked | Anthropic's [prototype](https://www.anthropic.com/research/provable-inference), which "recomputes inference on a trusted server" |
| [[trusted execution environment|Trust an enclave]] | The chip maker's key, the expected measurement | The chip maker, and the server's physical security | First-token latency 9 to 16 % longer, throughput 2.88 % lower at 64 concurrent requests and 15.38 % lower at one ([Cai and others, 2025](https://arxiv.org/abs/2504.04715v2): Llama 3 8B, one H100) | Intel, AMD and Nvidia server chips |
| [[proof of inference|Check a proof]] | The commitment and the verifier | Cryptographic assumptions, the verifier's code, whoever supplies the commitment, sometimes a third party | A [large multiple](/) of serving to prove, CPU time to verify | [Research prototypes](/proof-of-inference#today-s-systems), such as SASH and Anthropic's FlashProve |

[TEE.fail](https://tee.fail/)'s authors forged [[attestation|attestations]] of Intel's CPU enclaves (SGX, TDX) with a memory-bus interposer costing "under $1000" to build. Intel and AMD leave interposer attacks outside their threat models.

:::quote https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note SASH, Towards Proving Frontier-Scale LLM Inference, September 2026
TEEs and activation checks are cheap, and for many settings they are the right tool; TEEs are a sensible starting point for a first agreement. What they cost is trust: in a hardware vendor, in a third party, or in a tolerance. A proof moves that trust into cryptographic assumptions and into code that both sides can read.
:::

## In an agreement

A hypothetical rule: declared data centres in States A and B serve only models whose [[commitment|commitments]] are in a shared register. An inspectorate holds the register and checks State A's [[operator]], which keeps its weights.

Given accepted proofs and a trusted traffic record, the inspectorate could sign one finding: each sampled reply is what the registered quantized copy gives for its recorded prompt.

:::stage measured This reply is what the registered model gives
The inspectorate verifies a reply's proof against the registered commitment. That does not show the reply came from [live traffic](/proof-of-inference#outside-the-proof), or that the [weights stayed hidden](/checks#weights_hidden). We run this step on open-weights models, with [512-token prompts and replies](/checks#passed).
:::

:::stage demonstrated The model that was evaluated is the model that serves
Proved against one commitment, evaluation replies and served replies are what the same weights give. [South and others](https://arxiv.org/abs/2402.02675) proved evaluations of small models this way in 2024. No proof says whether the evaluation asked the right questions.
:::

:::stage proposed A sample stands for the traffic
A certifier at the data centre's boundary, in State A, records a fingerprint of every prompt and reply, and must be trusted. [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) writes: "Nothing yet ties a proof to what the certifier recorded."

The inspectorate later draws replies for the operator to prove. SASH's publisher adds that "the draw must be unpredictable to the provider, and the provider must commit to its answers before the draw." By our arithmetic, when both hold, 300 draws catch an unregistered model serving 1 reply in 100 about 95 % of the time, and 1 in 10,000 about 3 %.

Any reply may be drawn, so the [[quantization|quantized copy]] must generate every reply. Where the ladder prints a generation [part](/checks#multiple), that part is paid on every reply, drawn or not. Of the "commit and proving" part, only proving shrinks with the sample.
:::

:::stage outside The data centre did nothing else
The [AI 2040 verification plan](https://ai-2040.com/supplements/verification-plan) would keep data centres to inference, and currently recommends aiming for "a network-tap and recomputation based approach". [Amodo Design](https://amododesign.com/ai-verification/plan-a-sitrep/) grades the plan's measures: 4 items with an active effort, 6 not started, 7 "Not on track".
:::

:::stage outside Nothing was left undeclared
To find undeclared data centres, a RAND working paper ([Baker and others, 2025](https://arxiv.org/abs/2507.15916)) names chip tracking, satellite images, whistleblowers and national intelligence.
:::

:::reading
- [AI Workload Verification Papers](https://github.com/WHodgkins/AI-Verification-Papers/blob/d57c49060942c17e8a9082e1263b8591c38343ec/README.md), a bibliography built on lists by Will Hodgkins, Mauricio Baker and James Petrie.
:::
