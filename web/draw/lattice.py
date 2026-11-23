"""The lattice at a band's foot: a rail of cells on a square grid, each a cipher character, a tile
or a dot, thick along the band's lower edge and thinning upward by levels (characters and
tiles, then dots). A few cells are lit, in the accent, its light and its deep blue. It is a
drawing of the idea the site measures, something unreadable that gets checked, and it carries
no data: every cell comes from a hash of the page's address, so a page keeps its rail from
build to build. words.css places it under everything a band holds and passes one line of light
along it when a page arrives; a lens follows the pointer along it (words.js), the cells under
it drawn once more in brighter inks.
"""

import hashlib

CELL = 18  # px
COLS, ROWS = 150, 3  # wide enough for a 2700 px screen; the rows from the band's lower edge up
LEVEL = (0.92, 0.74, 0.5)  # how thick each row is, the lowest first
CHARS = "0123456789ABCDEF#%&$@+=*/<>?!;"
# a tile's outline from its cell's corner, in the cell's own units
TILES = (
    "m3 3h12v12h-12z",  # square
    "m9 3l6 6l-6 6l-6-6z",  # diamond
    "m3 9a6 6 0 1 0 12 0a6 6 0 1 0-12 0z",  # disc
    "m3 15v-12a12 12 0 0 1 12 12z",  # quarter
    "m9 3q0 6 6 6q-6 0-6 6q0-6-6-6q6 0 6-6z",  # star
)
RING = "m4 9a5 5 0 1 0 10 0a5 5 0 1 0-10 0z"
DOT = "m8 8h2v2h-2z"
LIT = (("p", 0.03), ("a", 0.016), ("c", 0.009))  # the lit cells' shares: light, accent, deep


def _r(seed, i, j, k):
    h = hashlib.sha256(f"{seed}:{i}:{j}:{k}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 2**32


def _esc(ch):
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)


def _tone(seed, i, j, t):
    """A cell's ink: lit only where the field is thick, else one of the band's two near inks."""
    q = _r(seed, i, j, "l")
    for name, share in LIT if t >= 0.62 else ():
        if q < share:
            return name
        q -= share
    return "b" if _r(seed, i, j, "b") < 0.3 else "d"


def _cell(seed, i, j):
    """(kind, tone, drawing) of the cell at column i (0 the rightmost) and row j (0 the lowest),
    or None where the field is empty: kind fill and ring carry a path, text and cut a character."""
    t = LEVEL[j] + (_r(seed, i, j, "j") - 0.5) * 0.3
    if t < 0.45:  # the lowest level: a dot, or nothing
        return ("fill", "d", DOT) if t >= 0.25 and _r(seed, i, j, "s") < 0.55 else None
    if _r(seed, i, j, "g") < (0.34 if t < 0.7 else 0.14):
        return None
    tone, k = _tone(seed, i, j, t), _r(seed, i, j, "k")
    lit = tone in "pac"
    if not lit and ((t < 0.7 and k < 0.45) or k < 0.22):  # a tile
        n = int(_r(seed, i, j, "t") * (len(TILES) + 1))
        return ("ring", tone, RING) if n == len(TILES) else ("fill", tone, TILES[n])
    ch = _esc(CHARS[int(_r(seed, i, j, "c") * len(CHARS))])
    # a coded square (its character cut out of it), or the character alone
    return ("cut" if k < 0.3 or (lit and k < 0.7) else "text", tone, ch)


def lattice(seed):
    """The rail for one band, as an svg in its box."""
    fills, rings, texts = {}, {}, {}
    for i in range(COLS):
        for j in range(ROWS):
            cell = _cell(seed, i, j)
            if not cell:
                continue
            kind, tone, what = cell
            x, y = (COLS - 1 - i) * CELL, (ROWS - 1 - j) * CELL
            if kind in ("fill", "ring"):
                (fills if kind == "fill" else rings).setdefault(tone, []).append(f"M{x} {y}{what}")
                continue
            if kind == "cut":
                fills.setdefault(tone, []).append(f"M{x} {y}{TILES[0]}")
            texts.setdefault(("k" if kind == "cut" else tone, y), []).append((x + CELL // 2, what))
    out = [f'<path class="{t}" d="{"".join(d)}"/>' for t, d in fills.items()]
    out += [f'<path class="{t} o" d="{"".join(d)}"/>' for t, d in rings.items()]
    for (t, y), row in sorted(texts.items()):
        row.sort()
        out.append(f'<text class="{t}" y="{y + 13}" x="{" ".join(str(x) for x, _ in row)}">'
                   f'{"".join(c for _, c in row)}</text>')  # fmt: skip
    w, h = COLS * CELL, ROWS * CELL
    box = f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" focusable="false"'
    # the rail, then the same cells once more inside the lens (words.css, words.js): drawn by reference, in brighter inks
    return (f'<div class="latw" aria-hidden="true"><svg class="lat" {box}><g id="lat-g" class="lg">{"".join(out)}</g></svg>'
            f'<div class="lens"><div class="lensin"><svg class="lat hot" {box}><use href="#lat-g"/></svg></div></div>'
            "</div>")  # fmt: skip
