"""The drawings of a system page: bars of one row's GPU times per reply, the fidelity tracks and
the dot plots that open its Cost and Fidelity blocks.
Every mark is geometry from a stored value of one row or one model: no number is typed here, and
nothing is ranked across models (RFC-0018 OR-1). Each bar sits beside its labelled figure.

A bar is SVG on a viewBox VB units wide, stretched to its box (`preserveAspectRatio="none"`), so
a length is the stored value over the largest value it is drawn beside; lines keep their width
(`vector-effect`, words.css). words.css inks them.
"""

import math

VB = 1000  # a bar's length in user units, at the largest value it is drawn beside
MIN = 4  # a part shorter than this, in user units, is also marked by a line where it ends


def svg(cls, h, body):
    return (f'<svg class="{cls}" viewBox="0 0 {VB} {h}" preserveAspectRatio="none" '
            f'aria-hidden="true" focusable="false">{body}</svg>')  # fmt: skip


def hbar(segs, top, h=12, cls="hb"):
    """One bar of consecutive parts, each (value, class), on the scale where `top` fills the box;
    a hairline track under it shows the scale's end. Class "bc" is drawn as an outline. Every
    part is drawn at its own length; one too short to see is marked by a line where it ends (a
    position on the scale, never drawn longer than its value)."""
    out = [f'<rect class="tk" y="{h / 2 - 0.5:g}" width="{VB}" height="1"/>']
    x, cuts, nibs = 0.0, [], []
    for v, c in segs:
        w = VB * v / top if top else 0
        if c == "bc":
            out.append(f'<rect class="bc" x="{x:.2f}" y=".75" width="{w:.2f}" '
                       f'height="{h - 1.5:g}"/>')  # fmt: skip
        else:
            out.append(f'<rect class="{c}" x="{x:.2f}" width="{w:.2f}" height="{h}"/>')
        x += w
        cuts.append(x)
        if w < MIN:
            nibs.append(f'<line class="nib {c}" x1="{x:.2f}" x2="{x:.2f}" y2="{h}"/>')
    out += [f'<line class="cut" x1="{c:.2f}" x2="{c:.2f}" y2="{h}"/>' for c in cuts[:-1]]
    return svg(cls, h, "".join(out + nibs))


def fid_svg(value, bar, top, kind, h=18):
    """A fidelity track from no matched token to the whole reply (`top`): the stretch up to the
    model's bar shaded, the bar a line, the replies' mean matched prefix a tick (kind: me,
    honest, damaged, bar)."""
    out = [f'<rect class="tk" y="{h / 2 - 0.5:g}" width="{VB}" height="1"/>']
    if bar is not None:
        b = VB * bar / top
        out.append(f'<rect class="fz" width="{b:.2f}" height="{h}"/>')
        out.append(f'<line class="fb" x1="{b:.2f}" x2="{b:.2f}" y2="{h}"/>')
    if value is not None:
        x = min(max(VB * value / top, 1), VB - 1)
        out.append(f'<line class="ft {kind}" x1="{x:.2f}" x2="{x:.2f}" y1="2" y2="{h - 2}"/>')
    return svg("fdt", h, "".join(out))


# ------------------------------------------------------------------ a dot plot: named rows, one axis
# The Cost and Fidelity blocks open with one: each row a word, its labelled figure and its plot,
# every plot on the axis drawn once over them. A plot is SVG with no viewBox: every horizontal
# coordinate is a percentage of its cell (as on the Scale page), so text keeps its size at any
# width and no inline style is needed. A mark is a position only: no number is printed here.
AX_H, ROW_H = 30, 30  # the axis's height and a row's plot's, in px
ADV = 7.15  # an 11 px tick label's advance per character, in px (scale.py: ADV * TICK_PX)
# the narrowest plot each set of tick labels is drawn for (words.css shows one): a desktop's
# plot beside its words, and a phone's under them (a 320 px screen)
PLOT_WIDE, PLOT_NARROW = 560, 280


