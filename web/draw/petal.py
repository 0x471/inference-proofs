"""A criterion on a system page (RFC-0018 SI-3, GL-11, amended 2026-11-17 and 2026-11-22, owner
decisions).

Each criterion (a petal of the glyph, which the system page no longer draws) answers four
questions in the owner's order: what full marks (Met) need, what the system has, what it misses
and who acts, and where to check. Its closed row prints its name, its plain question, its grade
as a word in its ink, one sentence (the first item missing) and its track: Partly met, Mostly met
and Met as three cells, those it holds solid in its grade's ink, each of the others holding one
open square per item missing for it. Opened, the track unfolds in place: each square becomes its
numbered item in words under its cell, with who acts; what it protects, what Met needs and what
it has stand under the question; Fidelity draws its mean among the runs its thresholds come
from; then the evidence and "Why this grade" one click further each: what the grade comes from,
why, Met needs and Has in full, each item with what it is today, our records, the limits no rule
counts and the field's terms. Every line is worded here and in words.py from the board's keys
(`to_met`, `read_facts`, `why`, the petal's facts) and the stored records; nothing is typed per
system, and nothing here sets a state. The page does not print a petal's `reason` or scale label:
both stay on the board.
"""

import re

from . import state as S
from .chrome import CHECKS_PAGE, link, rung_of
from .ladder import bits_words, name_of, proved_words
from .plots import ZERO, hbar
from .words import (
    CAME_FROM,
    CAUSE_WORD,
    CHART_BAR,
    CHART_CAPTION,
    CHART_NEEDS,
    CHART_NOT_SHOWN,
    CONTROL_NAME,
    EVIDENCE,
    EVIDENCE_TAG,
    FIELD_TERMS_TITLE,
    FORMAT_WORD,
    FROM_WORD,
    GAP,
    GAP_ANY,
    GRADE_SCALE,
    GRADE_SCALE_HEAD,
    GRADE_SCALE_SEP,
    HAS_HEAD,
    IN_FULL,
    KEPT_TIME,
    MISSING_STEP,
    MISSING_TAG,
    NEEDS_HEAD,
    NEEDS_SHORT,
    NEEDS_TINY,
    PETAL_ASK,
    PETAL_BLOCK,
    PETAL_NAME,
    PETAL_PROTECTS,
    PETAL_TERM,
    PROTECTS_HEAD,
    REACH_LABEL,
    READING_MARK,
    READING_TOPIC,
    RECORD_LINK,
    RECORDS,
    SCOPE_LINK,
    STEP_WORD,
    TRACK_SAID,
    VISIBLE_KINDS,
    VISIBLE_OTHERS,
    VISIBLE_TAG_WORD,
    WHO,
    WHO_HEAD,
    WHO_TAG,
    e,
    petal_step,
    quoted,
    sig,
    step_key,
)

# ------------------------------------------------------------------ shared with pages.py


def chip(state, word, form=""):
    """A state as a chip: ground ink on its state's ink, an outline when undecided or hollow; amber
    in lesser part notched (cut), a silent red an outline in the red ink (open)."""
    tok = f"{state} {form}".strip()
    return f'<span class="schip {tok}">{e(word)}</span>'


CHECK_INK = {"held": "green", "failed": "red", "undecided": "hollow"}


def state_word(state, word):
    """A check's state on a system page as the petals print their grades: a word in its ink, set
    in display type (passed green, failed red, not decided muted)."""
    return f'<span class="pvd sw {CHECK_INK.get(state, "hollow")}">{e(word)}</span>'


QUANT = re.compile(r"q\d")  # a quantized copy's id ("q8_0", "q4_k_m")


def control_name(cid):
    """A control's name as a row prints it: its words (CONTROL_NAME: a quantized copy by its bits,
    its id in parentheses), else a quantized copy by its id in capitals. Returns (name, title: the
    id, and for a quantized copy the llama.cpp commit that made it, FI-2)."""
    name = CONTROL_NAME.get(cid) or (cid.upper() if QUANT.match(cid) else cid)
    if not QUANT.match(cid):
        return name, (cid if cid in CONTROL_NAME else "")
    engine = S.V["constants"].get("fidelity_engine") or {}
    made = (f", made by {engine['tool']} at {str(engine['commit'])[:7]}"
            if engine.get("tool") and engine.get("commit") else "")  # fmt: skip
    return name, f"{cid}{made}"


# a publisher's Markdown and source-comment marks, which a quote prints without: **strong**, a
# [link](target) (its words kept), a comment marker opening one of the lines it spans, and " -- "
MARKS = ((re.compile(r"\*\*(.+?)\*\*"), r"\1"), (re.compile(r"\[([^\]]+)\]\([^)\s]+\)"), r"\1"),
         (re.compile(r"(^|\s)//[!/]?\s+"), r"\1"), (re.compile(r" -- "), " \u2013 "))  # fmt: skip


def unmarked(text):
    """A quote's words as the publisher wrote them, the marks of their file's syntax left out
    (the words themselves unchanged, hard rule 9)."""
    for mark, to in MARKS:
        text = mark.sub(to, text)
    return text


def in_quotes(text):
    """A publisher's words between quotation marks; a quotation inside them takes single marks,
    so a quote that opens with one does not print two opening marks in a row."""
    inner = quoted(unmarked(text)).replace("\u201c", "\u2018").replace("\u201d", "\u2019")
    return f"\u201c{inner}\u201d"


def quote_links(quotes):
    return "".join(f'<a class="qt" href="{e(q["url"])}">{in_quotes(q["text"])}</a>'
                   for q in quotes)  # fmt: skip


FITTED = "fitted_to_weights"  # the one kind of visible value that sets Weights hidden's step


def forms_html(forms):
    """Weights hidden: the forms of the proved zero knowledge, each the publisher's words linked
    to its quote (amended 2026-11-15). They set no step."""
    if not forms:
        return ""
    items = "".join(f'<li><a href="{e(f["quotes"][0]["url"])}">{quoted(f["item"])}</a></li>'
                    for f in forms)  # fmt: skip
    return f'<p class="pvh">Zero knowledge, as stated</p><ul class="pvis">{items}</ul>'


def visible_html(visible, at_least=False):
    """Weights hidden: what the publisher lists as visible, each item linked to its quote, in two
    groups: those whose words say they depend on the weights (the only kind that sets the step,
    WH-5, WH-6), then the others, each with its kind. The second group's head says "others", not
    "independent of the weights": an item is untagged when its quote does not say it depends on
    them, which does not show that it does not (AGENTS.md rule 9)."""
    if not visible:
        return ""

    def items(vs, tagged):
        return "".join(f'<li><a href="{e(v["quotes"][0]["url"])}">{e(v["item"])}</a>'
                       + (f' <span class="vt">{e(VISIBLE_TAG_WORD[v["tag"]])}</span>' if tagged
                          else "") + "</li>" for v in vs)  # fmt: skip

    fitted = [v for v in visible if v["tag"] == FITTED]
    other = [v for v in visible if v["tag"] != FITTED]
    groups = ((f"{len(fitted):,} that {VISIBLE_TAG_WORD[FITTED].replace('depends', 'depend')}",
               fitted, False),
              (f"{len(other):,} {VISIBLE_OTHERS}, each with its kind ({VISIBLE_KINDS})" if fitted
               else "", other, True))  # fmt: skip
    head = "Visible, as listed" + (" (at least these)" if at_least else "")
    return f'<p class="pvh">{e(head)}</p>' + "".join(
        (f'<p class="pvg">{e(head)}</p>' if head else "")
        + f'<ul class="pvis">{items(vs, tagged)}</ul>'
        for head, vs, tagged in groups
        if vs
    )


# ------------------------------------------------------------------ small words


def cap(s):
    return s[:1].upper() + s[1:]


def count(k, one, many=None):
    """ "1 item", "3 items"."""
    return f"{k:,} {one}" if k == 1 else f"{k:,} {many or one + 's'}"


def number(k):
    """Two to nine in words where a sentence counts things ("two points")."""
    return ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")[k] \
        if 0 <= k < 10 else f"{k:,}"  # fmt: skip


def and_list(words):
    words = list(words)
    if len(words) < 3:
        return " and ".join(words)
    return ", ".join(words[:-1]) + ", and " + words[-1]


def tenth(x):
    """A mean or a threshold as the board stores its display, one decimal place."""
    return f"{x:,.1f}"


def secs(x):
    return f"{x:,.0f}\u00a0s"


def hours(x):
    """A duration in seconds as a reader pictures it: "about 19 hours"."""
    h = x / 3600
    return f"about {h:,.0f} hours" if h >= 2 else f"about {x / 60:,.0f} minutes"


def q_html(q, words=None):
    """One quote of the publisher's, inline, its marks of syntax left out, linked at the pin."""
    text = e(words) if words is not None else in_quotes(q["text"])
    return f'<a class="iq" href="{e(q["url"])}">{text}</a>'


def p_(html, cls=""):
    return f'<p class="{cls}">{html}</p>' if cls else f"<p>{html}</p>"


def facts_of(p):
    return p.get("facts") or {}


def said_of(p, key):
    return ((facts_of(p).get("said") or {}).get(key)) or {}


def first_quote(p, key):
    found = said_of(p, key).get("quotes") or []
    return found[0] if found else None


def pin7(row):
    return (row.get("commit") or "")[:7]


def tool_word(petals):
    formal = petals["machine_checked"].get("formal") or {}
    return str(formal["tool"]).split(" ")[0] if formal.get("tool") else None


def check_state(row, cid):
    return next((c["state"] for c in row["checks"] if c["id"] == cid), None)


def verifiers(row, petals):
    """The verifier the row runs and the one a statement is about, each with the publisher's own
    description where the properties file gives one ("cp_verify", "the publisher's C++
    verifier")."""
    st = (row.get("statement") or {}).get("verifiers") or {}
    said = (facts_of(petals["unforgeable"]).get("verifiers")) or {}
    return {k: (st.get(k), (said.get(k) or {}).get("described")) for k in ("run", "stated")}


def run_named(row, petals):
    """ "cp_verify, the publisher's C++ verifier, which we run"."""
    run, d = verifiers(row, petals)["run"]
    if not run:
        return "the verifier we run"
    return f"{run}, {d}, which we run" if d else f"{run}, the verifier we run"


def items_of(p):
    return [it for g in p["to_met"] for it in g["items"]]


# ------------------------------------------------------------------ what the step comes from


def came_from(p):
    """ "from our test", "from the publisher's words and our reading"; "" on a Not stated or Not
    decided petal."""
    key = p.get("came_from")
    return f"{FROM_WORD} {CAME_FROM[key]}" if key else ""


def read_sets_grade(p):
    """Whether a reading of ours is among what the grade comes from (GL-5 `sources`, GL-10): the
    row marks it beside the grade."""
    return str(p.get("came_from") or "").endswith("reading")


def came_from_words(p):
    """The opened petal's first line of evidence: what the grade comes from, and on how many
    points our reading where more than one ("From the publisher's words and our reading, on 2
    points"); "" on a Not stated or Not decided petal."""
    key = p.get("came_from")
    if not key:
        return ""
    k = len(used_facts(p))
    pts = EVIDENCE["points"].format(n=k) if read_sets_grade(p) and k > 1 else ""
    return EVIDENCE["from"].format(src=CAME_FROM[key]) + pts


