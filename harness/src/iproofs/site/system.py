"""What a system page prints beside the board's figures, from the records they were taken on.

RFC-0018 SI-3 (amended 2026-11-15): the Statement block (what the verifier the row runs takes
from the harness record, from the request and from the proof, as the claim card says it), the
machine the counted sessions ran and verified on (SE-2, the Verifying line), and the precision
the row proves beside the release serving runs. Every value is read from a stored record: the
claim card, the counted sessions' manifests and verify traces, `system.yaml`, the workload and
serving-model records. Nothing is computed but counts and sets of what the records hold.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from iproofs.model import card_path
from iproofs.provenance import file_digest
from iproofs.schema import parse_tree
from iproofs.site import inputs
from iproofs.trials import summary

# RFC-0018 SI-3 (amended 2026-11-15): the Statement block's rows, in the page's order
STATEMENT_ROWS = ("commit_record", "request", "proof", "decoding", "unchecked", "architecture")
NOT_STATED = "not stated"


def _field(card: dict[str, Any], path: str) -> object:
    node: object = card
    for part in path.split("."):
        if isinstance(node, list):
            node = node[int(part)] if part.isdigit() and int(part) < len(node) else None
        elif isinstance(node, dict):
            node = node.get(part)
        else:
            return None
    return node


def _source(sources: dict[str, Any], path: str) -> str | None:
    """A field's link: its own key in `sources`, else the nearest field above it. An item of a
    list falls back to the list's key only as item 0 (claim.yaml: `<field>.<n>` keys the n-th)."""
    parts = path.split(".")
    while parts:
        key = ".".join(parts)
        if key in sources:
            return str(sources[key])
        last = parts.pop()
        if last.isdigit() and last != "0":
            return None
    return None


def card_refs(card: dict[str, Any], refs: object, where: str) -> list[dict[str, str]] | None:
    """The card's fields a Statement row names, each as its text and link; None for "not
    stated". A path that names no text, or no source, is a config error: the row would print
    words the card does not hold."""
    if refs == NOT_STATED:
        return None
    if not isinstance(refs, list) or not refs:
        raise inputs.config(f"{where}: {refs!r} is neither a list of fields nor {NOT_STATED!r}")
    out = []
    for path in refs:
        text, url = _field(card, str(path)), _source(card.get("sources") or {}, str(path))
        if not isinstance(text, str) or not text.strip():
            raise inputs.config(f"{where}: {path!r} names no text of the card")
        if url is None:
            raise inputs.config(f"{where}: {path!r} has no source in the card")
        out.append({"field": str(path), "text": " ".join(text.split()), "url": url})
    return out


def _parts(names: list[str]) -> list[dict[str, Any]]:
    """A proof's files by kind, in first-seen order: files that share the suffix after their
    first dot as one kind ("*.proof.json", with their count), a file alone by its name."""
    kinds: dict[str, list[str]] = {}
    for name in names:
        stem, dot, rest = name.partition(".")
        kinds.setdefault(f"*.{rest}" if dot and stem else name, []).append(name)
    return [{"kind": k if len(ns) > 1 else ns[0], "count": len(ns)} for k, ns in kinds.items()]


def _json(path: Path) -> dict[str, Any]:
    found = json.loads(path.read_text())
    return found if isinstance(found, dict) else {}


def _manifests(root: Path, release: str, row: dict[str, Any]) -> list[tuple[Path, dict[str, Any]]]:
    """The counted sessions' run directories and manifests, those stored in this tree."""
    out = []
    for s in row["sessions"]:
        d = root / "results" / release / row["system"] / str(s["run_id"])
        if (d / "manifest.json").is_file():
            out.append((d, _json(d / "manifest.json")))
    return out