def log_extent(vals):
    """The decades a multiple's axis draws, (lo, hi): from 1× (or the decade under the smallest
    value) to one past the largest's, never fewer than two."""
    lo = min(0, math.floor(math.log10(min(vals))))
    hi = math.floor(math.log10(max(vals))) + 1
    return lo, max(hi, lo + 2)


def log_x(v, lo, hi):
    """A value's place on a decade axis, in percent of the plot's width."""
    return 100 * (math.log10(v) - lo) / (hi - lo)


def lin_x(v, lo, hi):
    """A value's place on a linear axis from lo to hi, in percent of the plot's width."""
    return 100 * (v - lo) / (hi - lo)


def pc(x):
    return f"{x:.2f}%"


def axis_svg(ticks, minor=()):
    """The axis over a dot plot: a tick at each of `ticks` ((x, words), evenly spaced, the first
    and last the axis's ends), a short one at each of `minor` (x), and the words in two sets,
    for a wide plot and a phone's: every k-th from the first, k the least for which two never
    meet (an end's label, set inside the plot, beside a centred one is the worst pair)."""
    out = [f'<line class="mn" x1="{pc(x)}" x2="{pc(x)}" y1="23" y2="{AX_H}"/>' for x in minor]
    out += [f'<line class="mj" x1="{pc(x)}" x2="{pc(x)}" y1="17" y2="{AX_H}"/>' for x, _ in ticks]
    w = max(len(t) for _, t in ticks) * ADV
    last = len(ticks) - 1
    for cls, width in (("w", PLOT_WIDE), ("n", PLOT_NARROW)):
        d = width / last
        k = next(k for k in range(1, last + 1) if k * d >= 1.5 * w + 12 or k == last)
        for i in range(0, last + 1, k):
            x, words = ticks[i]
            anchor = "start" if i == 0 else "end" if i == last else "middle"
            out.append(f'<text class="tl {cls}" x="{pc(x)}" y="11" text-anchor="{anchor}">'
                       f"{words}</text>")  # fmt: skip
    return (f'<svg class="dax" width="100%" height="{AX_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def dot_svg(x, kind, grid):
    """One row's plot: the axis's lines (`grid`, x), a track, and the row's mark at x (kind: me,
    this system's figure, solid; ref, serving or a copy, an outline; part, a part of this
    system's figure, small); the lines only where x is None (a figure not measured)."""
    out = [f'<line class="gd" x1="{pc(g)}" x2="{pc(g)}" y1="0" y2="{ROW_H}"/>' for g in grid]
    out.append(f'<line class="tk" x1="0%" x2="100%" y1="{ROW_H / 2:g}" y2="{ROW_H / 2:g}"/>')
    if x is not None:
        r = {"me": 6, "ref": 5, "part": 4}[kind]
        out.append(f'<svg class="mk {kind}" x="{pc(x)}" y="{ROW_H / 2:g}" overflow="visible">'
                   f'<rect x="{-r}" y="{-r}" width="{2 * r}" height="{2 * r}"/></svg>')  # fmt: skip
    return (f'<svg class="dpl" width="100%" height="{ROW_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def dot_plot(head, caption, axis, grid, rows, at=""):
    """A dot plot as markup: its head (the figure's name, linked) and the axis's caption over
    the axis, then one row each (cls, word, figure, x or None, kind, or a head of a group of
    rows as (cls, words) alone); the words and figures are text a reader reads, the plots
    aria-hidden beside them."""
    out = [f'<div class="dph">{head}</div><div class="dpa"><span class="dpc">{caption}</span>'
           f"{axis}</div>"]  # fmt: skip
    for r in rows:
        if len(r) == 2:
            cls, words = r
            out.append(f'<div class="dpg {cls}">{words}</div>')
            continue
        cls, word, fig, x, kind = r
        out.append(f'<div class="dpr {cls}"><span class="dpw">{word}</span>'
                   f'<span class="dpf">{fig}</span>{dot_svg(x, kind, grid)}</div>')  # fmt: skip
    place = f' id="{at}"' if at else ""
    return f'<div class="dp"{place}>{"".join(out)}</div>'
