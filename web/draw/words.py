"""The fixed words the pages print for stored ids, and the numbers as they are shown.

Check ids, states, causes, scopes, grades, tiers, null reasons and units are worded through the
tables here, keyed by the stored ids, so an id with no words stops the build. `number` prints a
stored value at four significant digits in a reading unit; it never changes the stored value.
The check definitions are RFC-0018's table in short. Nothing here reads the view.
"""

import html
import math
import re


def e(s):
    return html.escape(str(s), quote=True)


def curly(text):
    """Straight double quotes curly: opening at the start or after a space or bracket, closing
    elsewhere."""
    return re.sub(r'(?:^|(?<=[\s(\[{]))"', "“", text).replace('"', "”")


def quoted(text):
    """A publisher's words as the card stores them: escaped, quotes curly, `code` set as code."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(curly(str(text))).replace("&quot;", '"'))


# ------------------------------------------------------------------ the six checks (RFC-0018)
CHECK_NAME = {"run": "Run", "model": "Model", "prompt": "Prompt", "reply": "Reply",
              "no_weight_file": "Verify without weights", "fidelity": "Fidelity"}  # fmt: skip
# Each check in one plain sentence, printed first under its name on the checks page, before the
# precise rule, and the title of a check's name on a system page and the ladder: what passes it (SPEC section 8; RFC-0018 SI-3, amended 2026-11-16). {slots} and
# {reply_tokens} are the level file's constants, 0.05 its fidelity.alpha
CHECK_PLAIN = {
    "run": "The publisher's prover, as published at the pin, ran {slots} sessions from a cold "
    "start, and every reply got an accepted proof.",
    "model": "A proof made with one weight changed is not accepted against the original weights' "
    "commitment.",
    "prompt": "With one prompt token changed, the verifier refuses the proof.",
    "reply": "Every proof covers all {reply_tokens} reply tokens, and with one changed (first, "
    "last or one inside) the verifier refuses it.",
    "no_weight_file": "The verifier reached every verdict with no copy of the model and no GPU.",
    "fidelity": "The proved replies match the original's opening tokens better than the bar (a "
    "damaged copy of the model) does, by a paired test at p\u00a0<\u00a00.05.",
}
# Each check's rule, RFC-0018's table ("Held when", "Failed when") in short, as a condition in the
# present tense. {slots}, {attempts}, {reply_tokens} and {reference} are the level file's
# constants (`overview.filled`); 3 of 3 and 0.05 (fidelity.alpha) are typed as the level's.
CHECK_HELD = {
    # Terms (Slot, Session: complete), SE-1
    "run": "The model's prompts are split into {slots} slots. Each slot has a complete session: a "
    "job from a cold start whose prove call exits 0 with an accepted proof for every request. It "
    "is built from the pinned public commit as published there, with no weakening flag.",
    # P1 against the commitment of W, CH-1a (p1_refusals: an outcome the publisher documents at
    # the pin as meaning the weights are not the committed ones; a layout guard is not one), C3
    "model": "Proving with one weight changed, against the commitment to the unchanged weights, "
    "gives no accepted proof in 3\u00a0of\u00a03 trials of the same change. A prove call that "
    "makes no proof counts only when its publisher documents, at the pinned commit, that this "
    "outcome means the weights are not the committed ones. An honest proof checked against the "
    "changed weights' commitment is refused in 3\u00a0of\u00a03 trials of the same pair.",
    "prompt": "With one prompt token changed, at a position set by a seed and new in each trial, "
    "the verifier refuses the proof in 3\u00a0of\u00a03 trials.",
    "reply": "Every accepted proof covers all {reply_tokens} reply tokens. With one reply token "
    "changed, the verifier refuses the proof at the first position and at the last, 3\u00a0of"
    "\u00a03 trials of the same change each, and at an interior position set by a seed, new in "
    "each of 3\u00a0trials.",
    # the table's (a) to (c), CH-4a (the re-verify counts in the run's image, when it accepts)
    "no_weight_file": "Every counted verdict comes from a verify call with no GPU visible and no "
    "file of the model on its filesystem, and the trace of the files it opened names none. A "
    "verdict reached with a GPU visible counts when the same proof, verified again in the run's "
    "image on a host with no GPU, is accepted under these conditions.",
    "fidelity": "The replies the counted sessions proved score above the bar, by a paired "
    "one-sided sign-flip test at p\u00a0<\u00a00.05.",
}
# CH-8: an accepted trial is failed only once the system's own command accepts the same input
CHECK_FAILED = {
    "run": "A slot has {attempts} incomplete runs, or a recorded refusal by the system's own code "
    "with a reason about its inputs, or a counted session used a weakening flag.",
    "model": "A trial was accepted, and the system's own command, run outside our adapter, "
    "accepted the same changed input.",
    "prompt": "A trial was accepted, and the system's own command, run outside our adapter, "
    "accepted the same changed input.",
    "reply": "A proof covered fewer than {reply_tokens} reply tokens, or a trial was accepted and "
    "the system's own command, run outside our adapter, accepted the same changed input.",
    "no_weight_file": "The trace names a file of the model, or a verify call needed one.",
    "fidelity": "The bar scores above the replies, by the same test. With neither shown, the "
    "check is not decided.",
}
# a check's lines after held and failed: Run's cap (SE-4: 40 and 120 USD are the level file's
# sessions.cap_usd and the Maverick rung's cap_usd, typed as the level's; the view carries
# neither) and which session counts (SE-3, SE-3a); Fidelity's score and bar (FI-1 to FI-6)
CHECK_MORE = {
    "run": (
        ("cap", "A session that reaches the spending cap, 120\u00a0USD on Llama 4 Maverick and "
         "40\u00a0USD on the others, stops and is incomplete."),
        ("counted", "A slot counts its first complete session by start time, never one chosen for "
         "its figures. A session that missed Verify without weights only for a visible GPU, and "
         "was never verified again, gives its slot to the next complete session of the same "
         "image and adapter commit that meets the check."),
    ),
    "fidelity": (
        ("score", "For one reply, the number of leading tokens equal to the original's reply to "
         "the same prompt, 0 to {reply_tokens}. The original is a Hub copy of the model "
         "publisher's release, at the publisher's precision, named with its commit on each "
         "system page: {reference}."),
        ("bar", "Among the damaged controls that every honest control scores above, the one with "
         "the highest mean score. The honest controls are the original run again and its 8-bit "
         "and 4-bit copies (Q8_0, Q4_K_M). A system's page lists the damaged ones. With none, the "
         "model has no bar and the check is not decided on every row."),
    ),
}  # fmt: skip
# a check in one line, for its search entry: the held rule with every condition kept, about 95
# characters at most (two lines of the search list); {slots} and {reply_tokens} as above
CHECK_LINE = {
    "run": "{slots} slots, each with a complete cold-start session: public pin as published, no "
    "weakening flag.",
    "model": "Commit, change a weight: no accepted proof. Honest proof, changed commitment: "
    "refused. 3\u00a0of\u00a03 of one change each.",
    "prompt": "One prompt token changed, at a seeded position: the verifier refuses, "
    "3\u00a0of\u00a03 trials.",
    "reply": "All {reply_tokens} reply tokens covered. First, last, seeded interior token changed: "
    "refused, 3\u00a0of\u00a03 each.",
    "no_weight_file": "Verdicts, or an accepted second verify, with no GPU visible and no model "
    "file present or opened.",
    "fidelity": "The counted sessions' proved replies score above the bar: paired sign-flip test, "
    "p\u00a0<\u00a00.05.",
}
# a check's stored state in words (RFC-0018 Terms, amended 2026-11-16); the ids stay
STATE_WORD = {"held": "passed", "failed": "failed", "undecided": "not decided"}
# what a control's counted trials sent, from the board's `trials` (RFC-0018 CH-1c), by control
# and C1's position; printed with a check's records
TRIAL_WHAT = {("P1", None): "proved with one weight changed",
              ("C3", None): "an honest proof checked against the changed weights' commitment",
              ("C2", None): "one prompt token changed",
              ("C1", "first"): "the first reply token changed",
              ("C1", "last"): "the last reply token changed",
              ("C1", "interior"): "one interior reply token changed"}  # fmt: skip
TRIALS_HEAD = "What ran"
# how a counted trial was refused (CH-1c): the prover made no proof (`no_proof`, a stop its
# publisher documents, CH-1a), so no verifier saw one; or a verifier refused the proof
TRIAL_NO_PROOF = "the prover made no proof, as its publisher documents"
TRIAL_REFUSED = "refused by the verifier"
# a stored verifier trial (RFC-0008 §Verifier trials), printed beside the check whose change it
# makes, or under Machine-checked for another of the publisher's verifiers; it sets no state
KEPT_HEAD = "Outside the counted suite"
KEPT_CHANGE = {"reply_token": "one reply token changed, at every reply position in turn",
               "other_session_commitment": "checked against another session's commitment of "
               "the same weights",
               "commitment_id": "checked against a commitment ID no session recorded"}  # fmt: skip
# what a trial whose every changed call was refused shows, by its change
KEPT_MEANS = {"other_session_commitment": "So a refusal against the changed weights' "
              "commitment does not by itself show that the verifier tells weights apart: it also "
              "refuses a second commitment of the same weights."}  # fmt: skip
KEPT_TIME = "the trial script's wall clock"
STATEMENT_WORD = {
    "stated": "the reply is the committed model's own greedy reply to the prompt, as the publisher "
    "states",
    "read": "the reply is the committed model's own greedy reply to the prompt, on our reading of "
    "several of the publisher's sentences, none of which says it alone",
    "not": "not stated: the publisher's documents read at the pinned commit do not say that the "
    "reply is the committed model's own greedy reply to the prompt, so the system has no position",
}
READ_AS = "our reading"  # before ACCEPT_STATE["read"], linked to the checks page's #reading

# ------------------------------------------------------------------ the five petals (RFC-0018 §The glyph)
# the display names (RFC-0018 §The glyph, amended 2026-11-16, Q37); the ids stay
PETAL_NAME = {"unforgeable": "Integrity", "weights_hidden": "Confidentiality",
              "faithful_model": "Fidelity", "machine_checked": "Formally verified",
              "no_trusted_party": "Trust assumptions"}  # fmt: skip
# each petal's field term, its subtitle under its name on a system page and the checks page
# (depths 2 to 4): the plain name for the policy reader, the term for the expert
PETAL_TERM = {"unforgeable": "soundness",
              "weights_hidden": "zero knowledge of the weights",
              "faithful_model": "quantization error, in matched leading tokens",
              "machine_checked": "machine-checked soundness proof",
              "no_trusted_party": "trusted setup or party"}  # fmt: skip
# the petal name's title on a system page, which the probe shows beside it: its field term
FIELD_TERMS_TITLE = "in the field's terms: {term}"
# each petal in plain words: a question, what it grades, whom it protects, what Met means. The
# name's title at depths 1 and 2; printed under the name at depth 3 and on the checks page
PETAL_PLAIN = {
    "unforgeable": "Can a provider get a reply accepted that the committed model did not compute? "
    "Integrity grades the chance of that, as the publisher states it, and whether the statement "
    "covers what we run. It protects the customer. Met: a proved chance of at most 2^-128 "
    "(128 bits) that covers what we run.",
    "weights_hidden": "Does checking a proof reveal the model's weights? Confidentiality grades "
    "what the publisher states and proves about keeping them secret. It protects the provider. "
    "Met: zero knowledge proved for what we run.",
    "faithful_model": "Is the model that is proved as good as the one its publisher released? "
    "Proving usually runs a copy whose numbers are stored in fewer bits (quantization). Fidelity "
    "compares its replies with the original's, using our 8-bit and 4-bit copies as yardsticks. It "
    "protects the customer. Met: shown closer to the original run again than to the 8-bit copy.",
    "machine_checked": "Has a computer checked the mathematical proof that false replies are "
    "refused, and does that check reach the code we run? It protects the customer. Met: "
    "the verifier we run is machine-checked.",
    "no_trusted_party": "Does checking a proof rely on anyone's honesty besides the mathematics, "
    "such as whoever ran a one-time setup or holds a hardware maker's key? It protects the "
    "customer. Met: nothing to trust but cryptography, as the publisher states.",
}
# whom each petal protects (the checks page's "Protects" line)
PETAL_PROTECTS = {"unforgeable": "the customer", "weights_hidden": "the provider",
                  "faithful_model": "the customer", "machine_checked": "the customer",
                  "no_trusted_party": "the customer"}  # fmt: skip
# a reading's notes, in a petal's disclosure (GL-10, amended 2026-11-15): our words, not a quote
READING_HEAD = "Our reading"
# a petal's stored (step, cause) in words (RFC-0018 §The glyph, step table, amended 2026-11-16):
# one word set for all five petals, keyed by the step, and by the cause where red splits; the
# inks are drawn, never printed (SI-6)
STEP_WORD = {"green": "Met", "amber_upper": "Mostly met", "amber_lower": "Partly met",
             ("red", "stated"): "Not met", ("red", "check_failed"): "Failed",
             ("red", "not_stated"): "Not stated", None: "Not decided"}  # fmt: skip


def step_key(step, cause):
    """The STEP_WORD key of a stored (step, cause): red splits by its cause."""
    return (step, cause) if step == "red" else step


def petal_step(p):
    """A petal's step in words (STEP_WORD)."""
    return STEP_WORD[step_key(p["step"], p["cause"])]


