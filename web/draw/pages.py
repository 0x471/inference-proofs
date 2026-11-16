"""The system pages (RFC-0018 SI-3), the checks page and the 404.

A system page holds one row of the board: its other figures in one ruled row; the glyph once,
large, its arms the heads of a ruled table of the petals (state, reason, and behind a disclosure
the publisher's quotes and basis); then the six checks as a ruled table (state, cause, evidence
behind a disclosure), the cost parts, fidelity beside the model's controls and the sessions.
"""

import math
import re

from . import state as S
from .chrome import (
    CHECKS_PAGE,
    LEVEL_ANCHOR,
    MANDATE_PAGE,
    card_current,
    cards_record,
    counted,
    fig_words,
    footer,
    gpu_name,
    has,
    header,
    how_computed,
    lead_figure,
    link,
    page,
    pnav,
    row_cost,
    rung_of,
    share_words,
)
from .glossary import term
from .hexagon import glyph_svg
from .overview import (
    BARE,
    BINDING_GAP,
    NOT_TESTED,
    defined,
    fidelity_word,
    fig_html,
    filled,
    how_link,
    href,
    multiple_html,
    name_of,
    nobreak,
    pct,
    request_words,
    serving_words,
    split_html,
    standing_html,
    states,
    sub_line,
    whole_line,
    whole_note,
)
from .plots import fid_svg, hbar
from .words import (
    ARCH_LONG,
    ARCH_NO_FACT,
    ARCH_SHORT,
    AS_READ,
    BASIS_BITS,
    BASIS_READING,
    BASIS_WORD,
    CARD_ERRATUM,
    CAUSE_WORD,
    CHECK_CAUSE_LEAD,
    CHECK_CAUSE_WORD,
    CHECK_FAILED,
    CHECK_HELD,
    CHECK_MORE,
    CHECK_NAME,
    CHECK_PLAIN,
    CHECKS_DESC,
    CHECKS_LEAD,
    CONTROL_NAME,
    DOCS_READ,
    DTYPE_BITS,
    FID_KIND,
    FID_LABEL,
    FID_LEAD_CHECK,
    FID_LEAD_LOGITS,
    FID_LEAD_PREFIX,
    FID_LEAD_TF,
    FID_PLAIN,
    FID_PLAIN_COPIES,
    FID_PLAIN_TF,
    FID_WHO,
    FID_WHY,
    FIGURE_ANCHOR,
    FIGURE_HEAD,
    FIGURE_NAME,
    FIGURE_RULE,
    FULL_LOAD_WORD,
    HIDING_LABEL,
    HOW_RULE,
    KEPT_CHANGE,
    KEPT_HEAD,
    KEPT_MEANS,
    KEPT_SETS,
    KEPT_TIME,
    KNOW_COLS,
    KNOW_HEAD,
    KNOW_LINES,
    KNOW_WHERE,
    KNOW_WORD,
    LEVEL_STATEMENT_HEAD,
    LIM_CEILING,
    LIM_COPY,
    LIM_ENGINES,
    LIM_GREEN,
    LIM_LLAMA,
    LIM_ORIGINAL,
    LIM_PART,
    LIM_PROMPTS,
    LIM_VLLM,
    M_COL,
    M_HEAD,
    M_NAME,
    MANDATE,
    MANDATE_BELIEF,
    MANDATE_CORRECTIONS,
    MANDATE_CORRECTIONS_IN,
    MANDATE_DESC,
    MANDATE_LEVEL,
    MANDATE_LEVEL_IN,
    MANDATE_LEVEL_LINK,
    MANDATE_MEMBERS_IN,
    NEXT_BY,
    NEXT_HEAD,
    NO_STEADY_WORD,
    NOT_RUN_LEAD,
    NOT_RUN_RULE,
    NOT_TIMED_APART,
    NOTION_HEAD,
    NULL_WORD,
    OF_WHICH,
    ORDER_RULE,
    P_ABOVE,
    P_FLOOR,
    PART_WORD,
    PETAL_CAUSE_DRAW,
    PETAL_CAUSE_RULE,
    PETAL_CHECKS,
    PETAL_MORE,
    PETAL_NAME,
    PETAL_NOT_GRADED,
    PETAL_PLAIN,
    PETAL_PROTECTS,
    PETAL_QUESTION,
    PETAL_RULE,
    PETAL_STEPS_FOOT,
    PETAL_TERM,
    PREFIX,
    QUOTES_HEAD,
    REACH_GAP,
    REACH_LABEL,
    REACH_STATED,
    READ_AS,
    READING_HEAD,
    READING_RULE,
    REASON_LINK,
    RECORD_WORD,
    REPLY_TOKENS_HEAD,
    SCOPE_BOUND_HEAD,
    SCOPE_CARD_HEAD,
    SCOPE_COL_WORD,
    SCOPE_GRADED,
    SCOPE_HEAD,
    SCOPE_NOT_GRADED,
    SCOPE_PROTECTS,
    SCOPE_ROW_WORD,
    SCOPE_SHORT,
    SCOPE_STATED,
    SCOPE_TESTED,
    SCOPE_VALUE_WORD,
    SCOPE_WORD,
    SE3A_NONE,
    SE3A_ROW,
    SE3B_NONE,
    SE3B_ROW,
    SEP,
    STATE_WORD,
    STATED_SECURITY,
    STATEMENT_WORD,
    STEP_WORD,
    TF_AGREE,
    TF_BOTH,
    TF_FAILED,
    TF_INTERVAL,
    TF_KL,
    TF_KL_SUB,
    TF_KL_TITLE,
    TF_SUB,
    TF_TEST,
    TF_TESTS_ON,
    TIER_WORD,
    TRIAL_NO_PROOF,
    TRIAL_REFUSED,
    TRIAL_WHAT,
    TRIALS_HEAD,
    VERIFIER_LINE,
    VISIBLE_OTHERS,
    VISIBLE_TAG_WORD,
    architecture,
    beside_unit,
    curly,
    e,
    kl_head,
    number,
    petal_step,
    quoted,
    range_words,
    said_word,
    sig,
    step_key,
)

GLYPH = 6  # the checks page's key glyph, px per unit (318 by 174 px)
GPU_S = "gpu_s/request"  # a session's values: GPU-seconds per reply (RFC-0018 CO-1, CO-3)


def section(sid, title, body):
    return (f'<section class="blk" id="{sid}" aria-labelledby="h-{sid}">'
            f'<h2 class="sect" id="h-{sid}">{e(title)}</h2>{body}</section>')  # fmt: skip


RUN_ID = re.compile(r"^(\d{4}-\d{2}-\d{2})-.*-(\d+)$")


def where(d):
    """A record's directory in short: its run by date and ordinal, then what lies under it."""
    parts = d.split("/")
    for i, part in enumerate(parts):
        m = RUN_ID.match(part)
        if m:
            return " / ".join([f"{m[1]} \u00b7 {m[2]}", *parts[i + 1 :]])
    return parts[-1]


def run_link(row, run_id):
    """A run by date and ordinal (its id in the title), linked to its record."""
    rel = S.V["release"]
    label = f'<span title="{e(run_id)}">{e(where(run_id))}</span>'
    if rel is None or not str(rel["board"]).startswith("releases/"):
        return f'<span class="rid">{label}</span>'
    path = f"results/{rel['id']}/{row['system']}/{run_id}/run.json"
    return f'<a class="rid" href="{e(link(path))}" title="{e(run_id)}">{e(where(run_id))}</a>'


def run_words(path):
    """The run a record lies under, by date and ordinal ("2026-11-11 · 1"); None outside a run."""
    for part in path.split("/"):
        m = RUN_ID.match(part)
        if m:
            return f"{m[1]} \u00b7 {m[2]}"
    return None


def record_words(path, ptrs=()):
    """A record in words: its run, then what the file holds (RECORD_WORD), or, for JSON Pointers
    into it, their count by the entries' kind ("2 controls"). No file name, path or entry id: those
    stand in the link's title."""
    word = RECORD_WORD.get(path.rsplit("/", 1)[-1], path.rsplit("/", 1)[-1])
    if ptrs:
        word = counted_words(len(ptrs), ptrs[0].split("/")[0].removesuffix("s"))
    run = run_words(path)
    return f"{run}: {word}" if run else word


def evidence_links(paths):
    """A check's records, one link per file, labelled in words (`record_words`), the file's path
    and the entries a JSON Pointer names in its title; a directory's files (a trace per proof
    makes many) as one link to the directory with their count. A list: its length is the count
    the check's summary prints."""
    files: dict[str, list[str]] = {}
    for p in paths:
        path, _, ptr = p.partition("#")
        files.setdefault(path.rstrip("/"), []).append(ptr.strip("/"))
    dirs: dict[str, list[str]] = {}
    for path in files:
        dirs.setdefault(path.rsplit("/", 1)[0], []).append(path)
    out = []
    for d, paths_in in dirs.items():
        whole = [p for p in paths_in if not any(files[p])]
        if len(whole) > 1:  # several plain files of one directory: one link to it
            said = (", ".join(record_words(p).rsplit(": ", 1)[-1] for p in whole)
                    if len(whole) <= 3 else f"{len(whole):,} files")  # fmt: skip
            run = run_words(d)
            out.append(f'<a class="ev" href="{e(S.REPO_URL)}/tree/{e(S.LINK_REF)}/{e(d)}" '
                       f'title="{e(d)}">{e(f"{run}: {said}" if run else said)}</a>')  # fmt: skip
        for path in (p for p in paths_in if len(whole) <= 1 or p not in whole):
            ptrs = [x for x in files[path] if x]
            href = link(path) + (f"#/{ptrs[0]}" if len(ptrs) == 1 else "")
            title = path + (" #/" + ", /".join(ptrs) if ptrs else "")
            out.append(f'<a class="ev" href="{e(href)}" title="{e(title)}">'
                       f"{e(record_words(path, ptrs))}</a>")  # fmt: skip
    return out


def chip(state, word, form=""):
    """A state as a chip: ground ink on its state's ink, an outline when undecided or hollow; amber
    in lesser part notched (cut), a silent red an outline in the red ink (open)."""
    tok = f"{state} {form}".strip()
    return f'<span class="schip {tok}">{e(word)}</span>'


def stacked(heads, rows, titles=None):
    """A ruled table whose cells carry their column's head (data-l), so a phone stacks each row
    as labelled lines instead of hiding columns past the edge. rows: lists of cell html; titles:
    a head's title, by the head."""
    titles = titles or {}

    def th(h):
        title = f' title="{e(titles[h])}"' if h in titles else ""
        return f'<th scope="col"{title}>{e(h)}</th>'

    ths = "".join(th(h) for h in heads)
    trs = "".join(
        "<tr>" + "".join(f'<td data-l="{e(h)}">{c}</td>' for h, c in zip(heads, r, strict=True))
        + "</tr>" for r in rows
    )  # fmt: skip
    return f'<table class="rt stk"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>'


def petals_of(check):
    """The petals whose red names a check (PETAL_CHECKS), by their place in the glyph (p1 to
    p5), so the page lights them with the check's row (words.js)."""
    return " ".join(f"p{i + 1}" for i, p in enumerate(S.V["petals"]) if check in PETAL_CHECKS[p])


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


def formal_facts_html(formal):
    """Machine-checked's recorded facts, inside its disclosure: the tool, the theorem (linked at
    the pin) and the trusted base as the publisher lists it. The scope card is printed at the
    head of the Glyph section (`scope_head_html`)."""
    if formal is None:
        return ""
    if silent(formal):  # nothing stated: said once, not in every fact
        return (
            f'<p class="pvh">Tool, theorem, trusted base: {e(SCOPE_VALUE_WORD["not_stated"])}</p>'
        )
    theorem = formal["theorem"]
    code = (
        f"<code>{e(theorem).replace('.', '.<wbr>')}</code>" if theorem else None
    )  # breaks at a dot
    if theorem and formal["theorem_url"]:
        theorem = f'<a href="{e(formal["theorem_url"])}">{code}</a>'
    elif theorem:
        theorem = code
    lines = (("Tool", e(formal["tool"]) if formal["tool"] else None), ("Theorem", theorem),
             ("Trusted base", e(", ".join(formal["trusted_base"])) if formal["trusted_base"]
              else None))  # fmt: skip
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{v or e(SCOPE_VALUE_WORD['not_stated'])}</dd></div>"
                    for k, v in lines)  # fmt: skip
    return f'<dl class="pf">{facts}</dl>'


def scope_card_html(formal):
    """The scope card (MC-6, amended 2026-11-15): for soundness, zero knowledge and completeness,
    the publisher's bound verbatim and linked, then what it states of the protocol, the verifier
    run and the prover run, each word linked to its first quote. The two cells that ask a
    property of the wrong party print "does not apply". It sets no state."""
    if formal is None:
        return ""

    # each cell carries its column's head (`data-h`): a phone stacks the card, one block a row
    def cell(c, col):
        word = e(SCOPE_VALUE_WORD[c["value"]])
        if c["quotes"]:
            word = f'<a class="sv" href="{e(c["quotes"][0]["url"])}">{word}</a>'
        return f'<td class="{e(c["value"])}" data-h="{e(SCOPE_COL_WORD[col])}">{word}</td>'

    def bound(r):
        b = (formal.get("scope_bounds") or {}).get(r)
        h = f' data-h="{e(SCOPE_BOUND_HEAD)}"'
        if not b:
            return f'<td class="not_stated"{h}>{e(SCOPE_VALUE_WORD["not_stated"])}</td>'
        text = quoted(b["text"])
        if b["quotes"]:
            text = f'<a class="sv" href="{e(b["quotes"][0]["url"])}">{text}</a>'
        return f'<td class="sb"{h}>{text}</td>'

    card = formal["scope_card"]
    heads = f'<th scope="col">{e(SCOPE_BOUND_HEAD)}</th>' + "".join(
        f'<th scope="col">{e(w)}</th>' for w in SCOPE_COL_WORD.values())  # fmt: skip
    body = "".join(
        f'<tr><th scope="row">{e(SCOPE_ROW_WORD[r])}</th>{bound(r)}'
        + "".join(cell(card[r][c], c) for c in SCOPE_COL_WORD) + "</tr>"
        for r in SCOPE_ROW_WORD
    )  # fmt: skip
    return (f'<p class="pvh">{e(SCOPE_CARD_HEAD)}</p>'
            f'<table class="scard"><caption class="sr">Scope card</caption>'
            f'<thead><tr><td><span class="sr">What</span></td>{heads}</tr></thead>'
            f"<tbody>{body}</tbody></table>")  # fmt: skip


