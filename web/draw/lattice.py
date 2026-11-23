"""The lattice in a band: a field of cells on a square grid, each a cipher character, a tile or a
dot, thickest in the band's lower right corner and thinning by levels (characters and tiles,
then dots, then nothing) toward its title. A few cells are lit, in the accent, its light and
its deep blue. It is a drawing of the idea the site measures, something unreadable that gets
checked, and it carries no data: every cell comes from a hash of the page's address, so a page
keeps its field from build to build. words.css places it, keeps it clear of a band's small text
and passes one line of light over it when a page arrives.
"""

import hashlib

CELL = 18  # px at a 1500 px screen; the field scales with the screen
COLS, ROWS = 64, 34
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


def _cell(seed, i, j, reach):
    """(kind, tone, drawing) of the cell at column i (0 the rightmost) and row j (0 the lowest),
    or None where the field is empty: kind fill and ring carry a path, text and cut a character."""
    t = 1.0 - (i / reach) ** 1.15 - (j / ROWS) * 0.42 + (_r(seed, i, j, "j") - 0.5) * 0.3
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


def lattice(seed, reach=62):
    """The field for one band, as an svg; `reach`, the columns it takes to thin out (fewer under a
    band whose lines of text run long)."""
    fills, rings, texts = {}, {}, {}
    for i in range(COLS):
        for j in range(ROWS):
            cell = _cell(seed, i, j, reach)
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
    return (f'<div class="latw" aria-hidden="true"><svg class="lat" viewBox="0 0 {w} {h}" '
            f'focusable="false">{"".join(out)}</svg></div>')  # fmt: skip
