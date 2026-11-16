"""The overview (`index.html`): the ladder (RFC-0018 SI-1). The title, then one section per
model, largest first, the frontier's marked as the largest model with a passed row: its head (model,
publisher, architecture, the serving baseline) and its rows in the board's order (OR-5), then
the systems not run (SI-4). Rows sort
only by the order rule: no column head re-sorts them. Also the figure cells the system pages use.
"""

from . import state as S
from .chrome import (
    CHECKS_PAGE,
    ONLY_RUN,
    counted,
    footer,
    has,
    header,
    how_computed,
    lead_figure,
    not_passed,
    page,
    parts_of,
    row_cost,
    rung_of,
)
from .hexagon import glyph_svg
from .words import (
    BASIS_BITS,
    CAUSE_WORD,
    CHECK_NAME,
    CHECK_PLAIN,
    COPY_WORD,
    FIDELITY_AGAINST,
    FIDELITY_CHECK_TITLE,
    FIDELITY_FIG_TITLE,
    FIDELITY_TITLE,
    FIGURE_ANCHOR,
    FIGURE_HEAD,
    FORMAT_WORD,
    FRONTIER_WORD,
    FULL_LOAD_WORD,
    NULL_WORD,
    PETAL_NAME,
    PETAL_PLAIN,
    PROVED_HEAD,
    REFERENCE_WORD,
    SCALE_NOT_RUN,
    SEP,
    STATE_WORD,
    STEADY_STATE,
    TF_INTERVAL,
    WHOLE_SESSIONS,
    WHY_TOP_TOKEN,
    architecture,
    e,
    labels,
    number,
    params,
    petal_step,
    session_count,
    sig,
    sub_words,
)

# what the checks do not test (the checks page, #not-tested; RFC-0018 Non-Goals)
NOT_TESTED = (
    "No check attempts a forged proof. Soundness and weight secrecy are not tested: the glyph "
    "reports what the publisher's documents state about them."
)
# the binding-only gap (RFC-0018 SI-4, SI-4a), on the checks page beside NOT_TESTED
BINDING_GAP = (
    "The checks run the publisher's own prover honestly and try changes it should refuse. A hash "
    "of the commitment, prompt and reply, computed from the weights the prover loads, would hold "
    "all six. Level 1 keeps such a system from a position, not from the ladder: it would still "
    "read passed. What keeps it from a position is its publisher's recorded statement that an "
    "accept is the committed model's own greedy reply, or our reading of one, not a test."
)
ROW_GLYPH = 3  # the row glyph's unit in px: its arms carry their names (159 by 87 px)


def states(row):
    """The five petals, in the glyph's order (GL-5), as glyph_svg draws them: each with its state,
    step, cause and form (view._glyph)."""
    return row["glyph"]


def petal_words(p):
    """A petal's step in words, and for a Not decided petal what it waits on (§The glyph, step
    table, amended 2026-11-16; GL-3): Not met, Failed and Not stated already say their cause."""
    words = petal_step(p)
    return f"{words}, {CAUSE_WORD[p['cause']]}" if p["step"] is None else words


def states_words(row):
    """The petals in words, for screen readers (the glyph is drawn, not read): "Integrity:
    Partly met"; one span per petal, its name in <b>, which words.js shows beside a petal
    pointed at with the petal's plain sentence (`data-plain`, not read out). It sits in the
    glyph's cell, so the row's header reads the name and standing only."""
    return "; ".join(f'<span data-plain="{e(PETAL_PLAIN[p["id"]])}"><b>{e(PETAL_NAME[p["id"]])}'
                     f"</b>: {e(petal_words(p))}</span>" for p in row["glyph"])  # fmt: skip


def name_of(row):
    return S.V["systems"][row["system"]]["name"]


def href(row):
    return f"/{row['page']}"


BARE = ""  # `fig_html`'s `sub` for a figure with no line under it