# what a petal rests on, beside its step (amended 2026-11-16): our test, the publisher's words,
# or our reading of them (GL-10)
SAID_WORD = {"test": "tested by us", "statement": "stated", "reading": "read as"}


def said_word(p):
    """The word for what a petal rests on, from its basis and its reading flag."""
    if p["basis"] == "statement" and p["reading"]:
        return SAID_WORD["reading"]
    return SAID_WORD[p["basis"]]


# why a petal is red or hollow (GL-1, GL-3); the checks page defines each at #cause-<id>
CAUSE_WORD = {"not_stated": "not stated",
              "stated": "below Partly met, as the publisher states it",
              "check_failed": "a check failed, or the proof build failed",
              "not_read": "not read yet",
              "not_decided": "Fidelity check not decided or not recorded",
              "proof_build_not_run": "waits on our finished build of the publisher's machine-checked proof"}  # fmt: skip
# each cause in a line, on the checks page (#cause-<id>), opened by its word and how it is drawn:
# the checks page draws that opening as the chip a system page prints for the petal
# (PETAL_CAUSE_DRAW), the words kept for a screen reader
PETAL_CAUSE_RULE = {
    "not_stated": "Not stated (drawn as an outline): the publisher's documents read at the pinned "
    "commit are silent on the property. A guarantee nobody states is graded as none, never as "
    "not decided.",
    "stated": "Not met or Failed (drawn filled, name struck): the publisher states that the "
    "property does not hold, or what it states falls below Partly met.",
    "check_failed": "Not met or Failed (drawn filled, name struck): a check failed, or the "
    "matching build of the publisher's machine-checked proof failed or reported axioms other "
    "than the declared ones.",
    "not_read": "Not decided (drawn hollow): our record of the publisher's documents is missing, "
    "in another form or read at a commit other than the one the row runs, or the row has no "
    "recorded commit. Not read is not silent: it is not decided, never Not stated.",
    "not_decided": "Not decided (drawn hollow), Fidelity only: the Fidelity check is not decided, "
    "or the row has no fidelity record or no scores.",
    "proof_build_not_run": "Not decided (drawn hollow), Formally verified only: the publisher "
    "states a machine-checked proof, and no build of the named theorem is recorded at the pinned "
    "commit with the publisher's toolchain, or the one recorded was stopped at its time limit or "
    "by a kill before it reached a verdict. None can match where the publisher names no "
    "toolchain.",
}
# how a cause's opening words are drawn: (state, form) of the chip, its word the cause's step's
# (STEP_WORD)
PETAL_CAUSE_DRAW = {"Not stated (drawn as an outline)": ("red", "open"),
                    "Not met or Failed (drawn filled, name struck)": ("red", ""),
                    "Not decided (drawn hollow)": ("hollow", "")}  # fmt: skip
BASIS_WORD = {"statement": "the publisher's documents", "test": "our tests"}
# the From cell of a petal decided on the publisher's documents when a fact it read carries a note
# (the board petal's `reading`), and what that means, on the checks page (#reading, a block of its
# own after the causes, headed by BASIS_READING[1]; GL-1, GL-5)
BASIS_READING = ("the publisher's documents", "our reading")
# a system page's From line (GL-1, GL-5): the label over a silent red's documents read, and the
# words, linked to #reading, that say a fact behind the step is our reading
DOCS_READ, AS_READ = "Documents read", "as we read them"
READING_RULE = (
    "At least one fact behind the petal's step is our reading, not the publisher's words. The "
    "petal says it comes from our reading, the publisher's quotes are printed with it, and it is "
    "graded Mostly met at most, for every system alike. The name of a construction is never read as a "
    "claim."
)
# Machine-checked's scope card: what is machine-checked, for which program (printed, sets no state)
SCOPE_ROW_WORD = {"soundness": "Soundness", "zero_knowledge": "Zero knowledge",
                  "completeness": "Completeness"}  # fmt: skip
SCOPE_COL_WORD = {"protocol": "Protocol", "verifier_run": "The verifier we run",
                  "prover_run": "The prover we run"}  # fmt: skip
# Formally verified's stored build (GL-5), a fact beside the tool in the petal's details
PROOF_BUILD_HEAD = "Proof build"
# "tested" is the publisher's word for its own tests ("tested, not proved"), never ours: our runs are
# the Completeness line above the card
SCOPE_VALUE_WORD = {"machine_checked": "machine-checked", "paper": "on paper",
                    "tested": "tested by the publisher, not proved",
                    "not_stated": "not stated", "does_not_apply": "does not apply"}  # fmt: skip
# the scope card's bound column head, and the three lines over the card (MC-6, amended
# 2026-11-15): what the publisher states and what we test, for the row
SCOPE_BOUND_HEAD = "Bound, as stated"
# beside the claim card's link, while web/_data/errata.json corrects the card ({fields}, {says})
CARD_ERRATUM = "Erratum: the card's {fields} describe {says}. At Level 1:"
SCOPE_CARD_HEAD = (
    "What is verified, and for which code, as the publisher states it; it sets no state"
)
# the one line under the five petals (RFC-0018, the paragraph after MC-7, amended 2026-11-17, owner
# decision): the three properties a proof system is read for, in priority order, each its
# glossary entry, then where it is graded or tested; what each means and whom it protects is the
# glossary's. (glossary id, name, the petal that grades it or None)
SCOPE_TERMS = (("soundness", "Soundness", "unforgeable"),
               ("zero-knowledge", "Zero knowledge", "weights_hidden"),
               ("completeness", "Completeness", None))  # fmt: skip
SCOPE_GRADED = "graded under {petal}"
SCOPE_TESTED = "{n} of {n} replies accepted, our {run}"
SCOPE_CARD_WORD = "scope card"  # with the stated security, behind one disclosure under the line
STATED_SECURITY = "Stated security"
NOTION_HEAD = "Its notion, as the publisher names it"
# Weights hidden: what kind of value a proof leaves visible (only fitted_to_weights sets a step)
VISIBLE_TAG_WORD = {"statement_io": "the statement's input or output", "shape": "shape",
                    "side_channel": "side channel",
                    "fitted_to_weights": "depends on the weights"}  # fmt: skip
# the head of the visible values not tagged fitted, after those that are: "8 others" (an untagged
# item's quote does not say it is fitted; that does not show it is not, AGENTS.md rule 9)
VISIBLE_OTHERS = "others"
# the kinds, in plain words (RFC-0018 WH facts: `side_channel`, `shape`, `statement_io`)
VISIBLE_KINDS = ("side channel: seen around a proof, such as time, lengths, failures or volume; shape: "
                 "the architecture and sizes; the statement's input or output: the prompt, the reply, "
                 "served or refused")  # fmt: skip
