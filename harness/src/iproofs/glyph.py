"""The glyph of a row (RFC-0018 §The glyph, GL-1 to GL-9): five petals, each a step on its own
question, never a total (GL-8). It never moves a position (GL-4).

Four statement petals are computed from the facts a reviewer copies into
`systems/<name>/properties.yaml` (schema `properties/2`): no state is typed (GL-1). Tests only
lower them (GL-2). `faithful_model` is measured: it reads the step tests that `iproofs fidelity
score` stores in the rung's `fidelity.json`. Each decision function follows its table line by
line (UF-1 to UF-9, MC-1 to MC-7, WH-1 to WH-6, FM-1 to FM-7, NT-1 to NT-6): the first matching
line wins. A statement petal that rests on our reading is drawn amber in part at most (GL-10).
Every function here is pure except `load_properties` and `load_proof_build`.
"""

import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from iproofs.errors import ErrorKind, IProofsError
from iproofs.fidelity import sign_flip_p
from iproofs.serialize import load_yaml

GREEN, AMBER, RED, HOLLOW = "green", "amber", "red", "hollow"
AMBER_UPPER, AMBER_LOWER = "amber_upper", "amber_lower"
STATEMENT, TEST = "statement", "test"
PETALS = ("unforgeable", "weights_hidden", "faithful_model", "machine_checked", "no_trusted_party")
STATEMENT_PETALS = ("unforgeable", "weights_hidden", "machine_checked", "no_trusted_party")
STEPS = (GREEN, AMBER_UPPER, AMBER_LOWER, RED, None)
STEP_STATE: Mapping[str | None, str] = {GREEN: GREEN, AMBER_UPPER: AMBER, AMBER_LOWER: AMBER,
                                        RED: RED, None: HOLLOW}  # fmt: skip
RED_CAUSES = ("not_stated", "stated", "check_failed")
HOLLOW_CAUSES = ("not_read", "not_decided", "proof_build_not_run")
NOT_STATED, STATED, CHECK_FAILED = RED_CAUSES
NOT_READ, NOT_DECIDED, PROOF_BUILD_NOT_RUN = HOLLOW_CAUSES
PROPERTIES_SCHEMA = "properties/2"
NO_PROPERTIES = "no properties file"
EXACT_MATCH = "exact_match"
# GL-2: the checks whose failure lowers a petal (Machine-checked only where it was green)
LOWERED_BY: Mapping[str, tuple[str, ...]] = {
    "unforgeable": ("model", "prompt", "reply"),
    "weights_hidden": ("no_weight_file",),
    "faithful_model": ("fidelity",),
    "machine_checked": ("model", "prompt", "reply"),
    "no_trusted_party": (),
}
_CHECK_NAMES = {"model": "Model", "prompt": "Prompt", "reply": "Reply",
                "no_weight_file": "Verify without weights", "fidelity": "Fidelity"}  # fmt: skip
_REACH_WORDS = {"part": "a part", "protocol": "the protocol",
                "protocol_and_statement": "the protocol and the model's statement",
                "verifier_run": "the verifier program the row runs",
                "none": "nothing", "not_stated": "not stated"}  # fmt: skip
_REST_WORDS = {"single_party_setup": "a setup run by one party",
               "hardware_key": "a hardware maker's key",
               "trusted_key": "a trusted key"}  # fmt: skip
SCOPE_ROWS = ("soundness", "zero_knowledge", "completeness")
SCOPE_COLS = ("protocol", "verifier_run", "prover_run")
# the two cells of the scope card that ask a property of the wrong party: soundness holds against
# a cheating prover and is the verifier's; zero knowledge holds against a cheating verifier and is
# the prover's (amended 2026-11-15)
DOES_NOT_APPLY = "does_not_apply"
SCOPE_NOT_APPLICABLE = frozenset({("soundness", "prover_run"), ("zero_knowledge", "verifier_run")})
# MC-7: the axioms a build may report for a step above amber in lesser part, by the tool's first
# word: Lean's three standard axioms (a proof with `sorry` reports `sorryAx`). For a tool not
# named here, no reported axiom may name a gap (`sorry`, `admit`, `Admitted`)
STANDARD_AXIOMS = {"Lean": frozenset({"propext", "Classical.choice", "Quot.sound"})}
_GAP_WORDS = ("sorry", "admit")
_STEP_WORDS = {GREEN: "green in full", AMBER_UPPER: "amber in part",
               AMBER_LOWER: "amber in lesser part", RED: "red"}  # fmt: skip
# what one stated bound covers, as a reason prints it after the bound (UF, GL-5)
_UNIT_WORDS = {"proof": "per proof", "reply": "per reply", "part": "per part of a proof",
               "round": "per round"}  # fmt: skip
_ZK_KIND_WORDS = {"statistical": "statistical", "computational": "computational",
                  "perfect": "perfect"}  # fmt: skip
_ZK_MODEL_WORDS = {"random_oracle": "random-oracle model", "standard": "standard model"}
# the facts whose quotes a board petal carries, in the properties order (spec 1.5)
_QUOTED = {
    "unforgeable": ("bound", ("stated", "expression", "basis", "unit", "batch", "adversary",
                              "parameters", "conditions_shown", "program")),
    "weights_hidden": ("hiding", ("stated", "verifier_gets_weights", "proof", "programs",
                                  "visible_listed", "visible_at_least")),
    "machine_checked": ("formal", ("reach", "conclusion", "tool", "toolchain", "trusted_base",
                                   "input_code_unverified")),
    "no_trusted_party": ("trust", ("rests_on", "publicly_checkable")),
}  # fmt: skip

Quote = Mapping[str, str]


