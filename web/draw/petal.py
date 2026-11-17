"""A petal on a system page (RFC-0018 SI-3, GL-11, amended 2026-11-17, owner decision).

Each petal answers four questions under fixed labels: what Met needs, what the system has, what
it misses for Met and who acts, and where to check. The default row prints the plain question,
the grade and what it comes from, one Has line and one Missing line; one native disclosure holds
the rest: Met needs, Has (with a Why line where the grade surprised readers), how it is graded
with the system's step marked, Missing, what is not graded here, Evidence and the field's terms.
Every line is worded here and in words.py from the board's keys (`to_met`, `read_facts`, `why`,
the petal's facts) and the stored records; nothing is typed per system, and nothing here sets a
state. The page no longer prints a petal's `reason` or scale label: both stay on the board.
"""

import re

from . import state as S
from .chrome import CHECKS_PAGE, link, rung_of
from .overview import bits_words, name_of, proved_words
from .words import (
    CAME_FROM,
    CAUSE_WORD,
    CHECKS_LINK,
    EVIDENCE,
    FIDELITY_LINK,
    FORMAT_WORD,
    FROM_WORD,
    GLYPH_LEAD,
    HAS_HEAD,
    HERE,
    LADDER,
    LADDER_CAP,
    LADDER_CASES,
    LADDER_OR,
    LIMITS_LINE,
    MET_NEEDS,
    MISSING_DECIDE,
    MISSING_GROUP,
    MISSING_HEAD,
    MISSING_NONE,
    MISSING_REPAIR,
    NOT_GRADED_HERE,
    OURS_NOTHING,
    PETAL_ASK,
    PETAL_BLOCK,
    PETAL_NAME,
    PETAL_TERM,
    REACH_LABEL,
    READING_ON,
    READING_TOPIC,
    RECORD_LINK,
    RECORDS,
    SCOPE_LINK,
    STEP_WORD,
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


def quote_links(quotes):
    return "".join(f'<a class="qt" href="{e(q["url"])}">\u201c{quoted(unmarked(q["text"]))}\u201d</a>'
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
    """Weights hidden: what the publisher lists as visible to a proof's reader, each item linked
    to its quote, in two groups: those fitted to the weights (the only kind that sets the step,
    WH-5, WH-6), then the others, each with its kind. The second group's head says "others", not
    "not fitted": an item is untagged when its quote does not say it is fitted, which does not
    show that it is not (AGENTS.md rule 9)."""
    if not visible:
        return ""

    def items(vs, tagged):
        return "".join(f'<li><a href="{e(v["quotes"][0]["url"])}">{e(v["item"])}</a>'
                       + (f' <span class="vt">{e(VISIBLE_TAG_WORD[v["tag"]])}</span>' if tagged
                          else "") + "</li>" for v in vs)  # fmt: skip

    fitted = [v for v in visible if v["tag"] == FITTED]
    other = [v for v in visible if v["tag"] != FITTED]
    groups = ((f"{len(fitted):,} {VISIBLE_TAG_WORD[FITTED]}", fitted, False),
              (f"{len(other):,} {VISIBLE_OTHERS}" if fitted else "", other, True))  # fmt: skip
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


def points(k):
    return count(k, "point").replace(" ", "\u00a0")


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


def q_html(q, words=None):
    """One quote of the publisher's, inline, its marks of syntax left out, linked at the pin."""
    text = e(words) if words is not None else f"“{quoted(unmarked(q['text']))}”"
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


# ------------------------------------------------------------------ what the step comes from


def came_from(p):
    """The words beside the grade: "from our test", "from the publisher's words and our reading
    (2 points)"; "" on a Not stated or Not decided petal."""
    key = p.get("came_from")
    if not key:
        return ""
    return f"{FROM_WORD} {CAME_FROM[key].format(k=points(len(p['read_facts'])))}"


# ------------------------------------------------------------------ Has, short (the default row)


def per_words(f, short=False):
    """What one limit is stated per: "per proof", "per segment, one transformer layer"."""
    unit = f.get("unit")
    named = (f.get("said") or {}).get("unit") or {}
    if unit == "part" and named.get("named"):
        d = named.get("described")
        return f"per {named['named']}" + (f", {d}" if d and not short else "")
    return {"proof": "per proof", "reply": "per reply", "part": "per part of a proof",
            "round": "per round"}.get(unit, "")  # fmt: skip


def has_short(p, row, petals):  # noqa: PLR0911, PLR0912, PLR0915 (one clause per rule path)
    """One clause, in the system's own numbers and names: what it has today."""
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
        if f.get("basis") == "conjectured":
            said = f"a conjectured {least} bits (a chance of about 2^-{least}) {per}; not a theorem"
            return said + ("; no verifier named" if not stated else f"; for {stated}")
        head = f"a proved limit, {expr} {per}" if f.get("basis") == "proved" else \
            f"a limit, {expr} {per}, not said to be proved"  # fmt: skip
        if cause == "stated":
            return head + "; " + p["reason"].split("; ")[0]
        if stated and f.get("program") not in ("proved", "stated"):
            return f"{head}, for {stated}; it does not cover {run}, which we run"
        return head + (f", for {run}, the verifier we run" if run else "; no verifier named")
    if pid == "weights_hidden":
        if cause == "not_stated":
            tail = (
                "; the verifier does not hold them"
                if f.get("verifier_gets_weights") is False
                else ""
            )
            return f"nothing in the {count(k_docs, 'document')} we read on whether a proof hides the weights{tail}"
        if f.get("verifier_gets_weights") is True:
            return "the verifier is given the weights"
        if cause == "stated":
            return "the publisher states that a proof does not hide the weights"
        if step == "amber_lower":
            return "a statement that a proof hides the weights; no theorem"
        n = f.get("batch_size")
        said = "a theorem that a proof hides the weights"
        if f.get("proof") == "configuration_run":
            return said + ", for what we run"
        if f.get("zk_unit") == "request":
            said += ", for one request per proof"
            if n and n > 1:
                said += f", not the {n}-reply batches we run"
        return said
    if pid == "faithful_model":
        if not f:
            return p["reason"]
        c = f["controls"]
        return (f"replies match the original's for {tenth(f['display'])} tokens on average; our "
                f"4-bit copy {tenth(c['q4_k_m']['display'])}, our 8-bit copy "
                f"{tenth(c['q8_0']['display'])}")  # fmt: skip
    if pid == "machine_checked":
        formal = p.get("formal") or {}
        tool = str(formal.get("tool") or "").split(" ")[0]
        run = (row.get("statement") or {}).get("verifiers", {}).get("run")
        stated = (row.get("statement") or {}).get("verifiers", {}).get("stated")
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
        if reach == "verifier_run":
            return f"a {tool} theorem we rebuilt, about {run}, the verifier we run"
        if reach == "protocol_and_statement":
            about = f"about {stated} and the method" if stated else "about the method"
            return f"a {tool} theorem we rebuilt, {about}; it does not reach {run}, which we run"
        return f"a {tool} theorem we rebuilt, about part of the method"
    if pid == "no_trusted_party":
        if cause == "not_stated":
            return f"nothing in the {count(k_docs, 'document')} we read on what soundness rests on"
        if step == "green":
            return "cryptographic assumptions only and no setup secret, in the publisher's words"
        if f.get("clause") == "reading":
            return ("on our reading, cryptographic assumptions only and no setup secret; the "
                    "publisher does not say it in one sentence")  # fmt: skip
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
        return f"that limit for {it['run']}" if it.get("stated") else \
            f"the limit for {it['run']}, the verifier we run"  # fmt: skip
    if need == "zk_run":
        n = it.get("n")
        return f"that theorem for the {n}-reply batches we run" if it.get("unit") == "request" \
            and n and n > 1 else "that theorem for what we run"  # fmt: skip
    if need == "rebuild":
        return "a rebuild of that new theorem" if it.get("new") else "a rebuild of it"
    if need == "reach_run":
        return f"a theorem that reaches {run}"
    if need == "exponent":
        return f"every term at most 2^-{it['floor']}"
    if need == "above":
        return f"an average above {tenth(it['value'])}"
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
    "visible_list": "a published list of what a proof shows",
    "fitted": "nothing on that list computed from the weights",
    "hide_statement": "a statement that a proof keeps the weights secret",
    "zk_theorem": "a zero-knowledge theorem",
    "one_at_a_time": "a run of ours that sends one request at a time",
    "named_theorem": "a named computer-checked theorem",
    "whole_method": "a theorem of the whole method, the model's computation included",
    "conclusion": "a conclusion about the model",
    "axioms": "a rebuild with only the tool's standard axioms",
    "trusted_base": "a list of everything the theorem relies on",
    "input_code": "no input-reading code outside the theorem",
    "rests_sentence": "that sentence in its own words",
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
                "A theorem. Today the documents do not say whether the limit is proved.")  # fmt: skip
    elif need == "adversary":
        said = "A statement that it holds against any cheating prover. " + (
            "Today it is stated only against a weaker cheater." if it.get("adversary") == "weaker"
            else "Today the documents do not say.")  # fmt: skip
    elif need == "unit":
        unit = it.get("unit")
        u = (f.get("said") or {}).get("unit") or {}
        today = (f"Today it is for one {u['named']}, {u.get('described')}." if unit == "part" and u.get("named")
                 else "Today it is for one part of a proof." if unit == "part"
                 else "Today it is for one round." if unit == "round"
                 else "Today one proof covers more than one reply." if unit == "proof"
                 else "Today the documents do not say what it is for.")  # fmt: skip
        said = f"A limit for a whole reply. {today}"
    elif need == "granularity":
        said = "A record of how many replies one proof covers. Today none is recorded."
    elif need == "batch":
        n = it.get("n")
        if it.get("batch") == "together":
            said = (f"A limit for each reply checked on its own. Our {n} replies are made as one "
                    "batch, and we check each reply's proof in its own call. For a batch the "
                    f"publisher states one limit for its members checked together: {n} times the "
                    "limit for one proof, counting the hash queries made for the whole batch. For "
                    "members checked in separate calls it states no limit. It does not say why, "
                    "or whether such a limit would be larger or smaller.")  # fmt: skip
        else:
            said = (f"A limit for each reply checked on its own. Our {n} replies are made as one "
                    "batch, and the publisher states no limit for the members of a batch.")  # fmt: skip
    elif need == "batch_size":
        said = "A record of our batch size. Today none is recorded."
    elif need == "parameters":
        said = "The publisher's statement that the limit is for the settings we run. " + (
            "Today it is stated for other settings." if it.get("parameters") == "other"
            else "Today the documents do not show that it is.")  # fmt: skip
    elif need == "conditions":
        head = ("A record that the theorem's condition holds for the files we run." if it.get("proved")
                else "A record that the limit's conditions hold for the files we run.")  # fmt: skip
        plain = said_of(p, "conditions_shown").get("plain")
        cond = said_of(p, "conditions_shown").get("quotes") or []
        today = plain or ("Today the documents name none and show none." if not cond
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
        if floor == 128:
            if f.get("basis") == "conjectured" or (len(terms) == 1 and not it.get("q")):
                today = f"Today about 2^-{terms[0]} ({terms[0]} bits)." if terms else ""
            else:
                written = [f"q × 2^-{t}" if i == 0 and it.get("q") else f"2^-{t}"
                           for i, t in enumerate(terms)]  # fmt: skip
                today = f"Today the terms are {and_list(written)}."
                if it.get("q"):
                    today += (f" The rule compares the exponents as written, {and_list(map(str, terms))}, "
                              "with 128, and fixes no number of queries.")  # fmt: skip
            said = f"Every term at most 2^-128. {today}"
        else:
            said = f"Every term at most 2^-{floor}. Today the smallest exponent is {min(terms)}."
    elif need == "reading":
        k = len(it["facts"])
        this = "this is" if k == 1 else "both are" if k == 2 else "all are"
        said = f"The publisher's own words {reading_topics(it['facts'])}. Today {this} our reading."
    elif need == "zk_run":
        n = it.get("n")
        said = (f"The theorem for the {n}-reply batches we run. Today it covers one request per "
                "proof." if it.get("unit") == "request" and n and n > 1
                else "That theorem for what we run.")  # fmt: skip
    elif need == "programs":
        said = "The publisher's statement that its programs keep the weights secret."
        if it.get("programs") == "expected":
            said += " Today it states an expectation, not a statement."
        elif it.get("read"):
            said += " Today we count none for the programs we run; this is our reading."
    elif need == "visible_list":
        said = (
            "A published list of what a proof shows, with nothing on it computed from the weights."
        )
    elif need == "fitted":
        said = ("Nothing on the list of what a proof shows that is computed from or fitted to the "
                f"weights. Today {count(it['k'], 'item')} {'is' if it['k'] == 1 else 'are'}.")  # fmt: skip
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
        said = (f"An average shown above {tenth(t['display'])}, halfway between {names[0]} "
                f"({tenth(a['display'])}) and {names[1]} ({tenth(b['display'])}). Today "
                f"{tenth(fd['display'])}.")  # fmt: skip
        if it is first_above(p):
            said += (f" The number format of the copy {name_of(row)} proves is the publisher's "
                     "choice, so this item is the publisher's.")  # fmt: skip
    elif need == "one_at_a_time":
        fid = rung_of(row).get("fidelity") or {}
        said = ("Our test run one request at a time on this model. Today " + runs_words(fid)
                + ". Serving several requests at once can change replies, so it can change the "
                f"second run's score ({tenth(f['controls'][f['rerun']]['display'])}), from which the "
                f"{tenth(f['green']['display'])} threshold is computed.")  # fmt: skip
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
    """How our fidelity run sent its prompts, part by part (FI-9): "part of our run, the
    original and its second run, sent every prompt in one call, and our copies ran 16 at a
    time"."""
    parts = []
    for r in fid.get("runs") or ():
        who = "the original and its second run" if r.get("part") is None else "our copies"
        if r.get("engine") == "vllm":
            parts.append(f"part of our run, {who}, sent every prompt in one call")
        elif r.get("slots") is not None:
            parts.append(f"{who} ran {r['slots']} at a time")
    return "; ".join(parts) if parts else "no slot count is recorded"


def missing_line(p, row):
    """The default row's Missing line: the count of items, who acts, the first need, and ours
    where both act; Fidelity lists every item."""
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
    pub = sum(1 for it in items if it["by"] == "publisher")
    us = n - pub
    if n == 1:
        return f"1 item, {WHO[items[0]['by']]}: {item_short(items[0], p, row)}."
    who = (("both" if n == 2 else "all") + " " + WHO["publisher"] if not us
           else ("both" if n == 2 else "all") + " " + WHO["us"] if not pub
           else f"{pub} {WHO['publisher']} and {us} {WHO['us']}")  # fmt: skip
    head = f"{count(n, 'item')}, {who}"
    if p["id"] == "faithful_model" and all(
        it["need"] in ("above", "one_at_a_time") for it in items
    ):
        said = []
        aboves = [(g["to"], it) for g in groups for it in g["items"] if it["need"] == "above"]
        for i, (to, it) in enumerate(aboves):
            said.append(f"{'an average' if i == 0 else 'then'} above {tenth(it['value'])} (for "
                        f"{STEP_WORD[to]})")  # fmt: skip
        said += [item_short(it, p, row) for it in items if it["need"] == "one_at_a_time"]
        return f"{head}: {and_list(said) if len(said) > 2 else ', '.join(said)}."
    first = items[0]
    said = f"{head}. First: {item_short(first, p, row)}."
    if pub and us:
        ours = next(it for it in items if it["by"] == "us")
        said += f" Ours: {item_short(ours, p, row)}."
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


def reading_html(p, skip=()):
    """ "Our reading, on two points the grade uses. (1) ... (2) ...", each note's plain words."""
    facts = [f for f in p["read_facts"] if f["fact"] not in skip]
    if not facts or not p["reading"]:
        return ""
    k = len(p["read_facts"])
    head = f"Our reading, on {number(k) if k > 1 else 'one'} {'point' if k == 1 else 'points'} the grade uses."
    body = " ".join(f"({i}) {f['plain'] or f['note']}" for i, f in enumerate(facts, 1)) \
        if len(facts) > 1 else (facts[0]["plain"] or facts[0]["note"])  # fmt: skip
    return p_(quoted(f"{head} {body}"))


def has_unforgeable(p, row, petals):  # noqa: PLR0915 (one paragraph per fact)
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
        said = f"The publisher proves{by} a limit on the chance that a fake reply passes: at most {expr} {per}."
        q = f.get("q_cross")
        if q:
            k = len(f["terms"]) - 1
            said += (" Here q is the number of hash queries a cheating prover makes, that is, how "
                     "many times it runs the hash function while searching for a proof that passes. "
                     f"The other {'term is' if k == 1 else 'terms are'} fixed. The first grows with q: "
                     f"it reaches 2^-100 at 2^{q[0]} queries and 2^-80 at 2^{q[1]}.")  # fmt: skip
        batch = next((i for i, it in enumerate(items_of(p), 1) if it["need"] == "batch"), None)
        if f.get("unit") == "proof" and f.get("one_reply") and batch:
            said += (f" Each reply has its own proof, but our {f['batch_size']} replies are made as "
                     f"one batch (see item {batch}).")  # fmt: skip
        out.append(p_(e(said)))
    elif f.get("basis") == "conjectured":
        thing = unit_said.get("named") or "proof"
        said = (f"The publisher states {least} conjectured bits of security {per_words(f, True)}"
                f"{' of a proof' if unit_said.get('named') else ''}: a chance of about 2^-{least} "
                f"that a fake {thing} passes.")  # fmt: skip
        b = (f.get("said") or {}).get("basis") or {}
        if b.get("named"):
            said += f" The figure comes from the accounting of {b['named']}, {b.get('described') or 'as the publisher states'}."
        said += " Conjectured: it rests on an unproven assumption, not a theorem."
        out.append(p_(e(said)))
    else:
        out.append(
            p_(
                e(
                    f"The publisher states a limit, {expr} {per}, and does not say whether it is proved."
                )
            )
        )
    if f.get("unit") == "part" and unit_said.get("named"):
        q = (unit_said.get("quotes") or [None])[0]
        quote = f" ({q_html(q)})" if q else ""
        out.append(p_(f"One {e(unit_said['named'])} proves {e(unit_said.get('described') or 'part of a reply')}"
                      f"{quote}. A whole reply needs many {e(unit_said['named'])}s, and the publisher "
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
        if tested or no_claim:
            parts = (["is tested, not proved"] if tested else []) + (
                ["claims no limit for it"] if no_claim else []
            )
            said += e(f" The publisher states that {run} {' and '.join(parts)}.") if tested else \
                e(f" The publisher claims no limit for {run}.")  # fmt: skip
            if tested and no_claim:
                said = said.replace(f"{run} is tested, not proved and claims no limit for it.",
                                    f"{run} is tested, not proved, and claims no limit for it.")  # fmt: skip
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
        out.append(
            p_(
                f"The publisher names no verifier for this figure{e(adv)}. We run {run_words}{runs}."
            )
        )
    out.append(reading_html(p))
    out.append(why_html(p, row))
    return out


def items_of(p):
    return [it for g in p["to_met"] for it in g["items"]]


def why_html(p, row):
    """The Why line on UF-9, WH-6 and MC-6 (amended 2026-11-17): the condition that set the step
    and the one that stops the next. No state reads it."""
    w = p.get("why")
    if not w:
        return ""
    step = STEP_WORD[step_key(p["step"], p["cause"])]
    if p["id"] == "unforgeable":
        i, j = w["first"], w["last"]
        items = f"item {i}" if i == j else f"items {i} to {j}"
        said = f"Why {step}: the limit is not shown to cover what we run ({items} below)."
        if w["floor"] == 80:
            exps = and_list(str(t) for t in w["exps"])
            said += (f" For a theorem, Partly met needs every term at most 2^-80, and the exponents "
                     f"as written, {exps}, pass.")  # fmt: skip
            if w.get("q"):
                said += " The rule compares the written exponents and fixes no number of queries."
        else:
            least = w["least"]
            said += (" For a limit that is not a theorem, Partly met needs every term at most "
                     f"2^-100, and {least} bits {'is exactly that' if least == 100 else 'passes'}.")  # fmt: skip
            if w.get("unit_item"):
                named = ((facts_of(p).get("said") or {}).get("unit") or {}).get("named") or "part"
                said += (f" The rule reads the figure per {named}, as stated. That it is not for a "
                         f"whole reply is item {w['unit_item']}, which keeps the grade below Mostly "
                         "met but does not lower it further.")  # fmt: skip
        return p_(e(said), "pwy")
    if p["id"] == "weights_hidden":
        n = w["n"]
        return p_(e(f"Why {step}: Mostly met needs a zero-knowledge theorem, at least for the "
                    f"method, and there is one. The {count(n, 'item')} below {'is' if n == 1 else 'are'} "
                    "what Met adds."), "pwy")  # fmt: skip
    if p["id"] == "machine_checked":
        run = w.get("run")
        read = ", on our reading of the reach and the conclusion" if w.get("read") else ""
        stop = (f"It stops below Met because it does not reach {run}." if not w.get("gaps")
                else "It stops below Met because of the gaps listed below.")  # fmt: skip
        return p_(e(f"Why {step}: the rules read how far the theorem reaches, what its conclusion "
                    "is about, whether input-reading code sits outside it, its axioms, and our "
                    f"rebuild. On those it reaches {step}{read}. {stop}"), "pwy")  # fmt: skip
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
                (f" ({q_html(vq)})" if vq else "") + "."  # fmt: skip
        return [p_(html)]
    if f.get("verifier_gets_weights") is True:
        out.append(
            p_("The verifier is given the weights" + (f" ({q_html(vq)})" if vq else "") + ".")
        )
    if f.get("stated") is False:
        q = first_quote(p, "stated")
        out.append(
            p_(
                "The publisher states that a proof does not hide the weights"
                + (f" ({q_html(q)})" if q else "")
                + "."
            )
        )
    if p["step"] in ("amber_upper", "green"):
        tool = tool_word(petals)
        formal = petals["machine_checked"].get("formal") or {}
        in_tool = f" in {tool}" if tool and (formal.get("scope_card") or {}).get("zero_knowledge", {}).get(
            "protocol", {}).get("value") == "machine_checked" else ""  # fmt: skip
        said = (f"The publisher proves{in_tool} a zero-knowledge theorem: everything a verifier "
                "sees could have been produced without the weights.")  # fmt: skip
        kind, model = f.get("zk_kind"), f.get("zk_model")
        bound = ((formal.get("scope_bounds") or {}).get("zero_knowledge") or {}).get("text")
        if kind == "statistical":
            said += " It is statistical: it holds up to a difference too small to detect"
            said += f" (the publisher's bound: {bound})" if bound else ""
            said += ", with the hash function treated as perfectly random (the random-oracle model)." \
                if model == "random_oracle" else "."  # fmt: skip
        elif kind:
            said += f" It is {kind}."
        n = f.get("batch_size")
        if f.get("proof") == "protocol":
            said += " The theorem covers the method"
            said += " with one request per proof." if f.get("zk_unit") == "request" else "."
            if f.get("zk_unit") == "request" and n and n > 1:
                said += f" We run batches of {n} replies, which it does not cover."
        else:
            said += " It covers what we run."
        out.append(p_(e(said)))
    elif p["step"] == "amber_lower":
        out.append(p_(e("The publisher states that a proof hides the weights, and proves no "
                        "zero-knowledge theorem.")))  # fmt: skip
    programs = next((r for r in p["read_facts"] if r["fact"] == "programs"), None)
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
    out.append(why_html(p, row))
    return out


def visible_para(p):
    """What a proof shows, as the publisher lists it, the items it describes as computed from or
    fitted to the weights named, each with the publisher's own explanation where it gives one."""
    f, visible = facts_of(p), p.get("visible") or []
    if not f.get("listed") or not visible:
        return ""
    m = len(visible)
    fitted = [v for v in visible if v["tag"] == "fitted_to_weights"]
    said = (
        f"The publisher lists {'at least ' if f.get('at_least') else ''}{m} things a proof shows."
    )
    if not fitted:
        return p_(e(said + " It describes none of them as computed from or fitted to the weights."))
    lis = []
    for v in fitted:
        item = v["item"].rstrip(".")
        item = item[:1].lower() + item[1:]
        more = v["quotes"][1:2]
        lis.append(f"<li>{e(item)}" + (f": {q_html(more[0])}" if more else "") + "</li>")
    return (p_(e(f"{said} It describes {len(fitted)} of them as computed from or fitted to the "
                 "weights:")) + f'<ul class="pls">{"".join(lis)}</ul>'
            + p_(e("The publisher lists these as visible. Neither its list nor our records measure "
                   "how much they reveal about the weights.")))  # fmt: skip


def has_faithful(p, row, petals):
    f, out = facts_of(p), []
    if not f:
        return [p_(e(cap(p["reason"]) + "."))]
    rung, name = rung_of(row), name_of(row)
    c = f["controls"]
    bits = {"bf16": "16-bit", "f16": "16-bit", "f32": "32-bit"}.get(rung.get("reference_dtype"), "")
    model = f"{rung['model']}, {bits}" if bits else rung["model"]
    out.append(p_(e(f"We sent {f['n']:,} prompts to {name} and to the original model ({model}). On "
                    f"average, {name}'s replies match the original's for {tenth(f['display'])} "
                    "tokens before the first difference.")))  # fmt: skip
    rerun = c[f["rerun"]]["display"] if f.get("rerun") in c else None
    tokens = (
        S.V.get("request", {}).get("output_tokens")
        if isinstance(S.V.get("request"), dict)
        else None
    )
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
        scale.append(
            f"and the bar, a copy we damaged on purpose{bar_bits}, {tenth(bar['display'])}"
        )
    out.append(p_(e("For scale, the same score on the same prompts: " + "; ".join(scale) + ".")))
    if f.get("slots") != 1 and f.get("rerun_engine") == "vllm":
        out.append(p_(e("On this model the original runs in vLLM, a serving program. Its second run "
                        "sends the prompts in reverse order, so they are batched differently, and "
                        "batching can change a reply: on some prompts the two runs differ. That is "
                        "why Met needs a run of one request at a time, so that batching does not "
                        "move the second run's score.")))  # fmt: skip
    out.append(p_(e(proved_sentence(row, f))))
    fid = rung.get("fidelity") or {}
    if f.get("slots") == 1:
        out.append(p_(e("Our run sent one request at a time, as Met needs.")))
    else:
        out.append(p_(e(cap(runs_words(fid)) + ".")))
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
        said = f"{name} proves a copy with {wword + ' ' if wword else ''}weights, {bits_words(bits)} bits each on average"
        total, active = rung.get("parameters_total"), rung.get("parameters_active")
        if active and total and active < total:
            short = (
                rung["model"].split(" ")[0]
                if " " not in rung["model"]
                else " ".join(rung["model"].split(" ")[:3])
            )
            said += (f" over the weights used for each token ({short} uses about {params_words(active)} "
                     f"of its {params_words(total)} weights on each token)")  # fmt: skip
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
    st = row.get("statement") or {}
    run, stated = (st.get("verifiers") or {}).get("run"), (st.get("verifiers") or {}).get("stated")
    k_docs = len(p["sources"])
    if p["cause"] == "not_stated":
        return [p_(e(f"The {count(k_docs, 'document')} we read at the version we ran ({pin7(row)}) "
                     "name no computer-checked theorem."))]  # fmt: skip
    if p["cause"] in ("stated", "not_read") or not formal:
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    tool = str(formal.get("tool") or "").split(" ")[0]
    who = stated or "its verifier"
    said = (f"The publisher proves in {tool}, a language in which a computer checks every step of a "
            f"proof, a theorem that {who} refuses fake replies, up to the chance limit under "
            f"{PETAL_NAME['unforgeable']}.")  # fmt: skip
    if formal.get("reach") == "protocol_and_statement":
        said += " The theorem's statement includes the model's computation."
    out.append(p_(e(said)))
    build = formal.get("build") or {}
    if build:
        version = str(build["toolchain"]["version"]).lstrip("v")
        if build.get("status") == "built" and build.get("exit_code") == 0:
            axioms = build.get("axioms") or []
            said = (f"We rebuilt it at the version we ran ({pin7(row)}) with the {tool} version the "
                    f"publisher pins, {version}. It checked (exit code 0, {secs(build['seconds'])}).")  # fmt: skip
            if axioms and p["step"] in ("amber_upper", "green"):
                said += (f" It uses only {tool}'s {number(len(axioms))} standard axioms, the basic "
                         f"assumptions any {tool} proof may use, and no step is skipped.")  # fmt: skip
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
            f"It does not reach {run}, which we run"
            + (", and which the publisher states is tested, not proved" if tested else "")
            + "."
        )
        if formal.get("input_code_unverified") is True:
            q = next(
                (q for q in p["quotes"] if "parser" in q["text"] or "outside" in q["text"]), None
            )
            said += " Input-reading code sits outside it" + (
                f": {q_html(q)}, as the publisher states." if q else "."
            )
        out.append(p_(said))
    if formal.get("theorem"):
        out.append(
            p_(
                e(
                    f"No outside {tool} expert has reviewed what the theorem states; none is recorded."
                )
            )
        )
    out.append(reading_html(p))
    out.append(why_html(p, row))
    lim = formal.get("limits") or []
    if lim:
        lis = "".join(f"<li>{quoted(i['plain'])} ({q_html(i['quotes'][0])} ↗)</li>" for i in lim)
        out.append(
            f'<h5 class="pbh">{e(PETAL_BLOCK["limits"])}</h5>'
            + p_(
                e(
                    "The rules above read five things only, so the limits below do not lower the "
                    "grade. A related question is open in our rules (RFC-0018, Q34): whether a "
                    "grade above Partly met should need a record that the verifier accepts honest "
                    "proofs at our files. Each item is a plain summary, then the publisher's "
                    "words, linked."
                )
            )
            + f'<ul class="pls">{lis}</ul>'
        )
    return out


def has_trust(p, row, petals):
    f, out = facts_of(p), []
    if p["cause"] in ("not_stated", "not_read") or not f:
        return [p_(e(cap(has_short(p, row, petals)) + "."))]
    q = first_quote(p, "publicly_checkable")
    if f.get("publicly_checkable") is True:
        out.append(
            p_(
                "Anyone can check a proof, as the publisher states"
                + (f" ({q_html(q)})" if q else "")
                + "."
            )
        )
    elif f.get("publicly_checkable") is False:
        out.append(
            p_(
                "Only a named party can check a proof, as the publisher states"
                + (f" ({q_html(q)})" if q else "")
                + "."
            )
        )
    rests = next((r for r in p["read_facts"] if r["fact"] == "rests_on"), None)
    if rests:
        out.append(p_(quoted(rests["plain"] or rests["note"])))
        out.append(p_(e("We read this as: soundness rests on cryptographic assumptions only, and no "
                        "setup step produced a secret. The publisher does not say that in one "
                        "sentence; it is our reading.")))  # fmt: skip
    else:
        out.append(p_(e(cap(has_short(p, row, petals)) + ".")))
    return out


HAS = {"unforgeable": has_unforgeable, "weights_hidden": has_weights_hidden,
       "faithful_model": has_faithful, "machine_checked": has_machine_checked,
       "no_trusted_party": has_trust}  # fmt: skip


# ------------------------------------------------------------------ how it is graded


def ladder_html(p, row):
    """The petal's ladder, its step's line (or its clause, on Trust's Mostly met) opened by
    "<System> is here:". A line that does not apply to this system is not printed."""
    here = HERE.format(system=name_of(row))
    key = step_key(p["step"], p["cause"])
    lines, cur = [], []
    for k, words, joins in LADDER[p["id"]]:
        if not joins and cur:
            lines.append(cur)
            cur = []
        cur.append((k, words))
    if cur:
        lines.append(cur)
    out = []
    for line in lines:
        hit = next((i for i, (k, _) in enumerate(line) if k == key), None)
        if hit is None:
            out.append(p_(e(" ".join(w for _, w in line))))
            continue
        before, mine, after = line[:hit], line[hit], line[hit + 1 :]
        if before:
            out.append(p_(e(" ".join(w for _, w in before))))
        if p["id"] == "no_trusted_party" and mine[0] == "amber_upper":
            clause = facts_of(p).get("clause") or "reading"
            other = "ceremony" if clause == "reading" else "reading"
            out.append(p_(e(mine[1])) + '<div class="plc">'
                       + p_(f'<span class="phere">{e(here)}</span>{e(LADDER_CASES[clause])}')
                       + p_(e(LADDER_OR + LADDER_CASES[other])) + "</div>")  # fmt: skip
        else:
            out.append(p_(f'<span class="phere">{e(here)}</span>{e(mine[1])}'))
        if after:
            out.append(p_(e(" ".join(w for _, w in after))))
        if (
            p["id"] == "faithful_model"
            and facts_of(p).get("policy_cap")
            and mine[0] == "amber_lower"
        ):
            out.append(p_(e(LADDER_CAP.format(system=name_of(row)))))
    if p["id"] == "no_trusted_party" and key != "amber_upper":
        out = [o.replace(e(LADDER["no_trusted_party"][1][1]), e("Mostly met, in either of two cases: "
                         + LADDER_CASES["reading"][:-1] + "; or " + LADDER_CASES["ceremony"])) for o in out]  # fmt: skip
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
        out.append(
            details_list(
                EVIDENCE["quotes"].format(pin=pin7(row), n=count(len(p["quotes"]), "quote")),
                quote_links(p["quotes"]),
            )
        )
    if p["sources"] and p["cause"] == "not_stated":
        docs = ", ".join(f'<a href="{e(d["url"])}">{e(d["path"])}</a>' for d in p["sources"])
        out.append(p_(f"{e(EVIDENCE['docs'].format(n=len(p['sources'])))}: {docs}", "pel"))
    if pid == "weights_hidden" and p.get("forms"):
        out.append(
            details_list(
                EVIDENCE["forms"].format(n=count(len(p["forms"]), "sentence")),
                headless(forms_html(p["forms"])),
            )
        )
    if pid == "weights_hidden" and p.get("visible"):
        k = sum(1 for v in p["visible"] if v["tag"] == "fitted_to_weights")
        n = f"{'at least ' if p.get('visible_at_least') else ''}{len(p['visible'])}"
        n += f", {k} computed from or fitted to the weights" if k else ""
        out.append(
            details_list(
                EVIDENCE["visible"].format(n=n),
                headless(visible_html(p["visible"], p.get("visible_at_least"))),
            )
        )
    if p["read_facts"]:
        k = len(p["read_facts"])
        on = {READING_ON.get(f["fact"]) for f in p["read_facts"]} - {None}
        head = EVIDENCE["reading"].format(n=count(k, "note")) + (
            f", on {and_list(sorted(on))}" if k == 1 and on else ""
        )
        body = "".join(p_(e(f["note"]), "cn") for f in p["read_facts"])
        line = details_list(head, body)
        if not p["reading"]:
            why = ""
            if pid == "unforgeable" and facts_of(p).get("basis") != "proved":
                why = ": a limit that is not a theorem stays at Partly met at most" + (
                    ", whatever its settings" if p["read_facts"][0]["fact"] == "parameters" else ""
                )
            line += p_(
                e(
                    EVIDENCE["not_used"].format(
                        this="this note" if k == 1 else "these notes", why=why
                    )
                ),
                "pel",
            )
        out.append(line)
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
                out.append(p_(f'<span class="k">{e(EVIDENCE["outside"])}</span> {e(trial_words(t))} '
                              f'<a href="{e(link(t["record"]))}">{e(RECORD_LINK)}</a>', "pel"))  # fmt: skip
            state = "passed on this run" if all(s == "held" for s in states) else \
                "did not all pass on this run (see Checks)"  # fmt: skip
            out.append(
                p_(f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))}', "pel")
            )
        else:
            state = ("Each was refused on this run;" if all(s == "held" for s in states)
                     else "Not every one was refused on this run;")  # fmt: skip
            out.append(
                p_(
                    f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))} {checks}',
                    "pel",
                )
            )
    elif pid == "weights_hidden":
        s = check_state(row, "no_weight_file")
        state = {"held": "It passed on this run.", "failed": "It failed on this run."}.get(
            s, "It is not decided on this run."
        )
        out.append(
            p_(
                f'<span class="k">{rec}</span> {e(RECORDS[pid].format(state=state))} {checks}',
                "pel",
            )
        )
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
    """TR-1's trial in plain words: what it accepted, what it refused, its times. It sets no
    grade."""
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
    said += " This trial sets no grade (RFC-0018, Q34 asks whether it should)."
    return said


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
        if f.get("forms"):
            pass
        n = f.get("batch_size")
        if f.get("zk_unit") == "request" and n and n > 1:
            out.append(f"Not for our {n}-reply batches.")
        out.append(f"Programs: {yes_no(f.get('programs'))}{r('programs')}.")
        out.append(f"Weights given to the verifier: {yes_no(f.get('verifier_gets_weights'))}.")
        if f.get("listed"):
            k = len(f.get("fitted") or [])
            out.append(
                f"Visible: {'at least ' if f.get('at_least') else ''}{f.get('visible_count')}, {k} tagged fitted to the weights."
            )
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
            out.append(
                "Decoding: exact match (only the model's top token), so the cap for other decoding rules does not apply."
            )
        fid = rung_of(row).get("fidelity") or {}
        slots = []
        for run in fid.get("runs") or ():
            slots.append("none recorded for the vLLM part" if run.get("engine") == "vllm"
                          else f"{run.get('slots')} for {'the copies in ' if run.get('part') else ''}{run.get('engine')}")  # fmt: skip
        out.append(f"Slots (requests at a time): {'; '.join(slots) or yes_no(None)}.")
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
                    f"Statement not reviewed by an outside {str(formal['tool']).split()[0]} expert."
                )
        else:
            out.append("Tool, theorem and trusted base: not stated.")
        out.append(("raw", f'Scope: <a href="#scope">{e(SCOPE_LINK)}</a>'))
    elif pid == "no_trusted_party" and f:
        out.append(f"Rests on: {yes_no(f.get('rests_on'))}{r('rests_on')}.")
        out.append(f"Publicly checkable: {yes_no(f.get('publicly_checkable'))}.")
        out.append("Not graded: which model a commitment names (RFC-0018, Q12).")
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
    return block("not_graded", p_(e(NOT_GRADED_HERE[p["id"]].format(arch=arch))))