def scope_head_html(row):
    """The head of the Glyph section (the paragraph after MC-7, amended 2026-11-16): soundness,
    zero knowledge and completeness, in that order, each with what it means, whether the publisher
    states it or we test it, computed for the row (soundness from Integrity's step, zero knowledge
    from Confidentiality's, completeness from the counted sessions' accepted replies), where it
    is graded and whom it protects; the publisher's stated security, verbatim with its link; then
    the scope card."""
    petal = {p["id"]: p for p in row["glyph"]}

    def stated(pid):
        p = petal[pid]
        silent_ = p["step"] is None or (p["step"] == "red" and p["cause"] == "not_stated")
        return SCOPE_STATED["not_stated" if silent_ else "stated"]

    n = row["honest_accepted"]
    lines = []
    for _, name, means, pid, whom, ours in SCOPE_HEAD:
        head = e(means[0].upper() + means[1:])
        if pid is not None:
            to = f'<a href="{CHECKS_PAGE}#{pid}">{e(PETAL_NAME[pid])}</a>'
            said = (f"{head}: {e(stated(pid))}. {e(SCOPE_GRADED).format(petal=to)} "
                    f"{e(SCOPE_PROTECTS.format(whom=whom))} {e(ours)}")  # fmt: skip
        else:
            tested = e(SCOPE_TESTED.format(n=f"{n:,}").replace(" of ", "\u00a0of\u00a0"))
            run = f'(<a href="{CHECKS_PAGE}#run">{e(CHECK_NAME["run"])} check</a>)'
            more = (f", {counted_words(len(row['incomplete']), 'incomplete session')} not counted"
                    if row["incomplete"] else "")  # fmt: skip
            said = (f"{head}: {tested} {run}{e(more)}. {e(SCOPE_NOT_GRADED)} "
                    f"{e(SCOPE_PROTECTS.format(whom=whom))}")  # fmt: skip
        lines.append((name, said.strip()))
    sec = row.get("security") or {}
    security = ""
    if sec.get("words"):
        src = str(sec.get("source") or "")
        key = src.partition("#")[2]
        url = S.V["systems"][row["system"]].get("sources", {}).get(key) or (
            src if src.startswith("https://") else None)  # fmt: skip
        words = quoted(sec["words"])
        words = f'<a href="{e(url)}">{words}</a>' if url else words
        notion = (row.get("statement") or {}).get("notion") or []
        if notion:  # the publisher's own name for the notion, verbatim (SI-3)
            words += f" {e(NOTION_HEAD)}: " + quote_links(notion)
        security = f"<div><dt>{e(STATED_SECURITY)}</dt><dd>{words}</dd></div>"
    facts = "".join(f"<div><dt>{e(k)}</dt><dd>{v}</dd></div>" for k, v in lines)
    formal = petal["machine_checked"]["formal"]
    return (f'<div class="sgh"><dl class="pf">{facts}{security}</dl>'
            f"{scope_card_html(formal)}</div>")  # fmt: skip


def silent(formal):
    """Whether Machine-checked's recorded facts state nothing at all."""
    return not (formal["tool"] or formal["theorem"] or formal["trusted_base"])


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


def basis_html(p):
    """What a petal rests on, its label first: from our tests, linked to the Fidelity section
    that holds them; from the publisher's documents, and, when a fact the decision read carries a
    note, "as we read them", linked to what that means (GL-5)."""
    if p["basis"] == "test":
        said = f'<a class="df" href="#fidelity">{e(BASIS_WORD["test"])}</a>'
    elif p["basis"] == "statement" and p["reading"]:
        read = e(AS_READ)  # the step's "read as" links to what a reading means (said_html)
        said = f"{e(BASIS_WORD['statement'])}, {read}"
    else:
        said = e(BASIS_WORD[p["basis"]])
    # the label and its words in two spans: in a petal's row a second line hangs under the words
    return f'<span class="k">From</span> <span>{said}</span>'


def counted_words(k, one):
    """A count in words: "1 quote", "16 quotes"."""
    return f"{k:,} {one}" if k == 1 else f"{k:,} {one}s"


def petal_more(p, of=None):
    """What a petal holds beyond its reason: first, in the row, what it rests on (a silent red's
    reason already names the publisher's documents, so it prints this line only when a fact is our
    reading); then, one click away, a native disclosure whose summary names by count what it
    holds (the documents read, the quotes, Machine-checked's scope card, Weights hidden's visible
    list), opening onto them (SI-3, GL-1)."""
    basis = basis_html(p) if not p["sources"] or p["reading"] else ""
    # our tests: said in the row; the publisher's documents: once, at the disclosure's foot, so
    # the same qualifier is not printed under every petal
    foot = f'<p class="pfrom">{basis}</p>' if basis and p["basis"] != "test" else ""
    row = f'<span class="bs">{basis}</span>' if basis and p["basis"] == "test" else ""
    # a silent red: the documents read, counted first (GL-1), then its quotes
    said = [counted_words(len(p["sources"]), "document") + " read"] if p["sources"] else []
    if p["quotes"]:  # the publisher's own words at the pinned commit
        said.append(QUOTES_HEAD.format(n=len(p["quotes"])))
    if p["formal"] is not None and not silent(p["formal"]):
        said.append("tool and theorem")
    if p["forms"]:
        said.append(counted_words(len(p["forms"]), "form"))
    kept = kept_html(of, p["id"]) if of is not None else ""  # `of`: the row
    if kept:
        said.append(counted_words(kept.count('<p class="cn">'), "trial"))
    notes = "".join(f'<p class="cn">{e(n)}</p>' for n in p["notes"])
    if notes:  # GL-10: what the reading rests on, in our words, apart from the quotes
        notes = f'<p class="pvh">{e(READING_HEAD)}</p>{notes}'
        said.append(READING_HEAD.lower())
    if p["visible"]:  # the publisher's "at least" kept with its count
        said.append(("at least " if p["visible_at_least"] else "")
                    + counted_words(len(p["visible"]), "visible value"))  # fmt: skip
    if not said:
        return f'<span class="bs">{basis}</span>' if basis else ""
    # a silent red: the documents read, each linked at the pin (GL-1)
    docs = ", ".join(f'<a href="{e(d["url"])}">{e(d["path"])}</a>' for d in p["sources"])
    docs = f'<p class="pfrom"><span class="k">{e(DOCS_READ)}</span> {docs}</p>' if docs else ""
    body = (quote_links(p["quotes"]) + notes + formal_facts_html(p["formal"]) + forms_html(p["forms"])
            + visible_html(p["visible"], p["visible_at_least"]) + kept + docs + foot)  # fmt: skip
    said = " · ".join(f'<span class="nw">{e(w)}</span>' for w in said)
    owner = f'<span class="sr">, {e(PETAL_NAME[p["id"]])}</span>'
    return f'{row}<details class="more"><summary>{said}{owner}</summary>{body}</details>'


def said_html(p):
    """What a petal rests on, under its step (amended 2026-11-16): "tested by us", "stated", or
    "read as", which links to what a reading means and caps the step (GL-10). A Not stated petal
    has none: its step already says it."""
    if p["cause"] == "not_stated":
        return ""
    word = said_word(p)
    if word == said_word({"basis": "statement", "reading": True}):
        return f'<a class="sd df" href="{CHECKS_PAGE}#reading">{e(word)}</a>'
    return f'<span class="sd">{e(word)}</span>'


def reach_label(formal):
    """Formally verified's stated reach in the scale's words (§3, amended 2026-11-16): what is
    verified, and for a verifier short of Met, its gaps."""
    r = formal["reach"]
    label = REACH_LABEL.get(r, r)
    if r == "verifier_run" and formal["stated_step"] != "green":
        gaps = [REACH_GAP[k] for k, gap in (("base", not formal["trusted_base"]),
                                            ("input", formal["input_code_unverified"] is not False))
                if gap]  # fmt: skip
        label += f", with gaps ({', '.join(gaps)})" if gaps else ""
    return label


STATED_REACH = ("part", "protocol", "protocol_and_statement", "verifier_run")


def scale_html(p):
    """The lines under a petal's step (§3, §4): Confidentiality's step as a scale of what is
    hidden and its architecture fact; Formally verified's stated reach. They set no state."""
    out = []
    if p["id"] == "weights_hidden":
        label = HIDING_LABEL.get(step_key(p["step"], p["cause"]))
        out += [label] if label else []
        out.append(ARCH_SHORT)
    formal = p.get("formal")
    if p["id"] == "machine_checked" and formal and formal["reach"] in STATED_REACH:
        out.append(REACH_STATED.format(label=reach_label(formal)))
    return "".join(f'<span class="psc">{e(w)}</span>' for w in out)


def next_html(p):
    """A petal's next step (GL-11, amended 2026-11-16), from the board: the step above and what
    the row lacks for it, then who acts; for a hollow petal what decides it; for a failed one its
    repair. It sets nothing."""
    nx = p.get("next")
    if not nx:
        return ""
    needs = "; ".join(n["text"] for n in nx["needs"])
    by = NEXT_BY[tuple(b for b in ("publisher", "us") if any(n["by"] == b for n in nx["needs"]))]
    if nx["to"] is not None:
        head = NEXT_HEAD["up"].format(to=STEP_WORD[nx["to"]])
    elif p["step"] is None:
        head = NEXT_HEAD["decide"]
    else:
        head, by = NEXT_HEAD["repair"], ""
    return f'<p class="pnx"><span class="k">{e(head)}:</span> {e(needs)}.{" " + e(by) if by else ""}</p>'


def extra_html(p, row):
    """A petal's lines after its next step, each printed and setting nothing: Confidentiality's
    architecture (§4: the publisher's words, linked to the line they cite); for Formally verified,
    which verifier the theorem is about (§3); Trust assumptions' Q12 line."""
    st = row.get("statement") or {}
    if p["id"] == "weights_hidden":
        fact = st.get("architecture_visible")
        said = next((r["said"] for r in st.get("rows") or () if r["id"] == "architecture"), None)
        url = said[0]["url"] if said else None
        words = e(f"{fact}, as the publisher states") if fact else e(ARCH_NO_FACT)
        if fact and url:
            words = f'<a href="{e(url)}">{words}</a>'
        return f'<p class="pxl">{e(ARCH_SHORT)} ({words}). {e(ARCH_LONG)}</p>'
    named = st.get("verifiers") or {}
    if p["id"] == "machine_checked" and named.get("stated") and named.get("run") and (
            named["stated"] != named["run"]):  # fmt: skip
        return f'<p class="pxl">{e(VERIFIER_LINE.format(**named))}</p>'
    if p["id"] == "no_trusted_party":
        return "".join(f'<p class="pxl">{e(w)}</p>' for _, w in PETAL_MORE["no_trusted_party"])
    return ""


def glyph_html(row):
    """The glyph once, large, as the heads of the petals' table: each arm is its petal's name on
    the ink of its state (never its state word: the ink says it, and the chip beside it), on one
    stem, its plain sentence in its title, with its field term under it; then the step in words
    (a hollow petal's cause in the chip's title), what it rests on and its scale; then the plain
    sentence, the reason, the next step, the petal's other lines, and what it holds besides
    (`petal_more`). An arm, its row and the checks its red names light together."""
    trs = []
    for i, p in enumerate(row["glyph"]):
        tok = f"{p['state']} {p['form']}".strip()
        data = f' data-step="{e(p["step"] or "none")}"'
        state = chip(p["state"], petal_step(p), p["form"])
        if p["cause"] is not None:  # the reason says it; the chip links its definition
            data += f' data-cause="{e(p["cause"])}"'
            state = (f'<a class="cc" href="{CHECKS_PAGE}#cause-{e(p["cause"])}" '
                     f'title="{e(CAUSE_WORD[p["cause"]])}">{state}</a>')  # fmt: skip
        plain = PETAL_PLAIN[p["id"]]
        trs.append(
            f'<tr class="pt {tok}"><th scope="row">'
            f'<a class="sl s{i + 1} {tok}"{data} href="{CHECKS_PAGE}#{p["id"]}" data-k="p{i + 1}" '
            f'title="{e(plain)}"><span>{e(PETAL_NAME[p["id"]])}</span></a>'
            f'<span class="pst">{e(PETAL_TERM[p["id"]])}</span></th>'
            f'<td class="cst">{state}{said_html(p)}{scale_html(p)}</td>'
            f'<td class="prs"><span class="ppl">{e(plain)}</span>'
            f'<span class="rs">{e(p["reason"])}</span>{next_html(p)}{extra_html(p, row)}'
            f"{petal_more(p, row)}</td></tr>"
        )
    return (scope_head_html(row) + '<div class="checks"><table class="rt ckt gbig"><caption '
            f'class="sr">Petal, state, reason</caption><tbody>{"".join(trs)}</tbody></table></div>')  # fmt: skip


# RFC-0018 SI-3 (amended 2026-11-15): the Statement block's rows, in the view's order
STATEMENT_HEAD = {"commit_record": "From our commit record", "request": "From the request",
                  "proof": "From the proof", "decoding": "Decoding rule",
                  "unchecked": "Checked by no call", "architecture": "Architecture"}  # fmt: skip


