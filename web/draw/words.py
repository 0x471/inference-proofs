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
# precise rule: what passes it (SPEC section 8; RFC-0018 SI-3, amended 2026-11-16). {slots} and
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
    "check is undecided (not resolved).",
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
         "and 4-bit copies (Q8_0, Q4_K_M). A system's page lists the damaged ones. With none, the model has no "
         "bar and the check is undecided (not resolved) on every row."),
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
STATE_WORD = {"held": "held", "failed": "failed", "undecided": "undecided"}
# under a system page's Checks head (depth 3): what a held check is
CHECKS_LEAD = (
    "Each check runs the publisher's own prover honestly and tries a change it should refuse. A "
    "held check is a refused change, not a test of soundness."
)
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
KEPT_SETS = "it sets no state"
KEPT_CHANGE = {"reply_token": "one reply token changed, at every reply position in turn",
               "other_session_commitment": "checked against another session's commitment of "
               "the same weights",
               "commitment_id": "checked against a commitment ID no session recorded"}  # fmt: skip
# what a trial whose every changed call was refused shows, by its change
KEPT_MEANS = {"other_session_commitment": "So C3 is refused for any second commitment of the "
              "same weights: its refusal does not show that the weights differ."}  # fmt: skip
KEPT_TIME = "the trial script's wall clock"
# the Level 1 statement on a system page (RFC-0018 SI-4a): the label, and the line by whether
# the publisher's documents state it at the pin
LEVEL_STATEMENT_HEAD = "Level 1 statement"  # SI-4a; the page's Statement section is SI-3's
STATEMENT_WORD = {
    "stated": "the publisher states that an accept means the reply is the committed model's own "
    "greedy reply to the prompt",
    "read": "stating that an accept means the reply is the committed model's own greedy reply to "
    "the prompt, from several of the publisher's sentences, none of which says it alone",
    "not": "the publisher's documents read at the pinned commit do not state that an accept means "
    "the reply is the committed model's own greedy reply to the prompt, so the system has no "
    "position",
}
READ_AS = "read as"  # before STATEMENT_WORD["read"], linked to the checks page's #reading

# ------------------------------------------------------------------ the five petals (RFC-0018 §The glyph)
PETAL_NAME = {"unforgeable": "Unforgeable", "weights_hidden": "Weights hidden",
              "faithful_model": "Close to the original", "machine_checked": "Machine-checked",
              "no_trusted_party": "No third party trusted"}  # fmt: skip
# each petal's field term, under its name on a system page (depths 2 and 3; RFC-0018 §The glyph,
# amended 2026-11-15): the plain name for the policy reader, the term for the expert
PETAL_TERM = {"unforgeable": "soundness error, as stated",
              "weights_hidden": "zero knowledge, as stated",
              "faithful_model": "matched leading tokens",
              "machine_checked": "soundness, machine-checked",
              "no_trusted_party": "trusted setup, as stated"}  # fmt: skip
# the end of a field term that a petal resting on our reading drops (GL-10): it is not as stated
TERM_STATED = ", as stated"
# a reading's notes, in a petal's disclosure (GL-10, amended 2026-11-15): our words, not a quote
READING_HEAD = "Our reading"
# a petal's stored step in words (None: hollow, undecided), §The glyph, step table and GL-8
STEP_WORD = {"green": "green · in full", "amber_upper": "amber · in part",
             "amber_lower": "amber · in lesser part", "red": "red · no",
             None: "undecided"}  # fmt: skip
# a red the publisher's silence set is "not stated", never "no" (amended 2026-11-15)
SILENT_STEP = "red · not stated"


def petal_step(p):
    """A petal's step in words (STEP_WORD), "red · not stated" for a red whose cause is silence."""
    if p["step"] == "red" and p["cause"] == "not_stated":
        return SILENT_STEP
    return STEP_WORD[p["step"]]


