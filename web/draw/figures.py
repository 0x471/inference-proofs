"""What the Learn pages draw: the figures, the explorers and the measured blocks.

A page's text names one by `:::figure <id>`, `:::explore <id>` or `:::measured <id>` (learn.py).
Each is a function of no argument that returns markup:

- a figure is a static drawing made of words, boxes and lines in the site's inks;
- an explorer is a figure a reader can operate. Its markup reads in full without script (every
  step, every case); words.js then shows one state at a time and adds the controls. A worked
  example an explorer prints is computed here, by the same arithmetic the script runs;
- a measured block prints figures of the board file through `fig_html`, with their labels, and
  says so when the board holds none. Nothing here types a measured number.

No inline style: the Content-Security-Policy allows none (outputs.vercel_json). Cobalt frames
what a reader operates; the state inks stay with the states of a check (words.css).
"""

from . import state as S
from .chrome import counted, lead_figure, standing
from .overview import (
    BARE,
    baseline_html,
    fig_html,
    href,
    multiple_html,
    name_of,
    serving_words,
    split_html,
)
from .words import FIGURE_HEAD, SEP, e

FIGURES: dict = {}
EXPLORERS: dict = {}
MEASURED: dict = {}

# what a stage of the deployment page rests on today: the first word of a `:::stage` block
# (learn.py)
STAGE_WORD = {
    "measured": "Run on this site",
    "demonstrated": "Shown in research",
    "proposed": "Proposed, parts built",
    "outside": "Outside a proof's reach",
}


def drawn(table, name):
    """Register a drawing under the name a page's text uses for it."""

    def register(f):
        table[name] = f
        return f

    return register


def arrow(cls="ar"):
    """An arrow between two boxes: it points right on a wide screen, down on a phone."""
    return (f'<svg class="{cls}" viewBox="0 0 40 16" width="40" height="16" aria-hidden="true" '
            'focusable="false"><path d="M0 8h34M27 2l8 6-8 6" fill="none" stroke="currentColor" '
            'stroke-width="2"/></svg>')  # fmt: skip


# ------------------------------------------------------------------ figures
@drawn(FIGURES, "parties")
def parties():
    """Who holds what: the operator, the verifier and the relying party (a proof of inference).
    Each thing held or passed carries a key (`data-k`): pointing at one lights it wherever it is
    held or passed (words.js), so a reader sees what the verifier never holds."""

    def held(words, cls=""):
        return "".join(f'<li{f" class={cls}" if cls else ""}{f" data-k={k}" if k else ""}>'
                       f"{e(w)}</li>" for w, k in words)  # fmt: skip

    def card(name, role, holds, never=()):
        return (f'<div class="pc"><p class="pk">{e(name)}</p><p class="pd">{e(role)}</p>'
                f'<ul class="ph">{held(holds)}{held(never, "nv")}</ul></div>')  # fmt: skip

    def passes(*lines):
        return (f'<div class="pa">{arrow()}<ul>'
                + "".join(f"<li{f' data-k={k}' if k else ''}>{e(a)}<span>{e(b)}</span></li>"
                          for a, b, k in lines)
                + "</ul></div>")  # fmt: skip

    return (
        '<div class="pt3">'
        + card("The operator", "runs the model, makes the proof",
               (("the model's weights", "w"), ("the prompt", "p"), ("the reply", "r")))
        + passes(("the commitment", "once, before any request", "c"),
                 ("a proof", "for each reply to be checked", "f"))
        + card("The verifier", "a program anyone can run",
               (("the commitment and its public settings", "c"), ("the prompt", "p"),
                ("the reply, given or read from the proof", "r"), ("the proof", "f")),
               never=(("never the weights", "w"),))
        + passes(("accepts or refuses", "with no GPU and no weights", "v"))
        + card("The relying party", "acts on the verdict",
               (("the verdict", "v"), ("the statement it stands for", ""),
                ("the assumptions it rests on", "")))
        + "</div>"
    )  # fmt: skip


