"""A petal on a system page (RFC-0018 SI-3, GL-11, amended 2026-11-17, owner decision).

Each petal answers four questions in the owner's order: what full marks (Met) need, what the
system has, what it misses and who acts, and where to check. The default row prints the plain
question, the grade and what it comes from, and three short lines, Needs, Has and Missing; the
three lines are the toggle of one native disclosure, which holds the four answers in full, then
why the grade is what it is, every grade of the petal, the limits no rule counts, what is not
graded here and the field's terms. Every line is worded here and in words.py from the board's
keys (`to_met`, `read_facts`, `why`, the petal's facts) and the stored records; nothing is typed
per system, and nothing here sets a state. The page does not print a petal's `reason` or scale
label: both stay on the board.
"""

import re

from . import state as S
from .chrome import CHECKS_PAGE, link, rung_of
from .overview import bits_words, name_of, proved_words
from .words import (
    CAME_FROM,
    CAUSE_WORD,
    CHECKS_LINK,
    DETAILS_WORD,
    EVIDENCE,
    FIDELITY_LINK,
    FORMAT_WORD,
    FROM_WORD,
    GLYPH_KEY,
    GLYPH_KEY_HEAD,
    GLYPH_LEAD,
    HAS_HEAD,
    HERE,
    LADDER,
    LADDER_CAP,
    LADDER_CASES,
    MET_NEEDS,
    MISSING_DECIDE,
    MISSING_GROUP,
    MISSING_HEAD,
    MISSING_NONE,
    MISSING_REPAIR,
    NEEDS_HEAD,
    NEEDS_SHORT,
    NOT_GRADED_HERE,
    OPEN_QUESTION,
    OURS_NOTHING,
    PETAL_ASK,
    PETAL_BLOCK,
    PETAL_NAME,
    PETAL_TERM,
    REACH_LABEL,
    READING_TOPIC,
    RECORD_LINK,
    RECORDS,
    SCOPE_LINK,
    STEP_WORD,
    VISIBLE_KINDS,
    VISIBLE_OTHERS,
    VISIBLE_TAG_WORD,
    WHO,
    e,
    petal_step,
    quoted,
    step_key,
)

# ------------------------------------------------------------------ shared with pages.py


def chip(state, word, form=""):
    """A state as a chip: ground ink on its state's ink, an outline when undecided or hollow; amber
    in lesser part notched (cut), a silent red an outline in the red ink (open)."""
    tok = f"{state} {form}".strip()
    return f'<span class="schip {tok}">{e(word)}</span>'


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


def open_question(words=OPEN_QUESTION):
    """ "an open question in our rules", linked to the rules."""
    return f'<a href="{e(link("rfcs/0018-level-1-ladder.md"))}">{e(words)}</a>'


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
    """The words beside the grade: "from our test", "from the publisher's words and our reading";
    "" on a Not stated or Not decided petal. How many points our reading covers is said in the
    petal's Has."""
    key = p.get("came_from")
    return f"{FROM_WORD} {CAME_FROM[key]}" if key else ""


# ------------------------------------------------------------------ the default row


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


def has_short(p, row, petals):  # noqa: PLR0911, PLR0912, PLR0915 (one clause per rule path)
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
        expr, per = f.get("expression"), per_words(f)
        run, stated = f.get("run"), f.get("stated_for")
        least = min(f.get("terms") or [0])
        q = " (q: the hash queries a cheater makes)" if f.get("q_cross") else ""
        if f.get("basis") == "conjectured":
            said = f"a conjectured limit, a chance of about 2^-{least} {per}; not a theorem"
            return said + ("; no verifier named" if not stated else f"; for {stated}")
        head = f"a proved limit, {expr} {per}{q}" if f.get("basis") == "proved" else \
            f"a limit, {expr} {per}, not said to be proved"  # fmt: skip
        if cause == "stated":
            return head
        if stated and f.get("program") not in ("proved", "stated"):
            return f"{head}, for {stated}; not for {run_named(row, petals)}"
        return head + (f", for {run_named(row, petals)}" if run else "; no verifier named")
    if pid == "weights_hidden":
        if cause == "not_stated":
            tail = (
                "; they say the verifier does not hold them"
                if f.get("verifier_gets_weights") is False
                else ""
            )
            return (f"nothing in the {count(k_docs, 'document')} we read on whether a proof hides "
                    f"the weights{tail}")  # fmt: skip
        if f.get("verifier_gets_weights") is True:
            return "the verifier is given the weights"
        if cause == "stated":
            return "the publisher states that a proof does not hide the weights"
        if step == "amber_lower":
            return "a statement that a proof hides the weights; no theorem"
        n = f.get("batch_size")
        if f.get("proof") == "configuration_run":
            return "a theorem that a proof of what we run hides the weights"
        said = "a theorem that the method hides the weights"
        if f.get("zk_unit") == "request":
            said += ", for one request per proof"
        nots = []
        if f.get("programs") != "stated":
            nots.append("the programs we run")
        if f.get("zk_unit") == "request" and n and n > 1:
            nots.append(f"our {n}-reply batches")
        return said + (f"; not for {' or '.join(nots)}" if nots else "")
    if pid == "faithful_model":
        if not f:
            return p["reason"]
        c = f["controls"]
        return (f"replies match the original's for their first {tenth(f['display'])} tokens on "
                f"average; our 4-bit copy {tenth(c['q4_k_m']['display'])}, our 8-bit copy "
                f"{tenth(c['q8_0']['display'])} (the Fidelity figure above is another measure)")  # fmt: skip
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
                return f"a {tool} theorem is named; our rebuild stopped before a verdict"
            return f"a {tool} theorem is named; we have not rebuilt it yet"
        reach = formal.get("reach")
        k = len(formal.get("limits") or [])
        lim = f"; the publisher states {k} limits the grade does not count" if k else ""
        if reach == "verifier_run":
            return f"a {tool} theorem we rebuilt, about {run}, the verifier we run{lim}"
        if reach == "protocol_and_statement":
            about = f"about {stated} and the method" if stated else "about the method"
            return f"a {tool} theorem we rebuilt, {about}; not about {run_named(row, petals)}{lim}"
        return f"a {tool} theorem we rebuilt, about part of the method{lim}"
    if pid == "no_trusted_party":
        if cause == "not_stated":
            return f"nothing in the {count(k_docs, 'document')} we read on what soundness rests on"
        if step == "green":
            return "cryptographic assumptions only and no setup secret, in the publisher's words"
        if f.get("clause") == "reading":
            return ("on our reading, cryptographic assumptions only and no setup secret; the "
                    "publisher does not say so in one sentence")  # fmt: skip
        if f.get("clause") == "ceremony":
            return "a setup secret made in an open ceremony with a public record"
        return p["reason"]
    return p["reason"]


