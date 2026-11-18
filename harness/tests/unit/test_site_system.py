"""RFC-0018 SI-3 (amended 2026-11-15): a Statement row prints the claim card's own text with the
link the card gives it, never another field's link."""

import pytest

from iproofs.errors import IProofsError
from iproofs.site.system import card_refs

CARD = {
    "assumptions": ["first", "second", "third"],
    "binding": {"statement": "the ID is a hash"},
    "sources": {"assumptions": "https://x/a#L1", "assumptions.2": "https://x/a#L3",
                "binding": "https://x/b#L9"},
}  # fmt: skip


def test_item_and_nested_field_links() -> None:
    """Item 0 of a list takes the list's link; item 2 its own; a nested field its parent's."""
    got = card_refs(CARD, ["assumptions.0", "assumptions.2", "binding.statement"], "t")
    assert got is not None
    assert [(r["text"], r["url"]) for r in got] == [
        ("first", "https://x/a#L1"), ("third", "https://x/a#L3"),
        ("the ID is a hash", "https://x/b#L9")]  # fmt: skip


def test_item_without_its_own_link_is_refused() -> None:
    """Item 1 has no `assumptions.1` key: the list's link is item 0's, so it is not used."""
    with pytest.raises(IProofsError):
        card_refs(CARD, ["assumptions.1"], "t")


def test_not_stated_and_unknown_field() -> None:
    assert card_refs(CARD, "not stated", "t") is None
    with pytest.raises(IProofsError):
        card_refs(CARD, ["assumptions.9"], "t")
