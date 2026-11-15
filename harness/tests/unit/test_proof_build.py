"""The proof-build record from a build job's folder (RFC-0018 MC-4, MC-4a, MC-5)."""

import json
from pathlib import Path

import pytest
import yaml

from iproofs.errors import IProofsError
from iproofs.glyph import machine_checked
from iproofs.proof_build import build_record
from iproofs.schema import SchemaRegistry

ROOT = Path(__file__).resolve().parents[3]
PIN = "9e2bdd8ff5bf9c62f18263d7dac189b0400b260c"
NAME = "VerifierAndGoals.AtTheName.sound_of_verify_at"
TARGET = "Johnson.Goal.Skeleton.SoundOfVerifyAt"
IMAGE = "sha256:" + "f" * 64
FORMAL = {
    "theorem": NAME,
    "theorem_url": f"https://github.com/anthropics/FlashProve/blob/{PIN}/x.lean#L1",
}
# Lean prints one `#print axioms` line per theorem; the file holds a second theorem whose name
# ends the same way, and a line may wrap (lean/THEOREM.md L455-L456 at the pin).
LOG = f"""✔ [16056/16057] Built Johnson.Goal.Skeleton.Other
info: SoundOfVerifyAt.lean, line 83: '{NAME}' depends on axioms:
[propext, Classical.choice,
 Quot.sound]
info: SoundOfVerifyAt.lean, line 84: \
'VerifierAndGoals.AtTheName.nearestSound_of_verify' depends on axioms: [propext, sorryAx]
Build completed successfully (16057 jobs).
"""


def folder(tmp: Path, exit_code: int, log: str = LOG) -> Path:
    rows = [
        {"started_at": "2026-11-15T21:30:00Z", "image": f"docker.io/library/ubuntu@{IMAGE}",
         "repo": "anthropics/FlashProve", "commit": PIN, "target": TARGET, "timeout_s": 25200,
         "toolchain_file": "leanprover/lean4:v4.29.1"},
        {"exit_code": exit_code, "seconds": 5400},
    ]  # fmt: skip
    (tmp / "meta.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp / "build.log").write_text(log)
    return tmp


def test_built_record_reads_the_theorem_own_axioms_and_the_toolchain_file(tmp_path: Path) -> None:
    rec = build_record(folder(tmp_path, 0), "flashprove", FORMAL)
    assert rec["status"] == "built"
    assert rec["axioms_reported"] == ["propext", "Classical.choice", "Quot.sound"]
    assert rec["toolchain"] == {
        "name": "leanprover/lean4",
        "version": "v4.29.1",
        "image": "sha256:" + "f" * 64,
    }
    assert SchemaRegistry.from_tree(ROOT / "schema").errors("proof-build/1", rec) == []


@pytest.mark.parametrize(
    ("code", "log", "status", "cause"),
    [
        (124, "partial\n", "stopped", "timeout"),
        (137, "partial\n", "stopped", "signal"),
        (1, "error: external command 'lean' exited with code 137\n", "stopped", "signal"),
        (1, "error: X.lean, line 3: unknown identifier 'foo'\n", "failed", None),
    ],
)
def test_status(tmp_path: Path, code: int, log: str, status: str, cause: str | None) -> None:
    rec = build_record(folder(tmp_path, code, log), "flashprove", FORMAL)
    assert rec["status"] == status
    stop = rec.get("stop")
    assert (stop.get("cause") if isinstance(stop, dict) else None) == cause
    assert SchemaRegistry.from_tree(ROOT / "schema").errors("proof-build/1", rec) == []


def test_exit_zero_without_the_axioms_line_is_refused(tmp_path: Path) -> None:
    with pytest.raises(IProofsError, match="no axioms line"):
        build_record(folder(tmp_path, 0, "Build completed successfully.\n"), "flashprove", FORMAL)


def test_setup_stop_is_no_build(tmp_path: Path) -> None:
    (tmp_path / "meta.jsonl").write_text(
        json.dumps({"stopped": "setup", "step": "cache-get"}) + "\n"
    )
    with pytest.raises(IProofsError, match="never started"):
        build_record(tmp_path, "flashprove", FORMAL)


def test_the_flashprove_record_draws_the_stated_step(tmp_path: Path) -> None:
    """End to end on the real properties file: a matching built record shows amber in part."""
    props = yaml.safe_load((ROOT / "systems/flashprove/properties.yaml").read_text())
    formal = props["petals"]["machine_checked"]["formal"]
    rec = build_record(folder(tmp_path, 0), "flashprove", formal)
    petal = machine_checked(props, {}, PIN, rec)
    assert (petal.step, petal.cause) == ("amber_upper", None)
