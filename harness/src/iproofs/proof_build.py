"""A proof-build record (`proof-build/1`, RFC-0018 MC-4, MC-4a, MC-5) from what a build job wrote.

`docs/runbooks/proof-build.sh` runs one of a publisher's own commands for its named theorem and
writes, into one folder: `meta.jsonl` (one JSON object per line: what ran, its start, exit code and
seconds, or the setup step that stopped it), `build.log` (the command's whole output), `job.log`
(the job's own lines), `lean-version.txt` (what `lean --version` printed where the build ran) and,
for the full check, `check/` (the logs check.py wrote in its scratch folder). This module reads that
folder and writes nothing; it types no value: the toolchain comes from the toolchain file the job
read at the pin, checked against the Lean that ran, the axioms from Lean's own lines for the
theorem, the status from the exit code and the output.

Status (MC-4, MC-4a): `failed` when Lean itself gave up, whatever else the log holds: a panic
(the publisher's LEAN_ABORT_ON_PANIC=1 makes it abort, exit 134, lean/scripts/check.py L1280 at
the pin), a stack overflow or another abort. `stopped` when the build reached no verdict because
we stopped it: its own time limit (exit 124, or 137 at or past the limit when `timeout -k` sends
KILL), or SIGKILL or SIGTERM to the build or a process it started (137 or 143, the kernel's
out-of-memory kill among them). Otherwise `built` at exit 0, else `failed`. A job whose setup
failed never started the build and gives no record; nor does a full check that reached no verdict
on the library for a reason of its own (too little memory at a step's start, no Lake call, other
Lake files, exit 2 or 3): this refuses those folders, which keep their logs.
"""

import json
import re
from collections.abc import Mapping
from pathlib import Path

from iproofs.errors import ErrorKind, IProofsError

LAST_LINES = 20
TIMEOUT_EXIT = 124  # coreutils `timeout`: the command ran past its limit
KILLED_EXITS = {137: "SIGKILL", 143: "SIGTERM"}  # 128 + 9, 128 + 15: we, or the kernel, ended it
# Lake's line for a process it started that SIGKILL or SIGTERM ended (the out-of-memory kill is
# SIGKILL): "... exited with code 137", "... terminated by signal 9" or the shell's "Killed".
CHILD_KILLED = re.compile(
    r"exited with code (?:137|143)\b|terminated by signal (?:9|15)\b|^Killed$", re.M
)
# Lean gave up on its own: a panic (aborts under LEAN_ABORT_ON_PANIC=1), a stack overflow, or an
# abort (SIGABRT, 134) or crash (SIGSEGV, 139) of a process the build started.
LEAN_GAVE_UP = re.compile(
    r"^(?:INTERNAL )?PANIC\b|Stack overflow detected|exited with code (?:134|139)\b"
    r"|terminated by signal (?:6|11)\b",
    re.M,
)

# The full check's own lines at the pin (lean/scripts/check.py L43-L61, L913-L936, L1259-L1274,
# L1535, L3734-L3772, L3971-L3973, L4137-L4220; lean/CHECKING.md L292-L298).
CHECK_PASSED = "All steps passed: tree, words, imports, build (kernel replay, audit)."
CHECK_FAILED = re.compile(r"Check failed: ([a-z]+(?:, [a-z]+)*)")
LAKE_STEPS = frozenset({"build", "replay", "audit"})  # the steps that start Lake
CHECK_NO_VERDICT = re.compile(
    r"no step was run, and nothing was built"
    r"|^Traceback \(most recent call last\):"
    r"|^   TOO LITTLE MEMORY: |^   THE CONTROL FAILED: "
    r"| not run: (?:another account could|Lake is not called|too little memory)"
    r"|^The Lake files are not the ones that this check\.py expects",
    re.M,
)
CHECK_GAVE_UP = re.compile(
    r"^   PANIC: lines in the output of |^   Lean aborted \(exit status 134\) in "
    r"|\bexit (?:134|139|-6|-11)\b|Stack overflow detected",
    re.M,
)
CHECK_KILLED = re.compile(r"\bexit (?:137|143|-9|-15)\b")


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


def _names(listed: str) -> list[str]:
    return [a.strip() for a in listed.replace("\n", " ").split(",") if a.strip()]


