"""RFC-0018 GL-11 (amended 2026-11-17): what a petal lacks for Met (`to_met`), the facts its
reading rests on, the Why line's inputs and the Fidelity petal's printed numbers, computed on
hand-built inputs and on the stored v1.0 board. Each case asserts keys, counts and numbers,
never wording; none reads or sets a step."""

import json
from pathlib import Path

import pytest

from fixtures.board import PIN, fact, properties2
from iproofs.glyph import Coverage, Petal, q_cross, statement_petals, unforgeable

ROOT = Path(__file__).resolve().parents[3]
HELD = dict.fromkeys(("run", "model", "prompt", "reply", "no_weight_file", "fidelity"), "held")
ONE = Coverage("request", 1)
BOARD = json.loads((ROOT / "releases" / "v1.0" / "board.json").read_text())
ROWS = {row["system"]: row for rung in BOARD["rungs"] for row in rung["rows"]}


def petal(system: str, pid: str) -> dict[str, object]:
    return next(p for p in ROWS[system]["glyph"] if p["id"] == pid)


def needs(groups: object) -> list[list[tuple[str, str]]]:
    assert isinstance(groups, list)
    return [[(str(i["need"]), str(i["by"])) for i in g["items"]] for g in groups]


def uf(coverage: Coverage = ONE, **bound: object) -> Petal:
    return unforgeable(properties2(bound=bound), HELD, PIN, coverage)


@pytest.mark.parametrize(
    ("expression", "after", "found"),
    [
        ("q/2^124 + 2^-101", "q hash queries", [24, 44]),
        ("q / 2^(130) + 2^-128", "q queries", [30, 50]),
        ("q/2^124 + 2^-101", None, None),  # `after` names no q
        ("q/2^124 + 2^-101", "rounds", None),
        ("2^-128", "q hash queries", None),  # no term written q/2^t
    ],
)
def test_q_cross(expression: str, after: str | None, found: list[int] | None) -> None:
    bound: dict[str, object] = {"expression": {"value": expression}}
    if after is not None:
        bound["after"] = {"value": after}
    assert q_cross(bound) == found


def test_uf9_to_met_follows_the_failing_conditions() -> None:
    """UF-9: one item per failing condition, program first, in the reason's order, then Met's
    own: every term at most 2^-128 and the words in place of each reading. The Why line's items
    are the cover conditions, its floor 80 on a proved bound and 100 otherwise."""
    read = fact("any_prover", commit=PIN) | {"note": "read"}
    p = uf(Coverage("request", 24), batch="together", conditions_shown=False,
           program="not_stated", terms=[124, 101], adversary=read)  # fmt: skip
    assert p.step == "amber_lower"
    tree = p.tree()
    assert needs(tree["to_met"]) == [
        [("program", "publisher"), ("batch", "publisher"), ("conditions", "publisher")],
        [("exponent", "publisher"), ("reading", "publisher")],
    ]
    assert tree["to_met"][1]["items"][1]["facts"] == ["adversary"]  # type: ignore[index]
    assert tree["why"] == {"floor": 80, "first": 1, "last": 3, "exps": [124, 101], "least": 101,
                           "q": False, "unit": "reply", "unit_item": None}  # fmt: skip
    assert [f["fact"] for f in tree["read_facts"]] == ["adversary"]  # type: ignore[attr-defined]
    conjectured = uf(basis="conjectured", unit="part", terms=[100]).tree()
    assert conjectured["why"]["floor"] == 100  # type: ignore[index]
    assert conjectured["why"]["unit_item"] == 2  # type: ignore[index]
    assert needs(conjectured["to_met"])[0] == [("basis", "publisher"), ("unit", "publisher")]


def test_under_100_is_its_own_item_outside_the_why_range() -> None:
    tree = uf(terms=[124, 90], conditions_shown=False).tree()
    assert needs(tree["to_met"])[0] == [("conditions", "publisher"), ("exponent", "publisher")]
    assert tree["why"]["last"] == 1  # type: ignore[index]


def test_met_has_nothing_to_meet() -> None:
    p = uf(terms=[128, 130])
    assert p.step == "green"
    assert p.tree()["to_met"] == []