# ------------------------------------------------------------------ Met needs and Has, in a few words


def per_words(f, short=False):
    """What one limit is stated per: "per proof", "per segment, one transformer layer"."""
    unit = f.get("unit")
    named = (f.get("said") or {}).get("unit") or {}
    if unit == "part" and named.get("named"):
        d = named.get("described")
        return f"per {named['named']}" + (f" ({d})" if d and not short else "")
    return {"proof": "per proof", "reply": "per reply", "part": "per part of a proof",
            "round": "per round"}.get(unit, "")  # fmt: skip


def needs_short(p):
    """What full marks need, in one short line."""
    f = facts_of(p)
    green = tenth(f["green"]["display"]) if p["id"] == "faithful_model" and f.get("green") else "?"
    return NEEDS_SHORT[p["id"]].format(green=green)


def has_short(p, row, petals):  # noqa: PLR0911, PLR0912 (one clause per rule path)
    """One or two clauses, in the system's own numbers and names: what it has today."""
    f, pid, step, cause = facts_of(p), p["id"], p["step"], p["cause"]
    k_docs = len(p["sources"])
    if cause == "not_read":
        return "we have not read the publisher's documents at this version yet"
    if cause == "check_failed":
        names = and_list(CHECK_WORD.get(c, c) for c in p["lowered_by"])
        return f"our {names} {'test' if len(p['lowered_by']) == 1 else 'tests'} failed on this run"
    if pid == "unforgeable":
        if cause == "not_stated":
            return (
                f"no limit on the chance of a fake reply in the {count(k_docs, 'document')} we read"
            )
        expr, per = f.get("expression"), per_words(f, short=True)
        run, stated = f.get("run"), f.get("stated_for")
        least = min(f.get("terms") or [0])
        q = " (q: hash queries)" if f.get("q_cross") else ""
        if f.get("basis") == "conjectured":
            said = f"a conjectured limit, a chance of about 2^-{least} {per}"
            return said + (f", for {stated}" if stated else "")
        head = f"a proved limit, {expr} {per}{q}" if f.get("basis") == "proved" else \
            f"a limit, {expr} {per}, not said to be proved"  # fmt: skip
        if cause == "stated":
            return head
        if stated and f.get("program") not in ("proved", "stated"):
            return f"{head}, for {stated}"
        return head + (f", for {run}, which we run" if run else "")
    if pid == "weights_hidden":
        if cause == "not_stated":
            tail = (
                ", but they say the verifier is not given them"
                if f.get("verifier_gets_weights") is False
                else ""
            )
            return f"nothing on whether a proof hides the weights{tail}"
        if f.get("verifier_gets_weights") is True:
            return "the verifier is given the weights"
        if cause == "stated":
            return "the publisher states that a proof does not hide the weights"
        if step == "amber_lower":
            return "a statement that a proof hides the weights, but no theorem"
        if f.get("proof") == "configuration_run":
            return "a theorem that a proof of what we run hides the weights"
        said = "a theorem that the method hides the weights"
        if f.get("zk_unit") == "request":
            said += ", for one request per proof"
        return said
    if pid == "faithful_model":
        if not f:
            return p["reason"]
        c = f["controls"]
        return (f"replies match the original's for their first {tenth(f['display'])} tokens on "
                f"average, against {tenth(c['q8_0']['display'])} for our 8-bit copy and "
                f"{tenth(c['q4_k_m']['display'])} for our 4-bit copy")  # fmt: skip
    if pid == "machine_checked":
        formal = p.get("formal") or {}
        tool = str(formal.get("tool") or "").split(" ")[0]
        run, stated = (v[0] for v in verifiers(row, petals).values())
        if cause == "not_stated":
            return f"no computer-checked theorem named in the {count(k_docs, 'document')} we read"
        if cause == "stated":
            return "the publisher states that nothing is checked by computer"
        if cause == "proof_build_not_run":
            build = formal.get("build") or {}
            if build.get("status") == "stopped":
                return f"a {tool} theorem is named, but our rebuild stopped before a verdict"
            return f"a {tool} theorem is named, but we have not rebuilt it yet"
        reach = formal.get("reach")
        k = len(formal.get("limits") or [])
        lim = f", and the publisher states {k} limits the grade does not count" if k else ""
        if reach == "verifier_run":
            return f"a {tool} theorem we rebuilt, about {run}, the verifier we run{lim}"
        if reach == "protocol_and_statement":
            about = f"about {stated} and the method" if stated else "about the method"
            return f"a {tool} theorem we rebuilt, {about}{lim}"
        return f"a {tool} theorem we rebuilt, about part of the method{lim}"
    if pid == "no_trusted_party":
        if cause == "not_stated":
            return f"nothing in the {count(k_docs, 'document')} we read on what soundness rests on"
        if step == "green":
            return "cryptographic assumptions only and no setup secret, in the publisher's words"
        if f.get("clause") == "reading":
            return ("on our reading, cryptographic assumptions only and no setup secret, but "
                    "the publisher does not say so in one sentence")  # fmt: skip
        if f.get("clause") == "ceremony":
            return "a setup secret made in an open ceremony with a public record"
        return p["reason"]
    return p["reason"]


CHECK_WORD = {"model": "Model", "prompt": "Prompt", "reply": "Reply",
              "no_weight_file": "Verify without weights", "fidelity": "Fidelity",
              "proof_build": "rebuild"}  # fmt: skip


# ------------------------------------------------------------------ the items missing for Met


def item_short(it, p, row):  # noqa: PLR0911 (one phrase per item key)
    """An item in a few words, as an opened row lists it under its grade's cell."""
    need, f = it["need"], facts_of(p)
    run = (
        it.get("run")
        or f.get("run")
        or ((row.get("statement") or {}).get("verifiers") or {}).get("run")
    )
    if need == "text":
        return it["text"]
    if need == "program":
        return f"a limit for {run}"
    if need == "zk_run":
        n = it.get("n")
        return f"the theorem for our {n}-reply batches" if it.get("unit") == "request" \
            and n and n > 1 else "the theorem for what we run"  # fmt: skip
    if need == "rebuild":
        return "our rebuild of that theorem" if it.get("new") else "our rebuild of it"
    if need == "reach_run":
        return f"a theorem reaching {run}, which we run"
    if need == "conditions":
        return f"a record its condition{' holds' if it.get('proved') else 's hold'} for our files"
    if need == "exponent":
        return f"every part of the limit at most 2^-{it['floor']}"
    if need == "above":
        return f"an average shown above {tenth(it['value'])} tokens"
    if need == "one_at_a_time":
        engine = it.get("engine")
        return "our whole run one request at a time" + (f" in {engine}" if engine else "")
    if need == "fitted":
        return f"no visible item that depends on the weights ({it['k']:,} today)"
    return SHORT.get(need, need)


SHORT = {
    "basis": "a mathematical theorem rather than a conjecture",
    "adversary": "a statement that the bound holds against any cheating prover",
    "unit": "a bound covering an entire reply",
    "granularity": "a record of how many replies one proof covers",
    "batch": "a bound covering each reply verified individually",
    "batch_size": "a record of our batch size",
    "parameters": "a statement that the bound applies to the settings we run",
    "reading": "explicit publisher wording for each point currently based on our reading",
    "programs": "a statement that the compiled programs keep the weights secret",
    "visible_list": "a published list of what remains visible",
    "fitted": "nothing on that list depending on the weights",
    "hide_statement": "a statement that a proof keeps the weights secret",
    "zk_theorem": "a zero-knowledge theorem",
    "named_theorem": "a named machine-checked theorem",
    "whole_method": "a formal theorem covering the full protocol and the model's computation",
    "conclusion": "a formal conclusion about the model",
    "axioms": "a rebuild using only the proof assistant's standard axioms",
    "trusted_base": "a complete list of what the theorem relies on",
    "input_code": "no unverified input-reading code outside the theorem",
    "rests_sentence": "an explicit sentence from the publisher stating this",
    "no_setup_secret": "a publisher statement that no setup produced a secret",
}


def reading_topics(facts):
    """ "that the limit holds against any cheating prover and is for the settings we run"."""
    out, last = [], None
    for k in facts:
        subject, said = READING_TOPIC.get(k, (None, k))
        out.append(
            said
            if subject == last
            else f"{'that ' if subject else ''}{subject or ''} {said}".strip()
        )
        last = subject
    return and_list(out)


