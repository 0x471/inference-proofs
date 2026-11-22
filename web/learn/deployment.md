A cloud customer and its provider might both trust the chip manufacturer, and a company and its auditor might trust a locked server rack. Two countries that expect each other to cheat will usually not trust hardware controlled by the other side.

## Rerun, enclave or proof

| Way | Needs | Trusts | Cost | Today |
|---|---|---|---|---|
| [[recomputation|Rerun the model]] | The weights and GPUs | The machine rerunning the model | One extra forward pass per checked reply | Anthropic's [prototype](https://www.anthropic.com/research/provable-inference), which "recomputes inference on a trusted server" |
| [[trusted execution environment|Trust an enclave]] | The chip maker's signing key and expected measurement | The chip maker and physical security of the server | First-token latency 9 to 16 % longer; throughput 2.88 % lower at 64 concurrent requests and 15.38 % lower at 1 ([Cai and others, 2025](https://arxiv.org/abs/2504.04715v2): Llama 3 8B on one H100) | Intel, AMD and Nvidia server chips |
| [[proof of inference|Check a proof]] | The commitment and the verifier | Cryptographic assumptions, the verifier's code, whoever supplies the commitment, and sometimes a third party | A [large multiple](/) of serving cost to prove, plus CPU time to verify | [Research prototypes](/proof-of-inference#today-s-systems), such as SASH and Anthropic's FlashProve |

Hardware enclaves carry real physical and architectural limits. The authors of [TEE.fail](https://tee.fail/) forged [[attestation|attestations]] for Intel CPU enclaves (SGX and TDX) using a memory-bus interposer that cost "under $1000" to build, and both Intel and AMD treat physical interposer attacks as outside their threat models.

The same authors also showed that "[the fact that Nvidia's attestation reports are not bound to the identity of a specific CVM means we can "borrow" Nvidia attestations from devices that aren't ours](https://tee.fail/)" (where a CVM is a confidential virtual machine). On its own, a GPU attestation does not prove which physical machine ran the workload.

:::quote https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note SASH, Towards Proving Frontier-Scale LLM Inference, September 2026
TEEs and activation checks are cheap, and for many settings they are the right tool; TEEs are a sensible starting point for a first agreement. What they cost is trust: in a hardware vendor, in a third party, or in a tolerance. A proof moves that trust into cryptographic assumptions and into code that both sides can read.
:::

## What a relying party supplies

A verifier checks a proof against inputs it must trust from the outside. For every system on the ladder, the table below shows what the claim card says about each input, linked directly to the publisher's documentation at the pinned commit:

:::measured supplies
:::

## In an agreement

Imagine a hypothetical bilateral AI agreement between the United States (US) and China, where declared data centres in both countries may serve only models whose [[commitment|commitments]] appear in a shared register. An inspectorate agreed on by both countries holds the register and audits an [[operator]] in either country while the operator keeps its weights private. This is an illustrative scenario, not a description of an existing deal.

Even with accepted proofs and a trusted traffic log, the inspectorate could certify only one narrow conclusion: each sampled reply matches what the registered quantized copy outputs for its recorded prompt.

:::stage measured This reply is what the registered model gives
The inspectorate checks a reply's proof against the registered commitment. That verdict does not show that the reply came from [live traffic](/proof-of-inference#outside-the-proof), nor that the [weights stayed hidden](/checks#weights_hidden). On this site, we test this step on open-weights models using [512-token prompts and replies](/checks#passed).
:::

:::stage demonstrated The model that was evaluated is the model that serves
If both safety-evaluation replies and served replies are proved against the same commitment, then both came from the same weights. [South and others](https://arxiv.org/abs/2402.02675) demonstrated this on small models in 2024. Still, a proof cannot tell you whether the evaluation asked the right questions.
:::

:::stage proposed A sample stands for the traffic
A trusted certifier sitting at the boundary of the inspected data centre records a cryptographic fingerprint of every prompt and reply. As [SASH's publisher](https://www.aisafety.sg/research/what-proving-llm-inference-actually-costs-research-note) notes: "Nothing yet ties a proof to what the certifier recorded."

Later, the inspectorate picks a random sample of recorded replies and asks the operator to prove them. SASH's publisher adds that "the draw must be unpredictable to the provider, and the provider must commit to its answers before the draw." When both conditions hold, simple probability shows that 300 random draws catch an unregistered model serving 1 reply in 100 about 95 % of the time, whereas one serving 1 in 10,000 is caught only about 3 % of the time.

Because any reply could be selected for auditing, the [[quantization|quantized copy]] has to generate every reply up front. When a system page splits out a separate generation [part](/checks#multiple), that cost applies to every reply, sampled or not. Within the remaining "commit and proving" part, only the proving step shrinks with the sampling rate.
:::

:::stage outside The data centre did nothing else
The [AI 2040 verification plan](https://ai-2040.com/supplements/verification-plan) aims to restrict declared data centres to inference and currently recommends working toward "a network-tap and recomputation based approach". [Amodo Design](https://amododesign.com/ai-verification/plan-a-sitrep/) tracks progress on those measures: 4 have active efforts, 6 have not started, and 7 are marked "Not on track".
:::

:::stage outside Nothing was left undeclared
To detect undeclared data centres, a RAND working paper ([Baker and others, 2025](https://arxiv.org/abs/2507.15916)) points to chip tracking, satellite imagery, whistleblowers, and national intelligence.
:::

:::reading
- [AI Workload Verification Papers](https://github.com/WHodgkins/AI-Verification-Papers/blob/d57c49060942c17e8a9082e1263b8591c38343ec/README.md), a bibliography built on lists by Will Hodgkins, Mauricio Baker and James Petrie.
:::