@drawn(FIGURES, "pipeline")
def pipeline():
    """One forward pass as its operations. A tag marks what a step multiplies: the committed
    weights (the three weight products) or other activations (attention's mix); a step with no
    tag needs more than additions and multiplications, which the note under the steps says."""
    steps = (
        ("Embed", "look up one row of a table per token", "other"),
        ("Normalise", "divide by a root mean square", "other"),
        ("Attention: project", "multiply by weight matrices", "linear"),
        (
            "Attention: mix",
            "multiply activations by activations, take a softmax, multiply again",
            "mixed",
        ),
        ("MLP: project", "multiply by weight matrices", "linear"),
        ("MLP: activate", "apply a fixed curve to each number", "other"),
        ("Unembed", "multiply by a weight matrix", "linear"),
        ("Choose", "take the largest of the vocabulary's scores", "other"),
    )
    # the tag of a step that multiplies; the other steps carry none
    tag = {"linear": "× committed weights", "mixed": "× activations"}
    rows = "".join(
        f'<li class="op {"other" if k == "mixed" else k}"><span class="o1">{e(name)}</span>'
        f'<span class="o2">{e(does)}</span>'
        + (f'<span class="o3">{e(tag[k])}</span>' if k in tag else "")
        + "</li>"
        for name, does, k in steps
    )
    return (f'<ol class="ops">{rows}</ol><p class="opn">The steps from Normalise to MLP: activate repeat once '
            "per layer. A step with no tag needs more than additions and multiplications.</p>")  # fmt: skip


SESSION_SAID = (
    "A session on a time axis: the commit step, then a generation phase where a system has one, "
    "then four groups of proofs released one after another. The steady interval runs from the "
    "release of the first group to the release of the last. The generation phase is counted in "
    "m. The whole session starts with the commit step."
)
SESSION_GROUPS = ("group 1", "group 2", "group 3", "group 4")


def session_svg(cls, w, h, at, said):
    """One layout of the session drawing: `at` places each mark (x of commit, generation and
    each group's release; y of the brackets, the boxes, and the labels of the four groups, commit
    and generation; and, where two labels over brackets would meet, the x each is centred on,
    "x" by label, else its bracket's middle), `said` its words by line."""
    c0, c1, g0, g1 = at["commit"] + at["gen"]
    rel, y = at["groups"], at["y"]
    box = f'y="{y["box"]}" height="36"'
    ticks = "".join(
        f'<g class="grp{" g1" if k == 0 else ""}"><rect x="{x - at["gw"]}" {box} '
        f'width="{at["gw"]}"/><text x="{x - at["gw"] / 2:g}" y="{y["lab"][k]}" '
        f'text-anchor="middle">{label}</text></g>'
        for k, (x, label) in enumerate(zip(rel, SESSION_GROUPS, strict=True))
    )

    def lines(cls, x, ys, words):
        return "".join(f'<text class="{cls}" x="{x:g}" y="{yy}" text-anchor="middle">{t}</text>'
                       for yy, t in zip(ys, words, strict=True))  # fmt: skip

    top, base, low = y["br"], y["box"] + 36, y["low"]
    mid = {"m": (g0 + g1) / 2, "steady": (rel[0] + rel[-1]) / 2} | at.get("x", {})
    return (
        f'<svg class="sx {cls}" viewBox="0 0 {w} {h}" role="img" aria-label="{SESSION_SAID}">'
        f'<line class="ax" x1="{c0}" y1="{base}" x2="{w - c0}" y2="{base}"/>'
        f'<rect class="scm" x="{c0}" {box} width="{c1 - c0}"/>'
        f'<text x="{(c0 + c1) / 2:g}" y="{y["lab"][4]}" text-anchor="middle">commit</text>'
        f'<rect class="sgn" x="{g0}" {box} width="{g1 - g0}"/>'
        f'<text x="{(g0 + g1) / 2:g}" y="{y["lab"][5]}" text-anchor="middle">generation</text>'
        f"{ticks}"
        f'<path class="br" d="M{g0} {top}v-10H{g1}v10"/>'
        + lines("bt", mid["m"], y["m"], said["m"])
        + f'<path class="br" d="M{rel[0]} {top}v-10H{rel[-1]}v10"/>'
        + lines("bt", mid["steady"], y["steady"], said["steady"])
        + f'<path class="br2" d="M{c0} {low}v10H{rel[-1]}v-10"/>'
        + lines("bt2", (c0 + rel[-1]) / 2, y["whole"], said["whole"])
        + "</svg>"
    )


