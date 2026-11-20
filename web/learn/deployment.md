A cloud customer and its operator can trust the GPU's maker, and a company and its auditor can trust a locked server rack. But two states that expect each other to cheat may trust no hardware they share.

## Rerun, enclave or proof

| Way | Needs | Trusts | Cost | Today |
|---|---|---|---|---|
| [[recomputation|Rerun the model]] | The weights and GPUs | The machine running it again | One more run per reply checked | Anthropic's [prototype](https://www.anthropic.com/research/provable-inference), which "recomputes inference on a trusted server" |
| [[trusted execution environment|Trust an enclave]] | The chip maker's key, the expected measurement | The chip maker, and the server's physical security | First-token latency 9 to 16 % longer, throughput 2.88 % lower at 64 concurrent requests and 15.38 % lower at one ([Cai and others, 2025](https://arxiv.org/abs/2504.04715v2): Llama 3 8B, one H100) | Intel, AMD and Nvidia server chips |
| [[proof of inference|Check a proof]] | The commitment and the verifier | Cryptographic assumptions, the verifier's code, whoever supplies the commitment, sometimes a third party | A [large multiple](/) of serving to prove, CPU time to verify | [Research prototypes](/proof-of-inference#today-s-systems), such as SASH and Anthropic's FlashProve |

The authors of [TEE.fail](https://tee.fail/) forged [[attestation|attestations]] of Intel's CPU enclaves (SGX, TDX) with a memory-bus interposer costing "under $1000" to build. Intel and AMD leave interposer attacks outside their threat models.

The same authors write that "[the fact that Nvidia's attestation reports are not bound to the identity of a specific CVM means we can "borrow" Nvidia attestations from devices that aren't ours](https://tee.fail/)" (a CVM is a confidential virtual machine). So a GPU attestation does not show which machine ran the workload.

:::quote https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note SASH, Towards Proving Frontier-Scale LLM Inference, September 2026
TEEs and activation checks are cheap, and for many settings they are the right tool; TEEs are a sensible starting point for a first agreement. What they cost is trust: in a hardware vendor, in a third party, or in a tolerance. A proof moves that trust into cryptographic assumptions and into code that both sides can read.
:::

## What a relying party supplies

The verifier checks a proof against inputs it takes as given. For each system on the ladder, we print the claim card's words on each input, linked to the publisher's line at the row's commit:

:::measured supplies
:::

## In an agreement

Take a hypothetical bilateral AI agreement between the United States (US) and China, under which declared data centres in both countries serve only models whose [[commitment|commitments]] are in a shared register. An inspectorate that both countries agree on holds the register and checks an [[operator]] in either country, and the operator keeps its weights. This is an illustrative scenario, not a description of an existing deal.

With accepted proofs and a trusted traffic record, the inspectorate could sign one finding: each sampled reply is what the registered quantized copy gives for its recorded prompt.

:::stage measured This reply is what the registered model gives
The inspectorate verifies a reply's proof against the registered commitment. But that does not show that the reply came from [live traffic](/proof-of-inference#outside-the-proof), or that the [weights stayed hidden](/checks#weights_hidden). We run this step on open-weights models, with [512-token prompts and replies](/checks#passed).
:::

:::stage demonstrated The model that was evaluated is the model that serves
When evaluation replies and served replies are proved against one commitment, both are what the same weights give. [South and others](https://arxiv.org/abs/2402.02675) proved evaluations of small models this way in 2024. But no proof says whether the evaluation asked the right questions.
:::

:::stage proposed A sample stands for the traffic
A certifier at the boundary of the inspected data centre, in either country, records a fingerprint of every prompt and reply, and it must be trusted. [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) writes: "Nothing yet ties a proof to what the certifier recorded."

Later, the inspectorate draws replies for the operator to prove. SASH's publisher adds that "the draw must be unpredictable to the provider, and the provider must commit to its answers before the draw." By our arithmetic, when both hold, 300 draws catch an unregistered model that serves 1 reply in 100 about 95 % of the time, but one that serves 1 in 10,000 about 3 % of the time.

Any reply may be drawn, so the [[quantization|quantized copy]] must generate every reply. Where a system's page prints a generation [part](/checks#multiple), that part is paid on every reply, drawn or not. Of the "commit and proving" part, only proving shrinks with the sample.
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
