"""RFC-0018 SI-4a: a system not run carries the source of its reason, and the stored facts follow
the rule's order where the review of 2026-11-15 found them filed apart."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from iproofs.errors import IProofsError
from iproofs.site.view import not_run

ROOT = Path(__file__).resolve().parents[3]


def _facts(**rows: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(rows=rows)


def _row(reason: str, source: SimpleNamespace | None) -> SimpleNamespace:
    return SimpleNamespace(name=reason.title(), reason=reason, reason_source=source)


def test_a_reason_without_its_source_stops_the_build() -> None:
    with pytest.raises(IProofsError, match="reason_source"):
        not_run(_facts(x=_row("licence", None)), ran=set())


def test_not_yet_run_needs_no_source_and_a_run_system_is_not_listed() -> None:
    src = SimpleNamespace(words="w", url="https://example.org")
    out = not_run(_facts(a=_row("not yet run", None), b=_row("licence", src),
                         c=_row("licence", None)), ran={"c"})  # fmt: skip
    assert [(r["id"], r["source"]) for r in out] == [
        ("b", {"words": "w", "url": "https://example.org"}), ("a", None)]  # fmt: skip


def test_stored_reasons_follow_the_rule() -> None:
    rows = json.loads((ROOT / "web/_data/facts.json").read_text())["rows"]
    reasons = {k: rows[k]["reason"] for k in ("deepprove", "jolt-atlas", "zkllm", "zkgpt")}
    assert reasons == {"deepprove": "no public verifier", "jolt-atlas": "no public verifier",
                       "zkllm": "no public verifier", "zkgpt": "a different statement"}  # fmt: skip
