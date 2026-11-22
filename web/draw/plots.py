"""The drawings of a system page: bars of one row's GPU times per reply, of its multiple's two
parts and of its model's serving ladder, the fidelity tracks and the dot plots that open its Cost
and Fidelity blocks.
Every mark is geometry from a stored value of one row or one model: no number is typed here, and
nothing is ranked across models (RFC-0018 OR-1). Each bar sits beside its labelled figure.

A bar is SVG on a viewBox VB units wide, stretched to its box (`preserveAspectRatio="none"`), so
a length is the stored value over the largest value it is drawn beside; lines keep their width
(`vector-effect`, words.css). words.css inks them.
"""

import math
from itertools import pairwise

VB = 1000  # a bar's length in user units, at the largest value it is drawn beside
MIN = 4  # a part shorter than this, in user units, is also marked by a line where it ends
ZERO = 0  # the value at a bar's start: every bar is drawn from zero (RFC-0018 Q50)


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
# coordinate is a percentage of its cell (as on the Overview page), so text keeps its size at any
# width and no inline style is needed. A mark is a position only: no number is printed here.
AX_H, ROW_H = 40, 48  # the axis's height and a row's plot's, in px: a row has room around its mark
ADV = 7.8  # a 12 px tick label's advance per character, in px (Martian Mono at 87.5 %: 0.65 em)
LABEL_GAP = 10  # the least room between two tick labels, in px
# the narrowest plot each set of tick labels is drawn for (words.css shows one), measured in the
# browser: the Cost plot from 601 px (under its words up to 1000 px; beside them from there, where
# it is narrowest, 487 px), the Fidelity plot beside its words from 761 px (464 px), and a phone's
# under them on a 320 px screen
PLOT_FULL = 640  # the narrowest plot from 1201 px (675 px, the Cost plot with a six-character rate)
PLOT_WIDE, PLOT_BESIDE, PLOT_NARROW = 480, 440, 259


def log_extent(vals):
    """The decades an axis draws for values above zero, (lo, hi): from the decade under the
    smallest to the one past the largest, never fewer than two."""
    lo = math.floor(math.log10(min(vals)))
    hi = math.floor(math.log10(max(vals))) + 1
    return lo, max(hi, lo + 2)


def decade_words(k):
    """A decade as an axis prints it (0.1, 1, 10, 1,000): a place on the scale, not a figure."""
    return f"{10**k:,}" if k >= 0 else f"{10**k:.{-k}f}"


def log_x(v, lo, hi):
    """A value's place on a decade axis, in percent of the plot's width."""
    return 100 * (math.log10(v) - lo) / (hi - lo)


def lin_x(v, lo, hi):
    """A value's place on a linear axis from lo to hi, in percent of the plot's width."""
    return 100 * (v - lo) / (hi - lo)


def pc(x):
    return f"{x:.2f}%"


def label_spans(ticks, shown, width):
    """Where each shown tick's words stand on a plot `width` px wide, (left, right) in px: the
    first set from its tick, the last up to its tick, the others centred on theirs."""
    last, out = len(ticks) - 1, []
    for i in shown:
        x, w = ticks[i][0] * width / 100, len(ticks[i][1]) * ADV
        out.append((x, x + w) if i == 0 else (x - w, x) if i == last else (x - w / 2, x + w / 2))
    return out


def labelled(ticks, width):
    """The ticks whose words a plot `width` px wide prints, by index: the first and the last
    always, and between them every k-th from the first, no two words closer than LABEL_GAP. The
    least k that lands on the last tick is taken first, so the labelled ticks are evenly spaced;
    where none does (a prime count), the least k whose last label before the end is left out."""
    last = len(ticks) - 1

    def fits(shown):
        spans = label_spans(ticks, shown, width)
        return all(b[0] - a[1] >= LABEL_GAP for a, b in pairwise(spans))

    for k in (k for k in range(1, last) if last % k == 0):
        if fits(shown := [*range(0, last, k), last]):
            return shown
    for k in range(1, last):
        shown = [*range(0, last, k), last]
        while len(shown) > 2 and not fits(shown[-2:]):
            del shown[-2]
        if fits(shown):
            return shown
    return [0, last]