def statement_given(row, st, rid):  # noqa: PLR0911 (one return per row)
    """What the verifier the row runs is given, for one row of the Statement block, from the
    records: the files `commit` wrote (the manifests), the request's sizes, the proof's files
    the verifier reads (`system.yaml`), the level's decoding rule; the architecture's word."""
    req = S.V["request"]
    if rid == "commit_record":
        files = ", ".join(st["verifier_files"])
        return ("the commitment" + (f" and the files <code>commit</code> wrote: <code>{e(files)}"
                                    "</code>" if files else ""))  # fmt: skip
    if rid == "request":
        said = f"the prompt, {st['prompt_tokens']:,} token ids"
        if st["reply"] == "record":
            said += f", and the {st['output_tokens']:,}-token reply from our record"
        return e(said)
    if rid == "proof":
        kinds = ", ".join(f"{k['count']:,} × {k['kind']}" if k["count"] > 1 else k["kind"]
                          for k in st["proof_read"])  # fmt: skip
        said = (f"{st['proof_files']:,} {'file' if st['proof_files'] == 1 else 'files'}: "
                f"<code>{e(kinds)}</code>") if kinds else "its files"  # fmt: skip
        if st["reply"] == "proof":
            said += "; the reply is read from the proof, not given"
        if st.get("proof_caveat"):
            said += f"; {e(st['proof_caveat'])}"
        return said
    if rid == "decoding":
        return e(f"{req['decoding']}, at every reply position")
    if rid == "architecture":
        if st["architecture_visible"]:
            return e(f"visible: {st['architecture_visible']}")
        return e(SCOPE_VALUE_WORD["not_stated"])
    return ""


def statement_html(row):
    """SI-3 (amended 2026-11-15): what the verifier the row runs is given, and from where (our
    commit record, the request, the proof), the decoding rule, what no call checks and what of
    the architecture a proof shows. Each row: what the records show is given, then the claim
    card's words on it, each linked to the publisher's line, or "not stated". It sets no state."""
    st = row.get("statement")
    if not st:
        return f'<p class="none">{e(SCOPE_VALUE_WORD["not_stated"])}</p>'
    rows = []
    for r in st["rows"]:
        said = (f'<span class="na">{e(SCOPE_VALUE_WORD["not_stated"])}</span>' if r["said"] is None
                else "".join(f'<p class="stc">{e(q["text"])} <a href="{e(q["url"])}" '
                             f'title="{e(q["field"])}">source</a></p>' for q in r["said"]))  # fmt: skip
        rows.append([e(STATEMENT_HEAD[r["id"]]), statement_given(row, st, r["id"]), said])
    card = (f' <a href="{e(link(st["card"]))}" title="{e(st["card"])}">claim card</a>'
            if st["card"] else "")  # fmt: skip
    fix = st.get("erratum")
    erratum = ""
    if fix:  # the card is kept byte for byte (the runs record its digest): said beside its link
        fields = " and ".join(f"<code>{e(f)}</code>" for f in fix["fields"])
        q = fix["level_1"]
        erratum = (f'<p class="cn">{CARD_ERRATUM.format(fields=fields, says=e(fix["says"]))} '
                   f'<a class="qt" href="{e(q["url"])}">\u201c{e(q["quote"])}\u201d</a></p>')  # fmt: skip
    lead = (f'<p class="rb"><span class="k">Verifier</span> <span><code>{e(st["program"])}</code>; '
            f"each row's right column is the{card}, which copies the publisher's documents at "
            f"the row's commit</span></p>{erratum}")  # fmt: skip
    return lead + stacked(["What", "Given", "Claim card"], rows)


NOTE_SHORT = 48  # a check's note longer than this, in characters, is left to its records


def note_parts(note):
    """A check's note as (the internal id that leads it, "P1" or a run's request, or ""; its
    words)."""
    head, sep, tail = note.partition(": ")
    if not (sep and " " not in head):
        return "", note
    return head, tail


def note_gist(note):
    """A check's note as its row prints it: its words without the id that leads them, and only
    when they are short; None otherwise."""
    words = note_parts(note)[1]
    return words if len(words) <= NOTE_SHORT else None


def checks_html(row):
    """The six checks, the entry gate: one ruled row per check: name, state, cause (a column
    only where a check has one, a short note under it), and its records one click away, a note
    too long for the cause in full with them; a note's leading id stands in its title. A check
    names the petals its failure turns red."""
    caused = any(c["cause"] or c.get("note") for c in row["checks"])
    trs = []
    for c in row["checks"]:
        cause, note = "", c.get("note")
        if c["cause"]:  # in words, the stored cause in the title
            cause = (f'<a class="cw df" href="{CHECKS_PAGE}#cause-{e(c["cause"].replace(" ", "-"))}" '
                     f'title="{e(c["cause"])}">{e(CHECK_CAUSE_WORD[c["cause"]])}</a>')  # fmt: skip
        gist = note_gist(note) if note else None
        head = e(note_parts(note)[0]) if note else ""
        at = f' title="{head}"' if head else ""  # the id the note opens with, out of the words
        if gist:
            cause += f'<span class="cn"{at}>{quoted(gist)}</span>'
        # in full with the records, only when too long for the cause
        full = f'<p class="cn"{at}>{quoted(note_parts(note)[1])}</p>' if note and not gist else ""
        links = evidence_links(c["evidence"])  # counted as printed: a file's entries are one link
        recs = counted_words(len(links), "record") if links else "note"
        owner = f'<span class="sr">, {e(CHECK_NAME[c["id"]])}</span>'
        ran = trials_html(c.get("trials") or ()) + kept_html(row, c["id"])
        more = (f'<details class="more"><summary>{e(recs)}{owner}</summary>{full}{ran}'
                f"{''.join(links)}</details>"
                if c["evidence"] or full else "")  # fmt: skip
        to = petals_of(c["id"])
        to = f' data-to="{to}"' if to else ""
        trs.append(
            f'<tr class="ck {c["state"]}" id="ck-{c["id"]}"><th scope="row">'
            f'<a href="{CHECKS_PAGE}#{c["id"]}"{to} title="{e(filled(CHECK_PLAIN[c["id"]]))}">'
            f"{e(CHECK_NAME[c['id']])}</a></th>"
            f'<td class="cst">{chip(c["state"], STATE_WORD[c["state"]])}</td>'
            + (f"<td>{cause}</td>" if caused else "")
            + f"<td>{more}</td></tr>"
        )
    cause_th = '<th scope="col">Cause</th>' if caused else ""
    return (f'<p class="rd">{e(CHECKS_LEAD)}</p>'
            '<table class="rt ckt cks"><thead><tr><th scope="col">Check</th><th scope="col">'
            f'State</th>{cause_th}<th scope="col">Evidence</th></tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table>{level_statement_html(row)}')  # fmt: skip


def trials_html(trials):
    """What a check's counted trials sent (RFC-0018 CH-1c), from the board: per control and
    position, the trials, the inputs they sent and how many were refused, so three trials of one
    changed input never read as three inputs."""
    if not trials:
        return ""

    def one(t):
        n, inputs = t["trials"], t["inputs"]
        sent = ("the same input each time" if inputs == 1 and n > 1
                else "a new input each time" if inputs == n
                else f"{inputs:,} inputs")  # fmt: skip
        none, by = t.get("no_proof", 0), t["refused"] - t.get("no_proof", 0)
        how = [f"in {none:,}, {TRIAL_NO_PROOF}"] if none else []
        how += [f"{by:,} {TRIAL_REFUSED}"] if by or not none else []
        return f"{TRIAL_WHAT[(t['control'], t['position'])]}: {n:,} trials, {sent}; " \
            + ", ".join(how)  # fmt: skip

    words = "; ".join(one(t) for t in trials)
    return f'<p class="cn"><span class="k">{e(TRIALS_HEAD)}</span> {e(words)}</p>'


TRIAL_OTHER = (
    "machine_checked"  # the view's place of another verifier's trial (iproofs.site.system)
)


def kept_html(row, place):
    """The row's stored verifier trials printed at `place` (a check's id, or Machine-checked),
    each from its record: what its changed calls did and how many the verifier refused, beside
    its honest calls accepted, with its record. A trial sets no state (RFC-0008 §Verifier
    trials). Only a trial of another of the publisher's verifiers prints its times: they are what
    no counted session took (the Verifying line); the row's own verifier is timed there."""
    out = []
    for t in row.get("trials_kept") or ():
        if t["place"] != place:
            continue
        said = [f"{t['accepted']:,} of {counted_words(t['honest'], 'honest proof')} accepted"
                + (f" ({t['counted']:,} from counted sessions)" if t["counted"] < t["honest"]
                   else "")]  # fmt: skip
        said += [f"{KEPT_CHANGE.get(k, k)}: {t['changed_rejected']:,} of {t['changed']:,} refused"
                 for k in t["changes"]]  # fmt: skip
        if place == TRIAL_OTHER and t["seconds_min"] is not None:
            lo, hi = f"{t['seconds_min']:,.0f}", f"{t['seconds_max']:,.0f}"
            span = lo if lo == hi else f"{lo} to {hi}"
            said.append(f"{span}\u00a0s per proof, {KEPT_TIME}, n\u00a0=\u00a0"
                        f"{t['honest'] - t['no_verdict']:,}")  # fmt: skip
        who = f"{t['verifier'][0].upper()}{t['verifier'][1:]}, " if place == TRIAL_OTHER else ""
        means = " ".join(KEPT_MEANS[k] for k in t["changes"]
                         if k in KEPT_MEANS and t["changed_rejected"] == t["changed"])  # fmt: skip
        words = f"{who}{'; '.join(said)}." + (f" {means}" if means else "")
        rec = (
            f'<a class="ev" href="{e(link(t["record"]))}" title="{e(t["record"])}">trial record</a>'
        )
        out.append(f'<p class="cn"><span class="k">{e(KEPT_HEAD)}, {e(KEPT_SETS)}</span> '
                   f"{e(words)} {rec}</p>")  # fmt: skip
    return "".join(out)


def level_statement_html(row):
    """SI-4a: whether the publisher states Level 1's statement at the pin, with its quotes one
    click away; "read as", linked to what that means, when the fact is our reading."""
    st = row.get("level_statement")
    if st is None:
        return ""
    if st["reading"]:
        said = (f'<a class="df" href="{CHECKS_PAGE}#reading">{e(READ_AS.capitalize())}</a> '
                f"{e(STATEMENT_WORD['read'])}")  # fmt: skip
    else:
        said = e(STATEMENT_WORD["stated" if st["stated"] else "not"])
    quotes = (f'<details class="more"><summary>{e(QUOTES_HEAD.format(n=len(st["quotes"])))}'
              f'</summary>{quote_links(st["quotes"])}</details>' if st["quotes"] else "")  # fmt: skip
    head = f'<span class="k">{e(LEVEL_STATEMENT_HEAD)}</span>'
    return f'<p class="rb">{head} <span>{said}</span></p>{quotes}'


def plain(v, unit, record, said="", missing="none"):
    """A number the board stores without labels (a session's value, a mean prefix), in its
    column's unit, the labels its block knows (`said`: scope, n) and its record in its title;
    `missing` in its place when there is none."""
    if v is None:
        return f'<span class="na">{e(missing)}</span>'
    n, u = (sig(v), unit) if unit in ("tokens", "positions") else number(v, unit)
    title = f"{said}; record: {record}" if said else f"record: {record}"
    return (f'<span class="fig" title="{e(title)}"><span class="n">{e(n)}</span>'
            f'<span class="u">{e(u)}</span></span>')  # fmt: skip


def steady_cell(s, at, said):
    """A session's steady state in one cell (CO-3): its m, or "none" with the cause under it."""
    cell = plain(s["m"], GPU_S, f"{at}/m", said)
    if not s["steady"]:
        cell += f'<span class="sub">{e(s["cause"] or "no")}</span>'
    return cell


RULE_ID = re.compile(r"\b[A-Z]{2}-\d+[a-z]?\b")  # a rule's id in words ("SE-3a")


def whole_ids(text):
    """Escaped words with each rule id kept on one line (a line never breaks at its hyphen)."""
    return RULE_ID.sub(lambda m: f'<span class="nw">{m[0]}</span>', text)


def replaced_why(s):
    """A replaced session's reason (SE-3a) without its closing clause, where that clause names
    only what the row's Slot and Replaced by cells print ("; slot 1 counts <its run>")."""
    tail = f"; slot {s['slot']} counts {s['replaced_by']}"
    return s["cause"].removesuffix(tail)


