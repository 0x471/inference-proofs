"""The Overview page (`overview.html`, RFC-0018 SI-7): every system run on one drawing, two
figures at a time. Cost vs serving runs across; verify time, proof size or Fidelity runs up
(USD is printed under Cost on a system's page only).

Each figure that runs up is a section; the strip of sections picks the one drawn (words.js,
which moves each system to its new place), and with no script all three are drawn. A section is
one plot: a system is a mark where its two stored figures meet, and beside the mark its flag:
its glyph, drawn larger the larger its model (`unit_of`: a step of size, not an area to
measure; the model's size is printed in the flag), its position and name, its model, the two
figures as `fig_html` prints them (their labels in their titles, and in full on the system's
page the name links to) and its standing. A row with a figure missing has no place on the plot:
it is listed under it, with what is missing said in words. Under the sections the models stand
once, largest first, each with the size its systems' glyphs are drawn at, and a model no system
has run on says so. The systems not run stand under them by their reason, as on the ladder: no
figure of ours places them.

Every system shares the two axes (`extent` over the whole board), so a change of scale between
models is seen by position; nothing is ranked, divided or ordered across models, and no mark
joins two systems.

A mark is a position only. Its place is a custom property set by the page's own rules
(`place_css`: `--x` across, `--y` up, and the glyph's unit `--u`), written here from the view,
so text keeps its size at any width and no inline style is needed. The axes, the grid and the
sessions' ticks are SVG with no viewBox, each coordinate a percentage of the plot. A flag stands
on the side of its mark where it meets no other flag (`flag_sides`, on a plot of the size a wide
screen draws). No quotient computed here is printed.
"""

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
    fidelity_row,
    fidelity_word,
    fig_html,
    href,
    multiple_html,
    name_of,
    nobreak,
    not_run_html,
    position_html,
    scope_note,
    served_html,
    standing_html,
    states,
    states_words,
)
from .pages import title_band
from .plots import decade_words, lin_x, log_extent, log_x, pc
from .words import (
    FIGURE_ANCHOR,
    FIGURE_HEAD,
    FIGURE_RULE,
    FRONTIER_WORD,
    OVERVIEW_LEAD,
    OVERVIEW_OFF,
    PETAL_NAME,
    SCALE_LOG,
    SCALE_NOT_RUN,
    SCALE_SERVING,
    architecture,
    e,
    number,
    params,
)

# the figure that runs across every plot, and the figures that run up, in the strip's order (the
# first is drawn when the address names none): the section's id and the stored unit its axis
# reads in; a figure's name is FIGURE_HEAD's
ACROSS = ("multiple", "ratio")
DIMS = (("check-time", "s/request"), ("proof-size", "B/request"), ("fidelity", "percent"))
# a stored value in the unit `words.number` reads it in (bytes read as MB); 1 for the others
READING = {"B/request": 1e-6}
# Martian Mono's advance, in em, at the width the site sets it (87.5 %): every glyph alike,
# measured in the served face by the browser (11 px tick labels: 7.15 px a character)
ADV, TICK_PX = 0.65, 11
# the narrowest plot each set of tick labels is drawn for (words.css): a desktop's (from 1181 px),
# a narrower one (from 761 px) and a phone of 320 px
PLOT_FULL, PLOT_WIDE, PLOT_NARROW = 960, 600, 240
AXIS_H = 34  # the axis under the plot
# The plot `flag_sides` places the flags on, in px (a wide screen's), and a flag's parts there:
# the glyph's size per unit, the room between it and the words, the words' width at least, a
# character of a name and of a model's line, the words' height, the flag's padding, and how far
# a flag stands from its mark
PLOT_W, PLOT_H = 1100, 560
GLYPH_W, GLYPH_H, GLYPH_GAP, WORDS_W, NAME_CH, LINE_CH, WORDS_H, FLAG_PAD, FLAG_OFF = (
    53, 29, 14, 230, 14, 7, 104, 20, 12)  # fmt: skip
