"""`iproofs proof-build record FOLDER --system NAME --release RELEASE` (RFC-0018 MC-4a, MC-5).

Writes `results/<release>/proof-build/<system>/proof-build.json` from the folder a
`docs/runbooks/proof-build.sh` job wrote, checked against `proof-build/1`. The theorem and its
link are the system's properties file's (`formal.theorem`, `formal.theorem_url`), the build's
named theorem; every other value comes from what the job recorded. A stored record is never
written over: one build per system (MC-5), and a rerun is recorded in its own change.
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
    p.set_defaults(handler=proof_build_record)


def proof_build_record(args: argparse.Namespace) -> int:
    import yaml  # noqa: PLC0415

    from iproofs.errors import ErrorKind, IProofsError  # noqa: PLC0415
    from iproofs.proof_build import build_record  # noqa: PLC0415
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
    out = root / "results" / args.release / "proof-build" / args.system / "proof-build.json"
    if out.exists():
        raise IProofsError(ErrorKind.CONFIG, f"{out.relative_to(root)} exists; it is never "
                           "written over")  # fmt: skip
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, record)
    print(out.relative_to(root))
    return 0
