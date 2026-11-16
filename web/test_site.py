"""The site against the board file it is built from: every printed figure is a value the board
stores, every glyph draws the board's petal steps and causes and its check states, and no v0.1
figure is printed (RFC-0018 SI-1,
SI-3, SI-5, CH-7). Run from the repository root: uv run pytest web -q
"""

import html
import json
import math
import re
from pathlib import Path
from typing import Any

WEB = Path(__file__).resolve().parent

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


def test_petal_rows_print_the_boards_reasons(board_site: Any) -> None:
    """SI-3 (amended 2026-11-16): a petal's default line is its board reason's first clause and
    the count of the clauses cut (Fidelity's reason whole, its last clause the row's measure),
    never typed, and the full reason sits in the petal's disclosure."""
    text = pages(board_site.out)
    for row in rows(board_site.board):
        page = text[f"{row['system']}.html"]
        trs = re.findall(r'<tr class="pt [^"]*">(.*?)</tr>', page, re.S)
        assert len(trs) == len(row["glyph"]), row["system"]
        for tr, p in zip(trs, row["glyph"], strict=True):
            line = re.search(r'<span class="rs">([^<]*)</span>', tr)
            assert line, (row["system"], p["id"])
            clauses = p["reason"].split("; ")
            first = (p["reason"] if p["basis"] == "test" or len(clauses) == 1
                     else f"{clauses[0]}, and {len(clauses) - 1} more")  # fmt: skip
            assert html.unescape(line[1]) == first, (row["system"], p["id"])
            assert p["reason"] in html.unescape(tr), (row["system"], p["id"])


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


SCALE_LANE = re.compile(
    r'<table class="scl" data-lo="(-?\d+)" data-hi="(-?\d+)">(.*?)</table>', re.S
)
SCALE_ROW = re.compile(
    r'<tr class="row (ok|np)" id="scale-(multiple|check-time|proof-size)-([^"]+)">(.*?)</tr>',
    re.S,
)


def at(lo: int, hi: int, v: float) -> str:
    return f"{100 * (math.log10(v) - lo) / (hi - lo):.2f}%"


def test_scale_positions_are_the_boards(board_site: Any) -> None:
    """RFC-0018 SI-7: on the scale page, each mark sits where its row's printed figure falls on
    the figure's one decade grid, its session ticks where the board's sessions fall, serving's
    line where the rung's baseline falls; a row not passed is an outline; lanes and rows keep the
    board's order. The extents and two positions are hand-computed for the example board."""
    board = board_site.board
    text = pages(board_site.out)["scale.html"]
    lanes = SCALE_LANE.findall(text)
    assert len(lanes) == 3  # one table per figure, every lane under its one axis
    seen: dict[str, list[str]] = {}
    for lo_s, hi_s, body in lanes:
        lo, hi = int(lo_s), int(hi_s)
        for state, dim, _, tr in SCALE_ROW.findall(body):
            title = FIG.search(tr)
            assert title, (dim, tr[:80])
            pointer = re.search(r"record: [^#]+#(/[^;\"]+)", html.unescape(title[1]))
            assert pointer
            stored = resolve(board, pointer[1])
            at_row = pointer[1].rsplit("/", 1)[0]
            row = resolve(board, at_row)
            base = resolve(board, at_row.rsplit("/", 2)[0])["baseline"]
            seen.setdefault(dim, []).append(row["system"])
            assert state == ("ok" if row["passed"] else "np"), (dim, row["system"])
            v = stored["value"] * (1e-6 if stored["unit"] == "B/request" else 1)
            assert re.findall(r'<svg class="mk" x="([^"]+)"', tr) == [at(lo, hi, v)], (
                dim,
                row["system"],
            )
            # CO-5 (amended 2026-11-15): the whole sessions' scope wherever the row has it
            steady = row["session_multiple"]["value"] is None
            runs = [s["m" if steady else "session"] for s in row["sessions"]]
            if dim == "multiple":
                b = base["gpu_seconds_per_reply"]["value"]
                ticks, serve = [r / b for r in runs if r is not None], 1.0
            else:
                ticks, serve = [], None
            got = re.findall(r'<line class="ss" x1="([^"]+)"', tr)
            assert got == [at(lo, hi, t) for t in ticks], (dim, row["system"])
            sv = re.findall(r'<line class="sv" x1="([^"]+)"', tr)
            assert sv == ([at(lo, hi, serve)] if serve else []), (dim, row["system"])
    for dim in ("multiple", "proof-size", "check-time"):
        assert seen[dim] == [r["system"] for r in rows(board)], dim
    # hand-computed: the multiple from 1× to 1,000× (sessions up to 612 / 1.408 = 434.6×);
    # FlashProve at its whole sessions' scope, 49.83 / 0.6024 = 82.72× (log10 / 3 = 63.92 %), not
    # its steady 68.31×
    assert [(lo, hi) for lo, hi, _ in lanes] == [("0", "3"), ("0", "2"), ("0", "2")]
    assert re.search(r'id="scale-multiple-flashprove">.*?class="mk" x="63.92%"', text, re.S)


def test_session_parts_print_beside_the_whole_sessions_figure(board_site: Any) -> None:
    """RFC-0018 CO-7: a row with no steady state prints its session figure's two parts. In the
    example board SASH's session is 604.9 GPU-s per reply, of which 100.0 generation and 504.9
    commit and proving, so the ladder's share bar gives commit and proving 100 * 504.9 / 604.9 =
    83.47 % of its length; both parts' figures are on the ladder (over the two rates there,
    amended 2026-11-16), the system page and the card."""
    out = board_site.out
    at = "/rungs/1/rows/0/session_"
    for page in ("index.html", "sash.html", "og/sash.html"):
        text = html.unescape((out / page).read_text())
        for part in ("generation_multiple", "commit_and_proving_multiple"):
            assert f"{at}{part}" in text, (page, part)
    assert '<rect class="bp" width="83.47"' in (out / "index.html").read_text()


def printed(text: str) -> tuple[float, float]:
    """A printed number and half its last printed place (its rounding's reach)."""
    places = len(text.split(".")[1]) if "." in text else 0
    return float(text.replace(",", "")), 0.5 * 10.0**-places


def test_printed_rates_divide_to_the_printed_multiple(board_site: Any) -> None:
    """CO-8 (amended 2026-11-17): the proved rate under a row's multiple and the served rate in
    its model's head, as printed, divide to the multiple printed above. By hand on the example
    board: 849.92 / 10.274 = 82.72, printed "10.27 proved" under "82.72×" and "849.9" in the
    head. A row with no rate pair (SASH there) prints no line, and keeps its parts
    (`test_session_parts_print_beside_the_whole_sessions_figure`)."""
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
        pages_[page] = text.split('class="figs"')[0]  # the band (all of a card)
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
