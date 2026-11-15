### Adapter

The wrapper through which the harness runs a system's commands, in a container built at the system's pinned commit. It [changes nothing upstream](/mandate#what-we-do).

### AIR

An algebraic intermediate representation: a computation as a table of values (the trace) with polynomial constraints between rows. STARK provers such as [Winterfell](https://github.com/meta/winterfell/blob/2f78ee9bf667a561bdfcdfa68668d0f9b18b8315/README.md?plain=1#L59) take a computation in this form.

### Attestation

A report, signed by hardware or an organisation, that a condition holds. In policy writing, an attestation is a formal declaration that a standard is met.

### Bound

Said of a link in the computation that the verifier's acceptance constrains, such as the weights to their commitment. A [[claim card]] records what is bound as the publisher states it, or reads "not stated". As a noun, a bound is a stated limit, such as on the probability that a false proof is accepted.

### Check

One of the six tests of Level 1: Run, Model, Prompt, Reply, Verify without weights, Fidelity. Each ends held, failed or [undecided](/checks#undecided), and an undecided check names its cause: system limit, not run, not resolved or not reproduced.

### Claim card

The record of what one system's accepted proofs establish in one configuration, as its publisher states it. Each field is copied from the publisher's documents at the pinned commit and linked, or reads "not stated" ([RFC-0002](repo:rfcs/0002-claim-card.md)).

### Close to the original

The [petal](/checks#faithful_model) that grades how close a system's proved replies stay to the model its publisher released: how many leading reply tokens match the original's before the first difference, on average, against the same count for the model's 8-bit and 4-bit copies. It is a different measure from the [[fidelity]] figure, which counts top-token agreement. Until 2026-11-15 it was called Faithful model, a word that means something else in interpretability.

### Commitment

A value computed from data, such as a model's weights, that fixes them for later proofs without publishing them. The verifier takes it from [the harness's record](/statement#the-committed-weights), never from files sent with a proof. In policy writing, a commitment is a pledge.

### Completeness

The property that a verifier accepts every proof an honest prover makes of a true statement, often except with a small stated probability. It is the one of the three properties a test can show: on a system's page, completeness reads "tested by us on honest runs" with the count of honest replies whose proofs were accepted. In safeguards writing, a complete declaration leaves nothing out.

### Conjectured

Said of a soundness bound that rests on an unproved conjecture. On the [Unforgeable](/checks#unforgeable) petal, a conjectured bound reaches amber in lesser part at most.

### Control

An input changed on purpose (a negative control), from which a working system gives no accepted proof. A trial counts only if its honest twin, the trial unchanged, is accepted. The fidelity run's controls are runs beside the original, honest or [damaged](/checks#fidelity).

### Exact match

An acceptance policy under which each checked token must be the committed model's top token. A policy with a [tolerance](/statement#checked-tokens) also accepts other tokens.

### Fiat-Shamir

A transform that makes an interactive proof non-interactive by hashing the statement and transcript into each challenge.

### Fidelity

How closely the copy a system proves follows the model its publisher released. The Fidelity figure is the share of reply positions where the system's top token is the original's, with the system fed the prompt and then the original's reply (teacher forcing). It sets no state and is labelled "computed by the system's own code on the reference reply, not by the proved computation". The [Fidelity check](/checks#fidelity) and the [[close to the original]] petal score a proved reply by its leading tokens matching the original's.

### Field

A finite set of numbers, such as the integers modulo a prime, with exact addition, multiplication and division. Proof systems compute in one because their [random checks](/forward-pass#testing-a-product-at-random) need a product of two nonzero numbers never to be 0.

### FRI

A protocol that shows committed values lie close to a Reed-Solomon codeword, the evaluations of a low-degree polynomial. Its authors [built it](https://eccc.weizmann.ac.il/report/2017/134/) for proof systems that "require only public randomness for their setup".

### Glyph

A five-petal figure of how close a system is to a perfect prover. Its [petals](/checks#glyph), all green for such a prover, are Unforgeable, Weights hidden, Close to the original, Machine-checked and No third party trusted. Nothing adds them up, and the glyph never changes a system's position.

### Greedy decoding

Choosing the highest-scoring token at every step. With exact arithmetic and a fixed rule for ties, the same model and prompt always give the same reply.

### Harness

The benchmark's software (the Python package iproofs), which runs each adapter in a container and times it from outside.

### Inference

Running a trained model forward on an input to produce an output. A language model writes its reply one token at a time.

### KL divergence

A measure of how far one probability distribution lies from another (Kullback-Leibler divergence). [KL to the original weights](/checks#kl) is printed and gates nothing.

### Ladder

The home page: one table per open-weights model, largest first, with one row per system run on it. Systems are [ranked](/checks#order) inside a model, never across models.

### Level

A frozen definition of the benchmark in one file: the models, request, checks, order rule and constants. The glyph's rules are not part of it, and changing them needs no [new level](repo:rfcs/0018-level-1-ladder.md#the-glyph).

### Lookup argument

A proof that every value in a long list appears in a fixed public table. Provers use it for the [steps of a model](/forward-pass#lookups) that need more than additions and multiplications.

### Machine-checked

Said of a proof checked by a proof assistant's kernel, such as Lean's. What it takes on trust, such as the kernel and its axioms, is its trusted base. The [Machine-checked](/checks#machine_checked) petal grades how much such a proof of soundness covers, up to the verifier the row runs.

### Mixture of experts

A model that runs only part of its weights for each token. Llama 4 Maverick runs about 17 billion of its 400 billion parameters.

### Multilinear extension

The one polynomial, linear in each variable, that takes a table's values on the corners of the boolean hypercube.

### Multiple

The ranked figure: steady GPU-seconds per further proved reply over the serving baseline's GPU-seconds per reply at full load. The ladder prints it as Cost vs serving, with generation counted. A row with no steady state has [none](/checks#multiple) and prints its whole sessions' cost over serving.

### Operator

The party that serves a model and makes its proofs, such as a lab or an API provider. [RFC-0018](repo:rfcs/0018-level-1-ladder.md) also uses the word for the team that runs this benchmark.

### Passed

Said of a system on a model when all six [checks](/checks#passed) held there.

### Pinned commit

The full commit hash at which a system is built, run and quoted. It is unrelated to a [[commitment]], which fixes a model's weights.

### Polynomial commitment

A commitment to a polynomial that the prover opens at any point the verifier picks, with a [short proof](/forward-pass). It lets a verifier check claims about a model's weights without holding them.

### Position

A ranked system's place in its model's table: 1 plus the number of systems placed above it. A system [has one](/checks#order) only if it passed and its publisher states a numeric security level at the pinned commit, for at least one verifier it ships.

### Proof of inference

Files that let a verifier check that a reply is what a committed model produces for a prompt. In policy writing, a proof is evidence strong enough to support a conclusion.

### Proved

Said of a statement that a [[soundness|sound]] verifier's acceptance establishes, under the claim card's stated assumptions.

### Prover

The program that makes a proof, and by extension whoever runs it. It holds the [[witness]].

### Publisher

The organisation that releases a proof system and its documents, or a model and its weights. The model as its publisher released it is the original.

### Q8_0 and Q4_K_M

Two copies of the original model quantized by llama.cpp, two of the fidelity run's three honest controls. The ladder prints their [[fidelity]] under each system's.

### Quantization

Storing a model's weights, and often its activations, as low-precision integers in place of floating point. Each system on the ladder proves a [quantized copy](/statement#integer-arithmetic) of the original, whose replies can differ from the original's.

### Random oracle

An ideal hash function that gives every new input a fresh, uniformly random output. [[Fiat-Shamir]] proofs are usually proved sound with the hash taken as one.

### Read as

Said of a petal whose state rests on our reading of a publisher's documents, not on a sentence that says it. The petal prints the quotes it rests on and is drawn amber at most, for every system alike. The name of a construction, such as STARK, is never read as a claim.

### Recomputation

Checking a claimed output by [running the computation again](/deployment) and comparing. It needs the weights, hardware to run them, and arithmetic that two honest runs agree on or a tolerance between them.

### Relying party

Whoever acts on a verifier's verdict, such as a customer, an auditor, a regulator or an inspectorate. It runs the [[verifier]] or trusts someone who does, and judges what a verdict is worth.

### Request

One prompt and the reply checked for it: at Level 1, 512 prompt tokens and a [512-token greedy reply](/checks#passed).

### Residual

What a dishonest prover can still do while its proofs are accepted. FlashProve's [[claim card]] quotes its publisher's known limits, and SASH's reads "not stated".

### Sampled

Said of a guarantee that comes from checking [a random part of the work](/deployment), such as some replies. It is statistical, not cryptographic, and certifies no reply left unchecked.

### Security level

A measure, in bits, of how hard it is to get a false proof accepted. It is not a fixed chance per attempt: the [[soundness error]] usually grows with the forger's work. FlashProve states q/2^124 + 2^-101 after q hash queries, so each further query adds to a forger's chance. A stated level's basis is proved, [[conjectured]] or not said, and Level 1 prints the level as stated.

### Serving baseline

The GPU-seconds per reply that serving the request takes with no proof, on the model publisher's own release. It is measured at [full load](/checks#multiple).

### Session

One cold-start run of a system on a model: setup, commit, then proofs for one slot's requests. Three complete sessions [count](/checks#run), one per slot (a fixed share of the prompts).

### SNARK and STARK

Two names for proof systems: SNARKs (succinct non-interactive arguments of knowledge) and STARKs. A STARK is typically built from hash functions, with no trusted setup. Neither name means that the proof hides anything ([[zero knowledge]]).

### Soundness

The property that a verifier refuses proofs of false statements, except with a probability the [[security level]] bounds. It rests on a security proof under stated assumptions. A test can refute it but never establish it.

### Soundness error

The probability, as the publisher states it, that a verifier accepts a proof of a false statement: the bound behind [[soundness]]. It is stated for a given verifier, per proof or per part of one, often as a function of the forger's hash queries. The [Unforgeable](/checks#unforgeable) petal prints it first, then every condition that keeps it from covering what the row runs, such as a verifier other than the one the bound is stated for.

### Statement

The proposition that an accepted proof establishes. For [an inference prover](/statement): *the model fixed by this commitment, run on this prompt under this decoding rule, produces this reply*.

### Steady state

A session's state when enough release groups follow the first, each at an even time per reply. A release group is a burst of proofs released together. A row is [steady](/checks#multiple) when its three sessions are.

### Sumcheck

A protocol that convinces a verifier of a polynomial's sum over exponentially many points with one random evaluation. The verifier's work is [one round per variable](/forward-pass).

### Token

The unit of text a model reads and writes, a word or part of one, stored as an integer.

### Trusted execution environment

A hardware enclave (TEE) in a processor that isolates code and memory from the machine's owner. It signs a report of what it loaded, an [[attestation]] that rests on the chip maker's keys and an untampered chip.

### Trusted setup

A one-time step that makes public parameters from a secret whose holder could forge proofs, as in KZG commitments. A system is [transparent](/checks#no_trusted_party) when soundness rests on cryptographic assumptions alone and no setup produced a secret.

### Verification

Checking a claim against evidence that holds even if the claimant has a reason to cheat. The word also names judging compliance with a law or a treaty, and proving software correct against a specification. On the ladder it means running a [[verifier]], whose verdict alone never settles compliance.

### Verifier

The program that checks a proof against the commitment and the prompt, and accepts or refuses. It is given the reply or reads it from the proof. In policy writing, the verifier is the inspectorate or the auditor, here called the [[relying party]].

### Weights

The learned numbers a model is made of, about 8 billion in Llama 3.1 8B. For a closed model they are its owner's trade secret.

### Witness

Everything the prover uses to build a proof and the verifier does not see. In a proof of inference: the weights and every layer's activations.

### Zero knowledge

The property that a proof shows nothing beyond the truth of its statement: all a verifier sees could be simulated without the weights. It comes in forms. Honest-verifier zero knowledge holds only against a verifier that follows the protocol. After Fiat-Shamir it can hold against any verifier, often within a stated number of hash queries and in the [[random oracle]] model. It is perfect, statistical or computational as the simulated view is identical, close up to a stated distance, or only hard to tell apart. What the statement makes public stays visible: the model's sizes, the prompt, the reply. The [Weights hidden](/checks#weights_hidden) petal prints the form the publisher states, asks it of the programs that run, not only of the protocol, and of the row's batches.