def sessions_html(row):
    """SE-3: each counted session (slot, run, m or why there is none, session cost per reply),
    then every incomplete session with its exit code and last line (AGENTS.md rule 5), then each
    replaced session (SE-3a), its reason said once over the table where the sessions share it,
    then each run RFC-0014 keeps out of the release with its reasons (SE-3b)."""
    rec = row["record"]
    gen = any(s.get("generation_gpu_seconds_per_reply") is not None for s in row["sessions"])
    # release groups: a column where the sessions differ, else said once over the table
    groups = {len(s["groups"]) for s in row["sessions"]}
    steady, whole = (f"scope: {SCOPE_WORD[k]}" for k in ("prove.steady", "whole_wall"))

    def cells(k, s):
        at = f"{rec}/sessions/{k}"
        g = s.get("generation_gpu_seconds_per_reply")  # CO-7: the generation phase, part of the
        return [  # whole session (and of m, where the session has one)
            str(s["slot"]),
            run_link(row, s["run_id"]),
            steady_cell(s, at, steady),
            plain(s["session"], GPU_S, f"{at}/session", whole),
            *([plain(g, GPU_S, f"{at}/generation_gpu_seconds_per_reply", whole)] if gen else []),
            *([f"{len(s['groups']):,}"] if len(groups) > 1 else []),
        ]

    of_gen = f"{OF_WHICH} {PART_WORD['generation']}".capitalize()
    heads = ["Slot", "Run", M_COL, "Session", *([of_gen] if gen else []),
             *(["Release groups"] if len(groups) > 1 else [])]  # fmt: skip
    once = (f'<p class="rb"><span class="k">Release groups</span> {next(iter(groups)):,} in each '
            "session</p>" if len(groups) == 1 else "")  # fmt: skip
    # D1: what a session, a slot and a whole session are, each linked to its definition, once
    lead = (
        f'<p class="rd">Each {term("session", "Session")} is one run from a cold start on '
        f"one {term('slot', 'Slot')}'s prompts, and one counts per slot. Session: its GPU "
        f"time per reply over the {term('whole session', 'Whole session')}. {e(M_COL)}: the "
        f"same after its first release group, in {term('steady state', 'Steady state')}.</p>"
    )
    out = (lead + once + stacked(heads, [cells(k, s) for k, s in enumerate(row["sessions"])],
                                 {M_COL: M_NAME})
           if row["sessions"] else '<p class="none">No counted session.</p>')  # fmt: skip
    if row["incomplete"]:
        rows = [
            [
                str(s["slot"]) if s["slot"] is not None else "",
                run_link(row, s["run_id"]),
                e(s["exit_code"]) if s["exit_code"] is not None else "none",
                e(s["step"] or ""),
                e(s["cause"]),
                f"<code>{e(s['last_line'] or '')}</code>",
            ]
            for s in row["incomplete"]
        ]
        out += '<h3 class="sub-h">Incomplete sessions</h3>' + stacked(
            ["Slot", "Run", "Exit code", "Step", "Cause", "Last line"], rows
        )
    if row.get("replaced"):  # SE-3a: listed with why, in no figure and no check
        whys = [replaced_why(s) for s in row["replaced"]]
        once = len(set(whys)) == 1
        rows = [
            [
                str(s["slot"]) if s["slot"] is not None else "",
                run_link(row, s["run_id"]),
                run_link(row, s["replaced_by"]),
                *([] if once else [e(why)]),
            ]
            for s, why in zip(row["replaced"], whys, strict=True)
        ]
        lead = (
            f'<p class="rb"><span class="k">Why</span> <span>{whole_ids(e(whys[0]))}</span></p>'
            if once
            else ""
        )
        out += (
            '<h3 class="sub-h">Replaced sessions</h3>'
            + lead
            + stacked(["Slot", "Run", "Replaced by", *([] if once else ["Why"])], rows)
        )
    if row.get("ineligible"):  # SE-3b: kept out by RFC-0014, in no figure and no check
        rows = [
            [
                str(s["slot"]) if s["slot"] is not None else "",
                run_link(row, s["run_id"]),
                e("; ".join(s["words"])),
            ]
            for s in row["ineligible"]
        ]
        out += '<h3 class="sub-h">Ineligible sessions</h3>' + stacked(["Slot", "Run", "Why"], rows)
    return out


def kept(*pieces):
    """A line's pieces (markup), each kept whole: a line too long breaks between two, the dot that
    parts them opening the next line, never left at a line's end."""
    head, *rest = pieces
    return f'<span class="nw">{head}</span>' + "".join(
        f' <span class="nw">\u00b7\u00a0{p}</span>' for p in rest
    )


# CO-7: a GPU time's two parts, where the system generates in a phase of its own, drawn in this
# order (the part that is not generation first, in paper)
GPU_PARTS = {
    "steady_gpu_seconds_per_reply": (("proving", "steady_proving_gpu_seconds_per_reply"),
                                     ("generation", "steady_generation_gpu_seconds_per_reply")),
    "session_gpu_seconds_per_reply": (
        ("commit_and_proving", "session_commit_and_proving_gpu_seconds_per_reply"),
        ("generation", "session_generation_gpu_seconds_per_reply")),
}  # fmt: skip


def cost_sub(f, n, head="", own=False):
    """The line under a Cost figure, where the block's Proving line says the whole sessions and
    their n once (`n`, the counted sessions): nothing for a figure that shares both, else what
    differs (a steady or a verify scope, another n), a scope its `head` already names left out
    ("Verify time" over no "verify"). A figure the Proving line does not cover (`own`: verify
    time, proof size) prints its n even where it is the block's. None (the figure's own line)
    with no n."""
    if n is None or not has(f):
        return None
    short = SCOPE_SHORT[f["scope"]]
    said = [short] if short not in ("", "session") and short not in head.lower() else []
    count = f["n"] if f["n"] is not None else n
    if own or count != n:
        said.append(f"n\u00a0=\u00a0{count}")
    if spread := range_words(f):  # AGENTS.md rule 5: a mean prints its range
        said.append(spread)
    return SEP.join(said)


def serving_fig(f, line=True):
    """The serving baseline's figure: timed at full load (CO-4), so its title names that scope;
    with the Serving line above it (`line`) nothing under it, else "full load"."""
    if not has(f):
        return fig_html(f)
    return fig_html({**f, "scope": "serving"}, sub=BARE if line else FULL_LOAD_WORD)


def gpu_parts(figs, key):
    """A GPU time's two parts (CO-7) as (part word, figure), where the board holds both; else
    None."""
    parts = [(w, figs.get(k)) for w, k in GPU_PARTS.get(key, ())]
    return parts if parts and all(has(p) for _, p in parts) else None


def cost_bars(row, drawn):
    """CO-7 drawn: a GPU time per reply that splits in two (the steady m or the whole session,
    where the system generates in a phase of its own) as one bar of its two parts, on one scale,
    this row's own (one model). Each line: its name, its bar, its labelled figure and its parts'
    figures. A GPU time with no parts is a figure of the sheet under the bars (`cost_html`): a
    bar of one part says no more than its figure. `drawn`: (name, figure, key, title)."""
    figs, n = row["figures"], counted(row)
    if not drawn:
        return ""
    top = max(f["value"] for _, f, _, _ in drawn)
    lines = []
    for name, f, key, title in drawn:
        parts = gpu_parts(figs, key)
        segs = [(p["value"], c) for (_, p), c in zip(parts, ("bp", "bg"), strict=True)]
        # each part under its whole, by its name alone (CO-7)
        cps = "".join(f'<span class="cpt {c}"><span class="cpl">{e(PART_WORD[w])}</span>'
                      f"{fig_html(p, n, sub=cost_sub(p, n))}</span>"
                      for (w, p), c in zip(parts, ("pp", "pg"), strict=True))  # fmt: skip
        bar = hbar(segs, top, h=14, cls="hb")
        named = f' title="{e(title)}"' if title else ""
        fig = fig_html(f, n, sub=cost_sub(f, n, name))
        lines.append(f'<div class="cl"><span class="cln"{named}>{e(beside_unit(name))}</span>{bar}'
                     f'<span class="clf">{fig}</span><span class="cps">{cps}</span></div>')  # fmt: skip
    return f'<div class="cbars">{"".join(lines)}</div>'


def low_first(name):
    """A label inside a list: its first letter lower case, unless it opens a capitalised word
    ("GPU time" stays)."""
    return name if name[1:2].isupper() else name[:1].lower() + name[1:]


def missing_html(missing):
    """The figures the board holds no value for, named once per reason, in the board's words."""
    return "".join(
        f'<p class="cnone">{e(", ".join(k if i == 0 else low_first(k) for i, k in enumerate(names)))}'
        f": none, {e(why)}</p>"
        for why, names in missing.items()
    )  # fmt: skip


def gpus_words(row):
    """The GPUs a row's counted sessions bound (SE-2, the sessions' `gpus`): "1 × H200"; where
    the rented machine held more, as its manifests record (SE-2: printed, not counted), "2 × H200
    rented, 1 bound and priced"."""
    bound = {s.get("gpus") for s in row["sessions"]}
    if not bound or not all(bound):
        return "GPUs not recorded"
    said = " or ".join(f"{g:,}" for g in sorted(bound))
    seen = (row.get("machine") or {}).get("gpus_visible") or []
    if seen and max(seen) > max(bound):
        rented = " or ".join(f"{g:,}" for g in seen)
        return f"{rented} × H200 rented, {said} bound and priced"
    return f"{said} × H200"


def words_or(values):
    """A record's values in words: one, or each joined by "or" where the sessions differ."""
    return " or ".join(str(v) for v in values)


HOST_WORD = {"same_as_prover": "the prover's host"}  # a manifest's `verifier_host`, in words


def verifying_html(row):
    """The Verifying line (CO-6's verify time, amended 2026-11-15): the program the row's verify
    time timed, on what (the verifier's CPUs and their model, the host, whether a GPU was
    visible to it, from the counted sessions' manifests and traces), the range of the sessions'
    means and n; then each of the publisher's verifiers no session timed."""
    st, mc = row.get("statement"), row.get("machine")
    f = row["figures"]["verify_seconds_per_reply"]
    if not st or not has(f):
        return ""
    said = [f"<code>{e(st['program'])}</code>"]
    if mc and mc["verifier_cpus"] and mc["cpu_model"]:
        cpus = words_or(mc["verifier_cpus"])
        host = words_or(HOST_WORD.get(h, h) for h in mc["verifier_host"])
        on = f"on {cpus} CPUs of an {words_or(mc['cpu_model'])}" + (f", {host}" if host else "")
        seen = mc["verify_gpu_visible"]  # from the verify traces
        on += {(True,): ", its GPU visible", (False,): ", no GPU visible"}.get(
            tuple(seen), ", a GPU visible in some sessions" if seen else ""
        )
        said.append(e(on))
    spread = range_words(f)
    count = f["n"] if f["n"] is not None else counted(row)
    timed = (f"{spread}, the {count:,} sessions' means" if spread
             else fig_words(f)) + f", n\u00a0=\u00a0{count:,}"  # fmt: skip
    rel = (S.V["release"] or {}).get("id")
    untimed = "".join(f" \u00b7 {e(u)}: not timed" + (f" in {e(rel)}'s sessions" if rel else "")
                      + (f" (a trial under {PETAL_NAME['machine_checked']})" if any(
                          t["place"] == TRIAL_OTHER and u.lower() in t["verifier"].lower()
                          for t in row.get("trials_kept") or ()) else "")
                      for u in st["untimed"])  # fmt: skip
    return (f'<p class="rb"><span class="k">Verifying</span> <span>{" ".join(said)}; '
            f"{e(timed)}{untimed}</span></p>")  # fmt: skip


def proved_html(row):
    """The precision the row proves (its workload record), beside the release serving runs (the
    Serving line above it): the copy, its words, its weight bits and how they were found, and
    where the bits cover part of the weights, so."""
    p = row.get("precision")
    if not p:
        return ""
    said = (f'<a href="{e(link(p["record"]))}" title="{e(p["record"])}">{e(p["proved"])}</a>'
            + (f" ({e(p['proved_words'])})" if p["proved_words"] else ""))  # fmt: skip
    if isinstance(p["bits"], int | float):
        n = f"{p['bits']:,}" if float(p["bits"]).is_integer() else sig(p["bits"], 3)
        how = BASIS_BITS.get(p["bits_basis"], p["bits_basis"] or "")
        if p["bits_source"]:
            how = f'<a href="{e(p["bits_source"])}">{e(how)}</a>'
        part = " for part of the weights" if p["bits_covers"] == "part" else ""
        said += f", {e(n)} bits per weight{e(part)}, {how}"
    return f'<p class="rb"><span class="k">Proved</span> <span>{said}</span></p>'


def generation_html(row):
    """CO-7 (amended 2026-11-15): where the system generates in a phase of its own, what
    generates (the facts file, with the publisher's words linked) and that phase's GPU-seconds
    per reply token, with its range and n."""
    gen = S.V["systems"][row["system"]].get("generation")
    f = row["figures"].get("generation_gpu_seconds_per_reply_token")
    if not gen or not has(f):
        return ""
    quote = f'<a class="qt" href="{e(gen["url"])}">\u201c{e(gen["quote"])}\u201d</a>'
    sub = SEP.join(w for w in (range_words(f), f"n\u00a0=\u00a0{f['n']}" if f["n"] else "") if w)
    return (f'<p class="rb"><span class="k">Generation</span> <span>{e(gen["words"])} '
            f"{quote}; {fig_html(f, sub=sub)}</span></p>")  # fmt: skip


def size_html(row):
    """What Proof size counts: every file a proof is released as, by kind, from the sessions'
    manifests (a size is the bytes as written, JSON text where the files are JSON)."""
    st = row.get("statement")
    if not st or not st["proof_parts_count"] or not has(row["figures"]["proof_bytes_per_reply"]):
        return ""
    kinds = ", ".join(f"{k['count']:,} × {k['kind']}" if k["count"] > 1 else k["kind"]
                      for k in st["proof_parts"])  # fmt: skip
    n = st["proof_parts_count"]
    return (f'<p class="rb"><span class="k">Proof size</span> <span>the bytes of the {n:,} '
            f"{'file' if n == 1 else 'files'} a proof is released as, as written: "
            f"<code>{e(kinds)}</code></span></p>")  # fmt: skip


def ladder_html(rung):
    """CO-4: the serving ladder, each concurrency's rate, the full-load rung marked; behind a
    disclosure, under the Serving line."""
    b = rung["baseline"] or {}
    ladder = [c for c in b.get("ladder") or [] if c["rate"] is not None]
    if not ladder:
        return ""
    rows = [[f"{c['concurrency']:,}" + (" (full load)" if c["concurrency"] == b["concurrency"]
                                       else ""),
             fig_html(c["rate"], sub=BARE)] for c in ladder]  # fmt: skip
    return (
        f'<details class="more"><summary>serving ladder, {len(ladder):,} concurrencies'
        "</summary>" + stacked(["Concurrent requests", "Rate"], rows) + "</details>"
    )


# a stored tier's glossary entry, where its words link (D2: they say whose runs these are)
TIER_TERM = {"reported": "Evidence: our runs only, not rerun by anyone else"}