# each petal's question in the field's terms, RFC-0018's petal table ("rung" said "model"): on the
# checks page under the plain sentence, and its search line
PETAL_QUESTION = {
    "unforgeable": "The bound the publisher states on a false reply being accepted: whether it is "
    "proved, and whether it covers what we run.",
    "weights_hidden": "What the publisher states and proves about a proof showing nothing of the "
    "weights' values.",
    "faithful_model": "How close the proved replies stay to the model publisher's own release, "
    "against the model's 8-bit and 4-bit copies.",
    "machine_checked": "How far a machine-checked proof of soundness reaches: part of the "
    "protocol, an abstraction of it, the protocol with the model, or the verifier code the row "
    "runs.",
    "no_trusted_party": "What checking a proof relies on besides cryptography: a setup secret, a "
    "fixed set of parties, or a hardware maker's or another trusted key.",
}
# each petal's steps, RFC-0018's tables in plain sentences, top step first: (STEP_WORD key, rule);
# a rule that is a tuple prints as a list. The first line that matches decides (§Reading the
# tables); 128, 100 and 80 are RFC-0018's cut points, 0.05 the level's fidelity.alpha. A petal
# lists only the steps it can take: Fidelity has no Not met or Not stated (it is a test), Trust
# assumptions no Failed (no check lowers it)
NOT_READ_RULE = "We have not read the publisher's documents at the commit we run."
PETAL_RULE = {
    "unforgeable": (
        ("green", "A proved bound that covers what we run, every exponent 128 or more."),
        ("amber_upper", "The same with every exponent 100 or more, or Met resting on our "
         "reading."),
        ("amber_lower", "Any other stated bound above Not met: conjectured, not shown to cover "
         "what we run, or an exponent from 80 to 99 on a proved bound."),
        (("red", "stated"), "The bound holds only against a weaker prover, has an exponent under "
         "80, or has an exponent under 100 and is not proved."),
        (("red", "not_stated"), "No bound with its exponents in the documents read at the pinned "
         "commit."),
        (("red", "check_failed"), "Our Model, Prompt or Reply check failed."),
        (None, NOT_READ_RULE),
    ),
    "weights_hidden": (
        ("green", "A zero-knowledge theorem proved for the configuration we run, batch "
         "size included, and stated for its programs. A published list of what stays visible, "
         "with nothing on it that depends on the weights."),
        ("amber_upper", "A zero-knowledge theorem is proved and a condition of Met is missing."),
        ("amber_lower", "The publisher states that the weights stay hidden and proves no "
         "zero-knowledge theorem."),
        (("red", "stated"), "The verifier is given the weights, or the publisher states that they "
         "are not hidden."),
        (("red", "not_stated"), "The documents read say nothing on hiding the weights."),
        (("red", "check_failed"), "Our Verify without weights check failed."),
        (None, "Not read at the commit we run."),
    ),
    # FM-5, FM-6, FM-7 in the RFC's order, then FM-1 and FM-2
    "faithful_model": (
        ("green", "Replies shown above halfway between the original run again and the 8-bit "
         "copy, in a fidelity run of one request at a time."),
        ("amber_upper", "Replies shown above halfway between the 8-bit and the 4-bit copy."),
        ("amber_lower", (
            "The Fidelity check passed, and the replies are not shown above halfway between the "
            "8-bit and 4-bit copies.",
            "Or no claim card is found, or its policy accepts tokens other than the model's top "
            "token.",
            "Or a copy a halfway point needs did not run, failed, or was scored on another "
            "number of replies.",
        )),
        (("red", "check_failed"), "The Fidelity check failed: the bar, a damaged copy, scores "
         "above the replies."),
        (None, "The Fidelity check is not decided, or no fidelity record is stored."),
    ),
    # §3 (amended 2026-11-16): the step grades what is verified (REACH_LABEL)
    "machine_checked": (
        ("green", "Built: the verifier we run, from the bytes it reads to its "
         "verdict, with its trusted base listed and no input-reading code outside the proof."),
        ("amber_upper", "Built: the protocol, model included; or the verifier we run, "
         "with a gap in its trusted base or its input-reading code."),
        ("amber_lower", "Built: an abstraction of the protocol (the protocol without the model, "
         "or the model without the protocol), or part of the protocol. A theorem whose "
         "conclusion is not about the model, or a build with axioms beyond its tool's standard "
         "ones, also stops here."),
        (("red", "stated"), "The publisher states that nothing is machine-checked."),
        (("red", "not_stated"), "The documents read name no machine-checked proof."),
        (("red", "check_failed"), "Our build of the named theorem failed or reported axioms "
         "other than the declared ones; or our Model, Prompt or Reply check failed where the "
         "stated step is Met."),
        (None, "A machine-checked proof is stated, and our build of it is not recorded yet, or "
         "the recorded one stopped before a verdict; or not read at the commit we run."),
    ),
    # NT-4 comes before NT-5 and NT-6; Q12's line is printed under the steps (PETAL_MORE)
    "no_trusted_party": (
        ("green", "The publisher states that soundness rests on cryptography alone: no setup "
         "made a secret. Met also needs proof files anyone can check, unless the publisher is silent "
         "on who can check them."),
        ("amber_upper", "An open setup ceremony with a public transcript, safe if one participant "
         "was honest; or Met's facts read by us, not stated in words."),
        ("amber_lower", "One honest party among a fixed set, or a challenger within a window; or "
         "proofs only a designated verifier can check."),
        (("red", "stated"), "A setup run by one party, a hardware maker's key or another trusted "
         "key."),
        (("red", "not_stated"), "The documents read say nothing on what soundness rests on."),
        (None, "Not read at the commit we run."),
    ),
}  # fmt: skip
# a petal's terms, defined under its steps, as (label, words)
PETAL_MORE = {
    "unforgeable": (
        ("covers what we run", "The bound holds for the settings we run, against any "
         "prover, per reply (or per proof with one reply a proof), with each reply checked alone. "
         "The publisher's or our records show its conditions hold for the files we run, and the "
         "verifier program we run is proved or stated to implement what the bound is "
         "about. A batch size not recorded is not covered."),
        ("exponent", "In 2^-t, the t: a larger exponent is a smaller chance. An error term "
         "q/2^t also has exponent t. A bound that is a sum of terms needs every term's exponent, so "
         "the whole stays within a few times the smallest chance allowed. Exponents are read as "
         "the publisher states them, and no bits figure is computed; no number of hash queries "
         "q is fixed. A bound stated per part of a proof (a segment, a layer) is read per part, "
         "as stated: that it is not per reply is a gap in covering what we run, and lowers the "
         "step no further."),
    ),
    "faithful_model": (
        ("halfway", "The average of two copies' mean scores, from the unrounded means."),
        ("one request at a time", "Every part of the rung's fidelity run sends one request at a "
         "time in llama.cpp (slots 1). Where llama.cpp at the level's pin cannot run the "
         "original, the original and its second run go to vLLM, which takes every prompt in one "
         "call: that part does not count as one at a time. There the second run sends the prompts "
         "in reverse order, so its batches differ from the first run's."),
        ("shown above", "The Fidelity check's paired sign-flip test gives p\u00a0<\u00a00.05 "
         "for the system's scores against the halfway point."),
        ("measure", "Graded on matched leading tokens, as the Fidelity check is. The Fidelity "
         "figure is top-token agreement and sets nothing."),
    ),
    "machine_checked": (
        ("build", "Each step above Not met needs a matching build of the named theorem: one "
         "recorded at the pinned commit with the publisher's toolchain. We run the publisher's own "
         "command for it, unpatched, and record what it reports. We do not review what the theorem "
         "states: the step is read from the publisher's words, printed with the petal."),
        ("above Partly met", "Needs a theorem whose conclusion is about a reference definition of "
         "the model, and a build that reports only its tool's standard axioms (for Lean, propext, "
         "Classical.choice and Quot.sound), so no sorry. The system page says that no outside "
         "reader of the proof has reviewed the statement."),
        ("the code", "Only the verifier we run counts as the code. A verified verifier "
         "we do not run counts at the protocol level."),
        ("protocol or code", "A proof about a formal model of the method, rather than about a "
         "program, verifies the protocol, not the code. Level 1 says the protocol, model "
         "included, when that formal model includes this model's computation, and an "
         "abstraction of the protocol when it leaves the computation out (or covers the model "
         "without the method). Only a proof about the verifier program we run verifies "
         "the code."),
        ("scope card", "Printed under a system's petals, it sets no state: the petal "
         "grades soundness only. Soundness is the verifier's and zero knowledge the prover's, so "
         "the cells that ask them of the other party do not apply."),
    ),
    # Q12: printed under the steps, as the question is printed over them
    "no_trusted_party": (
        ("", "This petal does not grade which model a commitment names, nor how strong "
         "soundness is (a theorem or a conjecture: Integrity grades that). Where a publisher's "
         "theorem asks that the public files were fixed before the hash function was drawn, "
         "Integrity counts that condition."),
    ),
}  # fmt: skip
# what each petal leaves to another place, under its steps on the checks page
PETAL_NOT_GRADED = {
    "unforgeable": "Not graded here: completeness. Integrity grades soundness only; completeness "
    "is what the Run check tests. Our Model, Prompt and Reply checks can set Failed; they do not "
    "measure the bound.",
    "weights_hidden": "Not graded here: hiding the architecture. Level 1 models are "
    "open-weights, so their architecture is public; a closed-weights level would grade it. Our "
    "Verify without weights check can set Failed; it does not test what a proof reveals.",
    "machine_checked": "Not graded here: prover code. Prover code bears on completeness and zero "
    "knowledge; the scope card prints what is verified for it, and it sets no step. Limits a "
    "publisher states beyond the five things graded here (reach, conclusion, input-reading "
    "code, axioms, our build) do not lower the step. Open questions in the rules: whether a "
    "step above Partly met should need a record that the verifier we run accepts honest proofs "
    "at our files, and whether our trial of another of the publisher's verifiers should set a "
    "step; today such a trial sets none.",
}
# once for the checks page's glyph section, after the steps
PETAL_STEPS_FOOT = "Each system page prints what each petal misses for Met, and who acts, computed from this table."
# Confidentiality's steps as a scale of what was proved or stated (§4, amended 2026-11-16),
# printed beside the step at depth 3: what the publisher proved, never a result for the row.
# Mostly met splits by its path: WH-6's missing conditions, or WH-5 capped by our reading (GL-10)
HIDING_LABEL = {"green": "Zero knowledge proved for what we run",
                "amber_upper": "Zero knowledge proved, with limits",
                "amber_reading": "Zero knowledge proved for what we run, on our reading",
                "amber_lower": "Stated, no proof",
                ("red", "stated"): "Not hidden",
                ("red", "not_stated"): "No guarantee stated"}  # fmt: skip