def block(key, body):
    return f'<h5 class="pbh">{e(PETAL_BLOCK[key])}</h5>{body}'


def petal_body(p, row, petals):
    """The petal opened: Met needs, Has (with its Why line), how it is graded, Missing, what is
    not graded here, Evidence, the field's terms."""
    tokens = (
        S.V.get("request", {}).get("output_tokens", 512)
        if isinstance(S.V.get("request"), dict)
        else 512
    )
    needs = MET_NEEDS[p["id"]].format(tokens=tokens, alpha="0.05")
    has = "".join(HAS[p["id"]](p, row, petals))
    return (block("needs", p_(e(needs))) + block("has", has) + block("how", ladder_html(p, row))
            + block("missing", missing_html(p, row, petals)) + not_graded_html(p, row)
            + block("evidence", evidence_html(p, row, petals)) + terms_html(p, row, petals))  # fmt: skip


def petal_row(i, p, row, petals):
    """One petal's row: its name with its plain question; its grade and what it comes from; one
    Has line, Formally verified's limits line, the Missing line; Details."""
    tok = f"{p['state']} {p['form']}".strip()
    data = f' data-step="{e(p["step"] or "none")}"'
    state = chip(p["state"], petal_step(p), p["form"])
    if p["cause"] is not None:
        data += f' data-cause="{e(p["cause"])}"'
        state = (f'<a class="cc" href="{CHECKS_PAGE}#cause-{e(p["cause"])}" '
                 f'title="{e(CAUSE_WORD[p["cause"]])}">{state}</a>')  # fmt: skip
    src = came_from(p)
    src = f'<span class="pfr">{e(src)}</span>' if src else ""
    lines = [
        f'<p class="phs"><span class="k">{e(HAS_HEAD)}:</span> {e(has_short(p, row, petals))}.</p>'
    ]
    limits = ((p.get("formal") or {}).get("limits") or []) if p["id"] == "machine_checked" else []
    if limits:
        lines.append(p_(e(LIMITS_LINE.format(k=len(limits))), "plm"))
    lines.append(
        f'<p class="pms"><span class="k">{e(MISSING_HEAD)}:</span> {e(missing_line(p, row))}</p>'
    )
    owner = f'<span class="sr">, {e(PETAL_NAME[p["id"]])}</span>'
    details = (f'<details class="more pdt"><summary>Details{owner}</summary>'
               f'<div class="pbd">{petal_body(p, row, petals)}</div></details>')  # fmt: skip
    ask = PETAL_ASK[p["id"]]
    return (f'<tr class="pt {tok}" id="petal-{e(p["id"])}"><th scope="row">'
            f'<a class="sl s{i + 1} {tok}"{data} href="{CHECKS_PAGE}#{p["id"]}" data-k="p{i + 1}" '
            f'title="{e(PETAL_TERM[p["id"]])}"><span>{e(PETAL_NAME[p["id"]])}</span></a>'
            f'<span class="pst">{e(ask)}</span></th>'
            f'<td class="cst">{state}{src}</td>'
            f'<td class="prs">{"".join(lines)}{details}</td></tr>')  # fmt: skip


def glyph_section(row, scope_head):
    """The Glyph section: its lead, the five petals, then soundness, zero knowledge and
    completeness with the stated security and the scope card (`scope_head`)."""
    petals = {p["id"]: p for p in row["glyph"]}
    lead = "".join(
        p_(e(w), "glead" + (" gwords" if i == 2 else "")) for i, w in enumerate(GLYPH_LEAD)
    )
    trs = "".join(petal_row(i, p, row, petals) for i, p in enumerate(row["glyph"]))
    return (f'<div class="glede">{lead}</div>'
            '<div class="checks"><table class="rt ckt gbig gpl"><caption class="sr">Petal, grade, '
            f'what it has and what it misses</caption><tbody>{trs}</tbody></table></div>'
            f'<div id="scope">{scope_head}</div>')  # fmt: skip