def axioms_of(log: str, theorem: str) -> list[str] | None:
    """The axioms Lean's `#print axioms` reports for exactly `theorem` ("'NAME' depends on
    axioms: [a, b]", which may wrap over lines), None when the log has no such line."""
    m = re.search(re.escape(f"'{theorem}' depends on axioms:") + r"\s*\[([^\]]*)\]", log)
    return None if m is None else _names(m.group(1))


def audit_axioms_of(log: str, theorem: str) -> list[str] | None:
    """The axioms the full check's audit reports for exactly `theorem`: its line
    "   AUDIT NAME: ...; axioms [a, b]; ..." (check.py L3971-L3973, Audit.lean.in L1230, L1361),
    None when the log has none. Two lines for the name are refused."""
    lines = re.findall(r"^   AUDIT " + re.escape(theorem) + r": (.*)$", log, re.M)
    if len(lines) > 1:
        raise IProofsError(ErrorKind.CONFIG, f"the audit printed {len(lines)} lines for {theorem}")
    if not lines:
        return None
    m = re.search(r"(?:^|; )axioms \[([^\]]*)\]", lines[0])
    return None if m is None else _names(m.group(1))


def toolchain_of(spelled: str) -> dict[str, str]:
    """`leanprover/lean4:v4.29.1` as the toolchain file spells it: name and version."""
    name, sep, version = spelled.strip().partition(":")
    if not sep or not name or not version:
        raise IProofsError(ErrorKind.CONFIG, f"toolchain {spelled!r} is not NAME:VERSION")
    return {"name": name, "version": version}


def publisher_command(argv: list[str]) -> list[str]:
    """The publisher's command inside our wrapper: a leading `env NAME=value ...` and our time
    limit `timeout -k N S` dropped (docs/runbooks/proof-build.sh writes both)."""
    rest = list(argv)
    if rest[:1] == ["env"]:
        rest = rest[1:]
        while rest and "=" in rest[0]:
            rest = rest[1:]
    if rest[:2] == ["timeout", "-k"] and len(rest) > 4:
        rest = rest[4:]
    return rest


def record_path(release: str, system: str) -> str:
    """Where a system's proof-build record is stored, relative to the repository (MC-5)."""
    return f"results/{release}/proof-build/{system}/proof-build.json"


def _last_lines(text: str) -> list[str]:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    return lines[-LAST_LINES:]


def _stop(exit_code: int, seconds: float, limit: float) -> dict[str, str] | None:
    """Our time limit or a SIGKILL or SIGTERM to the whole command (MC-4a), from its exit code."""
    if exit_code == TIMEOUT_EXIT or (exit_code in KILLED_EXITS and seconds >= limit):
        detail = f"the build's own time limit of {limit:.0f} s (exit {exit_code})"
        return {"cause": "timeout", "detail": detail}
    if exit_code in KILLED_EXITS:
        return {"cause": "signal", "detail": f"{KILLED_EXITS[exit_code]} (exit {exit_code})"}
    return None


def status_of(
    exit_code: int, log: str, seconds: float, limit: float
) -> tuple[str, dict[str, str] | None]:
    """The targeted build's `built`, `failed` or `stopped` and its stop (MC-4, MC-4a), from the
    exit code, the output, the build's seconds and its own time limit."""
    if exit_code == 0:
        return "built", None
    if LEAN_GAVE_UP.search(log):  # Lean's own verdict, even if a kill came after it
        return "failed", None
    stop = _stop(exit_code, seconds, limit)
    if stop is not None:
        return "stopped", stop
    killed = CHILD_KILLED.search(log)
    if killed:
        detail = f"a process the build started: {killed.group(0)!r}"
        return "stopped", {"cause": "signal", "detail": detail}
    return "failed", None


def kept_logs(folder: Path) -> str:
    """The logs of the calls the full check finished, as the job copied them into `check/` (check.py
    writes a call's log when it returns, L1324); not panic-control.log, whose panic is its control
    (L1526)."""
    base = folder / "check"
    if not base.is_dir():
        return ""
    parts = [p.read_text(errors="replace") for p in sorted(base.rglob("*.log"))
             if p.name != "panic-control.log"]  # fmt: skip
    return "\n".join(parts)