# the need a reading adds to a next step (glyph.py's READING_NEED, the same words on the board)
READING_NEED = "a sentence of the publisher's that says it, in place of our reading"
# Confidentiality's architecture fact (§4): printed on every Level 1 row, it sets no state
ARCH_SHORT = "Architecture: visible"
ARCH_LONG = (
    "Not graded at Level 1: every model here is open-weights, so its architecture is public. A "
    "closed-weights level would grade hiding it."
)
ARCH_NO_FACT = "the model is open-weights"
# Formally verified: what is verified, by `formal.reach` (§3, amended 2026-11-16); glyph.py's
# _REACH_WORDS holds the same words for the reasons
REACH_LABEL = {"verifier_run": "the verifier we run",
               "protocol_and_statement": "the protocol, model included",
               "protocol": "an abstraction of the protocol (the protocol without the model, or "
               "the model without the protocol)",
               "part": "part of the protocol",
               "none": "nothing, as the publisher states", "not_stated": "not stated"}  # fmt: skip
REACH_GAP = {"base": "no trusted base listed", "input": "input-reading code outside the proof"}
REACH_STATED = "{said}: {label}"  # "stated" or "read as" (SAID_WORD), by the petal's reading
# the line that says which verifier a theorem is about (§3): only the one the row runs is the code
VERIFIER_LINE = (
    "The theorem is stated for {stated}; we run {run}. Only the verifier we run counts as the code."
)
# a petal's next step (GL-11), at depth 3 under its reason
NEXT_HEAD = {"up": "Next step, {to}", "decide": "To decide", "repair": "Next step"}
NEXT_BY = {("publisher",): "By the publisher.", ("us",): "By us.",
           ("publisher", "us"): "By the publisher and us."}  # fmt: skip
# a system page's petal row (amended 2026-11-16): the next step's target and who acts, every need
# in the petal's disclosure; a cut reason's first clause and how many clauses follow
NEXT_SHORT = {"up": "Next step: {to}, {by}", "decide": "To decide, {by}"}
NEXT_MORE = "{need}, and {k} more"
# the one disclosure per petal, and the head of the full reason inside it
DETAILS_HEAD = "Details"
REASON_HEAD = "Reason"
# ------------------------------------------------------------------ a petal on a system page (RFC-0018 SI-3, GL-11,
# amended 2026-11-17, owner decision): what full marks need, what the system has, what it misses and who acts,
# and where to check. Every line is worded here from the board's keys; nothing is typed per system.
# the grade scale, the one line over the five petals (amended 2026-11-17, owner decision): each
# grade in its ink, best first, linked to its definition in the glossary; no paragraph
GRADE_SCALE = (("green", "Met", "met-mostly-met-partly-met"),
               ("amber", "Mostly met", "met-mostly-met-partly-met"),
               ("amber cut", "Partly met", "met-mostly-met-partly-met"),
               ("red", "Not met", "not-met"), ("red open", "Not stated", "not-stated"),
               ("red", "Failed", "failed"), ("hollow", "Not decided", "not-decided"))  # fmt: skip
GRADE_SCALE_HEAD = "Grades"
# between two grades on the scale line: an angle quote (U+203A) where the left one is higher, a
# slash between the three reds, which are not ranked among themselves, a middle dot before Not
# decided, which is on no rank
GRADE_SCALE_SEP = ("\u203a", "\u203a", "\u203a", "/", "/", "\u00b7")
# each petal's plain question, beside its name in the default row
PETAL_ASK = {
    "unforgeable": "Can a fake reply pass the check?",
    "weights_hidden": "Does a proof keep the weights secret?",
    "faithful_model": "Does the proved model answer like the original?",
    "machine_checked": "Has a computer checked that fake replies are refused?",
    "no_trusted_party": "Does checking trust a setup or a party?",
}
# what a grade comes from (the board's `sources`), beside the grade
CAME_FROM = {
    "test": "our test",
    "statement": "the publisher's words",
    "statement_reading": "the publisher's words and our reading",
    "build": "the publisher's words and our rebuild",
    "build_reading": "the publisher's words, our rebuild, our reading",
}
FROM_WORD = "from"
# the default row's three labels, then the disclosure's label
NEEDS_HEAD, HAS_HEAD = "Met needs", "Has"
# beside the grade, where a reading of ours sets it (GL-10), linked to the checks page's #reading
READING_MARK = "our reading"
# the opened petal's head over its items missing
PANEL_HEAD = {"missing": "Missing"}
# the disclosure's label: how many items Met lacks and who acts ("5 missing · publisher acts",
# "3 missing · publisher 2, us 1"); at Met, the evidence alone
MISSING_TAG = "{n} missing"
WHO_TAG = {"publisher": "publisher", "us": "us"}
WHO_ACTS = {"publisher": "publisher acts", "us": "we act"}
WHO_SPLIT = "publisher {pub}, us {us}"
EVIDENCE_TAG = "Evidence"
# the one more click down in an opened petal: this system's own facts in full
IN_FULL = "Why this grade"
# the opened petal's link to the rule that sets its grade, on the checks page
RULE_LINK = "Grading rule"
# what full marks need, per petal, in a few words for the closed row ({green}: Fidelity's Met
# threshold)
NEEDS_TINY = {
    "unforgeable": "a proved limit of 2^-128 for {run}",
    "weights_hidden": "a zero-knowledge theorem for exactly what we run",
    "faithful_model": "an average shown above {green} tokens, one request at a time",
    "machine_checked": "a rebuilt theorem reaching {run}",
    "no_trusted_party": "the publisher's words: cryptography only, no setup secret",
}
# the row's one sentence: the first item missing for Met, in plain words (amended 2026-11-17),
# by the item's `need`; GAP_ANY words an item with no sentence of its own
GAP = {
    "none": "Nothing missing.",
    "decide": "To decide: {need}.",
    "repair": "To repair: {need}.",
    "program_proved": "The limit is proved for {stated}, not {run}.",
    "program_stated": "The limit is stated for {stated}, not {run}.",
    "program_none": "The limit names no verifier.",
    "zk_batch": "The theorem covers one request per proof, not our {n}-reply batches.",
    "zk_run": "The theorem is not shown for exactly what we run.",
    "above": "Not shown above {value} tokens, which {to} needs.",
    "one_at_a_time": "Our fidelity run did not send one request at a time.",
    "reach_stated": "The theorem stops at {stated}, short of {run}.",
    "reach_none": "No theorem reaches {run}, the verifier we run.",
    "rests_sentence": "No single sentence of the publisher's says it.",
    "no_setup_secret": "A setup made a secret, in an open ceremony.",
    "hide_statement": "Nothing on hiding the weights in the {docs} we read.",
    "zk_theorem": "The publisher proves no zero-knowledge theorem.",
    "named_theorem": "No computer-checked theorem named in the {docs} we read.",
    "basis_conjectured": "The limit is a conjecture, not a theorem.",
    "basis": "The documents we read do not say whether the limit is proved.",
    "exponent": "A part of the limit is above 2^-{floor}.",
    "reading": "Met needs the publisher's own words {topics}; today that is our reading.",
}
GAP_ANY = "Missing: {need}."
# what full marks need, per petal, in one short line for the default row ({green}: Fidelity's
# Met threshold)
NEEDS_SHORT = {
    "unforgeable": "a proved limit of 2^-128 on a fake reply passing the verifier we run",
    "weights_hidden": "a theorem that proofs of exactly what we run reveal nothing about the "
    "weights",
    "faithful_model": "an average above {green} matched tokens, shown by our test, in a run of one "
    "request at a time",
    "machine_checked": "a computer-checked theorem that the verifier we run refuses fake "
    "replies, rebuilt by us",
    "no_trusted_party": "the publisher's own sentence that checking needs no secret setup and no "
    "trusted party",
}
# the blocks one click down in an opened petal (IN_FULL), in order: this system's own facts
PETAL_BLOCK = {"needs": "Met needs, in full", "has": "What it has", "missing": "Each item today",
               "records": "Our records", "terms": "In the field's terms",
               "limits": "Limits the publisher states, which the grade does not count"}  # fmt: skip
# an open question in our rules, linked to the RFC
OPEN_QUESTION = "an open question in our rules"
# the Missing line of the default row and the Missing block: counts, who acts, the group heads
WHO = {"publisher": "for the publisher", "us": "for us"}
MISSING_NONE = "nothing."
MISSING_GROUP = {"first": "To reach {to}", "then": "Then, to reach {to}", "decide": "To decide",
                 "repair": "To repair"}  # fmt: skip
# the opened petal's Missing block: each group's head, who acts in parentheses where one acts
MISSING_STEP = {"first": "For {to}", "then": "For {to}", "decide": "To decide",
                "repair": "To repair"}  # fmt: skip
# the topics our reading covers, per fact: (subject, predicate), so two that share a subject
# read "that the limit holds ... and is ..."
READING_TOPIC = {
    "adversary": ("the limit", "holds against any cheating prover"),
    "parameters": ("the limit", "is for the settings we run"),
    "unit": ("the limit", "is for a whole reply"),
    "batch": ("the limit", "is for each reply checked on its own"),
    "conditions_shown": ("its condition", "holds for our files"),
    "program": ("the limit", "is for the verifier we run"),
    "basis": ("the limit", "is proved"),
    "stated": ("a proof", "hides the weights"),
    "proof": ("the theorem", "is for what we run"),
    "programs": ("its programs", "keep the weights secret"),
    "visible_listed": ("its list of what stays visible", "is complete"),
    "verifier_gets_weights": ("the verifier", "is not given the weights"),
    "reach": ("the theorem", "covers the model's computation"),
    "conclusion": ("its conclusion", "is about the model"),
    "rests_on": ("soundness", "rests on cryptographic assumptions only"),
}  # fmt: skip
# the opened petal's evidence lines, then the heads one click down
EVIDENCE = {
    "quotes": "Publisher's words at {pin} ({n})",
    "notes": "Our notes ({n})",
    "docs": "Documents we read ({n})",
    "forms": "Zero knowledge, as stated ({n})",
    "visible": "What stays visible ({n})",
    "head": "Evidence",
    "from": "From {src}",
    "points": " ({n} points)",
    "checks_short": "Our {names} check{s}: {state} ↓",
    "rebuild_short": "Our rebuild: exit code {code}",
    "fidelity_short": "Our fidelity run, {n} ↓",
    "none_short": "no test of ours bears on it",
    "rebuild": "Our rebuild:",
    "outside": "Outside the grade:",
    "used": "The grade uses our reading {this}.",
    "not_used": "It does not use our reading {this}; Met needs the publisher's words there too.",
}  # fmt: skip
# what each petal's tests do, under Evidence
RECORDS = {
    "unforgeable": "our Model, Prompt and Reply tests each give the verifier a proof with the "
    "wrong model, prompt or reply. {state}",
    "weights_hidden": "our Verify without weights test checks that every verdict came with no "
    "model file and no GPU. {state}",
    "machine_checked": "our Model, Prompt and Reply tests {state}.",
    "no_trusted_party": "no test of ours bears on this property.",
}
RECORD_LINK = "Record ↗"
SCOPE_LINK = "the scope table further down this page ↓"
# the checks whose failure a petal's red names (PETAL_RULE), so a petal and its checks light
# together on a system page
PETAL_CHECKS = {"unforgeable": ("model", "prompt", "reply"), "weights_hidden": ("no_weight_file",),
                "faithful_model": ("fidelity",), "machine_checked": ("model", "prompt", "reply"),
                "no_trusted_party": ()}  # fmt: skip