@dataclass(frozen=True, slots=True)
class Petal:
    """One petal. `state` is the step's ink (STEP_STATE), never set on its own."""

    id: str
    step: str | None
    cause: str | None
    basis: str
    reason: str
    quotes: tuple[Quote, ...] = ()
    lowered_by: tuple[str, ...] = ()
    formal: Mapping[str, object] | None = None
    visible: Sequence[Mapping[str, object]] | None = None
    reading: bool = False  # a fact the decision read carries a note: the reader's reading (N1)
    sources: tuple[Mapping[str, str], ...] = ()  # R-SILENT: the documents read, linked at the pin
    forms: Sequence[Mapping[str, object]] | None = None  # Weights hidden: the stated ZK forms
    visible_at_least: bool = False  # Weights hidden: the publisher's list is a lower bound

    @property
    def state(self) -> str:
        return STEP_STATE[self.step]

    def tree(self) -> dict[str, object]:
        out: dict[str, object] = {
            "id": self.id,
            "state": self.state,
            "step": self.step,
            "cause": self.cause,
            "basis": self.basis,
            "reason": self.reason,
            "quotes": [_quote(q) for q in self.quotes],
            "lowered_by": list(self.lowered_by),
        }
        if self.id == "machine_checked":
            out["formal"] = None if self.formal is None else dict(self.formal)
        if self.id == "weights_hidden":
            out["visible"] = None if self.visible is None else [
                {"item": str(i.get("item")), "tag": str(i.get("tag")),
                 "quotes": [_quote(q) for q in _quotes(i)]} for i in self.visible]  # fmt: skip
        if self.id == "weights_hidden" and self.forms:
            out["forms"] = [{"item": str(i.get("item")), "quotes": [_quote(q) for q in _quotes(i)]}
                            for i in self.forms]  # fmt: skip
        if self.id == "weights_hidden" and self.visible_at_least:
            out["visible_at_least"] = True
        if self.reading:
            out["reading"] = True
        if self.sources:
            out["sources_read"] = [dict(s) for s in self.sources]
        return out


@dataclass(frozen=True, slots=True)
class Coverage:
    """What the row proves, from stored records (spec §2): the system's `proofs.granularity`
    and the workload's `shape.batch_size`, None when not recorded."""

    granularity: str | None
    batch_size: int | None

    @property
    def one_reply(self) -> bool:
        """One proof covers one reply (U4); the batch size does not change replies per proof."""
        return self.granularity == "request"


# ---------------------------------------------------------------- reading the records


def load_properties(root: Path, system: str) -> dict[str, object] | None:
    path = root / "systems" / system / "properties.yaml"
    return load_yaml(path) if path.is_file() else None


def load_proof_build(root: Path, release: str, system: str) -> dict[str, object] | None:
    """The proof-build record of `system` (`proof-build/1`), None when none is stored."""
    path = root / "results" / release / "proof-build" / system / "proof-build.json"
    if not path.is_file():
        return None
    found = json.loads(path.read_text())
    return found if isinstance(found, dict) else None


def _m(x: object) -> Mapping[str, object]:
    return x if isinstance(x, Mapping) else {}


def _v(fact: object) -> object:
    return _m(fact).get("value")


def _quotes(fact: object) -> tuple[Quote, ...]:
    found = _m(fact).get("quotes")
    return tuple(q for q in found if isinstance(q, Mapping)) if isinstance(found, list) else ()


def _quote(q: Quote) -> dict[str, str]:
    return {"text": str(q["text"]), "url": str(q["url"])}


class _Facts:
    """The facts of one group as a decision reads them, in order. `noted` turns true once a fact
    read carries a `note`: the value is then the reader's reading, not the publisher's words
    (N1)."""

    def __init__(self, group: Mapping[str, object]) -> None:
        self.group = group
        self.noted = False

    def __call__(self, key: str) -> object:
        fact = _m(self.group.get(key))
        if fact.get("note"):
            self.noted = True
        return fact.get("value")


def _pin(props: Mapping[str, object]) -> str:
    return str(_m(props.get("upstream")).get("commit"))


def read(
    props: Mapping[str, object] | None, commit: str | None
) -> tuple[Mapping[str, object] | None, str | None]:
    """The file's petals, or None and why it is not read (GL-3: not read is not silent)."""
    if props is None:
        return None, NO_PROPERTIES
    schema = props.get("schema")
    if schema != PROPERTIES_SCHEMA:
        return None, f"properties file is {schema}, the glyph reads {PROPERTIES_SCHEMA}"
    pin = _pin(props)
    if commit is None:  # U7: the row's commit is not known, so the file is not shown to fit it
        return None, "the row's commit is not recorded"
    if pin != commit:
        return None, f"properties file read at {pin[:7]}, the row runs {commit[:7]}"
    return _m(props.get("petals")), None


def failed(checks: Mapping[str, str], ids: Sequence[str]) -> list[str]:
    """GL-2: the failed checks among `ids`; an undecided check lowers nothing."""
    return [c for c in ids if checks.get(c) == "failed"]


def _check_failed(
    pid: str,
    ids: Sequence[str],
    quotes: tuple[Quote, ...] = (),
    formal: Mapping[str, object] | None = None,
    visible: Sequence[Mapping[str, object]] | None = None,
) -> Petal:
    """R-CF: red, cause check_failed, basis test, naming the failed checks (GL-2)."""
    names = ", ".join(_CHECK_NAMES[c] for c in ids)
    return Petal(pid, RED, CHECK_FAILED, TEST, f"our {names} check failed", quotes, tuple(ids),
                 formal, visible)  # fmt: skip


def _not_read(pid: str, reason: str) -> Petal:
    return Petal(pid, None, NOT_READ, STATEMENT, reason)


def _silent(petal: Mapping[str, object], props: Mapping[str, object]) -> str:
    """R-SILENT: silence at the pin; the documents read go with the petal (`_with_sources`)."""
    return "not stated in the publisher's documents read at the pinned commit"


def _with_sources(p: Petal, props: Mapping[str, object] | None) -> Petal:
    """R-SILENT: a silent red carries the petal's `sources_read`, each linked at the pin."""
    if p.cause != NOT_STATED or props is None:
        return p
    up = _m(props.get("upstream"))
    docs = _m(_m(props.get("petals")).get(p.id)).get("sources_read")
    base = f"https://github.com/{up.get('repo')}/blob/{up.get('commit')}/"
    found = tuple({"path": str(d), "url": base + str(d)}
                  for d in (docs if isinstance(docs, list) else ()))  # fmt: skip
    return replace(p, sources=found)


def petal_quotes(pid: str, petal: Mapping[str, object]) -> tuple[Quote, ...]:
    """The quotes of the facts that decide `pid`, in the properties order, each once."""
    key, facts = _QUOTED[pid]
    group = _m(petal.get(key))
    seen: set[tuple[str, str]] = set()
    out: list[Quote] = []
    for fact in facts:
        for q in _quotes(group.get(fact)):
            k = (str(q.get("text")), str(q.get("url")))
            if k not in seen:
                seen.add(k)
                out.append(q)
    return tuple(out)


# ---------------------------------------------------------------- Unforgeable (UF-1 to UF-9)


def _verifiers(props: Mapping[str, object] | None) -> tuple[str | None, str | None]:
    """The verifier program the row runs and the one the publisher's bound and theorem are stated
    for, as the properties file names them (GL-5), None where it names none."""
    found = _m(_m(props).get("verifiers"))
    run, stated = _v(found.get("run")), _v(found.get("stated"))
    return (str(run) if run else None), (str(stated) if stated else None)