def fig_html(f, n=None, sub=None, why=None, note=None, how=None):
    """One stored figure: the number in a reading unit, its labels in its title, and under it its
    scope in a word and its sample size (AGENTS.md rule 2). `sub` replaces the line under it
    (`BARE`: no line, as the ladder and the Scale page print a figure; its labels stay in its
    title, `n` and `note` among them, and stand in full on the system's page); `why` replaces a
    null figure's reason (NO_STEADY_WORD on a row with no steady state); `how` opens the title
    with how the figure is computed (the headline's, `how_computed`)."""
    if f is None:
        return '<span class="na">not recorded</span>'
    if f["value"] is None:
        why = why or NULL_WORD[f["null_reason"]]
        return (
            f'<span class="na" title="{e(labels(f))}">none</span><span class="sub">{e(why)}</span>'
        )
    num, unit = number(f["value"], f["unit"])
    x = " x" if f["unit"] == "ratio" else ""
    line = sub if sub is not None else sub_words(f, n)
    title = f"{how} {labels(f, n, note)}" if how else labels(f, n, note)
    return (f'<span class="fig" title="{e(title)}"><span class="n">{e(num)}</span>'
            f'<span class="u{x}">{e(unit)}</span></span>'
            + (f'<span class="sub">{sub_line(line)}</span>' if line else ""))  # fmt: skip


def sub_line(line):
    """The line under a figure, escaped, its dot in a span (a phone's ladder row breaks the line
    there instead, scope over n)."""
    return e(line).replace(SEP, f'<span class="sep">{SEP}</span>')


def nobreak(text):
    """Words escaped, a short token that holds a hyphen ("17B-128E", "Apache-2.0") kept on one
    line; a long one (a repository name) may still break."""
    return " ".join(f'<span class="nw">{e(t)}</span>' if "-" in t and len(t) <= 12 else e(t)
                    for t in str(text).split(" "))  # fmt: skip


def lead_fig(row, bare=False):
    """A row's one figure, labelled for what it is (CO-5, `chrome.lead_figure`). Returns (label,
    figure html); `bare` (the overview's band): the figure's plain name and the figure alone,
    what it is in its title."""
    label, f, _ = lead_figure(row)
    if bare:
        return FIGURE_HEAD["multiple"], multiple_html(row, parts=False, bare=True)
    return label, fig_html(f, counted(row))


def whole_note(row, key):
    """CO-5's label for a figure of the whole sessions, for its title; nothing for a steady one."""
    if key != "session_multiple":
        return None
    return WHOLE_SESSIONS.format(n=rung_of(row)["requests_per_session"])


def scope_note(row, f):
    """CO-5's label for any figure timed over the whole sessions (a session's cost beside its
    multiple), so the figures of one row carry the same scope words in their titles."""
    if f is None or f.get("scope") != "whole_wall":
        return None
    return WHOLE_SESSIONS.format(n=rung_of(row)["requests_per_session"])


def whole_line(row, count):
    """What a figure of the whole sessions counted, as the line under it says it: their number,
    then CO-5's label whole ("3 whole sessions of 120 replies")."""
    label = WHOLE_SESSIONS.format(n=rung_of(row)["requests_per_session"])
    if count is None:
        return label
    return f"{label}{SEP}{session_count(count)}" if count == 1 else f"{count:,} {label}"


def steady_line(count):
    """What a steady figure counted, as the line under it says it (CO-3): "steady state · 3
    sessions"."""
    return SEP.join([STEADY_STATE, *([session_count(count)] if count is not None else [])])


def serving_missing(b, why="no full load recorded"):
    """A model's serving figure where the board holds none: "not run yet" with no serving run,
    "not measured" with one; the stored cause in its title."""
    word = "not run yet" if b is None or b.get("run_id") is None else "not measured"
    cause = (b or {}).get("cause") or why
    return f'<span class="na" title="{e(cause)}">{word}</span>'


def to_section(html, to):
    """A figure linked to its section of the system's page (`to`, its address), on the ladder:
    the row leads to the page, a figure to where it was taken (DEPTH law 1). None: as it is."""
    return f'<a class="flk" href="{e(to)}">{html}</a>' if to else html