# ------------------------------------------------------------------ the figures (RFC-0018 §Cost, FI-7)
# The figures the checks page defines: the anchor on the checks page, the figure's name, and the
# definition as (label, words) lines, a line with no label its figure's own. {slots}, {gap} (the
# release-group gap), {full} (the share of the highest rate that is full load) and {top} (the
# ladder's top concurrency) are the level file's constants; 3 and 5 % (steady.min_later_groups,
# steady.tolerance), 1 (baseline.ladder's first rung), 64 and 512 (kl.texts, kl.tokens) are typed
# as the level's. "fidelity-figure" is the figure the ladder prints as Fidelity (SI-9); "fidelity"
# is the check's anchor.
FIGURE_NAME = {"multiple": "Cost vs serving", "cost": "Cost per reply", "rate": "Tokens per second",
               "check-time": "Verify time per reply", "proof-size": "Proof size per reply",
               "fidelity-figure": "Fidelity figure", "kl": "KL to the original weights"}  # fmt: skip
# a figure's head where its unit stands beside it: the unit says "per reply", so the head does
# not; and the surface names fidelity, not the metric (KL and the matched tokens' bar are under
# Fidelity on a system's page)
FIGURE_HEAD = {"multiple": "Cost vs serving", "cost": "Cost", "check-time": "Verify time",
               "proof-size": "Proof size", "fidelity": "Fidelity", "serving": "Serving",
               "rate": "Tokens per second"}  # fmt: skip
# where a head links on the checks page, where its anchor is not its key: the Fidelity figure has
# a rule of its own there, apart from the check it does not set (SI-9)
FIGURE_ANCHOR = {"fidelity": "fidelity-figure"}
# how the headline is computed, in one plain sentence (B5): at the Cost section's head and first
# in the headline figure's title, by the figure printed (`chrome.lead_figure`); {on} the GPUs
HOW_MULTIPLE = {
    "session_multiple": "Cost vs serving divides the GPU-seconds a proved reply took over whole "
    "sessions (from the start of the commit call to the last proof: commit, generation and "
    "proving, not the loading before the commit) by the GPU-seconds serving the same reply took "
    "with no proof, at full load, {on}, at the same GPU price on both sides.",
    "multiple": "Cost vs serving divides the GPU-seconds each further proved reply took in steady "
    "state (generation included) by the GPU-seconds serving the same reply took with no proof, "
    "at full load, {on}, at the same GPU price on both sides.",
}
HOW_ON = {True: "both on {gpu} GPUs", False: "proved on {gpu}, served on {serving}"}
SERVING_GPU = "H200"  # CO-4: the serving baseline runs on the fewest H200 that hold the model
# CO-8 (adopted 2026-11-16): reply tokens per GPU-second under Cost (depth 3); amended 2026-11-16:
# the proved and the served rate also print as one line under the multiple (`overview.rate_html`)
REPLY_TOKENS_HEAD = "Tokens per second"
# that line (Q41): the proved rate's word after its number ("2.027 proved"), then its unit and
# GPU ("tokens/s per H200"); a model's head prints its served rate in the same unit
RATE_PROVED = "proved"
RATE_PER = "tokens/s per {gpu}"
# its title, first: how the two rates are read against the multiple above them
RATE_HOW = ("how: the request's {tokens} reply tokens over the GPU-seconds one reply took, on "
            "one GPU")  # fmt: skip
RATE_IS = "ratio: served ÷ proved = {multiple}, Cost vs serving"
FIDELITY_TITLE = "leading tokens matching the original, mean"  # in a fidelity word's title
# Fidelity as a figure (RFC-0018 SI-9, amended 2026-11-14): FI-10's mean as a percentage of the
# reply's positions, beside the model's Q8_0 and Q4_K_M copies; it sets no state
FIDELITY_AGAINST = ("q8_0", "q4_k_m")  # the controls printed beside a row's Fidelity
FIDELITY_FIG_TITLE = ("Fidelity figure: the share of reply positions where the system's top token is "
                      "the original's reply token, fed the prompt and then that reply token by "
                      "token")  # fmt: skip
# the copies printed beside a row's Fidelity at depths 1 and 2 (RFC-0018 SI-9, amended
# 2026-11-16): plain words; their ids (Q8_0, Q4_K_M) stand in titles and at depth 3
COPY_WORD = {"q8_0": "8-bit copy", "q4_k_m": "4-bit copy"}
# what the row proves, beside every Fidelity figure: the weight bits (the workload record) and the
# number format (the properties file, the publisher's words), one word per recorded value
FORMAT_WORD = {"integer": "integer", "fixed_point": "fixed-point",
               "floating_point": "floating-point"}  # fmt: skip
PROVED_HEAD = "proved"
FORMAT_HEAD = "number format"  # the depth-3 Proved line's words where none is stated
# the Cost section's Serving line points to the Proved line at the head of Fidelity
PROVED_LINK = ("the copy this row proves", " is under Fidelity")
# how a workload record found its weight bits, in words
BASIS_BITS = {"computed": "computed from its files", "stated": "as the publisher states it",
              "file_size": "from its file size"}  # fmt: skip
# why the surface figure is top-token agreement, in one line ({tokens}: the request's reply tokens)
WHY_HEAD = "Why top-token agreement: "
WHY_TOP_TOKEN = (
    "Why top-token agreement: a greedy reply is the top token at each position, so this counts "
    "how often the proved model makes the original's choice, at every one of the {tokens:,} "
    "positions, not only up to the first difference."
)
FIDELITY_CHECK_TITLE = "Fidelity check: {state}"


def beside_unit(name):
    """A figure's name where its unit follows it: "per reply" is the unit's to say."""
    return name.replace(" per reply", "")


FIGURE_RULE = {
    "multiple": (
        ("multiple", "m over b, on one model. GPU time counts only the H200 GPUs bound to the "
         "job."),
        ("m", "GPU-seconds per proved reply, generation included: the mean of {slots} sessions. "
         "Proofs released within {gap} of the previous one form a release group. m runs from the "
         "first group's last release to the session's last, over the replies released after it. "
         "Where a system generates all its replies in a phase of its own, m adds that phase's "
         "GPU-seconds over the session's replies."),
        # CO-4; FP8 on Maverick is the level file's serving record (the original is 16-bit, FI-1)
        ("b", "GPU-seconds per reply when the same request is served without a proof. The model "
         "publisher's own release (FP8 on Llama 4 Maverick) runs on the pinned engine and the "
         "fewest NVIDIA H200 GPUs that hold it, at full load. Full load is the lowest concurrency, "
         "doubling from 1 to {top}, whose rate reaches {full} of the highest. If that is {top}, the "
         "model has no b (not saturated)."),
        ("whole sessions", "A row has m when each of its {slots} sessions has at least 3 groups "
         "after the first, each group's time per reply within 5\u202f% of their median. Otherwise "
         "it has no multiple and prints its session GPU-seconds per reply over b, labelled "
         "\u201cwhole sessions of N replies\u201d."),
        ("parts", "Where a system generates its replies in a phase of its own, the figure "
         "splits in two, each over b: generation, and the rest (proving under m, commit and "
         "proving under whole sessions). Not every system times them apart, so they print only "
         "under Cost on its own page. The order reads the figure, never a part."),
    ),
    # CO-8 (amended 2026-11-16): the two rates under the multiple; {reply_tokens} the level's
    "rate": (
        ("", "The request's {reply_tokens} reply tokens over the GPU-seconds one reply took, on one "
         "GPU, printed in tokens/s per GPU with the GPU named. Proved: over whole sessions, as "
         "Cost vs serving counts them. Served: the same reply served without a proof, at full "
         "load, on the same GPU type. Served over proved is Cost vs serving."),
        ("", "Both depend on the GPU, so neither ranks a row: the order reads m, the steady "
         "multiple (OR-3), never a rate."),
        ("", "Prompt side (prefill) and reply side (decode) are not timed apart in the records."),
    ),
    "cost": (
        ("steady", "m in USD, at the release's price for one H200 GPU-hour."),
        ("session", "GPU-seconds from the start of commit to the release of the session's last "
         "proof, over its replies, generation included, in USD at the same price: the mean of "
         "{slots} sessions."),
    ),
    "check-time": (
        ("", "The wall time of the verify calls on a session's proofs, summed, over the session's "
         "replies: the mean of {slots} sessions. A second verify never replaces the session's own "
         "time."),
    ),
    "proof-size": (
        ("", "The bytes of every file of a session's proofs, as stored, over the session's replies. "
         "A proof that covers several replies is counted once. The mean of {slots} sessions, in MB "
         "(1\u00a0MB is 1,000,000 bytes)."),
    ),
    "fidelity-figure": (
        ("", "The share of reply positions where the system's top token is the original's reply "
         "token, when the system is fed the prompt and then that reply token by token. It is the "
         "mean over the prompts, as a percentage, with 0 for a prompt the system's own code "
         "declines. The model's 8-bit and 4-bit copies' percentages (Q8_0, Q4_K_M) are printed "
         "under it."),
        ("", "100\u00a0% is the original's choice at every position. It counts chosen tokens "
         "and compares no probabilities: KL does."),
        ("", "Computed by the system's own code on the reference reply, not by the proved "
         "computation. It sets no state."),
        ("", WHY_TOP_TOKEN.replace("{tokens:,}", "{reply_tokens}")),
    ),
    "kl": (
        # FI-7 over the KL texts (PR-3; 64 and 512 are the level file's kl.texts and kl.tokens)
        ("", "Mean KL divergence per scored token, in nats, of the file the system commits against "
         "the original, over 64 texts of 512 tokens. Computed by llama.cpp "
         "on the committed file, not the proved computation. It gates nothing."),
        ("not measured", "Printed with the reason where llama.cpp cannot run the original (Llama 4 "
         "Maverick's 16-bit file), or cannot load the committed file and the system's adapter "
         "returns no distributions of its own."),
    ),
}  # fmt: skip
# a figure in one line, for its search entry: what the figure is, about 95 characters at most
FIGURE_LINE = {
    "multiple": "GPU-seconds per proved reply, generation included, over a served reply's at full "
    "load.",
    "rate": "Reply tokens per GPU-second, proved and served on the same GPU type. Their ratio is "
    "Cost vs serving.",
    "check-time": "Wall time of the verify calls on a session's proofs, over its replies: the mean "
    "of {slots} sessions.",
    "proof-size": "A session's stored proof bytes over its replies, in MB. A proof of several "
    "replies counts once.",
    "fidelity-figure": "Share of positions where the system's top token is the original's reply "
    "token, fed prompt and reply.",
    "kl": "KL per token, committed file against the original, by llama.cpp. It gates nothing.",
}
# a rung's fidelity reference, by its stored precision (FI-1)
# (a no-break hyphen: the precision never splits from its number at a line's end)
REFERENCE_WORD = {"bf16": "16\u2011bit", "f16": "16\u2011bit", "f32": "32\u2011bit"}


