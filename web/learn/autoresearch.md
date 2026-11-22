## Why parts

The [ladder](/) ranks whole provers, and a whole prover now takes a very large engineering effort, so few teams can enter it. Progress is more likely to come one part at a time: [[lookup argument|lookup arguments]], [[range check|range checks]], the nonlinear steps of a model (softmax, SiLU, RMSNorm) and the GPU kernels under them. So this track benchmarks those parts, and it is built for a program, or an AI agent, that tries many variants of a prover and keeps the one that scores better.

## How it works

:::cells
### A statement, not a method

Each task is a statement to prove, such as "every value is in this table". We fix the sizes, the [[field|fields]] allowed and the [[security level]], and how you prove it is up to you.

### A verifier proved in Lean

We publish each task's theorem in [[Lean]], with a [[soundness]] error bound. An entry counts only if its verifier is proved to meet it, and we run that Lean code, compiled. The prover is free, because a wrong prover can only make proofs that are refused.

### A size for loops

Every task has a small size that runs on a CPU in minutes, so a loop can run against it many times. The Lean kernel decides what counts, and the assumptions allowed, such as the [[random oracle]] model, are printed beside the result.
:::

## Not decided yet

- The tasks after lookups and range checks
- The sizes and the hardware
- How figures are combined
- Whether entries are ranked
- The track's name
- Any date

We are writing the rules in the [repository](https://github.com/ai-verification-observatory/inference-proofs), where you can follow them.
