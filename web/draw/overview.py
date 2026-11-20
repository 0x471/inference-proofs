"""The Overview page (`overview.html`, RFC-0018 SI-7): the ladder drawn to scale, every system
on one drawing, one figure at a time (cost vs serving, proof size and verify time per reply,
Fidelity; USD is printed under Cost on a system's page only).

Each figure is a section; the strip of sections picks the one drawn (words.js, which moves each
mark to its new place), and with no script all four are drawn. A section is one drawing: its
figure's axis across the top, and each model a rung, a cobalt rule set at the height of its
parameter count on a decade axis, largest at the top. A system is a mark on its model's rung at
its stored figure, and under the mark its flag: its position, name, standing and the figure, as
`fig_html` prints it (its labels in its title, and in full on the system's page the name links
to), beside its glyph. Flags hang one under the other in the board's order (OR-5), so two never
meet. Every rung shares the figure's one axis (`extent` over the whole board), so a change of
scale between models is seen by position; nothing is ranked, divided or ordered across rungs,
and no mark joins two rungs. The systems not run stand under the drawing by their reason, as on
the ladder: no figure of ours places them.

Where the models' sizes leave too little room between two rungs for their flags, the rungs are
set one under the other, evenly, and no size axis is drawn (`layout`); a narrow screen always
reads so.

A mark is a position only. Its place is a custom property set by the page's own rules
(`place_css`: `--x` across the figure's axis, `--y` down the size axis), written here from the
view, so text keeps its size at any width and no inline style is needed. The drawings beside
them (axes, the sessions' ticks, the marks a figure is read against) are SVG with no viewBox,
each horizontal coordinate a percentage of its plot. No quotient computed here is printed.
"""

import itertools
import math
import re

from . import state as S
from .chrome import (
    CHECKS_PAGE,
    OVERVIEW_PAGE,
    counted,
    footer,
    has,
    header,
    lead_figure,
    page,
    pnav,
)
from .hexagon import glyph_svg
from .ladder import (
    BARE,
    ROW_GLYPH,
    copies_of,
    fidelity_row,
    fidelity_word,
    fig_html,
    href,
    multiple_html,
    name_of,
    nobreak,
    not_run_html,
    pct,
    position_html,
    proved_words,
    scope_note,
    served_html,
    standing_html,
    states,
    states_words,
)
from .pages import title_band
from .plots import decade_words, lin_x, log_extent, log_x, pc
from .words import (
    COPY_WORD,
    FIGURE_ANCHOR,
    FIGURE_HEAD,
    FIGURE_RULE,
    FRONTIER_WORD,
    OVERVIEW_LEAD,
    PETAL_NAME,
    SCALE_LOG,
    SCALE_NOT_RUN,
    SCALE_SERVING,
    SIZE_AXIS,
    architecture,
    e,
    number,
    params,
)

# the figures, in the strip's order (the first is drawn when the address names none): the section's
# id and the stored unit its axis reads in; its name is FIGURE_HEAD's
DIMS = (("multiple", "ratio"), ("proof-size", "B/request"), ("check-time", "s/request"),
        ("fidelity", "percent"))  # fmt: skip
# a stored value in the unit `words.number` reads it in (bytes read as MB); 1 for the others
READING = {"B/request": 1e-6}
# Martian Mono's advance, in em, at the width the site sets it (87.5 %): every glyph alike,
# measured in the served face by the browser (11 px tick labels: 7.15 px a character)
ADV, TICK_PX = 0.65, 11
# the narrowest plot each set of tick labels is drawn for (words.css): beside the models' heads
# from 1181 px (699 px) and from 901 px (435 px), under them from 601 px (537 px), and a phone of
# 320 px (272 px)
PLOT_FULL, PLOT_WIDE, PLOT_NARROW = 696, 432, 272
AXIS_H = 32  # the figure's axis over the drawing
RULE_H = 28  # the drawing on a rung's rule: its height in px (the rule runs through its middle)
# The size axis (`layout`), in px: a decade's height at least; at most with whole flags, and at
# most with flags on one line (four decades then stand about 1,000 and 1,300 px tall)
DECADE, DECADE_WHOLE, DECADE_LINES = 130, 250, 320
# What words.css gives a rung's parts, in px, measured in the browser (`needs` adds them up, a
# little over what is drawn). A head: its size tab, the frontier's line, the room over its name, a
# line of its name (two lines from NAME_WRAP characters), a line of its facts (its architecture,
# its serving rate), the room over the copies' lines and one of them, the room under the head
TAB_H, FRONT_H, NAME_TOP, NAME_H, NAME_WRAP, FACT_H, COPY_TOP, COPY_H, HEAD_FOOT = (
    26, 22, 12, 26, 21, 28, 8, 20, 16)  # fmt: skip
