Every system runs on H200 GPUs at one price, timed by the [[harness]], [not by its own code](repo:rfcs/0011-measurement-and-sampling.md#motivation), and is checked against the same [statement](/statement). No two runnable systems share a model at their pinned commits ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#motivation)), so each model has its own table. Nothing is ranked across tables: Maverick (a 400B [[mixture of experts|mixture-of-experts]]) and a dense 8B differ in what serving costs and in how proving scales.

## Fixed before the runs

The level file was [frozen](/mandate#level) before the first counted run, and every counted run names its digest. The prompts are 512-token windows of Project Gutenberg books, cut with a seed from a [public randomness beacon](https://docs.drand.love/) at its first round after the freezing commit's time. That time is the committer's own clock, and GitHub recorded each freeze 2 s after it. The level was frozen three times on 2026-11-11, and each freeze drew new prompts ([PR-2](repo:rfcs/0018-level-1-ladder.md#prompts)); every counted run uses the third draw.

Each system runs at a full commit hash, and the [[adapter]] uses no undocumented setting. FlashProve runs its upstream commit unchanged. SASH runs a commit of a pull request that this project's owner wrote and upstream has not merged ([ties](/mandate#ties)).

[The request](/checks#passed), 512 + 512, fills FlashProve's 1,024-token window and uses the one block size in SASH's own recorded runs ([RFC-0017](repo:rfcs/0017-requests-tasks-and-tested-states.md#b1-tasks)).

## The checks

Timing an honest run cannot show that a verifier refuses a changed model, prompt or reply, so [six checks](/checks#checks) gate a position. They run the publisher's own honest prover, so they are sanity checks, as a passing CI run is: honest runs verify and the changes we make are refused. They do not show that a cheating prover is caught. Each changed input is verified beside its [honest twin](repo:rfcs/0008-negative-controls.md#honest-twins), and a trial whose twin is not accepted is void.

The [Fidelity check](/checks#fidelity) is a floor against gross damage, coarse at 15 replies on the 8B model.

:::note Not tested
Soundness and weight secrecy are [not tested](/checks#not-tested): tests cannot tell a proof from a signature ([RFC-0018](repo:rfcs/0018-level-1-ladder.md#drawbacks)). If the operator signed the commitment, prompt and reply only when its weights matched the commitment, no changed input would be accepted either.
:::

## The figure

:::measured rows
A row prints whole sessions when any of its three sessions has [too few or too uneven](/checks#multiple) release groups.
:::

[[multiple|Cost vs serving]] counts generation in both forms, [m over b](/checks#multiple) and whole sessions over b. An exact-match proof covers only [the committed copy's own greedy reply](/statement#integer-arithmetic), so every reply is written with that copy first.

:::figure session
:::

FlashProve's replies come from its [integer-model package](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/integrations/vllm/integer_model/README.md?plain=1#L18-L19), which runs "greedy decoding, one sequence at a time, one GPU". The baseline serves at full load, since one request at a time would make every multiple smaller.

:::measured baselines
:::

The engine runs at its defaults, not its highest throughput. It serves the model publisher's release, and provers run quantized copies, so the multiple includes that difference in precision. Only bound GPU time is priced, idle time included. CPU, host memory, disk and network are not.

## Order and the glyph

Level 1 sets no floor under the numeric [[security level]] a [position](/checks#order) needs: tests cannot tell 60 bits from 128, and stated levels are not comparable without recomputing them.

On the [[glyph]], silence is graded Not stated: nobody can rely on a guarantee nobody states. A passed check never raises a petal above what the publisher states, since a refused change shows only that one attack was refused. The glyph never moves a position.

## Judgement and changes

Set by judgement before the runs:

- the 10 % margin of the [order rule](/checks#order)
- the 5 % steady and full-load tolerances
- three trials per changed input
- p < 0.05 in the fidelity test

The [Integrity](/checks#unforgeable) petal's cut points were adopted on 2026-11-13, after the freeze: 128 and 100 from the Ethereum Foundation's [zkEVM security milestones](https://blog.ethereum.org/2025/12/18/zkevm-security-foundations), 80 as a strength [NIST SP 800-57 Part 1 Rev. 5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf) disallows. Its Table 4 disallows every strength under 112 bits for applying protection and accepts 112 only through 2030, so the 80 and 100 cuts sit below NIST's floor.

Some rules added to [RFC-0018](repo:rfcs/0018-level-1-ladder.md) after the last freeze decided rows. Under [CH-1a](/checks#model), FlashProve's Model check passed: given changed weights, its prover answered "failed" with no proof, [as it documents](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/prover/docs/ends-in-short.md?plain=1#L126). [Two SASH slots](/sash) went to their next complete sessions under [SE-3a](/checks#run): the replaced ones verified with a GPU visible and kept no proofs to verify again.

## Getting a row

[Open an issue](https://github.com/ai-verification-observatory/inference-proofs/issues) naming the upstream repository, the full commit hash and the workloads the system supports. The adapter lands by pull request ([Writing an adapter](repo:systems/README.md)). A system with another statement or another kind of check is listed after the ladder as not run.

A changed input accepted in our adapter fails a check only once the system's own command, run outside the adapter, accepts it too. Until then the check reads not decided, and the publisher is told under [embargo](repo:SECURITY.md).