def item_long(it, p, row, petals, mixed):  # noqa: PLR0912, PLR0915 (one sentence set per key)
    """An item in full, one click down: what is needed, then "Today ...", and in a group
    where both act, who acts."""
    need, f = it["need"], facts_of(p)
    st = row.get("statement") or {}
    run = it.get("run") or f.get("run") or (st.get("verifiers") or {}).get("run")
    stated = f.get("stated_for") or (st.get("verifiers") or {}).get("stated")
    said = ""
    if need == "text":
        said = cap(it["text"]) + "."
    elif need == "program":
        said = f"A bound covering {run}, the verifier we run. " + (
            f"Today the theorem covers {stated} only." if it.get("stated") and f.get("basis") == "proved"
            else f"Today the bound is stated for {stated} only." if it.get("stated")
            else "Today no verifier is named.")  # fmt: skip
    elif need == "basis":
        least = min(it.get("terms") or [0])
        said = (f"A mathematical theorem rather than a conjecture. Today the {least}-bit figure "
                "rests on an unproven assumption." if it.get("basis") == "conjectured" else
                "A mathematical theorem. Today the documents we read do not say whether the bound "
                "is proved.")  # fmt: skip
    elif need == "adversary":
        said = "A statement that the bound holds against any cheating prover. " + (
            "Today it is stated only against a weaker adversary." if it.get("adversary") == "weaker"
            else "Today the documents we read do not specify the adversary model.")  # fmt: skip
    elif need == "unit":
        unit = it.get("unit")
        u = (f.get("said") or {}).get("unit") or {}
        today = (f"Today it covers one {u['named']} ({u.get('described')})." if unit == "part" and u.get("named")
                 else "Today it covers only part of a proof." if unit == "part"
                 else "Today it covers only a single round." if unit == "round"
                 else "Today a single proof covers more than one reply." if unit == "proof"
                 else "Today the documents we read do not specify what unit the bound covers.")  # fmt: skip
        said = f"A bound covering a full reply. {today}"
    elif need == "granularity":
        said = "A record of how many replies one proof covers. Today none is recorded."
    elif need == "batch":
        n = it.get("n")
        if it.get("batch") == "together":
            said = (f"A bound covering each reply verified individually. We generate replies in "
                    f"batches of {n} and verify each reply's proof on its own. The publisher's "
                    f"batch bound covers all {n} proofs only when checked together ({n} times the "
                    "single-proof error across total batch hash queries), with no bound stated "
                    "for proofs verified one at a time.")  # fmt: skip
        else:
            said = (f"A bound covering each reply verified individually. We generate replies in "
                    f"batches of {n}, and the publisher states no bound for individual replies "
                    "inside a batch.")  # fmt: skip
    elif need == "batch_size":
        said = "A record of our batch size. Today none is recorded."
    elif need == "parameters":
        said = "An explicit statement that the bound applies to the settings we run. " + (
            "Today it is stated only for different settings." if it.get("parameters") == "other"
            else "Today the documents we read do not state this explicitly.")  # fmt: skip
    elif need == "conditions":
        head = ("A record showing the theorem's preconditions hold for the files we run." if it.get("proved")
                else "A record showing the bound's preconditions hold for the files we run.")  # fmt: skip
        plain = said_of(p, "conditions_shown").get("plain")
        cond = said_of(p, "conditions_shown").get("quotes") or []
        today = plain or ("Today the documents we read neither name nor verify any preconditions." if not cond
                          else "Today no record shows that those preconditions hold.")  # fmt: skip
        trial = trial_of(row)
        aside = ""
        if trial and stated:
            aside = (f" Outside the grade, in our trial under {PETAL_NAME['machine_checked']}, "
                     f"{stated} accepted {trial['accepted']:,} of "
                     f"{count(trial['honest'], 'honest proof')} on our files.")  # fmt: skip
        said = f"{head} {today}{aside}"
    elif need == "exponent":
        floor, terms = it["floor"], it.get("terms") or []
        if f.get("basis") == "conjectured" or (len(terms) == 1 and not it.get("q")):
            today = f"Today it is roughly 2^-{terms[0]} ({terms[0]} bits)." if terms else ""
        else:
            written = [f"q × 2^-{t}" if i == 0 and it.get("q") else f"2^-{t}"
                       for i, t in enumerate(terms)]  # fmt: skip
            today = f"Today the error terms are {and_list(written)}."
        said = f"Every term in the bound at most 2^-{floor}. {today}"
    elif need == "reading":
        k = len(it["facts"])
        this = "this rests on" if k == 1 else "both rest on" if k == 2 else "all rest on"
        said = (
            f"Explicit publisher wording {reading_topics(it['facts'])}. Today {this} our reading."
        )
    elif need == "zk_run":
        n = it.get("n")
        said = (f"A zero-knowledge theorem covering our {n}-reply batches. Today the theorem covers "
                "only one request per proof."
                if it.get("unit") == "request" and n and n > 1
                else "A zero-knowledge theorem covering the exact setup we run.")  # fmt: skip
    elif need == "programs":
        said = "An explicit publisher statement that the compiled programs keep the weights secret."
        if it.get("programs") == "expected":
            said += " Today the publisher states only an expectation, not a guarantee."
        elif it.get("read"):
            said += " Today, on our reading, no statement covers the programs we run."
    elif need == "visible_list":
        said = ("A published list of everything that stays visible, containing nothing that "
                "depends on the weights.")  # fmt: skip
    elif need == "fitted":
        k = it["k"]
        said = ("Nothing on the published list of visible values that depends on the weights "
                f"according to the publisher's own description. Today {count(k, 'item')} "
                f"{'does' if k == 1 else 'do'}.")  # fmt: skip
    elif need == "hide_statement":
        said = "A publisher statement that a proof keeps the weights secret from the verifier."
    elif need == "zk_theorem":
        said = "A proved zero-knowledge theorem, at least for the protocol."
    elif need == "above":
        fd = f
        t = fd[it["key"]]
        a, b = (fd["controls"][c] for c in t["controls"])
        names = {"upper": ("our 8-bit copy", "our 4-bit copy"),
                 "green": ("a second run of the original", "our 8-bit copy")}[it["key"]]  # fmt: skip
        said = (f"An average shown above {tenth(t['display'])} tokens, halfway between {names[0]} "
                f"({sig(a['mean'])}) and {names[1]} ({sig(b['mean'])}). Today the average is "
                f"{sig(fd['mean'])} tokens, which is not shown above that threshold.")  # fmt: skip
        if it is first_above(p):
            said += (f" Because the publisher chooses the number format of the copy {name_of(row)} "
                     "proves, this item is for the publisher.")  # fmt: skip
    elif need == "one_at_a_time":
        fid = rung_of(row).get("fidelity") or {}
        engine = it.get("engine")
        said = ("Running our full fidelity evaluation on this model one request at a time"
                + (f" in {engine}, as the rule requires" if engine else "") + ". Today "
                + runs_words(fid) + ".")  # fmt: skip
        rerun = (f.get("controls") or {}).get(f.get("rerun") or "")
        tokens = (S.V.get("request") or {}).get("output_tokens")
        if rerun and f.get("rerun_engine") == "vllm" and tokens and rerun["mean"] < tokens:
            said += (f" A second run of the original model in vLLM scores {sig(rerun['mean'])} "
                     f"rather than {tokens}, and the {tenth(f['green']['display'])} threshold is "
                     "computed from that score.")  # fmt: skip
    elif need == "named_theorem":
        said = ("A named theorem, checked by a proof assistant such as Lean with a pinned version, "
                "proving that at least part of the protocol rejects fake replies.")  # fmt: skip
    elif need == "rebuild":
        said = "Our own rebuild of that new theorem." if it.get("new") else \
            "Our own rebuild of it (and of any updated theorem)."  # fmt: skip
    elif need == "whole_method":
        said = ("A theorem covering the full protocol including the model's computation, with a "
                "conclusion about the model and only standard proof-assistant axioms.")  # fmt: skip
    elif need == "conclusion":
        said = "A formal conclusion about the model (a reference definition of its forward pass)."
    elif need == "axioms":
        said = "A rebuild using only the proof assistant's standard axioms."
    elif need == "reach_run":
        formal = p.get("formal") or {}
        said = (f"A formal proof covering {run}, the verifier we run, from raw input bytes to "
                "verdict, listing its trusted base and leaving no input-reading code outside "
                "the proof.")  # fmt: skip
        if formal.get("reach") in ("protocol_and_statement", "protocol", "part") and stated:
            said += f" Today it covers only {stated}"
            said += (", and unverified input-reading code sits outside it." if formal.get("input_code_unverified")
                     is True else ".")  # fmt: skip
    elif need == "trusted_base":
        said = "A complete list of what the theorem relies on. Today none is listed."
    elif need == "input_code":
        said = "No unverified input-reading code outside the proof. Today some remains outside."
    elif need == "rests_sentence":
        said = ("An explicit sentence from the publisher stating that soundness rests solely on "
                "cryptographic assumptions with no setup secret. Today this relies on our reading.")  # fmt: skip
    elif need == "no_setup_secret":
        said = ("A publisher statement that no setup produced a secret. Today a secret was "
                "created during an open ceremony.")  # fmt: skip
    else:
        said = cap(need) + "."
    if mixed:
        said += f" {cap(WHO[it['by']])}."
    return said


def fidelity_figures(p):
    """Fidelity's row in numbers: the row's mean matched leading tokens and the 8-bit and 4-bit
    copies' means at four significant digits, as the Fidelity check prints its mean, and the first
    threshold missing for Met with the step it reaches, at one decimal, as the board stores it
    (None at Met); None where the petal has no fidelity facts."""
    f = facts_of(p)
    if p["id"] != "faithful_model" or not f:
        return None
    c = f["controls"]
    nxt = next(((STEP_WORD[g["to"]], tenth(it["value"])) for g in p["to_met"]
                for it in g["items"] if it["need"] == "above"), None)  # fmt: skip
    return {"own": sig(f["mean"]), "q8": sig(c["q8_0"]["mean"]), "q4": sig(c["q4_k_m"]["mean"]),
            "next": nxt}  # fmt: skip


def first_above(p):
    for g in p["to_met"]:
        for it in g["items"]:
            if it["need"] == "above":
                return it
    return None


def runs_words(fid):
    """How our fidelity run sent its prompts, part by part (FI-9): "the original and its second
    run got every prompt in one call, in vLLM; our copies ran 16 at a time, in llama.cpp"."""
    parts = []
    for r in fid.get("runs") or ():
        who = "the original and its second run" if r.get("part") is None else "our copies"
        if r.get("engine") == "vllm":
            parts.append(f"{who} got every prompt in one call, in vLLM")
        elif r.get("slots") is not None:
            parts.append(f"{who} ran {r['slots']} at a time, in {r.get('engine')}")
    return ", and ".join(parts) if parts else "no slot count is recorded"


# ------------------------------------------------------------------ the row's words (amended 2026-11-17)


def needs_tiny(p, row, petals):
    """What full marks need, in a few words, naming the verifier we run ("cp_verify, which we
    run")."""
    f = facts_of(p)
    green = tenth(f["green"]["display"]) if p["id"] == "faithful_model" and f.get("green") else "?"
    run = verifiers(row, petals)["run"][0]
    return NEEDS_TINY[p["id"]].format(
        green=green, run=f"{run}, which we run" if run else "the verifier we run"
    )


def has_tiny(p, row, petals, charted=False):  # noqa: PLR0911, PLR0912 (one phrase per rule path)
    """What the system has, in a few words: the figure or the fact, the gap left to the row's
    sentence; Fidelity's figure alone where its chart (`charted`) prints the copies'. Every path
    the short words do not cover reads as `has_short`."""
    f, pid, step, cause = facts_of(p), p["id"], p["step"], p["cause"]
    if cause == "not_stated":
        if pid == "weights_hidden" and f.get("verifier_gets_weights") is False:
            return "the verifier gets no weights, as stated"
        return "nothing stated"
    if cause in ("not_read", "check_failed", "stated", "proof_build_not_run"):
        return has_short(p, row, petals)
    if pid == "unforgeable" and f.get("terms"):
        per = per_words(f, short=True)
        if f.get("basis") == "conjectured":
            return f"about 2^-{min(f['terms'])} {per}, conjectured"
        said = "proved" if f.get("basis") == "proved" else "not said to be proved"
        return f"{f['expression']} {per}, {said}"
    if (
        pid == "weights_hidden"
        and step == "amber_upper"
        and f.get("verifier_gets_weights") is not True
    ):
        if f.get("proof") == "configuration_run":
            return "a zero-knowledge theorem for what we run"
        return "a zero-knowledge theorem for the method"
    if pid == "faithful_model" and f:
        if charted:
            return f"{sig(f['mean'])} matched tokens"
        fig = fidelity_figures(p)
        return f"{fig['own']} matched tokens (8-bit copy {fig['q8']}, 4-bit copy {fig['q4']})"
    if pid == "machine_checked":
        formal = p.get("formal") or {}
        tool = str(formal.get("tool") or "").split(" ")[0]
        reach = formal.get("reach")
        if tool and reach == "verifier_run":
            return f"a {tool} theorem of the verifier we run, rebuilt by us"
        if tool and reach == "protocol_and_statement":
            return f"a {tool} theorem of the method, rebuilt by us"
        if tool:
            return f"a {tool} theorem of part of the method, rebuilt by us"
    if pid == "no_trusted_party":
        if step == "green":
            return "cryptography only, in the publisher's words"
        if f.get("clause") == "reading":
            return "cryptography only, no setup secret, on our reading"
        if f.get("clause") == "ceremony":
            return "a setup secret from an open ceremony"
    return has_short(p, row, petals)


