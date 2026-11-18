"""Verifier trials (`verifier-trial/1`, RFC-0008 §Verifier trials): verify calls on stored proofs
that no counted session or control suite makes. They gate nothing; this module only checks a
record against the run records it names and counts what it shows, for a page to print."""

import hashlib
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from iproofs.schema import parse_tree

TRIAL_GLOB = "results/*/*/_trials/*/trial.json"


@dataclass(frozen=True, slots=True)
class TrialSummary:
    """The honest calls of a trial (no `change`) and the changed ones, counted. `seconds_min`
    and `seconds_max` span the honest calls that returned a verdict (None when none did);
    `counted` is the number of honest calls whose proof comes from a counted session."""

    honest: int
    accepted: int
    rejected: int
    no_verdict: int
    counted: int
    counted_accepted: int
    changed: int
    changed_rejected: int
    seconds_min: float | None
    seconds_max: float | None


def summary(doc: Mapping[str, Any], counted_runs: Collection[str] = ()) -> TrialSummary:
    calls: Sequence[Mapping[str, Any]] = doc["calls"]
    honest = [c for c in calls if c["change"] is None]
    changed = [c for c in calls if c["change"] is not None]
    timed = [float(c["seconds"]["value"]) for c in honest
             if c["verdict"] is not None and c["seconds"]["value"] is not None]  # fmt: skip
    counted = [
        c for c in honest if c["proof"]["in_results"] and c["proof"]["run_id"] in counted_runs
    ]
    return TrialSummary(
        honest=len(honest),
        accepted=sum(c["verdict"] == "accept" for c in honest),
        rejected=sum(c["verdict"] == "reject" for c in honest),
        no_verdict=sum(c["verdict"] is None for c in honest),
        counted=len(counted),
        counted_accepted=sum(c["verdict"] == "accept" for c in counted),
        changed=len(changed),
        changed_rejected=sum(c["verdict"] == "reject" for c in changed),
        seconds_min=min(timed) if timed else None,
        seconds_max=max(timed) if timed else None,
    )


def _archives(run_dir: Path) -> dict[str, str]:
    """`archive/<proof id>.tar` digests of a run's digests.txt, by proof id."""
    path = run_dir / "digests.txt"
    if not path.is_file():
        return {}
    out = {}
    for line in path.read_text().splitlines():
        name, _, digest = line.partition("\t")
        if name.startswith("archive/") and name.endswith(".tar"):
            out[name.removeprefix("archive/").removesuffix(".tar")] = digest
    return out


def problems(path: Path, root: Path) -> list[tuple[str, str]]:
    """(pointer, message) for each way a trial record disagrees with what it names: a source
    `in_results` whose run directory is missing, whose manifest records another commitment ID
    (AGENTS.md rule 6) or whose digests.txt records another archive digest for the proof; a
    raw file that is missing; a script whose sha256 is not `script_digest`."""
    doc: dict[str, Any] = parse_tree(path)
    folder = path.parent
    found: list[tuple[str, str]] = []
    runs = root / "results" / str(doc["release"]) / str(doc["system"])
    script = folder / str(doc["runner"]["script"])
    if not script.is_file():
        found.append(("/runner/script", f"{doc['runner']['script']} is missing"))
    elif (
        "sha256:" + hashlib.sha256(script.read_bytes()).hexdigest()
        != doc["runner"]["script_digest"]
    ):
        found.append(("/runner/script_digest", "is not the sha256 of the script"))
    for i, call in enumerate(doc["calls"]):
        for side in ("proof", "commitment"):
            src = call[side]
            where = f"/calls/{i}/{side}"
            if not src["in_results"]:
                continue
            run_dir = runs / str(src["run_id"])
            manifest = run_dir / "manifest.json"
            if not manifest.is_file():
                found.append((where, f"run {src['run_id']} is not in {runs.relative_to(root)}"))
                continue
            record: dict[str, Any] = parse_tree(manifest)
            recorded = record["commitment"]["commitment_id"]
            if recorded != src["commitment_id"]:
                found.append((f"{where}/commitment_id", f"the run's manifest records {recorded}"))
            if side == "proof" and "archive_digest" in src:
                kept = _archives(run_dir).get(str(src.get("proof_id")))
                if kept != src["archive_digest"]:
                    found.append((f"{where}/archive_digest",
                                  f"digests.txt of {src['run_id']} records {kept}"))  # fmt: skip
        for raw in call["raw"]:
            if not (folder / raw).is_file():
                found.append((f"/calls/{i}/raw", f"{raw} is missing"))
    return found