def _bound_head(b: Mapping[str, object], stated_for: str | None) -> str:
    """UF (amended 2026-11-15): the stated bound as the reason opens with it, the publisher's
    expression with what it is stated per and the verifier it is stated for."""
    expr = str(_v(b.get("expression")))
    head = f"at most {expr}" if _EXPONENT.search(expr) else expr
    per = _UNIT_WORDS.get(str(_v(b.get("unit"))))
    head += f" {per}" if per else ""
    return head + (f", stated for {stated_for}" if stated_for else "")


def _program_short(b: Mapping[str, object], run: str | None, stated_for: str | None) -> str | None:
    """U6: the program condition, None when the bound is proved or stated for the program run."""
    if _v(b.get("program")) in ("proved", "stated"):
        return None
    if run is None:
        return "not stated for the verifier program the row runs"
    if stated_for is not None:
        return f"none stated for {run}, which this row runs"
    return f"not stated for {run}, the verifier this row runs"


def _batch_short(batch: object, n: int | None) -> str | None:
    """U5, U6: whether the bound covers each member of the row's batch as the row checks it."""
    if n == 1:
        return None
    if n is None:
        return "batch size not recorded"
    if batch == "each_member":
        return None
    if batch == "together":
        return f"stated for proofs checked together, not for our separate checks of {n}-reply " \
            "batches"  # fmt: skip
    return f"no bound stated for batch members, and the row proves {n} replies a batch"


def _failing(
    b: Mapping[str, object], coverage: Coverage, run: str | None, stated_for: str | None
) -> list[str]:
    """UF-9 (amended 2026-11-15): every condition that keeps the bound from covering the run, the
    program condition first, then the basis, the adversary, the unit, the batch, the parameters
    and the conditions; empty when the bound covers it. Read for the reason only: the step is
    decided by `_covers`, which reads each fact only when the conditions before it hold (N1)."""
    out = []
    program = _program_short(b, run, stated_for)
    if program is not None:
        out.append(program)
    basis = _v(b.get("basis"))
    if basis == "conjectured":
        out.append("conjectured, not proved")
    elif basis != "proved":
        out.append("not said to be proved")
    if _v(b.get("adversary")) != "any_prover":
        out.append("not said which provers it holds against")
    unit = _v(b.get("unit"))
    if unit in ("part", "round"):
        out.append("not per reply")
    elif unit not in ("reply", "proof"):
        out.append("not said what it is stated per")
    elif unit == "proof" and not coverage.one_reply:
        out.append("replies per proof not recorded" if coverage.granularity is None
                   else "a proof here covers more than one reply")  # fmt: skip
    batch = _batch_short(_v(b.get("batch")), coverage.batch_size)
    if batch is not None:
        out.append(batch)
    parameters = _v(b.get("parameters"))
    if parameters == "other":
        out.append("stated for other parameters than the row's")
    elif parameters != "row":
        out.append("its parameters not shown to be the row's")
    if _v(b.get("conditions_shown")) is not True:
        out.append("its conditions not shown to hold for the row's files")
    return out


def _covers(v: _Facts, coverage: Coverage) -> bool:
    """U5, U6: whether a proved bound covers the run. Each fact is read only when the conditions
    before it hold, so `v.noted` names the readings the step rests on (N1)."""
    if v("adversary") != "any_prover":
        return False
    unit = v("unit")
    if unit not in ("reply", "proof") or (unit == "proof" and not coverage.one_reply):
        return False
    n = coverage.batch_size
    if n != 1 and (n is None or v("batch") != "each_member"):
        return False
    if v("parameters") != "row" or v("conditions_shown") is not True:
        return False
    return v("program") in ("proved", "stated")


def unforgeable(  # noqa: PLR0911 (one return per line of the table)
    props: Mapping[str, object] | None,
    checks: Mapping[str, str],
    commit: str | None,
    coverage: Coverage,
) -> Petal:
    pid = "unforgeable"
    petals, nr = read(props, commit)
    petal = _m(petals.get(pid)) if petals is not None else {}
    quotes = petal_quotes(pid, petal) if petals is not None else ()
    f = failed(checks, LOWERED_BY[pid])
    if f:  # UF-1
        return _check_failed(pid, f, quotes)
    if petals is None or props is None:  # UF-2
        return _not_read(pid, nr or NO_PROPERTIES)
    b = _m(petal.get("bound"))
    v = _Facts(b)
    raw_terms = b.get("terms")
    terms = [int(t) for t in raw_terms] if isinstance(raw_terms, list) else []
    if v("stated") is not True or not terms:  # UF-3
        return Petal(pid, RED, NOT_STATED, STATEMENT, _silent(petal, props), quotes,
                     reading=v.noted)  # fmt: skip
    run, stated_for = _verifiers(props)
    head = _bound_head(b, stated_for)

    def decided(step: str, cause: str | None, *why: str) -> Petal:
        return Petal(pid, step, cause, STATEMENT, "; ".join((head, *why)), quotes,
                     reading=v.noted)  # fmt: skip

    least = min(terms)
    if v("adversary") == "weaker":  # UF-4
        return decided(RED, STATED, "stated against a weaker prover")
    if least < 80:  # UF-5
        return decided(RED, STATED, f"exponent {least}, under 80")
    basis = v("basis")
    if basis != "proved" and least < 100:  # UF-6
        said = "conjectured, not proved" if basis == "conjectured" else "not said to be proved"
        return decided(RED, STATED, f"{said}, and exponent {least}, under 100")
    covers = basis == "proved" and _covers(v, coverage)
    if covers and least >= 128:  # UF-7
        return decided(GREEN, None, "covers each reply as the row runs it, every exponent 128 or "
                       "more")  # fmt: skip
    if covers and least >= 100:  # UF-8
        return decided(AMBER_UPPER, None, "covers each reply as the row runs it, with exponent "
                       f"{least}, under 128")  # fmt: skip
    why = _failing(b, coverage, run, stated_for)  # UF-9: every failing condition, program first
    if least < 100:
        why.append(f"exponent {least}, under 100")
    return decided(AMBER_LOWER, None, *why)


# ---------------------------------------------------------------- Machine-checked (MC-1 to MC-6)


