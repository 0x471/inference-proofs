### Abstraction of the protocol

What a machine-checked proof covers comes in three levels, and **an abstraction of the protocol** is the first: the method without this model's computation (or the model without the method). The second, **the protocol**, is the method with the model's computation, and the third, **the code this row runs**, is the verifier program the row actually runs. Only the verifier the row runs counts as the code. A proof about a formal model of the method, rather than about a program, verifies the protocol (or an abstraction of it), never the code.

### Adapter

An adapter is the wrapper through which the harness runs a system's commands, in a container built at the system's pinned commit. It passes no setting the system's documentation does not name ([what we do](/mandate#what-we-do)).

### AIR

An AIR (algebraic intermediate representation) writes a computation as a table of values with polynomial constraints between its rows. This table is called the trace. STARK provers such as [Winterfell](https://github.com/meta/winterfell/blob/2f78ee9bf667a561bdfcdfa68668d0f9b18b8315/README.md?plain=1#L59) take a computation in this form.

### Any cheating prover

Any cheating prover means a cheater that controls its own machine, with no hardware or outside party assumed honest. For Met, Integrity needs a limit that holds against any cheating prover.

### Architecture

A model's architecture is its layout and sizes: its layers, widths and heads. It is public for every Level 1 model, so no Level 1 petal grades hiding it.

### Attestation

An attestation is a report, signed by hardware or an organisation, that a condition holds. In policy writing, an attestation is a formal declaration that a standard is met.

### Bar

The bar is the most faithful damaged copy that every honest copy scores above. To pass the [[Fidelity check]], a system's proved replies must score above it. Its rule is on the [checks page](/checks#fidelity).

### Bound

A link in the computation is bound when the verifier's acceptance constrains it, such as the link from the weights to their commitment. A [[claim card]] records what is bound as the publisher states it, or reads "not stated". As a noun, a bound is a stated limit, such as on the probability that a false proof is accepted.

### Check

A check is one of the six tests of Level 1, which are [[run check|Run]], [[model check|Model]], [[prompt check|Prompt]], [[reply check|Reply]], [[verify without weights check|Verify without weights]] and [[fidelity check|Fidelity]]. Each ends [[passed (check)|passed]], [[failed (check)|failed]] or [[not decided (check)|not decided]], and a check not decided names its cause: the system cannot do what the test needs, the check has not run yet, the test ran and its result does not count yet, or a changed input was accepted in our adapter and we have not yet repeated it with the system's own command.

### Claim card

A claim card is the record of what one system's accepted proofs establish in one configuration, as its publisher states it. We copy each field from the publisher's documents at the pinned commit and link it, or the field reads "not stated" ([RFC-0002](repo:rfcs/0002-claim-card.md)).

### Commit and proving

Commit and proving is the part of a [[whole session]]'s GPU time that is not [[generation]]: the commit call, which commits to the weights, and the proving of every reply. A system's page prints it under Cost, beside generation, each over the same serving time as Cost vs serving.

### Commitment

A commitment is a value computed from data, such as a model's weights, that fixes them for later proofs without publishing them. The verifier takes it from [the harness's record](/statement#the-committed-weights), never from files sent with a proof. In policy writing, a commitment is a pledge.

### Completeness

Completeness is the property that a verifier accepts every proof an honest prover makes of a true statement, often except with a small stated probability. It protects the provider, and it is the one of the three properties a test can show. A system's page prints it as the count of honest replies whose proofs were accepted in our [[run check|Run check]], and no petal grades it. In safeguards writing, a complete declaration leaves nothing out.

### Confidentiality

Confidentiality is the petal for one question: does checking a proof reveal the model's weights? We grade it on the [[zero knowledge]] the publisher states and proves ([petal](/checks#weights_hidden)). It protects the provider. At Level 1 the [[architecture]] is visible, since the models are open-weights.

### Computed by our code from recorded numbers

This label says how we obtained a derived figure: our code calculates it from the times and counts our harness recorded, and no one types it. The figure's title names the records it is computed from ([RFC-0004](repo:rfcs/0004-metrics-timing-grades.md)).

### Conjectured

A soundness limit is conjectured when it rests on an unproven assumption, not a theorem. On the [Integrity](/checks#unforgeable) petal, a conjectured limit reaches Partly met at most.

### Control

A control is an input we change on purpose (a negative control), from which a working system gives no accepted proof. A trial counts only if its honest twin, the trial unchanged, is accepted. The fidelity run's controls are runs beside the original, honest or [damaged](/checks#fidelity).

### Cost vs serving

Cost vs serving is the GPU time a proved reply takes, as a multiple of the GPU time that serving the same reply without a proof takes at full load on the same GPU type. Both sides are GPU-seconds per reply, the proved side over [[whole session]]s (generation, commit and proving), so the GPU price is the same on both sides. [The rule](/checks#multiple) says how we time each side.

### Evidence: our runs only, not rerun by anyone else

We measured it on our own [[session]]s, and no one else has rerun them yet. Every Level 1 figure has this evidence, and a figure that an unaffiliated team reran would say so ([RFC-0007](repo:rfcs/0007-evidence-tiers-and-reproduction.md)).

### Exact match

Exact match is an acceptance policy under which each checked token must be the committed model's top token. A policy with a [tolerance](/statement#checked-tokens) also accepts other tokens.

### Failed

We grade a petal Failed when one of our checks, or our build of the publisher's proof, has contradicted it. For a check, see [[failed (check)]].

### Failed (check)

A check fails when its test shows the opposite of what it needs. Where a changed input was accepted in our adapter, the check fails only once the system's own command, run on the same changed input, accepts it too.

### Fiat-Shamir

Fiat-Shamir is a transform that makes an interactive proof non-interactive by hashing the statement and transcript into each challenge.

### Fidelity

Fidelity is how closely the copy a system proves answers like the model its publisher released. One name covers three things, told apart by a word: the [[Fidelity check]] and the Fidelity [petal](/checks#faithful_model) count [[matched leading tokens]], and the [[Fidelity figure]] counts top-token agreement. Beside a figure, the site prints the [[quantization]] the system proves.

### Fidelity check

For the Fidelity check, one of the six [checks](/checks#fidelity), the proved replies must match the original's opening tokens better than the [[bar]] does, by a paired test at p < 0.05.

### Fidelity figure

The Fidelity figure is the share of reply positions where the system, fed the prompt and the original's reply, picks the original's next token. This is called top-token agreement. It sets no state, and its label reads "computed by the system's own code on the reference reply, not by the proved computation". One thing ties it to the proofs. Where a proved reply starts like the original's, both models have read the same text, so a proof tells us which token the proved model picks there. We count those positions and require the system's code to pick the same token at each; the count is on the system's page.

### Field

A field is a finite set of numbers, such as the integers modulo a prime, with exact addition, multiplication and division. Proof systems compute in one because their [random checks](/forward-pass#testing-a-product-at-random) need a product of two nonzero numbers never to be 0.

### Formally verified

Formally verified is the [petal](/checks#machine_checked) for how far a computer-checked ([[machine-checked]]) proof of soundness reaches: part of the protocol, an abstraction of it, the protocol with the model, or the verifier code the row runs. Our recorded build of the named proof decides the step. It protects the customer.

### FRI

FRI is a protocol that shows committed values lie close to a Reed-Solomon codeword, the evaluations of a low-degree polynomial. Its authors [built it](https://eccc.weizmann.ac.il/report/2017/134/) for proof systems that "require only public randomness for their setup".

### Generation

Generation is the phase of a [[session]] in which the system's own model computes the replies, where the system does this apart from proving them. Its GPU time counts in the proved side of Cost vs serving, and a system's page prints it under Cost as a part of its own.

### Glyph

The glyph is a five-petal figure of how close a system is to a perfect prover. Its [petals](/checks#glyph) are [[integrity|Integrity]], [[confidentiality|Confidentiality]], [[fidelity|Fidelity]], [[formally verified|Formally verified]] and [[trust assumptions|Trust assumptions]], and such a prover would have every one Met. Nothing adds them up, and the glyph never changes a system's position.

### GPU-second

A GPU-second is one GPU busy for one second. GPU-seconds add over every GPU a job holds, so two GPUs for one second are two GPU-seconds.

### Greedy decoding

Greedy decoding chooses the highest-scoring token at every step. With exact arithmetic and a fixed rule for ties, the same model and prompt always give the same reply.

### Halfway point

A halfway point is the average of two copies' mean scores. A row is shown above it by a paired sign-flip test at p < 0.05. The Fidelity petal's steps are halfway points between the original run again, the 8-bit copy and the 4-bit copy.

### Hash query

A hash query is one run of the hash function by a cheating prover searching for a proof that passes. A limit written q/2^t grows with the number of hash queries, q.

### Honest and damaged copies

Honest and damaged copies are the fidelity run's yardsticks, which the [level](/mandate#level) file fixes before any run. The honest copies are the original run again and its 8-bit and 4-bit copies, the usual ways to run the model. The damaged copies are made worse on purpose (3-bit and 2-bit copies, a quarter of the model's blocks cut, a smaller model), and the highest-scoring of them that every honest copy scores above is the [[bar]].

### Harness

The harness is the benchmark's software (the Python package iproofs). It runs each adapter in a container and times it from outside.

### Inference

Inference is running a trained model forward on an input to produce an output. A language model writes its reply one token at a time.

### Integrity

Integrity is the petal for one question: can a provider get a reply accepted that the model did not compute? We grade it on the [[soundness]] bound the publisher states for what the row runs ([petal](/checks#unforgeable)). It protects the customer, and it grades soundness only (the Run check tests [[completeness]]).

### KL divergence

KL divergence (Kullback-Leibler divergence) measures how far one probability distribution lies from another. We print [KL to the original weights](/checks#kl), but neither a check state nor a position depends on it.

### Ladder

The ladder is the home page, with one table per open-weights model, largest first, and one row for each system run on it. The [order rule](/checks#order) ranks systems inside a model, never across models.

### Lean

Lean is a proof assistant, a program that checks every step of a mathematical proof. A proof it accepts is [[machine-checked]].

### Level

A level is a frozen definition of the benchmark in one file: the models, request, checks, order rule and constants. The glyph's rules are not part of it, and changing them needs no [new level](repo:rfcs/0018-level-1-ladder.md#the-glyph).

### Lookup argument

A lookup argument is a proof that every value in a long list appears in a fixed public table. Provers use it for the [steps of a model](/forward-pass#lookups) that need more than additions and multiplications.

### Machine-checked

A proof is machine-checked when a proof assistant's kernel, such as Lean's, has checked it. What it takes on trust, such as the kernel and its axioms, is its trusted base. The [[formally verified|Formally verified]] petal grades how far such a proof of soundness reaches.

### Merkle tree

A tree of hashes built over a list of values. Each leaf is the hash of one value, each node above is the hash of its children, and the root at the top fixes every value under it, so the root is a [[commitment]] to them all. To open one value, the prover sends it with the hashes beside its path, and the verifier hashes up the path and compares the result with the root. FlashProve's commitment ID is a hash of, among other values, "the Merkle root and shape of the first weight table" ([its guide](https://github.com/anthropics/FlashProve/blob/9e2bdd8ff5bf9c62f18263d7dac189b0400b260c/guide/how-it-works.md?plain=1#L32-L37)).

### Met, Mostly met, Partly met

Met is a petal's top step, Mostly met the step below it, and Partly met the lowest step above Not met. Each petal's rule on the [checks page](/checks#glyph) says what each needs. The site draws the steps as inks, and no printed word names an ink.

### Matched leading tokens

Matched leading tokens is the number of tokens at the start of a reply that equal the original's, up to the first difference, and it is the score of the [[Fidelity check]].

### Missing for Met

Missing for Met is everything a petal lacks for its top grade, Met. A system page prints it as items in groups, by the step each group reaches, each item with who acts (the publisher or us) and what it is today.

### Mixture of experts

A mixture of experts is a model that runs only part of its weights for each token. Llama 4 Maverick runs about 17 billion of its 400 billion parameters.

### Model check

For the Model check, we change one weight, and no proof made with it is accepted against the original weights' commitment ([rule](/checks#model)).

### Multilinear extension

A table's multilinear extension is the one polynomial, linear in each variable, that takes the table's values on the corners of the boolean hypercube.

### Multiple

The multiple is the ranked figure: steady GPU-seconds per further proved reply over the serving baseline's GPU-seconds per reply at full load. The ladder prints it as Cost vs serving, with generation counted. A row with no steady state has [none](/checks#multiple), and it prints its whole sessions' cost over serving.

### Next step

The next step is what would move a petal up one step, computed from its rule, with who acts: the publisher or us. A system page prints everything a petal misses for Met as **Missing for Met**, grouped by the step each group reaches, each item with who acts. A petal not decided prints what decides it.

### Not decided

A petal is Not decided when we cannot grade it yet. Its line says what it waits on, and it is never a failure. It is not a step of the scale. It says that our part is not done yet.

### Not decided (check)

A check is not decided when it has not run, ran without a result that counts yet, or the system cannot run it. Its line says what would decide it and who acts.

### Not met

A petal is Not met when the publisher's own facts fall below Partly met. Not met, Not stated and Failed are the three red steps, and none of them ranks above another.

### Not stated

A petal is Not stated when the publisher's documents read at the pinned commit say nothing on it. We grade a guarantee nobody states as none.

### Number format

The number format says whether the proved copy computes in integers, fixed point (integers with a fixed scale) or floating point, and with how many bits per weight.

### Operator

The operator is the party that serves a model and makes its proofs, such as a lab or an API provider. [RFC-0018](repo:rfcs/0018-level-1-ladder.md) also uses the word for the team that runs this benchmark.

### Our rebuild

Our rebuild is our run of the publisher's machine-checked proof through the proof-checking program it names, at the version we ran, with the program version the publisher pins. A Formally verified grade above Not met needs it.

### Passed

A system has passed on a model when all six of our [checks](/checks#passed) passed there. It reads **Not passed yet** when no check failed but at least one is [[not decided (check)|not decided]], and **Not passed** when a check failed. It reads **Not ranked** when it passed but has no [[position]], for the reason printed beside it.

### Passed (check)

A check has passed when its test came out as its rule requires. For a check that changes an input, this means the change we made was refused.

### Pinned commit

The pinned commit is the full commit hash at which we build, run and quote a system. It is unrelated to a [[commitment]], which fixes a model's weights.

### Polynomial commitment

A polynomial commitment is a commitment to a polynomial that the prover opens at any point the verifier picks, with a [short proof](/forward-pass). It lets a verifier check claims about a model's weights without holding them.

### Position

A position is a ranked system's place in its model's table: 1 plus the number of systems placed above it. A system [has one](/checks#order) only if it passed and its publisher states a numeric security level at the pinned commit, for at least one verifier it ships.

### Prompt check

For the Prompt check, we change one prompt token, and the verifier must refuse the proof ([rule](/checks#prompt)).

### Proof

On a system's page, a proof is the file the system sends with each reply for the [[verifier]] to check. A mathematical result with its argument is called a [[theorem]].

### Proof of inference

A proof of inference is a set of files that lets a verifier check that a reply is what a committed model produces for a prompt. In policy writing, a proof is evidence strong enough to support a conclusion.

### Proved

A statement is proved when a [[soundness|sound]] verifier's acceptance establishes it, under the claim card's stated assumptions.

### Prover

The prover is the program that makes a proof, and by extension whoever runs it. It holds the [[witness]].

### Publisher

A publisher is the organisation that releases a proof system and its documents, or a model and its weights. The model as its publisher released it is the original.

### The publisher's words

The publisher's words are sentences we copy word for word from the publisher's documents at the pinned commit, each linked to its line. We print them as the publisher's, and they never set a state alone.

### Q8_0 and Q4_K_M

Q8_0 is the 8-bit copy and Q4_K_M the 4-bit copy: the original model with its weights rounded to 8 bits, and mostly to 4 bits, by llama.cpp at the level's pinned commit. We run them without a proof, as yardsticks, and the ladder prints their [[Fidelity figure]] under each system's.

### Quantization

Quantization stores a model's numbers in fewer bits, which is cheaper to prove and can change replies. Each system on the ladder proves a [quantized copy](/statement#integer-arithmetic) of the original, and the [[Fidelity figure]] shows how far its replies move.

### Random oracle

A random oracle is an ideal hash function that gives every new input a fresh, uniformly random output. [[Fiat-Shamir]] proofs are usually proved sound with the hash taken as one.

### Read as

A system's page prints what a grade comes from at the head of an opened petal's evidence, with "our reading" beside the grade wherever a reading of ours sets it. **The publisher's words** means the publisher's own sentence. **Our reading** means that no single sentence of the publisher's states a point, so we read it from several passages and link them, and the page prints the number of points our reading covers. **Our test** means our own runs, and **our rebuild** means our run of the publisher's proof through its proof-checking program. A grade that uses our reading is Mostly met at most, for every system alike. We never read the name of a construction, such as STARK, as a claim. Until 2026-11-17 the page printed this as "stated", "read as" or "tested by us". It now says "from" and "our reading", here and in a system's Statement block.

### Recomputation

Recomputation checks a claimed output by [running the computation again](/deployment) and comparing. It needs the weights, hardware to run them, and arithmetic that two honest runs agree on or a tolerance between them.

### Relying party

The relying party is whoever acts on a verifier's verdict, such as a customer, an auditor, a regulator or an inspectorate. It runs the [[verifier]] or trusts someone who does, and judges what a verdict is worth.

### Reply check

For the Reply check, every proof must cover all of the request's reply tokens, and when we change one of them (the first, the last or one inside), the verifier must refuse the proof ([rule](/checks#reply)).


### Request

A request is one prompt and the reply checked for it. At Level 1 it is 512 prompt tokens and a [512-token greedy reply](/checks#passed).

### Residual

The residual is what a dishonest prover can still do while its proofs are accepted. FlashProve's [[claim card]] quotes its publisher's known limits, and SASH's reads "not stated".

### Run check

For the Run check, we run the publisher's prover, as published at the pin, for three sessions from a cold start, and every reply must get an accepted proof ([rule](/checks#run)).

### Sampled

A guarantee is sampled when it comes from checking [a random part of the work](/deployment), such as some replies. It is statistical, not cryptographic, and certifies no reply left unchecked.

### Security level

A security level measures, in bits, how hard it is to get a false proof accepted. It is not a fixed chance per attempt, because the [[soundness error]] usually grows with the forger's work. FlashProve states q/2^124 + 2^-101 after q hash queries, so each further query adds to a forger's chance. A stated level's basis is proved, [[conjectured]] or not said, and Level 1 prints the level as stated.

### Serving baseline

The serving baseline is the GPU-seconds per reply that serving the request takes with no proof, on the model publisher's own release. We measure it at [full load](/checks#multiple).

### Session

A session is one run of a system from a cold start on one [[slot]]'s prompts. The system loads the model, commits to the weights, then proves every reply (120 replies on Llama 4 Maverick, 5 on Llama 3.1 8B). Three complete sessions [count](/checks#run), one per slot.

### Slot

A slot is one of three fixed sets of a model's prompts. Each slot counts its first complete [[session]], and we rerun a failed session in the same slot.

### SNARK and STARK

SNARK (succinct non-interactive argument of knowledge) and STARK are two names for proof systems. A STARK is typically built from hash functions, with no trusted setup. Neither name means that the proof hides anything ([[zero knowledge]]).

### Soundness

Soundness is the property that a verifier refuses proofs of false statements, except with a probability the [[security level]] bounds. It protects the customer, and [[integrity|Integrity]] grades the bound its publisher states. It rests on a security proof under stated assumptions. A test can refute it but never establish it.

### Soundness error

The soundness error is the probability, as the publisher states it, that a verifier accepts a proof of a false statement, and it is the bound behind [[soundness]]. The publisher states it for a given verifier, per proof or per part of one, often as a function of the forger's hash queries. The [Integrity](/checks#unforgeable) petal grades it. Under the petal, a system's page lists every condition that keeps the bound from covering what the row runs, such as a verifier other than the one the bound is stated for, and the petal's full reason stays on the board. A chance written 2^-128 is 1 in 2^128, about 3 in 10^39, and a smaller chance than 2^-100.

### Statement

The statement is the proposition that an accepted proof establishes. For [an inference prover](/statement): *the model fixed by this commitment, run on this prompt under this decoding rule, produces this reply*.

### Steady state

The steady state is the part of a [[session]] after its first group of proofs, when proofs come out at an even pace. A release group is a burst of proofs released together. A row is [steady](/checks#multiple) when its three sessions are.

### Shown above

An average is shown above a threshold when our statistical test finds it above at the usual 5% level: p < 0.05 in a paired sign-flip test over the prompts. We never print "not shown" alone. Not shown above means the test does not find it, not that the average is below.

### Sumcheck

Sumcheck is a protocol that convinces a verifier of a polynomial's sum over exponentially many points with one random evaluation. The verifier's work is [one round per variable](/forward-pass).

### Theorem

A theorem is a mathematical result with its proof. On a system's page, a theorem is one the publisher states and proves, such as a limit on the chance that the verifier accepts a fake reply.

### Token

A token is the unit of text a model reads and writes, a word or part of one, stored as an integer.

### Tokens per second

Tokens per second is the request's reply tokens over the GPU-seconds one reply took, on one GPU, and the site prints it in tokens/s per GPU with the GPU named. A row has two, on the same GPU type: proved, over [[whole session]]s, and served, by the [[serving baseline]] at full load. Served over proved is the row's [[cost vs serving|Cost vs serving]]. They depend on the GPU, so neither ranks a row ([RFC-0018](repo:rfcs/0018-level-1-ladder.md) CO-8).

### Trust assumptions

Trust assumptions is the petal for whether checking a proof relies on anyone's honesty besides the mathematics, such as a [[trusted setup|setup]] secret or a hardware maker's key ([petal](/checks#no_trusted_party)). It protects the customer.

### Trusted execution environment

A trusted execution environment (TEE) is a hardware enclave in a processor that isolates code and memory from the machine's owner. It signs a report of what it loaded, and this report is an [[attestation]] that rests on the chip maker's keys and an untampered chip.

### Trusted setup

A trusted setup is a one-time step that makes public parameters from a secret whose holder could forge proofs, as in KZG commitments. The [[trust assumptions|Trust assumptions]] petal is Met when the publisher states that soundness rests on cryptographic assumptions alone and no setup produced a secret.

### Verification

Verification is checking a claim against evidence that holds even if the claimant has a reason to cheat. The word also names judging compliance with a law or a treaty, and proving software correct against a specification. On the ladder it means running a [[verifier]], whose verdict alone never settles compliance.

### Verifier

The verifier is the program that checks a proof against the commitment and the prompt, and accepts or refuses it. It takes the reply as an input or reads it from the proof. In policy writing, the verifier is the inspectorate or the auditor, here called the [[relying party]].

### Verify without weights check

For the Verify without weights check, the verifier must reach every verdict with no copy of the model and no GPU ([rule](/checks#no_weight_file)).

### Weights

A model's weights are the learned numbers it is made of, about 8 billion in Llama 3.1 8B. For a closed model they are its owner's trade secret.

### Whole session

A figure of whole sessions counts a [[session]]'s GPU time from the start of its commit call to its last proof (the commit, generation and proving, but not loading the model before the commit), divided by its replies. Cost vs serving, the session GPU time and the proved tokens per second are figures of whole sessions.

### Witness

The witness is everything the prover uses to build a proof and the verifier does not see. In a proof of inference, it is the weights and every layer's activations.

### Zero knowledge

Zero knowledge is the property that a proof shows nothing beyond the truth of its statement. All a verifier sees could be simulated without the weights. It comes in several forms. Honest-verifier zero knowledge holds only against a verifier that follows the protocol. After Fiat-Shamir it can hold against any verifier, often within a stated number of hash queries and in the [[random oracle]] model. It is perfect, statistical or computational as the simulated view is identical, close up to a stated distance, or only hard to tell apart. What the statement makes public stays visible: the model's sizes, the prompt and the reply. It protects the provider. The [[confidentiality|Confidentiality]] petal prints the form the publisher states, and it asks for zero knowledge of the programs that run, not only of the protocol, and of the row's batches.