def check_status_of(
    exit_code: int, out: str, kept: str, seconds: float, limit: float
) -> tuple[str, dict[str, str] | None]:
    """The full check's `built`, `failed` or `stopped` (MC-4, MC-4a), from its exit code, its own
    output and the logs it kept. Raises where it reached no verdict on the library."""
    lines = [ln for ln in out.splitlines() if ln.strip()]
    last = lines[-1] if lines else ""
    if exit_code == 0:
        if not last.startswith(CHECK_PASSED):
            raise IProofsError(ErrorKind.CONFIG, f"check.py exited 0 with last line {last!r}")
        return "built", None
    if CHECK_GAVE_UP.search(out) or LEAN_GAVE_UP.search(kept):
        return "failed", None
    stop = _stop(exit_code, seconds, limit)
    if stop is not None:
        return "stopped", stop
    if CHECK_NO_VERDICT.search(out) or exit_code != 1:
        raise IProofsError(ErrorKind.CONFIG, f"check.py exited {exit_code} with no verdict on the "
                           f"library ({last!r}): read build.log; no record is written")  # fmt: skip
    failed = CHECK_FAILED.search(last)
    if failed is None:
        raise IProofsError(ErrorKind.CONFIG, f"check.py exited 1 with last line {last!r}")
    steps = set(failed.group(1).split(", "))
    killed = CHECK_KILLED.search(out) or CHILD_KILLED.search(out) or CHILD_KILLED.search(kept)
    if killed and steps <= LAKE_STEPS:
        detail = f"a process check.py started: {killed.group(0)!r}"
        return "stopped", {"cause": "signal", "detail": detail}
    return "failed", None


def _lean_ran(folder: Path, version: str) -> None:
    """The Lean that ran is the toolchain file's version (AGENTS.md rule 11)."""
    path = folder / "lean-version.txt"
    text = path.read_text(errors="replace") if path.is_file() else ""
    if f"version {version.removeprefix('v')}," not in text:
        raise IProofsError(ErrorKind.CONFIG, f"{path} does not show Lean {version}: {text[:120]!r}")


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
    check = meta.get("mode") == "check"
    keys = ["image", "repo", "commit", "toolchain_file", "timeout_s", "started_at", "seconds",
            "exit_code", "argv" if check else "target"]  # fmt: skip
    for key in keys:
        if key not in meta:
            raise IProofsError(ErrorKind.CONFIG, f"{folder}/meta.jsonl has no {key}")
    exit_code = meta["exit_code"]
    if not isinstance(exit_code, int):
        raise IProofsError(ErrorKind.CONFIG, "meta.jsonl's exit_code is not an integer")
    toolchain = toolchain_of(str(meta["toolchain_file"]))
    _lean_ran(folder, toolchain["version"])
    log = (folder / "build.log").read_text(errors="replace")
    seconds, limit = float(str(meta["seconds"])), float(str(meta["timeout_s"]))
    if check:
        kept = kept_logs(folder)
        status, stop = check_status_of(exit_code, log, kept, seconds, limit)
        found = audit_axioms_of(log, theorem)
        lean_says = axioms_of(kept, theorem)
        if found is not None and lean_says is not None and set(found) != set(lean_says):
            raise IProofsError(ErrorKind.CONFIG, f"the audit reports axioms {found} and Lean's own "
                               f"line {lean_says} for {theorem}: read the logs")  # fmt: skip
        argv_raw = meta["argv"]
        if not isinstance(argv_raw, list) or not argv_raw:
            raise IProofsError(ErrorKind.CONFIG, "meta.jsonl's argv is not a list")
        argv = [str(a) for a in argv_raw]
    else:
        status, stop = status_of(exit_code, log, seconds, limit)
        found = axioms_of(log, theorem)
        argv = ["env", "LEAN_ABORT_ON_PANIC=1", "timeout", "-k", "60", str(meta["timeout_s"]),
                "lake", "build", str(meta["target"])]  # fmt: skip
    if status == "built" and found is None:
        raise IProofsError(ErrorKind.CONFIG, f"the build exited 0 and printed no axioms line for "
                           f"{theorem}: read build.log before recording anything")  # fmt: skip
    record: dict[str, object] = {
        "schema": "proof-build/1",
        "system": system,
        "upstream": {"repo": meta["repo"], "commit": meta["commit"]},
        "theorem": {"name": theorem, "url": url},
        "toolchain": {**toolchain, "image": str(meta["image"]).rpartition("@")[2]},
        "argv": argv,
        "started_at": str(meta["started_at"]),
        "seconds": seconds,
        "exit_code": exit_code,
        "status": status,
        "last_lines": _last_lines(log),
        "axioms_reported": found or [],
    }
    if stop is not None:
        record["stop"] = stop
    return record