@drawn(FIGURES, "session")
def session():
    """One session on a time axis: commit, a generation phase where a system has one, the first
    release group and the later groups, and the GPU time that makes m (RFC-0018 CO-1 to CO-3).
    Two layouts of one drawing: a wide one, and on a phone a narrow one at its own size, its
    long words on two lines, the names under the axis on two rows, in turn, and the two labels
    over the brackets drawn apart (each is wider than its bracket: measured in Chrome, "counted
    in m" 101 units, "the GPU time behind m" 177 of the 328)."""
    wide = session_svg(
        "sxw", 681, 190,
        {"commit": (1, 101), "gen": (113, 223), "groups": (301, 401, 501, 601), "gw": 26,
         "y": {"br": 52, "box": 72, "lab": (130,) * 6, "low": 150, "m": (30,),
               "steady": (30,), "whole": (180,)}},
        {"m": ("generation: counted in m",), "steady": ("steady interval: the GPU time behind m",),
         "whole": ("whole session: from the start of the commit step",)},
    )  # fmt: skip
    narrow = session_svg(
        "sxn", 328, 206,
        {"commit": (4, 54), "gen": (62, 122), "groups": (160, 206, 252, 298), "gw": 18,
         "y": {"br": 52, "box": 64, "lab": (120, 138, 120, 138, 120, 138), "low": 150,
               "m": (14, 30), "steady": (14, 30), "whole": (178, 194)},
         "x": {"m": 72, "steady": 238}},
        {"m": ("generation:", "counted in m"), "steady": ("steady interval:", "the GPU time behind m"),
         "whole": ("whole session: from the start", "of the commit step")},
    )  # fmt: skip
    return f'<div class="tw">{wide}{narrow}</div>'


# ------------------------------------------------------------------ explorers
# ---- a random check of a matrix product (Freivalds) and a sumcheck of an inner product: the
# worked examples, by the arithmetic words.js runs. The sentences words.js prints are the
# templates here ({name} filled in), so the page reads the same with script and without.
P = 97  # the small prime field of the worked examples: small enough that a lie sometimes survives
FA = ((2, 0, 1), (1, 3, 0), (0, 1, 2))
FB = ((1, 2, 0), (0, 1, 1), (3, 0, 1))
WRONG = (1, 2, 1)  # row, column, and what is added there to make the claimed product false
RC_WORDS = {
    "diff": "different: the claimed product is refused",
    "miss": "equal: this draw misses the wrong entry",
    "true": "equal: the claimed product is the true one",
    "tally": "{n} {draws} from {set} so far, {k} of them refused the claimed product.",
    "draw": "draw",  # {draws} after a count of one
    "draws": "draws",
    "bits": "Draw r from 0 and 1",
    "field": "Draw r from 0 to {top}",
    "many": "Draw {n} times from 0 to {top}",
    "manybits": "Draw {n} times from 0 and 1",
    "setbits": "0 and 1",
    "setfield": "0 to {top}",
    "wrong": "One entry of the claimed product is wrong",
}
RC_RUNS = 1000  # how many draws each "many" button makes (from the field, from 0 and 1)


def data_words(words):
    return " ".join(f'data-w-{k}="{e(v)}"' for k, v in words.items())


def fill(template, **values):
    return template.format(**values)


def matmul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(len(b))) % P
                       for j in range(len(b[0]))) for i in range(len(a)))  # fmt: skip


def matvec(a, v):
    return tuple(sum(x * y for x, y in zip(row, v, strict=True)) % P for row in a)


def claimed(honest):
    """The product the prover claims: A·B, or A·B with one entry changed."""
    c = [list(row) for row in matmul(FA, FB)]
    if not honest:
        i, j, d = WRONG
        c[i][j] = (c[i][j] + d) % P
    return tuple(tuple(row) for row in c)