def how_html(row):
    """B5 at the Cost section's head: how the headline is computed, in one sentence (the same as
    opens its title), its scope's words linked to their definition, then the rule."""
    said = e(how_computed(row)).replace(
        "whole sessions", term("whole sessions", "Whole session"), 1
    )
    return (
        f'<p class="rd">{said} <a class="df" href="{CHECKS_PAGE}#multiple">{e(HOW_RULE)}</a>.</p>'
    )


def reply_tokens_html(row):
    """CO-8 (adopted 2026-11-16): reply tokens per GPU-second, once, beside the session GPU time:
    the figure with its unit, its range, n in whole sessions and the GPUs bound, then what the
    records do not time apart. It depends on the GPU, so it prints nowhere above this depth."""
    f = row["figures"].get("session_reply_tokens_per_gpu_second")
    if not has(f):
        return ""
    st = f.get("stats") or {}
    count = f["n"] if f["n"] is not None else counted(row)
    said = []
    if (st.get("n") or 0) > 1 and st.get("min") is not None and st.get("max") is not None:
        lo, hi = (number(st[k], f["unit"])[0] for k in ("min", "max"))
        said.append(e(f"{lo} to {hi}"))
    said.append(f"n\u00a0=\u00a0{count:,} " + term("whole sessions", "Whole session"))
    bound = sorted({s.get("gpus") for s in row["sessions"] if s.get("gpus")})
    if bound:  # the GPUs the sessions bound, the ones its GPU-seconds count (SE-2)
        said.append(e(f"{' or '.join(f'{g:,}' for g in bound)} × {gpu_name(row)}"))
    head = term(REPLY_TOKENS_HEAD, REPLY_TOKENS_HEAD)
    return (f'<p class="rb rtk"><span class="k">{head}</span> <span>{fig_html(f, count, sub=BARE)} '
            f"({', '.join(said)}). {e(NOT_TIMED_APART)}</span></p>")  # fmt: skip


def evidence_words(named):
    """The evidence tier of a block's figures in words (TIER_WORD, AGENTS.md rule 2), once for the
    block where they share one; else each tier with the figures that carry it. `named`: (name,
    figure) pairs, each figure present."""
    tiers: dict[str, list[str]] = {}
    for k, f in named:
        tiers.setdefault(TIER_WORD[f["tier"]], []).append(beside_unit(k))

    def linked(w):
        tier = next((k for k, v in TIER_WORD.items() if v == w), None)
        return term(w, TIER_TERM[tier]) if tier in TIER_TERM else e(w)

    if len(tiers) == 1:
        return linked(next(iter(tiers)))
    return "; ".join(f"{linked(w)}: {e(', '.join(low_first(k) for k in ks))}"
                     for w, ks in tiers.items())  # fmt: skip


# CO-7 (amended 2026-11-15): the session less its commit call and its generation phase
PROVING_REST = "Proving GPU time per reply"


def cost_html(row):
    """The cost parts (CO-1 to CO-5), each figure as the board stores it (the figures block above
    prints the cost alone): how the model was served; once what the proving figures are over (the
    GPUs the counted sessions bound, SE-2, and the whole sessions, n), a figure that differs
    saying so under it (`cost_sub`); once the evidence of the block's figures (the tier, which
    their titles also carry: DEPTH law 3). Then a GPU time with two parts drawn as a bar
    (`cost_bars`), a sheet of the other figures, and, once, each figure the board holds no value
    for with the board's reason (a steady figure on a row with no steady state: NO_STEADY_WORD).
    Verify time and proof size close the sheet, each with its own scope and n under it (SI-8): the
    Proving line names the proving's GPUs and sessions, not theirs."""
    rung = rung_of(row)
    figs, b, n = row["figures"], rung["baseline"] or {}, counted(row)
    price = S.V["price"]
    _, _, key = lead_figure(row)
    # the multiple the band does not print: a steady row's session one, beside the session cost
    # (CO-5's label is the band's, for a row's one figure; this one's scope is in its title)
    other = ((f"Session {FIGURE_NAME['multiple'].lower()}", figs["session_multiple"], n)
             if key == "multiple" else (f"Steady {FIGURE_NAME['multiple'].lower()}",
                                        figs["multiple"], n))  # fmt: skip
    gpu = [("Serving GPU time per reply", b.get("gpu_seconds_per_reply"), None, None),
           (M_HEAD, figs["steady_gpu_seconds_per_reply"], n, "steady_gpu_seconds_per_reply"),
           ("Session GPU time per reply", figs["session_gpu_seconds_per_reply"], n,
            "session_gpu_seconds_per_reply"),
           # CO-7 (amended 2026-11-15): the session in its timed calls
           ("Commit GPU time per reply", figs.get("session_commit_gpu_seconds_per_reply"), n,
            None),
           (PROVING_REST, figs.get("session_proving_gpu_seconds_per_reply"), n, None)]  # fmt: skip
    # a GPU time with two parts is drawn (its head's title its full name), the others are cells
    drawn = [(k, f, key, M_NAME if k == M_HEAD else "") for k, f, _, key in gpu
             if has(f) and gpu_parts(figs, key)]  # fmt: skip
    sheet = [*((k, f, count) for k, f, count, key in gpu if not any(f is d[1] for d in drawn)),
             other, ("Steady cost per reply", figs["steady_usd_per_reply"], n),
             ("Session cost per reply", figs["session_usd_per_reply"], n),
             ("Serving cost per reply", b.get("usd_per_reply"), None),
             (FIGURE_NAME["check-time"], figs["verify_seconds_per_reply"], n),
             (FIGURE_NAME["proof-size"], figs["proof_bytes_per_reply"], n)]  # fmt: skip
    own = (figs["verify_seconds_per_reply"], figs["proof_bytes_per_reply"])  # their scope and n
    no_steady = not has(figs["multiple"]) and figs["multiple"]["null_reason"] == "not_applicable"
    steady_figs = (figs["multiple"], figs["steady_gpu_seconds_per_reply"],
                   figs["steady_usd_per_reply"])  # fmt: skip
    missing: dict[str, list[str]] = {}
    for k, f, _ in sheet:
        if has(f):
            continue
        why = ("not recorded" if not f else NO_STEADY_WORD
               if no_steady and any(f is g for g in steady_figs) else NULL_WORD[f["null_reason"]])  # fmt: skip
        missing.setdefault(why, []).append(k)
    base = rung["baseline"]
    line = bool(base) and has(base["gpu_seconds_per_reply"])
    rows = [(k, serving_fig(f, line) if count is None and k.startswith("Serving")
             else fig_html(f, count, sub=cost_sub(f, n, k, any(f is o for o in own))))
            for k, f, count in sheet if has(f)]  # fmt: skip
    if price and has(price["usd_per_gpu_hour"]):  # the head says what, the unit per what
        when = f"as of {price['date']}" if price["date"] else None
        rows.append(("H200 price", fig_html(price["usd_per_gpu_hour"], sub=when,
                                            note=f"basis: {price['basis']}")))  # fmt: skip
    else:
        missing.setdefault("not recorded", []).append("Price of one H200 GPU-hour")
    m_title = f' title="{e(M_NAME)}"'
    cells = "".join(f"<div><dt{m_title if k == M_HEAD else ''}>{e(beside_unit(k))}</dt>"
                    f"<dd>{v}</dd></div>" for k, v in rows)  # fmt: skip
    serving = (f'<p class="rb"><span class="k">Serving</span> <span>{e(serving_words(base))}</span>'
               f"</p>{ladder_html(rung)}" if line else "")  # fmt: skip
    whole = e(whole_line(row, n)).replace(
        "whole sessions", term("whole sessions", "Whole session"), 1
    )
    over = (f'<span class="nw">{e(gpus_words(row))},</span> '
            f'<span class="nw">{whole}</span>')  # fmt: skip
    proving = f'<p class="rb"><span class="k">Proving</span> <span>{over}</span></p>' if n else ""
    # the tier of every figure the block prints (the price is the reference file's, not a run's)
    shown = [(k, f) for k, f, _, _ in drawn] + [(k, f) for k, f, _ in sheet if has(f)]
    evidence = (f'<p class="rb"><span class="k">Evidence</span> <span>{evidence_words(shown)}'
                "</span></p>" if shown else "")  # fmt: skip
    missing.pop(NO_STEADY_WORD, None)  # the sessions table prints each session's none and why
    return (f"{how_html(row)}{serving}{proved_html(row)}{proving}{generation_html(row)}"
            f"{verifying_html(row)}{size_html(row)}{evidence}{cost_bars(row, drawn)}"
            f"{reply_tokens_html(row)}"
            f'<dl class="parts">{cells}</dl>{missing_html(missing)}')  # fmt: skip


def p_html(p):
    """A p value at two significant digits; below 0.001 as a power of ten, the exponent raised
    ("5.0 × 10" and "minus 6" above it), which reads where seven decimal places do not."""
    if p == 0 or p >= 0.001:
        return e(sig(p, 2))
    exp = math.floor(math.log10(p))
    mant = f"{p / 10**exp:.1f}"
    if mant == "10.0":
        mant, exp = "1.0", exp + 1
    return f"{mant}\u00a0\u00d7\u00a010<sup>\u2212{-exp}</sup>"


def p_floor(n):
    """FI-4: the lowest p a test on n prompts can give: 2^-n when it counts every sign vector,
    1 / (1 + resamples) when it draws them."""
    c = S.V["constants"]
    return 2.0**-n if n <= c["fidelity_exact_up_to"] else 1 / (1 + c["fidelity_resamples"])


def p_said(p, n):
    """A p as a line prints it: "p = 0.0058"; at its test's floor a drawn p is a bound, "p <
    5.0 × 10^-6, the test's floor", and a counted one its value with the same words."""
    if p != p_floor(n):
        return f"p\u00a0=\u00a0{p_html(p)}"
    if n <= S.V["constants"]["fidelity_exact_up_to"]:
        return f"p\u00a0=\u00a0{p_html(p)}{e(P_FLOOR)}"
    return f"p\u00a0&lt;\u00a0{p_html(p_bound(p))}{e(P_FLOOR)}"


def p_bound(p):
    """The two-digit power of ten at or above p, so "p < bound" holds as printed."""
    exp = math.floor(math.log10(p))
    mant = math.ceil(p / 10**exp * 10) / 10
    return mant * 10**exp


QUANT = re.compile(r"q\d")  # a quantized copy's id ("q8_0", "q4_k_m")
RULE_AT = re.compile(r"\s*\((?:RFC-\d+ )?[A-Z]{2}-\d+[a-z]?\)$")  # a note's closing rule id


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


def control_th(cid):
    """A control's row head, its id in the title where its name is not the id; an id in
    parentheses after the name is set small in the mono face, whose underscore reads."""
    name, title = control_name(cid)
    at = f' title="{e(title)}"' if title else ""
    words, paren, rest = name.partition(" (")
    said = e(words) + (f' <span class="cid">({e(rest)}</span>' if paren else "")
    return f'<th scope="row"{at}>{said}</th>'


def kl_why(row):
    """Why the row's KL is not measured, in visible words (its note without the state that opens
    it and the rule id that closes it, which stay in the title), and the note whole."""
    note = (row["fidelity"] or {}).get("kl_note") or ""
    return RULE_AT.sub("", note.removeprefix("not measured: ").removeprefix("not measured")), note


def kl_cell(row):
    """The row's KL in its column: the figure, or "not measured" with why under it."""
    kl = (row["fidelity"] or {}).get("kl")
    if has(kl):
        return fig_html(kl)
    why, note = kl_why(row)
    return (f'<span class="na" title="{e(note or "not measured")}">not measured</span>'
            + (f'<span class="sub">{e(why)}</span>' if why else ""))  # fmt: skip


def tf_kl_html(entry, block_n):
    """A teacher-forced KL figure with its labels in its title (its n under it where it is not
    the block's), or "not measured" with the cause."""
    kl = entry["kl"]
    if kl is None:
        note = entry["kl_note"] or "not measured"
        return f'<span class="na" title="{e(note)}">not measured</span>'
    num, unit = number(kl["value"], kl["unit"])
    title = (f"{kl['unit']} · measured, reported · {kl['note']} · {kl['n']:,} prompts, "
             f"{kl['positions']:,} positions · mean probability the original gives the pooled "
             f"tokens: {sig(kl['reference_rest_mass'] or 0, 2)} · record: {kl['source']}")  # fmt: skip
    sub = "" if kl["n"] == block_n else f'<span class="sub">{e(TF_KL_SUB.format(n=kl["n"]))}</span>'
    return (f'<span class="fig" title="{e(title)}"><span class="n">{e(num)}</span>'
            f'<span class="u">{e(unit)}</span></span>{sub}')  # fmt: skip


def agree_html(entry, tf, sub):
    """FI-10's agreement for one row of the table: the percentage of the positions (SI-9), its
    labels in its title, and `sub` (the median, failed prompts) under it; "not run" with the
    cause in its title where the pass did not run."""
    if entry is None or entry["status"] != "ok":
        why = (entry or {}).get("cause") or "not run"
        return f'<span class="na" title="{e(why)}">not run</span>'
    said = f"mean {sig(entry['mean'])} of {tf['positions']:,} positions; n = {entry['n']:,} prompts"
    if entry.get("percent_interval"):
        said += "; " + interval_words(entry)
    return (f'<span class="fig" title="{e(said)}; record: {e(tf["path"])}">'
            f'<span class="n">{e(pct(entry["percent"]))}</span><span class="u">%</span></span>'
            + "".join(f'<span class="sub">{e(line)}</span>' for line in sub if line))  # fmt: skip


def interval_words(entry):
    """SI-9: a percentage's 95 % bootstrap interval over the prompts, as the board computed it."""
    low, high = entry["percent_interval"]
    return TF_INTERVAL.format(low=pct(low), high=pct(high))


def median_words(entry, tf):
    """The median in the mean's unit, a percentage of the positions."""
    if entry is None or entry["status"] != "ok":
        return ""
    return TF_SUB.format(median=f"{pct(entry['median'] / tf['positions'] * 100)}\u202f%")