# what a petal rests on, in one word beside its step (amended 2026-11-15): our test, the
# publisher's words, or our reading of them (GL-10)
SAID_WORD = {"test": "tested", "statement": "stated", "reading": "read as"}


def said_word(p):
    """The word for what a petal rests on, from its basis and its reading flag."""
    if p["basis"] == "statement" and p["reading"]:
        return SAID_WORD["reading"]
    return SAID_WORD[p["basis"]]


# why a petal is red or hollow (GL-1, GL-3); the checks page defines each at #cause-<id>
CAUSE_WORD = {"not_stated": "not stated", "stated": "stated, short of amber",
              "check_failed": "a check or proof build failed", "not_read": "not read yet",
              "not_decided": "our Fidelity check undecided or not recorded",
              "proof_build_not_run": "no matching proof build"}  # fmt: skip
# each cause in a line, on the checks page (#cause-<id>), opened by how it is drawn: the checks page
# draws that opening as the chip a system page prints for the petal (PETAL_CAUSE_DRAW), the words
# kept for a screen reader
PETAL_CAUSE_RULE = {
    "not_stated": "Red (open outline): the publisher's documents read at the pinned commit are "
    "silent on the property. Silence is red, never undecided.",
    "stated": "Red (filled): the publisher states that the property does not hold, or what it "
    "states does not reach amber.",
    "check_failed": "Red (filled): a check failed, or the matching build of the publisher's "
    "machine-checked proof failed or reported axioms other than the declared ones.",
    "not_read": "Hollow: our record of the publisher's documents is missing, in another form or "
    "read at a commit other than the one the row runs, or the row has no recorded commit. Not "
    "read is not silent: it is undecided, never red.",
    "not_decided": "Hollow, Close to the original only: the Fidelity check is undecided, or the row has "
    "no fidelity record or no scores.",
    "proof_build_not_run": "Hollow, Machine-checked only: the publisher states a machine-checked "
    "proof, and no build of the named theorem is recorded at the pinned commit with the "
    "publisher's toolchain. None can match where the publisher names no toolchain.",
}
# how a cause's opening words are drawn: (state, form) of the chip, its word the step's (STEP_WORD)
PETAL_CAUSE_DRAW = {"Red (open outline)": ("red", "open"), "Red (filled)": ("red", ""),
                    "Hollow": ("hollow", "")}  # fmt: skip
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
    "petal says \u201cread as\u201d, the publisher's quotes are printed with it, and it is drawn "
    "amber in part at most, for every system alike. The name of a construction is never read as a "
    "claim."
)
# Machine-checked's scope card: what is machine-checked, for which program (printed, sets no state)
SCOPE_ROW_WORD = {"soundness": "Soundness", "zero_knowledge": "Zero knowledge",
                  "completeness": "Completeness"}  # fmt: skip
SCOPE_COL_WORD = {"protocol": "Protocol", "verifier_run": "Verifier we run",
                  "prover_run": "Prover we run"}  # fmt: skip
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
SCOPE_CARD_HEAD = "Scope card, as the publisher states it; it sets no state"
SCOPE_LINES = {"stated": "stated by the publisher", "not_stated": "not stated by the publisher",
               "tested": "tested by us on honest runs"}  # fmt: skip
STATED_SECURITY = "Stated security"
NOTION_HEAD = "Its notion, as the publisher names it"
# Weights hidden: what kind of value a proof leaves visible (only fitted_to_weights sets a step)
VISIBLE_TAG_WORD = {"statement_io": "the statement's input or output", "shape": "shape",
                    "side_channel": "side channel",
                    "fitted_to_weights": "depends on the weights"}  # fmt: skip