def multiple_html(row, parts=True, bare=False, to=None):
    """CO-5: the multiple; with no steady state, the session cost over serving, labelled as whole
    sessions. With `parts`, its two parts under it (CO-7, `split_html`). `bare` (the ladder, the
    Scale page): the figures alone, no line of scope and n under any; `to` (the ladder): the
    figure and its parts each linked there."""
    _, f, key = lead_figure(row)
    split = split_html(row, key, bare=bare, to=to) if parts else ""
    how = how_computed(row)
    if bare:
        fig = fig_html(f, counted(row), sub=BARE, note=whole_note(row, key), how=how)
        return (to_section(fig, to) if has(f) else fig) + (split if has(f) else "")
    if key == "session_multiple":
        count = f["n"] if f["n"] is not None else counted(row)
        return fig_html(f, counted(row), sub=whole_line(row, count), how=how) + split
    if not has(f):
        return fig_html(f, counted(row))
    count = f["n"] if f["n"] is not None else counted(row)
    return fig_html(f, counted(row), sub=steady_line(count), how=how) + split


def split_html(row, key, bar=True, bare=False, to=None):
    """CO-7: under a multiple (`key`: the steady one or the whole sessions'), its two parts, each
    a figure with its scope and n (`bare`: the figure alone, where the whole above them says both
    once), after a bar of their shares, where the system generates in a phase of its own; nothing
    otherwise. The part that is not generation first, in paper."""
    parts = parts_of(row, key)
    if not parts:
        return ""
    (w1, f1), (w2, f2) = parts
    share = 100 * f1["value"] / (f1["value"] + f2["value"])
    svg = ""
    if bar:
        # each share at its own length; one too short to see is marked by a line where it ends
        nib = f'<line class="nib" x1="{share:.2f}" x2="{share:.2f}" y2="4"/>' if share < 1.5 else ""
        svg = (f'<svg class="sbar" viewBox="0 0 100 4" preserveAspectRatio="none" aria-hidden="true">'
               f'<rect class="bp" width="{share:.2f}" height="4"/>'
               f'<rect class="bg" x="{share:.2f}" width="{100 - share:.2f}" height="4"/>{nib}</svg>')  # fmt: skip
    n = counted(row)
    line, note = (BARE, whole_note(row, key)) if bare else (None, None)
    out = "".join(f'<span class="part {c}"><span class="pl">{e(w)}</span>'
                  f"{to_section(fig_html(f, n, sub=line, note=note), to)}</span>"
                  for c, w, f in (("pp", w1, f1), ("pg", w2, f2)))  # fmt: skip
    return f'<span class="split">{svg}{out}</span>'


def pct(v):
    """A percentage as the site prints it: one decimal."""
    return f"{v:.1f}"


def fidelity_against(rung):
    """The rung's 8-bit and 4-bit copies' Fidelity in one line ("8-bit copy 98.4 % · 4-bit copy
    90.6 %"), each that ran; "" where none did. Their ids stand in the figure's title."""
    tf = rung.get("teacher_forced") or {}
    by = {c["id"]: c for c in tf.get("controls") or []}
    out = [f"{COPY_WORD[i]} {pct(by[i]['percent'])}\u202f%" for i in FIDELITY_AGAINST
           if i in by and by[i]["status"] == "ok" and by[i].get("percent") is not None]  # fmt: skip
    return SEP.join(out)


def bits_words(bits):
    """Weight bits at 3 significant digits, whole when integral ("4.84", "8")."""
    return f"{bits:,.0f}" if float(bits).is_integer() else sig(bits, 3)


def proved_words(row, long=False):
    """What the row proves, beside every Fidelity figure (RFC-0018 SI-9, amended 2026-11-16): its
    weight bits from the workload record and its number format from the properties file, where
    that records one (never inferred from a format's name). The ladder's short form: "proved:
    4.84-bit integer weights"; `long` (the Figures row) adds the activations, a part of the
    weights the bits cover, and "number format not stated" where the publisher states none. ""
    where the row has no precision record."""
    p = row.get("precision") or {}
    if not p:
        return ""
    fmt = p.get("number_format") or {}
    w, a = (FORMAT_WORD.get(fmt.get(k, "")) for k in ("weights", "activations"))
    bits = p.get("bits")
    head = f"{bits_words(bits)}-bit " if isinstance(bits, int | float) else ""
    said = f"{PROVED_HEAD}: {head}{w + ' ' if w else ''}weights"
    if not long:
        return said + (", format not stated" if fmt and not w else "")
    if a:
        said += f", {a} activations"
    if p.get("bits_covers") == "part":
        said += ", for part of the weights"
    if fmt and not (w and a):  # recorded, and the publisher states no format for a part
        said += ("; number format not stated" if not (w or a)
                 else f"; {'activations' if w else 'weights'}' format not stated")  # fmt: skip
    return said


