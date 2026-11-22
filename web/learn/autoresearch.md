## Why benchmark components

The [ladder](/) ranks end-to-end inference provers. Building a complete prover takes a major engineering effort, which limits how many teams can enter. In practice, progress often happens one building block at a time: [[lookup argument|lookup arguments]], [[range check|range checks]], nonlinear model layers (softmax, SiLU, RMSNorm), and the GPU kernels underneath them. This track benchmarks those components directly, and is designed so a script or AI agent can iterate through prover variants and keep whichever ones score better.

## How it works

:::cells
### Specify the statement, not the method

Each task defines a statement to prove, such as "every value appears in this table." We fix the input sizes, allowed [[field|fields]], and required [[security level]]; how you construct the proof is up to you.

### Verifier proved in Lean

We publish each task's theorem in [[Lean]] with an explicit [[soundness]] error bound. An entry counts only when its verifier is proved to satisfy that theorem, and we compile and run that exact Lean verifier. The prover itself is unconstrained, since a buggy prover can only produce proofs that the verifier rejects.

### Sized for automated loops

Every task includes a small problem size that runs on a CPU in minutes, letting an automated loop test many candidates in sequence. The Lean kernel checks validity, and any cryptographic assumptions the proof relies on (such as the [[random oracle]] model) are shown alongside the result.
:::

## Open questions

- Tasks beyond lookups and range checks
- Input sizes and hardware
- How metrics are combined
- Whether entries are ranked
- Track name
- Launch date

We are drafting the rules in the [repository](https://github.com/ai-verification-observatory/inference-proofs), where you can follow along.