def stated_reach_step(
    formal: Mapping[str, object], v: Callable[[str], object] | None = None
) -> str:
    """The step the publisher's words reach, before a proof build or a check lowers it. `v`
    reads a fact's value (by default straight from `formal`)."""
    v = v or (lambda key: _v(formal.get(key)))
    r = v("reach")
    if r in ("part", "protocol"):
        return AMBER_LOWER
    if r == "protocol_and_statement":
        return AMBER_UPPER
    if r == "verifier_run":
        if v("trusted_base") and v("input_code_unverified") is False:
            return GREEN
        return AMBER_UPPER
    return RED  # none, not_stated, or anything the table does not name: the lower step


def standard_axioms(tool: object, reported: set[str]) -> bool:
    """MC-7: whether a build's reported axioms are only its tool's standard ones (for Lean, the
    three; for another tool, none that names a gap such as `sorry` or `admit`)."""
    standard = STANDARD_AXIOMS.get(str(tool).split(" ")[0]) if tool else None
    if standard is not None:
        return reported <= standard
    return not any(w in a.lower() for a in reported for w in _GAP_WORDS)


def ceiling(
    stated: str, conclusion: object, tool: object = None, reported: set[str] | None = None
) -> str:
    """MC-7 (amended 2026-11-15): the most a matching proof build can give. A step above amber
    in lesser part needs a theorem whose conclusion is about a reference definition of the model
    (`conclusion` is `model`) and, once built, only its tool's standard axioms, so no `sorry`;
    otherwise the stated step stops at amber in lesser part."""
    if stated not in (GREEN, AMBER_UPPER):
        return stated
    if conclusion != "model":
        return AMBER_LOWER
    if reported is not None and not standard_axioms(tool, reported):
        return AMBER_LOWER
    return stated


def _scope_cell(card: Mapping[str, object], row: str, col: str) -> dict[str, object]:
    """One cell of the scope card: the two cells that ask a property of the wrong party print
    "does not apply" whatever the file says (SCOPE_NOT_APPLICABLE); the others as recorded."""
    if (row, col) in SCOPE_NOT_APPLICABLE:
        return {"value": DOES_NOT_APPLY, "quotes": []}
    fact = _m(_m(card.get(row)).get(col))
    return {"value": str(_v(fact)), "quotes": [_quote(q) for q in _quotes(fact)]}


def _scope_bound(card: Mapping[str, object], row: str) -> dict[str, object] | None:
    fact = _m(_m(card.get(row)).get("bound"))
    text = _v(fact)
    return None if not text else {"text": str(text), "quotes": [_quote(q) for q in _quotes(fact)]}


def _formal_tree(formal: Mapping[str, object], stated: str, top: str) -> dict[str, object]:
    card = _m(formal.get("scope_card"))
    base = _v(formal.get("trusted_base"))
    theorem, url = formal.get("theorem"), formal.get("theorem_url")
    conclusion = _v(formal.get("conclusion"))
    return {
        "stated_step": stated,
        "ceiling": top,
        "conclusion": str(conclusion) if conclusion is not None else "not_stated",
        "reach": str(_v(formal.get("reach"))),
        "tool": None if _v(formal.get("tool")) is None else str(_v(formal.get("tool"))),
        "theorem": None if theorem is None else str(theorem),
        "theorem_url": None if url is None else str(url),
        "trusted_base": [str(i) for i in base] if isinstance(base, list) else [],
        "input_code_unverified": _v(formal.get("input_code_unverified")),
        "scope_card": {row: {col: _scope_cell(card, row, col) for col in SCOPE_COLS}
                       for row in SCOPE_ROWS},
        "scope_bounds": {row: _scope_bound(card, row) for row in SCOPE_ROWS},
    }  # fmt: skip


def _axioms(found: object) -> set[str]:
    return {str(a) for a in found} if isinstance(found, list) else set()


def _toolchain(found: object) -> str:
    t = _m(found)
    return f"{t.get('name')} {t.get('version')}"


def _mc_tail(fm: Mapping[str, object], r: object, run: str | None, stated_for: str | None,
             top: str | None) -> str:  # fmt: skip
    """Machine-checked's reason after its first clause (amended 2026-11-15): the verifier the
    theorem is stated for against the one the row runs, the most a build can give, and that no
    outside reader of the tool has reviewed the statement (none is recorded at Level 1)."""
    out = []
    if r == "verifier_run" and run:
        out.append(f"it is stated for {run}, which this row runs")
    elif stated_for and run:
        out.append(f"it is stated for {stated_for}, not for {run}, which this row runs")
    if top is not None:
        out.append(f"once built: {_STEP_WORDS[top]} at most")
    tool = _v(fm.get("tool"))
    if fm.get("theorem") is not None and tool:
        out.append(f"statement not reviewed by an outside {str(tool).split()[0]} reader")
    return "".join(f"; {w}" for w in out)