# a flag: its padding, then its words (name, figure, standing; its glyph is no taller); one more
# line of a long name (from FLAG_WRAP characters), of the checks not passed, of what it proves
FLAG_PAD, FLAG_WORDS, FLAG_WRAP, FLAG_LINE, PROVED_WRAP = 28, 88, 17, 20, 28
# a flag on one line (`layout`): its height, and the line under it of what it proves
LINE_FLAG, LINE_SUB = 46, 22
RUNG_GAP = 28  # from a rung's last line to the next rule
EMPTY_H = 56  # a model no system has run on: its one line
SIZE_TOP = 28  # the room over the size axis's first decade, under the figure's axis


def place_css(eid, **places):
    """One rule of the page's own: the custom properties that place the element with this id
    (a rung's `y`, a mark's `x`, the drawing's `h`). An id may hold a dot ("llama-3.1-8b"), which
    a selector escapes."""
    name = re.sub(r"([^A-Za-z0-9_-])", r"\\\1", eid)
    return f"#{name}{{{';'.join(f'--{k}:{v}' for k, v in places.items())}}}"


# ------------------------------------------------------------------ what a rung draws, per figure
def read(v, unit):
    return v * READING.get(unit, 1) if v is not None else None


def baseline_value(rung, key):
    b = rung["baseline"]
    return b[key]["value"] if b and has(b[key]) else None


def figure_of(row, dim):
    """The row's one stored figure for this dimension, as the ladder prints it (the multiple at
    the whole sessions' scope wherever the row has it: `lead_figure`); None for Fidelity, whose
    figure is the rung's teacher-forced record's (`fidelity_row`)."""
    figs = row["figures"]
    if dim == "multiple":
        return lead_figure(row)[1]
    if dim == "fidelity":
        return None
    return figs["verify_seconds_per_reply" if dim == "check-time" else "proof_bytes_per_reply"]


def value_of(row, dim, unit):
    """Where the row's mark sits, in the axis's unit: the figure the ladder prints, or None
    where it prints none (a null figure; a Fidelity that reads as the check's state) and where a
    decade axis has no place for it (a stored value of zero or less: the flag still prints it)."""
    if dim == "fidelity":
        mine = fidelity_row(row)
        return mine["percent"] if mine else None
    f = figure_of(row, dim)
    v = read(f["value"], unit) if has(f) else None
    return v if v is not None and v > 0 else None


def ticks_of(row, dim, rung):
    """Where the counted sessions sit, in the axis's unit: the multiple from each session's GPU
    time at the printed figure's scope (the whole session, or m where the row has only a steady
    figure), placed by the rung's serving GPU time; none for the other figures, which store no
    value per session."""
    if dim != "multiple":
        return []
    steady = lead_figure(row)[2] == "multiple"
    vals = [s.get("m" if steady else "session") for s in row["sessions"]]
    b = baseline_value(rung, "gpu_seconds_per_reply")
    return [v / b for v in vals if v is not None] if b else []


def marks_of(row, dim, rung, unit):
    """(mean, ticks, range) in the axis's unit: the figure, its sessions, and the stretch they
    cover (or the figure's stored minimum and maximum where no session value is stored). A row
    with no mark has no ticks and no range; a value a decade axis cannot place is left out."""
    mean = value_of(row, dim, unit)
    if mean is None:
        return None, [], None
    ticks = [t for t in ticks_of(row, dim, rung) if t > 0]
    stats = (figure_of(row, dim) or {}).get("stats") or {}
    if len(ticks) > 1:
        span = (min(ticks), max(ticks))
    elif not ticks and stats.get("min") is not None and stats.get("max") is not None:
        span = (read(stats["min"], unit), read(stats["max"], unit))
        span = span if span[0] > 0 else None
    else:
        span = None
    return mean, ticks, span