def proved_title(row):
    """The proved copy in a Fidelity figure's title: its id, its bits and how they were found,
    and what they cover."""
    p = row.get("precision") or {}
    if not p:
        return ""
    said = f"{PROVED_HEAD}: {p['proved']}"
    if isinstance(p.get("bits"), int | float):
        said += f", {bits_words(p['bits'])} bits per weight"
        if p.get("bits_covers") == "part":
            said += " for part of the weights"
        if how := BASIS_BITS.get(p.get("bits_basis") or ""):
            said += f", {how}"
    return said


def fidelity_word(row, page=None, against=True, long=False):
    """A row's Fidelity as the surface prints it (RFC-0018 SI-9, amended 2026-11-14): FI-10's
    mean as a percentage of the reply's positions, linked to the Fidelity section of the
    system's page, then what the row proves (`proved_words`, `long` on the Figures row), then
    the rung's 8-bit and 4-bit copies (`against`). Its title says what it is, why top-token
    agreement, whose computation, the proved copy, n and the record, and the Fidelity check's
    state, which it does not set. A row with no teacher-forced pass prints the check's state in a
    word, as before."""
    tf = rung_of(row).get("teacher_forced") or {}
    mine = (tf.get("rows") or {}).get(row["system"])
    if mine is None or mine["status"] != "ok" or mine.get("percent") is None:
        return check_word(row, page)
    check = next(c for c in row["checks"] if c["id"] == "fidelity")
    low_high = mine.get("percent_interval")
    spread = ([TF_INTERVAL.format(low=pct(low_high[0]), high=pct(low_high[1]))]
              if low_high else [])  # fmt: skip
    why = WHY_TOP_TOKEN.format(tokens=S.V["request"]["output_tokens"])
    copies = [f"{COPY_WORD[i]}: {i.upper()}" for i in FIDELITY_AGAINST]
    title = [f"{FIDELITY_FIG_TITLE}. {why.rstrip('.')}", mine["label"], f"n = {mine['n']:,} prompts",
             *spread, *([proved_title(row)] if proved_title(row) else []), *copies,
             FIDELITY_CHECK_TITLE.format(state=STATE_WORD[check["state"]]),
             f"record: {tf['path']}"]  # fmt: skip
    at = href(row) if page is None else page
    proved = proved_words(row, long)
    line = fidelity_against(rung_of(row)) if against else ""
    return (f'<a class="fig fp" href="{e(at)}#fidelity" title="{e("; ".join(title))}">'
            f'<span class="n">{e(pct(mine["percent"]))}</span><span class="u">%</span></a>'
            + (f'<span class="sub pv">{e(proved)}</span>' if proved else "")
            + (f'<span class="sub">{sub_line(line)}</span>' if line else ""))  # fmt: skip


def check_word(row, page=None):
    """A row's fidelity as the surface prints it: the FIDELITY check's state in a word (held,
    failed, undecided: FI-6), linked to the Fidelity section of the system's page, which holds
    what it is read from. Its title carries the stored figures: the replies' mean count of
    leading tokens equal to the original's (FI-3), the rung's bar (FI-5) and n. The closeness
    grade is the glyph's Fidelity petal; KL is under Fidelity on the system's page."""
    check = next(c for c in row["checks"] if c["id"] == "fidelity")
    mine, bar = row["fidelity"], (rung_of(row)["fidelity"] or {}).get("bar")
    title = []
    if mine is not None and mine.get("mean_prefix") is not None:
        title.append(f"{FIDELITY_TITLE}: {sig(mine['mean_prefix'])} tokens")
        if bar is not None:
            title.append(f"bar: {sig(bar['mean_prefix'])} tokens")
        title += [f"n = {mine['n']:,} replies", f"record: {row['record']}/fidelity"]
    at = href(row) if page is None else page
    return (f'<a class="fw {e(check["state"])}" href="{e(at)}#fidelity" '
            f'title="{e("; ".join(title))}">{e(STATE_WORD[check["state"]])}</a>')  # fmt: skip