# a glyph's unit, in px, by its model's size: UNIT at 100M parameters and UNIT_STEP more for each
# decade, between UNIT_LEAST and UNIT_MOST (the ladder's is 3)
UNIT, UNIT_STEP, UNIT_LEAST, UNIT_MOST = 1.6, 0.5, 1.4, 3.8


def place_css(eid, **places):
    """One rule of the page's own: the custom properties that place the element with this id
    (a mark's `x` and `y`, a glyph's unit `u`). An id may hold a dot ("llama-3.1-8b"), which a
    selector escapes."""
    name = re.sub(r"([^A-Za-z0-9_-])", r"\\\1", eid)
    return f"#{name}{{{';'.join(f'--{k}:{v}' for k, v in places.items())}}}"


# ------------------------------------------------------------------ what a system draws, per figure
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
    """Where the row sits on this figure's axis, in the axis's unit: the figure the ladder
    prints, or None where it prints none (a null figure; a Fidelity that reads as the check's
    state) and where a decade axis has no place for it (a stored value of zero or less)."""
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
    return [v / b for v in vals if v is not None and v > 0] if b else []


def spread_of(row, dim, rung, unit):
    """(ticks, range) on this figure's axis: the row's sessions, and the stretch they cover (or
    the figure's stored minimum and maximum where no session value is stored)."""
    ticks = ticks_of(row, dim, rung)
    stats = (figure_of(row, dim) or {}).get("stats") or {}
    if len(ticks) > 1:
        return ticks, (min(ticks), max(ticks))
    if not ticks and stats.get("min") is not None and stats.get("max") is not None:
        span = (read(stats["min"], unit), read(stats["max"], unit))
        return ticks, span if span[0] > 0 else None
    return ticks, None


def drawn(row, dim, unit):
    """(x, y) in the axes' units where the row has both figures, else None: such a row has no
    place on the plot and is listed under it."""
    x, y = value_of(row, *ACROSS), value_of(row, dim, unit)
    return (x, y) if x is not None and y is not None else None


def values(dim, unit, rungs, other):
    """Every value this figure's axis holds on these rungs, for the rows drawn against `other`
    (the figure on the plot's second axis, as (dim, unit)): figures, sessions and ranges."""
    out = []
    for rung in rungs:
        for row in rung["rows"]:
            if value_of(row, dim, unit) is None or value_of(row, *other) is None:
                continue
            ticks, span = spread_of(row, dim, rung, unit)
            out += [value_of(row, dim, unit), *ticks, *(span or ())]
    return [v for v in out if v is not None and (v > 0 or dim == "fidelity")]


# ------------------------------------------------------------------ an axis
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


def axis_of(dim, unit, rungs, other):
    """A figure's axis over these rungs, or None with nothing to draw: its ends (`lo`, `hi`:
    decades, or percent for Fidelity), where a value sits on it (`at`, in percent of the plot),
    its ticks as (place, words) and its minor ticks' places."""
    vals = values(dim, unit, rungs, other)
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
    """A decade as an axis prints it: a display word, not a measurement."""
    return f"{decade_words(k)}×" if unit == "ratio" else decade_words(k)


def labelled(ticks, width):
    """The ticks labelled on an axis `width` px long, by index: every k-th from the first, k the
    least for which two labels never meet (a start-anchored end label beside a centred one is the
    worst pair)."""
    last = len(ticks) - 1
    w = max(len(words) for _, words in ticks) * ADV * TICK_PX
    d = width / last
    k = next(k for k in range(1, last + 1) if k * d >= 1.5 * w + 12 or k == last)
    return set(range(0, last + 1, k))


