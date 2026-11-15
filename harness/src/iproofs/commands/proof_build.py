"""`iproofs proof-build record FOLDER --system NAME --release RELEASE` (RFC-0018 MC-4a, MC-5).

Writes `results/<release>/proof-build/<system>/proof-build.json` from the folder a
`docs/runbooks/proof-build.sh` job wrote, checked against `proof-build/1`. The theorem and its
link are the system's properties file's (`formal.theorem`, `formal.theorem_url`), the build's
named theorem; every other value comes from what the job recorded. One record per system (MC-5):
a stored record is replaced only with `--replace`, and only by a build that reached a verdict
(built or failed); a stopped build replaces none, its folder and the change say so (RFC-0018,
amended 2026-11-16).
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
                   help="replace the stored record with this built or failed build")  # fmt: skip
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
    if out.exists() and record["status"] == "stopped":
        stays = out.relative_to(root)
        raise IProofsError(ErrorKind.CONFIG, f"this build stopped ({record.get('stop')}): a "
                           f"stopped build replaces no record; {stays} stays")  # fmt: skip
    if out.exists() and not args.replace:
        raise IProofsError(ErrorKind.CONFIG, f"{out.relative_to(root)} exists; give --replace "
                           "to replace it with this build")  # fmt: skip
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, record)
    print(out.relative_to(root))
    return 0
