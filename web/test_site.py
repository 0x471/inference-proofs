"""The site against the board file it is built from: every printed figure is a value the board
stores, every glyph draws the board's petal steps and causes and its check states, and no v0.1
figure is printed (RFC-0018 SI-1,
SI-3, SI-5, CH-7). Run from the repository root: uv run pytest web -q
"""

import html
import json
import math
import re
from itertools import pairwise
from pathlib import Path
from typing import Any

WEB = Path(__file__).resolve().parent
ROOT = WEB.parent

FIG = re.compile(
    r'<span class="fig" title="([^"]*)"><span class="n">([^<]*)</span>'
    r'<span class="u(?: x)?">([^<]*)</span></span>'
)
SLICE = re.compile(
    r'class="sl s(\d) (green|amber|red|hollow)(?: (cut|open))?" data-step="([a-z_]+)"'
    r'(?: data-cause="([a-z_]+)")?'
)
CHECK_ROW = re.compile(
    r'<tr class="ck (held|failed|undecided)"(?: id="ck-[a-z_]+")?><th scope="row">'
    r'<a href="/checks#([a-z_]+)"'
)
PETALS = ("unforgeable", "weights_hidden", "faithful_model", "machine_checked", "no_trusted_party")
STEP_STATE = {"green": "green", "amber_upper": "amber", "amber_lower": "amber", "red": "red",
              "none": "hollow"}  # fmt: skip
CHECKS = ("run", "model", "prompt", "reply", "no_weight_file", "fidelity")


def resolve(doc: Any, pointer: str) -> Any:
    for raw in pointer.strip("/").split("/"):
        part = raw.replace("~1", "/").replace("~0", "~")
        doc = doc[int(part)] if isinstance(doc, list) else doc[part]
    return doc


def pages(out: Path) -> dict[str, str]:
    return {p.name: p.read_text() for p in sorted(out.glob("*.html"))}


def rows(board: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for rung in board["rungs"] for row in rung["rows"]]


def test_every_printed_figure_is_a_board_value(board_site: Any) -> None:
    """AGENTS.md rules 2 and 3: each figure names its record in the board, and prints that
    stored value in its unit, through the renderer's own number words."""
    number = board_site.build.number
    seen = 0
    for name, text in pages(board_site.out).items():
        assert text.count('class="fig"') == len(FIG.findall(text)), name
        for title, n, said in FIG.findall(text):
            record = re.search(r"record: [^#]+#(/[^;\"]+)", html.unescape(title))
            assert record, (name, title)
            stored = resolve(board_site.board, record[1])
            if isinstance(stored, dict):  # a quantity: its own unit
                want = number(stored["value"], stored["unit"])
                unit = said  # a rate may name its GPU in its unit
                if stored["unit"] == "token/gpu_s":
                    unit = re.sub(r"^tokens/s per \S+$", want[1], said)
                assert (n, unit) == want, (name, record[1])
            elif said == "tokens":  # a mean matched prefix
                assert n == board_site.build.sig(stored), (name, record[1])
            else:  # a session's GPU-seconds per reply
                assert (n, said) == number(stored, "gpu_s/request"), (name, record[1])
            seen += 1
    assert seen > 40


PERCENT = re.compile(
    r'<(?:a|span) class="fig(?: fp)?"[^>]*? title="([^"]*)"><span class="n">([^<]*)</span>'
    r'<span class="u">%</span>'
)


def test_fidelity_percentages_are_the_boards(release_site: Any) -> None:
    """RFC-0018 SI-9: every printed Fidelity figure (a row's on the ladder and on its page, a
    copy's in the Fidelity block and its table) is the `percent` the release's board computed,
    at one decimal."""
    seen = set()
    for name, text in pages(release_site.out).items():
        for title, n in PERCENT.findall(text):
            record = re.search(r"record: [^#]+#(/[^;\"]+)", html.unescape(title))
            assert record, (name, title)
            assert n == f"{resolve(release_site.board, record[1]):.1f}", (name, record[1])
            seen.add(record[1])
    scored = [row["system"] for rung in release_site.board["rungs"]
              for row in rung["rows"] if (rung.get("teacher_forced") or {}).get("rows", {})
              .get(row["system"], {}).get("percent") is not None]  # fmt: skip
    assert all(any(p.endswith(f"/rows/{s}/percent") for p in seen) for s in scored)