def random_check(r, honest=False):
    """One random check of the claimed product with the vector r: A·(B·r) against C·r."""
    left, right = matvec(FA, matvec(FB, r)), matvec(claimed(honest), r)
    return {"r": r, "left": left, "right": right, "equal": left == right}


def grid(m, mark=None, cls="mx"):
    """A matrix as a table of its entries (one marked: the changed one)."""
    trs = "".join(
        "<tr>" + "".join(
            f'<td{" class=bad" if mark == (i, j) else ""}>{v}</td>' for j, v in enumerate(row)
        ) + "</tr>"
        for i, row in enumerate(m)
    )  # fmt: skip
    return f'<table class="{cls}"><tbody>{trs}</tbody></table>'


def column(v, cls="mx"):
    return grid(tuple((x,) for x in v), cls=cls)


def named(label, matrix):
    """A matrix and its name as one group: a line that wraps never leaves a name without it."""
    return f'<div class="mxg"><span class="lb">{e(label)}</span>{matrix}</div>'


def flat(m):
    """A matrix as the script reads it: its rows, entries separated by spaces, rows by commas."""
    return ",".join(" ".join(str(v) for v in row) for row in m)


@drawn(EXPLORERS, "random-check")
def random_check_html():
    """A·B against a claimed C with one wrong entry: two draws worked in full, one that catches
    the change and one that misses it. With script: draw r, from bits or from the whole field,
    once or RC_RUNS times, each set with its own count of refusals."""
    i, j, _ = WRONG

    def draw(r):
        got = random_check(r)
        verdict = RC_WORDS["miss"] if got["equal"] else RC_WORDS["diff"]
        return (f'<div class="dr"><div class="eq">{named("r", column(got["r"]))}'
                f'{named("A·(B·r)", column(got["left"]))}{named("C·r", column(got["right"]))}</div>'
                f'<p class="vd">{e(verdict)}</p></div>')  # fmt: skip

    data = (f'data-a="{flat(FA)}" data-b="{flat(FB)}" data-c="{flat(claimed(False))}" '
            f'data-ok="{flat(claimed(True))}" data-p="{P}" data-runs="{RC_RUNS}" '
            f"{data_words(RC_WORDS)}")  # fmt: skip
    shown_c = f'<div class="xcl">{grid(claimed(False), mark=(i, j))}</div>'
    return (
        f'<div class="xpl" data-x="random-check" {data}>'
        f'<div class="eq mm">{named("A", grid(FA))}{named("B", grid(FB))}'
        f"{named('claimed C', shown_c)}"
        f'<span class="lv">arithmetic modulo {P}</span></div>'
        f'<div class="xo">{draw((1, 0, 1))}{draw((1, 1, 0))}</div></div>'
    )


# the sumcheck of an inner product <a, b> of two vectors of four numbers, over the field of P
# elements: two rounds, a polynomial of degree two in each (three values sent)
SA = (2, 7, 1, 8)
SB = (3, 1, 4, 1)
CHALLENGES = (5, 11)  # the worked example's two random draws
LIE = 1  # what the lying prover adds to the true result
SC_WORDS = {
    "honest": "An honest prover claims the result {claim}",
    "lying": "A lying prover claims the result {claim}",
    "round": "Round {k}",
    "sent": "{s0}, {s1}, {s2}",
    "check": "{s0} + {s1} = {sum}, the running claim",
    "last": "a(r)·b(r) = {a} · {b} = {final}, and the last claim is {last}: {verdict}",
    "accepted": "accepted",
    "refused": "refused",
    "lies": "The prover lies about the result",
    "redraw": "Draw new challenges",
    "many": "Run {n} times",
    "runs": "Over {n} runs with fresh challenges the verifier accepted {k}.",
}


def fold(v, r):
    """The table of a multilinear polynomial with its first variable set to r."""
    half = len(v) // 2
    return tuple(((1 - r) * v[k] + r * v[half + k]) % P for k in range(half))


def round_poly(a, b):
    """s(0), s(1), s(2) of s(X) = sum over the other variables of a(X, ..)·b(X, ..)."""
    return tuple(sum(x * y for x, y in zip(fold(a, t), fold(b, t), strict=True)) % P
                 for t in (0, 1, 2))  # fmt: skip