def gap_sentence(p, row, petals):  # noqa: PLR0911, PLR0912 (one sentence per item kind)
    """The row's one sentence: the first item missing for Met, in plain words; "Nothing missing."
    at Met. A row below Met whose board lists no item (a board from before `to_met`) has none:
    nothing is said to be missing or not."""
    groups = p["to_met"]
    if not groups:
        return GAP["none"] if p["step"] == "green" else ""
    g, it = groups[0], groups[0]["items"][0]
    if g["kind"] in ("decide", "repair"):
        return GAP[g["kind"]].format(need=item_short(it, p, row))
    need, f = it["need"], facts_of(p)
    st = (row.get("statement") or {}).get("verifiers") or {}
    run = it.get("run") or f.get("run") or st.get("run")
    stated = f.get("stated_for") or st.get("stated")
    if need == "program":
        if not it.get("stated") or not stated:
            return GAP["program_none"].format(run=run)
        key = "program_proved" if f.get("basis") == "proved" else "program_stated"
        return GAP[key].format(stated=stated, run=run)
    if need == "zk_run":
        n = it.get("n")
        if it.get("unit") == "request" and n and n > 1:
            return GAP["zk_batch"].format(n=n)
        return GAP["zk_run"]
    if need == "above":
        return GAP["above"].format(to=STEP_WORD[g["to"]], value=tenth(it["value"]))
    if need == "reach_run":
        if (p.get("formal") or {}).get("tool") and stated:
            return GAP["reach_stated"].format(stated=stated, run=run)
        return GAP["reach_none"].format(run=run)
    if need == "basis":
        return GAP["basis_conjectured" if it.get("basis") == "conjectured" else "basis"]
    if need == "exponent":
        return GAP["exponent"].format(floor=it["floor"])
    if need == "reading":
        return GAP["reading"].format(topics=reading_topics(it["facts"]))
    if need in GAP:
        return GAP[need].format(docs=count(len(p["sources"]), "document"))
    if need == "text":
        return cap(it["text"]) + "."
    return GAP_ANY.format(need=item_short(it, p, row))


# an item's first sentence (what it needs, which the opened row's items already say)
# ends at the first full stop followed by a new sentence
FIRST_SENTENCE = re.compile(r"(?<=[\w)\]])\. (?=[A-Z(])")


def today_html(p, row, petals):
    """One click down, each item missing by its number with what it is today and our facts on it:
    the item in full less its first sentence, which the opened row's items already say; an item
    with nothing more is left out."""
    lis = []
    for k, it in enumerate(items_of(p), 1):
        rest = FIRST_SENTENCE.split(item_long(it, p, row, petals, False), maxsplit=1)
        if len(rest) == 2 and rest[1].strip():
            lis.append(f'<li value="{k}">{quoted(rest[1])}</li>')
    return f'<ol class="pmi">{"".join(lis)}</ol>' if lis else ""


# ------------------------------------------------------------------ Has, in full


def trial_of(row):
    """The stored trial of another of the publisher's verifiers (TR-1), printed under Formally
    verified; None where none is stored."""
    return next((t for t in row.get("trials_kept") or () if t["place"] == "machine_checked"), None)


def used_facts(p):
    return [f for f in p["read_facts"] if f.get("used", True)]


def reading_html(p, skip=()):
    """ "Our reading, on two points the grade uses. (1) ... (2) ...", each note's plain words; a
    fact only Met reads is named among the items missing, not here."""
    used = used_facts(p)
    facts = [f for f in used if f["fact"] not in skip]
    if not facts or not p["reading"]:
        return ""
    k = len(used)
    head = (f"Our reading, on {number(k) if k > 1 else 'one'} {'point' if k == 1 else 'points'} "
            "the grade uses (no single sentence of the publisher's says it):")  # fmt: skip
    body = " ".join(f"({i}) {f['plain'] or f['note']}" for i, f in enumerate(facts, 1)) \
        if len(facts) > 1 else (facts[0]["plain"] or facts[0]["note"])  # fmt: skip
    return p_(quoted(f"{head} {body}"), "prd")


def has_unforgeable(p, row, petals):  # noqa: PLR0912, PLR0915 (one paragraph per fact)
    f, out = facts_of(p), []
    if not f or not f.get("terms") or p["cause"] in ("not_stated", "check_failed", "not_read"):
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    expr, per = f["expression"], per_words(f)
    run, stated = f.get("run"), f.get("stated_for")
    vs = f.get("verifiers") or {}
    least = min(f["terms"])
    unit_said = (f.get("said") or {}).get("unit") or {}
    if f.get("basis") == "proved":
        tool = tool_word(petals)
        formal = petals["machine_checked"].get("formal") or {}
        checked = (
            (formal.get("scope_card") or {}).get("soundness", {}).get("protocol", {}).get("value")
        )
        by = (
            f", and states that {tool} has checked,"
            if tool and checked == "machine_checked"
            else ""
        )
        said = (f"The publisher proves{by} an upper bound on the chance that a fake reply passes "
                f"verification: at most {expr} {per}.")  # fmt: skip
        q = f.get("q_cross")
        if q:
            k = len(f["terms"]) - 1
            said += (" Here q is the number of hash queries a cheating prover makes while "
                     "searching for a forgery. The other "
                     f"{'term is' if k == 1 else 'terms are'} fixed, while the first grows with q, "
                     f"reaching 2^-100 at 2^{q[0]} queries and 2^-80 at 2^{q[1]} queries.")  # fmt: skip
        batch = next((i for i, it in enumerate(items_of(p), 1) if it["need"] == "batch"), None)
        if f.get("unit") == "proof" and f.get("one_reply") and batch:
            said += (f" Each reply has its own proof, generated in batches of "
                     f"{f['batch_size']} (see item {batch} below).")  # fmt: skip
        out.append(p_(e(said)))
    elif f.get("basis") == "conjectured":
        thing = unit_said.get("named") or "proof"
        said = (f"The publisher states {least} conjectured bits of security {per_words(f, True)}"
                f"{' of a proof' if unit_said.get('named') else ''}, corresponding to roughly a "
                f"2^-{least} chance that a forged {thing} passes.")  # fmt: skip
        b = (f.get("said") or {}).get("basis") or {}
        if b.get("named"):
            said += (f" This figure comes from the accounting of {b['named']}, "
                     f"{b.get('described') or 'as documented by the publisher'}.")  # fmt: skip
        said += (
            " Because it is conjectured, it rests on an unproven assumption rather than a proof."
        )
        out.append(p_(e(said)))
    else:
        out.append(p_(e(f"The publisher states a bound of {expr} {per}, without specifying "
                        "whether it is formally proved.")))  # fmt: skip
    if f.get("unit") == "part" and unit_said.get("named"):
        q = (unit_said.get("quotes") or [None])[0]
        quote = f" ({q_html(q)})" if q else ""
        out.append(p_(f"One {e(unit_said['named'])} covers {e(unit_said.get('described') or 'part of a reply')}"
                      f"{quote}. A full reply traverses every layer of the model, yet the "
                      "publisher states no combined bound for an entire reply."))  # fmt: skip
    rq = ((vs.get("run") or {}).get("quotes") or [None])[0]
    run_d = (vs.get("run") or {}).get("described")
    run_words = e(f"{run}, {run_d}" if run_d else f"{run}, the verifier we run")
    if stated:
        stated_d = (vs.get("stated") or {}).get("described")
        what = "The theorem is about" if f.get("basis") == "proved" else "The limit is stated for"
        said = f"{e(what)} {e(stated)}" + (f", {e(stated_d)}" if stated_d else "") + "."
        said += f" We run {run_words}" + (f" ({q_html(rq)})" if rq else "") + "."
        formal = petals["machine_checked"].get("formal") or {}
        tested = (formal.get("scope_card") or {}).get("soundness", {}).get("verifier_run", {}).get(
            "value"
        ) == "tested"
        no_claim = f.get("program") not in ("proved", "stated")
        if tested and no_claim:
            said += e(f" For {run}, the publisher states that it is tested, not proved, and claims "
                      "no limit.")  # fmt: skip
        elif tested:
            said += e(f" The publisher states that {run} is tested, not proved.")
        elif no_claim:
            said += e(f" The publisher claims no limit for {run}.")
        out.append(p_(said))
    else:
        adv = (
            ", and does not say which cheating provers it holds against"
            if f.get("adversary") == "not_said"
            else ""
        )
        check = (vs.get("run") or {}).get("check")
        runs = f". The publisher states that this command runs the publisher's check, {e(check)} ({q_html(rq)})" \
            if check and rq else (f" ({q_html(rq)})" if rq else "")  # fmt: skip
        said = f"The publisher names no verifier for this figure{e(adv)}. We run {run_words}{runs}."
        if check and unit_said.get("named") and rq and "chunk" in rq["text"]:
            said += e(f" The quotes we hold do not say how a chunk relates to a "
                      f"{unit_said['named']}.")  # fmt: skip
        out.append(p_(said))
    out.append(reading_html(p))
    return out


def why_html(p, row, petals):
    """The Why block on UF-9, WH-6 and MC-6 (amended 2026-11-17): the condition that set the
    step and the one that stops the next. No state reads it."""
    w = p.get("why")
    if not w:
        return ""
    step = STEP_WORD[step_key(p["step"], p["cause"])]
    if p["id"] == "unforgeable":
        i, j = w["first"], w["last"]
        items = f"item {i}" if i == j else f"items {i} to {j}"
        said = f"{step}: the limit is not shown to cover what we run ({items} above)."
        if w["floor"] == 80:
            said += f" Its exponents, as written, are {and_list(str(t) for t in w['exps'])}."
        else:
            said += f" It is not a theorem, and its exponent is {w['least']}."
        return p_(e(said), "pwy")
    if p["id"] == "weights_hidden":
        n = w["n"]
        return p_(e(f"{step}: there is a zero-knowledge theorem, at least for the method. Met needs the "
                    f"{count(n, 'item')} above."), "pwy")  # fmt: skip
    if p["id"] == "machine_checked":
        run = w.get("run")
        read = ", on our reading of the reach and the conclusion" if w.get("read") else ""
        stop = (f" It does not reach {run}." if not w.get("gaps")
                else " Met needs the items above.")  # fmt: skip
        return p_(e(f"{step}{read}.{stop}"), "pwy")
    return ""