def against_of(rung, dim):
    """What a rung's figures are read against on this axis, as (value, words, title): serving at
    1× on the multiple's (serving over itself; only where the rung's head prints its serving
    rate, so the mark and the head read one record), the model's 8-bit and 4-bit copies on
    Fidelity's (SI-9); nothing for a rung with no row (nothing is read against it), where the
    rung has none, or for a figure with no such counterpart."""
    if not rung["rows"]:
        return []
    if dim == "multiple":
        served = all(baseline_value(rung, k)
                     for k in ("gpu_seconds_per_reply", "reply_tokens_per_gpu_second"))  # fmt: skip
        return [(1.0, SCALE_SERVING, f"{SCALE_SERVING}: 1×")] if served else []
    if dim == "fidelity":
        return [(v, COPY_WORD[i].removesuffix(" copy"), f"{COPY_WORD[i]} ({i.upper()})")
                for i, v in copies_of(rung)]  # fmt: skip
    return []


def values(dim, unit, rungs):
    """Every value the dimension draws on these rungs: figures, sessions, ranges, and what they
    are read against. A decade axis holds values above zero only; Fidelity's holds zero too."""
    out = []
    for rung in rungs:
        out += [v for v, _, _ in against_of(rung, dim)]
        for row in rung["rows"]:
            mean, ticks, span = marks_of(row, dim, rung, unit)
            out += [mean, *ticks, *(span or ())]
    return [v for v in out if v is not None and (v > 0 or dim == "fidelity")]


# ------------------------------------------------------------------ the figure's axis
def extent(vals, ratio=False):
    """The decades drawn, (lo, hi): from the decade of the smallest value to one past the
    largest's, never fewer than two; a multiple's axis starts at 1× at most. None with no value."""
    if not vals:
        return None
    lo, hi = log_extent(vals)
    return (min(0, lo), hi) if ratio else (lo, hi)


def share_extent(vals):
    """Fidelity's axis, (lo, 100), in percent: from the ten under the lowest drawn value, 90 at
    most, as a system page's Fidelity drawing reads (Q50). None with no value."""
    if not vals:
        return None
    return (min(90, 10 * math.floor(min(vals) / 10)), 100)


def axis_of(dim, unit, rungs):
    """The figure's one axis over these rungs, or None with nothing to draw: its ends (`lo`,
    `hi`: decades, or percent for Fidelity), where a value sits on it (`at`, in percent of the
    plot's width), its ticks as (place, words) and its minor ticks' places."""
    vals = values(dim, unit, rungs)
    if dim == "fidelity":
        ext = share_extent(vals)
        if ext is None:
            return None
        lo, hi = ext
        ticks = [(lin_x(v, lo, hi), f"{v}\u202f%") for v in range(lo, hi + 1, 5)]
        return {"lo": lo, "hi": hi, "at": lambda v: lin_x(v, lo, hi), "ticks": ticks, "minor": []}
    ext = extent(vals, unit == "ratio")
    if ext is None:
        return None
    lo, hi = ext
    ticks = [(log_x(10**k, lo, hi), tick_words(k, unit)) for k in range(lo, hi + 1)]
    minor = [log_x(m * 10**k, lo, hi) for k in range(lo, hi) for m in (2, 5)]
    return {"lo": lo, "hi": hi, "at": lambda v: log_x(v, lo, hi), "ticks": ticks, "minor": minor}


def tick_words(k, unit):
    """A decade as the axis prints it: a display word, not a measurement."""
    return f"{decade_words(k)}×" if unit == "ratio" else decade_words(k)


def labelled(ticks, width):
    """The ticks labelled on a plot `width` px wide, by index: every k-th from the first, k the
    least for which two labels never meet (a start-anchored end label beside a centred one is the
    worst pair)."""
    last = len(ticks) - 1
    w = max(len(words) for _, words in ticks) * ADV * TICK_PX
    d = width / last
    k = next(k for k in range(1, last + 1) if k * d >= 1.5 * w + 12 or k == last)
    return set(range(0, last + 1, k))