def kl_head(dtype):
    """The KL column's head: one name on every page; the precision of each model's reference is
    in the figure's definition."""
    return FIGURE_NAME["kl"]


# the order rule (RFC-0018 OR-1 to OR-6, GL-4), as (label, words). {margin} is the level's.
# "Session m" is one counted session's m.
ORDER_RULE = (
    ("ranked", "Only systems that passed on a model are ranked."),
    # OR-2; no floor: Non-Goals (printed as stated), Alternatives (a security floor, rejected)
    ("unranked", "A system that passed is ranked only if its publisher states, at the pinned "
     "commit, that an accept means the reply is the committed model's own greedy reply to the "
     "prompt, or is read as stating it (marked read as, with its quotes), and the level file records a numeric security level that its publisher states "
     "there, for at least one verifier it ships. Otherwise it is listed as Passed, not ranked, with "
     "the reason. Level 1 sets no minimum level."),
    ("above", "One system is placed above another when both have a multiple, its mean multiple is "
     "at least {margin} lower, and its highest session m is below the other's lowest. A system "
     "with a multiple is placed above one without. Two systems without one compare the same way, "
     "on session cost per reply."),
    ("position", "1 plus the number of systems placed above it, so equal counts share a position. "
     "It is printed beside the count of systems run on that model."),
    ("below", "Under the ranked systems: passed and unranked, then not passed, each group in "
     "alphabetical order. A system that has not passed prints its checks and figures and has no "
     "position."),
    ("largest model with a passed row", "The largest model, by total parameters, with at least one system "
     "that passed and whose publisher states that an accept is the model's own reply."),
    ("glyph", "The glyph never moves a position."),
    ("models", "Nothing is ranked across models."),
)  # fmt: skip
# the checks page's table of what we test and what we read (RFC-0018 CH-6, GL-1, OR-2, SI-4a):
# what a line is about, where a row shows it (checks, petals, figures and the order rule, by their
# addresses on the checks page; "figures" stands for every figure) and how it is known
KNOW_HEAD = "What we test and what we read"
KNOW_COLS = ("What", "Where", "How we know it")
KNOW_WORD = {"test": "we test it", "read": "we read it from the publisher's documents",
             "neither": "no check tests it; the petal prints what the publisher states"}  # fmt: skip
KNOW_LINES = (
    ("completeness: the publisher's prover, run honestly, gives accepted proofs", ("run",),
     "test"),
    ("binding: a changed weight, commitment, prompt token or reply token is refused",
     ("model", "prompt", "reply"), "test"),
    ("verdicts reached with no model file and no GPU", ("no_weight_file",), "test"),
    ("how close the proved replies stay to the original's", ("fidelity", "faithful_model"),
     "test"),
    ("every figure", ("figures",), "test"),
    ("soundness, as a stated bound", ("unforgeable",), "read"),
    ("zero knowledge", ("weights_hidden",), "read"),
    ("formal proofs", ("machine_checked",), "read"),
    ("setup", ("no_trusted_party",), "read"),
    ("the stated security level", ("unranked",), "read"),
    ("that an accept is the committed model's own greedy reply", ("unranked",), "read"),
    ("soundness against a cheating prover", ("unforgeable",), "neither"),
    ("zero knowledge of the programs the row runs", ("weights_hidden",), "neither"),
)  # fmt: skip
KNOW_WHERE = {"figures": "Figures", "unranked": "Order"}  # the two that are no check or petal
# the checks page in one sentence: its description and its search entry
CHECKS_DESC = (
    "The rules behind a row of the ladder: the six checks, each figure, the order and the glyph's "
    "five petals."
)
# the words of a rule that link to where Learn gives the rule's reason (/method), by the rule's
# constant and its line's label: (phrase, address). The phrase is linked where the line holds it,
# or the label itself where it is the phrase
REASON_LINK = {
    ("NOT_TESTED", ""): ("not tested", "/method#the-checks"),
    ("summary", ""): ("a passed check raises none", "/method#order-and-the-glyph"),
    ("FIGURE_RULE", "parts"): ("generation", "/method#the-figure"),
    ("CHECK_MORE", "bar"): ("bar", "/method#the-checks"),
    ("ORDER_RULE", "models"): ("across models", "/method"),
}
# ------------------------------------------------------------------ the scale page (RFC-0018 SI-7)
SCALE_LOG = "log scale"  # beside an axis's unit
SCALE_SERVING = "Serving"  # a lane's foot: serving's line and its stored figure
# a model no system has run on (the ladder, the scale page); its serving line keeps "not run yet"
SCALE_NOT_RUN = "no system run yet"
# the start of the scale page's description and search line, before its figures' names
SCALE_LEAD = "Every system run, on a log axis"
# beside the size tab of the frontier's rung on the ladder (OR-6: the largest with a passed row)
FRONTIER_WORD = "Largest model with a passed row"
# ------------------------------------------------------------------ the mandate page
# The headline, then who runs it, its ties, what we do, what we do not do, how to check us and how
# a row is changed, with the dated corrections: each line
# (a plain label, the rule that binds it, the file that holds the rule with its section's anchor,
# the words; two rules of one file in two sections: a pair of each; a source outside the
# repository: its link's words and its address). A line with no file is the owner's commitment. {lead} and {builder} are the names
# facts.json `credit` gives, linked as the footer links them. The members (`credit`) are listed in
# the section MANDATE_MEMBERS_IN names, once any has agreed.
RFC_18 = "rfcs/0018-level-1-ladder.md"
MANDATE_BELIEF = (
    "We believe a claim about which AI model answered should come with evidence anyone can "
    "afford to check."
)
# the page's description, share text and search line
MANDATE_DESC = "Who runs Inference proofs, what it commits to and how to check its figures."
MANDATE = (
    ("Who runs it", (
        ("Run by", "", None, "{lead}."),
        ("Built by", "", None, "The {builder}, led by {lead}."),
    )),
    ("Ties", (
        ("Its business", "lucidcomputing.ai", "https://lucidcomputing.ai/", "{lead} runs this "
         "project and builds the site. It sells inference run in hardware enclaves: \u201cAll "
         "inference runs inside hardware-encrypted Trusted Execution Environments.\u201d It "
         "builds none of the listed provers. Two systems listed as another kind of check, "
         "Private ML SDK and Tinfoil, are enclave systems too."),
        ("Rules", "Conflicts of Interest", f"{RFC_18}#conflicts-of-interest", "Level 1's rules "
         "were drafted with an AI model made by FlashProve's publisher. RFC-0018 names the rules "
         "this touches and the readings taken that favour FlashProve."),
        ("SASH's change", "pull request #36",
         "https://github.com/sg-ai-safety-hub/zk-inference-prover/pull/36", "SASH runs commit "
         "4f41667 of pull request #36 to SASH, written by this project's owner and not merged "
         "upstream; a SASH maintainer has since added commits to it. At upstream's own commit, "
         "eb95bfa, SASH refused one of the level's prompts."),
        # {se3a} and {se3b}: the board's replaced and ineligible sessions, in words (pages.py)
        ("After the freeze", ("CH-1a", "SE-3a", "SE-3b", "SI-4a"),
         (f"{RFC_18}#the-six-checks", f"{RFC_18}#sessions-and-what-is-recorded",
          f"{RFC_18}#sessions-and-what-is-recorded", f"{RFC_18}#site"), "Four rules added to "
         "RFC-0018 after the level was frozen bear on rows. Under CH-1a, FlashProve's Model check "
         "passed on its prover answering \u201cfailed\u201d. Under SE-3a, {se3a}. Under SE-3b, "
         "{se3b}. Under SI-4a, a passed row takes a position only on its publisher's recorded "
         "statement that an accept is the committed model's own greedy reply, or on our reading "
         "of one; LV-1 reserves such a rule for a new level."),
    )),
    ("What we do", (
        ("Pinned commit", "rule 1", "AGENTS.md#hard-rules", "Each system runs at one pinned "
         "public commit, and our adapter passes no setting the system's documentation does not "
         "name. FlashProve runs its upstream commit unchanged. SASH runs a commit of a pull "
         "request to SASH that this project's owner wrote and upstream has not merged (see Ties)."),
        ("Same request", "Prompts, PR-2", f"{RFC_18}#prompts", "Every system gets the same "
         "request. Its prompts come from a public randomness beacon: drand's first round after "
         "the commit that froze the level, by that commit's own time, which our own clock sets. "
         "GitHub recorded each freeze 2 s after that time. The level was frozen three times on "
         "2026-11-11, and each freeze drew new prompts; every counted run uses the third draw."),
        ("Sample size", "rule 5", "AGENTS.md#hard-rules", "Cost figures come with their sample "
         "size and each counted session's value, never one best run."),
        ("Computed", ("CO-6", "CH-6"), (f"{RFC_18}#cost", f"{RFC_18}#the-six-checks"),
         "Check states and figures are computed "
         "from stored run records. No reviewer sets a state or types a figure."),
        ("Reproduced first", "CH-8", f"{RFC_18}#the-six-checks", "When a verifier accepts a "
         "changed model, prompt or reply in our adapter, the check reads not decided (not "
         "reproduced), and the publisher is told. The check reads failed only once a record "
         "shows the system's own command, run outside our adapter, accepting the same input."),
    )),
    ("What we do not do", (
        ("Payment", "", None, "We take no payment for a listing, a position or a run."),
        ("Provers", "What this project is", "AGENTS.md#what-this-project-is", "We run provers. "
         "We do not build our own or certify any."),
        ("Not tested", "Non-Goals", f"{RFC_18}#non-goals", "No check tries to forge a proof or "
         "recover the weights. The system's page quotes the publisher on soundness and weight "
         "secrecy."),
        ("Ranking", "OR-1", f"{RFC_18}#order", "We rank only systems that passed the six "
         "checks, and never across models."),
    )),
    ("How to check us", (
        ("Labels", "rule 2", "AGENTS.md#hard-rules", "Every figure carries its unit and its "
         "record, and a timed figure says what was timed. Nobody else has rerun any of our "
         "runs."),
        ("Repository", "Licence", "README.md#licence", "The rules, the adapters, the measuring "
         "code and the run records are in one public repository. Proofs, weights and other bulk "
         "files stay outside it, named by digest. The proofs are not public yet."),
        ("Rebuild", "Tier 1", "docs/REPRODUCE.md", "Anyone can rebuild the board from the run "
         "records, recompute every figure and validate the repository on a laptop, with no GPU. "
         "Verifying a proof again needs its bytes."),
    )),
    ("Changes and corrections", (
        ("Contest a row", "issues", "https://github.com/ai-verification-observatory/"
         "inference-proofs/issues", "Open an issue naming the row and the fact you hold wrong, "
         "with your source. The answer goes in the issue, and a change goes in the list below."),
        ("A petal", "GL-1", f"{RFC_18}#the-glyph", "A statement petal moves on a sentence the "
         "publisher wrote at the pinned commit, quoted with its link, or on a failed check. A "
         "state we read rather than copied says so and is graded Mostly met at most. Fidelity "
         "moves on a fidelity run."),
        ("A check", "CH-6", f"{RFC_18}#the-six-checks", "A check moves on a stored run record "
         "only. A changed input accepted in our adapter fails a check once the system's own "
         "command accepts it too."),
    )),
)  # fmt: skip
# the corrections the mandate lists in the section MANDATE_CORRECTIONS_IN names, newest first:
# (date, words). A correction is added here when it is made; none is removed.
# the board's replaced (SE-3a) and ineligible (SE-3b) sessions in the mandate's words, one
# clause per row that has any; with none, the empty case
SE3A_ROW = "{n} {name} {slot} went to a later session"
SE3A_NONE = "no slot went to a later session"
SE3B_ROW = "{n} {name} {session} ran on a host whose self-test failed and no longer counts"
SE3B_NONE = "no session was dropped"
MANDATE_CORRECTIONS_IN = "Changes and corrections"
MANDATE_CORRECTIONS = (
    ("2026-11-16", "SASH's slot 2 counts a new session, run on a host whose self-test passed "
     "and verified again on a host with no GPU. SASH's row reads Passed again."),
    ("2026-11-16", "The petals are renamed Integrity, Confidentiality, Fidelity, Formally verified "
     "and Trust assumptions, and the state words are plain. No state, step, position or figure "
     "moved."),
    ("2026-11-15", "SASH's Trust assumptions petal is read by the same test as FlashProve's: from "
     "Not stated to Mostly met, read as. Both rest on our reading of the publisher's sentences, "
     "printed with the petal."),
    ("2026-11-15", "The mandate said two SASH slots went to later sessions. One did; slot 2's "
     "replacement ran on a host whose self-test failed and no longer counts."),
    ("2026-11-15", "A SASH session that failed the machine self-test no longer counts "
     "(RFC-0014); SASH's row reads Not passed yet until a replacement session runs."),
    ("2026-11-15", "A state that rests on our reading of a publisher's documents, not on a "
     "sentence that says it, is marked \u201cread as\u201d and graded Mostly met at most, for every "
     "system. FlashProve's Trust assumptions petal moves from Met to Mostly met."),
    ("2026-11-15", "SASH's pin is disclosed: it runs a pull request this project's owner wrote. "
     "The mandate said our adapter changes no source."),
    ("2026-11-15", "The beacon line said nobody chose the prompts. The freeze time is ours, and "
     "each of the three freezes drew new prompts."),
    ("2026-11-15", "The reasons a system is not run follow one written rule: DeepProve, JOLT "
     "Atlas and zkLLM are listed under no public verifier, zkGPT under a different statement."),
)  # fmt: skip
MANDATE_MEMBERS_IN = "Who runs it"
# the mandate's line on the level (its label is the level and its state, linked to the level
# file): the one home of the level's history (three freezes on 2026-11-11, each followed by its
# beacon round, in the git history of levels/L1.yaml and levels/L1-beacon.json; the file unchanged
# since; LV-1; RFC-0018's changes since, and the rules added since that decided rows, which
# MANDATE_LEVEL_LINK leads to: CH-1a, SE-3a)
MANDATE_LEVEL_IN = "How to check us"
MANDATE_LEVEL = (
    "The models, the request, the prompts' corpus and beacon, and the constants of the cost, "
    "fidelity and order rules are one file. It was frozen three times that day, before the first "
    "counted run, each time with a fresh beacon round, and has not changed since. A change of "
    "rule is meant to make a new level. But RFC-0018 has changed since the last freeze, and some "
    "rules added to it decided rows."
)
# the words of the level line that link to where Learn names those rules: (phrase, address)
MANDATE_LEVEL_LINK = ("decided rows", "/method#judgement-and-changes")
# why a check is undecided (its cause as the board stores it): a system page's title for the cause,
# lower case and with no full stop; the checks page prints each as a sentence (#cause-<cause>)
CHECK_CAUSE_WORD = {
    # CH-5: "with the publisher's sentence. The row cannot pass."
    "system limit": "the system cannot do what this test needs (its publisher's words are "
    "quoted), so the row cannot pass",
    "not run": "not run yet",
    "not resolved": "the test ran, and its result does not count yet",
    "not reproduced": "a verifier accepted a changed input in our adapter; not yet repeated with "
    "the system's own command",
}
# what decides a check that is not decided, and who acts, by (check, cause); None for any check.
# {session}: the session the check's note names, by date and ordinal. Printed under its cause
CHECK_DECIDE = {
    ("no_weight_file", "not resolved"): ("the proofs of session {session} verified again, in the "
                                         "run's image, on a host with no GPU", "us"),
    (None, "not reproduced"): ("the same changed input run with the system's own command, "
                               "outside our adapter", "us"),
}  # fmt: skip
# the line that opens the not-decided causes (a check not decided is never worded as a failure;
# the standing words are chrome.not_passed's)
CHECK_CAUSE_LEAD = (
    "Not decided is not failed: a row short of passing only because checks are not decided reads "
    "Not passed yet. A verifier trial outside the counted suite, printed on a system page beside "
    "the check whose change it makes, sets no state."
)