def has_weights_hidden(p, row, petals):  # noqa: PLR0912 (one paragraph per fact)
    f, out = facts_of(p), []
    if p["cause"] in ("check_failed", "not_read") or not f:
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    k_docs = len(p["sources"])
    vq = first_quote(p, "verifier_gets_weights")
    if p["cause"] == "not_stated":
        said = (f"The {count(k_docs, 'document')} we read at the version we ran ({pin7(row)}) do "
                "not say whether a proof reveals the weights.")  # fmt: skip
        html = e(said)
        if f.get("verifier_gets_weights") is False:
            html += " They state that the verifier does not hold the weights" + \
                (f" ({q_html(vq)})" if vq else "") + \
                ", but that does not mean a proof hides them."  # fmt: skip
        return [p_(html)]
    if f.get("verifier_gets_weights") is True:
        out.append(
            p_("The verifier is given the weights" + (f" ({q_html(vq)})" if vq else "") + ".")
        )
    if f.get("stated") is False:
        q = first_quote(p, "stated")
        out.append(p_("The publisher states that a proof does not hide the weights"
                      + (f" ({q_html(q)})" if q else "") + "."))  # fmt: skip
    if p["step"] in ("amber_upper", "green"):
        tool = tool_word(petals)
        formal = petals["machine_checked"].get("formal") or {}
        in_tool = f" in {tool}" if tool and (formal.get("scope_card") or {}).get("zero_knowledge", {}).get(
            "protocol", {}).get("value") == "machine_checked" else ""  # fmt: skip
        said = (f"The publisher proves{in_tool} a zero-knowledge theorem showing that everything "
                "the verifier sees can be simulated without knowing the weights.")  # fmt: skip
        kind, model = f.get("zk_kind"), f.get("zk_model")
        if kind == "statistical":
            said += (" The guarantee is statistical, meaning the real and simulated views differ "
                     "by at most the tiny bound listed under the field's terms below.")  # fmt: skip
            said += (" It also assumes the random-oracle model, treating the hash function as "
                     "ideal randomness." if model == "random_oracle" else "")  # fmt: skip
        elif kind:
            said += f" It is {kind}."
        n = f.get("batch_size")
        if f.get("proof") == "protocol":
            said += (" The theorem covers the abstract protocol (as defined"
                     + (in_tool or "") + ") rather than the compiled programs we run")  # fmt: skip
            said += (", and applies to one request per proof." if f.get("zk_unit") == "request"
                     else ".")  # fmt: skip
            if f.get("zk_unit") == "request" and n and n > 1:
                said += (
                    f" Our benchmark runs batches of {n} replies, which the theorem does not cover."
                )
        else:
            said += " It covers the exact setup we run."
        out.append(p_(e(said)))
    elif p["step"] == "amber_lower":
        out.append(p_(e("The publisher claims that proofs hide the weights without proving a "
                        "zero-knowledge theorem.")))  # fmt: skip
    programs = next((r for r in used_facts(p) if r["fact"] == "programs"), None)
    if programs:
        out.append(p_(quoted((programs["plain"] or programs["note"]) + " This is our reading.")))
    elif f.get("programs") == "stated":
        out.append(p_(e("The publisher states that its programs keep the weights secret.")))
    elif f.get("programs") == "expected":
        out.append(p_(e("For its programs, the publisher states an expectation, not a statement.")))
    elif p["step"] in ("amber_upper", "green"):
        out.append(
            p_(e("The publisher does not say whether its programs keep the weights secret."))
        )
    out.append(visible_para(p))
    out.append(reading_html(p, skip=("programs",)))
    return out


def visible_para(p):
    """What stays visible, as the publisher lists it, the items whose own words say they depend
    on the weights named in the publisher's words, each with its explanation where it gives one."""
    f, visible = facts_of(p), p.get("visible") or []
    if not f.get("listed") or not visible:
        return ""
    m = len(visible)
    fitted = [v for v in visible if v["tag"] == FITTED]
    said = (f"The publisher lists {'at least ' if f.get('at_least') else ''}{m} things that stay "
            "visible to clients or the public, in a proof or around it.")  # fmt: skip
    if not fitted:
        return p_(e(said + " By its own words, none of them depends on the weights."))
    lis = []
    for v in fitted:
        head = q_html(v["quotes"][0]) if v["quotes"] else e(v["item"])
        more = v["quotes"][1:2]
        lis.append(f"<li>{head}" + (f" {q_html(more[0])}" if more else "") + "</li>")
    return (p_(e(f"{said} By its own words, {len(fitted)} of them depend on the weights:"))
            + f'<ul class="pls">{"".join(lis)}</ul>'
            + p_(e("Neither the publisher's list nor our records measure how much these reveal "
                   "about the weights.")))  # fmt: skip


def has_faithful(p, row, petals):
    f, out = facts_of(p), []
    if not f:
        return [p_(e(cap(p["reason"]) + "."))]
    rung, name = rung_of(row), name_of(row)
    c = f["controls"]
    bits = {"bf16": "16-bit", "f16": "16-bit", "f32": "32-bit"}.get(rung.get("reference_dtype"), "")
    model = f"{rung['model']}, {bits}" if bits else rung["model"]
    tokens = (
        S.V.get("request", {}).get("output_tokens")
        if isinstance(S.V.get("request"), dict)
        else None
    )
    most = f" ({tokens} at most)" if tokens else ""
    out.append(p_(e(f"We sent {f['n']:,} prompts to {name} and to the original model ({model}). On "
                    f"average, {name}'s replies match the original's for their first "
                    f"{sig(f['mean'])} tokens, up to the first difference{most}.")))  # fmt: skip
    rerun = c[f["rerun"]]["mean"] if f.get("rerun") in c else None
    every = (
        f" (every token, since {tokens} is the most a reply has)"
        if rerun is not None and tokens and rerun == tokens
        else ""
    )
    bar = f.get("bar") or {}
    m = re.match(r"q(\d)", str(bar.get("control") or ""))
    bar_bits = f" ({m.group(1)}-bit)" if m else ""
    scale = []  # (who, what it scores): the first takes the verb, the others share it
    if rerun is not None:
        scale.append(("the original model run a second time", f"{sig(rerun)}{every}"))
    scale += [
        ("our 8-bit copy", sig(c["q8_0"]["mean"])),
        ("our 4-bit copy", sig(c["q4_k_m"]["mean"])),
    ]
    if bar.get("display") is not None:
        scale.append((f"a copy we damaged on purpose{bar_bits}",
                      f"{sig((c.get(bar.get('control')) or {}).get('mean', bar['display']))}, "
                      "the pass bar every system must beat"))  # fmt: skip
    said = and_list([f"{scale[0][0]} scores {scale[0][1]}", *(f"{w} {v}" for w, v in scale[1:])])
    out.append(p_(e(f"For scale, we scored other runs on the same prompts: {said}.")))
    out.append(p_(e(proved_sentence(row, f))))
    if f.get("slots") == 1:
        out.append(p_(e("Our run sent one request at a time, as Met needs.")))
    return out


def proved_sentence(row, f):
    """What the row proves, in plain words: its weight bits and number format (the workload
    record and the publisher's words), and, where a copy proved at 8 bits scores below our 8-bit
    copy, that the two are different copies."""
    pr = row.get("precision") or {}
    fmt = pr.get("number_format") or {}
    name, rung = name_of(row), rung_of(row)
    w = (fmt.get("weights") or {}).get("value")
    a = (fmt.get("activations") or {}).get("value")
    bits = pr.get("bits")
    act = {"fixed_point": "fixed-point numbers (integers with a fixed scale)",
           "floating_point": "floating-point numbers",
           "integer": "integers"}.get(a)  # fmt: skip
    wword = FORMAT_WORD.get(w, "")
    if isinstance(bits, int | float) and pr.get("bits_covers") == "part":
        said = (f"The publisher states that {name} proves a copy with {bits_words(bits)}-bit "
                f"{wword} weights for part of its weights, and states no width for the rest.")  # fmt: skip
    elif isinstance(bits, int | float):
        said = (f"{name} proves a copy with {wword + ' ' if wword else ''}weights of "
                f"{bits_words(bits)} bits each on average")  # fmt: skip
        total, active = rung.get("parameters_total"), rung.get("parameters_active")
        if active and total and active < total:
            short = (
                rung["model"].split(" ")[0]
                if " " not in rung["model"]
                else " ".join(rung["model"].split(" ")[:3])
            )
            said += (f", counting the weights each token uses ({short} uses about "
                     f"{params_words(active)} of its {params_words(total)} weights for each "
                     "token)")  # fmt: skip
        said += "."
    else:
        said = f"{name} proves a copy whose weight width is not recorded."
    if act:
        said += f" Values between its layers are {act}."
    if f.get("below_own_width"):
        said += (f" {name}'s copy and our 8-bit copy (Q8_0, a llama.cpp format) are different 8-bit "
                 "copies. Our test measures the gap, not its cause.")  # fmt: skip
    return said


def params_words(n):
    return f"{n / 1e9:,.0f}B"


def has_machine_checked(p, row, petals):  # noqa: PLR0912 (one paragraph per fact)
    formal, out = p.get("formal") or {}, []
    run, stated = (v[0] for v in verifiers(row, petals).values())
    k_docs = len(p["sources"])
    if p["cause"] == "not_stated":
        return [p_(e(f"The {count(k_docs, 'document')} we read at the version we ran ({pin7(row)}) "
                     "name no computer-checked theorem."))]  # fmt: skip
    if p["cause"] in ("stated", "not_read") or not formal:
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    tool = str(formal.get("tool") or "").split(" ")[0]
    who = stated or "its verifier"
    said = (f"The publisher proves in {tool} (a proof assistant that mechanically checks every "
            f"step) that {who} rejects fake replies up to the error bound listed under "
            f"{PETAL_NAME['unforgeable']}.")  # fmt: skip
    noted = {f["fact"] for f in used_facts(p)}
    if formal.get("reach") == "protocol_and_statement":
        said += " The theorem statement includes the model's computation" + (
            " (see our reading below)." if "reach" in noted else ".")  # fmt: skip
    out.append(p_(e(said)))
    build = formal.get("build") or {}
    if build:
        version = str(build["toolchain"]["version"]).lstrip("v")
        if build.get("status") == "built" and build.get("exit_code") == 0:
            axioms = build.get("axioms") or []
            said = (f"We rebuilt the proof at commit {pin7(row)} using the publisher's pinned "
                    f"{tool} {version}. The publisher's check command exited 0 after "
                    f"{secs(build['seconds'])} ({hours(build['seconds'])}).")  # fmt: skip
            if axioms and p["step"] in ("amber_upper", "green"):
                said += (f" It relies only on {tool}'s {number(len(axioms))} standard axioms, "
                         "confirming no proof steps were skipped.")  # fmt: skip
            if formal.get("limits"):
                said += (f" {tool} itself remains part of the trusted base, and the publisher's "
                         "documented caveats appear below.")  # fmt: skip
        elif build.get("status") == "stopped":
            said = (
                f"Our rebuild at {pin7(row)} stopped before reaching a verdict "
                f"({secs(build['seconds'])})."
            )
        else:
            said = f"Our rebuild at {pin7(row)} failed with exit code {build.get('exit_code')}."
        out.append(p_(e(said)))
    elif p["cause"] == "proof_build_not_run":
        out.append(p_(e("We have not rebuilt it yet.")))
    if formal.get("reach") != "verifier_run" and run:
        tested = (formal.get("scope_card") or {}).get("soundness", {}).get("verifier_run", {}).get(
            "value"
        ) == "tested"
        said = e(
            f"It does not reach {run_named(row, petals)}"
            + (f". The publisher states that {run} is tested, not proved" if tested else "")
            + "."
        )
        if formal.get("input_code_unverified") is True:
            qs = ((formal.get("said") or {}).get("input_code_unverified") or {}).get("quotes") or []
            said += " Input-reading code sits outside it" + (
                f": {q_html(qs[0])}, as the publisher states." if qs else "."
            )
        out.append(p_(said))
    if formal.get("theorem"):
        out.append(p_(e(f"We hold no record of a review of the theorem's statement by an outside "
                        f"{tool} expert.")))  # fmt: skip
    out.append(reading_html(p))
    return out


def limits_html(p):
    """Formally verified: the limits the publisher states that no rule reads, each in plain words
    and then its own, linked. They set nothing."""
    lim = (p.get("formal") or {}).get("limits") or []
    if not lim:
        return ""
    lis = "".join(f"<li>{quoted(i['plain'])} ({q_html(i['quotes'][0])} ↗)</li>" for i in lim)
    return block("limits", f'<ul class="pls">{lis}</ul>')