def statement(root: Path, release: str | None, row: dict[str, Any],
              request: dict[str, Any]) -> dict[str, Any] | None:  # fmt: skip
    """The Statement block of a row, or None when its properties file has no `verifier_inputs`
    (each row names fields of the claim card, which holds the text and its sources)."""
    path = card_path(root, row["system"], str(row["configuration"]))
    card = inputs.read_yaml(path) if path is not None else {}
    props = root / "systems" / row["system"] / "properties.yaml"
    vi = (inputs.read_yaml(props) if props.is_file() else {}).get("verifier_inputs")
    if not isinstance(vi, dict):
        return None
    where = f"systems/{row['system']}/properties.yaml verifier_inputs"
    rows = [{"id": k, "said": card_refs(card, vi[k], f"{where}.{k}")} for k in STATEMENT_ROWS]
    files: list[str] = []
    parts: list[str] = []
    for _, m in _manifests(root, release, row) if release else []:
        for f in (m.get("commitment") or {}).get("verifier_files") or []:
            if f.get("name") not in files:
                files.append(str(f.get("name")))
        if not parts and m.get("proofs"):
            parts = [str(p.get("name")) for p in m["proofs"][0].get("parts") or []]
    system = root / "systems" / row["system"] / "system.yaml"
    reads = (inputs.read_yaml(system).get("proofs") or {}).get("verify_reads") if \
        system.is_file() else None  # fmt: skip
    read = parts
    if isinstance(reads, dict) and isinstance(reads.get("read"), list):
        read = [p for p in parts if p in reads["read"]]
    # an erratum to the card (web/_data/errata.json `cards`), printed while the card is the one
    # it corrects: the runs record the card's digest, so the card itself is not edited
    fix = (inputs.errata(root).get("cards") or {}).get(row["system"])
    if not (isinstance(fix, dict) and path is not None
            and file_digest(path) == fix.get("card_digest")):  # fmt: skip
        fix = None
    return {
        "erratum": fix,
        "notion": list(
            ((inputs.read_yaml(props) if props.is_file() else {}).get("notion") or {}).get("quotes")
            or []
        ),  # the publisher's name for its soundness notion
        "program": str(vi["program"]),
        "untimed": [str(u) for u in vi.get("untimed") or []],
        "reply": str(vi["reply"]),
        "proof_caveat": vi.get("proof_caveat"),
        "architecture_visible": vi.get("architecture_visible"),
        "rows": rows,
        "card": f"systems/{row['system']}/{path.name}" if path else None,
        "verifier_files": files,
        "proof_read": _parts(read),  # the files the verifier reads (system.yaml verify_reads)
        "proof_files": len(read),
        "proof_parts": _parts(parts),  # every file a proof is released as: what its size counts
        "proof_parts_count": len(parts),
        "prompt_tokens": request["prompt_tokens"],
        "output_tokens": request["output_tokens"],
    }


def _bound(gpu: dict[str, Any]) -> int | None:
    if isinstance(gpu.get("bound_indices"), list) and gpu["bound_indices"]:
        return len(gpu["bound_indices"])
    return 1 if isinstance(gpu.get("bound_index"), int) else None


def machine(root: Path, release: str | None, row: dict[str, Any],
            gpus: dict[str, str]) -> dict[str, Any] | None:  # fmt: skip
    """The machine the counted sessions ran on (SE-2) and verified on (the Verifying line), as
    their manifests and verify traces record it; each fact the sorted set of the sessions'
    values (one value when they agree). None with no stored manifest."""
    found = _manifests(root, release, row) if release else []
    if not found:
        return None

    def values(get: Any) -> list[Any]:
        return sorted({v for v in (get(m) for _, m in found) if v is not None}, key=str)

    def gpu_seen(d: Path) -> bool | None:
        seen = [bool(_json(t).get("gpu_visible"))
                for t in sorted((d / "verify-trace").glob("*.json"))]  # fmt: skip
        return any(seen) if seen else None

    def machine_of(m: dict[str, Any]) -> dict[str, Any]:
        return dict(m.get("machine") or {})

    return {
        "sessions": len(found),
        "cpu_model": values(lambda m: (machine_of(m).get("cpu") or {}).get("model")),
        "verifier_cpus": values(lambda m: len((machine_of(m).get("cpu") or {})
                                              .get("bound_verifier") or []) or None),
        "verifier_host": values(lambda m: machine_of(m).get("verifier_host")),
        "gpu_model": values(lambda m: gpus.get(str((machine_of(m).get("gpu") or {})
                                                   .get("model")))),
        "gpus_visible": values(lambda m: (machine_of(m).get("gpu") or {}).get("count_visible")),
        "gpus_bound": values(lambda m: _bound(machine_of(m).get("gpu") or {})),
        "verify_gpu_visible": sorted({v for v in (gpu_seen(d) for d, _ in found)
                                      if v is not None}),
    }  # fmt: skip


