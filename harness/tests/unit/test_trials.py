"""Verifier trials (`verifier-trial/1`): the counts and the time range a page prints come from
the calls, and a record that names another commitment or archive than the run records is
refused (AGENTS.md rule 6)."""

import json
import shutil
from pathlib import Path

import pytest

from iproofs.trials import problems, summary

ROOT = Path(__file__).resolve().parents[3]
LEAN = ROOT / "results/v1.0/flashprove/_trials/2026-11-15-lean-verify/trial.json"


def _call(name: str, verdict: str | None, seconds: float, change: object = None,
          run: str = "r-1") -> dict[str, object]:  # fmt: skip
    src = {"run_id": run, "in_results": True, "commitment_id": "a" * 64, "slot": 1}
    return {"name": name, "proof": src, "commitment": src, "change": change, "verdict": verdict,
            "seconds": {"value": seconds}}  # fmt: skip


def test_summary_hand_case() -> None:
    """Three honest calls (accept 10 s, accept 30 s, no verdict 99 s) and one changed call
    (reject 5 s): 2 of 3 accepted, times 10 to 30 s (the call without a verdict and the changed
    call are not in the range), 1 of 1 changed call rejected; one honest call is counted."""
    doc = {"calls": [_call("a", "accept", 10.0, run="counted-1"), _call("b", "accept", 30.0),
                     _call("c", None, 99.0), _call("d", "reject", 5.0, {"kind": "x"})]}  # fmt: skip
    s = summary(doc, counted_runs={"counted-1"})
    assert (s.honest, s.accepted, s.rejected, s.no_verdict) == (3, 2, 0, 1)
    assert (s.counted, s.counted_accepted, s.changed, s.changed_rejected) == (1, 1, 1, 1)
    assert (s.seconds_min, s.seconds_max) == (10.0, 30.0)


def test_stored_lean_trial() -> None:
    """2026-11-15: five kept proofs accepted by the Lean verifier, two of them from counted
    sessions (slots 2 and 3; slot 1's counted proof was not among the inputs), 1,237.3 to
    1,529.9 s, and the call with a commitment ID no session recorded rejected."""
    board = json.loads((ROOT / "releases/v1.0/board.json").read_text())
    (row,) = [r for g in board["rungs"] for r in g["rows"] if r["system"] == "flashprove"]
    s = summary(json.loads(LEAN.read_text()), {x["run_id"] for x in row["sessions"]})
    assert (s.honest, s.accepted, s.no_verdict) == (5, 5, 0)
    assert (s.counted, s.counted_accepted) == (2, 2)
    assert (s.changed, s.changed_rejected) == (1, 1)
    assert (s.seconds_min, s.seconds_max) == (1237.3, 1529.9)
    assert problems(LEAN, ROOT) == []


@pytest.mark.parametrize(
    ("field", "value", "pointer"),
    [("commitment_id", "b" * 64, "/calls/0/proof/commitment_id"),
     ("archive_digest", "sha256:" + "e" * 64, "/calls/0/proof/archive_digest")],
)  # fmt: skip
def test_a_source_the_run_does_not_record_is_refused(
    tmp_path: Path, field: str, value: str, pointer: str
) -> None:
    root = tmp_path / "repo"
    folder = root / LEAN.parent.relative_to(ROOT)
    shutil.copytree(LEAN.parent, folder)
    run = json.loads(LEAN.read_text())["calls"][0]["proof"]["run_id"]
    for name in ("manifest.json", "digests.txt"):
        dst = root / "results/v1.0/flashprove" / run / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "results/v1.0/flashprove" / run / name, dst)
    doc = json.loads((folder / "trial.json").read_text())
    doc["calls"][0]["proof"][field] = value
    (folder / "trial.json").write_text(json.dumps(doc))
    assert pointer in [where for where, _ in problems(folder / "trial.json", root)]


def test_stored_c3_null_twin() -> None:
    """2026-11-15: each kept proof accepted against its own session's commitment (3 of 3) and
    rejected against another session's commitment of the same weights (3 of 3)."""
    path = ROOT / "results/v1.0/flashprove/_trials/2026-11-15-c3-null-twin/trial.json"
    doc = json.loads(path.read_text())
    s = summary(doc)
    assert (s.honest, s.accepted, s.changed, s.changed_rejected) == (3, 3, 3, 3)
    assert {c["change"]["kind"] for c in doc["calls"] if c["change"]} == {
        "other_session_commitment"
    }
    assert problems(path, ROOT) == []


def test_stored_c1_every_position() -> None:
    """2026-11-15: slot 2's kept proof accepted with its claimed reply, then rejected with the
    token changed at each of its 512 reply positions, one call per position."""
    path = ROOT / "results/v1.0/flashprove/_trials/2026-11-15-c1-every-position/trial.json"
    doc = json.loads(path.read_text())
    s = summary(doc)
    assert (s.honest, s.accepted, s.changed, s.changed_rejected) == (1, 1, 512, 512)
    assert sorted(c["change"]["index"] for c in doc["calls"] if c["change"]) == list(range(512))
    assert problems(path, ROOT) == []