def has_trust(p, row, petals):
    f, out = facts_of(p), []
    if p["cause"] in ("not_stated", "not_read") or not f:
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    q = first_quote(p, "publicly_checkable")
    plain = said_of(p, "publicly_checkable").get("plain")
    if plain:
        out.append(p_(quoted(plain) + (f" (the publisher's words: {q_html(q)})" if q else "")))
    elif f.get("publicly_checkable") is True:
        out.append(p_("Anyone can check a proof, as the publisher states"
                      + (f" ({q_html(q)})" if q else "") + "."))  # fmt: skip
    elif f.get("publicly_checkable") is False:
        out.append(p_("Only a named party can check a proof, as the publisher states"
                      + (f" ({q_html(q)})" if q else "") + "."))  # fmt: skip
    rests = next((r for r in used_facts(p) if r["fact"] == "rests_on"), None)
    if rests:
        out.append(p_(quoted(rests["plain"] or rests["note"])))
        out.append(p_(e("So, on our reading, soundness rests on cryptographic assumptions only, "
                        "and no setup step produced a secret. But the publisher does not say this "
                        "in one sentence.")))  # fmt: skip
    else:
        out.append(p_(e(cap(has_short(p, row, petals)) + ".")))
    return out


HAS = {"unforgeable": has_unforgeable, "weights_hidden": has_weights_hidden,
       "faithful_model": has_faithful, "machine_checked": has_machine_checked,
       "no_trusted_party": has_trust}  # fmt: skip


# ------------------------------------------------------------------ Evidence and the field's terms


def headless(html):
    """A block without its own head, where the summary over it already says it."""
    return re.sub(r'^<p class="pvh">.*?</p>', "", html, count=1)


def details_list(head, body):
    return f'<details class="more pev"><summary>{e(head)}</summary>{body}</details>'


def evidence_short(p, row, petals):  # noqa: PLR0912 (one line per kind of evidence)
    """An opened row's evidence, one line each, under the disclosure that names it: what the grade
    comes from where our reading is part of it, the publisher's words (their count, opening on the
    quotes), the documents read where they are silent, what the publisher states and lists, our
    reading's notes, and our test or rebuild in a few words, linked to its record."""
    out, pid = [], p["id"]
    src = came_from_words(p) if read_sets_grade(p) else ""
    if src:
        out.append(p_(e(src), "pel pfm"))
    if p["quotes"]:
        out.append(details_list(EVIDENCE["quotes"].format(pin=pin7(row), n=f"{len(p['quotes']):,}"),
                                quote_links(p["quotes"])))  # fmt: skip
    if p["sources"] and p["cause"] == "not_stated":
        docs = "".join(f'<p class="pel"><a href="{e(d["url"])}">{e(d["path"])}</a></p>'
                       for d in p["sources"])  # fmt: skip
        out.append(details_list(EVIDENCE["docs"].format(n=len(p["sources"])), docs))
    if pid == "weights_hidden" and p.get("forms"):
        out.append(details_list(EVIDENCE["forms"].format(n=f"{len(p['forms']):,}"),
                                headless(forms_html(p["forms"]))))  # fmt: skip
    if pid == "weights_hidden" and p.get("visible"):
        n = f"{'at least ' if p.get('visible_at_least') else ''}{len(p['visible'])}"
        out.append(details_list(EVIDENCE["visible"].format(n=n),
                                headless(visible_html(p["visible"], p.get("visible_at_least")))))  # fmt: skip
    if p["read_facts"]:
        k = len(p["read_facts"])
        body = "".join(p_(e(f["note"]), "cn") for f in p["read_facts"])
        used = used_facts(p)
        unused = [f for f in p["read_facts"] if not f.get("used", True)]
        if unused:  # which readings the grade uses and which it does not, each named
            if used:
                body += p_(e(EVIDENCE["used"].format(this=reading_topics(f["fact"] for f in used))),
                           "pel")  # fmt: skip
            body += p_(e(EVIDENCE["not_used"].format(
                this=reading_topics(f["fact"] for f in unused))), "pel")  # fmt: skip
        out.append(details_list(EVIDENCE["notes"].format(n=f"{k:,}"), body))
    if pid in ("unforgeable", "machine_checked", "weights_hidden"):
        if pid == "machine_checked":
            formal = p.get("formal") or {}
            build = formal.get("build") or {}
            if build:
                tool = build["toolchain"]["name"].rsplit("/", 1)[-1]
                tc = f"{tool} {build['toolchain']['version']}"
                said = EVIDENCE["rebuild_short"].format(tc=tc, code=build["exit_code"])
                out.append(p_(f'<a href="{e(link(build["record"]))}">{e(said)} ↗</a>', "pel"))
        cids = ("no_weight_file",) if pid == "weights_hidden" else ("model", "prompt", "reply")
        states = {check_state(row, c) for c in cids}
        word = "passed" if states == {"held"} else "failed" if "failed" in states else "not decided"
        said = EVIDENCE["checks_short"].format(names=", ".join(CHECK_WORD[c] for c in cids),
                                               s="" if len(cids) == 1 else "s", state=word)  # fmt: skip
        out.append(p_(f'<a href="#checks">{e(said)}</a>', "pel"))
    elif pid == "faithful_model":
        fid = rung_of(row).get("fidelity") or {}
        n = facts_of(p).get("n")
        said = EVIDENCE["fidelity_short"].format(n=f"{n:,} prompts" if n else "")
        recl = f' <a href="{e(link(fid["path"]))}">{e(RECORD_LINK)}</a>' if fid.get("path") else ""
        out.append(p_(f'<a href="#fidelity">{e(said)}</a>{recl}', "pel"))
    else:
        out.append(p_(e(cap(EVIDENCE["none_short"])), "pel"))
    return "".join(out)


def records_full(p, row):
    """Our records in full, one click down: what each test does, the rebuild's command and times,
    and a trial outside the grade."""
    out, pid = [], p["id"]
    if pid in ("unforgeable", "machine_checked"):
        states = [check_state(row, c) for c in ("model", "prompt", "reply")]
        if pid == "machine_checked":
            formal = p.get("formal") or {}
            build = formal.get("build") or {}
            if build:
                thm = formal.get("theorem")
                thm_html = (
                    f'<a href="{e(formal["theorem_url"])}"><code>{e(thm)}</code> ↗</a>'
                    if thm and formal.get("theorem_url")
                    else e(thm or "")
                )
                tc = f"{build['toolchain']['name']} {build['toolchain']['version']}"
                axioms = ", ".join(build.get("axioms") or [])
                said = (f"{thm_html}, {e(tc)}, the publisher's command, started "
                        f"{e(build['started_at'][:10])}, {e(secs(build['seconds']))}, exit code "
                        f"{build['exit_code']}" + (f", axioms {e(axioms)}" if axioms else "") + ". "
                        f'<a href="{e(link(build["record"]))}">{e(RECORD_LINK)}</a>')  # fmt: skip
                out.append(p_(f'<span class="k">{e(EVIDENCE["rebuild"])}</span> {said}', "pel"))
            t = trial_of(row)
            if t:
                out.append(p_(f'<span class="k">{e(EVIDENCE["outside"])}</span> {trial_words(t)} '
                              f'<a href="{e(link(t["record"]))}">{e(RECORD_LINK)}</a>', "pel"))  # fmt: skip
            state = "passed on this run" if all(s == "held" for s in states) else \
                "did not all pass on this run (see Checks)"  # fmt: skip
            out.append(p_(e(cap(RECORDS[pid].format(state=state))), "pel"))
        else:
            state = ("Each was refused on this run." if all(s == "held" for s in states)
                     else "Not every one was refused on this run.")  # fmt: skip
            out.append(p_(e(cap(RECORDS[pid].format(state=state))), "pel"))
    elif pid == "weights_hidden":
        s = check_state(row, "no_weight_file")
        state = {"held": "It passed on this run.", "failed": "It failed on this run."}.get(
            s, "It is not decided on this run."
        )
        out.append(p_(e(cap(RECORDS[pid].format(state=state))), "pel"))
    elif pid == "faithful_model":
        rung = rung_of(row)
        n = facts_of(p).get("n")
        out.append(p_(e(cap(f"our fidelity run on {rung['model']}" + (f", {n:,} prompts" if n else "")
                            + ", each reply scored against the original's.")), "pel"))  # fmt: skip
    return out


TRIAL_CHANGE = {"commitment_id": "one proof with a commitment that no run of ours made",
                "other_session_commitment": "a proof checked against another run's commitment of "
                "the same weights",
                "reply_token": "proofs with one reply token changed"}  # fmt: skip


def trial_words(t):
    """TR-1's trial in plain words, as HTML: what it accepted, what it refused, its times. It sets
    no grade."""
    n = t["honest"]
    said = (f"we ran {t['verifier']} on {count(n, 'honest proof')} from our runs, at the files we "
            f"run")  # fmt: skip
    if t.get("counted") is not None and t["counted"] < n:
        said += f" ({t['counted']:,} from counted sessions)"
    said += f". It accepted {t['accepted']:,} of {n:,}."
    for k in t["changes"]:
        what = TRIAL_CHANGE.get(k, k)
        refused = t["changed_rejected"] == t["changed"]
        said += (f" As a check that it can refuse, we also gave it {what}, and "
                 + ("it refused that proof." if refused and t["changed"] == 1 else
                    f"it refused {t['changed_rejected']:,} of {t['changed']:,}."))  # fmt: skip
    if t.get("seconds_min") is not None:
        lo, hi = f"{t['seconds_min']:,.0f}", f"{t['seconds_max']:,.0f}"
        span = lo if lo == hi else f"{lo} to {hi}"
        said += (f" {cap(KEPT_TIME)} reads {span}\u00a0s per proof (n\u00a0=\u00a0"
                 f"{n - t.get('no_verdict', 0):,}).")  # fmt: skip
    return e(said)


def yes_no(v):
    return {True: "yes", False: "no", None: "not stated"}.get(v, str(v).replace("_", " "))