def machine_checked(  # noqa: PLR0911, PLR0912, PLR0915 (one return per line of the table)
    props: Mapping[str, object] | None,
    checks: Mapping[str, str],
    commit: str | None,
    build: Mapping[str, object] | None,
) -> Petal:
    pid = "machine_checked"
    petals, nr = read(props, commit)
    if petals is None or props is None:  # MC-1
        return _not_read(pid, nr or NO_PROPERTIES)
    petal = _m(petals.get(pid))
    fm = _m(petal.get("formal"))
    v = _Facts(fm)
    quotes = petal_quotes(pid, petal)
    stated = stated_reach_step(fm, v)
    conclusion = v("conclusion") if stated in (GREEN, AMBER_UPPER) else _v(fm.get("conclusion"))
    top = ceiling(stated, conclusion)
    formal = _formal_tree(fm, stated, top)
    r = _v(fm.get("reach"))
    run, stated_for = _verifiers(props)
    if stated == RED:  # MC-2
        if r == "none":
            return Petal(pid, RED, STATED, STATEMENT, "stated that nothing is machine-checked",
                         quotes, formal=formal, reading=v.noted)  # fmt: skip
        return Petal(pid, RED, NOT_STATED, STATEMENT, _silent(petal, props), quotes,
                     formal=formal, reading=v.noted)  # fmt: skip
    f = failed(checks, LOWERED_BY[pid])
    if f and stated == GREEN:  # MC-3
        return _check_failed(pid, f, quotes, formal=formal)
    pin = _pin(props)
    pin7 = pin[:7]
    theorem = fm.get("theorem")
    recorded = _m(build)
    b_upstream = _m(recorded.get("upstream"))
    b_commit = str(b_upstream.get("commit"))
    b_name = _m(recorded.get("theorem")).get("name")
    at_pin = (build is not None and b_upstream.get("repo") == _m(props.get("upstream")).get("repo")
              and b_commit == pin and theorem is not None and b_name == theorem)  # fmt: skip
    pinned = _m(v("toolchain")) if at_pin else {}  # M2: the publisher's toolchain, verbatim
    used = _m(recorded.get("toolchain"))
    match = at_pin and bool(pinned) and all(
        used.get(k) == pinned.get(k) for k in ("name", "version"))  # fmt: skip
    reported = _axioms(recorded.get("axioms_reported"))
    if match:
        status, code = recorded.get("status"), recorded.get("exit_code")
        if status != "built" or code != 0:  # MC-4
            return Petal(pid, RED, CHECK_FAILED, TEST,
                         f"the recorded proof build has status {status}, exit code {code}", quotes,
                         ("proof_build",), formal)  # fmt: skip
        declared = _axioms(fm.get("axioms"))
        if reported != declared:  # MC-4
            return Petal(pid, RED, CHECK_FAILED, TEST,
                         f"the build reports axioms {', '.join(sorted(reported))}, the publisher "
                         f"declares {', '.join(sorted(declared))}", quotes, ("proof_build",),
                         formal)  # fmt: skip
    reach = _REACH_WORDS.get(str(r), str(r))
    if not match:  # MC-5
        if at_pin and not pinned:
            reason = "the publisher pins no toolchain, so no proof build can match"
        elif at_pin:
            reason = (f"the recorded build used {_toolchain(used)}, the publisher pins "
                      f"{_toolchain(pinned)}")  # fmt: skip
        elif build is not None:
            reason = (f"the recorded proof build is of {b_name} at {b_commit[:7]}, not the row's "
                      "theorem at its commit")  # fmt: skip
        elif theorem is None:
            reason = "no theorem is named, so no proof build is recorded"
        else:
            reason = "no proof build of the named theorem is recorded yet"
        reason += _mc_tail(fm, r, run, stated_for, top)
        return Petal(pid, None, PROOF_BUILD_NOT_RUN, STATEMENT, reason, quotes, formal=formal,
                     reading=v.noted)  # fmt: skip
    step = ceiling(stated, conclusion, _v(fm.get("tool")), reported)  # MC-7
    reason = f"the named theorem builds at {pin7}, stated to reach {reach}"  # MC-6
    if r == "verifier_run" and stated == AMBER_UPPER:
        unverified = v("input_code_unverified")
        but = ("no trusted base listed" if not v("trusted_base")
               else "input code outside the proof" if unverified is True
               else "input code not stated to be inside the proof")  # fmt: skip
        reason += f", but {but}"
    if step != stated:  # MC-7: the conclusion or the reported axioms stop it
        reason += (", but its conclusion is not stated about a reference definition of the model"
                   if conclusion != "model" else
                   f", but the build reports axioms {', '.join(sorted(reported))}, not only its "
                   "tool's standard ones")  # fmt: skip
    reason += _mc_tail(fm, r, run, stated_for, None)
    return Petal(pid, step, None, STATEMENT, reason, quotes, formal=formal, reading=v.noted)


# ---------------------------------------------------------------- Weights hidden (WH-1 to WH-6)


def _visible(hiding: Mapping[str, object]) -> list[Mapping[str, object]]:
    found = hiding.get("visible")
    return [i for i in found if isinstance(i, Mapping)] if isinstance(found, list) else []


def _forms(hiding: Mapping[str, object]) -> list[Mapping[str, object]]:
    found = hiding.get("forms")
    return [i for i in found if isinstance(i, Mapping)] if isinstance(found, list) else []


def _zk_proved(h: Mapping[str, object], proof: object, n: int | None) -> list[str]:
    """WH-6 (amended 2026-11-15): what zero knowledge is proved for, its form and what one proof
    of it covers, in the publisher's facts (`zk_kind`, `zk_model`, `zk_unit`), then the row's
    batch when one statement covers one request. Printed; sets no step."""
    if proof != "protocol":
        return []
    form = [w for w in (_ZK_KIND_WORDS.get(str(_v(h.get("zk_kind")))),
                        _ZK_MODEL_WORDS.get(str(_v(h.get("zk_model"))))) if w]  # fmt: skip
    head = "zero knowledge proved for the protocol only"
    if form:
        head = f"zero knowledge ({', '.join(form)}) proved for the protocol only"
    unit = _v(h.get("zk_unit"))
    if unit == "request":
        head += ", one request a proof"
    out = [head]
    if unit == "request" and n is not None and n > 1:
        out.append(f"not for the row's {n}-reply batches")
    return out


def weights_hidden(  # noqa: PLR0911 (one return per line of the table)
    props: Mapping[str, object] | None,
    checks: Mapping[str, str],
    commit: str | None,
    coverage: Coverage | None = None,
) -> Petal:
    pid = "weights_hidden"
    petals, nr = read(props, commit)
    petal = _m(petals.get(pid)) if petals is not None else {}
    h = _m(petal.get("hiding"))
    v = _Facts(h)
    visible = _visible(h) if petals is not None else None
    quotes = petal_quotes(pid, petal) if petals is not None else ()
    f = failed(checks, LOWERED_BY[pid])
    if f:  # WH-1
        return _check_failed(pid, f, quotes, visible=visible)
    if petals is None or props is None or visible is None:  # WH-2
        return Petal(pid, None, NOT_READ, STATEMENT, nr or NO_PROPERTIES)
    forms, at_least = _forms(h), _v(h.get("visible_at_least")) is True

    def decided(step: str, cause: str | None, reason: str) -> Petal:
        return Petal(pid, step, cause, STATEMENT, reason, quotes, visible=visible,
                     reading=v.noted, forms=forms, visible_at_least=at_least)  # fmt: skip

    if v("verifier_gets_weights") is True:  # WH-3
        return decided(RED, STATED, "the verifier receives the weights")
    stated = v("stated")
    if stated is False:  # WH-3
        return decided(RED, STATED, "stated not to hide the weights")
    if stated is not True:  # WH-3: not_stated
        return decided(RED, NOT_STATED, _silent(petal, props))
    proof = v("proof")
    if proof not in ("protocol", "configuration_run"):  # WH-4 (none)
        return decided(AMBER_LOWER, None, "hiding is stated, with no zero-knowledge theorem")
    programs, listed = v("programs"), v("visible_listed") is True
    fitted = [str(i.get("item")) for i in visible if i.get("tag") == "fitted_to_weights"]
    if (proof == "configuration_run" and programs == "stated" and listed and visible
            and not fitted):  # WH-5 (W1: a listed set is copied, not empty)  # fmt: skip
        return decided(GREEN, None, "zero knowledge proved for the configuration the row runs, "
                       "with no listed visible value that depends on the weights")  # fmt: skip
    missing = _zk_proved(h, proof, coverage.batch_size if coverage else None)  # WH-6
    if programs == "expected":
        missing.append("only expected of the programs the row runs")
    elif programs != "stated":
        missing.append("not stated for the programs the row runs")
    if not listed:
        missing.append("no list of visible values")
    elif not visible:
        missing.append("visible values listed but none copied")
    if fitted:  # the names are printed in the visible list below the reason
        k = len(fitted)
        missing.append(f"{k} listed value{'s' * (k != 1)} depend{'s' * (k == 1)} on the weights")
    return decided(AMBER_UPPER, None, "; ".join(missing))