def axis_svg(ticks, minor=(), wide=PLOT_WIDE):
    """The axis over a dot plot: a tick at each of `ticks` ((x, words), evenly spaced, the first
    and last the axis's ends), a short one at each of `minor` (x), and the words in three sets
    (words.css shows one), for a desktop's plot, a narrower one (`wide` px at its narrowest) and a
    phone's: both ends always, so a mark
    never stands past the last labelled tick, and between them every k-th from the first, k the
    least step that keeps two words from meeting (an end's label, set inside the plot, beside a
    centred one is the worst pair); one too close to the last tick's is left out."""
    out = [
        f'<line class="mn" x1="{pc(x)}" x2="{pc(x)}" y1="{AX_H - 6}" y2="{AX_H}"/>' for x in minor
    ]
    out += [
        f'<line class="mj" x1="{pc(x)}" x2="{pc(x)}" y1="{AX_H - 12}" y2="{AX_H}"/>'
        for x, _ in ticks
    ]
    for cls, width in (("x", PLOT_FULL), ("w", wide), ("n", PLOT_NARROW)):
        for i in labelled(ticks, width):
            x, words = ticks[i]
            anchor = "start" if i == 0 else "end" if i == len(ticks) - 1 else "middle"
            out.append(f'<text class="tl {cls}" x="{pc(x)}" y="12" text-anchor="{anchor}">'
                       f"{words}</text>")  # fmt: skip
    return (f'<svg class="dax" width="100%" height="{AX_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def dot_svg(x, kind, grid, span=None):
    """One row's plot: the stretch between two places of the axis (`span`, (x, x): what lies
    between two figures of the drawing), the axis's lines (`grid`, x), a dotted guide from the
    row's words across the plot, and the row's mark at x (kind: me, this system's figure, solid;
    ref, serving or a copy, an outline); no mark where x is None (a figure not measured)."""
    mid = ROW_H / 2
    out = []
    if span:
        a, b = sorted(span)
        out.append(f'<rect class="sp" x="{pc(a)}" width="{pc(b - a)}" height="{ROW_H}"/>')
    out += [f'<line class="gd" x1="{pc(g)}" x2="{pc(g)}" y1="0" y2="{ROW_H}"/>' for g in grid]
    out.append(f'<line class="tk" x1="0%" x2="100%" y1="{mid:g}" y2="{mid:g}"/>')
    if x is not None:
        r = {"me": 8, "ref": 7}[kind]
        out.append(f'<svg class="mk {kind}" x="{pc(x)}" y="{mid:g}" overflow="visible">'
                   f'<rect x="{-r}" y="{-r}" width="{2 * r}" height="{2 * r}"/></svg>')  # fmt: skip
    return (f'<svg class="dpl" width="100%" height="{ROW_H}" aria-hidden="true" '
            f'focusable="false">{"".join(out)}</svg>')  # fmt: skip


def dot_plot(head, caption, axis, grid, rows, at="", foot="", span=None):
    """A dot plot as markup: its head (the figure's name, linked) beside the axis's caption, the
    axis, then one row each (cls, word, figure, x or None, kind), `span` shaded in every row's
    plot, and, under them, `foot` (a figure's few words of meaning); the words and figures are text a reader reads, the plots
    aria-hidden beside them."""
    out = [f'<div class="dph">{head}</div><div class="dpa"><span class="dpc">{caption}</span>'
           f"{axis}</div>"]  # fmt: skip
    for cls, word, fig, x, kind in rows:
        out.append(f'<div class="dpr {cls}"><span class="dpw">{word}</span>'
                   f'<span class="dpf">{fig}</span>{dot_svg(x, kind, grid, span)}</div>')  # fmt: skip
    if foot:
        out.append(f'<div class="dpm">{foot}</div>')
    place = f' id="{at}"' if at else ""
    return f'<div class="dp"{place}>{"".join(out)}</div>'
