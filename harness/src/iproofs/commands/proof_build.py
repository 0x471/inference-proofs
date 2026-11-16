"""`iproofs proof-build record FOLDER --system NAME --release RELEASE` (RFC-0018 MC-4a, MC-5).

Writes `results/<release>/proof-build/<system>/proof-build.json` from the folder a
`docs/runbooks/proof-build.sh` job wrote, checked against `proof-build/1`. The theorem and its
link are the system's properties file's (`formal.theorem`, `formal.theorem_url`), the build's
named theorem; every other value comes from what the job recorded. One record per system (MC-5):
with `--replace`, the publisher's full check replaces a stored targeted build when it reached a
verdict (built or failed); a stopped build, a targeted build over a full check, or a second full
check replaces none (RFC-0018 Q43, owner decision 2026-11-16).
"""

import argparse
from pathlib import Path

from iproofs.commands import Command


def register(sub: "argparse._SubParsersAction[argparse.ArgumentParser]", command: Command) -> None:
    group = sub.add_parser("proof-build", help="proof-build records (RFC-0018 MC-5)")
    actions = group.add_subparsers(dest="proof_build_command", required=True, metavar="ACTION")
    p = command("record", "write a proof-build/1 record from a build job's folder", actions,
                "proof-build record")  # fmt: skip
    p.add_argument("folder", type=Path, help="the folder the build job wrote (its OUT)")
    p.add_argument("--system", required=True)
    p.add_argument("--release", required=True)
    p.add_argument("--replace", action="store_true",
                   help="replace a stored targeted build with this full check")  # fmt: skip
    p.set_defaults(handler=proof_build_record)


def proof_build_record(args: argparse.Namespace) -> int:
    import yaml  # noqa: PLC0415

    from iproofs.errors import ErrorKind, IProofsError  # noqa: PLC0415
    from iproofs.proof_build import build_record, record_path  # noqa: PLC0415
    from iproofs.schema import SchemaRegistry  # noqa: PLC0415
    from iproofs.serialize import write_json  # noqa: PLC0415
    from iproofs.validate import repo_root  # noqa: PLC0415

    root = repo_root(Path.cwd())
    props = yaml.safe_load((root / "systems" / args.system / "properties.yaml").read_text())
    formal = (((props or {}).get("petals") or {}).get("machine_checked") or {}).get("formal") or {}
    record = build_record(args.folder, args.system, formal)
    errors = SchemaRegistry.from_tree(root / "schema").errors("proof-build/1", record)
    if errors:
        raise IProofsError(ErrorKind.INTERNAL, f"the record fails proof-build/1: {errors[0]}")
    out = root / record_path(args.release, args.system)
    replaces(out, record, args.replace, root)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, record)
    print(out.relative_to(root))
    return 0


def _full_check(record: dict[str, object]) -> bool:
    argv = record.get("argv")
    return isinstance(argv, list) and "scripts/check.py" in [str(a) for a in argv]


def replaces(out: Path, record: dict[str, object], replace: bool, root: Path) -> None:
    """Raises unless `record` may be written at `out` (Q43): anything where none is stored; with
    `--replace`, a full check that reached a verdict over a stored targeted build."""
    import json  # noqa: PLC0415

    from iproofs.errors import ErrorKind, IProofsError  # noqa: PLC0415

    if not out.exists():
        return
    if record["status"] == "stopped":
        stays = out.relative_to(root)
        raise IProofsError(ErrorKind.CONFIG, f"this build stopped ({record.get('stop')}): a "
                           f"stopped build replaces no record; {stays} stays")  # fmt: skip
    if not replace:
        raise IProofsError(ErrorKind.CONFIG, f"{out.relative_to(root)} exists; give --replace "
                           "to replace a targeted build with a full check")  # fmt: skip
    stored = json.loads(out.read_text())
    if _full_check(stored) or not _full_check(record):
        raise IProofsError(ErrorKind.CONFIG, "only the publisher's full check replaces a stored "
                           "targeted build (Q43)")  # fmt: skip