def test_the_count_against_the_proofs_is_the_boards(release_site: Any) -> None:
    """RFC-0018 FI-16: a system's page prints the board's count of positions a proof covers and
    of those its code agreed at, whole and at the positions where the two replies part."""
    seen = 0
    text = "".join(pages(release_site.out).values())
    for rung in release_site.board["rungs"]:
        for entry in (rung.get("teacher_forced") or {}).get("rows", {}).values():
            tie = entry.get("proved_tokens")
            if tie is None:
                continue
            assert f"{tie['agreeing']:,} of {tie['positions']:,} positions" in text
            assert f"{tie['split_agreeing']:,} of {tie['split_positions']:,} where" in text
            seen += 1
    assert seen


def arm(p: dict[str, Any]) -> tuple[str, str, str, str, str]:
    """A board petal as its arm must be drawn: (state, form, step, cause). The form is the rule's
    (§The glyph, Q7): cut for amber in lesser part, open for a red the publisher's silence set."""
    step = p["step"] or "none"
    form = "cut" if step == "amber_lower" else "open" if (
        p["state"] == "red" and p["cause"] == "not_stated") else ""  # fmt: skip
    return p["id"], p["state"], form, step, p["cause"] or ""


def drawn(found: list[tuple[str, ...]]) -> list[tuple[str, str, str, str, str]]:
    return [(PETALS[int(n) - 1], s, f, st, c) for n, s, f, st, c in found]


def test_glyphs_draw_the_board_states(board_site: Any) -> None:
    """GL-5, §The glyph (Q7): every glyph of a row, on the overview and on its page, draws its
    five petals in order, one arm each, with the board's state, step and cause, in the form its
    step and cause give; a petal the board marks as our reading says so on the page; the page's
    checks table prints the board's check states."""
    text = pages(board_site.out)
    index = text["index.html"]
    for row in rows(board_site.board):
        assert [p["id"] for p in row["glyph"]] == list(PETALS)
        want = [arm(p) for p in row["glyph"]]
        assert all(STEP_STATE[step] == state for _, state, _, step, _ in want), row["system"]
        tr = re.search(rf'<tr class="row" id="row-{row["system"]}">(.*?)</tr>', index, re.S)
        assert tr, row["system"]
        found = drawn(SLICE.findall(tr[1]))
        assert found
        assert tr[1].count('class="sl ') == len(found)
        assert len(found) % 5 == 0
        for k in range(0, len(found), 5):
            assert found[k : k + 5] == want, row["system"]
        page = text[f"{row['system']}.html"]
        assert page.count('class="sl ') == 5, row["system"]
        assert drawn(SLICE.findall(page)) == want, row["system"]
        read = [p.get("reading", False) and p["basis"] == "statement" for p in row["glyph"]]
        assert page.count('href="/checks#reading"') == sum(read), row["system"]
        checks = [(c, s) for s, c in CHECK_ROW.findall(page)]
        assert checks == [(c, row["checks"][c]["state"]) for c in CHECKS], row["system"]


def test_petal_rows_count_the_boards_items_for_met(board_site: Any) -> None:
    """SI-3 (amended 2026-11-17): a petal's row counts the board's items missing for Met
    (`to_met`) and who acts on them, never typed; at Met it counts none."""
    text = pages(board_site.out)
    for row in rows(board_site.board):
        page = text[f"{row['system']}.html"]
        trs = re.findall(r'<tr class="pt [^"]*"[^>]*>(.*?)</tr>', page, re.S)
        assert len(trs) == len(row["glyph"]), row["system"]
        for tr, p in zip(trs, row["glyph"], strict=True):
            tag = re.search(r'<span class="pdl">(.*?)<span class="sr">', tr, re.S)
            assert tag, (row["system"], p["id"])
            said = html.unescape(re.sub(r"<[^>]+>", "", tag[1]))
            groups = p.get("to_met")
            if groups is None:  # a board from before 2026-11-17: its next step's needs
                nx = p.get("next")
                groups = [{"items": nx["needs"]}] if nx else []
            items = [i for g in groups for i in g["items"]]
            if not items:
                assert "missing" not in said, (row["system"], p["id"])
                continue
            us = sum(1 for i in items if i["by"] == "us")
            pub = len(items) - us
            who = "publisher" if not us else "us" if not pub else f"{pub} publisher, {us} us"
            assert said == f"{len(items)} missing \u00b7 {who}", (row["system"], p["id"], said)


