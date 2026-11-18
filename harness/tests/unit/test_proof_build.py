"""The proof-build record from a build job's folder (RFC-0018 MC-4, MC-4a, MC-5)."""

import json
from pathlib import Path

import pytest
import yaml

from iproofs.errors import IProofsError
from iproofs.glyph import machine_checked
from iproofs.proof_build import BUILDER_HOME, _last_lines, build_record, publisher_command
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
info: ././Johnson/Goal/Skeleton/SoundOfVerifyAt.lean:83:0: '{NAME}' depends on axioms:
[propext, Classical.choice,
 Quot.sound]
info: ././Johnson/Goal/Skeleton/SoundOfVerifyAt.lean:84:0: \
'VerifierAndGoals.AtTheName.nearestSound_of_verify' depends on axioms: [propext, sorryAx]
Build completed successfully (16057 jobs).
"""


def folder(tmp: Path, exit_code: int, log: str = LOG, seconds: int = 5400) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    rows = [
        {"started_at": "2026-11-15T21:30:00Z", "image": f"docker.io/library/ubuntu@{IMAGE}",
         "repo": "anthropics/FlashProve", "commit": PIN, "target": TARGET, "timeout_s": 25200,
         "toolchain_file": "leanprover/lean4:v4.29.1"},
        {"exit_code": exit_code, "seconds": seconds},
    ]  # fmt: skip
    (tmp / "meta.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp / "build.log").write_text(log)
    (tmp / "lean-version.txt").write_text(LEAN)
    return tmp


LEAN = "Lean (version 4.29.1, x86_64-unknown-linux-gnu, commit f72c35b, Release)\n"


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


PANIC = "PANIC at Lean.Expr.bindingBody! Lean.Expr:1:0: binding expected\nbacktrace:\n"
CHILD = "error: ././Johnson/X.lean: Lean exited with code "


@pytest.mark.parametrize(
    ("code", "log", "seconds", "status", "cause"),
    [
        (124, "partial\n", 25200, "stopped", "timeout"),
        (137, "partial\n", 25260, "stopped", "timeout"),  # `timeout -k 60` sent KILL at the limit
        (137, "partial\n", 3000, "stopped", "signal"),  # killed below the limit: out of memory
        (1, CHILD + "137\n", 3000, "stopped", "signal"),
        (1, "error: ././Johnson/X.lean:3:0: unknown identifier 'foo'\n", 3000, "failed", None),
        (1, PANIC + CHILD + "134\n", 3000, "failed", None),  # LEAN_ABORT_ON_PANIC: Lean's verdict
        (1, "Stack overflow detected. Aborting.\n" + CHILD + "134\n", 3000, "failed", None),
        (134, "partial\n" + PANIC, 3000, "failed", None),
        (1, PANIC + CHILD + "137\n", 3000, "failed", None),  # a kill after a panic: still failed
    ],
)
def test_status(
    tmp_path: Path, code: int, log: str, seconds: int, status: str, cause: str | None
) -> None:
    rec = build_record(folder(tmp_path, code, log, seconds), "flashprove", FORMAL)
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


def test_another_lean_than_the_toolchain_file_is_refused(tmp_path: Path) -> None:
    (folder(tmp_path, 0) / "lean-version.txt").write_text("Lean (version 4.30.0, x86_64)\n")
    with pytest.raises(IProofsError, match=r"does not show Lean v4\.29\.1"):
        build_record(tmp_path, "flashprove", FORMAL)


# ---------------------------------------------------------------- the full check (check.py)

ARGV = ["timeout", "-k", "60", "23400", "python3", "-B", "scripts/check.py", "--wide-jobs", "24"]
PASSED = (
    "All steps passed: tree, words, imports, build (kernel replay, audit). This script runs no "
    "mutation tests and no second, independent proof checker."
)
AUDIT = f"   AUDIT {NAME}: general; 3 binders after unfolding; axioms [propext, Classical.choice, Quot.sound]; reach 12\n"  # noqa: E501
LEAN_LINE = (
    f"info: x.lean:83:0: '{NAME}' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
)


def check_folder(
    tmp: Path, code: int, out: str, kept: str = LEAN_LINE, seconds: int = 16000
) -> Path:
    tmp.mkdir(parents=True, exist_ok=True)
    rows = [
        {"started_at": "2026-11-16T00:00:00Z", "image": f"docker.io/library/ubuntu@{IMAGE}",
         "repo": "anthropics/FlashProve", "commit": PIN, "timeout_s": 23400, "mode": "check",
         "toolchain_file": "leanprover/lean4:v4.29.1", "argv": ARGV},
        {"exit_code": code, "seconds": seconds},
    ]  # fmt: skip
    (tmp / "meta.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    (tmp / "build.log").write_text(out)
    (tmp / "lean-version.txt").write_text(LEAN)
    logs = tmp / "check" / "home" / "lean-check-x"
    logs.mkdir(parents=True)
    (logs / "build.log").write_text(kept)
    (logs / "panic-control.log").write_text("PANIC at the control, by design\n")
    return tmp


def test_full_check_built_reads_the_audit_axioms_and_keeps_the_job_argv(tmp_path: Path) -> None:
    rec = build_record(check_folder(tmp_path, 0, AUDIT + PASSED + "\n"), "flashprove", FORMAL)
    assert (rec["status"], rec["argv"]) == ("built", ARGV)
    assert rec["axioms_reported"] == ["propext", "Classical.choice", "Quot.sound"]
    assert SchemaRegistry.from_tree(ROOT / "schema").errors("proof-build/1", rec) == []


@pytest.mark.parametrize(
    ("code", "out", "kept", "seconds", "status", "cause"),
    [
        (1, "   REPLAY FAILED (exit 1): x\nCheck failed: build\n", LEAN_LINE, 9000, "failed", None),
        (
            1,
            "   PANIC: lines in the output of y\nCheck failed: build, replay, audit\n",
            "",
            9000,
            "failed",
            None,
        ),
        (
            1,
            "Check failed: build, replay, audit\n",
            "error: Lean exited with code 134\n",
            9000,
            "failed",
            None,
        ),
        (
            1,
            '   "lake build" from scratch: exit 137\nCheck failed: build, replay, audit\n',
            "",
            9000,
            "stopped",
            "signal",
        ),
        (
            1,
            "   x: exit 137\nCheck failed: words, build\n",
            "",
            9000,
            "failed",
            None,
        ),  # a words failure is ours to show
        (
            1,
            "   TOO LITTLE MEMORY: the build\n   FAILED: build not run: too little memory is free\n"
            "   FAILED: words\nCheck failed: words, build, replay, audit\n",
            "",
            9000,
            "failed",
            None,
        ),
        (
            1,
            "   REPLAY FAILED (exit 1): x\n   TOO LITTLE MEMORY: the audit\n"
            "Check failed: replay, audit\n",
            "",
            9000,
            "failed",
            None,
        ),
        (124, "partial\n", "", 23400, "stopped", "timeout"),
        (137, "partial\n", "", 23460, "stopped", "timeout"),
    ],
)
def test_full_check_status(
    tmp_path: Path, code: int, out: str, kept: str, seconds: int, status: str, cause: str | None
) -> None:
    rec = build_record(check_folder(tmp_path, code, out, kept, seconds), "flashprove", FORMAL)
    assert rec["status"] == status
    stop = rec.get("stop")
    assert (stop.get("cause") if isinstance(stop, dict) else None) == cause


@pytest.mark.parametrize(
    ("code", "out"),
    [
        (3, "  - NOT RUN: the listing (not written)\nPassed so far, and not the full check\n"),
        (1, "   TOO LITTLE MEMORY: the build\nCheck failed: build\n"),
        (1, "check.py: no step was run, and nothing was built\n"),
        (
            1,
            "   FAILED: build not run: too little memory is free\n"
            "Check failed: build, replay, audit\n",
        ),
        (2, "check.py: --jobs must be a whole number. Nothing was checked.\n"),
        (0, "Partial run passed (tree): only these steps were run\n"),
    ],
)
def test_full_check_without_a_verdict_is_no_record(tmp_path: Path, code: int, out: str) -> None:
    with pytest.raises(IProofsError):
        build_record(check_folder(tmp_path, code, out), "flashprove", FORMAL)


def test_full_check_audit_and_lean_disagreeing_is_refused(tmp_path: Path) -> None:
    kept = f"info: x.lean:83:0: '{NAME}' depends on axioms: [propext]\n"
    with pytest.raises(IProofsError, match="read the logs"):
        build_record(check_folder(tmp_path, 0, AUDIT + PASSED + "\n", kept), "flashprove", FORMAL)


def test_publisher_command_drops_our_wrapper() -> None:
    targeted = [
        "env",
        "LEAN_ABORT_ON_PANIC=1",
        "timeout",
        "-k",
        "60",
        "25200",
        "lake",
        "build",
        TARGET,
    ]
    assert publisher_command(targeted) == ["LEAN_ABORT_ON_PANIC=1", "lake", "build", TARGET]
    assert publisher_command(ARGV) == ["python3", "-B", "scripts/check.py", "--wide-jobs", "24"]


def test_full_check_records_the_lean_threads_it_ran_with(tmp_path: Path) -> None:
    folder_ = check_folder(tmp_path, 0, AUDIT + PASSED + "\n")
    with (folder_ / "meta.jsonl").open("a") as f:
        f.write(json.dumps({"lean_num_threads": "64"}) + "\n")
    rec = build_record(folder_, "flashprove", FORMAL)
    assert rec["argv"] == ["env", "LEAN_NUM_THREADS=64", *ARGV]
    assert publisher_command(rec["argv"])[:2] == ["LEAN_NUM_THREADS=64", "python3"]


# ---------------------------------------------------------------- which record stands (Q43)


def _stored(tmp: Path, record: dict[str, object]) -> Path:
    out = tmp / "results/v1.0/proof-build/flashprove/proof-build.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record))
    return out


def test_replace_rules(tmp_path: Path) -> None:
    from iproofs.commands.proof_build import replaces  # noqa: PLC0415

    targeted = build_record(folder(tmp_path / "t", 0), "flashprove", FORMAL)
    check = build_record(
        check_folder(tmp_path / "c", 0, AUDIT + PASSED + "\n"), "flashprove", FORMAL
    )
    stopped = build_record(
        check_folder(tmp_path / "s", 124, "partial\n", "", 23400), "flashprove", FORMAL
    )
    out = tmp_path / "repo" / "results/v1.0/proof-build/flashprove/proof-build.json"
    replaces(out, stopped, False, tmp_path / "repo")  # none stored: any build is written
    out = _stored(tmp_path / "repo", targeted)
    before = out.read_bytes()
    with pytest.raises(IProofsError, match="replaces no record"):
        replaces(out, stopped, True, tmp_path / "repo")
    with pytest.raises(IProofsError, match="give --replace"):
        replaces(out, check, False, tmp_path / "repo")
    with pytest.raises(IProofsError, match="only the publisher's full check"):
        replaces(out, targeted, True, tmp_path / "repo")
    replaces(out, check, True, tmp_path / "repo")  # a full check over a targeted build
    out.write_text(json.dumps(check))
    with pytest.raises(IProofsError, match="only the publisher's full check"):
        replaces(out, check, True, tmp_path / "repo")  # never a second full check
    assert before != out.read_bytes()


def test_last_lines_print_the_jobs_home_as_tilde() -> None:
    """check.py prints its scratch paths under the job user's home; the record must pass SEC-10."""
    out = "  - the logs are in " + BUILDER_HOME + "scratch/lean-check-fd954dd1\nAll steps passed\n"
    lines = _last_lines(out)
    assert lines == ["  - the logs are in ~/scratch/lean-check-fd954dd1", "All steps passed"]