def across_svg(axis):
    """The axis under the plot: a tick at each of its ticks and a short one at each minor one,
    and the ticks' words in three sets, for a desktop's plot, a narrower one and a phone's
    (words.css shows one)."""
    ticks = axis["ticks"]
    out = [f'<line class="mn" x1="{pc(x)}" x2="{pc(x)}" y1="0" y2="5"/>' for x in axis["minor"]]
    out += [f'<line class="mj" x1="{pc(x)}" x2="{pc(x)}" y1="0" y2="10"/>' for x, _ in ticks]
    for tl, width in (("x", PLOT_FULL), ("w", PLOT_WIDE), ("n", PLOT_NARROW)):
        for i in sorted(labelled(ticks, width)):
            x, words = ticks[i]
            anchor = "start" if i == 0 else "end" if i == len(ticks) - 1 else "middle"
            out.append(f'<text class="tl {tl}" x="{pc(x)}" y="26" text-anchor="{anchor}">'
                       f"{e(words)}</text>")  # fmt: skip
    return (f'<svg class="ax ox" width="100%" height="{AXIS_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def up_svg(axis):
    """The axis left of the plot, as tall as it: a tick and its words at each of its ticks, a
    short tick at each minor one; a place is counted from the plot's foot."""
    out = [f'<line class="mn" x1="94%" x2="100%" y1="{pc(100 - y)}" y2="{pc(100 - y)}"/>'
           for y in axis["minor"]]  # fmt: skip
    for y, words in axis["ticks"]:
        at = pc(100 - y)
        out.append(f'<line class="mj" x1="88%" x2="100%" y1="{at}" y2="{at}"/>'
                   f'<text class="tl" x="82%" y="{at}" dy=".35em" text-anchor="end">{e(words)}'
                   "</text>")  # fmt: skip
    return (f'<svg class="ax oy" width="100%" height="100%" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def grid_svg(across, up):
    """The two axes' lines over the whole plot, behind every system: one grid for all of them."""
    lines = [f'<line x1="{pc(x)}" x2="{pc(x)}" y1="0" y2="100%"/>' for x, _ in across["ticks"]]
    lines += [f'<line x1="0" x2="100%" y1="{pc(100 - y)}" y2="{pc(100 - y)}"/>'
              for y, _ in up["ticks"]]  # fmt: skip
    return (f'<svg class="ovg" width="100%" height="100%" aria-hidden="true" focusable="false">'
            f"{''.join(lines)}</svg>")  # fmt: skip


def spread_svg(points, across, up, dim, unit):
    """Each drawn row's spread behind its mark: its sessions as ticks on the stretch they cover,
    across (the multiple), and the stretch from its stored minimum to maximum, up (the figure
    that stores no value per session)."""
    out = []
    for row, rung, x, y in points:
        cls = "ok" if row["passed"] else "np"
        px, py = pc(across["at"](x)), pc(100 - up["at"](y))
        ticks, span = spread_of(row, ACROSS[0], rung, ACROSS[1])
        if span is not None:
            out.append(f'<line class="rg {cls}" x1="{pc(across["at"](span[0]))}" '
                       f'x2="{pc(across["at"](span[1]))}" y1="{py}" y2="{py}"/>')  # fmt: skip
        # as tall as the mark, so sessions under it hide behind it and only a spread one shows
        out += [f'<svg class="ss {cls}" x="{pc(across["at"](t))}" y="{py}" overflow="visible">'
                '<line y1="-7" y2="7"/></svg>' for t in ticks]  # fmt: skip
        _, rise = spread_of(row, dim, rung, unit)
        if rise is not None:
            out.append(f'<line class="rg {cls}" x1="{px}" x2="{px}" '
                       f'y1="{pc(100 - up["at"](rise[0]))}" y2="{pc(100 - up["at"](rise[1]))}"/>')  # fmt: skip
    return (f'<svg class="ovm" width="100%" height="100%" aria-hidden="true" focusable="false">'
            f"{''.join(out)}</svg>") if out else ""  # fmt: skip


# ------------------------------------------------------------------ a system: its mark and its flag
def unit_of(rung):
    """The unit a model's systems' glyphs are drawn at, in px: a step up for each decade of its
    parameters, so a larger model's glyph is larger. A step of size, not a measure: the model's
    size is printed in the flag and under the plots."""
    step = UNIT + UNIT_STEP * (math.log10(rung["parameters_total"]) - 8)
    return round(min(UNIT_MOST, max(UNIT_LEAST, step)), 2)


def flag_size(row, rung, dim):
    """A flag's (width, height) on the plot `flag_sides` places it on, in px, a little over what
    is drawn: its glyph beside its words."""
    u = unit_of(rung)
    words = max(WORDS_W, 38 + NAME_CH * len(name_of(row)), 60 + LINE_CH * len(rung["model"]))
    tall = WORDS_H + (60 if dim == "fidelity" else 0) + (0 if row["passed"] else 20)
    return (GLYPH_W * u + GLYPH_GAP + words + FLAG_PAD, max(GLYPH_H * u, tall) + FLAG_PAD)


def flag_sides(points, across, up, dim):
    """The side of its mark each flag stands on, as (left, over) per point, in the points'
    order: of the four sides, the one where the flag covers least of the flags placed before
    it, of the other marks and of what lies outside the plot. With nothing to avoid, a flag
    stands toward the middle of the plot."""
    spots = [(across["at"](x) * PLOT_W / 100, (100 - up["at"](y)) * PLOT_H / 100)
             for _, _, x, y in points]  # fmt: skip
    placed, sides = [], []

    def over(a, b):
        wide = max(0, min(a[2], b[2]) - max(a[0], b[0]))
        return wide * max(0, min(a[3], b[3]) - max(a[1], b[1]))

    for (row, rung, _, _), (px, py) in zip(points, spots, strict=True):
        w, h = flag_size(row, rung, dim)
        left, above = px > PLOT_W / 2, py > PLOT_H / 2
        best = None
        for lf, ov in ((left, above), (left, not above), (not left, above), (not left, not above)):
            x0 = px - FLAG_OFF - w if lf else px + FLAG_OFF
            y0 = py - FLAG_OFF - h if ov else py + FLAG_OFF
            box = (x0, y0, x0 + w, y0 + h)
            cost = 3 * (w * h - over(box, (0, 0, PLOT_W, PLOT_H))) + sum(
                over(box, b) for b in placed
            )
            cost += sum(4000 for sx, sy in spots if (sx, sy) != (px, py)
                        and box[0] - 9 < sx < box[2] + 9 and box[1] - 9 < sy < box[3] + 9)  # fmt: skip
            if best is None or cost < best[0] - 1:  # a px² apart: the first of two alike stands
                best = (cost, lf, ov, box)
        placed.append(best[3])
        sides.append((best[1], best[2]))
    return sides


def figure_html(row, dim):
    """The row's figure as the ladder prints it (the multiple's two parts are the system page's,
    CO-7; Fidelity with what the row proves and its model's two copies under it, SI-9)."""
    if dim == "multiple":
        return multiple_html(row, bare=True)
    if dim == "fidelity":
        return fidelity_word(row)
    f = figure_of(row, dim)
    return fig_html(f, counted(row), sub=BARE, note=scope_note(row, f))


def flag_html(row, rung, dim):
    """A system's flag: its glyph (its size its model's step, `unit_of`), then its position and
    name, its model with its size in a tab, the two figures, across first, and its standing.
    The petals in words for a screen reader stand after the name they belong to."""
    at, name = e(href(row)), e(name_of(row))
    arms = glyph_svg(ROW_GLYPH, states(row), names=[PETAL_NAME[p["id"]] for p in row["glyph"]])
    return (
        f'<div class="ofl row"><a class="glyph" href="{at}" tabindex="-1" aria-hidden="true">'
        f'{arms}</a><div class="ofw"><p class="ofn">{position_html(row, rung)}'
        f'<a class="sname" href="{at}">{name}</a></p>'
        f'<span class="sr pw">{states_words(row)}</span>'
        f'<p class="ofm"><span class="rk">{e(params(rung["parameters_total"]))}</span>'
        f"{nobreak(rung['model'])}</p>"
        f'<div class="off"><p>{figure_html(row, ACROSS[0])}</p><p>{figure_html(row, dim)}</p></div>'
        f'<p class="st">{standing_html(row)}</p></div></div>'
    )


def systems_html(points, across, up, dim, css):
    """The drawn rows, in the board's order: each a box at its place holding its mark, the two
    lines that lead from it to the axes when it is in hand, and its flag on the side
    `flag_sides` gives it. Each box's place and its glyph's unit go to `css`."""
    out = []
    sides = flag_sides(points, across, up, dim)
    for (row, rung, x, y), (left, over) in zip(points, sides, strict=True):
        fx, fy = across["at"](x), up["at"](y)
        bid = f"ob-{dim}-{row['page']}"
        css.append(place_css(bid, x=pc(fx), y=pc(fy), xf=f"{fx / 100:.4f}", yf=f"{fy / 100:.4f}",
                             u=unit_of(rung)))  # fmt: skip
        side = (" r" if left else "") + (" u" if over else "")
        state = "ok" if row["passed"] else "np"
        at = e(href(row))
        out.append(
            f'<div class="obx {state}{side}" id="{bid}" data-s="{e(row["page"])}">'
            '<i class="gx"></i><i class="gy"></i>'
            f'<a class="mk" href="{at}" tabindex="-1" aria-hidden="true"></a>'
            f"{flag_html(row, rung, dim)}</div>"
        )
    return "".join(out)


def list_html(points, dim, css):
    """The drawn rows once more as a list, in the board's order, for a phone: its plot has room
    for a mark and a name, so each system's glyph, model, figures and standing stand under it
    (words.css shows the list under 761 px only, where a flag on the plot is its name alone)."""
    items = []
    for row, rung, _, _ in points:
        bid = f"ol-{dim}-{row['page']}"
        css.append(place_css(bid, u=unit_of(rung)))
        items.append(f'<li class="{"ok" if row["passed"] else "np"}" id="{bid}">'
                     f"{flag_html(row, rung, dim)}</li>")  # fmt: skip
    return f'<ul class="oli">{"".join(items)}</ul>'


def off_html(rows, dim, css):
    """The rows with a figure missing here, under the plot: each its flag, which says what is
    missing in words (a null figure's reason, a Fidelity that reads as the check's state)."""
    if not rows:
        return ""
    items = []
    for row, rung in rows:
        bid = f"of-{dim}-{row['page']}"
        css.append(place_css(bid, u=unit_of(rung)))
        items.append(f'<li class="{"ok" if row["passed"] else "np"}" id="{bid}">'
                     f"{flag_html(row, rung, dim)}</li>")  # fmt: skip
    return f'<div class="oof"><p class="k">{e(OVERVIEW_OFF)}</p><ul>{"".join(items)}</ul></div>'


# ------------------------------------------------------------------ a section, the models, the page
def named(dim):
    """A figure's name, linked to its definition on the checks page."""
    name = FIGURE_HEAD[dim]
    anchor = FIGURE_ANCHOR.get(dim, dim)
    return (f'<a class="df" href="{CHECKS_PAGE}#{anchor}">{e(name)}</a>'
            if dim in FIGURE_RULE or dim in FIGURE_ANCHOR else e(name))  # fmt: skip


def unit_words(dim, unit):
    """An axis's unit and scale in words; the unit keeps its own case in an uppercased head
    ("s/reply", not "S/REPLY")."""
    if dim == "fidelity":
        return '<span class="u">%</span>'
    _, sign = number(1, unit)
    rest = f" {SCALE_SERVING.lower()}" if unit == "ratio" else ""
    return f'<span class="u">{e(sign)}</span>{e(rest)}, {e(SCALE_LOG)}'


def panel_html(dim, unit, css):
    """One section: the figure that runs up, named at its head with its unit, the plot with its
    two axes, and under the plot the rows it could not place. With no row to place, the plot is
    left out; with no row at all the section says so."""
    rungs = S.V["rungs"]
    pairs = [(row, rung) for rung in rungs for row in rung["rows"]]
    points = [(row, rung, *xy) for row, rung in pairs if (xy := drawn(row, dim, unit))]
    off = [(row, rung) for row, rung in pairs if drawn(row, dim, unit) is None]
    across = axis_of(*ACROSS, rungs, (dim, unit))
    up = axis_of(dim, unit, rungs, ACROSS)
    head = (f'<div class="ovh"><h2 class="ovt" id="h-{dim}">{named(dim)}'
            f'<span class="sr"> against {e(FIGURE_HEAD[ACROSS[0]].lower())}</span></h2>'
            f'<span class="al">{unit_words(dim, unit)}</span></div>')  # fmt: skip
    if not points or across is None or up is None:
        plot = "" if pairs else f'<p class="onr">{e(SCALE_NOT_RUN)}</p>'
        data = ""
    else:
        plot = (
            f'<div class="ovq">{up_svg(up)}<div class="ovb">{grid_svg(across, up)}'
            f"{spread_svg(points, across, up, dim, unit)}"
            f"{systems_html(points, across, up, dim, css)}</div>{across_svg(across)}"
            f'<p class="oxh">{named(ACROSS[0])}<span class="al">{unit_words(*ACROSS)}</span></p>'
            f"</div>{list_html(points, dim, css)}"
        )
        data = (f' data-xlo="{across["lo"]}" data-xhi="{across["hi"]}" data-ylo="{up["lo"]}" '
                f'data-yhi="{up["hi"]}"')  # fmt: skip
    return (f'<section class="blk ovp" id="{dim}" aria-labelledby="h-{dim}">'
            f'<div class="ov" id="ov-{dim}"{data}>{head}{plot}{off_html(off, dim, css)}</div>'
            "</section>")  # fmt: skip


def models_html(css):
    """The models, once under the sections, largest first: each its size in a tab (the
    frontier's marked, OR-6), its name, its architecture and its serving rate, beside the size
    its systems' glyphs are drawn at; a model no system has run on says so."""
    front = S.V["frontier"]
    # the glyph with no state, in the frame's ink (as the checks page's key draws it)
    key = glyph_svg(ROW_GLYPH, ["key"] * len(S.V["petals"]),
                    names=[PETAL_NAME[p] for p in S.V["petals"]])  # fmt: skip
    items = []
    for rung in S.V["rungs"]:
        total, active = rung["parameters_total"], rung.get("parameters_active")
        mid = f"om-{rung['id']}"
        css.append(place_css(mid, u=unit_of(rung)))
        mark = (f'<p class="rf">{e(FRONTIER_WORD)}</p>'
                if front and front["rung"] == rung["id"] else "")  # fmt: skip
        none = "" if rung["rows"] else f'<p class="onr">{e(SCALE_NOT_RUN)}</p>'
        items.append(
            f'<li id="{mid}"><span class="gsw" aria-hidden="true">{key}</span><div>'
            f'<p class="rk">{e(params(total))}</p>{mark}'
            f'<h3 class="ln">{nobreak(rung["model"])}</h3>'
            f'<p class="lf">{nobreak(architecture(total, active, sized=False))}</p>'
            f'<p class="lsv"><span class="k">{e(SCALE_SERVING)}</span>'
            f"{served_html(rung['baseline'])}</p>{none}</div></li>"
        )
    return (f'<section class="omd" aria-labelledby="h-models"><h2 class="sr" id="h-models">'
            f'Models</h2><ul class="okm">{"".join(items)}</ul></section>')  # fmt: skip


def build_overview():
    css: list[str] = []
    panels = "".join(panel_html(d, u, css) for d, u in DIMS)
    body = f"""
{header("overview")}
<main id="main" class="sys">
  {title_band("Overview")}
  {pnav("Overview", [(d, FIGURE_HEAD[d]) for d, _ in DIMS])}
  <div class="wrap">{panels}{models_html(css)}{not_run_html()}</div>
</main>
{footer()}"""
    return page("Overview", overview_words(), body, "system overviewpage",
                OVERVIEW_PAGE.strip("/"), "home", css="".join(css))  # fmt: skip


def overview_words():
    """The overview page in a line (its description and its search line): its figures' names in
    lower case."""
    ups = ", ".join(FIGURE_HEAD[d].lower() for d, _ in DIMS)
    return f"{OVERVIEW_LEAD}: {FIGURE_HEAD[ACROSS[0]].lower()} against {ups}."