def tests_html(row, tf, mine):
    """FI-11's tests, printed and not gating (SI-9): one native disclosure under the table, its
    summary their count, each control's two p values on a line (the row above it, below it), each
    half kept whole (`kept`): a line too long breaks between the two."""
    if mine is None:
        return ""
    tests = {(t["a"], t["b"]): t["p"] for t in mine["tests"]}
    lines = []
    for c in tf["controls"]:
        above, below = tests.get((row["system"], c["id"])), tests.get((c["id"], row["system"]))
        if above is None or below is None:
            continue
        name, title = control_name(c["id"])
        at = f' title="{e(title)}"' if title else ""
        words = (e(TF_TEST.format(name=name_of(row), above="\0", below="\1"))
                 .replace("\0", p_said(above, tf["n"]))
                 .replace("\1", p_said(below, tf["n"])))  # fmt: skip
        lines.append(f"<div><dt{at}>{e(name)}</dt><dd>{kept(*words.split(' · '))}</dd></div>")
    if not lines:
        return ""
    said = f"{counted_words(2 * len(lines), 'test')} {TF_TESTS_ON}"  # the measure, visible
    return (f'<details class="more fts"><summary>{e(said)}<span class="sr">, '
            f'{e(FIGURE_HEAD["fidelity"])}</span></summary><dl>{"".join(lines)}</dl></details>')  # fmt: skip


NOT_RUN = '<span class="na">not run</span>'


def fid_tr(cls, th, kind, cells, heads, tf, entry, ink):
    """A row of the Fidelity table: its head, kind, the track of its teacher-forced mean (with a
    teacher-forced pass; `ink` its tick's class), then one cell per figure column, in `heads`'
    order."""
    track = ""
    if tf:
        mean = entry["mean"] if entry is not None and entry["status"] == "ok" else None
        track = (
            f'<td class="trk" aria-hidden="true">{fid_svg(mean, None, tf["positions"], ink)}</td>'
        )
    tds = "".join(f'<td data-l="{e(FID_LABEL.get(h, h))}">{c}</td>'
                  for h, c in zip(heads[2:], cells, strict=True))  # fmt: skip
    at = f' class="{cls}"' if cls else ""
    return f'<tr{at}>{th}<td data-l="{e(FID_KIND)}">{kind}</td>{track}{tds}</tr>'


def own_rows(row, tf, any_kl, heads):
    """The system's own replies: its Fidelity (median and failed prompts under it), its mean
    matched prefix (n in replies, where the Cost's n counts sessions, and p above the bar under
    it), its teacher-forced KL; then FI-13's label word for word, what ran and the records in a row
    of their own under it, on the same paper."""
    mine = row["fidelity"]
    tf_mine = tf["rows"].get(row["system"]) if tf else None
    if mine is None and tf_mine is None:
        return ""
    cells = []
    if tf:
        sub = [median_words(tf_mine, tf)]
        if tf_mine is not None and tf_mine.get("percent_interval"):
            sub.append(interval_words(tf_mine))
        if tf_mine is not None and tf_mine["failed"]:
            causes = sorted({f["cause"] for f in tf_mine["failed"]})
            sub.append(TF_FAILED.format(k=len(tf_mine["failed"]), n=tf_mine["n"]) + ": "
                       + "; ".join(causes))  # fmt: skip
        cells.append(agree_html(tf_mine, tf, sub))
    if mine is not None:
        prefix = plain(mine["mean_prefix"], "tokens", row["record"] + "/fidelity/mean_prefix",
                       f"n = {mine['n']:,} replies")  # fmt: skip
        said = [e(f"n\u00a0=\u00a0{mine['n']:,} replies")]
        if mine["p_above_bar"] is not None:
            said.append(
                e(P_ABOVE.format(p="\0")).replace("\0", p_said(mine["p_above_bar"], mine["n"]))
            )
        cells.append(f'{prefix}<span class="sub">{kept(*said)}</span>')
    else:
        cells.append(NOT_RUN)
    if tf:
        cells.append(tf_kl_html(tf_mine, tf["n"]) if tf_mine is not None else NOT_RUN)
    if any_kl:
        cells.append(kl_cell(row))
    out = fid_tr("me", f'<th scope="row">{e(name_of(row))}</th>', "this system", cells, heads, tf,
                 tf_mine, "me")  # fmt: skip
    if tf_mine is not None:  # FI-13: whose computation, what ran, the records; the columns it
        # labels named, since the row it sits under holds the leading tokens (FI-3) too
        records = [p for p in (tf_mine["run"], tf["path"]) if p]
        whose = f"{name_of(row)}'s {TF_BOTH}"
        label = (f'<p>{e(whose)}: {e(tf_mine["label"])}. What ran: '
                 f'{e(tf_mine["computed_by"])}.</p>{"".join(evidence_links(records))}')  # fmt: skip
        out += f'<tr class="me ml"><td colspan="{len(heads) + 1}">{label}</td></tr>'
    return out


def control_rows(fid, tf, any_kl, heads):
    """The model's controls, FI-3's in their order, then any only the teacher-forced pass has:
    each one's Fidelity (its median under it), its mean matched prefix, its teacher-forced KL; the
    bar's row ruled. A control that failed to run reads not run, its kind says so."""
    bar = (fid or {}).get("bar")
    fcs = {c["id"]: (i, c) for i, c in enumerate((fid or {}).get("controls") or [])}
    tcs = {c["id"]: c for c in (tf or {}).get("controls") or []}
    out = []
    for cid in [*fcs, *(k for k in tcs if k not in fcs)]:
        i, c = fcs.get(cid, (None, None))
        t = tcs.get(cid)
        is_bar = bar is not None and bar["control"] == cid
        failed = c is not None and c["status"] == "failed"
        kind = (
            (c or t)["kind"]
            + (", the bar" if is_bar else "")
            + (", failed to run" if failed else "")
        )
        none = f'<span class="na">{"not run" if failed or c is None else "not measured"}</span>'
        cells = [agree_html(t, tf, [median_words(t, tf)])] if tf else []
        cells.append(plain(c["mean_prefix"], "tokens", f"{fid['record']}/controls/{i}/mean_prefix",
                           missing="not run" if failed else "not measured")
                     if c is not None else none)  # fmt: skip
        if tf:
            cells.append(tf_kl_html(t, tf["n"]) if t is not None else NOT_RUN)
        if any_kl:
            kl = (c or {}).get("kl")
            cells.append(fig_html(kl) if has(kl) else none)
        out.append(fid_tr("bar" if is_bar else "", control_th(cid), e(kind), cells, heads, tf, t,
                          (c or t)["kind"]))  # fmt: skip
    return "".join(out)


def fidelity_html(row):
    """SI-9 and FI-3 to FI-7 in one table: the system's own replies (a paper row) and each of the
    model's controls, with Fidelity (FI-10's agreement, as a percentage of the reply's positions,
    its median under it) drawn on a track of the positions, the mean matched prefix the check reads
    (FI-3; the system's n and p above the bar under it, the bar's row ruled), and the KL of the
    teacher-forced pass (FI-12). Under the system's row, in a row of its own, FI-13's label word for
    word, what ran and the records. The tests (FI-11) one click away under the table. KL to the
    original weights (FI-7) is a column where a system or a control of the model has the figure;
    where none does, one line at the section's head says why the row's is not measured (law 2)."""
    rung = rung_of(row)
    fid, tf = rung["fidelity"], rung.get("teacher_forced")
    kl_h = kl_head(rung["reference_dtype"])
    # KL to the original weights is printed for each control (FI-7): a column wherever a system or
    # a control of the model has the figure
    any_kl = any(has((r.get("fidelity") or {}).get("kl")) for r in rung["rows"]) or any(
        has(c.get("kl")) for c in (fid or {}).get("controls") or []
    )
    heads = [FID_WHO, FID_KIND, *([TF_AGREE] if tf else []), PREFIX, *([TF_KL] if tf else []),
             *([kl_h] if any_kl else [])]  # fmt: skip
    body = own_rows(row, tf, any_kl, heads) + control_rows(fid, tf, any_kl, heads)
    if not body:
        return '<p class="none">Not run yet.</p>'
    lead = ""
    if fid is not None and fid.get("bar") is None:
        lead = f'<p class="flead">No bar: {e(fid["cause"] or "no damaged copy qualified")}</p>'
    if not any_kl and row["fidelity"] is not None:  # why, in words: no title alone (DEPTH law 3)
        why, note = kl_why(row)
        lead += (f'<p class="flead">{e(kl_h)}: <span class="na" title="{e(note or "not measured")}">'
                 f"not measured</span>{f' ({e(why)})' if why else ''}</p>")  # fmt: skip
    lead = "".join(f'<p class="flead">{line}</p>' for line in fid_lead(row, rung, tf)) + lead
    ths = (f'<th scope="col">{e(heads[0])}</th><th scope="col">{e(heads[1])}</th>'
           + ('<th scope="col" class="trk" aria-hidden="true"></th>' if tf else "")
           + "".join(f'<th scope="col"{tf_title(h, tf)}>{e(h)}</th>' for h in heads[2:]))  # fmt: skip
    tests = tests_html(row, tf, tf["rows"].get(row["system"])) if tf else ""
    limits = "".join(f'<p class="flead">{e(line)}</p>' for line in fid_limits(rung, tf))
    return (f'{lead}<table class="rt stk fid"><thead><tr>{ths}</tr></thead>'
            f"<tbody>{body}</tbody></table>{limits}{tests}")  # fmt: skip


def fid_lead(row, rung, tf):
    """The lines over the Fidelity table (SI-9, amended 2026-11-16), as HTML: in plain words what
    is compared with what (the copy the row proves, from its workload record, against the
    original), what 100 % means and what the 8-bit and 4-bit copies are; why the surface figure is
    top-token agreement; then which measure sets the check and the petal (the leading tokens,
    FI-3), what passes the check, that the figure sets no state, and that neither compares
    logits."""
    bits = DTYPE_BITS.get(rung["reference_dtype"], rung["reference_dtype"])
    p = row.get("precision") or {}
    proved = (f"{p['proved']} ({p['proved_words']})" if p.get("proved_words")
              else str(p.get("proved") or ""))  # fmt: skip
    if proved and isinstance(p.get("bits"), int | float):
        n = f"{p['bits']:,}" if float(p["bits"]).is_integer() else sig(p["bits"], 3)
        part = " for part of the weights" if p.get("bits_covers") == "part" else ""
        proved += f", {n} bits per weight{part}"
    plain = FID_PLAIN.format(name=name_of(row), bits=bits, proved=proved)
    if not proved:  # no workload record: the general sentence alone
        plain = plain.partition(", and ")[0] + "."
    controls = {c["id"] for c in ((rung.get("fidelity") or {}).get("controls") or [])}
    if tf:
        plain += FID_PLAIN_TF.format(n=tf["n"])
    if {"q8_0", "q4_k_m"} <= controls | {c["id"] for c in (tf or {}).get("controls") or []}:
        plain += FID_PLAIN_COPIES
    out = [to_rule(e(plain), "Fidelity figure", "fidelity-figure")]
    if tf:
        out.append(e(FID_WHY.format(tokens=tf["positions"])))
    exact = FID_LEAD_PREFIX.format(bits=bits) + FID_LEAD_CHECK + (FID_LEAD_TF if tf else "")
    out.append(to_rule(e(exact + FID_LEAD_LOGITS), "Fidelity check", "fidelity"))
    return out


def to_rule(html, phrase, anchor):
    """`html` with the first `phrase` in it linked to its rule on the checks page."""
    head, found, tail = html.partition(phrase)
    if not found:
        return html
    return f'{head}<a class="df" href="{CHECKS_PAGE}#{anchor}">{phrase}</a>{tail}'


def fid_limits(rung, tf):
    """What the Fidelity measures rest on, each line from the records (depth 3): where the
    original was fetched and the ceiling its own pass sets (FI-1, FI-15), the engines and slots
    of each part of the fidelity run (FI-9, FM-5), and what the prompts are cut from."""
    out = []
    o = rung.get("original")
    if o and o.get("repo"):
        bits = DTYPE_BITS.get(o["dtype"], o["dtype"])
        line = LIM_ORIGINAL.format(repo=o["repo"], rev=str(o["revision"])[:7], bits=bits)
        owner = str(o["repo"]).split("/")[0]
        if o.get("publisher_repo") and str(o["publisher_repo"]).split("/")[0] != owner:
            line += LIM_COPY.format(publisher=rung["publisher"])
        own = (tf or {}).get("reference_pass")
        if own and own.get("status") == "ok" and own.get("mean") is not None:
            line += LIM_CEILING.format(ceiling=pct(own["mean"] / tf["positions"] * 100))
        out.append(line)
    fid = rung.get("fidelity") or {}
    parts = []
    for r in fid.get("runs") or []:
        part = LIM_PART.get(r["part"], r["part"] or "")
        if r["engine"] == "vllm":
            parts.append(LIM_VLLM.format(part=part))
        elif r["engine"] is not None and r["slots"] is not None:
            slots = "one request" if r["slots"] == 1 else f"{r['slots']:,} requests"
            parts.append(LIM_LLAMA.format(part=part, slots=slots))
    if parts:
        line = LIM_ENGINES.format(parts="; ".join(parts))
        out.append(line + (LIM_GREEN if fid.get("slots") != 1 else ""))
    corpus = S.V.get("corpus")
    if corpus and corpus["texts"]:
        out.append(LIM_PROMPTS.format(tokens=S.V["request"]["prompt_tokens"], texts=corpus["texts"],
                                      hosts=", ".join(corpus["hosts"]),
                                      licences="; ".join(corpus["licences"])))  # fmt: skip
    return out


def tf_title(head, tf):
    """A column head's title (the teacher-forced KL's says what it compares, FI-12) and, for the
    Fidelity column, its class (words.css sets its width)."""
    if tf and head == TF_KL:
        return f' title="{e(TF_KL_TITLE.format(k=tf["top_k"]))}"'
    return ' class="fag"' if head == TF_AGREE else ""


