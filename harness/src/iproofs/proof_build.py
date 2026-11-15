"""A proof-build record (`proof-build/1`, RFC-0018 MC-4, MC-4a, MC-5) from what a build job wrote.

`docs/runbooks/proof-build.sh` runs a publisher's own build of its named theorem and writes, into
one folder: `meta.jsonl` (one JSON object per line: what ran, its start, exit code and seconds, or
the setup step that stopped it), `build.log` (the build's whole output), `job.log` (the job's own
lines) and `lean-version.txt`. This module reads that folder and writes nothing; it types no
value: the toolchain comes from the toolchain file the job read at the pin, the axioms from the
build's own line for the theorem, the status from the exit code and the output.

Status (MC-4a): `stopped` when the build reached no verdict on the theorem: the build's own time
limit stopped it (exit code 124), or a signal killed the build or a process it started (an exit
code of 128 or more, or Lake's line for a process it started that was killed). Otherwise `built`
when the exit code is 0, else `failed`. A job whose setup failed never started the build and
gives no record.
"""

import json
import re
from collections.abc import Mapping
from pathlib import Path

from iproofs.errors import ErrorKind, IProofsError

LAST_LINES = 20
TIMEOUT_EXIT = 124  # coreutils `timeout`: the command ran past its limit
SIGNAL_EXIT = 128  # a shell's exit code for a process killed by signal N is 128 + N
# Lake's report of a process it started that a signal ended (the kernel's out-of-memory kill is
# signal 9): "... exited with code 137", "... terminated by signal 9" or the shell's "Killed".
CHILD_KILLED = re.compile(
    r"exited with code (?:1[3-9][0-9]|2[0-5][0-9])\b|terminated by signal|^Killed$", re.M
)


def read_meta(folder: Path) -> dict[str, object]:
    """The job's `meta.jsonl`, its lines merged in order (a later key wins)."""
    path = folder / "meta.jsonl"
    if not path.is_file():
        raise IProofsError(ErrorKind.CONFIG, f"{path}: no meta.jsonl, so no build ran here")
    merged: dict[str, object] = {}
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.strip():
            row = json.loads(line)
            if not isinstance(row, dict):
                raise IProofsError(ErrorKind.CONFIG, f"{path}:{n}: not a JSON object")
            merged.update(row)
    return merged


def axioms_of(log: str, theorem: str) -> list[str] | None:
    """The axioms the build reports for exactly `theorem` (Lean's `#print axioms` line
    "'NAME' depends on axioms: [a, b]", which may wrap over lines), None when it has no line."""
    m = re.search(re.escape(f"'{theorem}' depends on axioms:") + r"\s*\[([^\]]*)\]", log)
    if m is None:
        return None
    return [a.strip() for a in m.group(1).replace("\n", " ").split(",") if a.strip()]


def toolchain_of(spelled: str) -> dict[str, str]:
    """`leanprover/lean4:v4.29.1` as the toolchain file spells it: name and version."""
    name, sep, version = spelled.strip().partition(":")
    if not sep or not name or not version:
        raise IProofsError(ErrorKind.CONFIG, f"toolchain {spelled!r} is not NAME:VERSION")
    return {"name": name, "version": version}


def _last_lines(text: str) -> list[str]:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    return lines[-LAST_LINES:]


def status_of(exit_code: int, log: str) -> tuple[str, dict[str, str] | None]:
    """`built`, `failed` or `stopped` and its stop (MC-4a), from the exit code and the output."""
    if exit_code == TIMEOUT_EXIT:
        return "stopped", {"cause": "timeout", "detail": "the build's own time limit (exit 124)"}
    if exit_code >= SIGNAL_EXIT:
        return "stopped", {
            "cause": "signal",
            "detail": f"killed by signal {exit_code - SIGNAL_EXIT}",
        }
    if exit_code != 0:
        killed = CHILD_KILLED.search(log)
        if killed:
            detail = f"a process the build started: {killed.group(0)!r}"
            return "stopped", {"cause": "signal", "detail": detail}
        return "failed", None
    return "built", None


def build_record(folder: Path, system: str, formal: Mapping[str, object]) -> dict[str, object]:
    """The `proof-build/1` record of the build in `folder`, for `system`'s named theorem
    (`formal.theorem`, `formal.theorem_url` of its properties/2 file). A job whose setup failed
    never started the build: it is no build, and this refuses it (its folder keeps its log)."""
    meta = read_meta(folder)
    if meta.get("stopped") == "setup":
        raise IProofsError(ErrorKind.CONFIG, f"{folder}: setup stopped at step "
                           f"{meta.get('step')}; the build never started, so there is no build "
                           "to record")  # fmt: skip
    theorem, url = str(formal.get("theorem") or ""), str(formal.get("theorem_url") or "")
    if not theorem or not url:
        raise IProofsError(ErrorKind.CONFIG, f"{system}: properties names no theorem and link")
    for key in ("image", "repo", "commit", "toolchain_file", "target", "timeout_s", "started_at",
                "seconds", "exit_code"):  # fmt: skip
        if key not in meta:
            raise IProofsError(ErrorKind.CONFIG, f"{folder}/meta.jsonl has no {key}")
    exit_code = meta["exit_code"]
    if not isinstance(exit_code, int):
        raise IProofsError(ErrorKind.CONFIG, "meta.jsonl's exit_code is not an integer")
    log = (folder / "build.log").read_text(errors="replace")
    status, stop = status_of(exit_code, log)
    found = axioms_of(log, theorem)
    if status == "built" and found is None:
        raise IProofsError(ErrorKind.CONFIG, f"the build exited 0 and printed no axioms line for "
                           f"{theorem}: read build.log before recording anything")  # fmt: skip
    image = str(meta["image"]).rpartition("@")[2]
    argv = ["env", "LEAN_ABORT_ON_PANIC=1", "timeout", "-k", "60", str(meta["timeout_s"]),
            "lake", "build", str(meta["target"])]  # fmt: skip
    record: dict[str, object] = {
        "schema": "proof-build/1",
        "system": system,
        "upstream": {"repo": meta["repo"], "commit": meta["commit"]},
        "theorem": {"name": theorem, "url": url},
        "toolchain": {**toolchain_of(str(meta["toolchain_file"])), "image": image},
        "argv": argv,
        "started_at": str(meta["started_at"]),
        "seconds": float(str(meta["seconds"])),
        "exit_code": exit_code,
        "status": status,
        "last_lines": _last_lines(log),
        "axioms_reported": found or [],
    }
    if stop is not None:
        record["stop"] = stop
    return record