def test_order_and_positions_are_the_boards(board_site: Any) -> None:
    """OR-5: rows print in the board's order, a position only where the board holds one."""
    index = pages(board_site.out)["index.html"]
    printed = re.findall(r'<tr class="row" id="row-([^"]+)"><td class="cp">(.*?)</td>', index)
    want = [(r["system"], r["position"]) for r in rows(board_site.board)]
    got = [(sid, int(m[1]) if (m := re.search(r'class="pn">(\d+)<', cell)) else None)
           for sid, cell in printed]  # fmt: skip
    assert got == want
    # OR-6: the rung marked as the largest model with a passed row is the board's frontier, and no other
    marked = [sid for sid, sec in re.findall(r'<section class="rung" id="([^"]+)"(.*?)</section>',
                                             index, re.S) if 'class="rf"' in sec]  # fmt: skip
    front = board_site.board["frontier"]
    assert marked == ([front["rung"]] if front else [])


def test_no_v01_figure(board_site: Any, empty_site: Path) -> None:
    """SI-5: the v0.1 release is a record only. With no Level 1 board the site prints no figure
    at all, and neither build names v0.1 or one of its headline figures."""
    for name, text in pages(empty_site).items():
        assert 'class="fig"' not in text, name
    for out in (empty_site, board_site.out):
        for name, text in {**pages(out), "search.json": (out / "search.json").read_text()}.items():
            assert "v0.1" not in text, name
            for figure in ("5.746", "7.128", "61.28"):
                assert figure not in text, (name, figure)


def test_every_rung_not_run_without_a_board(empty_site: Path) -> None:
    """With no board, each rung of the level file is drawn, and drawn as not run."""
    from iproofs.serialize import load_yaml  # noqa: PLC0415

    level = load_yaml(Path(__file__).resolve().parents[1] / "levels/L1.yaml")
    index = (empty_site / "index.html").read_text()
    sections = re.findall(r'<section class="rung" id="([^"]+)"(.*?)</section>', index, re.S)
    assert [s for s, _ in sections] == [r["id"] for r in level["rungs"]]  # type: ignore[index]
    assert all("not run yet" in body and "<table" not in body for _, body in sections)


OVERVIEW_PANEL = re.compile(
    r'<div class="ov" id="ov-([a-z-]+)"(?: data-xlo="(-?\d+)" data-xhi="(-?\d+)" '
    r'data-ylo="(-?\d+)" data-yhi="(-?\d+)")?>(.*?)(?=<section class="blk ovp"|<section class="omd")',
    re.S,
)


def overview_panels(text: str) -> dict[str, tuple[tuple[int, ...] | None, str]]:
    """The Overview page's sections by figure: the two axes' ends (xlo, xhi, ylo, yhi), or None
    where the section draws no plot, and the section's markup."""
    return {dim: (tuple(int(v) for v in ends) if ends[0] else None, body)
            for dim, *ends, body in OVERVIEW_PANEL.findall(text)}  # fmt: skip


def overview_place(text: str, name: str, key: str) -> str:
    """A custom property the page's own rules set on the element with that id."""
    found = re.search(rf"#{re.escape(name)}\{{[^}}]*--{key}:([^;}}]+)", text.replace("\\", ""))
    assert found, name
    return found[1]


def at(lo: int, hi: int, v: float) -> str:
    return f"{100 * (math.log10(v) - lo) / (hi - lo):.2f}%"