# ---------------------------------------------------------------- No third party trusted (NT)


def no_trusted_party(  # noqa: PLR0911 (one return per line of the table)
    props: Mapping[str, object] | None, commit: str | None
) -> Petal:
    """NT-1 to NT-6; no check lowers it."""
    pid = "no_trusted_party"
    petals, nr = read(props, commit)
    if petals is None or props is None:  # NT-1
        return _not_read(pid, nr or NO_PROPERTIES)
    petal = _m(petals.get(pid))
    t = _m(petal.get("trust"))
    v = _Facts(t)
    quotes = petal_quotes(pid, petal)

    def decided(step: str, cause: str | None, reason: str) -> Petal:
        return Petal(pid, step, cause, STATEMENT, reason, quotes, reading=v.noted)

    r = v("rests_on")
    rests_noted = v.noted  # N1: the value of rests_on is the reader's reading
    if r not in ("transparent", "open_ceremony", "fixed_parties", *_REST_WORDS):  # NT-2
        return decided(RED, NOT_STATED, _silent(petal, props))
    if r in _REST_WORDS:  # NT-3
        return decided(RED, STATED, f"soundness rests on {_REST_WORDS[str(r)]}")
    if r == "fixed_parties":  # NT-4
        return decided(AMBER_LOWER, None, "soundness rests on one honest party among a fixed set")
    if v("publicly_checkable") is False:  # NT-4
        return decided(AMBER_LOWER, None, "proofs are not publicly checkable")
    if r == "open_ceremony":  # NT-5 (N2)
        return decided(AMBER_UPPER, None, "soundness rests on an open setup ceremony whose "
                       "secret stays unknown if one participant was honest")  # fmt: skip
    if rests_noted:  # NT-6, N1, GL-10: no quote says it in words, so amber in part at most
        return decided(AMBER_UPPER, None, "read as resting on cryptographic assumptions alone, "
                       "with no setup that produced a secret; no quote says so, so amber in part "
                       "at most")  # fmt: skip
    return decided(GREEN, None, "stated to rest on cryptographic assumptions alone, with no "
                   "setup that produced a secret")  # NT-6  # fmt: skip


def statement_petals(
    props: Mapping[str, object] | None,
    checks: Mapping[str, str],
    commit: str | None,
    coverage: Coverage,
    build: Mapping[str, object] | None,
) -> dict[str, Petal]:
    """The four statement petals, each decided on its own (GL-7), none above amber in part when
    it rests on our reading (GL-10)."""
    found = {
        "unforgeable": unforgeable(props, checks, commit, coverage),
        "weights_hidden": weights_hidden(props, checks, commit, coverage),
        "machine_checked": machine_checked(props, checks, commit, build),
        "no_trusted_party": no_trusted_party(props, commit),
    }
    return {k: _with_sources(read_as(p), props) for k, p in found.items()}


def read_as(p: Petal) -> Petal:
    """GL-10 (amended 2026-11-15): a statement petal whose decision read a fact with a note rests
    on our reading of the publisher's documents, not a sentence that says it: it is drawn amber
    in part at most, and its reason says why."""
    if not p.reading or p.basis != STATEMENT or p.step != GREEN:
        return p
    return replace(p, step=AMBER_UPPER, reason=f"{p.reason}; it rests on our reading, so amber in "
                   "part at most")  # fmt: skip


# ---------------------------------------------------------------- Faithful model (FM-1 to FM-7)


def _scores(found: object) -> list[int] | None:
    scores = _m(found).get("scores")
    if not isinstance(scores, list) or not scores or not all(isinstance(s, int) for s in scores):
        return None
    return [int(s) for s in scores]


_THRESHOLD_NAMES = (("green", "T_green"), ("upper", "T_upper"))
_LINE_WORDS = {"green": "rerun and Q8_0", "upper": "Q8_0 and Q4_K_M"}  # whose midpoint each is
# FM (amended 2026-11-15): a control as a reason names it, by its type or recipe
_CONTROL_WORDS = {"q8_0": "the 8-bit copy", "q4_k_m": "the 4-bit copy",
                  "rerun": "the original run again"}  # fmt: skip
# the precision of the rung's fidelity reference (FI-1), as a reason names the original
_REFERENCE_WORDS = {"bf16": "16-bit", "f16": "16-bit", "f32": "32-bit"}


def tokens(x: float) -> str:
    """A mean count of leading tokens as a reason prints it: three significant digits below 100,
    whole above (29.7, 5.27, 106), never a gratuitous second decimal."""
    if abs(x) >= 100:
        return f"{x:,.0f}"
    if abs(x) >= 10:
        return f"{x:.1f}"
    return f"{x:.3g}"


def control_means(doc: Mapping[str, object]) -> dict[str, tuple[str, float]]:
    """Each stored control with scores: its words (`_CONTROL_WORDS`, by recipe for the rerun)
    and its mean score, by id."""
    out: dict[str, tuple[str, float]] = {}
    for c in doc.get("controls") or ():  # type: ignore[attr-defined]
        found = _scores(c)
        if found is None:
            continue
        cid = str(_m(c).get("id"))
        key = "rerun" if _m(c).get("recipe") == "rerun" else cid
        out[cid] = (_CONTROL_WORDS.get(key, cid), sum(found) / len(found))
    return out