def serving_release(root: Path, serving: str | None) -> dict[str, Any] | None:
    """The publisher's release serving runs (the rung's serving-model record, CO-4)."""
    sp = root / "workloads" / "serving" / f"{serving}.yaml"
    if not serving or not sp.is_file():
        return None
    doc = inputs.read_yaml(sp)
    return {"publisher": (doc.get("publisher") or {}).get("name"),
            "precision": (doc.get("precision") or {}).get("name"),
            "record": f"workloads/serving/{serving}.yaml"}  # fmt: skip


def precision(root: Path, row: dict[str, Any], models: dict[str, Any]) -> dict[str, Any] | None:
    """The precision the row proves, as its workload record states it."""
    path = root / "workloads" / f"{row['workload']}.yaml"
    if not path.is_file():
        return None
    wl = inputs.read_yaml(path)
    p = wl.get("precision") or {}
    bits = p.get("weight_bits") or {}
    words = (models.get(str((wl.get("model") or {}).get("digest"))) or {}).get("precision_words")
    proved = str(p.get("proved"))
    return {
        "proved": proved,
        "proved_words": (words or {}).get(proved),
        "bits": bits.get("bits"),
        "bits_basis": bits.get("basis"),
        "bits_covers": bits.get("covers"),
        "bits_source": bits.get("source"),
        "record": f"workloads/{row['workload']}.yaml",
        # the number format the row proves, where its properties file records it (properties/2
        # `number_format`, the publisher's words at the pin); None where it records none
        "number_format": number_format(root, row),
    }


def number_format(root: Path, row: dict[str, Any]) -> dict[str, str] | None:
    """The proved copy's number format, weights and activations, each `integer`,
    `fixed_point`, `floating_point` or `not_stated`, as the properties file records it with the
    publisher's words (RFC-0018 §5.3 of 2026-11-16: never inferred from a format's name); None
    where the file records none, so a page prints no format rather than "not stated"."""
    props = root / "systems" / row["system"] / "properties.yaml"
    raw = (inputs.read_yaml(props) if props.is_file() else {}).get("number_format")
    if not isinstance(raw, dict):
        return None
    return {k: str((raw.get(k) or {}).get("value") or "not_stated")
            for k in ("weights", "activations")}  # fmt: skip


# RFC-0008 §Verifier trials: where a stored trial is printed (it gates nothing). A trial of the
# verifier the row runs goes beside the check whose change it makes, by its calls' change kind; a
# trial of another of the publisher's verifiers goes under Machine-checked, the petal that names
# the verifier a theorem is stated for (MC-7). A trial of the row's verifier whose changes name no
# one check is printed nowhere.
TRIAL_PLACE = {"reply_token": "reply", "other_session_commitment": "model"}
OTHER_VERIFIER = "machine_checked"


def kept_trials(root: Path, release: str | None, row: dict[str, Any]) -> list[dict[str, Any]]:
    """The row's verifier trials, each with its place, the verifier's name (the properties
    file's `verifiers`), its record and its counts (`iproofs.trials.summary`, over the row's
    counted sessions)."""
    if not release:
        return []
    folder = root / "results" / release / row["system"] / "_trials"
    props = root / "systems" / row["system"] / "properties.yaml"
    named = (inputs.read_yaml(props) if props.is_file() else {}).get("verifiers") or {}
    run = (named.get("run") or {}).get("value")
    stated = (named.get("stated") or {}).get("value")
    counted = {str(s["run_id"]) for s in row["sessions"]}
    out = []
    for path in sorted(folder.glob("*/trial.json")):
        doc: dict[str, Any] = parse_tree(path)
        kinds = {str(c["change"]["kind"]) for c in doc["calls"] if c["change"] is not None}
        if run and str(run) in str(doc["program"]["name"]):
            places = {TRIAL_PLACE[k] for k in kinds if k in TRIAL_PLACE}
            if len(places) != 1:
                continue
            place, verifier = places.pop(), str(run)
        else:
            place, verifier = OTHER_VERIFIER, str(stated or doc["program"]["name"])
        out.append({"id": str(doc["id"]), "place": place, "verifier": verifier,
                    "changes": sorted(kinds), "record": path.relative_to(root).as_posix(),
                    **asdict(summary(doc, counted))})  # fmt: skip
    return out