def test_system_page_drawings_sit_where_the_figures_say(board_site: Any) -> None:
    """RFC-0018 Q50: a system page's marks are geometry from the board. Hand-computed for the
    example board: FlashProve's rates, 10.27 proved and 849.9 served tokens/s, span the decades
    10 to 1,000, so the marks stand at (log10 10.2742 - 1) / 2 = 0.59 % and (log10 849.92 - 1) / 2
    = 96.47 %; SASH's two parts, 358.479 and 71.0, cut their bar at 358.479 / 429.479 = 834.68 of
    1,000. On the release board, each Fidelity mark stands at its entry's percent on the axis from
    the ten under the lowest to 100 %. An axis labels both its ends at any count of ticks."""
    board, out = board_site.board, pages(board_site.out)
    row, base = board["rungs"][0]["rows"][0], board["rungs"][0]["baseline"]
    rates = (row["session_reply_tokens_per_gpu_second"]["value"],
             base["reply_tokens_per_gpu_second"]["value"])  # fmt: skip
    marks = re.findall(r'<svg class="mk (me|ref)" x="([^"]+)"', out["flashprove.html"])
    assert marks == [("me", at(1, 3, rates[0])), ("ref", at(1, 3, rates[1]))]
    assert [x for _, x in marks] == ["0.59%", "96.47%"]
    assert re.findall(r'class="hb pbar".*?<rect class="bp" x="0.00" width="([^"]+)"',
                      out["sash.html"]) == ["834.68"]  # fmt: skip
    plots = board_site.build.draw.plots
    assert f"{plots.lin_x(92.03, 70, 100):.2f}" == "73.43"  # (92.03 - 70) / 30
    for count in range(3, 13):
        ticks = [(100 * i / (count - 1), "100,000") for i in range(count)]
        for width in (plots.PLOT_WIDE, plots.PLOT_BESIDE, plots.PLOT_NARROW):
            shown = plots.labelled(ticks, width)
            assert (shown[0], shown[-1]) == (0, count - 1), (count, width)
            # seven characters of 7.8 px: an end's words start or end on its tick, the others
            # are centred, and no two stand closer than 10 px
            edges = [(x, x + 54.6) if i == 0 else (x - 54.6, x) if i == count - 1
                     else (x - 27.3, x + 27.3)
                     for i in shown for x in [i * width / (count - 1)]]  # fmt: skip
            assert all(b[0] - a[1] >= 10 - 1e-9 for a, b in pairwise(edges)), (count, width)
    release = ROOT / "releases/v1.0/board.json"
    if not release.exists():
        return
    for rung in json.loads(release.read_text())["rungs"]:
        tf = rung.get("teacher_forced")
        for system, mine in ((tf or {}).get("rows") or {}).items():
            page = (WEB / f"{system}.html").read_text()
            block = page[page.index('id="fidelity"') :].split("</section>")[0]
            bar = ((rung.get("fidelity") or {}).get("bar") or {}).get("control")
            rows = [mine, *(c for c in tf["controls"] if c["id"] == bar or c["id"][:1] == "q")]
            low = min(
                90, 10 * math.floor(min(c["percent"] for c in rows if c["status"] == "ok") / 10)
            )
            me = re.findall(r'<svg class="mk me" x="([^"]+)"', block)
            assert me == [f"{100 * (mine['percent'] - low) / (100 - low):.2f}%"], system


def test_overview_positions_are_the_boards(board_site: Any) -> None:
    """RFC-0018 SI-7: on the Overview page a system's mark stands where its two printed figures
    meet, cost vs serving across and the section's figure up, each on its one axis over the
    whole board; a row not passed is marked so and says so; the systems keep the board's
    order. The extents and two places are hand-computed for the example board."""
    board = board_site.board
    text = pages(board_site.out)["overview.html"]
    panels = overview_panels(text)
    assert list(panels) == ["check-time", "proof-size", "fidelity"]
    figure = {"check-time": "verify_seconds_per_reply", "proof-size": "proof_bytes_per_reply"}
    for dim, key in figure.items():
        ends, body = panels[dim]
        assert ends is not None, dim
        xlo, xhi, ylo, yhi = ends
        boxes = re.findall(rf'<div class="obx (ok|np)[^"]*" id="ob-{dim}-([^"]+)"', body)
        assert [page for _, page in boxes] == [r["system"] for r in rows(board)], dim
        for (state, page), rung in zip(boxes, [g for g in board["rungs"] for _ in g["rows"]],
                                       strict=True):  # fmt: skip
            row = next(r for r in rung["rows"] if r["system"] == page)
            assert state == ("ok" if row["passed"] else "np"), (dim, page)
            mark = re.search(rf'id="ob-{dim}-{re.escape(page)}".*?</div>', body, re.S)
            assert mark
            assert ("Not passed" in mark[0]) == (not row["passed"]), (dim, page)
            # CO-5 (amended 2026-11-15): the whole sessions' scope wherever the row has it
            steady = row["session_multiple"]["value"] is None
            x = row["multiple" if steady else "session_multiple"]["value"]
            y = row[key]["value"] * (1e-6 if row[key]["unit"] == "B/request" else 1)
            assert overview_place(text, f"ob-{dim}-{page}", "x") == at(xlo, xhi, x), (dim, page)
            assert overview_place(text, f"ob-{dim}-{page}", "y") == at(ylo, yhi, y), (dim, page)
    # hand-computed: the multiple from 1x to 1,000x (sessions up to 612 / 1.408 = 434.6x);
    # FlashProve at its whole sessions' scope, 49.83 / 0.6024 = 82.72x (log10 / 3 = 63.92 %), not
    # its steady 68.31x; its proof, 18.79 MB between 1 and 100 MB (log10 / 2 = 63.70 %)
    assert panels["check-time"][0] == (0, 3, 0, 2)
    assert panels["proof-size"][0] == (0, 3, 0, 2)
    assert overview_place(text, "ob-proof-size-flashprove", "x") == "63.92%"
    assert overview_place(text, "ob-proof-size-flashprove", "y") == "63.70%"
    # a board with no Fidelity figure draws no Fidelity plot: every row is listed under its head
    ends, body = panels["fidelity"]
    assert ends is None
    listed = re.search(r'<div class="oof">(.*)', body, re.S)
    assert listed
    assert re.findall(r'<a class="sname" href="/([^"]+)"', listed[1]) == [
        r["system"] for r in rows(board)
    ]