def terms_html(p, row, petals):  # noqa: PLR0912, PLR0915 (one sentence per fact)
    """The petal in the field's terms, for specialists: the exact facts, their values as the
    rules read them, and which are our reading."""
    f, pid = facts_of(p), p["id"]
    read = {r["fact"] for r in p["read_facts"]}

    def r(k):
        return " (our reading)" if k in read else ""

    term = PETAL_TERM[pid][:1].upper() + PETAL_TERM[pid][1:]
    out = [term + (f" (mean, n = {f['n']:,})." if pid == "faithful_model" and f else ".")]
    if pid == "unforgeable" and f.get("terms"):
        q = f.get("q_cross")
        out.append(f"Bound: {'at most ' if f.get('basis') == 'proved' else ''}{f['expression']} "
                   f"{per_words(f)}" + (f", after {f['after']}" if f.get("after") else "") + ".")  # fmt: skip
        if q:
            out.append(f"The first term is 2^-100 at q = 2^{q[0]} and 2^-80 at q = 2^{q[1]}.")
        basis = f.get("basis")
        b_named = ((f.get("said") or {}).get("basis") or {}).get("named")
        out.append(f"Basis: {basis}" + (f", {b_named}'s accounting" if b_named else "") + ".")
        out.append(f"Stated for: {f.get('stated_for') or 'no verifier named'}. We run: {f.get('run')}"
                   + (" (no bound claimed for it)" if f.get("program") not in ("proved", "stated") else "") + ".")  # fmt: skip
        out.append(f"Adversary: {yes_no(f.get('adversary'))}{r('adversary')}.")
        unit = f.get("unit")
        named = ((f.get("said") or {}).get("unit") or {}).get("named")
        out.append(
            f"Unit: {named or unit}"
            + (", one reply per proof" if unit == "proof" and f.get("one_reply") else "")
            + "."
        )
        n = f.get("batch_size")
        out.append(f"Batch: {yes_no(f.get('batch'))}. Ours is {count(n, 'reply', 'replies') if n else 'not recorded'}"
                   + (", each verified in its own call" if n and n > 1 else "") + ".")  # fmt: skip
        out.append(f"Parameters: {yes_no(f.get('parameters'))}{r('parameters')}.")
        out.append(f"Conditions shown for our files: {yes_no(f.get('conditions_shown'))}.")
    elif pid == "weights_hidden" and f:
        formal = petals["machine_checked"].get("formal") or {}
        bound = ((formal.get("scope_bounds") or {}).get("zero_knowledge") or {}).get("text")
        form = [
            w
            for w in (
                f.get("zk_kind"),
                {"random_oracle": "random-oracle model", "standard": "standard model"}.get(
                    f.get("zk_model")
                ),
            )
            if w
        ]
        if f.get("proof") in ("protocol", "configuration_run"):
            out.append(f"Proved: {', '.join(form) or 'yes'}, for the {'protocol' if f['proof'] == 'protocol' else 'configuration we run'}"
                       + (", one request a proof" if f.get("zk_unit") == "request" else "") + ".")  # fmt: skip
        else:
            out.append(f"Stated: {yes_no(f.get('stated'))}. Proved: no.")
        if bound:
            out.append(f"The publisher's bound: {bound}.")
        n = f.get("batch_size")
        if f.get("zk_unit") == "request" and n and n > 1:
            out.append(f"Not for our {n}-reply batches.")
        out.append(f"Programs: {yes_no(f.get('programs'))}{r('programs')}.")
        out.append(f"Weights given to the verifier: {yes_no(f.get('verifier_gets_weights'))}.")
        if f.get("listed"):
            k = len(f.get("fitted") or [])
            out.append(f"Visible: {'at least ' if f.get('at_least') else ''}{f.get('visible_count')}, "
                       f"{k} tagged fitted to the weights.")  # fmt: skip
        else:
            out.append("Visible list: none published.")
    elif pid == "faithful_model" and f:
        method = " (exact)" if f.get("method") == "exact" else ""
        alpha = f.get("alpha")
        u, g = f["upper"], f["green"]
        out.append(f"Above T_upper, {tenth(u['display'])} (Mostly met): "
                   f"{'shown' if u['shown'] else 'not shown'}. Above T_green, "
                   f"{tenth(g['display'])} (Met): {'shown' if g['shown'] else 'not shown'}. "
                   f"Test: paired sign-flip per prompt{method}, alpha {alpha}.")  # fmt: skip
        pw = proved_words(row, long=True)
        if pw:
            out.append(cap(pw) + ".")
        out.append("Decoding: accepts tokens other than the model's top choice." if
                   f.get("policy_cap") else "Decoding: exact match (only the model's top token).")  # fmt: skip
        fid = rung_of(row).get("fidelity") or {}
        slots = []
        for run in fid.get("runs") or ():
            who = ("the copies" if run.get("part") else "the original and its rerun") \
                if len(fid.get("runs") or ()) > 1 else "the whole run"  # fmt: skip
            slots.append(f"no count for {who} (vLLM, one call)" if run.get("engine") == "vllm"
                         else f"{run.get('slots')} for {who} ({run.get('engine')})")  # fmt: skip
        out.append(f"Requests at a time (slots): {and_list(slots) or yes_no(None)}.")
    elif pid == "machine_checked":
        formal = p.get("formal") or {}
        if formal.get("tool") or formal.get("theorem"):
            out.append(
                f"Reach: {REACH_LABEL.get(formal.get('reach'), formal.get('reach'))}{r('reach')}."
            )
            thm = formal.get("theorem")
            if thm:
                th = (
                    f'<a href="{e(formal["theorem_url"])}"><code>{e(thm)}</code> ↗</a>'
                    if formal.get("theorem_url")
                    else f"<code>{e(thm)}</code>"
                )
                out.append(("raw", f"Theorem: {th}."))
            out.append(f"Tool: {formal.get('tool')}.")
            base = formal.get("trusted_base") or []
            if base:
                out.append(f"Trusted base: {', '.join(base)}.")
            out.append(
                f"Input-reading code outside the proof: {yes_no(formal.get('input_code_unverified'))}."
            )
            out.append(f"Conclusion: {yes_no(formal.get('conclusion'))}{r('conclusion')}.")
            st = (row.get("statement") or {}).get("verifiers") or {}
            if st.get("stated") and st.get("run") and st["stated"] != st["run"]:
                out.append(f"Stated for {st['stated']}, not {st['run']}.")
            if thm and formal.get("tool"):
                out.append(
                    f"No review of the statement by an outside {str(formal['tool']).split()[0]} "
                    "expert is recorded."
                )
        else:
            out.append("Tool, theorem and trusted base: not stated.")
        out.append(("raw", f'Scope: <a href="#scope">{e(SCOPE_LINK)}</a>'))
    elif pid == "no_trusted_party" and f:
        rests = yes_no(f.get("rests_on"))
        rests += " (no setup made a secret)" if f.get("rests_on") == "transparent" else ""
        out.append(f"Rests on: {rests}{r('rests_on')}.")
        out.append(f"Publicly checkable: {yes_no(f.get('publicly_checkable'))}.")
    html = " ".join(o[1] if isinstance(o, tuple) else e(o) for o in out)
    return block("terms", p_(html, "ptm"))


# ------------------------------------------------------------------ a criterion's row (amended 2026-11-22, owner decision)


def block(key, body):
    return f'<div class="pbk"><h5 class="pbh">{e(PETAL_BLOCK[key])}</h5>{body}</div>'


def in_full(p, row, petals):
    """One click down in an opened row: this system's own facts in full (what it has, every
    item missing with what it is today, our records, why the grade, the limits the publisher
    states, the field's terms). How a grade is set is the checks page's."""
    why = why_html(p, row, petals)
    records = "".join(records_full(p, row))
    today = today_html(p, row, petals)
    body = (why
            + block("needs", p_(e(cap(needs_short(p)) + ".")))
            + block("has", "".join(HAS[p["id"]](p, row, petals)))
            + (block("missing", today) if today else "")
            + (block("records", records) if records else "") + limits_html(p)
            + terms_html(p, row, petals))  # fmt: skip
    return f'<details class="more pfull"><summary>{e(IN_FULL)}</summary>{body}</details>'


LADDER = ("amber_lower", "amber_upper", "green")  # the grades a track draws, lowest first
TRACK_CLASS = {"held": "hd", "open": "op", "unlisted": "un", "lead": "ld"}  # words.css draws each


def track(p):
    """The track a row draws, from the board's `to_met`: one column per grade from Partly met to
    Met, lowest first, after one for the items that come before any grade (a decision for a Not
    decided row, a repair for a Failed one) where the row has them. Each column is {key, word,
    kind, items}: kind `held` for a grade the row holds (drawn solid in its ink), `open` for one
    it does not hold up to the highest grade the board lists items for (an outline, one open
    square per item, none where reaching the grade above takes it too), `unlisted` for a grade
    past that one (dashed: the board lists what it needs only once the grades below are held),
    `lead` for the decision or the repair; items are (number, item), numbered from 1 in the
    board's order, the numbers "Why this grade" refers to."""
    numbered, k = [], 0
    for g in p["to_met"]:
        its = []
        for it in g["items"]:
            k += 1
            its.append((k, it))
        numbered.append((g, its))
    held = LADDER.index(p["step"]) + 1 if p["step"] in LADDER else 0
    reach = max((LADDER.index(g["to"]) + 1 for g, _ in numbered if g["to"] in LADDER), default=0)
    cols = []
    lead = [(g, its) for g, its in numbered if g["to"] not in LADDER]
    if any(its for _, its in lead):
        cols.append({"key": None, "word": MISSING_STEP[lead[0][0]["kind"]], "kind": "lead",
                     "items": [x for _, its in lead for x in its]})  # fmt: skip
    for i, key in enumerate(LADDER, 1):
        kind = "held" if i <= held else "open" if i <= reach else "unlisted"
        cols.append({"key": key, "word": STEP_WORD[key], "kind": kind,
                     "items": [x for g, its in numbered if g["to"] == key for x in its]})  # fmt: skip
    return cols


def track_said(cols):
    """The track in words, for a screen reader: "Partly met: held. Mostly met: 3 missing. Met:
    2 missing."."""
    return " ".join(TRACK_SAID[c["kind"]].format(grade=c["word"], n=f"{len(c['items']):,}") + "."
                    for c in cols)  # fmt: skip


def track_head(cols):
    """The closed row's track: each grade's word over its cell, a held grade's cell solid in the
    row's ink, each other cell holding one open square per item missing for it (words.css draws
    the kinds). The drawing is hidden from a screen reader, which reads `track_said`; opened, the
    squares give way to the items under their cells (`track_items`)."""
    cells = "".join(f'<span class="ctp {TRACK_CLASS[c["kind"]]}"><span class="cth">{e(c["word"])}'
                    '</span><span class="ctc">'
                    + '<i class="ctq"></i>' * len(c["items"]) + "</span></span>"
                    for c in cols)  # fmt: skip
    return (f'<div class="ctk"><p class="sr">{e(track_said(cols))}</p>'
            f'<div class="ctg n{len(cols)}" aria-hidden="true">{cells}</div></div>')  # fmt: skip


def track_items(cols, p, row, mixed):
    """The opened row's items, the track's columns again: under each grade's cell, in its column,
    each item missing for it by its number, in a few words, with who acts where both act. A
    grade's word and cell stand over its items on a phone only, where the columns stand one under
    another (words.css)."""
    out = []
    for c in cols:
        lis = "".join(f'<li><span class="ctn">{n:,}</span><span class="ctx">'
                      f'{e(cap(item_short(it, p, row)))}'
                      + (f'<span class="ctw">{e(WHO_TAG[it["by"]])}</span>' if mixed else "")
                      + "</span></li>" for n, it in c["items"])  # fmt: skip
        out.append(f'<div class="ctp {TRACK_CLASS[c["kind"]]}"><p class="cth">{e(c["word"])}</p>'
                   '<span class="ctc"></span>'
                   + (f'<ul class="ctl">{lis}</ul>' if lis else "") + "</div>")  # fmt: skip
    return f'<div class="ctg cti n{len(cols)}">{"".join(out)}</div>'