def position_html(row, rung):
    """A row's position as a square, position 1 solid paper, the others an outline; the count run
    under it. A row with no position keeps the square, a dash in it and no count (the dash is
    drawn, not read out: a screen reader reads "no position"), so every row starts alike. The
    only system run on its model (OR-4, amended 2026-11-15) holds position 1 against nothing: its
    square is an outline and says so in place of a count."""
    if row["position"] is None:
        return ('<span class="pos p0"><span class="pn" aria-hidden="true">\u2013</span>'
                '<span class="sr">no position</span></span>')  # fmt: skip
    if rung["systems_run"] == 1:
        return (f'<span class="pos solo"><span class="pn">{row["position"]}</span>'
                f'<span class="of">{e(ONLY_RUN)}</span></span>')  # fmt: skip
    lead = " p1" if row["position"] == 1 else ""
    return (f'<span class="pos{lead}"><span class="pn">{row["position"]}</span>'
            f'<span class="of">of {rung["systems_run"]}</span></span>')  # fmt: skip


def defined(words, anchor):
    """Words linked to where the checks page defines them (a short hyphened token on one line)."""
    return f'<a class="df" href="{CHECKS_PAGE}#{anchor}">{nobreak(words)}</a>'


def standing_html(row, page=None):
    """`standing` on the overview (§2.3, amended 2026-11-16): Passed and not ranked link to their
    definitions, each check not passed to its row on the system page (its cause and evidence).
    `page` is the address of that page from where the words are printed ("" on the page
    itself)."""
    if row["passed"] and not row["ranked"]:
        return (f"{defined('Passed', 'passed')}, {defined('not ranked', 'unranked')}: "
                f"{e(row['unranked_reason'])}")  # fmt: skip
    if row["passed"]:
        return defined("Passed", "passed")
    at = href(row) if page is None else page
    missing = [f'<span class="ckn"><a class="df" href="{e(at)}#ck-{c["id"]}" '
               f'title="{e(filled(CHECK_PLAIN[c["id"]]))}">'
               f'{e(CHECK_NAME[c["id"]])} check</a> {e(STATE_WORD[c["state"]])}</span>'
               for c in row["checks"] if c["state"] != "held"]  # fmt: skip
    state = f'<span class="nw">{e(not_passed(row))}{":" if missing else ""}</span>'
    # each comma inside the span of the check it follows, so a line never starts with one
    listed = " ".join(m.replace("</span>", ",</span>") if i < len(missing) - 1 else m
                      for i, m in enumerate(missing))  # fmt: skip
    return f"{state} {listed}" if missing else state


def reference_words():
    """Each model's reference precision (FI-1): "16-bit for A and B, 32-bit for C"."""
    by: dict[str, list[str]] = {}
    for rung in S.V["rungs"]:
        by.setdefault(REFERENCE_WORD[rung["reference_dtype"]], []).append(rung["model"])
    return ", ".join(f"{word} for {' and '.join(models)}" for word, models in by.items())


def filled(text):
    """A rule of `words` with the level file's constants in it."""
    r, c = S.V["request"], S.V["constants"]
    return text.format(
        gap=f"{c['group_gap_s']:g}\u202fs",
        reference=reference_words(),
        slots=c["slots"],
        attempts=c["attempts_per_slot"],
        reply_tokens=f"{r['output_tokens']:,}",
        full=f"{(1 - c['plateau']) * 100:g}\u202f%",
        top=f"{c['ladder_top']:,}",
        margin=f"{S.V['order_margin'] * 100:g}\u202f%",
        request=request_words().capitalize(),
    )


FIGURES = ("multiple", "cost", "check-time", "fidelity")  # the figure columns, in the row's order


def heads():
    """The figure columns' heads (`FIGURE_HEAD`: no word its unit says), each linked to its
    definition on the checks page (Fidelity to the figure's, not the check's: FIGURE_ANCHOR)."""
    return [defined(FIGURE_HEAD[f], FIGURE_ANCHOR.get(f, f)) for f in FIGURES]


def linked_fig(html, f, to):
    """A ladder figure linked to its section (`to_section`); a missing one ("none" and why) as it
    is."""
    return to_section(html, to) if has(f) else html