def test_overview_fidelity_positions_are_the_boards(release_site: Any, board_site: Any) -> None:
    """RFC-0018 SI-7 (amended 2026-11-20): on the Overview page's Fidelity plot a mark stands at
    its row's `percent` up, on an axis from the ten under the lowest drawn value to 100 %, and at
    its multiple across. The axis's rule is hand-computed: over 86.4 and 92.0 % it runs from 80,
    where 86.4 % stands at (86.4 - 80) / 20 = 32 % of the way; a value of 0 % is drawn, at the
    axis's start."""
    build = board_site.build
    assert build.share_extent([86.4, 92.0]) == (80, 100)
    assert build.pc(build.lin_x(86.4, 80, 100)) == "32.00%"
    assert build.share_extent([0.0, 96.2]) == (0, 100)
    assert build.share_extent([97.0, 99.0]) == (90, 100)  # never a narrower stretch than 10 %
    board = release_site.board
    text = pages(release_site.out)["overview.html"]
    ends, _ = overview_panels(text)["fidelity"]
    assert ends is not None, "the release draws no Fidelity figure"
    xlo, xhi, lo, hi = ends
    drawn: list[float] = []
    for rung in board["rungs"]:
        tf = rung.get("teacher_forced") or {}
        for row in rung["rows"]:
            percent = (tf.get("rows") or {}).get(row["system"], {}).get("percent")
            if percent is None:
                continue
            name = f"ob-fidelity-{row['system']}"
            assert overview_place(text, name, "y") == f"{100 * (percent - lo) / (hi - lo):.2f}%"
            steady = row["session_multiple"]["value"] is None
            x = row["multiple" if steady else "session_multiple"]["value"]
            assert overview_place(text, name, "x") == at(xlo, xhi, x), name
            drawn.append(percent)
    assert drawn
    assert (lo, hi) == (min(90, 10 * math.floor(min(drawn) / 10)), 100)


def test_session_parts_print_on_the_system_page_only(board_site: Any) -> None:
    """RFC-0018 CO-7 (amended 2026-11-17): a row with no steady state has its session figure's two
    parts, and they print only under Cost on its system page (not every system times them apart,
    so no surface carries them). In the example board SASH's session is 604.9 GPU-s per reply, of
    which 100.0 generation and 504.9 commit and proving: both parts' figures are on its page, and
    neither is on the ladder, the Overview page or the card."""
    out = board_site.out
    at = "/rungs/1/rows/0/session_"
    for page in ("index.html", "overview.html", "sash.html", "og/sash.html"):
        text = html.unescape((out / page).read_text())
        for part in ("generation_multiple", "commit_and_proving_multiple"):
            assert (f"{at}{part}" in text) == (page == "sash.html"), (page, part)


def printed(text: str) -> tuple[float, float]:
    """A printed number and half its last printed place (its rounding's reach)."""
    places = len(text.split(".")[1]) if "." in text else 0
    return float(text.replace(",", "")), 0.5 * 10.0**-places