def recheck(doc: Mapping[str, object]) -> dict[str, int]:
    """Spec 1.4, rule 3: each stored threshold is recomputed from its controls' scores with the
    same expression; any difference stops the board. Returns each threshold's score sum
    S_a + S_b, by step key."""
    steps = doc.get("steps")
    if not isinstance(steps, Mapping):
        return {}
    controls = {str(_m(c).get("id")): _m(c) for c in doc.get("controls") or ()}  # type: ignore[attr-defined]
    totals: dict[str, int] = {}
    for key, name in _THRESHOLD_NAMES:
        threshold = _m(steps.get(key))
        stored = threshold.get("value")
        if stored is None:
            continue
        ids = threshold.get("controls")
        found = [_scores(controls.get(str(i))) for i in ids] if isinstance(ids, list) else []
        if len(found) != 2 or found[0] is None or found[1] is None or (
                len(found[0]) != len(found[1])):  # fmt: skip
            raise IProofsError(ErrorKind.CONFIG, f"fidelity.json {name} {stored}, its controls "
                               "give no value")  # fmt: skip
        a, b = found[0], found[1]
        computed = (sum(a) + sum(b)) / (2 * len(a))
        if computed != stored:
            raise IProofsError(
                ErrorKind.CONFIG, f"fidelity.json {name} {stored}, its controls give {computed}"
            )
        totals[key] = sum(a) + sum(b)
    return totals


def _tie_step_tests(
    steps: Mapping[str, object],
    tests: Mapping[str, object],
    scores: Sequence[int],
    totals: Mapping[str, int],
    system: str,
) -> None:
    """F5: each stored step test is the test of the row's scores over its stored threshold: its
    threshold name, value and n match, and an exact test's p is counted again. A mismatch
    stops the board (rule 3)."""
    n = len(scores)
    for key, name in _THRESHOLD_NAMES:
        found = tests.get(key)
        if found is None:
            continue
        stored = _m(found)
        value = _m(steps.get(key)).get("value")
        where = f"fidelity.json {system} step test {key}"
        if stored.get("threshold") != name or stored.get("value") != value or (
                stored.get("n") != n):  # fmt: skip
            raise IProofsError(ErrorKind.CONFIG, f"{where} is for {stored.get('threshold')} = "
                               f"{stored.get('value')} over n = {stored.get('n')}, the stored "
                               f"step is {name} = {value} over n = {n}")  # fmt: skip
        if stored.get("method") == "exact" and key in totals:
            diffs = [2 * n * s - totals[key] for s in scores]
            p = sign_flip_p(diffs, exact_up_to=n, resamples=1, seed=0)
            if p != stored.get("p"):
                raise IProofsError(ErrorKind.CONFIG, f"{where} has p = {stored.get('p')}, the "
                                   f"scores give {p}")  # fmt: skip


def _alpha(doc: Mapping[str, object], level_alpha: float | None) -> float:
    """F5: the stored test's alpha, which equals the level's `fidelity.alpha` when it is given;
    never a default."""
    found = _m(doc.get("test")).get("alpha")
    if not isinstance(found, int | float) or isinstance(found, bool):
        raise IProofsError(ErrorKind.CONFIG, "fidelity.json stores step tests but no test alpha")
    if level_alpha is not None and float(found) != float(level_alpha):
        raise IProofsError(ErrorKind.CONFIG, f"fidelity.json alpha {found}, the level's "
                           f"fidelity.alpha is {level_alpha}")  # fmt: skip
    return float(found)


def faithful_model(  # noqa: PLR0911, PLR0912 (one return per line of the table)
    fidelity_state: str,
    fidelity_cause: str | None,
    doc: Mapping[str, object] | None,
    system: str,
    policy: str | None,
    level_alpha: float | None = None,
    reference: str | None = None,
) -> Petal:
    """FM-1 to FM-7 (basis test throughout). The step tests are read from `doc`, never run; an
    exact one is counted again to tie it to the stored threshold (F5). `reference` is the
    precision of the rung's fidelity reference (FI-1), which the reason names."""
    pid = "faithful_model"

    def petal(step: str | None, reason: str, cause: str | None = None) -> Petal:
        return Petal(pid, step, cause, TEST, reason)

    if fidelity_state == "failed":  # FM-1
        return Petal(pid, RED, CHECK_FAILED, TEST,
                     "the rung's bar scores above the row's replies",
                     lowered_by=("fidelity",))  # fmt: skip
    if doc is None:  # FM-2
        return petal(None, "no fidelity record stored for the rung", NOT_DECIDED)
    if fidelity_state != "held":
        return petal(None, f"the Fidelity check is undecided: {fidelity_cause or 'no cause'}",
                     NOT_DECIDED)  # fmt: skip
    row = _m(_m(doc.get("rows")).get(system))
    scores = _scores(row)
    if scores is None:
        return petal(None, "no fidelity scores stored for the row", NOT_DECIDED)
    totals = recheck(doc)
    if policy != EXACT_MATCH:  # FM-3
        return petal(
            AMBER_LOWER,
            f"the claim's policy is {policy}, not exact match"
            if policy is not None
            else "no claim card found, so exact match is not shown",
        )
    steps, tests = doc.get("steps"), row.get("step_tests")
    if not isinstance(steps, Mapping) or not isinstance(tests, Mapping):  # FM-4
        return petal(AMBER_LOWER, "no step tests stored for the rung")
    _tie_step_tests(steps, tests, scores, totals, system)
    for key, _ in _THRESHOLD_NAMES:  # FM-4 (F1): a control missing or failed
        threshold = _m(steps.get(key))
        if threshold.get("value") is None:
            cause = threshold.get("cause") or "no value stored"
            return petal(AMBER_LOWER, f"the {_LINE_WORDS[key]} midpoint has no value ({cause}), "
                         "and the steps above need it")  # fmt: skip
    g, u = _m(tests.get("green")), _m(tests.get("upper"))
    if not g or not u:  # FM-4
        return petal(AMBER_LOWER, "no step tests stored for the rung")
    alpha = _alpha(doc, level_alpha)
    pg, vg = float(g["p"]), float(g["value"])  # type: ignore[arg-type]
    pu, vu = float(u["p"]), float(u["value"])  # type: ignore[arg-type]
    # FM (amended 2026-11-15): the row's own mean first, then each midpoint with its two
    # controls' means, in FI-3's unit; the p values, alpha and n stay in fidelity.json
    means = control_means(doc)
    original = f"the {_REFERENCE_WORDS[reference]} original" if reference in _REFERENCE_WORDS \
        else "the original"  # fmt: skip
    lead = f"{tokens(sum(scores) / len(scores))} leading reply tokens match {original}, on average"

    def pair(key: str) -> str:
        ids = _m(steps.get(key)).get("controls")
        found = [means.get(str(i)) for i in ids] if isinstance(ids, list) else []
        return ", ".join(f"{m[0]} {tokens(m[1])}" for m in found if m is not None)

    def mid(key: str, value: float) -> str:
        return f"the midpoint of {pair(key)}, {tokens(value)}"

    green_shown, upper_shown = pg < alpha, pu < alpha
    slots = doc.get("slots")
    if green_shown and slots == 1:  # FM-5 (F2)
        return petal(GREEN, f"{lead}; shown above {mid('green', vg)}")
    had = "no slot count is stored" if slots is None else f"the run had {slots} slots"
    if upper_shown:  # FM-6 (F3)
        if green_shown:
            return petal(AMBER_UPPER, f"{lead}; shown above {mid('green', vg)}, but {had} and "
                         "green needs 1")  # fmt: skip
        return petal(AMBER_UPPER, f"{lead}; shown above {mid('upper', vu)}; not above "
                     f"{mid('green', vg)}")  # fmt: skip
    if green_shown:  # FM-7 (F4)
        return petal(AMBER_LOWER, f"{lead}; shown above {mid('green', vg)}, not above "
                     f"{mid('upper', vu)}, and {had}")  # fmt: skip
    return petal(AMBER_LOWER, f"{lead}; {pair('upper')}; not shown above their midpoint, "
                 f"{tokens(vu)}")  # FM-7  # fmt: skip