def row_html(row, rung):
    # one glyph at every width, its petals named (a phone sets it under the name, words.css)
    glyph = glyph_svg(ROW_GLYPH, states(row), names=[PETAL_NAME[p["id"]] for p in row["glyph"]])
    cost, verify = row_cost(row), row["figures"]["verify_seconds_per_reply"]
    # each figure leads to its section of the system's page: the multiple, the cost and the
    # verify time to Cost, where their scope and n are printed (Fidelity's word links its own)
    at = href(row)
    cells = (
        ("cm", multiple_html(row, bare=True, to=f"{at}#cost")),
        (
            "cc",
            linked_fig(
                fig_html(cost, counted(row), sub=BARE, note=scope_note(row, cost)),
                cost,
                f"{at}#cost",
            ),
        ),
        ("ct", linked_fig(fig_html(verify, counted(row), sub=BARE), verify, f"{at}#cost")),
        ("ck", fidelity_word(row)),
    )
    figs = "".join(f'<td class="{c}"><span class="lbl">{h}</span>{html}</td>'
                   for (c, html), h in zip(cells, heads(), strict=True))  # fmt: skip
    return (
        f'<tr class="row" id="row-{e(row["page"])}">'
        f'<td class="cp">{position_html(row, rung)}</td>'
        f'<td class="cg"><span class="sr pw">{states_words(row)}</span>'
        f'<a class="glyph" href="{e(href(row))}" tabindex="-1" aria-hidden="true">{glyph}</a></td>'
        f'<th class="csys" scope="row"><a class="sname" href="{e(href(row))}">{e(name_of(row))}</a>'
        f'<span class="st">{standing_html(row)}</span></th>{figs}</tr>'
    )


def request_words():
    r = S.V["request"]
    return (f"{r['prompt_tokens']:,} prompt tokens, {r['output_tokens']:,} reply tokens, "
            f"{r['decoding']}, every reply token checked")  # fmt: skip


def engine_words():
    eng = S.V["engine"] or {}
    name = {"vllm": "vLLM"}.get(str(eng.get("name")), eng.get("name") or "engine not recorded")
    return f"{name} {eng['version']}" if eng.get("version") else name


def baseline_html(rung):
    """The serving baseline in one line (CO-4): engine, GPUs, concurrency at full load and its
    GPU-seconds per reply."""
    b = rung["baseline"]
    # no figure: the ladder's state word, the stored cause in its title
    if b is None or not has(b["gpu_seconds_per_reply"]):
        return f'<p class="rb"><span class="k">Serving</span> {serving_missing(b)}</p>'
    gpus = f"{b['gpus']} × H200" if b["gpus"] else "GPUs not recorded"
    return (f'<p class="rb"><span class="k">Serving</span> {e(engine_words())}, {e(gpus)}, '
            f"full load at {b['concurrency']:,} concurrent requests: "
            f'{fig_html(b["gpu_seconds_per_reply"], sub=FULL_LOAD_WORD)}</p>')  # fmt: skip


def serving_words(b):
    """How the baseline was served (CO-4): the publisher's release, the engine, its GPUs and the
    full-load concurrency, then what its figure is over: the timed batches there, one run."""
    gpus = f"{b['gpus']} × H200" if b["gpus"] else "GPUs not recorded"
    rel = b.get("release") or {}
    head = (f"{rel['publisher']}'s {rel['precision']} release, "
            if rel.get("publisher") and rel.get("precision") else "")  # fmt: skip
    batches = S.V["constants"].get("timed_batches")
    over = (f"{SEP}n\u00a0=\u00a0{batches:,} timed batches, 1 run"
            if batches and b.get("run_id") else "")  # fmt: skip
    return (f"{head}{engine_words()}, {gpus}, full load at {b['concurrency']:,} concurrent "
            f"requests{over}")  # fmt: skip


def rung_meta(rung):
    """A model's head as labelled facts: publisher, architecture (the tab says its size: a
    mixture of experts names its active parameters only, as the Scale page's head does) and its
    serving GPU time per reply (CO-4), the figure every multiple under it is over. How it was
    served (engine, GPUs, concurrency) is on a system's page, under Cost."""
    b = rung["baseline"]
    facts = [("Publisher", e(rung["publisher"])),
             ("Architecture", nobreak(architecture(rung["parameters_total"],
                                                   rung.get("parameters_active"), sized=False)))]  # fmt: skip
    if b is None or not has(b["gpu_seconds_per_reply"]):
        facts.append(("Serving", serving_missing(b)))
    else:
        facts.append((FIGURE_HEAD["serving"],
                      fig_html(b["gpu_seconds_per_reply"], sub=BARE)))  # fmt: skip
    return '<dl class="meta">' + "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>"
                                         for k, v in facts) + "</dl>"  # fmt: skip