# ------------------------------------------------------------------ labels of a stored figure
SCOPE_SHORT = {None: "", "prove.steady": "steady", "prove.session": "session",
               "whole_wall": "session", "verify": "verify", "commit": "commit",
               "setup": "setup", "verify.single_thread": "verify, one thread",
               "serving": "full load"}  # fmt: skip
WHOLE_WALL_SPAN = "from commit to the last proof"  # what a whole session's time runs over
SCOPE_WORD = {
    None: "not a timed number",
    "setup": "setting up",
    "commit": "committing to the model",
    "prove.steady": "steady state, after the first release group",
    "prove.session": "the whole session, from the start of the commit call to the last proof",
    "whole_wall": f"the whole session, {WHOLE_WALL_SPAN}",
    "verify": "verifying",
    "verify.single_thread": "verifying on one CPU thread",
    "primitive": "one primitive",
    "serving": "serving at full load",  # the serving baseline's, in its title (CO-4)
}
GRADE_WORD = {
    "measured": "recorded by our harness",
    "derived": "computed by our code from recorded numbers",
    "projected": "projected, not measured",
    "external": "as the system publishes it",
    "asserted": "set in the reference file",
}
TIER_WORD = {
    "reported": "our runs only, not rerun by anyone else",
    "peer-reviewed": "reviewed, not rerun",
    "reproduced": "rerun by an unaffiliated runner",
}
NULL_WORD = {
    "not_externally_observable": "not observable from outside the system",
    "fewer_than_two_proofs": "fewer than two proofs",
    "not_applicable": "does not apply",
    "step_failed": "the step that records it failed",
    "not_measurable_on_profile": "not measurable on this GPU",
    "missing_input": "a number it is calculated from is missing",
}
# in place of a null reason: a steady figure on a row with no steady state (CO-3, CO-5)
NO_STEADY_WORD = "not every session had a steady state"
# the line under the serving baseline's figure: it is timed at full load, not steady (CO-4)
FULL_LOAD_WORD = "full load"
# CO-7: the two parts a multiple or a GPU time splits into where the system generates in a phase
# of its own. A session's second part holds commit as well (most of it), so it is never "proving"
PART_WORD = {"proving": "proving", "generation": "generation",
             "commit_and_proving": "commit and proving"}  # fmt: skip
# before a part's name where it stands beside its whole in a table's head (the sessions table);
# under its whole, a part's name stands alone
OF_WHICH = "of which"
# the Cost block's head over the multiple's two parts (CO-7, amended 2026-11-17: printed only there)
PARTS_HEAD = "Cost vs serving, in two parts"
# the GPU time per reply after the first release group, m (CO-3): its name beside the serving and
# session GPU times (Cost), its full name (that line's title, the sessions column's), its column
# (beside Session; a session with none prints why under its "none")
M_HEAD = "Steady GPU time per reply"
M_NAME, M_COL = "GPU time per reply after the first release group (m)", "Steady"
# CO-5's label for a figure of the whole sessions, N the level's replies per session
WHOLE_SESSIONS = "whole sessions of {n:,} replies"
STEADY_STATE = "steady state"  # under a steady multiple, before its sessions (CO-3)


def session_count(k):
    """A count of sessions in words: "3 sessions", "1 session"."""
    return f"{k:,} session" if k == 1 else f"{k:,} sessions"