CHECK_WORD = {"model": "Model", "prompt": "Prompt", "reply": "Reply",
              "no_weight_file": "Verify without weights", "fidelity": "Fidelity",
              "proof_build": "rebuild"}  # fmt: skip


# ------------------------------------------------------------------ the items missing for Met


def item_short(it, p, row):  # noqa: PLR0911 (one phrase per item key)
    """An item in a few words, for the default row."""
    need, f = it["need"], facts_of(p)
    run = (
        it.get("run")
        or f.get("run")
        or ((row.get("statement") or {}).get("verifiers") or {}).get("run")
    )
    if need == "text":
        return it["text"]
    if need == "program":
        return f"the limit for {run}, the verifier we run"
    if need == "zk_run":
        n = it.get("n")
        return f"the theorem for our {n}-reply batches" if it.get("unit") == "request" \
            and n and n > 1 else "the theorem for what we run"  # fmt: skip
    if need == "rebuild":
        return "our rebuild of that new theorem" if it.get("new") else "our rebuild of it"
    if need == "reach_run":
        return f"a theorem that reaches {run}, the verifier we run"
    if need == "exponent":
        return f"every part of the limit at most 2^-{it['floor']}"
    if need == "above":
        return f"an average above {tenth(it['value'])} tokens"
    if need == "one_at_a_time":
        engine = it.get("engine")
        return "our whole run one request at a time" + (f" in {engine}" if engine else "")
    return SHORT.get(need, need)