def rung_html(rung):
    """A model: a cobalt rule with its size in a tab, its name, its facts; then its rows, whose
    heads stay under the top bar with the size beside them while a long rung scrolls. The
    frontier's rung (OR-6: the largest with a passed row) says so beside its tab."""
    size = e(params(rung["parameters_total"]))
    front = S.V["frontier"]
    mark = f'<p class="rf">{e(FRONTIER_WORD)}</p>' if front and front["rung"] == rung["id"] else ""
    head = (
        f'<header class="rh"><p class="rk">{size}</p>{mark}'
        f'<h2 class="rm" id="h-{e(rung["id"])}">{nobreak(rung["model"])}</h2>'
        f"{rung_meta(rung)}</header>"
    )
    if not rung["rows"]:
        body = f'<p class="none">{e(SCALE_NOT_RUN)}</p>'
    else:
        first = (f'<th scope="col"><span class="hk" aria-hidden="true">{size}</span>'
                 f'<span class="hm" aria-hidden="true">{nobreak(rung["model"])}</span>'
                 '<span class="sr">Position</span></th>'
                 '<th scope="col"><span class="sr">Petals</span></th>')  # fmt: skip
        ths = first + "".join(f'<th scope="col">{h}</th>' for h in ("System", *heads()))
        rows = "".join(row_html(r, rung) for r in rung["rows"])
        cols = ('<colgroup><col class="c1"><col class="c2"><col class="c3"><col class="c4">'
                '<col class="c5"><col class="c6"><col class="c7"></colgroup>')  # fmt: skip
        body = (
            f'<table class="lad">{cols}<thead><tr>{ths}</tr></thead><tbody>{rows}</tbody></table>'
        )
    return (f'<section class="rung" id="{e(rung["id"])}" aria-labelledby="h-{e(rung["id"])}">'
            f"{head}{body}</section>")  # fmt: skip


# the overview's lead (SI-1, amended 2026-11-15): what a proof of inference is, for a reader with
# no context, then what the ladder below holds; the third sentence is the board's (`board_words`)
PROOF_WORDS = ("A proof of inference lets anyone check that a reply is the one a committed model "
               "returns for a prompt.")  # fmt: skip
LADDER_WORDS = ("Below, each model lists the systems run on it, whether they passed, and the cost "
                "of a proved reply as a multiple of serving that model.")  # fmt: skip
# what "passed" means, under the band on every build (SI-1, amended 2026-11-15)
PASSED_WORDS = ("Passed", ": all six of our ", "checks", " passed. No check tries to ",
                "forge a proof", ".")  # fmt: skip
# while no model has two systems run on it (SI-1, amended 2026-11-15): no row was ranked against
# another, and the line goes by itself once one model has two
ALONE_WORDS = "No two systems have yet been measured on the same model."


def band_html():
    """The band: the title on one line, and under it the lead (`lead_html`). The frontier (OR-6)
    is not named in the title: its rung, in the ladder under the band, is marked as the largest
    model proved (`rung_html`), and its rows say who passed there and at what multiple."""
    run = any(r["rows"] for r in S.V["rungs"])
    title = "Proved inference, by model size" if run else "No system has run yet."
    return f'<h1 class="band-h">{e(title)}</h1>{lead_html(run)}'


def lead_html(run):
    """At most three sentences under the title, for a reader with no context: what a proof of
    inference is, what the ladder holds and, from the board, on how many models a system passed
    and, on the largest of them, its figure (`board_words`). No figure of one model is set beside
    another model's."""
    said = [PROOF_WORDS] + ([LADDER_WORDS, board_words()] if run else [])
    return f'<p class="lede">{" ".join(said)}</p>'