def figures_html(row):
    """The row's other figures (the band prints its one figure) as one ruled row of cells, each
    figure with its unit and no more (SI-8): cost per reply at the multiple's own scope, verify
    time and proof size per reply, then Fidelity. Each one's scope and n stand under Cost (and in
    its title); the bar, the controls and KL under Fidelity."""
    figs, n = row["figures"], counted(row)
    cost = row_cost(row)  # its title names the whole sessions where it is theirs, and n (law 3)
    note = whole_note(row, "session_multiple") if cost is figs["session_usd_per_reply"] else None
    cells = [(defined(FIGURE_HEAD["cost"], "cost"), fig_html(cost, n, sub=BARE, note=note)),
             (defined(FIGURE_HEAD["check-time"], "check-time"),
              fig_html(figs["verify_seconds_per_reply"], n, sub=BARE)),
             (defined(FIGURE_HEAD["proof-size"], "proof-size"),
              fig_html(figs["proof_bytes_per_reply"], n, sub=BARE)),
             (defined(FIGURE_HEAD["fidelity"], FIGURE_ANCHOR["fidelity"]),
              fidelity_word(row, "", long=True))]  # fmt: skip
    return '<dl class="figs">' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>"
                                         for k, v in cells) + "</dl>"  # fmt: skip


def band_figure(row):
    """The band's one figure (`multiple_html` without its parts); of the whole sessions, its title
    names them and n, as the line under it does (law 3)."""
    _, f, key = lead_figure(row)
    if key != "session_multiple":
        return multiple_html(row, parts=False)
    count = f["n"] if f["n"] is not None else counted(row)
    # the line under it, "whole sessions" linked to their definition (D1)
    line = sub_line(whole_line(row, count)).replace(
        "whole sessions", term("whole sessions", "Whole session"), 1
    )
    return (fig_html(f, count, sub=BARE, note=whole_note(row, key), how=how_computed(row))
            + f'<span class="sub">{line}</span>')  # fmt: skip


PAPER_WORD = "PDF, at the commit this row runs"  # the band's Paper fact, linked (D5)
NAME_SIZES = (6, 12, 20)  # a system's name on its band: one size per length up to these
SHARE = (
    "Share",
    "Share card",
    "Copy link",
    "Copied",
)  # the share group: its name, its actions, done
# the card link's title (D4): what clicking it does, said before it is clicked
SHARE_CARD_TITLE = ("This page's share card: an image of its glyph and figure, the one a link "
                    "preview shows. Opens in a new tab, to save or share.")  # fmt: skip


def share_html(row):
    """The share group's actions: the page's share card, opened in a new tab as the image it is
    (a reader who clicks "Share card" sees it, then saves or shares it; it no longer downloads
    unannounced), while its picture is the one this build's source was rendered to (none
    otherwise), and Copy link, which words.js shows and runs (it copies the page's canonical
    address and says so)."""
    pid = row["page"]
    card = ""
    if card_current(pid):
        v = cards_record()[pid]["png"][:12]
        card = (f'<a href="/og/{e(pid)}.png?v={e(v)}" target="_blank" rel="noopener" '
                f'title="{e(SHARE_CARD_TITLE)}">{e(SHARE[1])}'
                '<span class="sr"> (image, opens in a new tab)</span></a>')  # fmt: skip
    return (card + f'<button type="button" class="cplink" data-done="{e(SHARE[3])}" hidden>'
            f"{e(SHARE[2])}</button>")  # fmt: skip


def pin_html(pin, name):
    """A row that runs a change to the publisher's code, in one line (SI-3, amended 2026-11-15):
    the pull request, whether upstream merged it, who wrote it, and what the publisher's own
    commit did on the level's request, linked to its record."""
    merged = "merged upstream" if pin["merged"] else "not merged upstream"
    who = ", written by this project's owner" if pin["by_owner"] else ""
    record = (f' (<a href="{e(link(pin["record"]))}" title="{e(pin["record"])}">record</a>)'
              if pin.get("record") else "")  # fmt: skip
    return (
        f'Runs <a href="{e(pin["url"])}">pull request #{pin["pull"]:,}</a> to {e(name)}, '
        f"{merged}{who}; at upstream <code>{e(pin['upstream_commit'][:7])}</code>, "
        f"{e(pin['upstream_outcome'])}{record}."
    )


def system_page(row):
    """A system on a model (SI-3): the band (its name, sized by its length, never more than two
    lines; its one figure on the right, labelled for what it is; the facts under them, the
    publisher's repository at the row's commit among them), then the glyph and its petals, its
    other figures, the checks, the cost, fidelity and, last, the sessions (the audit trail)."""
    rung = rung_of(row)
    sysd = S.V["systems"][row["system"]]
    name = name_of(row)
    facts = [("f-st", "Standing", standing_html(row, "")),
             ("f-md", "Model", f'<a href="/#{e(rung["id"])}">{nobreak(rung["model"])}</a>'
              f'<span class="msz">{e(architecture(rung["parameters_total"], rung.get("parameters_active")))}</span>')]  # fmt: skip
    source = ""
    pin = sysd.get("pin")
    if pin:  # a change to the publisher's code: the source is its pull request (SI-3)
        source = (f'<a href="{e(pin["url"])}">{nobreak(sysd["repo"] or name)} '
                  f'<span class="nw">#{pin["pull"]:,}</span></a>')  # fmt: skip
        facts.append(("f-src", "Source", source))
    elif sysd["repo"]:  # the publisher's repository, at the commit the row runs
        at = f"/tree/{e(row['commit'])}" if row["commit"] else ""
        source = (f'<a href="https://github.com/{e(sysd["repo"])}{at}">'
                  f'{nobreak(sysd["repo"])}</a>')  # fmt: skip
        facts.append(("f-src", "Source", source))
    paper = ""
    if sysd.get("paper"):  # D5: the publisher's paper, at the row's commit, where it has one
        paper = f'<a href="{e(sysd["paper"])}">{e(PAPER_WORD)}</a>'
        facts.append(("f-pap", "Paper", paper))
    if pin:  # SI-3 (amended 2026-11-15): the version the row runs, at depth 2
        facts.append(("f-pin", "Version", pin_html(pin, name)))
    share = share_html(row)
    size = next((i + 1 for i, k in enumerate(NAME_SIZES) if len(name) <= k), len(NAME_SIZES) + 1)
    # the figure's plain name, the figure, and under it, once, what was counted and n (CO-5)
    label, lead = FIGURE_HEAD["multiple"], band_figure(row)
    _, _, lkey = lead_figure(row)
    lead += split_html(row, lkey, bar=False, bare=True)
    unranked = "" if row["position"] is not None else " unr"
    band_ = (
        f'<section class="mast mast-sys sysb" aria-labelledby="h-name"><div class="mast-in">'
        f'<div class="sb"><h1 id="h-name" class="sysname nm{size}">{e(name)}</h1>'
        f'<p class="sbm{unranked}"><span class="sbl">{e(label)}</span>{lead}</p></div>'
        '<dl class="facts">'
        + "".join(f'<div class="{c}"><dt>{k}</dt><dd>{v}</dd></div>' for c, k, v in facts)
        + "</dl></div></section>"
    )
    # a phone's band holds the name, the model, the standing and the figure, and no more: the
    # source and the share group stand at the page's foot there (the source from 560 px down,
    # the share group from 760 px down, where the strip has no room for it)
    foot = (
        '<dl class="fend">'
        + (f'<div class="f-src"><dt>Source</dt><dd>{source}</dd></div>' if source else "")
        + (f'<div class="f-pap"><dt>Paper</dt><dd>{paper}</dd></div>' if paper else "")
        + f'<div class="fshr"><dt>{e(SHARE[0])}</dt><dd>{share}</dd></div></dl>'
    )
    # the share group at the strip's end on a wide screen
    share_strip = f'<div class="shr" role="group" aria-label="{e(SHARE[0])}">{share}</div>'
    parts = (("figures", "Figures"), ("glyph", "Glyph"), ("statement", "Statement"),
             ("checks", "Checks"), ("cost", "Cost"), ("fidelity", "Fidelity"),
             ("sessions", "Sessions"))  # fmt: skip
    body = f"""
{header("system")}
<main id="main" class="sys">
  {band_}
  {pnav(name, parts, share_strip)}
  <div class="wrap">
    {section("figures", "Figures", figures_html(row))}
    {section("glyph", "Glyph", glyph_html(row))}
    {section("statement", "Statement", statement_html(row))}
    {section("checks", "Checks", checks_html(row))}
    {section("cost", "Cost", cost_html(row))}
    {section("fidelity", "Fidelity", fidelity_html(row))}
    {section("sessions", "Sessions", sessions_html(row))}
    {foot}
  </div>
</main>
{footer()}"""
    # depth 0: where the system stands and its one figure with its parts, each with its unit (as
    # the card's alt says); what was counted is a step down, under the band's figure
    desc = share_words(row)
    return page(name, desc, body, "system syspage", row["page"], row["page"])


def build_system(pid):
    return system_page(S.PAGE[pid])


def linked(text, key):
    """A rule's words escaped, the phrase REASON_LINK names for `key` linked to where Learn gives
    the rule's reason; any other words escaped alone."""
    if key not in REASON_LINK:
        return e(text)
    phrase, address = REASON_LINK[key]
    head, found, tail = text.partition(phrase)
    if not found:
        raise RuntimeError(f"no {phrase!r} in the words of {key}")
    return f'{e(head)}<a href="{e(address)}">{e(phrase)}</a>{e(tail)}'


def rule_lines(lines, ids=(), at=""):
    """Labelled lines: (label, words) pairs, the level's constants filled in; a line with no label
    is its block's own. A label in `ids` is an address of its own, its spaces as hyphens. `at`
    names the lines' constant in REASON_LINK: the phrase it names links to the rule's reason (the
    label, where the label is the phrase)."""

    def line(k, v):
        key = (at, k)
        to_label = key in REASON_LINK and REASON_LINK[key][0] == k
        dt = linked(k, key) if to_label else e(k)
        dd = e(filled(v)) if to_label else linked(filled(v), key)
        place = f' id="{e(k.replace(" ", "-"))}"' if k in ids else ""
        return f"<div{place}><dt>{dt}</dt><dd>{dd}</dd></div>"

    return "".join(line(k, v) for k, v in lines)


def rules(lines, ids=(), at=""):
    """`rule_lines` as one list."""
    return f'<dl class="cs">{rule_lines(lines, ids, at)}</dl>'


def title_band(title, cls="ttl"):
    """The band of a page that is not a system's (the checks, the mandate, the 404): its title
    at the home title's size."""
    return (f'<div class="mast mast-t"><div class="mast-in"><h1 id="h-name" class="{cls}">'
            f"{e(title)}</h1></div></div>")  # fmt: skip


def cause_rule(cause, text):
    """A petal cause's rule (PETAL_CAUSE_RULE) with its opening words ("Not stated (drawn as an
    outline)", "Not decided (drawn hollow), Fidelity only") drawn as the chip a system page
    prints for such a petal, those words kept for a screen reader; what follows them ("Fidelity
    only") in words."""
    state_words = next(k for k in PETAL_CAUSE_DRAW if text.startswith(k))
    after = text[len(state_words) :]
    only, rest = after[2:].partition(": ")[::2] if after.startswith(", ") else ("", after[2:])
    state, form = PETAL_CAUSE_DRAW[state_words]
    drawn = chip(state, STEP_WORD[step_key("red" if state == "red" else None, cause)], form)
    lead = f"{e(only)}: " if only else ""
    return (f'<span aria-hidden="true">{drawn}</span><span class="sr">{e(state_words)}'
            f'{", " if only else ": "}</span>{lead}{e(rest)}')  # fmt: skip


INK = {"green": "green", "amber_upper": "amber", "amber_lower": "amber", "red": "red",
       None: "hollow"}  # a stored step's ink, as view.STEP_STATE  # fmt: skip


def step_chip(key):
    """A STEP_WORD key drawn as the chip a system page prints for it: its ink, and its form (cut
    for Partly met, open for Not stated)."""
    step, cause = key if isinstance(key, tuple) else (key, None)
    form = "cut" if step == "amber_lower" else "open" if cause == "not_stated" else ""
    return chip(INK[step], STEP_WORD[key], form)


def step_rule(rule):
    """A step's rule: a sentence, or its bullets as a list."""
    if isinstance(rule, str):
        return e(rule)
    return '<ul class="srl">' + "".join(f"<li>{e(r)}</li>" for r in rule) + "</ul>"


def petal_rules(p):
    """A petal on the checks page (depth 4, amended 2026-11-16): its name and field term, its
    plain sentence, whom it protects, the field's question; then each step it can take as the chip
    a system page prints beside its rule in one sentence, top step first; its terms; and what it
    leaves to another place."""
    lines = rule_lines((("", PETAL_PLAIN[p]), ("protects", PETAL_PROTECTS[p]),
                        ("question", PETAL_QUESTION[p])))  # fmt: skip
    steps = "".join(f"<div><dt>{step_chip(k)}</dt><dd>{step_rule(rule)}</dd></div>"
                    for k, rule in PETAL_RULE[p])  # fmt: skip
    more = rule_lines(PETAL_MORE.get(p, ()))
    if p in PETAL_NOT_GRADED:
        more += rule_lines((("", PETAL_NOT_GRADED[p]),))
    return (f'<div class="chk" id="{p}"><h3 class="cn2">{e(PETAL_NAME[p])}</h3>'
            f'<p class="cterm">{e(PETAL_TERM[p])}</p><dl class="cs">{lines}{steps}{more}</dl>'
            "</div>")  # fmt: skip


