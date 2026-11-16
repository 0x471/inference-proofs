"""The glossary's entries as links: what a Learn page's [[term]] and a system page's defined word
(session, whole session, slot, the evidence) carry. Apart from learn.py, which imports it, so a
page drawn by pages.py links a term without importing the Learn pages (figures.py, which learn.py
imports, imports pages.py)."""

import re

from . import state as S
from .words import e


class Halt(RuntimeError):
    """A page's text is outside the subset: `iproofs site build` reports it as a config error."""


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# the spaces a source line wraps at (str.split would eat a no-break one)
LINE_SPACE = re.compile(r"[ \t\n]+")


def squeeze(text):
    """Lines of the source as one line: its own wrapping spaces joined, a no-break space kept."""
    return LINE_SPACE.sub(" ", text).strip()


def glossary():
    return S.V["learn"]["glossary"]


def plain(text):
    """A text of the subset without its marks: for a line of the search index."""
    text = re.sub(
        r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]|\[([^\]]+)\]\([^)]+\)", lambda m: m[1] or m[2], text
    )
    return re.sub(r"[*`]", "", text)


def glossary_entries():
    """Each glossary term: its name, its id and the first sentence under it."""
    found = re.finditer(r"^### (.+)\n+((?:.+\n?)+)", glossary()["text"], re.M)
    return [(m[1], slug(m[1]), plain(squeeze(m[2])).split(". ")[0].rstrip(".") + ".")
            for m in found]  # fmt: skip


def defs():
    """Each glossary term's name and first sentence, by its id: what a link to it carries, for
    the reader who points at it or gives it focus (words.js)."""
    return {tid: (name, first) for name, tid, first in glossary_entries()}


def term(words, name):
    """`words` linked to the glossary entry `name`, wherever a page prints a term a reader may
    not know (session, whole session, slot, the evidence): the link leads to its definition on
    a phone, which has no hover (DEPTH law 3), and carries its first sentence for a pointer
    (words.js). The words alone where the tree holds no Learn words; a name the glossary lacks
    stops the build."""
    if not S.V.get("learn"):
        return e(words)
    tid = slug(name)
    found = defs().get(tid)
    if found is None:
        raise Halt(f"{name!r} is not a glossary entry")
    return (f'<a class="df" href="/{glossary()["slug"]}#{tid}" data-g="{e(found[0])}" '
            f'data-d="{e(found[1])}">{e(words)}</a>')  # fmt: skip