SHORT = {
    "basis": "a theorem, not a conjecture",
    "adversary": "a statement that it holds against any cheating prover",
    "unit": "a limit for a whole reply",
    "granularity": "a record of how many replies one proof covers",
    "batch": "a limit for each reply checked on its own",
    "batch_size": "a record of our batch size",
    "parameters": "a statement that the limit is for the settings we run",
    "conditions": "a record that its condition holds for our files",
    "reading": "the publisher's own words in place of our reading",
    "programs": "a statement that its programs keep the weights secret",
    "visible_list": "a published list of what stays visible",
    "fitted": "nothing on that list that depends on the weights",
    "hide_statement": "a statement that a proof keeps the weights secret",
    "zk_theorem": "a zero-knowledge theorem",
    "named_theorem": "a named computer-checked theorem",
    "whole_method": "a theorem of the whole method, the model's computation included",
    "conclusion": "a conclusion about the model",
    "axioms": "a rebuild with only the tool's standard axioms",
    "trusted_base": "a list of everything the theorem relies on",
    "input_code": "no input-reading code outside the theorem",
    "rests_sentence": "that sentence, in its own words",
    "no_setup_secret": "the publisher's statement that no setup made a secret",
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
    """An item in full, for the Missing block: what is needed, then "Today ...", and in a group
    where both act, who acts."""
    need, f = it["need"], facts_of(p)
    st = row.get("statement") or {}
    run = it.get("run") or f.get("run") or (st.get("verifiers") or {}).get("run")
    stated = f.get("stated_for") or (st.get("verifiers") or {}).get("stated")
    said = ""
    if need == "text":
        said = cap(it["text"]) + "."
    elif need == "program":
        said = f"The limit for {run}, the verifier we run. " + (
            f"Today the theorem is about {stated} only." if it.get("stated") and f.get("basis") == "proved"
            else f"Today the limit is stated for {stated} only." if it.get("stated")
            else "Today no verifier is named.")  # fmt: skip
    elif need == "basis":
        least = min(it.get("terms") or [0])
        said = (f"A theorem, not a conjecture. Today the {least} bits rest on an unproven "
                "assumption." if it.get("basis") == "conjectured" else
                "A theorem. Today the documents we read do not say whether the limit is proved.")  # fmt: skip
    elif need == "adversary":
        said = "A statement that it holds against any cheating prover. " + (
            "Today it is stated only against a weaker cheater." if it.get("adversary") == "weaker"
            else "Today the documents we read do not say.")  # fmt: skip
    elif need == "unit":
        unit = it.get("unit")
        u = (f.get("said") or {}).get("unit") or {}
        today = (f"Today it is for one {u['named']} ({u.get('described')})." if unit == "part" and u.get("named")
                 else "Today it is for one part of a proof." if unit == "part"
                 else "Today it is for one round." if unit == "round"
                 else "Today one proof covers more than one reply." if unit == "proof"
                 else "Today the documents we read do not say what it is for.")  # fmt: skip
        said = f"A limit for a whole reply. {today}"
    elif need == "granularity":
        said = "A record of how many replies one proof covers. Today none is recorded."
    elif need == "batch":
        n = it.get("n")
        if it.get("batch") == "together":
            said = (f"A limit for each reply checked on its own. We make replies in batches of {n} "
                    "and check each reply's proof alone. The publisher's limit for a batch covers "
                    f"its {n} proofs only when they are checked together ({n} times the limit for "
                    "one proof, counting the hash queries made for the whole batch). For proofs "
                    "checked one at a time it states no limit.")  # fmt: skip
        else:
            said = (f"A limit for each reply checked on its own. We make replies in batches of {n}, "
                    "and the publisher states no limit for the members of a batch.")  # fmt: skip
    elif need == "batch_size":
        said = "A record of our batch size. Today none is recorded."
    elif need == "parameters":
        said = "The publisher's statement that the limit is for the settings we run. " + (
            "Today it is stated for other settings." if it.get("parameters") == "other"
            else "Today the documents we read do not show that it is.")  # fmt: skip
    elif need == "conditions":
        head = ("A record that the theorem's condition holds for the files we run." if it.get("proved")
                else "A record that the limit's conditions hold for the files we run.")  # fmt: skip
        plain = said_of(p, "conditions_shown").get("plain")
        cond = said_of(p, "conditions_shown").get("quotes") or []
        today = plain or ("Today the documents we read name none and show none." if not cond
                          else "Today no record shows that they hold.")  # fmt: skip
        trial = trial_of(row)
        aside = ""
        if trial and stated:
            aside = (f" (Outside the grade, our trial had {stated} accept {trial['accepted']:,} of "
                     f"{count(trial['honest'], 'honest proof')} at the files we run; see "
                     f"{PETAL_NAME['machine_checked']}.)")  # fmt: skip
        said = f"{head} {today}{aside}"
    elif need == "exponent":
        floor, terms = it["floor"], it.get("terms") or []
        if f.get("basis") == "conjectured" or (len(terms) == 1 and not it.get("q")):
            today = f"Today about 2^-{terms[0]} ({terms[0]} bits)." if terms else ""
        else:
            written = [f"q × 2^-{t}" if i == 0 and it.get("q") else f"2^-{t}"
                       for i, t in enumerate(terms)]  # fmt: skip
            today = f"Today the parts are {and_list(written)}."
            if it.get("q"):
                today += (f" Our rule compares the exponents as written, {and_list(map(str, terms))}, "
                          f"with {floor}; it does not fix a number of queries q.")  # fmt: skip
        said = f"Every part of the limit at most 2^-{floor}. {today}"
    elif need == "reading":
        k = len(it["facts"])
        this = "this is" if k == 1 else "both are" if k == 2 else "all are"
        said = f"The publisher's own words {reading_topics(it['facts'])}. Today {this} our reading."
    elif need == "zk_run":
        n = it.get("n")
        said = (f"The theorem for our {n}-reply batches. Today it covers one request per proof."
                if it.get("unit") == "request" and n and n > 1
                else "That theorem for what we run.")  # fmt: skip
    elif need == "programs":
        said = "The publisher's statement that its programs keep the weights secret."
        if it.get("programs") == "expected":
            said += " Today it states an expectation, not a statement."
        elif it.get("read"):
            said += " Today we count none for the programs we run; this is our reading."
    elif need == "visible_list":
        said = ("A published list of what stays visible, with nothing on it that depends on the "
                "weights.")  # fmt: skip
    elif need == "fitted":
        k = it["k"]
        said = ("Nothing on the list of what stays visible that, by the publisher's own words, "
                f"depends on the weights. Today {count(k, 'item')} {'does' if k == 1 else 'do'}.")  # fmt: skip
    elif need == "hide_statement":
        said = "A statement that a proof keeps the weights secret from whoever checks it."
    elif need == "zk_theorem":
        said = "A zero-knowledge theorem for it, at least for the method."
    elif need == "above":
        fd = f
        t = fd[it["key"]]
        a, b = (fd["controls"][c] for c in t["controls"])
        names = {"upper": ("our 8-bit copy", "our 4-bit copy"),
                 "green": ("the original run a second time", "our 8-bit copy")}[it["key"]]  # fmt: skip
        said = (f"An average shown above {tenth(t['display'])} tokens, halfway between {names[0]} "
                f"({tenth(a['display'])}) and {names[1]} ({tenth(b['display'])}). Today "
                f"{tenth(fd['display'])}.")  # fmt: skip
        if it is first_above(p):
            said += (f" The number format of the copy {name_of(row)} proves is the publisher's "
                     "choice, so this item is the publisher's.")  # fmt: skip
    elif need == "one_at_a_time":
        fid = rung_of(row).get("fidelity") or {}
        engine = it.get("engine")
        said = ("Our whole fidelity run on this model sending one request at a time"
                + (f" in {engine}, as our rule asks" if engine else "") + ". Today "
                + runs_words(fid) + ".")  # fmt: skip
        if it.get("vllm"):
            said += (f" The original runs in vLLM because {engine or 'llama.cpp'} at the version "
                     "our level pins cannot run this model's 16-bit file, and our rule counts no "
                     "vLLM part as one at a time. The second run sends the prompts in reverse "
                     "order, so they are batched differently, and on some prompts the two runs "
                     f"differ: it scores {tenth(f['controls'][f['rerun']]['display'])}, not "
                     f"{S.V['request']['output_tokens'] if isinstance(S.V.get('request'), dict) else 512}. "
                     f"The {tenth(f['green']['display'])} threshold is computed from that score.")  # fmt: skip
    elif need == "named_theorem":
        said = ("A named theorem, checked by a proof-checking program such as Lean, that at least "
                "part of the method refuses fake replies, with the program's version pinned.")  # fmt: skip
    elif need == "rebuild":
        said = "Our rebuild of that new theorem." if it.get("new") else \
            "Our rebuild of it (and of any later theorem)."  # fmt: skip
    elif need == "whole_method":
        said = ("The theorem covering the whole method, the model's computation included, its "
                "conclusion about the model, with only the tool's standard axioms.")  # fmt: skip
    elif need == "conclusion":
        said = "A conclusion about the model (a written-out definition of what it computes)."
    elif need == "axioms":
        said = "A rebuild that reports only the tool's standard axioms."
    elif need == "reach_run":
        formal = p.get("formal") or {}
        said = (f"A theorem that reaches {run}, the verifier we run, from the bytes it reads to "
                "its verdict, with everything it relies on listed and no input-reading code "
                "outside it.")  # fmt: skip
        if formal.get("reach") in ("protocol_and_statement", "protocol", "part") and stated:
            said += f" Today it stops at {stated}"
            said += (", and input-reading code sits outside it." if formal.get("input_code_unverified")
                     is True else ".")  # fmt: skip
    elif need == "trusted_base":
        said = "A list of everything the theorem relies on. Today none is listed."
    elif need == "input_code":
        said = "No input-reading code outside the theorem. Today some sits outside it."
    elif need == "rests_sentence":
        said = ("The publisher's own sentence that soundness rests on cryptographic assumptions "
                "only and no setup produced a secret. Today this is our reading.")  # fmt: skip
    elif need == "no_setup_secret":
        said = ("The publisher's statement that no setup produced a secret. Today a setup made "
                "one, in an open ceremony.")  # fmt: skip
    else:
        said = cap(need) + "."
    if mixed:
        said += f" {cap(WHO[it['by']])}."
    return said


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
    return "; ".join(parts) if parts else "no slot count is recorded"


def who_words(items):
    n = len(items)
    pub = sum(1 for it in items if it["by"] == "publisher")
    us = n - pub
    if not us:
        return "both for the publisher" if n == 2 else "all for the publisher"
    if not pub:
        return "both for us" if n == 2 else "all for us"
    return f"{pub} for the publisher and {us} for us"


def missing_line(p, row):
    """The default row's Missing line: the count of items, who acts, how many each step needs,
    the first item, and ours where both act; Fidelity names every item."""
    groups = p["to_met"]
    if not groups:
        return MISSING_NONE
    kind = groups[0]["kind"]
    items = [it for g in groups for it in g["items"]]
    if kind == "decide":
        return MISSING_DECIDE.format(need=item_short(items[0], p, row))
    if kind == "repair":
        return MISSING_REPAIR.format(need=item_short(items[0], p, row))
    n = len(items)
    if n == 1:
        return f"1 item, {WHO[items[0]['by']]}: {item_short(items[0], p, row)}."
    head = f"{count(n, 'item')}, {who_words(items)}"
    if p["id"] == "faithful_model" and all(
        it["need"] in ("above", "one_at_a_time") for it in items
    ):
        steps, first = [], True
        for g in groups:
            said = []
            for it in g["items"]:
                words = item_short(it, p, row)
                words = words if first else words.replace("an average above", "above")
                first = False
                said.append(words)
            steps.append(f"for {STEP_WORD[g['to']]}, {and_list(said)}")
        return f"{head}. {cap('; '.join(steps))}."
    ladder = ""
    if len(groups) > 1:
        ladder = ": " + ", then ".join(
            f"{len(g['items'])} for {STEP_WORD[g['to']]}" for g in groups
        )
    said = f"{head}{ladder}. First: {item_short(items[0], p, row)}."
    ours = [it for it in items if it["by"] == "us"]
    if ours and len(ours) < n:
        said += f" Ours: {item_short(ours[0], p, row)}."
    return said


def missing_html(p, row, petals):
    """The Missing block: the groups of `to_met`, numbered across groups, each item in full."""
    groups = p["to_met"]
    if not groups:
        return p_("Nothing: this property is Met.")
    out, k = [], 0
    for gi, g in enumerate(groups):
        bys = {it["by"] for it in g["items"]}
        mixed = len(bys) > 1
        if g["kind"] in ("decide", "repair"):
            head = MISSING_GROUP[g["kind"]]
        else:
            head = MISSING_GROUP["first" if gi == 0 else "then"].format(to=STEP_WORD[g["to"]])
        if not mixed:
            head += f", {WHO[bys.pop()]}"
        lis = []
        for it in g["items"]:
            k += 1
            lis.append(f'<li value="{k}">{quoted(item_long(it, p, row, petals, mixed))}</li>')
        out.append(f'<p class="pgh">{e(head)}:</p><ol class="pmi">{"".join(lis)}</ol>')
    if p["id"] == "faithful_model" and facts_of(p).get("slots") == 1:
        out.append(p_(e(OURS_NOTHING)))
    return "".join(out)


# ------------------------------------------------------------------ Has, in full


def trial_of(row):
    """The stored trial of another of the publisher's verifiers (TR-1), printed under Formally
    verified; None where none is stored."""
    return next((t for t in row.get("trials_kept") or () if t["place"] == "machine_checked"), None)


def used_facts(p):
    return [f for f in p["read_facts"] if f.get("used", True)]


def reading_html(p, skip=()):
    """ "Our reading, on two points the grade uses. (1) ... (2) ...", each note's plain words; a
    fact only Met reads is named under Missing, not here."""
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
        said = (f"The publisher proves{by} a limit on the chance that a fake reply passes: at most "
                f"{expr} {per}.")  # fmt: skip
        q = f.get("q_cross")
        if q:
            k = len(f["terms"]) - 1
            said += (" Here q is the number of hash queries a cheater makes: how many times it "
                     "runs the hash function while searching for a proof that passes. The other "
                     f"{'part is' if k == 1 else 'parts are'} fixed; the first grows with q. It "
                     f"reaches 2^-100 at 2^{q[0]} queries and 2^-80 at 2^{q[1]} queries.")  # fmt: skip
        batch = next((i for i, it in enumerate(items_of(p), 1) if it["need"] == "batch"), None)
        if f.get("unit") == "proof" and f.get("one_reply") and batch:
            said += (f" Each reply has its own proof, and we make replies in batches of "
                     f"{f['batch_size']} (item {batch} below).")  # fmt: skip
        out.append(p_(e(said)))
    elif f.get("basis") == "conjectured":
        thing = unit_said.get("named") or "proof"
        said = (f"The publisher states {least} conjectured bits of security {per_words(f, True)}"
                f"{' of a proof' if unit_said.get('named') else ''}: a chance of about 2^-{least} "
                f"that a fake {thing} passes.")  # fmt: skip
        b = (f.get("said") or {}).get("basis") or {}
        if b.get("named"):
            said += (f" The figure comes from the accounting of {b['named']}, "
                     f"{b.get('described') or 'as the publisher states'}.")  # fmt: skip
        said += " Conjectured: it rests on an unproven assumption, not a theorem."
        out.append(p_(e(said)))
    else:
        out.append(p_(e(f"The publisher states a limit, {expr} {per}, and does not say whether it "
                        "is proved.")))  # fmt: skip
    if f.get("unit") == "part" and unit_said.get("named"):
        q = (unit_said.get("quotes") or [None])[0]
        quote = f" ({q_html(q)})" if q else ""
        out.append(p_(f"One {e(unit_said['named'])} proves {e(unit_said.get('described') or 'part of a reply')}"
                      f"{quote}. A reply passes through every layer of the model, and the publisher "
                      "states no limit for a whole reply."))  # fmt: skip
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
            said += e(f" The publisher states that {run} is tested, not proved, and claims no "
                      "limit for it.")  # fmt: skip
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
        runs = f", which runs the publisher's check, {e(check)}, as the publisher states ({q_html(rq)})" \
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
        said = f"{step}: the limit is not shown to cover what we run ({items} under Missing)."
        if w["floor"] == 80:
            exps = and_list(str(t) for t in w["exps"])
            said += (f" For a theorem, Partly met needs every part at most 2^-80, and the exponents "
                     f"as written, {exps}, pass.")  # fmt: skip
            if w.get("q"):
                said += " Our rule does not fix a number of queries q."
        else:
            least = w["least"]
            said += (" For a limit that is not a theorem, Partly met needs every part at most "
                     f"2^-100, and {least} bits {'is exactly that' if least == 100 else 'passes'}.")  # fmt: skip
            if w.get("unit_item"):
                named = ((facts_of(p).get("said") or {}).get("unit") or {}).get("named") or "part"
                said += (f" Our rule reads the figure per {named}, as stated. That it is per "
                         f"{named}, not per reply, is item {w['unit_item']}: it keeps the grade "
                         "below Mostly met, and our rule does not lower it further.")  # fmt: skip
        return p_(e(said), "pwy")
    if p["id"] == "weights_hidden":
        n = w["n"]
        return p_(e(f"{step}: there is a zero-knowledge theorem, at least for the method, which "
                    f"is what {step} needs. The {count(n, 'item')} under Missing "
                    f"{'is' if n == 1 else 'are'} what Met adds."), "pwy")  # fmt: skip
    if p["id"] == "machine_checked":
        run = w.get("run")
        read = ", on our reading of the reach and the conclusion" if w.get("read") else ""
        stop = (f"It stops below Met because it does not reach {run}." if not w.get("gaps")
                else "It stops below Met because of the gaps listed under Missing.")  # fmt: skip
        said = (f"{step}. Our rules grade five things here: how far the theorem reaches, what "
                "its conclusion is about, whether input-reading code sits outside it, its axioms, "
                f"and our rebuild. On those it reaches {step}{read}. {stop}")  # fmt: skip
        uf = petals.get("unforgeable") or {}
        uf_first = (uf.get("to_met") or [{}])[0].get("items") or []
        if run and any(it["need"] == "program" for it in uf_first):
            said += (f" Integrity asks for a limit for {run} from Mostly met up; this property asks "
                     f"for a theorem reaching {run} only at Met. That is why the same gap leaves "
                     f"Integrity at {STEP_WORD[step_key(uf['step'], uf['cause'])]} and this "
                     f"property at {step}.")  # fmt: skip
        return p_(e(said), "pwy")
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
            html += " They do state that the verifier does not hold the weights" + \
                (f" ({q_html(vq)})" if vq else "") + \
                ". Not holding the weights is not the same as a proof hiding them."  # fmt: skip
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
        said = (f"The publisher proves{in_tool} a zero-knowledge theorem: everything a verifier "
                "sees could have been produced without the weights.")  # fmt: skip
        kind, model = f.get("zk_kind"), f.get("zk_model")
        if kind == "statistical":
            said += (" It is statistical: the two can differ only by a tiny amount the publisher "
                     "bounds (its figures are under the field's terms below)")  # fmt: skip
            said += (", and it treats the hash function as perfectly random (the random-oracle "
                     "model)." if model == "random_oracle" else ".")  # fmt: skip
        elif kind:
            said += f" It is {kind}."
        n = f.get("batch_size")
        if f.get("proof") == "protocol":
            said += (" The theorem is about the method, the protocol as the publisher defines it"
                     + (in_tool or "") + ", not about the programs we run")  # fmt: skip
            said += ", and for one request per proof." if f.get("zk_unit") == "request" else "."
            if f.get("zk_unit") == "request" and n and n > 1:
                said += f" We run batches of {n} replies, which it does not cover."
        else:
            said += " It covers what we run."
        out.append(p_(e(said)))
    elif p["step"] == "amber_lower":
        out.append(p_(e("The publisher states that a proof hides the weights, and proves no "
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
                    f"{tenth(f['display'])} tokens, up to the first difference{most}.")))  # fmt: skip
    rerun = c[f["rerun"]]["display"] if f.get("rerun") in c else None
    every = (
        f" (every token: {tokens} is the most a reply has)"
        if rerun is not None and tokens and rerun == tokens
        else ""
    )
    bar = f.get("bar") or {}
    m = re.match(r"q(\d)", str(bar.get("control") or ""))
    bar_bits = f" ({m.group(1)}-bit)" if m else ""
    scale = []
    if rerun is not None:
        scale.append(f"the original model run a second time, {tenth(rerun)}{every}")
    scale += [
        f"our 8-bit copy, {tenth(c['q8_0']['display'])}",
        f"our 4-bit copy, {tenth(c['q4_k_m']['display'])}",
    ]
    if bar.get("display") is not None:
        scale.append(f"and a copy we damaged on purpose{bar_bits}, {tenth(bar['display'])}, the "
                     "bar every system must beat")  # fmt: skip
    out.append(p_(e("For scale, the same score on the same prompts: " + "; ".join(scale) + ".")))
    out.append(p_(e(proved_sentence(row, f))))
    if f.get("slots") == 1:
        out.append(p_(e("Our run sent one request at a time, as Met needs.")))
    out.append(p_(e("The Fidelity figure under Figures at the top of this page is a different "
                    "measure, top-token agreement in percent; it sets no grade.")))  # fmt: skip
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
        said = (f"{name} proves a copy with {bits_words(bits)}-bit {wword} weights for part of its "
                "weights, as the publisher states; the publisher states no width for the rest.")  # fmt: skip
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
    said = (f"The publisher proves in {tool}, a program that checks every step of a proof, a "
            f"theorem that {who} refuses fake replies, up to the chance limit under "
            f"{PETAL_NAME['unforgeable']}.")  # fmt: skip
    noted = {f["fact"] for f in used_facts(p)}
    if formal.get("reach") == "protocol_and_statement":
        said += " The theorem's statement includes the model's computation" + (
            " (our reading, below)." if "reach" in noted else ".")  # fmt: skip
    out.append(p_(e(said)))
    build = formal.get("build") or {}
    if build:
        version = str(build["toolchain"]["version"]).lstrip("v")
        if build.get("status") == "built" and build.get("exit_code") == 0:
            axioms = build.get("axioms") or []
            said = (f"We rebuilt it at the version we ran ({pin7(row)}) with the {tool} version the "
                    f"publisher pins, {version}. It checked: exit code 0 after "
                    f"{secs(build['seconds'])} ({hours(build['seconds'])}).")  # fmt: skip
            if axioms and p["step"] in ("amber_upper", "green"):
                said += (f" It uses only {tool}'s {number(len(axioms))} standard axioms, the basic "
                         f"assumptions any {tool} proof may use, so no step is skipped.")  # fmt: skip
            if formal.get("limits"):
                said += f" {tool} itself is trusted; see the limits below."
        elif build.get("status") == "stopped":
            said = (
                f"Our rebuild at {pin7(row)} stopped before a verdict ({secs(build['seconds'])})."
            )
        else:
            said = f"Our rebuild at {pin7(row)} failed (exit code {build.get('exit_code')})."
        out.append(p_(e(said)))
    elif p["cause"] == "proof_build_not_run":
        out.append(p_(e("We have not rebuilt it yet.")))
    if formal.get("reach") != "verifier_run" and run:
        tested = (formal.get("scope_card") or {}).get("soundness", {}).get("verifier_run", {}).get(
            "value"
        ) == "tested"
        said = e(
            f"It does not reach {run_named(row, petals)}"
            + ("; the publisher states that one is tested, not proved" if tested else "")
            + "."
        )
        if formal.get("input_code_unverified") is True:
            qs = ((formal.get("said") or {}).get("input_code_unverified") or {}).get("quotes") or []
            said += " Input-reading code sits outside it" + (
                f": {q_html(qs[0])}, as the publisher states." if qs else "."
            )
        out.append(p_(said))
    if formal.get("theorem"):
        out.append(p_(e(f"No review of the theorem's statement by an outside {tool} expert is "
                        "recorded.")))  # fmt: skip
    out.append(reading_html(p))
    return out


def limits_html(p):
    """Formally verified: the limits the publisher states that no rule reads, each in plain words
    and then its own, linked. They set nothing."""
    lim = (p.get("formal") or {}).get("limits") or []
    if not lim:
        return ""
    lis = "".join(f"<li>{quoted(i['plain'])} ({q_html(i['quotes'][0])} ↗)</li>" for i in lim)
    lead = p_(e("None of these limits is among the five things our rules grade (see Why this "
                "grade), so they do not lower the grade. A related question is ")
              + open_question("open in our rules")
              + e(": whether a grade above Partly met should need a record that the verifier "
                  "accepts honest proofs at our files. Each item is our plain summary, then the "
                  "publisher's words, linked."))  # fmt: skip
    return block("limits", lead + f'<ul class="pls">{lis}</ul>')


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
        out.append(p_(e("So, on our reading: soundness rests on cryptographic assumptions only, "
                        "and no setup step produced a secret. The publisher does not say this in "
                        "one sentence.")))  # fmt: skip
    else:
        out.append(p_(e(cap(has_short(p, row, petals)) + ".")))
    return out


HAS = {"unforgeable": has_unforgeable, "weights_hidden": has_weights_hidden,
       "faithful_model": has_faithful, "machine_checked": has_machine_checked,
       "no_trusted_party": has_trust}  # fmt: skip


# ------------------------------------------------------------------ how it is graded


def ladder_html(p, row):
    """The petal's grades, best first, the system's line (or its case, on Trust's Mostly met)
    marked "<System> is here." A line that does not apply to this system is not printed."""
    here = f' <span class="phere">{e(HERE.format(system=name_of(row)))}</span>'
    key = step_key(p["step"], p["cause"])
    clause = facts_of(p).get("clause") or "reading"
    out = []
    for k, words, _ in LADDER[p["id"]]:
        if p["id"] == "no_trusted_party" and k == "amber_upper":
            cases = "".join(
                p_(e(LADDER_CASES[c]) + (here if key == k and c == clause else ""))
                for c in ("reading", "ceremony")
            )
            out.append(p_(e(words)) + f'<div class="plc">{cases}</div>')
            continue
        line = e(words) + (here if k == key else "")
        out.append(p_(line, "pme" if k == key else ""))
        if (
            p["id"] == "faithful_model"
            and facts_of(p).get("policy_cap")
            and k == key == "amber_lower"
        ):
            out.append(p_(e(LADDER_CAP.format(system=name_of(row)))))
    return "".join(out)


# ------------------------------------------------------------------ Evidence and the field's terms


def headless(html):
    """A block without its own head, where the summary over it already says it."""
    return re.sub(r'^<p class="pvh">.*?</p>', "", html, count=1)


def details_list(head, body):
    return f'<details class="pev"><summary>{e(head)}</summary>{body}</details>'


def evidence_html(p, row, petals):  # noqa: PLR0912, PLR0915 (one line per record kind)
    out = []
    pid = p["id"]
    if p["quotes"]:
        out.append(details_list(EVIDENCE["quotes"].format(pin=pin7(row), n=count(len(p["quotes"]), "quote")),
                                quote_links(p["quotes"])))  # fmt: skip
    if p["sources"] and p["cause"] == "not_stated":
        docs = ", ".join(f'<a href="{e(d["url"])}">{e(d["path"])}</a>' for d in p["sources"])
        out.append(p_(f"{e(EVIDENCE['docs'].format(n=len(p['sources'])))}: {docs}", "pel"))
    if pid == "weights_hidden" and p.get("forms"):
        out.append(details_list(EVIDENCE["forms"].format(n=count(len(p["forms"]), "sentence")),
                                headless(forms_html(p["forms"]))))  # fmt: skip
    if pid == "weights_hidden" and p.get("visible"):
        k = sum(1 for v in p["visible"] if v["tag"] == FITTED)
        n = f"{'at least ' if p.get('visible_at_least') else ''}{len(p['visible'])}"
        n += f", {k} that {VISIBLE_TAG_WORD[FITTED].replace('depends', 'depend')}" if k else ""
        out.append(details_list(EVIDENCE["visible"].format(n=n),
                                headless(visible_html(p["visible"], p.get("visible_at_least")))))  # fmt: skip
    if p["read_facts"]:
        k = len(p["read_facts"])
        body = "".join(p_(e(f["note"]), "cn") for f in p["read_facts"])
        out.append(details_list(EVIDENCE["notes"].format(n=count(k, "note")), body))
        unused = [f for f in p["read_facts"] if not f.get("used", True)]
        if unused:
            topics = and_list(READING_TOPIC.get(f["fact"], ("", f["fact"]))[1] for f in unused)
            why = ""
            if pid == "unforgeable" and facts_of(p).get("basis") != "proved":
                why = " (a limit that is not a theorem stays at Partly met at most, whatever its settings)"
            out.append(p_(e(EVIDENCE["not_used"].format(
                this=f"our reading that the limit {topics}" if pid == "unforgeable"
                else f"our reading on {topics}", its="its" if len(unused) == 1 else "their",
                why=why)), "pel"))  # fmt: skip
    checks = f'<a href="#checks">{e(CHECKS_LINK)}</a>'
    rec = e(EVIDENCE["records"])
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
            out.append(
                p_(f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))}', "pel")
            )
        else:
            state = ("Each was refused on this run;" if all(s == "held" for s in states)
                     else "Not every one was refused on this run;")  # fmt: skip
            out.append(p_(f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))} '
                          f"{checks}", "pel"))  # fmt: skip
    elif pid == "weights_hidden":
        s = check_state(row, "no_weight_file")
        state = {"held": "It passed on this run.", "failed": "It failed on this run."}.get(
            s, "It is not decided on this run."
        )
        out.append(p_(f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))} '
                      f"{checks}", "pel"))  # fmt: skip
    elif pid == "faithful_model":
        rung = rung_of(row)
        fid = rung.get("fidelity") or {}
        f = facts_of(p)
        n = f.get("n")
        said = (f"our fidelity run on {rung['model']}" + (f", {n:,} prompts" if n else "")
                + ", each reply scored against the original's.")  # fmt: skip
        recl = f' <a href="{e(link(fid["path"]))}">{e(RECORD_LINK)}</a>' if fid.get("path") else ""
        out.append(p_(f'<span class="k">{rec}</span> {e(said)}{recl} '
                      f'<a href="#fidelity">{e(FIDELITY_LINK)}</a>', "pel"))  # fmt: skip
    else:
        out.append(p_(f'<span class="k">{rec}</span> {e(RECORDS[pid])}', "pel"))
    return "".join(out)


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
        said += (f" As a check that it can refuse, we also gave it {what}; "
                 + ("it refused it." if refused and t["changed"] == 1 else
                    f"it refused {t['changed_rejected']:,} of {t['changed']:,}."))  # fmt: skip
    if t.get("seconds_min") is not None:
        lo, hi = f"{t['seconds_min']:,.0f}", f"{t['seconds_max']:,.0f}"
        span = lo if lo == hi else f"{lo} to {hi}"
        said += f" {span}\u00a0s per proof (n\u00a0=\u00a0{n - t.get('no_verdict', 0):,})."
    return e(said) + e(" This trial sets no grade; whether it should is ") + open_question() + "."


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
            out.append(f"The rule reads the written exponents and fixes no q. The first term is "
                       f"2^-100 at q = 2^{q[0]} and 2^-80 at q = 2^{q[1]}.")  # fmt: skip
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
        out.append(f"Batch: {yes_no(f.get('batch'))}; ours is {count(n, 'reply', 'replies') if n else 'not recorded'}"
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
        out.append(f"Paired sign-flip test per prompt{method}, "
                   f"alpha {alpha}: above T_upper (the Mostly met threshold) {tenth(u['display'])} "
                   f"{'shown' if u['shown'] else 'not shown'}; above T_green (the Met threshold) "
                   f"{tenth(g['display'])} {'shown' if g['shown'] else 'not shown'}.")  # fmt: skip
        out.append("Thresholds are computed from unrounded means.")
        pw = proved_words(row, long=True)
        if pw:
            out.append(cap(pw) + ".")
        if f.get("policy_cap"):
            out.append(
                "Decoding: accepts tokens other than the model's top choice, so Partly met at most."
            )
        else:
            out.append("Decoding: exact match (only the model's top token), so the Partly met cap "
                       "for looser decoding rules does not apply.")  # fmt: skip
        fid = rung_of(row).get("fidelity") or {}
        slots = []
        for run in fid.get("runs") or ():
            who = "the copies" if run.get("part") else "the original and its rerun"
            slots.append(f"no count for {who} (vLLM, one call)" if run.get("engine") == "vllm"
                         else f"{run.get('slots')} for {who} ({run.get('engine')})")  # fmt: skip
        out.append(f"Requests at a time (slots): {'; '.join(slots) or yes_no(None)}.")
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
        out.append(("raw", "Not graded: which model a commitment names, " + open_question() + "."))
    html = " ".join(o[1] if isinstance(o, tuple) else e(o) for o in out)
    return details_list(PETAL_BLOCK["terms"], p_(html, "ptm"))


# ------------------------------------------------------------------ the petal


def not_graded_html(p, row):
    if p["id"] not in NOT_GRADED_HERE:
        return ""
    arch = ""
    if p["id"] == "weights_hidden":
        st = row.get("statement") or {}
        fact = st.get("architecture_visible")
        arch = f" ({fact}, as the publisher states)" if fact else ""
    said = e(NOT_GRADED_HERE[p["id"]].format(arch=arch, q="\x00")).replace("\x00", open_question())
    return block("not_graded", p_(said))


def block(key, body):
    return f'<div class="pbk"><h5 class="pbh">{e(PETAL_BLOCK[key])}</h5>{body}</div>'


def petal_body(p, row, petals):
    """The petal opened: the owner's four answers (Met needs, Has, Missing, Evidence), then why
    the grade is what it is, the limits no rule counts, every grade of the petal, what is not
    graded here, and the field's terms."""
    tokens = (
        S.V.get("request", {}).get("output_tokens", 512)
        if isinstance(S.V.get("request"), dict)
        else 512
    )
    needs = MET_NEEDS[p["id"]].format(tokens=tokens, alpha="0.05")
    has = "".join(HAS[p["id"]](p, row, petals))
    why = why_html(p, row, petals)
    how = details_list(PETAL_BLOCK["how"], ladder_html(p, row))
    return (block("needs", p_(e(needs))) + block("has", has)
            + block("missing", missing_html(p, row, petals))
            + block("evidence", evidence_html(p, row, petals))
            + (block("why", why) if why else "") + limits_html(p)
            + not_graded_html(p, row) + f'<div class="pmore">{how}{terms_html(p, row, petals)}</div>')  # fmt: skip


def petal_row(i, p, row, petals):
    """One petal's row: its name with its plain question; its grade and what it comes from; the
    three short lines (Needs, Has, Missing), which open the petal's one disclosure."""
    tok = f"{p['state']} {p['form']}".strip()
    data = f' data-step="{e(p["step"] or "none")}"'
    state = chip(p["state"], petal_step(p), p["form"])
    if p["cause"] is not None:
        data += f' data-cause="{e(p["cause"])}"'
        state = (f'<a class="cc" href="{CHECKS_PAGE}#cause-{e(p["cause"])}" '
                 f'title="{e(CAUSE_WORD[p["cause"]])}">{state}</a>')  # fmt: skip
    src = came_from(p)
    src = f'<span class="pfr">{e(src)}</span>' if src else ""

    def line(cls, head, words):
        return (f'<span class="pln {cls}"><span class="k">{e(head)}</span> '
                f'<span class="pv">{nobreak(e(words), row)}</span></span>')  # fmt: skip

    has = has_short(p, row, petals)
    lines = (line("pnd", NEEDS_HEAD, cap(needs_short(p)) + ".")
             + line("phs", HAS_HEAD, cap(has) + ".")
             + line("pms", MISSING_HEAD, cap(missing_line(p, row))))  # fmt: skip
    owner = f'<span class="sr">, {e(PETAL_NAME[p["id"]])}</span>'
    details = (f'<details class="more pdt"><summary>{lines}<span class="pdl">{e(DETAILS_WORD)}'
               f'{owner}</span></summary>'
               f'<div class="pbd">{nobreak(petal_body(p, row, petals), row)}</div></details>')  # fmt: skip
    ask = PETAL_ASK[p["id"]]
    return (f'<tr class="pt {tok}" id="petal-{e(p["id"])}"><th scope="row">'
            f'<a class="sl s{i + 1} {tok}"{data} href="{CHECKS_PAGE}#{p["id"]}" data-k="p{i + 1}" '
            f'title="{e(PETAL_TERM[p["id"]])}"><span>{e(PETAL_NAME[p["id"]])}</span></a>'
            f'<span class="pst">{e(ask)}</span></th>'
            f'<td class="cst">{state}{src}</td>'
            f'<td class="prs">{details}</td></tr>')  # fmt: skip


def nobreak(html, row):
    """A verifier's name never breaks across lines ("boundary-grid --verify"): it is wrapped in a
    span that CSS keeps whole, its characters unchanged, so a copied command still runs. Only in
    text, never inside a tag or an attribute."""
    names = sorted({n for n in ((row.get("statement") or {}).get("verifiers") or {}).values()
                    if n and "-" in n}, key=len, reverse=True)  # fmt: skip
    if not names:
        return html
    pat = re.compile("|".join(re.escape(e(n)) for n in names))
    parts = re.split(r"(<[^>]*>)", html)
    return "".join(pt if pt.startswith("<") else pat.sub(lambda m: f'<span class="nw">{m.group(0)}</span>', pt)
                   for pt in parts)  # fmt: skip


def glyph_section(row, scope_head):
    """The Glyph section: its one-line lead with the grades and words behind one disclosure, the
    five petals, then soundness, zero knowledge and completeness with the stated security and the
    scope card (`scope_head`)."""
    petals = {p["id"]: p for p in row["glyph"]}
    key = "".join(p_(e(w)) for w in GLYPH_KEY)
    lead = (p_(e(GLYPH_LEAD.format(system=name_of(row))), "glead")
            + f'<details class="more gkey"><summary>{e(GLYPH_KEY_HEAD)}</summary>'
            f'<div class="gwords">{key}</div></details>')  # fmt: skip
    trs = "".join(petal_row(i, p, row, petals) for i, p in enumerate(row["glyph"]))
    return (f'<div class="glede">{lead}</div>'
            '<div class="checks"><table class="rt ckt gbig gpl"><caption class="sr">Petal, grade, '
            f'what full marks need, what it has and what it misses</caption><tbody>{trs}</tbody>'
            f'</table></div><div id="scope">{scope_head}</div>')  # fmt: skip