def at(s, r):
    """The polynomial of degree two through (0, s0), (1, s1), (2, s2), at r."""
    inv2 = pow(2, -1, P)
    l0 = (r - 1) * (r - 2) * inv2
    l1 = -r * (r - 2)
    l2 = r * (r - 1) * inv2
    return (s[0] * l0 + s[1] * l1 + s[2] * l2) % P


def sumcheck(challenges=CHALLENGES, lie=0):
    """The transcript of one run: the claim, then per round the three values sent, the running
    claim their first two must sum to, the challenge and the next claim; then the final check
    against a(r)·b(r). A lying prover adds `lie` to the result and then, each round, sends the
    s(0) that makes the round's check pass, its other two values unchanged."""
    a, b = SA, SB
    claim = (sum(x * y for x, y in zip(a, b, strict=True)) + lie) % P
    rounds, running = [], claim
    for r in challenges:
        s = list(round_poly(a, b))
        s[0] = (running - s[1]) % P  # honest: the true s(0); lying: the value that passes
        nxt = at(s, r)
        rounds.append({"s": tuple(s), "claim": running, "r": r, "next": nxt})
        running, a, b = nxt, fold(a, r), fold(b, r)
    final = a[0] * b[0] % P
    return {"claim": claim, "rounds": rounds, "a": a[0], "b": b[0], "final": final,
            "accepted": final == running}  # fmt: skip


def transcript(run, who):
    # a variable stays on the line of the words it ends
    heads = ("Running claim", "Prover sends s(0),\u00a0s(1),\u00a0s(2)", "Verifier checks",
             "Verifier draws\u00a0r", "New claim\u00a0s(r)")  # fmt: skip
    rows = ""
    for k, rd in enumerate(run["rounds"], start=1):
        s0, s1, s2 = rd["s"]
        tds = (rd["claim"], e(fill(SC_WORDS["sent"], s0=s0, s1=s1, s2=s2)),
               e(fill(SC_WORDS["check"], s0=s0, s1=s1, sum=(s0 + s1) % P)), rd["r"], rd["next"])  # fmt: skip
        rows += (f'<tr><th scope="row">{e(fill(SC_WORDS["round"], k=k))}</th>'
                 + "".join(f'<td data-l="{e(h)}">{v}</td>' for h, v in zip(heads, tds, strict=True))
                 + "</tr>")  # fmt: skip
    last = fill(SC_WORDS["last"], a=run["a"], b=run["b"], final=run["final"],
                last=run["rounds"][-1]["next"],
                verdict=SC_WORDS["accepted" if run["accepted"] else "refused"])  # fmt: skip
    return (
        f'<div class="tr"><p class="vd">{e(fill(SC_WORDS[who], claim=run["claim"]))}</p>'
        '<div class="tw"><table class="rt lt mt"><thead><tr><td></td>'
        + "".join(f'<th scope="col">{e(h)}</th>' for h in heads)
        + f'</tr></thead><tbody>{rows}</tbody></table></div><p class="vl">{e(last)}</p></div>'
    )


@drawn(EXPLORERS, "sumcheck")
def sumcheck_html():
    """Two runs on the same draws, in full: first a prover that claims a result off by one,
    then an honest one. With script: the lying run first; choose the prover, draw again, run many
    times."""
    vectors = (f'<div class="eq mm"><span class="lb">a, the weights</span>{grid((SA,))}'
               f'<span class="lb">b, the activations</span>{grid((SB,))}'
               f'<span class="lv">arithmetic modulo {P}</span></div>')  # fmt: skip
    data = (f'data-a="{flat((SA,))}" data-b="{flat((SB,))}" data-p="{P}" data-lie="{LIE}" '
            f'data-runs="1000" {data_words(SC_WORDS)}')  # fmt: skip
    return (f'<div class="xpl" data-x="sumcheck" {data}>{vectors}<div class="xo">'
            f'{transcript(sumcheck(lie=LIE), "lying")}{transcript(sumcheck(), "honest")}'
            "</div></div>")  # fmt: skip


# ------------------------------------------------------------------ measured blocks
def release_words():
    rel = S.V["release"]
    if not rel:
        return "No board yet"
    return f"From the board, release {rel['id']}" + (f", {rel['date']}" if rel["date"] else "")


