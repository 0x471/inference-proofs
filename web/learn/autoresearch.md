:::figure autoresearch
A mock-up: no task is open and nothing has run, so the variants are made up and every figure is left blank. The Lean verifier decides each line, so a variant that drops a check is refused, and the loop keeps the better of the accepted ones.
:::

## Why parts

The [ladder](/) ranks whole provers, and a whole prover now takes a very large engineering effort, so few teams can enter it. Progress is more likely to come one part at a time: [[lookup argument|lookup arguments]], [[range check|range checks]], the nonlinear steps of a model (softmax, SiLU, RMSNorm) and the GPU kernels under them. So this track benchmarks those parts, and it is built for a program, or an AI agent, that tries many variants of a prover and keeps the one that scores better.

## How it works

Each task is a statement, like the one above, and how you prove it is up to you. We fix the sizes, the [[field|fields]] allowed and the [[security level]].

For each task we publish the theorem in [[Lean]], with a definition of [[soundness]] and a numeric error bound, and for a nonlinear step a bound on its error against the real function. An entry counts only if its verifier is proved to meet the theorem, and the verifier we run is that Lean code, compiled. The prover is free, any code and any GPU kernel, because a wrong prover can only make proofs that are refused.

Every task comes in a small size that runs on a CPU in minutes, so a loop can run against it many times, and the Lean kernel decides what counts, not a reviewer. We check every entry's axioms mechanically, and the assumptions allowed, such as the [[random oracle]] model, are printed beside the result.

## Not decided yet

- The tasks after lookups and range checks.
- The sizes and the hardware.
- How figures are combined, and whether entries are ranked.
- The track's name.
- Any date.

We are writing the rules in the [repository](https://github.com/ai-verification-observatory/inference-proofs), where you can follow them.
