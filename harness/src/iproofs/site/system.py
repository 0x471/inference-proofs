"""What a system page prints beside the board's figures, from the records they were taken on.

RFC-0018 SI-3 (amended 2026-11-15): the Statement block (what the verifier the row runs takes
from the harness record, from the request and from the proof, as the claim card says it), the
machine the counted sessions ran and verified on (SE-2, the Verifying line), and the precision
the row proves beside the release serving runs. Every value is read from a stored record: the
claim card, the counted sessions' manifests and verify traces, `system.yaml`, the workload and
serving-model records. Nothing is computed but counts and sets of what the records hold.
"""

import json
from pathlib import Path
from typing import Any

from iproofs.model import card_path
from iproofs.site import inputs

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
    """The Statement block of a row, or None when its claim card has no `verifier_inputs`."""
    path = card_path(root, row["system"], str(row["configuration"]))
    card = inputs.read_yaml(path) if path is not None else {}
    vi = card.get("verifier_inputs")
    if not isinstance(vi, dict):
        return None
    where = f"systems/{row['system']}/{path.name if path else 'claim.yaml'} verifier_inputs"
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
    return {
        "program": str(vi["program"]),
        "untimed": [str(u) for u in vi.get("untimed") or []],
        "reply": str(vi["reply"]),
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
    }
