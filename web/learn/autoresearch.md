Level 1 measures whole systems. Every system on a rung gets one fixed request, we run [six checks](/checks#checks) ourselves, and we print one figure: the cost of a proved reply as a multiple of serving it. Level 1 stays as it is.

## Why parts

A competitive full prover now takes a very large engineering effort, so few teams can enter the ladder. And a ladder that few can enter moves little research. Outside the large teams, progress is more likely to come one part of the problem at a time: [[lookup argument|lookup arguments]], [[range check|range checks]], the nonlinear steps of a model (softmax, SiLU, RMSNorm) and the GPU kernels under them. So this track will benchmark those parts, one task each.

Some of these parts weigh a lot. On GPT-2, DeepProve's authors find that "more than 50% of the prover cost comes from activation functions, Softmax, and requantization" ([Proving a forward pass](/forward-pass#lookups)). We did not measure this, and we plan to profile the Level 1 systems to see how much of their prover time each part takes.

## Tasks are statements

Each task is a statement to prove, not an algorithm to run. Take, for example, N values and a public table T of 2^16 entries: the task is to prove that every value is in T. Another task would be to prove that each value fits in 16 bits, and a later one to prove a softmax over a row of 512 values within an error ε of the real function. We fix the sizes, the [[field|fields]] allowed and the [[security level]]. How you prove the statement is up to you, because no proving method is chosen in advance.

## Only the verifier needs Lean

For each task we publish a theorem in [[Lean]]. It states the relation to prove and a definition of [[soundness]] with a numeric error bound, and for a nonlinear step it also bounds the error against the real function. An entry counts only if its verifier is proved to meet our theorem, and the verifier we run is that Lean code, compiled.

The prover is free: any code and any GPU kernel, written by people or by programs. We ask nothing of it, because the verifier is proved, so a wrong prover can only make proofs that are refused. On Level 1 our checks [cannot show](/checks#not-tested) that a cheating prover is caught. Here the theorem bounds the chance that any prover gets a false statement accepted, under the assumptions it lists.

We check every entry's axioms mechanically. The cryptographic assumptions allowed, such as the [[random oracle]] model, are listed in the theorem and printed beside the result.

## Built for search loops

Say a program, or an AI agent, tries many variants of a prover and keeps the one that scores better. This is called an automated search loop, and the track is built for it. Each task comes in a small size that runs on a CPU in minutes, so a loop can run against it many times. The Lean kernel decides what counts, so no reviewer has to read an entry before it is scored.

For each entry we plan to report prover time, proof size and verifier time, and for a nonlinear step its error. Nothing has been measured yet, so this page holds no figure.

## Decided and not decided

### Decided

- Level 1 stays as it is.
- A task is a statement, and no proving method is chosen in advance.
- An entry counts only if its verifier is proved in Lean to meet the task's theorem, and we run that verifier.
- Every task has a size that runs on a CPU in minutes.
- Lookups and range checks come first.

### Not decided

- The tasks after lookups and range checks.
- The sizes.
- The hardware.
- How figures are combined, and whether entries are ranked.
- The track's name.
- Any date.

## Status

The track is not open yet. We are writing its rules, no task takes entries, and nothing has been measured. The rules will be written in the [repository](https://github.com/ai-verification-observatory/inference-proofs), where you can follow them as they change.