def rows_words(found):
    """The board in one sentence: how many rows, how many passed, and how many sessions stand
    behind them against the number the level asks for."""
    n, passed = len(found), sum(1 for _, row in found if row["passed"])
    slots = S.V["constants"]["slots"]
    short = sum(1 for _, row in found if len(row["sessions"]) < slots)
    said = f"{n} {'row' if n == 1 else 'rows'} so far: {passed} passed all six checks."
    if short:
        who = "It rests" if n == 1 else f"{short} of them rest{'s' if short == 1 else ''}"
        said += f" {who} on fewer than the {slots} sessions a position needs."
    return said


def row_figure(row):
    """A row's multiple with, under it, what it counted and n, once; its two parts under that,
    bare (the whole above says both). The line under the whole breaks before its dot, so "n"
    keeps its dot."""
    whole = multiple_html(row, parts=False).replace(
        f'<span class="sep">{SEP}</span>', '<span class="sep"> ·\u00a0</span>'
    )
    return whole + split_html(row, lead_figure(row)[2], bare=True)


@drawn(MEASURED, "rows")
def measured_rows():
    """Every row of the board, one table per model (nothing is ranked across models):
    system, standing, multiple of serving, check time and proof size per reply. What the
    figures counted and n are said once, under the multiple; the rest print bare, their labels
    in their title. A row with no position is set in the muted ink, as on the ladder."""
    found = [(rung, row) for rung in S.V["rungs"] for row in rung["rows"]]
    if not found:
        return ('<p class="none">No system has a row yet. The <a href="/">ladder</a> shows each '
                "one as it is run.</p>")  # fmt: skip
    heads = ("System", "Standing", FIGURE_HEAD["multiple"], FIGURE_HEAD["check-time"],
             FIGURE_HEAD["proof-size"])  # fmt: skip
    ths = "".join(f'<th scope="col">{h}</th>' for h in heads)

    def tr(row):
        return (
            "<tr>"
            f'<th scope="row"><a href="{e(href(row))}">{e(name_of(row))}</a></th>'
            f'<td data-l="{heads[1]}">{e(standing(row))}</td>'
            f'<td data-l="{heads[2]}">{row_figure(row)}</td>'
            f'<td data-l="{heads[3]}">'
            f"{fig_html(row['figures']['verify_seconds_per_reply'], counted(row), sub=BARE)}</td>"
            f'<td data-l="{heads[4]}">'
            f"{fig_html(row['figures']['proof_bytes_per_reply'], counted(row), sub=BARE)}</td></tr>"
        )

    tables = "".join(
        f'<div class="tw"><table class="rt mt"><caption class="bm">On {e(rung["model"])}</caption>'
        f'<thead><tr>{ths}</tr></thead><tbody>{"".join(tr(row) for row in rung["rows"])}</tbody>'
        "</table></div>"
        for rung in S.V["rungs"] if rung["rows"]
    )  # fmt: skip
    return (f'<p class="fl">{e(release_words())}</p><p class="ms-s">{e(rows_words(found))}</p>'
            f"{tables}")  # fmt: skip


def serving_line(rung):
    """A model's serving baseline in one line (CO-4): how it was served, then its GPU-seconds per
    reply, bare (the words before it say full load); with none, why."""
    b = rung["baseline"]
    if (
        b is None
        or b["gpu_seconds_per_reply"] is None
        or b["gpu_seconds_per_reply"]["value"] is None
    ):
        return baseline_html(rung)
    return (f'<p class="rb"><span class="k">Serving</span> {e(serving_words(b))}: '
            f'{fig_html(b["gpu_seconds_per_reply"], sub=BARE)}</p>')  # fmt: skip


@drawn(MEASURED, "baselines")
def measured_baselines():
    """Each model's serving baseline in one line (CO-4)."""
    lines = "".join(f'<div class="bl2"><p class="bm">{e(rung["model"])}</p>{serving_line(rung)}'
                    "</div>" for rung in S.V["rungs"])  # fmt: skip
    return f'<p class="fl">{e(release_words())}</p>{lines}'