def glyph(petals: Mapping[str, Petal]) -> list[dict[str, object]]:
    """The five petals in drawing order (no field sums them, GL-8)."""
    return [petals[p].tree() for p in PETALS]


# ---------------------------------------------------------------- offline checks (GL-1, GL-9)


def _all_quotes(tree: object) -> list[Quote]:
    """Every quote of a properties file, wherever it sits."""
    out: list[Quote] = []
    if isinstance(tree, Mapping):
        for k, v in tree.items():
            if k == "quotes" and isinstance(v, list):
                out += [q for q in v if isinstance(q, Mapping)]
            else:
                out += _all_quotes(v)
    elif isinstance(tree, list):
        for v in tree:
            out += _all_quotes(v)
    return out


# U1: the exponent t of each 2^-t, 2^(-t) and /2^t in a stated bound
_EXPONENT = re.compile(
    r"2\s*(?:\^|\*\*)\s*[{(]?\s*[-\u2212]\s*(\d+)"
    r"|/\s*2\s*(?:\^|\*\*)\s*[{(]?\s*(\d+)"
    r"|2\s*<sup>\s*[-\u2212]\s*(\d+)\s*</sup>"
)


def properties_problems(  # noqa: PLR0912 (one branch per offline rule of spec 1.2)
    doc: Mapping[str, object], system_dir: Path, system_pin: str | None
) -> list[str]:
    """What the properties/2 schema cannot check (spec 1.2): the pin, the directory, the quote
    urls, and that the expression, terms, trusted base and axioms are copied from the quotes."""
    problems: list[str] = []
    upstream = _m(doc.get("upstream"))
    repo, pin = str(upstream.get("repo")), str(upstream.get("commit"))
    if system_pin is not None and pin != system_pin:
        problems.append(f"read at {pin}, system.yaml pins {system_pin}")
    if doc.get("system") != system_dir.name:
        problems.append(f"system {doc.get('system')!r} is not the directory {system_dir.name!r}")
    prefix = f"https://github.com/{repo}/blob/{pin}/"
    for q in _all_quotes(doc.get("petals")):
        if not str(q.get("url")).startswith(prefix):
            problems.append(f"quote url {q.get('url')} is not under {prefix}")
    petals = _m(doc.get("petals"))
    bound = _m(_m(petals.get("unforgeable")).get("bound"))
    expr = _v(bound.get("expression"))
    if isinstance(expr, str):
        texts = [str(q.get("text")) for q in _quotes(bound.get("expression"))]
        if not any(expr in t for t in texts):
            problems.append(f"expression {expr!r} is in none of its quotes")
        raw = bound.get("terms")
        terms = [int(t) for t in raw] if isinstance(raw, list) else []
        exps = [int(next(g for g in m if g)) for m in _EXPONENT.findall(expr)]
        if exps and sorted(set(exps)) != sorted(set(terms)):  # U1: both ways
            problems.append(f"expression exponents {exps} differ from terms {terms}")
        whole = sorted({int(x) for x in re.findall(r"\d+", expr)})
        if not exps and terms and whole != sorted(set(terms)):  # no 2^-t form: both ways too
            problems.append(f"numbers {whole} in the expression differ from terms {terms}")
    formal = _m(_m(petals.get("machine_checked")).get("formal"))
    url = formal.get("theorem_url")
    if url is not None and not str(url).startswith(prefix):
        problems.append(f"theorem_url {url} is not under {prefix}")
    base = _v(formal.get("trusted_base"))
    base_items = [str(i) for i in base] if isinstance(base, list) else []
    texts = [str(q.get("text")) for q in _quotes(formal.get("trusted_base"))]
    for item in base_items:
        if not any(item in t for t in texts):
            problems.append(f"trusted_base item {item!r} is in none of its quotes")
    axioms = formal.get("axioms")
    for a in axioms if isinstance(axioms, list) else []:
        if str(a) not in base_items:
            problems.append(f"axiom {a!r} is not in trusted_base")
    # amended 2026-11-15: a printed fact's words are copied from one of its quotes
    named = _m(doc.get("verifiers"))
    card = _m(formal.get("scope_card"))
    copied = [(f"verifiers.{k}", _m(named.get(k))) for k in ("run", "stated")]
    copied += [(f"scope_card.{r}.bound", _m(_m(card.get(r)).get("bound"))) for r in SCOPE_ROWS]
    for where, fact in copied:
        words = _v(fact)
        texts = [str(q.get("text")).lower() for q in _quotes(fact)]
        if words and not any(str(words).lower() in t for t in texts):
            problems.append(f"{where} {words!r} is in none of its quotes")
    hiding = _m(_m(petals.get("weights_hidden")).get("hiding"))
    for form in _forms(hiding):
        first = _quotes(form)[:1]
        if not first or str(form.get("item")) not in str(first[0].get("text")):
            problems.append(f"form {form.get('item')!r} is not in its first quote")
    return problems


def not_read_rows(board: Mapping[str, object]) -> list[str]:
    """GL-9: every petal of the board that is hollow because its properties file is not read."""
    out = []
    for rung in board.get("rungs") or ():  # type: ignore[attr-defined]
        for row in _m(rung).get("rows") or ():  # type: ignore[attr-defined]
            for p in _m(row).get("glyph") or ():  # type: ignore[attr-defined]
                if _m(p).get("state") == HOLLOW and _m(p).get("cause") == NOT_READ:
                    out.append(f"{_m(rung).get('id')}/{_m(row).get('system')}: "
                               f"{_m(p).get('id')} not read")  # fmt: skip
    return out