def axis_svg(axis, cls="ax"):
    """The figure's axis: a tick at each of its ticks and a short one at each minor one, and the
    ticks' words in three sets, for a desktop's plot, a narrower one and a phone's (words.css
    shows one)."""
    ticks = axis["ticks"]
    out = [f'<line class="mn" x1="{pc(x)}" x2="{pc(x)}" y1="25" y2="{AXIS_H}"/>'
           for x in axis["minor"]]  # fmt: skip
    out += [f'<line class="mj" x1="{pc(x)}" x2="{pc(x)}" y1="18" y2="{AXIS_H}"/>'
            for x, _ in ticks]  # fmt: skip
    for tl, width in (("x", PLOT_FULL), ("w", PLOT_WIDE), ("n", PLOT_NARROW)):
        for i in sorted(labelled(ticks, width)):
            x, words = ticks[i]
            anchor = "start" if i == 0 else "end" if i == len(ticks) - 1 else "middle"
            out.append(f'<text class="tl {tl}" x="{pc(x)}" y="12" text-anchor="{anchor}">'
                       f"{e(words)}</text>")  # fmt: skip
    return (f'<svg class="{cls}" width="100%" height="{AXIS_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def grid_svg(axis):
    """The axis's lines down the whole drawing, behind every rung: one grid for all of them."""
    lines = "".join(f'<line x1="{pc(x)}" x2="{pc(x)}" y1="0" y2="100%"/>' for x, _ in axis["ticks"])
    return (f'<svg class="ovg" width="100%" height="100%" aria-hidden="true" focusable="false">'
            f"{lines}</svg>")  # fmt: skip


# ------------------------------------------------------------------ the size axis
def size_words(k):
    """A decade of parameters as the size axis prints it ("100M", "1B", "1T"): a place on the
    scale, not a model's size."""
    for power, sign in ((12, "T"), (9, "B"), (6, "M"), (3, "K")):
        if k >= power:
            return f"{10 ** (k - power):,}{sign}"
    return f"{10**k:,}"


def head_needs(rung, dim):
    """The height of a rung's head on this figure's drawing, in px."""
    front = S.V["frontier"]
    lines = 2 if len(rung["model"]) >= NAME_WRAP else 1
    h = TAB_H + NAME_TOP + lines * NAME_H + FACT_H + HEAD_FOOT
    if front and front["rung"] == rung["id"]:
        h += FRONT_H
    if dim == "multiple":
        h += FACT_H
    elif dim == "fidelity" and (copies := copies_of(rung)):
        h += COPY_TOP + COPY_H * len(copies)
    return h


def flag_needs(row, dim, lines):
    """The height of a system's flag on this figure's drawing, in px; `lines`: set on one line."""
    proved = proved_words(row) if dim == "fidelity" else ""
    if lines:
        h = LINE_FLAG + (LINE_SUB if proved else 0)
        # the checks not passed, or why the row is not ranked, may take a second line
        return h if row["passed"] and row["ranked"] else h + FLAG_LINE
    h = FLAG_PAD + FLAG_WORDS
    if len(name_of(row)) >= FLAG_WRAP:
        h += NAME_H
    if not (row["passed"] and row["ranked"]):
        h += FLAG_LINE
    if proved:
        h += 4 + FLAG_LINE * math.ceil(len(proved) / PROVED_WRAP)
    return h


def needs(rung, lines=False):
    """The room a rung takes under its rule, in px, on the figure where it takes the most: its
    head, or its flags one under the other. One figure for all, so a rung stands at one height
    on every drawing and a mark moves across only when the figure changes."""

    def on(dim):
        rows = rung["rows"]
        flags = sum(flag_needs(row, dim, lines) for row in rows) if rows else EMPTY_H
        return max(head_needs(rung, dim), flags)

    return max(on(dim) for dim, _ in DIMS)


def layout(rungs):
    """Where each rung stands: `scaled`, whether the rungs are set by size; `lines`, whether a
    flag is set on one line; then, when scaled, the size axis's decades (`lo`, `hi`), a
    decade's height in px (`px`), each rung's distance from the drawing's top in px (`ys`: the
    rule's middle, at its parameter count on the decade axis, the largest decade at the top) and
    the drawing's `height`.

    A decade is DECADE px tall, or as tall as the tightest pair of rungs needs to hold the upper
    one's head and flags. Where that makes a decade taller than DECADE_WHOLE the flags are set
    on one line, without their glyphs; where a decade is then taller than DECADE_LINES, or two
    models are the same size, the rungs are not set by size and the flags stay whole."""
    sizes = [math.log10(r["parameters_total"]) for r in rungs]
    gaps = [a - b for a, b in itertools.pairwise(sizes)]
    if not rungs or any(g <= 0 for g in gaps):
        return {"scaled": False, "lines": False}
    lo, hi = math.floor(min(sizes)), math.floor(max(sizes)) + 1
    for lines, most in ((False, DECADE_WHOLE), (True, DECADE_LINES)):
        room = [needs(r, lines) for r in rungs]
        px = max([DECADE, *((n + RUNG_GAP) / g for n, g in zip(room, gaps, strict=False))])
        if px <= most:
            ys = [round(SIZE_TOP + (hi - s) * px, 1) for s in sizes]
            height = max(SIZE_TOP + (hi - lo) * px, ys[-1] + room[-1]) + RUNG_GAP
            return {"scaled": True, "lines": lines, "lo": lo, "hi": hi, "px": px, "ys": ys,
                    "height": math.ceil(height)}  # fmt: skip
    return {"scaled": False, "lines": False}


def size_svg(lay):
    """The size axis down the drawing's right side: a tick and its words at each decade, largest
    at the top, and a short paper tick where each rung stands."""
    lo, hi, px, ys, height = lay["lo"], lay["hi"], lay["px"], lay["ys"], lay["height"]
    foot = SIZE_TOP + (hi - lo) * px
    out = [f'<line class="sa" x1="0" x2="0" y1="{SIZE_TOP}" y2="{foot:.1f}"/>']
    for k in range(hi, lo - 1, -1):
        y = SIZE_TOP + (hi - k) * px
        out.append(f'<line class="mj" x1="0" x2="8" y1="{y:.1f}" y2="{y:.1f}"/>'
                   f'<text class="tl" x="14" y="{y + 4:.1f}">{e(size_words(k))}</text>')  # fmt: skip
    out += [f'<line class="at" x1="-6" x2="6" y1="{y}" y2="{y}"/>' for y in ys]
    return (f'<svg class="ovs" width="100%" height="{height}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


# ------------------------------------------------------------------ a rung
def rule_svg(axis, rung, dim, unit):
    """What is drawn on a rung's rule beside its marks: each row's sessions as ticks and the
    stretch they cover, and what the rung's figures are read against, each an outlined diamond
    with its word over the rule (two words that would meet stand on two lines). An outlined
    square is a row not passed, never one of these."""
    mid = RULE_H / 2
    out = []
    for row in rung["rows"]:
        _, ticks, span = marks_of(row, dim, rung, unit)
        cls = "ok" if row["passed"] else "np"
        if span is not None:
            out.append(f'<line class="rg {cls}" x1="{pc(axis["at"](span[0]))}" '
                       f'x2="{pc(axis["at"](span[1]))}" y1="{mid:g}" y2="{mid:g}"/>')  # fmt: skip
        # as tall as the mark, so sessions under it hide behind it and only a spread one shows
        out += [f'<line class="ss {cls}" x1="{pc(axis["at"](t))}" x2="{pc(axis["at"](t))}" '
                f'y1="{mid - 7:g}" y2="{mid + 7:g}"/>' for t in ticks]  # fmt: skip
    refs = sorted(against_of(rung, dim), key=lambda r: r[0])
    for i, (v, words, title) in enumerate(refs):
        x = axis["at"](v)
        anchor = "start" if x < 8 else "end" if x > 92 else "middle"
        # the plot may be 272 px wide: a word's width there, in percent, against the next mark's
        near = i and (x - axis["at"](refs[i - 1][0])) * PLOT_NARROW / 100 < len(words) * 7 + 8
        y = -15 if near and i % 2 else -3
        out.append(f'<svg class="rfm" x="{pc(x)}" y="{mid:g}" overflow="visible">'
                   f"<title>{e(title)}</title>"
                   '<rect x="-5" y="-5" width="10" height="10" transform="rotate(45)"/>'
                   f'<text y="{y - mid + 4:g}" text-anchor="{anchor}">{e(words)}</text></svg>')  # fmt: skip
    return (f'<svg class="ork" width="100%" height="{RULE_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>') if out else ""  # fmt: skip


def figure_html(row, dim):
    """The row's figure as the ladder prints it (the multiple's two parts are the system page's,
    CO-7; Fidelity with what the row proves under it, SI-9: the model's two copies are said once,
    in its head)."""
    if dim == "multiple":
        return multiple_html(row, bare=True)
    if dim == "fidelity":
        return fidelity_word(row, against=False)
    f = figure_of(row, dim)
    return fig_html(f, counted(row), sub=BARE, note=scope_note(row, f))


def flags_html(rung, dim, unit, axis, css):
    """A rung's systems: each a mark on the rule at its figure and its flag under it, one box
    inside the next in the board's order (OR-5), so each flag hangs under those before it and
    its pole runs from the rule to its foot. A flag stands right of its pole in the plot's left
    half and left of it in the right half, so it keeps to the plot. A row with no figure here
    (a null figure, a Fidelity that reads as the check's state) has its flag, which says so, and
    no mark. Each box's place goes to `css`."""
    inner = ""
    for row in rung["rows"]:
        mean, _, _ = marks_of(row, dim, rung, unit)
        x = axis["at"](mean) if mean is not None and axis is not None else None
        bid = f"ob-{dim}-{row['page']}"
        css.append(place_css(bid, x=pc(x if x is not None else 0)))
        at, name = e(href(row)), e(name_of(row))
        arms = glyph_svg(ROW_GLYPH, states(row), names=[PETAL_NAME[p["id"]] for p in row["glyph"]])
        # the petals in words for a screen reader, after the name they belong to
        flag = (
            f'<div class="ofl row{" r" if x is not None and x > 50 else ""}" data-s="{e(row["page"])}">'
            f'<a class="glyph" href="{at}" tabindex="-1" aria-hidden="true">{arms}</a>'
            f'<div class="ofw"><p class="ofn">{position_html(row, rung)}'
            f'<a class="sname" href="{at}">{name}</a></p>'
            f'<span class="sr pw">{states_words(row)}</span>'
            f'<p class="off">{figure_html(row, dim)}</p>'
            f'<p class="st">{standing_html(row)}</p></div></div>'
        )
        marks = ("" if x is None else
                 f'<i class="ld" data-s="{e(row["page"])}"></i><i class="gd"></i>'
                 f'<a class="mk" href="{at}" tabindex="-1" aria-hidden="true" '
                 f'data-s="{e(row["page"])}"></a>')  # fmt: skip
        state = "ok" if row["passed"] else "np"
        inner = (f'<div class="obx {state}{"" if x is not None else " nov"}" id="{bid}">'
                 f"{inner}{flag}{marks}</div>")  # fmt: skip
    return inner


def head_html(rung, dim, hid):
    """A model's head, under its rule's left end: its size in a tab (the frontier's rung marked
    beside it, OR-6), its name, its architecture (the tab says its size: a mixture of experts
    names its active parameters only), and what the figure drawn is read against, said once for
    the rung: its serving rate beside the multiple (its state where the model has none, as on
    the ladder), its two copies' Fidelity beside Fidelity."""
    total, active = rung["parameters_total"], rung.get("parameters_active")
    front = S.V["frontier"]
    mark = f'<p class="rf">{e(FRONTIER_WORD)}</p>' if front and front["rung"] == rung["id"] else ""
    against = ""
    if dim == "multiple":
        against = (f'<p class="lsv"><span class="k">{e(SCALE_SERVING)}</span>'
                   f"{served_html(rung['baseline'])}</p>")  # fmt: skip
    elif dim == "fidelity" and (copies := copies_of(rung)):
        against = '<p class="lsv lcp">' + "".join(
            f"<span>{e(COPY_WORD[i])} {pct(v)}\u202f%</span>" for i, v in copies) + "</p>"  # fmt: skip
    return (f'<header class="orh"><p class="rk">{e(params(total))}</p>{mark}'
            f'<h3 class="ln" id="{hid}">{nobreak(rung["model"])}</h3>'
            f'<p class="lf">{nobreak(architecture(total, active, sized=False))}</p>'
            f"{against}</header>")  # fmt: skip


def rung_html(rung, dim, unit, axis, css):
    """One model: its rule, its head under the rule's left end and, on the rule, its systems
    (`flags_html`) and what they are read against (`rule_svg`); each rung also carries the
    figure's axis, which a drawing with no size axis prints over every rung. A model not run is
    its head and a line; where no row of the board has the figure, the flags stand with no axis."""
    rid = f"ov-{dim}-{rung['id']}"
    hid = f"h-{rid}"
    head = head_html(rung, dim, hid)
    if not rung["rows"]:
        body = f'<p class="onr">{e(SCALE_NOT_RUN)}</p>'
        ticks = ""
    else:
        drawn = rule_svg(axis, rung, dim, unit) if axis is not None else ""
        body = drawn + flags_html(rung, dim, unit, axis, css)
        ticks = axis_svg(axis, "ax orx") if axis is not None else ""
    return (f'<section class="org" id="{rid}" aria-labelledby="{hid}">{head}{ticks}'
            f'<div class="ort">{body}</div></section>')  # fmt: skip


# ------------------------------------------------------------------ a section, the page
def panel_html(dim, unit, css):
    """One figure's section: its name and its axis across the top, then the drawing: the grid,
    the size axis where the rungs are set by size, and a rung per model, largest first. The
    drawing's and the rungs' places go to `css`."""
    rungs = S.V["rungs"]
    name = FIGURE_HEAD[dim]
    axis = axis_of(dim, unit, rungs)
    lay = layout(rungs)
    scaled = lay["scaled"]
    anchor = FIGURE_ANCHOR.get(dim, dim)
    named = (f'<a class="df" href="{CHECKS_PAGE}#{anchor}">{e(name)}</a>' if dim in FIGURE_RULE
             or dim in FIGURE_ANCHOR else e(name))  # fmt: skip
    if dim == "fidelity":
        words = '<span class="u">%</span>'
    else:
        # the unit keeps its own case in the uppercased head ("s/reply", not "S/REPLY")
        _, sign = number(1, unit)
        rest = f" {SCALE_SERVING.lower()}" if unit == "ratio" else ""
        words = f'<span class="u">{e(sign)}</span>{e(rest)}, {e(SCALE_LOG)}'
    top = axis_svg(axis) if axis is not None else ""
    lo, hi = (axis["lo"], axis["hi"]) if axis is not None else (0, 1)
    if scaled:
        css.append(place_css(f"ov-{dim}", h=f"{lay['height']}px"))
        css += [place_css(f"ov-{dim}-{r['id']}", y=f"{y}px")
                for r, y in zip(rungs, lay["ys"], strict=True)]  # fmt: skip
    size = (f'<p class="ovz">{e(SIZE_AXIS)}</p>', size_svg(lay)) if scaled else ("", "")
    body = "".join(rung_html(r, dim, unit, axis, css) for r in rungs)
    grid = grid_svg(axis) if axis is not None else ""
    return (
        f'<section class="blk ovp" id="{dim}" aria-labelledby="h-{dim}">'
        f'<div class="ov {"osc" if scaled else "oev"}{" oln" if lay["lines"] else ""}" id="ov-{dim}" data-lo="{lo}" data-hi="{hi}">'
        f'<div class="ovh"><h2 class="ovt" id="h-{dim}">{named}</h2>'
        f'<div class="ova"><span class="al">{words}</span>{top}</div>{size[0]}</div>'
        f'<div class="ovb">{grid}{size[1]}{body}</div></div></section>'
    )


def build_overview():
    css: list[str] = []
    panels = "".join(panel_html(d, u, css) for d, u in DIMS)
    body = f"""
{header("overview")}
<main id="main" class="sys">
  {title_band("Overview")}
  {pnav("Overview", [(d, FIGURE_HEAD[d]) for d, _ in DIMS])}
  <div class="wrap">{panels}{not_run_html()}</div>
</main>
{footer()}"""
    return page("Overview", overview_words(), body, "system overviewpage",
                OVERVIEW_PAGE.strip("/"), "home", css="".join(css))  # fmt: skip


def overview_words():
    """The overview page in a line (its description and its search line): its figures' names in
    lower case."""
    return f"{OVERVIEW_LEAD}: {', '.join(FIGURE_HEAD[d].lower() for d, _ in DIMS)}."
