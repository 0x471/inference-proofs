Every system runs on H200 GPUs at one price. The [[harness]] times each system from outside, [not with its own code](repo:rfcs/0011-measurement-and-sampling.md#motivation), and we check every system against the same [statement](/statement). No two runnable systems share a model at their pinned commits ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#motivation)), so each model has its own table. Nothing is ranked across tables, because Maverick (a 400B [[mixture of experts|mixture-of-experts]]) and a dense 8B differ in what serving costs and in how proving scales.

## Fixed before the runs

We [froze](/mandate#level) the level file before the first counted run, and every counted run names its digest. The prompts are 512-token windows of Project Gutenberg books. They are cut with a seed from a [public randomness beacon](https://docs.drand.love/), at the beacon's first round after the time of the freezing commit. That time comes from the committer's own clock, and GitHub recorded each freeze 2 s after it. We froze the level three times on 2026-11-11, and each freeze drew new prompts ([PR-2](repo:rfcs/0018-level-1-ladder.md#prompts)). Every counted run uses the third draw.

We run each system at a full commit hash, and the [[adapter]] uses no undocumented setting. FlashProve runs its upstream commit unchanged. SASH runs a commit of a pull request that this project's owner wrote and upstream has not merged ([ties](/mandate#ties)).

[The request](/checks#passed) is 512 prompt tokens and 512 reply tokens. It fills FlashProve's 1,024-token window and uses the one block size in SASH's own recorded runs ([RFC-0017](repo:rfcs/0017-requests-tasks-and-tested-states.md#b1-tasks)).

## The checks

Timing an honest run cannot show that a verifier refuses a changed model, prompt or reply. So [six checks](/checks#checks) gate a position. They run the publisher's own prover honestly, which makes them sanity checks, like a passing CI run: honest runs verify, and the changes we make are refused. But they do not show that a cheating prover gets caught. We verify each changed input beside its [honest twin](repo:rfcs/0008-negative-controls.md#honest-twins), and a trial whose twin is not accepted is void.

The [Fidelity check](/checks#fidelity) is a floor against gross damage. On the 8B model it rests on 15 replies, so it is coarse.

:::note Not tested
Soundness and weight secrecy are [not tested](/checks#not-tested), because tests cannot tell a proof from a signature ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#drawbacks)). Take an operator who would sign the commitment, prompt and reply only when its weights matched the commitment. No changed input would be accepted from it, so the tests could not tell its signatures from proofs.
:::

## The figure

:::measured rows
A row prints whole sessions when any of its three sessions has [too few or too uneven](/checks#multiple) release groups.
:::

An exact-match proof covers only [the committed copy's own greedy reply](/statement#integer-arithmetic), so the system first writes every reply with that copy. [[multiple|Cost vs serving]] counts that generation in both forms, [m over b](/checks#multiple) and whole sessions over b.

:::figure session
:::

FlashProve's replies come from its [integer-model package](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/vllm/integer_model/README.md?plain=1#L18-L19), which runs "greedy decoding, one sequence at a time, one GPU". We serve the baseline at full load, since serving one request at a time would make every multiple smaller.

:::measured baselines
:::

The serving engine runs at its defaults, not at its highest throughput. It serves the model publisher's release, and provers run quantized copies, so the multiple includes that difference in precision. The price covers only bound GPU time, idle time included, and not CPU, host memory, disk or network.

## Order and the glyph

Level 1 sets no floor under the numeric [[security level]] a [position](/checks#order) needs, because tests cannot tell 60 bits from 128 and stated levels are not comparable without recomputing them.

On the [[glyph]], when a publisher says nothing about a property, we grade its petal Not stated, because nobody can rely on a guarantee nobody states. A passed check never raises a petal above what the publisher states, since a refused change shows only that one attack was refused. The glyph never moves a position.

## Judgement and changes

These values were set by judgement before the runs:

- the 10 % margin of the [order rule](/checks#order)
- the 5 % steady and full-load tolerances
- three trials per changed input
- p < 0.05 in the fidelity test

The [Integrity](/checks#unforgeable) petal's cut points were adopted on 2026-11-13, after the freeze. The 128 and 100 come from the Ethereum Foundation's [zkEVM security milestones](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations), and 80 is a strength that [NIST SP 800-57 Part 1 Rev. 5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf) disallows. Its Table 4 disallows every strength under 112 bits for applying protection and accepts 112 only through 2030, so the 80 and 100 cuts sit below NIST's floor.

Some rules added to [RFC-0018](repo:rfcs/0018-level-1-ladder.md) after the last freeze decided rows. Under one of them, FlashProve's Model check passed: given changed weights, its prover answered "failed" with no proof, [as it documents](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/prover/docs/ends-in-short.md?plain=1#L126) ([CH-1a](/checks#model)). Under another, [two SASH slots](/sash) went to their next complete sessions, because the replaced ones verified with a GPU visible and kept no proofs to verify again ([SE-3a](/checks#run)).

## Getting a row

To get a system on the ladder, [open an issue](https://github.com/ai-verification-observatory/inference-proofs/issues) naming the upstream repository, the full commit hash and the workloads the system supports. The adapter then lands by pull request ([Writing an adapter](repo:systems/README.md)). A system with another statement or another kind of check is listed after the ladder as not run.

When a changed input is accepted in our adapter, the check does not fail yet. It fails only once the system's own command, run outside the adapter, accepts that input too. Until then the check reads not decided, and we tell the publisher under [embargo](repo:SECURITY.md).