def test_printed_rates_divide_to_the_printed_multiple(board_site: Any) -> None:
    """CO-8 (amended 2026-11-17): the proved rate under a row's multiple and the served rate in
    its model's head, as printed, divide to the multiple printed above. By hand on the example
    board: 849.92 / 10.274 = 82.72, printed "10.27 proved" under "82.72×" and "849.9" in the
    head. A row with no rate pair (SASH there) prints no line."""
    out = board_site.out
    index = (out / "index.html").read_text()
    for pid, body in re.findall(r'<tr class="row" id="row-([a-z0-9-]+)">(.*?)</tr>', index, re.S):
        assert ('class="rts"' in body) == (pid == "flashprove"), pid
    # the same on the stored release: 2,669 / 2.027 = 1,316.7 against 1,317x; 11,876 / 0.1911 =
    # 62,146 against 62,160x
    number = board_site.build.number
    board = json.loads((WEB.parent / "releases/v1.0/board.json").read_text())
    for rung in board["rungs"]:
        served = (rung["baseline"] or {}).get("reply_tokens_per_gpu_second") or {}
        for r in rung["rows"]:
            proved = r.get("session_reply_tokens_per_gpu_second") or {}
            if served.get("value") is None or proved.get("value") is None:
                continue
            sv, p = (float(number(f["value"], f["unit"])[0].replace(",", ""))
                     for f in (served, proved))  # fmt: skip
            m = float(number(r["session_multiple"]["value"], "ratio")[0].replace(",", ""))
            assert abs(sv / p - m) <= 1e-3 * m, (r["system"], sv, p, m)
    for words in ("82.72", "10.27</span> proved", "849.9"):
        assert words in index, words
    assert abs(849.9 / 10.27 - 82.72) <= 1e-3 * 82.72


def test_completeness_count_is_the_boards(board_site: Any) -> None:
    """MC-6 (amended 2026-11-15, 2026-11-16): the Completeness line at the head of a system's glyph
    counts the replies of the board's counted sessions (their release groups summed), N of N."""
    text = pages(board_site.out)
    for row in rows(board_site.board):
        n = sum(sum(s["groups"]) for s in row["sessions"])
        page = html.unescape(text[f"{row['system']}.html"])
        assert f"{n:,}\u00a0of\u00a0{n:,} replies accepted" in page, row["system"]


def test_surface_figures_are_whole_sessions(board_site: Any) -> None:
    """RFC-0018 CO-5 and SI-1 (amended 2026-11-15, 2026-11-16): the ladder, a system's band and
    its card print each row's multiple at the whole sessions' scope wherever the row has one, so
    a rung never mixes two scopes; the steady figures stay below, under Cost. USD is under Cost
    only. In the example board FlashProve has both: its ladder row names session_multiple and the
    two rates it is made of (CO-8), never multiple or a USD figure."""
    out = board_site.out
    index = html.unescape((out / "index.html").read_text())
    tr = re.search(r'<tr class="row" id="row-flashprove">(.*?)</tr>', index, re.S)
    assert tr
    at = "/rungs/0/rows/0/"
    pages_ = {"index.html": tr[1]}
    for page in ("flashprove.html", "og/flashprove.html"):
        text = html.unescape((out / page).read_text())
        band = re.search(r'<section class="mast.*?</section>', text, re.S)
        pages_[page] = band[0] if band else text  # the band (all of a card)
    for page, text in pages_.items():
        pointers = set(re.findall(r"record: [^#]+#(/[^;\"]+)", text))
        assert f"{at}session_multiple" in pointers, page
        assert f"{at}multiple" not in pointers, page
        assert not any("usd" in p for p in pointers), page
    rates = set(re.findall(r"record: [^#]+#(/[^;\"]+)", pages_["index.html"]))
    assert {f"{at}session_reply_tokens_per_gpu_second",
            "/rungs/0/baseline/reply_tokens_per_gpu_second"} <= rates  # fmt: skip


def test_a_lone_system_is_not_drawn_as_ranked(board_site: Any) -> None:
    """RFC-0018 OR-4 (amended 2026-11-15): a ranked row that is the only system run on its model
    is an outline square that says so, never a filled "1 of 1", on the ladder and its card."""
    out, build = board_site.out, board_site.build
    index = (out / "index.html").read_text()
    assert all(r["systems_run"] == 1 for r in board_site.board["rungs"])  # the example board
    row, lone, shared = {"position": 1}, {"systems_run": 1}, {"systems_run": 2}
    assert build.position_html(row, lone) in index  # every ranked row here is a lone one
    assert build.position_html(row, shared) not in index
    assert build.ONLY_RUN in build.position_html(row, lone)
    assert build.ONLY_RUN not in build.position_html(row, shared)


