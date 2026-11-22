Every system runs on NVIDIA H200 GPUs priced at the same hourly rate. The [[harness]] measures timing from outside the container [rather than trusting the system's own timers](repo:rfcs/0011-measurement-and-sampling.md#motivation), and every system is held to the same [statement](/statement). Because no two runnable systems currently support the same model at their pinned commits ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#motivation)), each model has its own table. We never rank systems across models: a 400B [[mixture of experts|mixture-of-experts]] model like Llama 4 Maverick and a dense 8B model have very different serving costs and proving scaling curves.

## Fixed before the runs

We [froze](/mandate#level) the level definition file before running any counted sessions, and every counted run records its SHA-256 digest. Prompts are 512-token excerpts from Project Gutenberg books, selected using a seed from the [drand public randomness beacon](https://docs.drand.love/) at the first beacon round after the freeze commit's timestamp. Because that timestamp came from the committer's own clock (GitHub recorded each freeze 2 s after it) and we froze the level three times on 2026-11-11, each freeze drew a fresh prompt set ([PR-2](repo:rfcs/0018-level-1-ladder.md#prompts)). Every counted run uses the third draw.

We build each system at a full commit hash, and the [[adapter]] passes only settings documented by the system itself. FlashProve runs its upstream commit unchanged. SASH runs a commit from a pull request written by this project's owner that upstream has not merged ([ties](/mandate#ties)).

[The request](/checks#passed) is fixed at 512 prompt tokens and 512 reply tokens. That total (1,024 tokens) fills FlashProve's 1,024-token window and matches the block size used in SASH's own published runs ([RFC-0017](repo:rfcs/0017-requests-tasks-and-tested-states.md#b1-tasks)).

## The checks

Timing honest runs cannot tell you whether a verifier actually catches a modified model, prompt, or reply. That is why [six checks](/checks#checks) gate entry into the ranking. All six run the publisher's own prover honestly, so they act as sanity checks rather than adversarial audits: they confirm that honest runs verify and that our specific edits get rejected, not that a cheating prover could never forge a proof. Every tampered test is paired with an untouched [honest twin](repo:rfcs/0008-negative-controls.md#honest-twins); if the honest twin fails to verify, the trial is void.

The [Fidelity check](/checks#fidelity) sets a basic floor against severe model degradation. On Llama 3.1 8B it evaluates 15 replies, so it is a coarse filter.

:::note Not tested
Soundness and weight secrecy are [not tested](/checks#not-tested), because black-box tests cannot distinguish a cryptographic proof from a plain signature ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#drawbacks)). Imagine an operator that simply signs the commitment, prompt, and reply whenever its weights match the commitment. None of our tampering checks would pass a modified input, so external tests alone could not tell those signatures apart from real proofs.
:::

## The figure

:::measured rows
A row reports whole-session cost whenever any of its three sessions has [too few or too uneven](/checks#multiple) release groups to establish a steady state.
:::

An exact-match proof certifies only [the committed copy's own greedy reply](/statement#integer-arithmetic), so the system must first generate every reply using that copy. [[multiple|Cost vs serving]] includes that generation cost in both steady-state (`m / b`) and whole-session figures ([cost rules](/checks#multiple)).

:::figure session
:::

FlashProve generates replies through its [integer-model package](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/vllm/integer_model/README.md?plain=1#L18-L19), which runs "greedy decoding, one sequence at a time, one GPU". On the serving side, we measure the baseline at full load, because serving one request at a time would artificially shrink the cost ratio.

:::measured baselines
:::

The serving engine runs with its default settings rather than custom tuning. It also serves the publisher's original release precision while provers run quantized copies, so the cost multiple reflects that difference too. Price calculations cover only GPU time bound to the job (including idle GPU time inside the session), excluding CPU, host RAM, disk, and network costs.

## Order and the glyph

Level 1 requires a publisher to state a numeric [[security level]] in order to receive a [ranking position](/checks#order), but it sets no minimum threshold. Black-box tests cannot distinguish 60 bits of security from 128, and different systems' stated numbers are not directly comparable without recomputing their underlying bounds.

On the [[glyph]], whenever a publisher's documentation is silent on a property, we grade that petal **Not stated**, because users cannot rely on an unstated guarantee. Passing a check never upgrades a petal beyond what the publisher states, since rejecting a few specific edits does not prove soundness. Finally, the glyph never changes a system's ranking position.

## Judgement and changes

Four parameters were chosen by editorial judgement before the runs began:

- the 10 % margin in the [order rule](/checks#order)
- the 5 % tolerances for steady state and full load
- three trials per tampered input
- the p < 0.05 significance level for the fidelity test

The cut points for the [Integrity](/checks#unforgeable) petal were adopted on 2026-11-13, after the level freeze. The 128-bit and 100-bit thresholds follow the Ethereum Foundation's [zkEVM security milestones](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations), while 80 bits falls below what [NIST SP 800-57 Part 1 Rev. 5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf) allows. Table 4 of that NIST standard disallows any strength below 112 bits for applying protection and permits 112 bits only through 2030, so both the 80-bit and 100-bit cut points sit below NIST's floor.

Several rules added to [RFC-0018](repo:rfcs/0018-level-1-ladder.md) after the third freeze affected live rows. Under [CH-1a](/checks#model), FlashProve passed the Model check because its prover answered "failed" with no proof when given perturbed weights, [as its documentation specifies](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/prover/docs/ends-in-short.md?plain=1#L126). Under [SE-3a](/checks#run), [two SASH slots](/sash) were reassigned to subsequent complete sessions because the earlier runs verified with a GPU visible and did not retain proofs for re-verification.

## Getting a row

Each row pairs one proof system with one model on [the ladder](/), and the level chooses the models rather than letting entrants pick their own ([LV-2](repo:rfcs/0018-level-1-ladder.md#levels)). Because we run all three counted sessions ourselves, external runs can be attached to an issue for reference but do not count as official sessions.

To add a system to the ladder, [open an issue](https://github.com/ai-verification-observatory/inference-proofs/issues) listing the upstream repository, full commit hash, and supported workloads. The adapter is then contributed by pull request ([Writing an adapter](repo:systems/README.md)). Systems that prove a different statement or use a different verification mechanism are catalogued below the ladder as not run.

If a tampered input is accepted inside our adapter, the check does not immediately flip to failed. We mark it **not decided**, notify the publisher under [embargo](repo:SECURITY.md), and change the check to failed only after reproducing the same acceptance using the system's own command outside our adapter.