# the head of the visible values not tagged fitted, after those that are: "8 others" (an untagged
# item's quote does not say it is fitted; that does not show it is not, AGENTS.md rule 9)
VISIBLE_OTHERS = "others"
# each petal's question, RFC-0018's petal table ("rung" said "model"): its first line on the checks
# page, and its search line
PETAL_QUESTION = {
    "unforgeable": "The bound the publisher states on a false reply being accepted: whether it is "
    "proved, and whether it covers what the row runs.",
    "weights_hidden": "What the publisher states and proves about a proof showing nothing of the "
    "weights' values.",
    "faithful_model": "How close the proved replies stay to the model publisher's own release, "
    "against the model's controls.",
    "machine_checked": "How far a machine-checked proof of soundness reaches toward the verifier "
    "the row runs.",
    "no_trusted_party": "What soundness rests on besides cryptographic assumptions.",
}
# what each step means for each petal, RFC-0018's tables in short: (green, amber in part, amber
# in lesser part, red). The first line that matches decides (§Reading the tables); 128, 100 and 80
# are RFC-0018's cut points, 0.05 the level's fidelity.alpha
PETAL_RULE = {
    "unforgeable": (
        "A proved bound that covers the run, every exponent 128 or more.",
        "The same, with every exponent 100 or more and one under 128.",
        "Any other stated bound that is not red: conjectured or its basis not said, not covering "
        "the run, or with an exponent under 100. The reason opens with the stated bound and the "
        "verifier it is stated for, then names every condition that fails, the program first.",
        "No bound with an exponent is stated, the bound holds only against a weaker prover, or an "
        "exponent is under 80 (under 100 for a bound not proved). A failed Model, Prompt or Reply "
        "check also sets it.",
    ),
    "weights_hidden": (
        "The publisher states a zero-knowledge theorem proved for the configuration the row runs, "
        "batch size included, and states that its programs implement it. It publishes a list of "
        "what stays visible, with nothing on it whose quote says it depends on or is fitted to "
        "the weights.",
        "The publisher states a proved zero-knowledge theorem, and a condition of green is "
        "missing.",
        "The publisher states that the weights stay hidden and proves no zero-knowledge theorem.",
        "The Verify without weights check failed, the verifier is given the weights, or the "
        "publisher states that they are not hidden or states nothing.",
    ),
    # FM-5, FM-6, FM-7 in the RFC's order: each line excludes the one above it ("short of
    # green", "Otherwise"); FM-1 and FM-2 (failed, undecided) are the red line and the summary's
    "faithful_model": (
        "Shown above the midpoint of the original's second run and Q8_0, in a fidelity run "
        "recorded as one request at a time.",
        "Shown above the midpoint of Q8_0 and Q4_K_M, short of green.",
        "Otherwise, with the Fidelity check held. A row with the check held is also here, whatever "
        "the midpoints show, when no claim card is found or the card's policy accepts tokens other "
        "than the proved model's own top token. So is one with no stored test against the "
        "midpoints, or with a midpoint whose control is missing, failed or scored on another "
        "number of replies.",
        "The Fidelity check failed.",
    ),
    "machine_checked": (
        "A machine-checked soundness theorem covers the verifier the row runs, from the bytes it "
        "reads to its verdict. Its trusted base is listed, and no named code that reads inputs "
        "sits outside the proof.",
        "The theorem covers the whole protocol and the relation that encodes the model but not the "
        "verifier the row runs, or it covers that verifier and a condition of green is missing.",
        "The theorem covers a component, the constraints against a specification or a "
        "sub-protocol, or the whole protocol without the relation that encodes the model, or the "
        "reverse.",
        "The publisher states that nothing is machine-checked or states nothing, or the matching "
        "build of the theorem failed or reported axioms other than the declared ones. A failed "
        "Model, Prompt or Reply check also sets it where the stated step is green.",
    ),
    # NT-4 comes before NT-5 and NT-6: green and amber in part carry NT-6's "publicly checkable or
    # not said"; "nothing else" answers the question printed above it (PETAL_QUESTION)
    "no_trusted_party": (
        "Soundness rests on nothing else: the publisher states that no setup produced a secret. "
        "Public files fixed before the hash, or derived by a fixed rule from public inputs, do not "
        "count against it. Anyone can check a proof file, or the publisher does not say.",
        "A setup produced a secret in an open ceremony with a public transcript, whose secret stays "
        "unknown if one participant was honest; or green's facts rest on our reading of a stated "
        "theorem or sentence, not on words that say them. Anyone can check a proof file, or the "
        "publisher does not say.",
        "Soundness needs one honest party among a fixed set or a challenger in a challenge "
        "window, or the check is interactive or for a designated verifier, not a proof file "
        "anyone can check.",
        "Soundness rests on a setup run by one party, a hardware key or another trusted key, or "
        "what it rests on is not stated.",
    ),
}
# a petal's terms, defined under its four steps, as (label, words)
PETAL_MORE = {
    "unforgeable": (
        ("covers the run", "The bound holds for the row's parameters and against any prover: one "
         "that controls its own machine, under no hardware or third-party condition. It covers one "
         "reply: stated per reply, or per proof with one proof a request. It covers the row's "
         "batch: a batch of 1, or a bound for each member checked alone. A batch size not "
         "recorded is not covered. The publisher's or the harness's records show its "
         "conditions hold for the row's files. The verifier the row runs is proved or stated to "
         "implement what the bound is about."),
        ("exponent", "An error term 2^-t or q/2^t has exponent t. Exponents are read as the "
         "publisher states them, and no bits figure is computed."),
    ),
    "faithful_model": (
        ("shown above", "The Fidelity check's sign-flip test gives p\u00a0<\u00a00.05 for the "
         "row's scores against the midpoint of the two controls' mean scores."),
        ("measure", "Graded on matched leading tokens, the Fidelity check's score. The Fidelity "
         "figure the ladder prints is another measure, top-token agreement, and sets no step."),
    ),
    "machine_checked": (
        ("build", "Each step above red needs a matching build of the named theorem: one recorded "
         "at the pinned commit with the publisher's toolchain. Level 1 reads that record and makes "
         "none."),
        ("above amber in lesser part", "Needs a theorem whose conclusion is about a reference "
         "definition of the model, and a build that reports only its tool's standard axioms (for "
         "Lean, propext, Classical.choice and Quot.sound), so no sorry. The petal's reason prints "
         "the most a build could give, and that no outside reader of the proof has reviewed the "
         "statement."),
        ("scope card", "Printed at the head of a system's glyph, it sets no state: the petal grades "
         "soundness only. Soundness is the verifier's and zero knowledge the prover's, so the "
         "cells that ask them of the other party do not apply."),
    ),
    # Q12: printed under the four steps, as the question is printed over them
    "no_trusted_party": (
        ("", "This petal does not grade which model a commitment names."),
    ),
}  # fmt: skip
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
FIGURE_NAME = {"multiple": "Cost vs serving", "cost": "Cost per reply",
               "check-time": "Verify time per reply", "proof-size": "Proof size per reply",
               "fidelity-figure": "Fidelity", "kl": "KL to the original weights"}  # fmt: skip