def test_a_p_at_its_test_floor_reads_as_a_bound(board_site: Any) -> None:
    """FI-4: a drawn p with no resample at least as extreme is 1 / (1 + 200,000), the lowest
    the test gives, so it prints as a bound; a counted p at 2^-15 is exact and says it is the
    floor; any other p is its value."""
    said, p_html = board_site.build.p_said, board_site.build.p_html
    drawn = html.unescape(said(1 / 200_001, 360))
    assert drawn.startswith("p\u00a0<\u00a05.0"), drawn  # a bound: no resample was as extreme
    counted = said(2.0**-15, 15)
    assert html.unescape(counted).startswith("p\u00a0=\u00a03.1"), counted  # exact, and floor
    assert counted != "p\u00a0=\u00a0" + p_html(2.0**-15)
    assert said(0.0058, 15) == "p\u00a0=\u00a0" + p_html(0.0058)
    assert said(4 / 2**15, 15) == "p\u00a0=\u00a0" + p_html(4 / 2**15)


def test_gpt2_prints_the_model_card_count() -> None:
    """The level file records GPT-2 at 137,022,720, the Hub's safetensors total, which counts its
    12 causal-mask buffers of 1 x 1 x 1,024 x 1,024; the site prints 137,022,720 less them,
    124,439,808, which reads 124M, the count the model card states."""
    from iproofs.site.view import site_view  # noqa: PLC0415

    view = site_view(Path(__file__).resolve().parents[1])
    gpt2 = next(r for r in view["rungs"] if r["id"] == "gpt-2")
    assert gpt2["parameters_total"] == 137_022_720 - 12 * 1024 * 1024 == 124_439_808
    assert "124M" in gpt2["parameters_erratum"]["card"]["quote"]


def test_cost_block_figures_share_the_bands_scope(board_site: Any) -> None:
    """CO-5 (amended 2026-11-17): the figures that lead a system page's Cost block (the two rates
    and the cost in USD; the multiple is the band's alone) are of the scope the band prints, so
    the block never sets a steady figure beside a whole-session one. In the example board
    FlashProve has both scopes: its Cost drawing and tiles name the proved rate and
    session_usd_per_reply, never multiple or steady_usd_per_reply."""
    text = html.unescape((board_site.out / "flashprove.html").read_text())
    block = re.search(r'<section class="blk" id="cost"(.*?)<details', text, re.S)
    assert block
    pointers = set(re.findall(r"record: [^#]+#(/[^;\"]+)", block[1]))
    at = "/rungs/0/rows/0/"
    assert {f"{at}session_reply_tokens_per_gpu_second", f"{at}session_usd_per_reply"} <= pointers
    assert not {f"{at}multiple", f"{at}steady_usd_per_reply"} & pointers


def test_fidelity_row_figures_are_the_boards(board_site: Any) -> None:
    """GL-11, SI-3 (amended 2026-11-17): a Fidelity petal's row prints the row's mean matched
    leading tokens and the 8-bit and 4-bit copies' means at the Fidelity check's precision (four
    significant digits), and the first threshold missing for Met with the step it reaches, at the
    board's one decimal; none at Met. On the stored release by hand: FlashProve 29.66 (8-bit
    65.71, 4-bit 30.29), Mostly met at 48.0; SASH 31.00 (8-bit 106.1, 4-bit 5.267), Mostly met at
    55.7."""
    figures = board_site.build.draw.petal.fidelity_figures
    board = json.loads((WEB.parent / "releases/v1.0/board.json").read_text())
    petals = {row["system"]: next(p for p in row["glyph"] if p["id"] == "faithful_model")
              for row in rows(board)}  # fmt: skip
    # the view's `facts` is the board's petal record (iproofs.site.view)
    got = {k: figures({**p, "facts": p["fidelity"]}) for k, p in petals.items()}
    assert got == {
        "flashprove": {
            "own": "29.66",
            "q8": "65.71",
            "q4": "30.29",
            "next": ("Mostly met", "48.0"),
        },
        "sash": {"own": "31.00", "q8": "106.1", "q4": "5.267", "next": ("Mostly met", "55.7")},
    }
    met = petals["flashprove"]
    assert figures({**met, "facts": met["fidelity"], "to_met": []})["next"] is None