def board_words():
    """On how many of the models a system passed, and on the largest such model (OR-6's
    frontier) its size and the figure of its one row there, with its unit and its labels in its
    title; with more than one row there, their count instead. Words escaped, the figure html."""
    rungs = S.V["rungs"]
    passed = sum(1 for r in rungs if any(row["passed"] for row in r["rows"]))
    front = S.V["frontier"]
    rung = next((r for r in rungs if front and r["id"] == front["rung"]), None)
    if rung is None or not passed:
        return e(f"No system has passed on any of the {len(rungs)} models yet.")
    where = f"{nobreak(rung['model'])} ({e(params(rung['parameters_total']))} parameters)"
    rows = front["rows"]
    if len(rows) == 1:
        row = rows[0]
        _, f, key = lead_figure(row)
        fig = fig_html(f, counted(row), sub=BARE, note=whole_note(row, key)) if has(f) else None
        name = f'<a href="{e(href(row))}">{e(name_of(row))}</a>'
        what = (f"a reply {name} proves with its verifier costs {fig} as much as serving it" if fig
                else f"{name} passed")  # fmt: skip
    else:
        what = f"{len(rows)} systems passed"
    head = e(f"A system passed on {passed} of the {len(rungs)} models")
    if passed == 1:
        return f"{head}: {where}, where {what}."
    return f"{head}; on the largest, {where}, {what}."


def head_html():
    """The lines between the band and the ladder: what "passed" means (always), and, while no
    model has two systems run on it, that none has (`alone`)."""
    if not any(r["rows"] for r in S.V["rungs"]):
        return ""
    a, b, c, d, f, g = PASSED_WORDS
    lines = [f'<p><a class="df" href="{CHECKS_PAGE}#passed">{e(a)}</a>{e(b)}'
             f'<a href="{CHECKS_PAGE}">{e(c)}</a>{e(d)}'
             f'<a href="{CHECKS_PAGE}#not-tested">{e(f)}</a>{e(g)}</p>']  # fmt: skip
    if alone(S.V["rungs"]):
        lines.append(f'<p class="lal">{e(ALONE_WORDS)}</p>')
    return f'<div class="lhd">{"".join(lines)}</div>'


def alone(rungs):
    """Whether no model has two or more systems run on it, while at least one has a row."""
    return any(r["rows"] for r in rungs) and all(r["systems_run"] < 2 for r in rungs)


def not_run_html():
    """The systems not run (SI-4), grouped by their reason, A to Z, each group's names A to Z
    in display type: each reason is said once."""
    if not S.V["not_run"]:
        return ""
    groups: dict[str, list[dict]] = {}
    for r in S.V["not_run"]:
        groups.setdefault(r["reason"], []).append(r)
    rows = "".join(
        f'<div><dt>{e(reason)}</dt><dd><ul class="nrl">'
        + "".join(f'<li id="nr-{e(r["id"])}"><span class="nn">{e(r["name"])}</span></li>'
                  for r in sorted(groups[reason], key=lambda r: r["name"].lower()))
        + "</ul></dd></div>"
        for reason in sorted(groups, key=str.lower)
    )  # fmt: skip
    return (f'<section class="notrun" aria-labelledby="h-notrun"><h2 class="nrh" id="h-notrun">'
            f'<a href="{CHECKS_PAGE}#not-run">Systems not run</a></h2><dl class="nrg">{rows}</dl></section>')  # fmt: skip


def build_index():
    rungs = "".join(rung_html(r) for r in S.V["rungs"])
    body = f"""
{header("home")}
<main id="main" class="home">
  <section class="mast"><div class="mast-in">{band_html()}</div></section>
  <div class="wrap ladder">{head_html()}{rungs}</div>
  <div class="wrap">{not_run_html()}</div>
</main>
{footer()}"""
    return page("Inference proofs", home_words(), body, "home", "", "home")


def home_words():
    """The home page in a sentence (its description and share text): what a proof states, the
    largest model one proved on (OR-6; left out while there is none), and what each row holds."""
    front = S.V["frontier"]
    rung = next((r for r in S.V["rungs"] if front and r["id"] == front["rung"]), None)
    size = f" up to {params(rung['parameters_total'])} parameters" if rung else ""
    return (f"Proofs that a reply is the one a committed model returns for a prompt, from systems "
            f"run on open-weights models{size}: six checks each, and the cost of a proved reply as "
            "a multiple of serving it.")  # fmt: skip
