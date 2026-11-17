### Abstraction of the protocol

What a machine-checked proof covers, in three levels: **an abstraction of the protocol**, the method without this model's computation (or the model without the method); **the protocol**, the method with the model's computation; **the code this row runs**, the verifier program the row actually runs. Only the verifier the row runs counts as the code. A proof about a formal model of the method, rather than about a program, verifies the protocol (or an abstraction of it), never the code.

### Adapter

The wrapper through which the harness runs a system's commands, in a container built at the system's pinned commit. It passes no setting the system's documentation does not name ([what we do](/mandate#what-we-do)).

### AIR

An algebraic intermediate representation: a computation as a table of values (the trace) with polynomial constraints between rows. STARK provers such as [Winterfell](https://github.com/meta/winterfell/blob/2f78ee9bf667a561bdfcdfa68668d0f9b18b8315/README.md?plain=1#L59) take a computation in this form.

### Any cheating prover

A cheater that controls its own machine, with no hardware or outside party assumed honest. Integrity's Met needs a limit that holds against any cheating prover.

### Architecture

A model's layout and sizes: its layers, widths and heads. It is public for every Level 1 model, so no Level 1 petal grades hiding it.

### Attestation

A report, signed by hardware or an organisation, that a condition holds. In policy writing, an attestation is a formal declaration that a standard is met.

### Bar

The most faithful damaged copy that every honest copy scores above; a system's proved replies must score above it to pass the [[Fidelity check]]. Its rule is on the [checks page](/checks#fidelity).

### Bound

Said of a link in the computation that the verifier's acceptance constrains, such as the weights to their commitment. A [[claim card]] records what is bound as the publisher states it, or reads "not stated". As a noun, a bound is a stated limit, such as on the probability that a false proof is accepted.

### Check

One of the six tests of Level 1: [[run check|Run]], [[model check|Model]], [[prompt check|Prompt]], [[reply check|Reply]], [[verify without weights check|Verify without weights]] and [[fidelity check|Fidelity]]. Each ends [[passed (check)|passed]], [[failed (check)|failed]] or [[not decided (check)|not decided]], and a check not decided names its cause: the system cannot do what the test needs, not run yet, the test ran and its result does not count yet, or a changed input accepted in our adapter and not yet repeated with the system's own command.

### Claim card

The record of what one system's accepted proofs establish in one configuration, as its publisher states it. Each field is copied from the publisher's documents at the pinned commit and linked, or reads "not stated" ([RFC-0002](repo:rfcs/0002-claim-card.md)).

### Commit and proving

The part of a [[whole session]]'s GPU time that is not [[generation]]: the commit call, which commits to the weights, and the proving of every reply. Under Cost vs serving it is printed beside generation, each over the same serving time.

### Commitment

A value computed from data, such as a model's weights, that fixes them for later proofs without publishing them. The verifier takes it from [the harness's record](/statement#the-committed-weights), never from files sent with a proof. In policy writing, a commitment is a pledge.

### Completeness

The property that a verifier accepts every proof an honest prover makes of a true statement, often except with a small stated probability. It protects the provider, and it is the one of the three properties a test can show: on a system's page it reads "tested by us on honest runs" with the count of honest replies whose proofs were accepted ([[run check|Run check]]). No petal grades it. In safeguards writing, a complete declaration leaves nothing out.

### Confidentiality

Whether checking a proof reveals the model's weights, graded on the [[zero knowledge]] the publisher states and proves ([petal](/checks#weights_hidden)). It protects the provider. At Level 1 the [[architecture]] is visible, since the models are open-weights.

### Computed by our code from recorded numbers

How a derived figure was obtained: code calculates it from the times and counts our harness recorded, and no one types it. Its title names the records it is computed from ([RFC-0004](repo:rfcs/0004-metrics-timing-grades.md)).

### Conjectured

Said of a soundness limit that rests on an unproven assumption, not a theorem. On the [Integrity](/checks#unforgeable) petal, a conjectured limit reaches Partly met at most.

### Control

An input changed on purpose (a negative control), from which a working system gives no accepted proof. A trial counts only if its honest twin, the trial unchanged, is accepted. The fidelity run's controls are runs beside the original, honest or [damaged](/checks#fidelity).

### Cost vs serving

How many times the GPU time of serving the same reply without a proof, at full load on the same GPU type, a proved reply takes. Both sides are GPU-seconds per reply, the proved side over [[whole session]]s (generation, commit and proving), so the GPU price is the same on both sides; [the rule](/checks#multiple) says how each side is timed.

### Evidence: our runs only, not rerun by anyone else

We measured it on our own [[session]]s, and no one else has rerun them yet. Every Level 1 figure has this evidence; a figure rerun by an unaffiliated team would say so ([RFC-0007](repo:rfcs/0007-evidence-tiers-and-reproduction.md)).

### Exact match

An acceptance policy under which each checked token must be the committed model's top token. A policy with a [tolerance](/statement#checked-tokens) also accepts other tokens.

### Failed

For a petal: one of our checks, or our build of the publisher's proof, contradicted it. For a check, see [[failed (check)]].

### Failed (check)

A check whose test showed the opposite of what it needs, repeated with the system's own command where a changed input was accepted in our adapter.

### Fiat-Shamir

A transform that makes an interactive proof non-interactive by hashing the statement and transcript into each challenge.

### Fidelity

How closely the copy a system proves answers like the model its publisher released. One name covers three things, told apart by a word: the [[Fidelity check]] and the Fidelity [petal](/checks#faithful_model) count [[matched leading tokens]], and the [[Fidelity figure]] counts top-token agreement. Beside a figure, the site prints the [[quantization]] the system proves.

### Fidelity check

One of the six [checks](/checks#fidelity): the proved replies match the original's opening tokens better than the [[bar]] does, by a paired test at p < 0.05.

### Fidelity figure

The share of reply positions where the system, fed the prompt and the original's reply, picks the original's next token (top-token agreement). It sets no state and is labelled "computed by the system's own code on the reference reply, not by the proved computation".

### Field

A finite set of numbers, such as the integers modulo a prime, with exact addition, multiplication and division. Proof systems compute in one because their [random checks](/forward-pass#testing-a-product-at-random) need a product of two nonzero numbers never to be 0.

### Formally verified

How far a computer-checked ([[machine-checked]]) proof of soundness reaches ([petal](/checks#machine_checked)): part of the protocol, an abstraction of it, the protocol with the model, or the verifier code the row runs. Our recorded build of the named proof decides the step. It protects the customer.

### FRI

A protocol that shows committed values lie close to a Reed-Solomon codeword, the evaluations of a low-degree polynomial. Its authors [built it](https://eccc.weizmann.ac.il/report/2017/134/) for proof systems that "require only public randomness for their setup".

### Generation

The phase of a [[session]] in which the system's own model computes the replies, where the system does this apart from proving them. Its GPU time counts in the proved side of Cost vs serving, and the figure prints it as a part of its own.

### Glyph

A five-petal figure of how close a system is to a perfect prover. Its [petals](/checks#glyph), every one Met for such a prover, are [[integrity|Integrity]], [[confidentiality|Confidentiality]], [[fidelity|Fidelity]], [[formally verified|Formally verified]] and [[trust assumptions|Trust assumptions]]. Nothing adds them up, and the glyph never changes a system's position.

### GPU-second

One GPU busy for one second. GPU-seconds add over every GPU a job holds, so two GPUs for one second are two GPU-seconds.

### Greedy decoding

Choosing the highest-scoring token at every step. With exact arithmetic and a fixed rule for ties, the same model and prompt always give the same reply.

### Halfway point

The average of two copies' mean scores; a row is shown above it by a paired sign-flip test at p < 0.05. The Fidelity petal's steps are halfway points between the original run again, the 8-bit copy and the 4-bit copy.

### Hash query

One run of the hash function by a cheating prover searching for a proof that passes. A limit written q/2^t grows with the number of hash queries, q.

### Honest and damaged copies

The fidelity run's yardsticks, fixed in the [level](/mandate#level) file before any run: honest copies are the original run again and its 8-bit and 4-bit copies, the usual ways to run the model; damaged copies (3-bit and 2-bit copies, a quarter of the model's blocks cut, a smaller model) are made worse on purpose, and the highest-scoring of them that every honest copy scores above is the [[bar]].

### Harness

The benchmark's software (the Python package iproofs), which runs each adapter in a container and times it from outside.

### Inference

Running a trained model forward on an input to produce an output. A language model writes its reply one token at a time.

### Integrity

Whether a provider can get a reply accepted that the model did not compute, graded on the [[soundness]] bound the publisher states for what the row runs ([petal](/checks#unforgeable)). It protects the customer. It grades soundness only: [[completeness]] is what the Run check tests.

### KL divergence

A measure of how far one probability distribution lies from another (Kullback-Leibler divergence). [KL to the original weights](/checks#kl) is printed and gates nothing.

### Ladder

The home page: one table per open-weights model, largest first, with one row per system run on it. Systems are [ranked](/checks#order) inside a model, never across models.

### Lean

A proof assistant: a program that checks every step of a mathematical proof. A proof it accepts is [[machine-checked]].

### Level

A frozen definition of the benchmark in one file: the models, request, checks, order rule and constants. The glyph's rules are not part of it, and changing them needs no [new level](repo:rfcs/0018-level-1-ladder.md#the-glyph).

### Lookup argument

A proof that every value in a long list appears in a fixed public table. Provers use it for the [steps of a model](/forward-pass#lookups) that need more than additions and multiplications.

### Machine-checked

Said of a proof checked by a proof assistant's kernel, such as Lean's. What it takes on trust, such as the kernel and its axioms, is its trusted base. The [[formally verified|Formally verified]] petal grades how far such a proof of soundness reaches.

### Met, Mostly met, Partly met

A petal's top step, the step below it, and the lowest step above Not met. Each petal's rule on the [checks page](/checks#glyph) says what each needs. The steps are drawn as inks; no printed word names an ink.

### Matched leading tokens

How many tokens at the start of a reply equal the original's, up to the first difference; the score of the [[Fidelity check]].

### Missing for Met

Everything a petal lacks for its top grade, Met, as a system page prints it: the items in groups by the step each group reaches, each with who acts, the publisher or us, and what it is today.

### Mixture of experts

A model that runs only part of its weights for each token. Llama 4 Maverick runs about 17 billion of its 400 billion parameters.

### Model check

A proof made with one weight changed is not accepted against the original weights' commitment ([rule](/checks#model)).

### Multilinear extension

The one polynomial, linear in each variable, that takes a table's values on the corners of the boolean hypercube.

### Multiple

The ranked figure: steady GPU-seconds per further proved reply over the serving baseline's GPU-seconds per reply at full load. The ladder prints it as Cost vs serving, with generation counted. A row with no steady state has [none](/checks#multiple) and prints its whole sessions' cost over serving.

### Next step

What would move a petal up one step, computed from its rule, and who acts: the publisher or us. A system page prints everything a petal misses for Met as **Missing for Met**, grouped by the step each group reaches, each item with who acts. A petal not decided prints what decides it.

### Not decided

A petal we cannot grade yet; its line says what it waits on, and it is never a failure. It is not a step of the scale: our part is not done yet.

### Not decided (check)

A check that has not run, ran without a result that counts yet, or that the system cannot run. Its line says what would decide it and who acts.

### Not met

A petal's step when the publisher's own facts fall below Partly met. Not met, Not stated and Failed are the three red steps, and none of them ranks above another.

### Not stated

A petal's step when the publisher's documents read at the pinned commit say nothing on it. A guarantee nobody states is graded as none.

### Number format

Whether the proved copy computes in integers, fixed point (integers with a fixed scale) or floating point, and with how many bits per weight.

### Operator

The party that serves a model and makes its proofs, such as a lab or an API provider. [RFC-0018](repo:rfcs/0018-level-1-ladder.md) also uses the word for the team that runs this benchmark.

### Our rebuild

Our run of the publisher's machine-checked proof through the proof-checking program it names, at the version we ran, with the program version the publisher pins. A Formally verified grade above Not met needs it.

### Passed

Said of a system on a model when all six of our [checks](/checks#passed) passed there. **Not passed yet**: no check failed, but at least one is [[not decided (check)|not decided]]. **Not passed**: a check failed. **Not ranked**: passed, without a [[position]], for the reason printed beside it.

### Passed (check)

A check whose test came out as its rule requires: for a check that changes an input, the change we made was refused.

### Pinned commit

The full commit hash at which a system is built, run and quoted. It is unrelated to a [[commitment]], which fixes a model's weights.

### Polynomial commitment

A commitment to a polynomial that the prover opens at any point the verifier picks, with a [short proof](/forward-pass). It lets a verifier check claims about a model's weights without holding them.

### Position

A ranked system's place in its model's table: 1 plus the number of systems placed above it. A system [has one](/checks#order) only if it passed and its publisher states a numeric security level at the pinned commit, for at least one verifier it ships.

### Prompt check

With one prompt token changed, the verifier refuses the proof ([rule](/checks#prompt)).

### Proof

On a system's page, the file the system sends with each reply for the [[verifier]] to check. A mathematical result and its argument are called a [[theorem]].

### Proof of inference

Files that let a verifier check that a reply is what a committed model produces for a prompt. In policy writing, a proof is evidence strong enough to support a conclusion.

### Proved

Said of a statement that a [[soundness|sound]] verifier's acceptance establishes, under the claim card's stated assumptions.

### Prover

The program that makes a proof, and by extension whoever runs it. It holds the [[witness]].

### Publisher

The organisation that releases a proof system and its documents, or a model and its weights. The model as its publisher released it is the original.

### The publisher's words

Sentences copied word for word from the publisher's documents at the pinned commit, each linked to its line. They are printed as the publisher's and never set a state alone.

### Q8_0 and Q4_K_M

The 8-bit copy (Q8_0) and the 4-bit copy (Q4_K_M): the original model with its weights rounded to 8 bits, and mostly to 4 bits, by llama.cpp at the level's pinned commit. We run them without a proof, as yardsticks, and the ladder prints their [[Fidelity figure]] under each system's.

### Quantization

Storing a model's numbers in fewer bits, which is cheaper to prove and can change replies. Each system on the ladder proves a [quantized copy](/statement#integer-arithmetic) of the original; the [[Fidelity figure]] shows how far its replies move.

### Random oracle

An ideal hash function that gives every new input a fresh, uniformly random output. [[Fiat-Shamir]] proofs are usually proved sound with the hash taken as one.

### Read as

What a grade comes from, printed beside it: **the publisher's words**, its own sentence; **our reading**, with the number of points it covers, where no single sentence of the publisher's states a point, so we read it from several passages, which are linked; **our test**, our own runs; **our rebuild**, our run of the publisher's proof through its proof-checking program. A grade that uses our reading is Mostly met at most, for every system alike. The name of a construction, such as STARK, is never read as a claim. Until 2026-11-17 the page printed this as "stated", "read as" or "tested by us".

### Recomputation

Checking a claimed output by [running the computation again](/deployment) and comparing. It needs the weights, hardware to run them, and arithmetic that two honest runs agree on or a tolerance between them.

### Relying party

Whoever acts on a verifier's verdict, such as a customer, an auditor, a regulator or an inspectorate. It runs the [[verifier]] or trusts someone who does, and judges what a verdict is worth.

### Reply check

Every proof covers all of the request's reply tokens, and with one changed (first, last or one inside) the verifier refuses it ([rule](/checks#reply)).


### Request

One prompt and the reply checked for it: at Level 1, 512 prompt tokens and a [512-token greedy reply](/checks#passed).

### Residual

What a dishonest prover can still do while its proofs are accepted. FlashProve's [[claim card]] quotes its publisher's known limits, and SASH's reads "not stated".

### Run check

The publisher's prover, as published at the pin, ran three sessions from a cold start, and every reply got an accepted proof ([rule](/checks#run)).

### Sampled

Said of a guarantee that comes from checking [a random part of the work](/deployment), such as some replies. It is statistical, not cryptographic, and certifies no reply left unchecked.

### Security level

A measure, in bits, of how hard it is to get a false proof accepted. It is not a fixed chance per attempt: the [[soundness error]] usually grows with the forger's work. FlashProve states q/2^124 + 2^-101 after q hash queries, so each further query adds to a forger's chance. A stated level's basis is proved, [[conjectured]] or not said, and Level 1 prints the level as stated.

### Serving baseline

The GPU-seconds per reply that serving the request takes with no proof, on the model publisher's own release. It is measured at [full load](/checks#multiple).

### Session

One run of a system from a cold start on one [[slot]]'s prompts: it loads the model, commits to the weights, then proves every reply (120 replies on Llama 4 Maverick, 5 on Llama 3.1 8B). Three complete sessions [count](/checks#run), one per slot.

### Slot

One of three fixed sets of a model's prompts. Each slot counts its first complete [[session]], and a failed session is rerun in the same slot.

### SNARK and STARK

Two names for proof systems: SNARKs (succinct non-interactive arguments of knowledge) and STARKs. A STARK is typically built from hash functions, with no trusted setup. Neither name means that the proof hides anything ([[zero knowledge]]).

### Soundness

The property that a verifier refuses proofs of false statements, except with a probability the [[security level]] bounds. It protects the customer, and [[integrity|Integrity]] grades the bound its publisher states. It rests on a security proof under stated assumptions. A test can refute it but never establish it.

### Soundness error

The probability, as the publisher states it, that a verifier accepts a proof of a false statement: the bound behind [[soundness]]. It is stated for a given verifier, per proof or per part of one, often as a function of the forger's hash queries. The [Integrity](/checks#unforgeable) petal grades it: its reason names every condition that keeps it from covering what the row runs, then the bound, such as a verifier other than the one the bound is stated for. A chance written 2^-128 is 1 in 2^128, about 3 in 10^39, and a smaller chance than 2^-100.

### Statement

The proposition that an accepted proof establishes. For [an inference prover](/statement): *the model fixed by this commitment, run on this prompt under this decoding rule, produces this reply*.

### Steady state

The part of a [[session]] after its first group of proofs, when proofs come out at an even pace. A release group is a burst of proofs released together. A row is [steady](/checks#multiple) when its three sessions are.

### Shown above

Our statistical test finds an average above a threshold at the usual 5% level: p < 0.05 in a paired sign-flip test over the prompts. Never "not shown" alone: not shown above means the test does not find it, not that the average is below.

### Sumcheck

A protocol that convinces a verifier of a polynomial's sum over exponentially many points with one random evaluation. The verifier's work is [one round per variable](/forward-pass).

### Theorem

A mathematical result with its proof. On a system's page, a theorem is one the publisher states and proves, such as a limit on the chance that the verifier accepts a fake reply.

### Token

The unit of text a model reads and writes, a word or part of one, stored as an integer.

### Tokens per second

The request's reply tokens over the GPU-seconds one reply took, on one GPU, printed in tokens/s per GPU with the GPU named. A row has two, on the same GPU type: proved, over [[whole session]]s, and served, by the [[serving baseline]] at full load. Served over proved is the row's [[cost vs serving|Cost vs serving]]. They depend on the GPU, so neither ranks a row ([RFC-0018](repo:rfcs/0018-level-1-ladder.md) CO-8).

### Trust assumptions

Whether checking a proof relies on anyone's honesty besides the mathematics, such as a [[trusted setup|setup]] secret or a hardware maker's key ([petal](/checks#no_trusted_party)). It protects the customer.

### Trusted execution environment

A hardware enclave (TEE) in a processor that isolates code and memory from the machine's owner. It signs a report of what it loaded, an [[attestation]] that rests on the chip maker's keys and an untampered chip.

### Trusted setup

A one-time step that makes public parameters from a secret whose holder could forge proofs, as in KZG commitments. The [[trust assumptions|Trust assumptions]] petal is Met when the publisher states that soundness rests on cryptographic assumptions alone and no setup produced a secret.

### Verification

Checking a claim against evidence that holds even if the claimant has a reason to cheat. The word also names judging compliance with a law or a treaty, and proving software correct against a specification. On the ladder it means running a [[verifier]], whose verdict alone never settles compliance.

### Verifier

The program that checks a proof against the commitment and the prompt, and accepts or refuses. It is given the reply or reads it from the proof. In policy writing, the verifier is the inspectorate or the auditor, here called the [[relying party]].

### Verify without weights check

The verifier reached every verdict with no copy of the model and no GPU ([rule](/checks#no_weight_file)).

### Weights

The learned numbers a model is made of, about 8 billion in Llama 3.1 8B. For a closed model they are its owner's trade secret.

### Whole session

A figure that counts a [[session]]'s GPU time from the start of its commit call to its last proof (the commit, generation and proving; loading the model before the commit is not counted), divided by its replies. Cost vs serving, the session GPU time and the proved tokens per second are figures of whole sessions.

### Witness

Everything the prover uses to build a proof and the verifier does not see. In a proof of inference: the weights and every layer's activations.

### Zero knowledge

The property that a proof shows nothing beyond the truth of its statement: all a verifier sees could be simulated without the weights. It comes in forms. Honest-verifier zero knowledge holds only against a verifier that follows the protocol. After Fiat-Shamir it can hold against any verifier, often within a stated number of hash queries and in the [[random oracle]] model. It is perfect, statistical or computational as the simulated view is identical, close up to a stated distance, or only hard to tell apart. What the statement makes public stays visible: the model's sizes, the prompt, the reply. It protects the provider. The [[confidentiality|Confidentiality]] petal prints the form the publisher states, asks it of the programs that run, not only of the protocol, and of the row's batches.