def know_html():
    """What we test and what we read (KNOW_LINES): what a line is about, where a row shows it,
    each check, petal and figure linked to its rule on this page by the name the site gives it,
    and how it is known."""

    def where(ids):
        names = []
        for i in ids:
            if i == "figures":
                names += [(f, FIGURE_NAME[f]) for f in FIGURE_RULE]
            else:
                names.append((i, CHECK_NAME.get(i) or PETAL_NAME.get(i) or KNOW_WHERE[i]))
        return ", ".join(f'<a href="#{e(a)}">{e(n)}</a>' for a, n in names) or "none"

    rows = [[e(what), where(ids), e(KNOW_WORD[how])] for what, ids, how in KNOW_LINES]
    return (f'<h3 class="sub-h" id="what-we-test">{e(KNOW_HEAD)}</h3>'
            + stacked(list(KNOW_COLS), rows))  # fmt: skip


def source_html(src):
    """The fact that sets a not-run reason, linked to where it is read; nothing for `not yet
    run`, which needs none (SI-4b)."""
    return f'<a href="{e(src["url"])}">{e(curly(src["words"]))}</a>' if src else ""


def not_run_rules():
    """SI-4b: the order of the reasons a system is not run, each reason with its words and the
    systems it holds, each system with the fact that sets its reason, linked to its source."""
    groups: dict[str, list[dict]] = {}
    for r in S.V["not_run"]:
        groups.setdefault(r["reason"], []).append(r)
    blocks = "".join(
        f'<div class="chk" id="nr-{e(reason.replace(" ", "-"))}"><h3 class="cn2">'
        f'{e(reason[0].upper() + reason[1:])}</h3><dl class="cs">'
        + rule_lines((("", words),))
        + "".join(f'<div><dt>{e(r["name"])}</dt><dd>{source_html(r["source"])}</dd></div>'
                  for r in sorted(groups.get(reason, []), key=lambda r: r["name"].lower()))
        + "</dl></div>"
        for reason, words in NOT_RUN_RULE.items()
    )  # fmt: skip
    return f'<p class="rd">{e(NOT_RUN_LEAD)}</p><div class="clist">{blocks}</div>'


def build_checks():
    """The rules behind a row: the request and the six checks as the entry gate (RFC-0018 §The six
    checks) with what is not tested, then the undecided causes; the figures (§Cost, FI-7, SI-9);
    the order rule (§Order); last the five petals (§The glyph), the key beside their rules, then
    why a petal is red or undecided, and what "our reading" means."""
    ids = list(S.V["petals"])
    names = [PETAL_NAME[p] for p in ids]
    glyph = glyph_svg(GLYPH, ["key"] * len(names), names=names, cls="pie-svg big",
                      hrefs=[f"#{p}" for p in ids])  # fmt: skip
    # each petal: its plain sentence, then its steps as the chips a system page prints (STEP_WORD)
    petals = "".join(petal_rules(p) for p in ids)
    # the six checks: on a wide screen one table (words.css), its heads over the passes and fails
    # lines (their own terms then left to a screen reader), each check's name and plain sentence in
    # its first column; a block each on a narrow one
    checks = '<div class="ckh" aria-hidden="true"><span>Check</span><span>Passes when</span>' + \
        "<span>Fails when</span></div>" + "".join(
        f'<div class="chk" id="{c}"><div class="chd"><h3 class="cn2">{e(CHECK_NAME[c])} check</h3>'
        f'<p class="ckp">{e(filled(CHECK_PLAIN[c]))}</p></div>'
        + rules((("passes", CHECK_HELD[c]), ("fails", CHECK_FAILED[c]), *CHECK_MORE.get(c, ())),
                at="CHECK_MORE")
        + "</div>"
        for c in S.V["checks"]
    )  # fmt: skip
    figures = "".join(
        f'<div class="chk" id="{f}"><h3 class="cn2">{e(FIGURE_NAME[f])}</h3>'
        f"{rules(FIGURE_RULE[f], at='FIGURE_RULE')}</div>"
        for f in FIGURE_RULE
    )
    # the request's one home on the site (SI-8), and what passed means
    gate = (
        f"Every system we can run at a public pin gets one request: {request_words()}. An end token does "
        "not stop the reply. A system has passed on a model when all six checks passed there."
    )
    # what the glyph is and what its petals rest on, at the head of their rules (§The glyph, GL-1,
    # GL-2, GL-8, FM-2, MC-5, §Reading the tables)
    summary = (
        "The glyph shows how close a row is to a perfect prover, one petal per property. Petals "
        "are never added up. Four petals are read from the publisher's documents at the pinned "
        "commit. Fidelity is measured by our fidelity run, and is not decided whenever the "
        "Fidelity check is. A failed check sets Failed on the petals whose claim it contradicts, "
        "a check not decided lowers none, and a passed check raises none. On any doubt the lower "
        "step wins."
    )
    # the step words once, each on its chip (the inks are drawn, never named: SI-6)
    legend = ('<p class="rd slg">' + " ".join(step_chip(k) for k in STEP_WORD) + "</p>"
              f'<p class="rd">{e(PETAL_STEPS_FOOT)}</p>')  # fmt: skip
    # why a petal is red or hollow: one address per cause, which a system page's State cell links,
    # in a block after the key's (a block inside it would be read as a sixth petal: words.js pairs
    # the key's arms with `.cwrap .chk`); then what "our reading" means (#reading, which a system
    # page's From cell links)
    petal_causes = "".join(
        f'<div id="cause-{e(k)}"><dt>{e(CAUSE_WORD[k])}</dt><dd>{cause_rule(k, v)}</dd></div>'
        for k, v in PETAL_CAUSE_RULE.items()
    )
    after_key = (
        '<div class="clist"><div class="chk"><h3 class="cn2">Why a petal is low or not decided</h3>'
        f'<dl class="cs">{petal_causes}</dl></div>'
        f'<div class="chk" id="reading"><h3 class="cn2">{e(BASIS_READING[1].capitalize())}</h3>'
        f'<dl class="cs">{rule_lines((("", READING_RULE),))}</dl></div></div>'
    )
    # why a check is undecided, the six checks' last block (#undecided, which a system page's
    # cause links): a cause's words are inline on a system page; here each is a sentence
    causes = "".join(f'<div id="cause-{e(k.replace(" ", "-"))}"><dt>{e(k)}</dt>'
                     f"<dd>{e(v[0].upper() + v[1:])}.</dd></div>"
                     for k, v in CHECK_CAUSE_WORD.items())  # fmt: skip
    undecided = (f'<div class="chk" id="undecided"><h3 class="cn2">Checks not decided</h3>'
                 f'<dl class="cs">{rule_lines((("", CHECK_CAUSE_LEAD),))}{causes}</dl></div>')  # fmt: skip
    passed = (f'<p class="rd" id="passed">{e(gate)}</p>'
              f'<p class="rd" id="not-tested">{linked(NOT_TESTED, ("NOT_TESTED", ""))}</p>'
              f'<p class="rd" id="binding">{e(BINDING_GAP)}</p>')  # fmt: skip
    six = (f'{how_link("rd")}{passed}<div class="clist six">{checks}</div><div class="clist">{undecided}</div>'
           f"{know_html()}")  # fmt: skip
    parts = (("checks", "Six checks"), ("figures", "Figures"), ("order", "Order"),
             ("glyph", "Glyph"), ("not-run", "Not run"))  # fmt: skip
    # the order rule; "largest model with a passed row" (OR-6) is an address the ladder's mark can link
    order = rules(ORDER_RULE, ids=("unranked", "largest model with a passed row"), at="ORDER_RULE")
    key = (f'<p class="rd">{linked(summary, ("summary", ""))}</p>{legend}'
           f'<div class="cwrap"><div class="gbig">{glyph}</div><div class="clist">{petals}'
           f"</div></div>{after_key}")  # fmt: skip
    body = f"""
{header("checks")}
<main id="main" class="sys">
  {title_band("Checks")}
  {pnav("Checks", parts)}
  <div class="wrap">
    {section("checks", "The six checks", six)}
    {section("figures", "Figures", f'<div class="clist">{figures}</div>')}
    {section("order", "Order", order)}
    {section("glyph", "Glyph", key)}
    {section("not-run", "Systems not run", not_run_rules())}
  </div>
</main>
{footer()}"""
    return page("Checks", CHECKS_DESC, body, "system checkspage", CHECKS_PAGE.strip("/"), "home")


def build_mandate():
    """The mandate: the belief as the headline, then who runs it (with the members, once any has
    agreed), what we do, what we do not do and how to check us (the level and its file among
    them: the footer's level cell leads there). A line bound by a rule prints the rule under its
    label, the document and the rule's id as the link's words, the link to the section of the
    file that holds it (DEPTH law 3: a phone and a keyboard see it). The names in a line are the
    facts file's (`credit`), linked as the footer links them."""

    def label(text, name, path):
        if not path:
            return e(text)
        if isinstance(path, str) and path.startswith("https://"):  # a source outside the repo
            return f'{e(text)}<a class="rl" href="{e(path)}">{e(name)}</a>'
        names, paths = (name, path) if isinstance(path, tuple) else ((name,), (path,))
        file = paths[0].split("#", 1)[0]
        rfc = re.match(r"rfcs/(\d{4})-", file)
        doc = f"RFC-{rfc[1]}" if rfc else file.rsplit("/", 1)[-1]
        if len(paths) == 1:
            return (f'{e(text)}<a class="rl" href="{e(link(path))}" title="{e(path)}">'
                    f"{e(doc)}, {e(name)}</a>")  # fmt: skip
        # rules of one file in two sections: the document once, each rule's id a link to its own
        ids = ", ".join(f'<a href="{e(link(p))}" title="{e(p)}">{e(n)}</a>'
                        for n, p in zip(names, paths, strict=True))  # fmt: skip
        return f'{e(text)}<span class="rl">{e(doc)}, {ids}</span>'

    credit = S.V["credit"]
    names = {k: f'<a href="{e(credit[k]["url"])}">{e(credit[k]["name"])}</a>'
             for k in ("lead", "builder")}  # fmt: skip

    # SE-3a and SE-3b in words, from the board's rows (a count typed here would go stale)
    def by_row(key, one, none, noun):
        said = []
        for r in S.ROWS:
            n = len(r.get(key) or ())
            if n:
                said.append(one.format(n="one" if n == 1 else f"{n:,}", name=name_of(r),
                                       **{noun: noun if n == 1 else f"{noun}s"}))  # fmt: skip
        return "; ".join(said) or none

    names["se3a"] = e(by_row("replaced", SE3A_ROW, SE3A_NONE, "slot"))
    names["se3b"] = e(by_row("ineligible", SE3B_ROW, SE3B_NONE, "session"))

    def words_html(words):
        return e(words).format_map(names) if "{" in words else e(words)

    members = credit["members"]
    # the members' names in display type, a ruled row; nothing while none has agreed
    row = ('<div class="mbr"><dt>Members</dt><dd><ul class="mbl">' + "".join(
        f'<li><a href="{e(m["url"])}">{e(m["name"])}</a></li>' for m in members)
        + "</ul></dd></div>") if members else ""  # fmt: skip
    lv = S.V["level"]
    # the level, its file's path under it as the link, as a bound line's rule is (its digest in
    # the title); its state opens the line
    state = f"Frozen {lv['frozen']}." if lv["frozen"] else "Draft."
    # the rules added since the freeze that decided rows: named, with their links, on /method
    phrase, href = MANDATE_LEVEL_LINK
    history = e(MANDATE_LEVEL).replace(e(phrase), f'<a href="{e(href)}">{e(phrase)}</a>', 1)
    level = (f'<div id="{LEVEL_ANCHOR}"><dt>{e(lv["name"])}<a class="rl" href="{e(link(lv["path"]))}" '
             f'title="{e(lv["digest"])}">{e(lv["path"])}</a></dt>'
             f"<dd>{e(state)} {history}</dd></div>")  # fmt: skip
    # the dated corrections, newest first, the last row of their section
    corrections = ('<div id="corrections"><dt>Corrections</dt><dd><ul>' + "".join(
        f"<li>{e(day)}: {e(words)}</li>" for day, words in MANDATE_CORRECTIONS)
        + "</ul></dd></div>")  # fmt: skip
    blocks = "".join(
        section(title.lower().replace(" ", "-"), title, '<dl class="cs">' + "".join(
            f"<div><dt>{label(text, name, path)}</dt><dd>{words_html(words)}</dd></div>"
            for text, name, path, words in lines)
            + (row if title == MANDATE_MEMBERS_IN else "")
            + (level if title == MANDATE_LEVEL_IN else "")
            + (corrections if title == MANDATE_CORRECTIONS_IN else "") + "</dl>")
        for title, lines in MANDATE
    )  # fmt: skip
    parts = [(title.lower().replace(" ", "-"), title) for title, _ in MANDATE]
    body = f"""
{header("mandate")}
<main id="main" class="sys">
  {title_band(MANDATE_BELIEF, cls="ttl creed")}
  {pnav("Mandate", parts)}
  <div class="wrap">
    {blocks}
  </div>
</main>
{footer()}"""
    return page("Mandate", MANDATE_DESC, body, "system mandatepage", MANDATE_PAGE.strip("/"),
                "home")  # fmt: skip


def build_404():
    """Not found: the systems with a page, each with its glyph and model; the header and footer
    link the rest (the ladder holds the models)."""
    systems = "".join(
        f'<li><a href="{e(href(r))}">{glyph_svg(2, states(r))}'
        f'<span class="ln">{e(name_of(r))}</span><span class="lp">{nobreak(rung_of(r)["model"])}</span>'
        "</a></li>"
        for r in S.ROWS
    )
    lists = (
        '<section class="blk" aria-labelledby="h-systems">'
        f'<h2 class="sect" id="h-systems">Systems</h2><ul class="lost lsys">{systems}</ul></section>'
    ) if systems else ""  # fmt: skip
    body = f"""
{header(None)}
<main id="main" class="sys">
  {title_band("Not found")}
  <div class="wrap">{lists}</div>
</main>
{footer()}"""
    return page("Not found", "No page at this address.", body, "system notfound", "404", None)