# the fidelity table (FI-5, FI-6): the replies' figure, a control's name as the table prints it
# (its id, with the llama.cpp pin that makes a quantized copy, in the title), the p line. FI-2's
# words: a quantized copy by its bits, which llama.cpp's type names (Q8_0 is 8-bit, Q4_K_M mostly
# 4-bit), the id kept in parentheses at this depth; a quarter of the blocks, both models; the
# smaller model is named in the level file
PREFIX = "Fidelity check: matched leading tokens, mean"
CONTROL_NAME = {"reference-2": "the original, run again",
                "q8_0": "8-bit copy (Q8_0)", "q4_k_m": "4-bit copy (Q4_K_M)",
                "q3_k_s": "3-bit copy (Q3_K_S)", "q2_k": "2-bit copy (Q2_K)",
                "drop-every-4th-block": "a quarter of blocks cut",
                "smaller-model": "a smaller model"}  # fmt: skip
# the table's first two heads: whose replies a row holds, and whether it is the system, an honest
# copy or a damaged one (FI-2)
FID_WHO = "Replies"
FID_KIND = "Kind"
KIND_TERM = "Honest and damaged copies"  # the glossary entry a control's kind links to
# a check's record as its link reads, by the file's name (the path stands in the link's title)
RECORD_WORD = {"run.json": "run record", "controls.json": "controls", "verify-trace": "verify traces",
               "reverify.json": "re-verify record", "fidelity.json": "fidelity record"}  # fmt: skip
P_ABOVE = "above the bar: {p}"  # {p} reads "p = 0.0058" or the floor's bound (`p_said`)
P_FLOOR = ", the test's floor"  # after a p at the lowest value its test can give (FI-4)
# the reference's precision in words, where a line names the original (FI-1)
DTYPE_BITS = {"bf16": "16-bit", "f16": "16-bit", "f32": "32-bit"}
# a column's head as the table prints it, on every width: the measure's name alone (its full
# name, with what it is a mean of and on which reply, is the head's title and the glossary's)
FID_HEAD = {"Fidelity figure: top-token agreement, mean": "Top-token agreement",
            "Fidelity check: matched leading tokens, mean": "Matched leading tokens",
            "KL to the original, on its reply": "KL divergence",
            "KL to the original weights": "KL on fixed texts"}  # fmt: skip
TF_INTERVAL = "95\u00a0% interval {low} to {high}\u202f%"  # SI-9, under and in a percentage's title
# the limits under the table (depth 3), each generated from the board, the level and its records
LIM_ORIGINAL = "Original: {repo} at {rev}, {bits}."
LIM_COPY = " It is a copy on the Hub, not {publisher}'s own repository."
LIM_CEILING = (" Fed its own reply, the original's engine picks that reply's token at {ceiling}\u202f%"
               " of positions: the figure of the original itself.")  # fmt: skip
LIM_ENGINES = "Engines: {parts}."
LIM_PART = {None: "the original and the controls run with it", "controls": "the quantized controls"}
LIM_VLLM = "{part} in vLLM, every prompt sent in one call"
LIM_LLAMA = "{part} in llama.cpp, {slots} at a time"
LIM_PROMPTS = ("Prompts: {tokens}-token windows of {texts} texts from {hosts} ({licences}), with "
               "no chat template.")  # fmt: skip
TF_AGREE = "Fidelity figure: top-token agreement, mean"
TF_KL = "KL to the original, on its reply"
# the summary of FI-11's tests: they are on top-token agreement and set nothing (the matched
# leading tokens set the check and the petal)
TF_TESTS_ON = "on top-token agreement; they set no state"
# the two teacher-forced columns by name: the lead and FI-13's label say which columns they are about
TF_BOTH = "top-token agreement and KL divergence"  # the table's heads for the two (FID_HEAD)
# the KL head's title (FI-12: the tokens both lists hold, every other token one outcome)
TF_KL_TITLE = (
    "KL compares, at each position, each token that both lists of the {k:,} most probable tokens "
    "hold, with every other token pooled as one outcome."
)
TF_SUB = "median {median}"
TF_FAILED = "{k:,} of {n:,} prompts failed, counted as 0"
TF_TEST = "{name} above it: {above} · below it: {below}"  # each p as `p_said` reads it
TF_KL_SUB = "n\u00a0=\u00a0{n:,}"  # under a KL figure whose n is not the block's


# ------------------------------------------------------------------ numbers (display only)
def sig(v, d=4):
    """v at d significant digits, thousands separated."""
    if v == 0:
        return "0"
    places = d - 1 - math.floor(math.log10(abs(v)))
    if places >= 0:
        return f"{v:,.{places}f}"
    return f"{round(v, places):,.0f}"


# a stored unit -> how its value reads: (number, unit words). One unit per quantity, whatever the
# value's size: every row of a column, and every page, reads a quantity in the same unit (money in
# USD, times in seconds, sizes in MB), so two rows are compared by their numbers alone. Per request
# reads per reply: the request is the level's one request, and its reply is what each proof covers
# (RFC-0018)
def number(v, unit):  # noqa: PLR0911 (one return per stored unit)
    if unit == "ratio":
        return sig(v), "×"
    if unit == "gpu_s/request":
        return sig(v), "GPU-s/reply"
    if unit == "s/request":
        return sig(v), "s/reply"
    if unit == "USD/request":
        return sig(v), "USD/reply"
    if unit == "B/request":
        return sig(v / 1e6), "MB/reply"
    if unit == "USD/gpu_hour":
        return sig(v), "USD/GPU-hour"
    if unit == "nat/token":
        return sig(v), "nats/token"
    if unit == "gpu_s/token":  # CO-7 (amended 2026-11-15): generation per reply token
        return sig(v), "GPU-s/reply token"
    if unit == "request/gpu_s":  # CO-4: a rung of the serving ladder
        return sig(v), "replies/GPU-s"
    if unit == "token/gpu_s":  # CO-8: 4 digits, every whole digit, so served over proved as
        # printed gives the printed multiple (amended 2026-11-16)
        return (f"{v:,.0f}" if abs(v) >= 1000 else sig(v, 4)), "tokens/s per GPU"
    raise KeyError(f"no words for the unit {unit!r}")


def release_tail(rel):
    """A release in words, "v1.0, runs to 2026-11-13": the board's date is its newest run date,
    not a date the release was made on, so it says what it is."""
    return rel["id"] + (f", runs to {rel['date']}" if rel["date"] else "")


def shown(v, unit):
    n, u = number(v, unit)
    return f"{n}{u}" if unit == "ratio" else f"{n}\u00a0{u}"


def params(n):
    """A parameter count in billions, or millions below one billion ("400B", "8.03B", "124M")."""
    text = sig(n / 1e9, 3) if n >= 1e9 else sig(n / 1e6, 3)
    text = text.rstrip("0").rstrip(".") if "." in text else text  # "17.0" reads "17"
    return f"{text}B" if n >= 1e9 else f"{text}M"


def architecture(total, active, sized=True):
    """ "Mixture of experts, 400B total, 17B active" or "Dense, 8.03B": a mixture of experts reads
    fewer parameters per token than it holds (the glossary's term, spelled out). Beside a size that
    says the total (a model's tab: `sized` False), the rest only: "Mixture of experts, 17B active"
    or "Dense"."""
    if active and active < total:
        return (f"Mixture of experts, {params(total)} total, {params(active)} active" if sized
                else f"Mixture of experts, {params(active)} active")  # fmt: skip
    return f"Dense, {params(total)}" if sized else "Dense"


def labels(f, n=None, note=None):
    """A figure's labels in words, for its title: scope, grade, evidence, sample size, record.
    `n` stands where the figure stores no sample size (the row's counted sessions); `note` opens
    the title (CO-5's "whole sessions of N replies")."""
    # CO-5's note says the session once, inside the scope: "scope: whole sessions of N replies,
    # from commit to the last proof"
    if note and f["scope"] == "whole_wall":
        parts = [f"scope: {note}, {WHOLE_WALL_SPAN}"]
    else:
        parts = [note] if note else []
        parts.append(f"scope: {SCOPE_WORD[f['scope']]}")
    parts += [f"grade: {GRADE_WORD[f['grade']]}", f"evidence: {TIER_WORD[f['tier']]}"]
    count = f["n"] if f["n"] is not None else n
    if count is not None:
        parts.append(f"n = {count}")
    if spread := range_words(f):  # AGENTS.md rule 5: a mean carries its range
        parts.append(f"range: {spread}")
    parts.append(f"record: {f['source']}")
    return "; ".join(parts)


def range_words(f):
    """A mean's range over its sessions, in the figure's unit ("17.66 to 18.07 s/reply"), where
    the board stores one over more than one value; None otherwise."""
    st = f.get("stats") or {}
    if (st.get("n") or 0) < 2 or st.get("min") is None or st.get("max") is None:
        return None
    lo, unit = number(st["min"], f["unit"])
    hi, _ = number(st["max"], f["unit"])
    return f"{lo} to {hi}\u00a0{unit}"


def sub_words(f, n=None):
    """The one line under a figure: its scope in a word and its sample size. The dot keeps to the
    scope word (no break before it), so a wrapped line never starts with it."""
    count = f["n"] if f["n"] is not None else n
    parts = [SCOPE_SHORT[f["scope"]], f"n\u00a0=\u00a0{count}" if count is not None else ""]
    return SEP.join(p for p in parts if p)


# the dot between a scope and its sample size
SEP = "\u00a0· "


# ------------------------------------------------------------------ systems not run (SI-4b)
# the checks page's last section: the one rule that gives a system not run its reason, each
# reason with its words, then the systems it holds, each with the fact that sets it and its link
NOT_RUN_LEAD = (
    "A system with no row is listed after the ladder with one reason: the first of these that "
    "holds in its sources, in this order. Each system's line is the fact that sets its reason, "
    "linked to where we read it."
)
NOT_RUN_RULE = {
    "another kind of check": "It makes no proof. Its check is an attestation, a re-execution, a "
    "dispute game or a fingerprint.",
    "a different statement": "It proves a statement other than Level 1's: that a reply is the "
    "committed model's own greedy reply to a prompt the verifier is given.",
    "no public verifier": "No public code to pin, or no public program that checks a stored proof "
    "apart from the prover against a commitment the verifier is given. A prover and verifier "
    "that run only together, and a verifier that reads the commitment from the proof file, are "
    "both this case.",
    "licence": "No licence file, or a licence that grants no use. A licence that grants internal "
    "use for testing and evaluating is read as covering runs we make ourselves; it grants no "
    "right to hand the software to anyone else.",
    "no configuration at the request": "No configuration its sources name proves a reply to the "
    "Level 1 request on a Level 1 model.",
    "not yet run": "Nothing above holds, and no session has run yet.",
}