# a figure's head where its unit stands beside it: the unit says "per reply", so the head does
# not; and the surface names fidelity, not the metric (KL and the matched tokens' bar are under
# Fidelity on a system's page)
FIGURE_HEAD = {"multiple": "Cost vs serving", "cost": "Cost", "check-time": "Verify time",
               "proof-size": "Proof size", "fidelity": "Fidelity", "serving": "Serving"}  # fmt: skip
# where a head links on the checks page, where its anchor is not its key: the Fidelity figure has
# a rule of its own there, apart from the check it does not set (SI-9)
FIGURE_ANCHOR = {"fidelity": "fidelity-figure"}
FIDELITY_TITLE = "leading tokens matching the original, mean"  # in a fidelity word's title
# Fidelity as a figure (RFC-0018 SI-9, amended 2026-11-14): FI-10's mean as a percentage of the
# reply's positions, beside the model's Q8_0 and Q4_K_M copies; it sets no state
FIDELITY_AGAINST = ("q8_0", "q4_k_m")  # the controls printed beside a row's Fidelity
FIDELITY_FIG_TITLE = ("Fidelity: the share of reply positions where the system's top token is "
                      "the original's reply token, fed the prompt and then that reply token by "
                      "token")  # fmt: skip
FIDELITY_CHECK_TITLE = "Fidelity check (leading tokens matching the original): {state}"


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
         "fewest H200 GPUs that hold it, at full load. Full load is the lowest concurrency, "
         "doubling from 1 to {top}, whose rate reaches {full} of the highest. If that is {top}, the "
         "model has no b (not saturated)."),
        ("whole sessions", "A row has m when each of its {slots} sessions has at least 3 groups "
         "after the first, each group's time per reply within 5\u202f% of their median. Otherwise "
         "it has no multiple and prints its session GPU-seconds per reply over b, labelled "
         "\u201cwhole sessions of N replies\u201d."),
        ("parts", "Where a system generates its replies in a phase of its own, two parts print "
         "beside the figure, each over b: generation, and the rest (proving under m, commit and "
         "proving under whole sessions). The order reads the figure, never a part."),
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
         "declines. The model's Q8_0 and Q4_K_M percentages are printed under it."),
        ("", "Computed by the system's own code on the reference reply, not by the proved "
         "computation. It sets no state."),
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
    "cost": "GPU time per proved reply, in USD at the release's price for one H200 GPU-hour.",
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
     "there, for at least one verifier it ships. Otherwise it is listed as passed, unranked, with "
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
    ("summary", ""): ("a held check raises none", "/method#order-and-the-glyph"),
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
         "held on its prover answering \u201cfailed\u201d. Under SE-3a, {se3a}. Under SE-3b, "
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
         "changed model, prompt or reply in our adapter, the check reads undecided (not "
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
         "state we read rather than copied says so and is drawn amber at most. Close to the "
         "original moves on a fidelity run."),
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
    ("2026-11-15", "SASH's No third party trusted is read by the same test as FlashProve's: from "
     "red, not stated, to amber in part, read as. Both rest on our reading of the publisher's "
     "sentences, printed with the petal."),
    ("2026-11-15", "The mandate said two SASH slots went to later sessions. One did; slot 2's "
     "replacement ran on a host whose self-test failed and no longer counts."),
    ("2026-11-15", "A SASH session that failed the machine self-test no longer counts "
     "(RFC-0014); SASH's row reads not passed yet until a replacement session runs."),
    ("2026-11-15", "A state that rests on our reading of a publisher's documents, not on a "
     "sentence that says it, is marked \u201cread as\u201d and drawn amber at most, for every system. "
     "FlashProve's No third party trusted moves from green to amber."),
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
    "system limit": "the system cannot do what the test needs, in its publisher's words quoted on "
    "the system's page, so the row cannot pass",
    "not run": "this check has not been run yet",
    "not resolved": "the test ran and decided nothing",
    # RFC-0018's own words, a comma for its semicolon
    "not reproduced": "a verifier accepted a changed input in our adapter, not yet reproduced "
    "with the system's own command",
}
# the line that opens the undecided causes (an undecided check is never worded as a failure; the
# standing words are chrome.not_passed's)
CHECK_CAUSE_LEAD = (
    "Undecided is not failed: a row short of passed only by undecided checks reads not passed yet."
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
    "prove.session": "the whole session, start-up included",
    "whole_wall": f"the whole session, {WHOLE_WALL_SPAN}",
    "verify": "verifying",
    "verify.single_thread": "verifying on one CPU thread",
    "primitive": "one primitive",
    "serving": "serving at full load",  # the serving baseline's, in its title (CO-4)
}
GRADE_WORD = {
    "measured": "recorded by our harness",
    "derived": "calculated from recorded numbers",
    "projected": "projected, not measured",
    "external": "as the system publishes it",
    "asserted": "set in the reference file",
}
TIER_WORD = {
    "reported": "one runner, not reproduced",
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
# before a part's name where it stands beside its whole in a sentence or a table's head (a card's
# alt text, the sessions table); under its whole, a part's name stands alone
OF_WHICH = "of which"
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
FID_WHO = "Whose replies"
FID_KIND = "Kind"
# a check's record as its link reads, by the file's name (the path stands in the link's title)
RECORD_WORD = {"run.json": "run record", "controls.json": "controls", "verify-trace": "verify traces",
               "reverify.json": "re-verify record", "fidelity.json": "fidelity record"}  # fmt: skip
P_ABOVE = "above the bar: {p}"  # {p} reads "p = 0.0058" or the floor's bound (`p_said`)
P_FLOOR = ", the test's floor"  # after a p at the lowest value its test can give (FI-4)
# the reference's precision in words, where a line names the original (FI-1)
DTYPE_BITS = {"bf16": "16-bit", "f16": "16-bit", "f32": "32-bit"}
# the Fidelity section's lead (RFC-0018 SI-9, amended 2026-11-16): first in plain words what is
# compared with what, what 100 % means and what the two yardstick copies are; then why the figure
# is top-token agreement (SPEC 5.4); then which measure sets a state, and that neither compares
# logits (the KL columns do). {name} the system, {proved} the copy it proves (its workload record),
# {bits} the original's precision, {n} the prompts, {tokens} the reply's positions
FID_PLAIN = (
    "Fidelity asks whether the model {name} proves answers like the original, the {bits} model "
    "its publisher released. Proving usually runs a copy whose numbers are stored in fewer bits "
    "(quantization), and {name} proves {proved}."
)
FID_PLAIN_TF = (
    " Each row below is fed the same {n:,} prompts, each followed by the original's reply. Its "
    "Fidelity figure is the share of the reply's positions where its top token is the "
    "original's next token: 100\u00a0% means the original's choice at every position."
)
FID_PLAIN_COPIES = (
    " The 8-bit copy (Q8_0) and the 4-bit copy (Q4_K_M) are the original with its weights "
    "rounded to 8 bits, and mostly to 4 bits, by llama.cpp; we run them without a proof, as "
    "yardsticks."
)
FID_WHY = (
    "Why top-token agreement: a greedy reply is the top token at each position, so this counts "
    "how often the proved model makes the original's choice, at every one of the {tokens:,} "
    "positions, not only up to the first difference."
)
FID_LEAD_PREFIX = (
    "Matched leading tokens set the Fidelity check and the Fidelity petal: the tokens at the "
    "start of each reply that equal the {bits} original's, counted up to the first difference."
)
FID_LEAD_CHECK = (
    " The Fidelity check passes when the replies the system proved match more of them than the "
    "bar, a damaged copy, by a paired test at p\u00a0<\u00a00.05."
)
FID_LEAD_TF = " The Fidelity figure sets no state."
FID_LEAD_LOGITS = " Neither compares logits: the KL columns do."
# what a column is called on a phone, where each card repeats it (the heads in full above)
FID_LABEL = {"Fidelity figure: top-token agreement, mean": "Fidelity figure",
             "Fidelity check: matched leading tokens, mean": "Matched leading tokens, mean"}  # fmt: skip
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
LIM_GREEN = (" The Fidelity petal needs a fidelity run of one request at a time for Met, so it "
             "cannot be Met until the original is run that way on this model.")  # fmt: skip
LIM_PROMPTS = ("Prompts: {tokens}-token windows of {texts} texts from {hosts} ({licences}), with "
               "no chat template.")  # fmt: skip
TF_AGREE = "Fidelity figure: top-token agreement, mean"
TF_KL = "KL to the original, on its reply"
# the summary of FI-11's tests: they are on top-token agreement and set nothing (the matched
# leading tokens set the check and the petal)
TF_TESTS_ON = "on top-token agreement; they set no state"
# the two teacher-forced columns by name: the lead and FI-13's label say which columns they are about
TF_BOTH = f"Fidelity figure and {TF_KL}"
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