def test_a_reading_capped_at_mostly_met_needs_only_the_words() -> None:
    """GL-10: a green capped by a reading lists one item, the publisher's words in place of the
    readings, each fact named."""
    props = properties2(trust={"rests_on": fact("transparent", commit=PIN) | {"note": "read"}})
    p = statement_petals(props, HELD, PIN, ONE, None)["no_trusted_party"]
    assert p.step == "amber_upper"
    assert needs(p.tree()["to_met"]) == [[("rests_sentence", "publisher")]]
    assert p.tree()["trust"]["clause"] == "reading"  # type: ignore[index]


def test_a_check_failed_petal_lists_its_repair() -> None:
    p = unforgeable(properties2(), {**HELD, "model": "failed"}, PIN, ONE)
    groups = p.met_groups()
    assert [(g["to"], g["kind"]) for g in groups] == [(None, "repair")]


# ---------------------------------------------------------------- the stored v1.0 board


def test_sources_count_is_the_facts_read() -> None:
    for row in ROWS.values():
        for p in row["glyph"]:
            assert p["sources_count"] == len(p.get("read_facts", [])), p["id"]


def test_v10_to_met_counts_and_actors() -> None:
    """The number of items to Met on each petal of both v1.0 rows, and who acts on each."""
    by = {(s, p["id"]): [b for g in needs(p["to_met"]) for _, b in g]
          for s, row in ROWS.items() for p in row["glyph"]}  # fmt: skip
    pub, us = "publisher", "us"
    assert by[("flashprove", "unforgeable")] == [pub] * 5
    assert by[("flashprove", "weights_hidden")] == [pub] * 3
    assert by[("flashprove", "faithful_model")] == [pub, pub, us]
    assert by[("flashprove", "machine_checked")] == [pub, pub, us]
    assert by[("flashprove", "no_trusted_party")] == [pub]
    assert by[("sash", "unforgeable")] == [pub] * 7
    assert by[("sash", "weights_hidden")] == [pub] * 5
    assert by[("sash", "faithful_model")] == [pub, pub]
    assert by[("sash", "machine_checked")] == [pub, us, pub, pub]
    assert by[("sash", "no_trusted_party")] == [pub]


def test_v10_why_item_range_is_the_cover_items() -> None:
    for system, last, floor in (("flashprove", 3, 80), ("sash", 5, 100)):
        p = petal(system, "unforgeable")
        first = p["to_met"][0]["items"]  # type: ignore[index]
        cover = [i for i, it in enumerate(first, 1) if it["need"] != "exponent"]
        assert p["why"]["first"] == cover[0]  # type: ignore[index]
        assert p["why"]["last"] == cover[-1] == last  # type: ignore[index]
        assert (p["why"]["floor"] == 80) == (p["bound"]["basis"] == "proved")  # type: ignore[index]
        assert p["why"]["floor"] == floor  # type: ignore[index]
    assert petal("flashprove", "unforgeable")["bound"]["q_cross"] == [24, 44]  # type: ignore[index]
    assert petal("sash", "unforgeable")["bound"]["q_cross"] is None  # type: ignore[index]


def test_v10_thresholds_round_from_unrounded_means() -> None:
    """Each threshold to one decimal is the halfway point of its two unrounded means, and the
    halfway point of the two printed means is within 0.05 of the printed threshold."""
    seen = []
    for row in ROWS.values():
        f = petal(row["system"], "faithful_model")["fidelity"]
        for key in ("upper", "green"):
            t = f[key]  # type: ignore[index]
            a, b = (f["controls"][c] for c in t["controls"])  # type: ignore[index]
            assert round(t["value"], 1) == round((a["mean"] + b["mean"]) / 2, 1)
            assert t["display"] == round(t["value"], 1)
            assert abs((a["display"] + b["display"]) / 2 - t["display"]) <= 0.05 + 1e-9
            seen.append(t["display"])
    assert seen == [48.0, 283.0, 55.7, 309.0]


def test_v10_below_own_width_and_trust_clause() -> None:
    assert petal("sash", "faithful_model")["fidelity"]["below_own_width"] is True  # type: ignore[index]
    assert petal("flashprove", "faithful_model")["fidelity"]["below_own_width"] is False  # type: ignore[index]
    for system in ROWS:
        assert petal(system, "no_trusted_party")["trust"]["clause"] == "reading"  # type: ignore[index]
        assert petal(system, "faithful_model")["fidelity"]["policy_cap"] is False  # type: ignore[index]