def kv_lines(p, row, petals, charted=False):
    """An opened row's three lines under its question: whom the criterion protects, what Met
    needs and what the system has, each in a few words, one home for every grade."""
    lines = ((PROTECTS_HEAD, PETAL_PROTECTS[p["id"]]), (NEEDS_HEAD, needs_tiny(p, row, petals)),
             (HAS_HEAD, has_tiny(p, row, petals, charted)))  # fmt: skip
    return ('<dl class="ckv">'
            + "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in lines if v)
            + "</dl>")  # fmt: skip


# a chart line's kind (its class) and how plots.hbar draws its bar: the row's own mean (solid
# paper), a grade's threshold (an outline), a run on the same prompts (grey)
CHART_INK = {"cfm": "bp", "cft": "bc", "cfo": "bg"}


def fidelity_chart(p, row):
    """Fidelity opened: the row's mean matched leading tokens among what its grades are measured
    against, as bars from zero on one scale: what Mostly met and Met need (outlines), the runs on
    the same prompts each lies halfway between and the bar's copy (grey, the bar linked to its
    definition), the row itself (solid), highest first, each beside its figure, a list a screen
    reader reads line by line; the axis from zero to the reply's length (the request's reply
    tokens), the measure and n between its ends, the figure's caption. Drawn only where the board
    holds the row's mean, n, the reply's length and one value at least to set beside the mean,
    every one on that axis; else nothing."""
    f, req = facts_of(p), S.V.get("request")
    top = req.get("output_tokens") if isinstance(req, dict) else None
    if p["id"] != "faithful_model" or not isinstance(f.get("mean"), int | float) \
            or not f.get("n") or not isinstance(top, int) or top <= ZERO:  # fmt: skip
        return ""
    lines = [(e(name_of(row)), sig(f["mean"]), f["mean"], "cfm")]
    for key, step in (("upper", "amber_upper"), ("green", "green")):
        t = f.get(key) or {}
        if isinstance(t.get("display"), int | float):
            said = tenth(t["display"]) + (CHART_NOT_SHOWN if t.get("shown") is False
                                          and f["mean"] > t["display"] else "")  # fmt: skip
            lines.append((e(CHART_NEEDS.format(grade=STEP_WORD[step])), said,
                          t.get("value", t["display"]), "cft"))  # fmt: skip
    bar = (f.get("bar") or {}).get("control")
    named = [*((f.get("upper") or {}).get("controls") or ()),
             *((f.get("green") or {}).get("controls") or ()), *((bar,) if bar else ())]  # fmt: skip
    for cid in dict.fromkeys(named):
        c = (f.get("controls") or {}).get(cid) or {}
        if isinstance(c.get("mean"), int | float):
            name, title = control_name(cid)
            label = e(cap(name.partition(" (")[0]))
            label = f'<span title="{e(title)}">{label}</span>' if title else label
            if cid == bar:
                label += f', <a href="/glossary#bar">{e(CHART_BAR)}</a>'
            lines.append((label, sig(c["mean"]), c["mean"], "cfo"))
    if len(lines) < 2 or any(not ZERO <= v <= top for _, _, v, _ in lines):
        return ""
    bars = "".join(f'<li class="cfr {kind}"><span class="cfl">{label}</span>'
                   f'<span class="cff">{e(said)}</span>{hbar([(v, CHART_INK[kind])], top, h=12)}'
                   "</li>" for label, said, v, kind in sorted(lines, key=lambda r: -r[2]))  # fmt: skip
    caption = CHART_CAPTION.format(n=f"{f['n']:,}")
    axis = (f'<figcaption class="cfx"><span>{ZERO:,}</span><span class="cfu">{e(caption)}</span>'
            f"<span>{top:,}</span></figcaption>")  # fmt: skip
    return f'<figure class="cfc"><ul class="cfg">{bars}</ul>{axis}</figure>'


def verdict(p):
    """The grade as a word in its ink, in display type, linked to the rule that sets it on the
    checks page (its cause's line where a cause set it); "our reading" beside it, linked to what
    that means there, where a reading of ours sets the grade."""
    tok = f"{p['state']} {p['form']}".strip()
    href = f"{CHECKS_PAGE}#cause-{e(p['cause'])}" if p["cause"] else f"{CHECKS_PAGE}#{e(p['id'])}"
    # the cause in the title, unless the step word already says it ("Not stated")
    cause = CAUSE_WORD[p["cause"]] if p["cause"] else ""
    title = f' title="{e(cause)}"' if cause and cause != petal_step(p).lower() else ""
    mark = (f'<a class="pfr" href="{CHECKS_PAGE}#reading">{e(READING_MARK)}</a>'
            if read_sets_grade(p) else "")  # fmt: skip
    return f'<a class="pvd {tok}" href="{href}"{title}>{e(petal_step(p))}</a>{mark}'


def criterion(p, row, petals):
    """One criterion's row. Closed: its name (linked to its rule on the checks page, its field
    term in the link's title), its plain question, its grade (`verdict`), the one sentence of what
    is missing first and its track; the whole row opens it, its control the count missing (or
    "Evidence" where none is), set at the row's top right. The control is a native disclosure's
    summary laid over the closed row (words.css), so nothing a reader can click sits inside it:
    the name's, the grade's and our reading's links stand over it. Opened (with or without script): Protects, Met needs and Has under the
    question; the items under their grades' cells, who acts; Fidelity's chart; then the evidence
    and "Why this grade", one click further each (the evidence open at once where nothing is
    missing, as the control already says "Evidence"). `data-step` and `data-cause` carry the
    board's step and cause."""
    pid, tok = p["id"], f"{p['state']} {p['form']}".strip()
    data = f' data-step="{e(p["step"] or "none")}"'
    if p["cause"] is not None:
        data += f' data-cause="{e(p["cause"])}"'
    cols, items = track(p), items_of(p)
    whos = sorted({it["by"] for it in items})
    gap = gap_sentence(p, row, petals)
    head = (f'<div class="crh"><h3 class="crn"><a href="{CHECKS_PAGE}#{e(pid)}" '
            f'title="{e(FIELD_TERMS_TITLE.format(term=PETAL_TERM[pid]))}">'
            f'{e(PETAL_NAME[pid])}</a></h3><p class="crq">{e(PETAL_ASK[pid])}</p>'
            f'<p class="crg">{verdict(p)}</p><div class="crm">'
            + (f'<p class="crs">{e(gap)}</p>' if gap else "") + f"{track_head(cols)}</div></div>")  # fmt: skip
    who = (f'<p class="crw"><span class="k">{e(WHO_HEAD)}</span> {e(WHO_TAG[whos[0]])}</p>'
           if len(whos) == 1 else "")  # fmt: skip
    evidence = (f'<details class="more cev"{"" if items else " open"}><summary>'
                f'{e(EVIDENCE["head"])}</summary><div class="cevb">'
                f"{evidence_short(p, row, petals)}</div></details>")  # fmt: skip
    chart = fidelity_chart(p, row)
    body = (f'<div class="crb">{kv_lines(p, row, petals, bool(chart))}<div class="crbm">'
            f"{track_items(cols, p, row, len(whos) > 1)}{who}{chart}"
            f'<div class="cro">{evidence}{in_full(p, row, petals)}</div></div></div>')  # fmt: skip
    tag = MISSING_TAG.format(n=f"{len(items):,}") if items else EVIDENCE_TAG
    toggle = f'<summary class="crt" aria-label="{e(tag)}, {e(PETAL_NAME[pid])}">{e(tag)}</summary>'
    return sup(nobreak(f'<div class="crr {tok}" id="petal-{e(pid)}"{data}>{head}'
                       f'<details class="more crd">{toggle}{body}</details></div>', row))  # fmt: skip


POWER = re.compile(r"(?<=[0-9q])\^(-?)(\d+)")  # 2^-128, 2^24 as the data writes them
QUOTE_OPEN = re.compile(r'<a class="(?:iq|qt)"')
MINUS = "\u2212"
NBSP = "\u00a0"
ARROW = re.compile(" ([\u2193\u2197])")  # an arrow stays on its words' line


def sup(html):
    """An exponent as typeset (2<sup>, a minus sign, 128, </sup>), in the page's own words only:
    the data keeps its ASCII, and a quote of the publisher's prints as written; an arrow stays on
    its words' line. Only in text, never in a tag."""
    out, in_quote = [], False
    for part in re.split(r"(<[^>]*>)", html):
        if part.startswith("<"):
            if QUOTE_OPEN.match(part):
                in_quote = True
            elif part == "</a>":
                in_quote = False
            out.append(part)
        else:
            text = ARROW.sub(NBSP + r"\1", part)
            out.append(text if in_quote else POWER.sub(
                lambda m: f"<sup>{MINUS if m[1] else ''}{m[2]}</sup>", text))  # fmt: skip
    return "".join(out)


HYPHENED = r"(?<![\w-])\w+(?:-\w+)+(?![\w-])"  # "8-bit", "zero-knowledge", "one-at-a-time"


def whole(m):
    """A match kept whole: one span, and in it each of its words, where it has more than one, kept
    whole too, so a column narrower than the name breaks it at a space only (words.css)."""
    words = m.group(0).split(" ")
    if len(words) > 1:
        each = " ".join(f'<span class="nw">{w}</span>' for w in words)
        return f'<span class="nw">{each}</span>'
    return f'<span class="nw">{m.group(0)}</span>'


def nobreak(html, row):
    """A verifier's name never breaks across lines ("boundary-grid --verify"), nor a word at its
    hyphen ("8-bit"): each is wrapped in a span that CSS keeps whole, its characters unchanged, so
    a copied command still runs; in an item's or a line's narrow column a name breaks at its space
    only (`whole`). Only in text, never inside a tag or an attribute."""
    names = sorted({n for n in ((row.get("statement") or {}).get("verifiers") or {}).values()
                    if n and "-" in n}, key=len, reverse=True)  # fmt: skip
    pat = re.compile("|".join([*(re.escape(e(n)) for n in names), HYPHENED]))
    parts = re.split(r"(<[^>]*>)", html)
    return "".join(pt if pt.startswith("<") else pat.sub(whole, pt) for pt in parts)


def grade_scale():
    """The grades on the title's line, always shown: their label, then the grades, best first, each
    in its ink, each linked to its definition; a line breaks only before a separator, which starts
    the next line."""
    seps = ("", *GRADE_SCALE_SEP)
    words = "".join('<span class="gw">'
                    + (f'<span class="gsep" aria-hidden="true">{e(sep)}</span>' if sep else "")
                    + f'<a class="pvd {tok}" href="/glossary#{slug}">{e(w)}</a></span>'
                    for (tok, w, slug), sep in zip(GRADE_SCALE, seps, strict=True))  # fmt: skip
    return f'<p class="gscale crsc"><span class="k">{e(GRADE_SCALE_HEAD)}</span>{words}</p>'


def criteria_section(row, scope_head):
    """The Criteria section (amended 2026-11-22, owner decision): the grade scale on the title's
    line, always shown, the five criteria in the board's order (`criterion`), then completeness on
    one line with the stated security and the scope card (`scope_head`) one click down."""
    petals = {p["id"]: p for p in row["glyph"]}
    rows = "".join(criterion(p, row, petals) for p in row["glyph"])
    return f'{grade_scale()}<div class="cri">{rows}</div><div id="scope">{scope_head}</div>'
