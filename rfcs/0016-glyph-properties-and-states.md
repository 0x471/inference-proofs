# RFC-0016: Glyph properties and states

- Authors: 0xchqrles
- Created: 2026-11-07
- Requires: RFC-0002, RFC-0008, RFC-0009, RFC-0012, RFC-0013, RFC-0015
- Superseded for Level 1 by RFC-0018 (2026-11-10): this RFC's properties and states no longer drive the site, and `web/_data/criteria.json` was initially retained as the v0.1 record (amended 2026-11-15: deleted on 2026-11-15 because it carried RFC-0016's vocabulary, such as Formally verified "yes" from documents, which no page reads; the v0.1 record remains in git history at `b9dfa3e`). The Level 1 glyph uses RFC-0018's five petals computed from facts copied into `systems/<name>/properties.yaml` and lowered by failed checks under RFC-0018 GL-2, while the six checks act as the entry gate rather than the glyph. RFC-0018 brings back ST-5 (one fact, one petal) and INV-GLYPH-1 (nothing to add up) as GL-6 and GL-8 (amendment of 2026-11-13).

## Summary

The v0.1 public site represents every row as a six-part glyph covering six properties (Weights hidden, Model bound, Whole output checked, Formally verified, Security level, and No trusted party), each taking one of four states printed as Yes, Partly, No, or Not stated. This RFC defines the rules behind those states recorded in `web/_data/criteria.json`.

The benchmark validates claims rather than auditing them. On a claim-card row, a state means three things at once: the system states the property at its pinned commit, the claim applies to the exact configuration the benchmark runs (including its verifier), and the benchmark's negative controls (RFC-0008) do not contradict it. On a reference row, a state describes the benchmark's own method (SRC-5); on a public-source row, it reflects what the authors publicly state without any benchmark run behind it (INV-GLYPH-5). No state is an audit of cryptographic soundness or zero knowledge, a probability that a property holds, or a benchmark-assigned security level.

This RFC specifies each property's exact question, scope limits, state rules, and applicable controls; establishes a single unordered four-state vocabulary with no scores, sums, counts, or property numbers; defines allowed sources for each row class (claim-card, reference, and public-source rows); requires card rows to match their card configuration and cite only the pinned commit; defines the mechanical override rule by which an unexpectedly accepted RFC-0008 control forces a stated Yes or Partly cell to No regardless of documentation; specifies archival requirements for web quotes from a system's own authors; and defines the JSON Schema contract (`schema: "criteria/1"`) that validates the criteria file.

## Motivation

At repository commit `356949a5ee8afe328ee2cb0d68b18be1b1d82453`, the prototype criteria pipeline had several concrete gaps:

- Neither an RFC nor `docs/spec/` formally defined the six glyph properties.
- States were entered manually via an external script (`generated_by: prototypes/v7/_data/make_site_data.py`). `web/build.py` never read claim cards, checking only that `glyph.rows[*].states` matched `criteria.json`'s `test_mapping` (L41 to L44). Nothing checked states against `systems/flashprove/claim.yaml` or `systems/sash/claim.yaml`, and `criteria.json` had no `schema` field or RFC-0013 §G2 validation glob.
- Several prototype rules violated AGENTS.md rule 9 ("Do not infer security properties"): `states.red.meaning` included "or the design rules it out", Weights hidden No included "or the design gives the checker the weights", and No trusted party No read "The check is a hardware attestation verified against a chip maker's keys", inferring from check type rather than documentation.
- FlashProve's Formally verified and Security level cells were copied from statements made for its Lean verifier `verify`, even though FlashProve's claim card targets the C++ verifier `cp_verify` and explicitly states neither property is claimed for it (`systems/flashprove/claim.yaml` L22 and L26 to L37).
- Owner decisions remained unresolved in `risks`: R1 (capping public-source rows), R2 (publications outside the pin), and R6 (fixed public parameters as trusted inputs).
- Two conflicting vocabularies coexisted: `green`, `amber`, `red`, `grey` with labels "holds", "partly", "does not hold", and "not stated" in `criteria.json`, versus Yes, Partly, No, and Not stated in `glyph.inks.ladder`.
- Sourcing had large gaps (counted in [Migration / Rollout](#migration--rollout)): 13 non-grey cells on public-source rows relied solely on unarchived web links without retrieval dates or stored copies, and 65 Not stated cells listed no sources read (53 simply saying "Not copied yet."). SASH's Whole output proved was set to Yes using `sg-ai-safety-hub/zk-inference-results`, a repository excluded by SASH's own claim card (`systems/sash/claim.yaml` L5 to L6, INV-CLAIM-3).
- Derived values were hand-typed rather than computed: `quote_check` stored a hardcoded count (77 quotes: 71 in cells, 4 in `aside`, 2 in `outside_pin`) with no automated check against drift.
- Nothing connected the glyph to benchmark test outcomes. Even though RFC-0008 runs tampering controls against every system's verifier and logs outcomes in `controls.json`, a row could still display Yes on Whole output checked after its verifier accepted a mutated output token (C1).

For these properties, the benchmark plays a role similar to L2BEAT for rollups: it validates documented claims rather than certifying systems. Each state rests on three verifiable layers: documentation at the pinned commit (Not stated where silent, RFC-0002), alignment with the exact configuration executed (including the verifier, SRC-1), and absence of contradictions from negative controls ([Negative control override](#negative-control-override)). Readers can check every layer directly from stored files without asking the benchmark to audit cryptographic proofs or code, which is explicitly out of scope ([PRD §5](../docs/PRD.md#5-non-goals): "it does not audit soundness proofs or code").

Concrete scenarios this RFC addresses:

1. A reader seeing Not stated for SASH and Partly for FlashProve on Weights hidden must understand that Not stated means the pinned documentation is silent, not that SASH hides more.
2. When a reviewer sets a public-source cell to Yes from an author's blog post, future readers need to inspect the exact text as it appeared on the retrieval date even if the live page later changes.
3. If a claim card updates `zero_knowledge.claimed` to `false`, the glyph cannot continue showing Yes.
4. Readers must not be given numbers or fill areas that invite summing six properties across rows.
5. If a card claims Whole output checked Yes but the release's verifier accepts C1 (a modified output token), the glyph must flip to No and the system page must show the quote, control, and run side by side.

## Goals

- Define clearly what a state means per row class: for claim-card rows, stated at the pin for the benchmarked configuration and uncontradicted by negative controls; for reference rows, describing the benchmark's own method (SRC-5); for public-source rows, stated by the authors without benchmark runs (INV-GLYPH-5).
- Give every property a clear question, explicit exclusions, written rules for all four states, and the exact list of RFC-0008 controls that can contradict it (or note that none can) ([Properties](#properties)).
- Require every system-row state to come strictly from verbatim quotes of the system's own documentation rather than design inferences (AGENTS.md rule 9), with a single exception: a contradicting negative control outcome overrides a stated Yes or Partly to No (OVR-4). Reference-row states come from RFC-0015 and this RFC.
- Make overrides purely mechanical, derived directly from stored `controls.json` files without reviewer discretion.
- Standardize on one unordered four-state vocabulary with one ID and one display label per state.
- Forbid totals, scores, counts, averages, orderings over states, and numeric labels on properties.
- Specify allowed sources per row class and map claim-card fields to allowed states for card rows.
- Validate the criteria file under gate G2 using the `criteria/1` JSON Schema.

## Non-Goals

- Visual glyph styling (shapes, colours, contrast, slice geometry, or animation). Those belong to the site design (RFC-0009, amended by #319) within INV-GLYPH-1; this RFC fixes only state display words and how silence is presented (ST-2).
- The family taxonomy (`proved`, `re_executed`, `attested`, `fingerprinted`, `unchecked`) and tab assignments.
- Site data generation and build pipeline refactoring (#320, #321).
- Writing claim cards for the 19 systems not yet benchmarked.
- Verifying whether a system's documentation is truthful. Like the claim card (RFC-0002 §Non-Goals), the glyph reports what documentation states and whether negative controls contradict it.
- Auditing cryptographic soundness, zero knowledge, formal proofs, or code, estimating failure probabilities, or assigning security levels (INV-GLYPH-3, [PRD §5](../docs/PRD.md#5-non-goals)). A passing control only proves that one specific mutation was rejected (RFC-0008 §Non-Goals) and therefore never raises a state.
- Defining new controls or altering control algorithms and expected outcome sets, which remain owned by RFC-0008.

## Proposed Design

### Terms

- **Glyph**: the six-part figure drawn for each row on the site.
- **Property**: one of the six questions defined below, identified by its ID.
- **Cell**: a single property of one row, containing a state, a short reason, and either supporting quotes or a list of sources consulted.
- **Deciding quote**: the verbatim quote that determines a cell's state; additional quotes provide supporting context only.
- **Row class**: `claim_card_at_pin` (a system with a claim card), `reference_rfc_0015` (a benchmark reference row), or `public_sources` (a system not yet benchmarked).
- **Own source**: a repository, domain, or published paper belonging to the system's own authors, listed on a public-source row ([SRC-8](#public-source-rows-public_sources)).
- **Stated state**: the state determined by a cell's quotes under ST-1 through ST-8 prior to any negative-control override. When no override applies, it equals the cell's final state.
- **Contradicting outcome**: a control mapped to a property by the [control map](#negative-control-override) whose stored `controls.json` record shows `accepted` even though `accepted` is not in its expected outcome set (OVR-3).
- **Overridden cell**: a card-row cell whose stated state is `yes` or `partly` and that has at least one contradicting outcome, forcing its final state to `no` (OVR-4).

### What the glyph is not

- INV-GLYPH-1. There is no total, score, rank, count, sum, or average over states, across properties, or across rows. No page, file, or report may compute one. The criteria file contains no key named `total`, `score`, `rank`, `count`, `sum`, `average`, `mean`, or `weight`. Visual designs must distinguish states by ink or pattern rather than additive fill areas; specific shapes belong to the site (#319).
- INV-GLYPH-2. Properties carry no numbers. The `order` array defines clockwise display order only, never priority or weight. The criteria file contains no number-typed values anywhere, and the site generator (#320) prints none: `iproofs.site.view` omits property numbers, and the prototype snapshot containing `glyph.properties[].n`, `glyph.key.numbers`, and numbered `aria` labels (`web/_data/` at `39662bf6`) is retired.
- INV-GLYPH-3. Security level records only whether a numeric bound is stated and whether documentation calls it proven. It never computes, compares, or assigns its own level; the level itself stays a verbatim quote in the claim card (RFC-0002 `security.level`, rejecting benchmark-assigned levels in RFC-0002 §Alternatives Considered).
- INV-GLYPH-4. Rows are never sorted by glyph states. Row ordering is governed by site rules (RFC-0009).
- INV-GLYPH-5. Every state is a validated claim rather than a certificate. On a card row, it means stated at the pin (SRC-2) for the benchmarked configuration (SRC-1, OVR-5) and uncontradicted by negative controls (OVR-4); before the first release, card rows reflect pinned statements with no runs yet (OVR-5). On a public-source row, it means stated by the authors (SRC-8) without benchmark runs. On a reference row, it describes the benchmark's own method (SRC-5). No state represents an audit, probability of correctness, or benchmark-assigned security level (§Non-Goals). The overview renders states alone, while quotes, sources, and control outcomes live on each system page (OVR-7).

### States

One shared four-state vocabulary is used across both the criteria file and every web page. The four states are unordered: none is ranked above another, and no rule compares states except ST-8 within a single conflicting cell. Overrides introduce no extra state; overridden cells take `no` (OVR-4).

| Id | Printed word | Meaning | Replaces |
|---|---|---|---|
| `yes` | Yes | The documentation says the property holds under the property's Yes rule, and no control contradicts it. | `green`, "holds" |
| `partly` | Partly | The documentation says the property holds with a stated limit under the property's Partly rule, and no control contradicts it. | `amber`, "partly" |
| `no` | No | The documentation says the property does not hold under the property's No rule, or a negative control contradicts a stated Yes or Partly (OVR-4). | `red`, "does not hold" |
| `not_stated` | Not stated | The sources read say nothing matching the three rules above, or they have not yet been read ([Q2](#decisions)). | `grey`, "not stated" |

Universal state rules:

- ST-1. A cell's stated state is `yes`, `partly`, or `no` only when a verbatim deciding quote from an allowed source ([Sources by row class](#sources-by-row-class)) satisfies that state's rule for the property (reference rows follow SRC-5 instead). The cell's final state equals its stated state unless overridden to `no` on a card row (OVR-4).
- ST-2. Silence is recorded as `not_stated`, never `no`, alongside a list of the sources consulted. Contradicting controls do not alter a `not_stated` cell (OVR-4, [Q5](#decisions)). On the site, `not_stated` renders visually and textually as No while its reason notes that the property is not stated: an unstated guarantee cannot be relied upon and must not appear gentler than a stated No (owner decision, 2026-11-10, after grey and half-red treatments read as softer than No). The underlying record preserves `not_stated` so future publisher statements cleanly replace it.
- ST-3. A stated `no` requires an explicit statement that the property does not hold. Design inferences, product categories ("runs in an enclave"), or absent features do not qualify; every prototype "or the design rules it out" clause is removed (AGENTS.md rule 9). The sole non-documentation path to `no` on a card row is a contradicting control recorded by the harness (OVR-4), which reflects an observed verifier outcome rather than a design inference.
- ST-4. On reference rows only, a method that neither proves nor checks outputs (plain serving) takes `no` across all six properties, while a method that checks without proving (recompute) takes `no` on Formally verified and Security level (SRC-7). On card and public-source rows, stating that a system does not prove outputs sets `no` only on properties whose own No rule the quote satisfies.
- ST-5. Each stated limitation counts in exactly one cell. If a limitation counted in one cell is relevant context for another, it is shown beside the second cell as an `aside` without affecting its state (for example, FlashProve's clipped-gap policy counts under Model bound, and its single leaked bit counts under Weights hidden).
- ST-6. Trust assumptions and caveats shared by every row (the verifier's own computer, compiler, and build, as well as which real-world model a commitment corresponds to) do not alter any state and are documented in prose. Every cell is evaluated strictly for the row's own configuration (SRC-1), never another configuration of the same system.
- ST-7. Fixed public parameters chosen before hashing are common to all non-interactive proofs; they set `partly` on No trusted party only when the documentation explicitly excludes a provider who tuned them from its proved statement ([Q1](#decisions)).
- ST-8. When two quotes from allowed sources satisfy rules for different states, both quotes are recorded, the cell sets `conflict: true` with a reason noting the conflict, and its stated state follows this precedence table ([Q4](#decisions)): `yes` + `partly` yields `partly`; `yes` + `no` or `partly` + `no` yields `no`. The quote corresponding to the resulting state becomes the deciding quote. This table resolves conflicts strictly inside a single cell and is never applied across cells or rows; OVR-4 then runs on the resulting stated state.

### Properties

The six properties in clockwise display order are `weights_hidden`, `model_bound`, `whole_output`, `formally_verified`, `security_level`, and `no_trusted_party`. Every rule below is satisfied solely by explicit documentation statements (ST-1, ST-3). Each property's "Controls" line identifies which RFC-0008 controls can contradict it ([control map](#negative-control-override)); properties with no mapped controls are documentation-only, meaning their card-row states reflect pinned claims for the run configuration without experimental testing.

#### Weights hidden (`weights_hidden`)

- Question: does the checker learn nothing about the weights?
- Not covered: hiding weights from the host operator (for example via an enclave) is outside this property.
- Yes: the documentation states that weights stay hidden from the checker under default use, naming no leakage beyond public settings.
- Partly: the documentation states that weights are hidden subject to an explicit limit: a named leak, hiding established only for one policy or setting, optional per-circuit hiding, or commitment-based hiding without formal zero knowledge.
- No: the documentation states that the checker sees the weights, or that hiding is disabled or unsupported. The prototype phrase "or the design gives the checker the weights" is removed; recompute's No rests on RFC-0015's explicit statement that its verifier holds the weights.
- Not stated: the sources read make no statement about hiding weights from the checker.
- Controls: none (documentation only). RFC-0008 controls only inspect verifier verdicts and prover failures, never information leaked about weights.

#### Model bound (`model_bound`)

- Question: is each checked token tied to the committed weights?
- Not covered: identifying which real-world named model a commitment represents. Both FlashProve and SASH place this outside their proofs; it is explained in prose.
- Yes: the documentation states that a passing check binds every checked token exactly to the committed weights under the row's configuration (the card configuration for card rows, or default/expected use for public-source rows).
- Partly: bound with an explicit limit, such as under only one of several policies, within a numeric tolerance or error bound, or demonstrated solely via empirical tests.
- No: the documentation states that outputs are not bound to any weights, or that nothing is checked.
- Not stated: silent.
- Controls: C3, P1, and P2 (OVR-2). Each mutates the weights, weight commitment, or precision named in this property's Yes rule; accepting such a mutation contradicts binding to the committed weights under the control map, though this mapping is a rule of this RFC rather than something an outcome uniquely proves ([Q9](#decisions)).

#### Whole output checked (`whole_output`)

- Question: does one check cover every output token of a request?
- Name: renamed from the prototype's "Whole output proved" because the question covers what a check verifies and reference rows prove nothing (AGENTS.md rule 10). The ID remains `whole_output`.
- Not covered: deployment choices about which requests are checked (such as sampling or post-hoc proving), as well as text before tokenization and after detokenization (placed outside both FlashProve's and SASH's proofs and noted in prose).
- Yes: the documentation states that one check, or one joined set of checks, covers the prompt and every output token of a request.
- Partly: a check covers only a stated subset, such as client-selected positions, a single segment, or one disputed step.
- No: the documentation states that no output tokens are checked, or that nothing is checked.
- Not stated: silent, including proved runs whose covered output tokens are left unnamed.
- Controls: C1, C2, C4, and C7 (OVR-2). Each alters the request, prompt, or claimed output named in this property's Yes rule; accepting such a mutation contradicts full request coverage under the control map ([Q9](#decisions)).

#### Formally verified (`formally_verified`)

- Question: is the security argument for the row's configuration checked by a proof assistant?
- Not covered: formal verification of the implementation code itself, which no row claims (stated in prose). Claims applying only to a different configuration of the same system (such as a different verifier, RFC-0002 §Configuration identity 5) appear as an `aside` and set nothing (ST-6, SRC-1).
- Yes: the documentation states that the soundness of the row's configuration is proved in a proof assistant (Lean, Coq, Isabelle, or similar).
- Partly: machine-checked only for a stated subset, such as a single component or a weaker statement than the system's full claim.
- No: the documentation states that the argument is not machine-checked, that formalization is merely planned, or that soundness relies solely on code review or testing. Reference rows follow ST-4.
- Not stated: silent.
- Controls: none (documentation only). Verifier verdicts cannot tell whether a security argument is machine-checked; any accepted control is printed on the system page and contradicts Model bound or Whole output checked per the control map.

#### Security level (`security_level`)

- Question: is a soundness level stated for the row's configuration, and proven?
- Not covered: the numeric value itself, which lives as a verbatim quote in the claim card (INV-GLYPH-3). Levels stated solely for another configuration of the same system appear as an `aside` and set nothing (ST-6, SRC-1).
- Yes: the documentation states a numeric soundness bound for the row's configuration and states that it is proven (by hand or machine) under named assumptions.
- Partly: a numeric level is stated as conjectured, appears only in code or config files, covers only part of the system, or is stated without specifying whether it is proven or conjectured ([Q10](#decisions)).
- No: the documentation states that the parameters yield no meaningful soundness (for example, test-only settings). Reference rows follow ST-4.
- Not stated: no level is stated for the row's configuration.
- Controls: none (documentation only). Security levels bound forgery probability, whereas RFC-0008 runs a handful of fixed trials (five for C6, RFC-0008 §Alternatives Considered 3) without estimating probabilities (INV-GLYPH-3).

#### No trusted party (`no_trusted_party`)

- Question: does a check hold without trusting a chip maker, a setup ceremony, or an honest party?
- Not covered: trust assumptions shared across all rows (ST-6), and provenance of the weights or commitment (see Model bound).
- Yes: the documentation states that verification relies solely on cryptography or requires no trusted setup, naming no chip maker, setup ceremony, or trusted party.
- Partly: the documentation states a trusted input or condition outside its proved statement: a setup file, public parameters the user must assume were fixed prior to hashing (ST-7), or an honest-party assumption among a group.
- No: the documentation states that verification checks hardware attestation against a chip maker's keys or certificate chain, or trusts the provider. The quote MUST state this dependency explicitly; merely writing "runs in a trusted execution environment" does not suffice (ST-3), replacing the prototype's check-type rule.
- Not stated: silent.
- Controls: none (documentation only). No RFC-0008 control mutates setup files, attestations, or third-party inputs: C3, P1, and P2 perturb weights or precision, while all remaining controls perturb requests, claimed outputs, or proofs.

### Sources by row class

#### Card rows (`claim_card_at_pin`)

- SRC-1. Every card row references exactly one claim card via `card: {system, configuration, card_version}` (RFC-0002 §File and identity). All states apply strictly to that configuration, including its verifier: statements covering only another acceptance policy or verifier (RFC-0002 §Configuration identity 2 and 5) appear as an `aside` and set nothing. A system with multiple cards in a release gets one row per card. This resolves R3: because FlashProve's card targets `exact-match-cp-verify` (issue #69 closed), its cells reflect exact match under the C++ verifier `cp_verify`, and statements about its Lean verifier set no states on this row.
- SRC-2. Every quote on a card row (deciding, supporting, or `aside`) must come verbatim from the card's `upstream.repo` at `upstream.commit`, enforcing AGENTS.md rule 9 ("copy what the system states at the pinned commit") and INV-CLAIM-3. Its `sources_read` list includes that repository at that commit. This settles SASH's companion repository: `sg-ai-safety-hub/zk-inference-results` cannot set any SASH card-row state because SASH's claim card excludes it (`systems/sash/claim.yaml` L5 to L6), though it may be listed in `sources_read` and `outside_pin`. If RFC-0002 is later amended to allow pinned companion repositories on claim cards, SRC-2 automatically adopts that amendment.
- SRC-3. Statements published by a system's team outside the pinned commit MAY be displayed beside a cell as `outside_pin` (with a reason and quotes, but no state). They never determine a cell's state and are never rendered in the glyph or in state inks. This resolves R2 under AGENTS.md rule 9 so the glyph and its claim card always agree; SASH can be invited to document such claims inside its main repository (#42).
- SRC-4. A reviewer determines each card row's stated states from verbatim quotes, constrained by the claim-card fields listed below. Whenever the card narrows the allowed set to a single state, the cell's stated state MUST match it ([Q3](#decisions)). OVR-4 runs afterward and is not constrained by the claim card.

Claim-card fields consulted per property (RFC-0002 §Fields). Card values not listed in the third column permit all four states.

| Property | Card fields read | States the card allows | Derivable from the card alone |
|---|---|---|---|
| Weights hidden | `zero_knowledge.claimed`, `.hidden`, `.not_hidden`, `.status`; `sources.zero_knowledge*` | `claimed: "not stated"` allows {`not_stated`}; `claimed: false` allows {`partly`, `no`} | Partly: Not stated is; choosing between `partly` and `no` requires reading the quote under property rules, and choosing between `yes` and `partly` requires reading `not_hidden` |
| Model bound | `relation`, `coverage.policy.kind`, `coverage.policy.detail`, `binding`, `claim_class` | `policy.kind: tolerance` allows {`partly`, `no`}; `policy.kind: not_stated` with `binding: "not stated"` allows {`not_stated`} | Partly |
| Whole output checked | `coverage.unit`, `coverage.tokens_covered`, `coverage.phase`, `relation` | none (`tokens_covered` is free text) | No |
| Formally verified | `relation_formal`, `security.notion.kind`, `security.notion.verifier`; `sources.security.notion*` | `relation_formal: "not stated"` allows {`partly`, `no`, `not_stated`} | No: only `yes` is ruled out |
| Security level | `security.level`, `security.notion.kind`, `security.notion.verifier`, `security.model` | `level: "not stated"` allows {`not_stated`} | Partly: Not stated is; distinguishing proven from conjectured and confirming configuration applicability requires reading `level` text |
| No trusted party | `security.setup`, `assumptions`, `assumptions_not_stated`, `security.model.assumption` | `setup: trusted` allows {`partly`, `no`}; `setup: not_stated` with `assumptions_not_stated: true` allows {`not_stated`} | Partly |

Reviewers must inspect every listed field, not just the most obvious one: for FlashProve, No trusted party is governed by the third entry in `assumptions` (`systems/flashprove/claim.yaml` L72 to L75, "Configuration files fixed before the hash function is drawn") even though `security.setup` reads `not_stated` (L43). Likewise, whenever a free-text field notes that a claim does not cover the card's configuration (such as FlashProve's `security.level`: "Not claimed for `cp_verify`"), SRC-1 rules out `yes` during review.

RISK: Whole output checked cannot be mechanically constrained from claim-card fields, and Formally verified is constrained only by `relation_formal`, creating a risk of stale cells after card edits. Mitigation: every card-row quote pins the card's commit and version, so updating to a new pin (creating a new card under RFC-0002 §Configuration identity 1) requires re-reading all cells. A future RFC-0002 amendment MAY add an explicit structured field for machine-checked soundness.

#### Reference rows (`reference_rfc_0015`)

- SRC-5. Reference rows document the benchmark's own baselines rather than proving systems and have no claim cards (RFC-0015 §Reference systems: "they prove nothing"). Their states are defined normatively by RFC-0015 together with the table below. Where RFC-0015 has no verbatim sentence matching a state rule word-for-word (for instance, plain serving checks nothing, and a local rerun trusts no outside party), the cell's reason begins with "By definition:" and cites the supporting RFC-0015 text. Every quote comes from `rfcs/0015-reference-rows.md` at a full commit hash. Any edit to RFC-0015 that alters a reference state or moves a quoted sentence MUST update this table and its quotes in the same pull request.
- SRC-6. Each reference row names the `workloads` whose configuration it reflects, describing the method documented in RFC-0015 rather than an empirical measurement. The table below assumes no precision substitution; a recompute row whose workloads declare a precision substitution (RFC-0015 PM-2, PM-4) takes `partly` on Model bound because the rerun uses a different precision from the workload, and all workloads grouped into a single row must agree on whether a substitution is declared. Currently, `systems/ref-recompute/system.yaml` declares a substitution for both SASH workloads (FP8 W8A8 for INT8 W8A8, RFC-0015 Q1 and PM-4) and none for the two Maverick workloads, so the single recompute row in `criteria.json` covers the Maverick workloads displayed on the site and keeps Yes. Displaying a SASH recompute row will require its own row with `partly` on Model bound. Configurations flagged `not_measurable_on_profile` (RFC-0015 NM-1) retain their method states while displaying the NM-1 reason (settling R8).

| Property | Plain serving (`ref-serve`) | Recompute (`ref-recompute`) | Deciding RFC-0015 text (supporting text) |
|---|---|---|---|
| Weights hidden | No (ST-4) | No | plain serving: §Reference systems L45 "they prove nothing" (§Summary L13); recompute: §Recompute L82 "A verifier holding the weights checks a claimed output by running the model itself." |
| Model bound | No (ST-4) | Yes; Partly with a declared substitution (SRC-6) | plain serving: §Reference systems L45 (SRV-4 L77, outputs not compared); recompute: PM-0 L102 (RC-3 L86, each claimed position compared with the argmax; ties follow the engine's stated rule) |
| Whole output checked | No (ST-4) | Yes | plain serving: §Reference systems L45 (§Summary L13); recompute: RC-3 L86, one forward pass over prompt plus every claimed output token (RC-7 L98) |
| Formally verified | No (ST-4) | No (ST-4) | §Reference systems L45 "they prove nothing" (plain serving: §Summary L13) |
| Security level | No (ST-4) | No (ST-4) | §Reference systems L45 "they prove nothing" (plain serving: §Summary L13) |
| No trusted party | No (ST-4) | Yes, by definition | plain serving: §Reference systems L45 (§Summary L13); recompute: §Recompute L82, the checker reruns the model itself and trusts no other party beyond ST-6 |

- SRC-7. On reference rows, `no` on Formally verified and Security level means "no security argument, by definition" (stated in the cell's reason), and `no` across all properties for plain serving means "by definition: nothing is checked" (RFC-0015 §Summary, SRV-4). No fifth "does not apply" state is introduced (settling R14 in favour of one four-state vocabulary).

#### Public-source rows (`public_sources`)

- SRC-8. Public-source states must rest on quotes published by the system's own authors: a repository at a full commit hash, a published paper, or documentation/blog pages on a domain controlled by the team. Each row declares these in `own_sources` (repositories, domains, or author-published URLs) with a note explaining how each was verified. Only own sources may provide deciding quotes; third-party coverage (press, surveys, or outside blogs) may appear only in `sources_read` or `aside` and never sets a state (AGENTS.md rule 9). Public-source rows are visually separated from card and reference rows and never appear in the benchmarked tab; exact visual markers (such as the prototype's pencil icon) belong to the site (#319).
- SRC-9. Instead of a commit hash, every web quote MUST include its `url`, a `retrieved` date (`"YYYY-MM-DD"`, RFC-0012), and either an `archive_url` (a public web archive snapshot captured on or after the retrieval date) or a `copy` (a repository file path holding the archived text along with its SHA-256). Web quotes lacking these fields cannot set a state.
- SRC-10. Public-source rows are not capped below Yes. This settles R1 under AGENTS.md rule 9: capping them would display Partly even when documentation states no limitation, injecting a benchmark opinion instead of reporting the source. The difference in depth of review is communicated instead by separating public-source rows (SRC-8) and archiving quoted web pages (SRC-9).

### Negative control override

This mechanism provides the third verification layer for card-row states (INV-GLYPH-5). RFC-0008 runs shared controls C1 through C8, P1, P2, and any registered system-specific controls against each benchmarked configuration's verifier and logs outcomes in `controls.json`. Overrides flow strictly in one direction: a recorded control failure can contradict a stated property, whereas passing controls never confirm or upgrade one.

- OVR-1. Overrides apply exclusively to card rows. Reference systems run no controls (RFC-0015 §Reference systems: "no controls"), and public-source rows have no benchmark runs.
- OVR-2. Each control can contradict only the property assigned in the normative control map below. Any addition or change to RFC-0008 controls updates this table in the same pull request, enforced by `test_control_map_matches_rfc`. Each control maps to the property whose Yes rule governs the mutated input: mutations to the request, prompt, or claimed output (C1, C2, C4, C7) map to Whole output checked; mutations to weights, weight commitments, or precision (C3, P1, P2) map to Model bound; and raw proof-byte corruptions (C5, C6, C8) map to none. This mapping is a deterministic rule of this RFC rather than an inference about root cause (for instance, an accepted C1 could also stem from unbound weights); keeping a single property per control keeps the override purely mechanical ([Q9](#decisions)).

| Control (RFC-0008) | Mutation | Property it can contradict | Why |
|---|---|---|---|
| C1 | change the claimed output token | Whole output checked | the check accepted a claimed output it was not made for; the changed input is an output token |
| C2 | change one prompt token in the request | Whole output checked | the check accepted a request it was not made for; the changed input is a prompt token, which the Yes rule covers |
| C3 | verify against the commitment of perturbed weights | Model bound | the check accepted a proof against a commitment it was not made for; the changed input is the weights' commitment |
| C4 | replay a valid proof for a different request | Whole output checked | the check accepted a request and output it was not made for; the changed input is the request |
| C5 | truncate the proof's largest part | none | see below |
| C6 | flip one bit in a part, 5 seeds | none | see below |
| C7 | swap the proofs of two requests in one batch | Whole output checked | as C4, inside one batch; the changed input is the request each proof is checked for |
| C8 | drop one part of the proof | none | see below |
| P1 | commit W, prove with W' | Model bound | the check accepted a proof made from weights other than the committed ones; the changed input is the weights |
| P2 | prove with a precision other than the committed one | Model bound | the check accepted a proof made at a precision other than the committed one; the changed input is the precision |
| system-specific (`fixture_proof`, `weakened_prover`) | registered in `systems/<name>/controls.yaml` | none ([Q7](#decisions)) | `system-controls/1` names no property, and a `weakened_prover` control expects `accepted` |

C5, C6, and C8 corrupt raw proof bytes rather than changing any input named in a property's Yes rule. If a verifier accepts a corrupted proof, we know it accepted altered bytes, but not which semantic property failed (for instance, a flipped bit might lie in unused padding); assigning it to a specific property would be an inference violating AGENTS.md rule 9. Their outcomes still appear on the system page (OVR-7), and any unexpected acceptance triggers disclosure (RFC-0008 §Disclosure). Weights hidden, Formally verified, Security level, and No trusted party have no mapped controls and remain documentation-only for the reasons stated in their property definitions.

- OVR-3. A control contradicts a property only when its stored record logs `accepted` (either as the control's top-level `outcome` or inside any of its `trials`) while `accepted` is absent from its `expected` set. No other outcome contradicts or raises a state:
  - `rejected` (plus `invalid_call` or `prover_failed` when listed in `expected`): control passed. Passing confirms only that one mutation was rejected (RFC-0008 §Non-Goals) and never raises a state, so `not_stated` remains `not_stated`.
  - `no_verdict`, or an unexpected `invalid_call` (such as on C1): the control failed inconclusively without accepting anything, so it never lowers a state.
  - `void` (honest twin not accepted, INV-CTRL-2), `not_applicable`, and `error`: nothing was tested, so no state changes.
  - not run: a control missing from `controls.json`, a run lacking `controls.json`, or an upstream example documented in an adapter README but not registered (RFC-0008 Q4; registered `fixture_proof` controls record `not_applicable`, RFC-0008 Q5). Never raises or lowers a state.
  All outcomes are printed verbatim on the system page (OVR-7).
- OVR-4. Any card-row cell whose stated state is `yes` or `partly` and that has at least one contradicting outcome from a mapped control takes the state `no`, regardless of documentation. The cell retains its deciding quotes (still validated against ST-1, ST-8, and the card-fields table), stores the original stated state in `stated`, and lists each contradicting `(control, run_id)` pair in `contradicted_by`. Cells whose stated state is already `no` or `not_stated` stay unchanged: `no` already reflects absence, and `not_stated` makes no claim to contradict ([Q5](#decisions)). Overriding to `no` is chosen over showing a side note or adding a fifth state because the overview draws states alone (leaving Yes or Partly visible after an accepted tampering check would violate INV-GLYPH-5), `no` directly reflects the measured breach, and a fifth state was already rejected in SRC-7. No information is lost because the system page prints the stated state and its quotes right beside the contradicting control.
- OVR-5. Overrides are computed per configuration and per release. The criteria file specifies its target `release`. For each card row, the read runs include all runs listed in `releases/<r>/release.yaml` `runs` for that release and every earlier release (ordered by release ID) whose `run.json` `claim.system` and `claim.configuration` match the row's `card`, excluding runs listed in any read release's `superseded_runs` or replaced via `replaces` by a read run (RFC-0009 §Append-only rule and corrections). When `run.json` has a null `claim` (as in v0.1 runs written before the runner copied claims into `run.json`), `manifest.json` `claim` is read instead (the field checked against release `claim_cards` digests under RFC-0014). This yields six consequences:
  - When `release` is set, every card row represents a benchmarked configuration whose `card` system and configuration appear in a read `release.yaml`'s `claim_cards` with at least one read run; otherwise the pull request removes the row or adds the run (INV-GLYPH-5).
  - Contradictions persist across later releases of the same configuration. A later passing run does not erase a contradiction because the accepted mutation is reproducible from its seed (INV-CTRL-3).
  - Editing a claim card at the same pin (bumping `card_version`) does not clear a contradiction. Moving to a new pin or changing any other attribute in RFC-0002 §Configuration identity creates a new configuration and card row that starts clean with its own runs.
  - A correction run that replaces the contradicting run clears the override (for example, if RFC-0008 §Disclosure uncovers an adapter verdict-mapping bug).
  - Releases never read runs from future releases, and published releases are never edited retroactively (RFC-0009).
  - A criteria file without `release` reads no runs and applies no overrides.
- OVR-6. Only a qualifying run under OVR-5 (a correction run or a run of a new configuration) can change an overridden cell.
- OVR-7. The overview renders each cell's final state alone. For every cell, the system page prints the stated state, its quotes, and its `sources_read`; for overridden cells, every `contradicted_by` entry (control ID and run ID) linked to `controls.json`; and for every mapped control, its recorded outcome across every read run (including passed, inconclusive, void, not applicable, error, and "not run" when absent). For properties with no mapped controls, the page explicitly notes that no RFC-0008 control tests them. The site derives these lists at build time from the control map and stored `controls.json` files so `criteria.json` stores only `stated` and `contradicted_by` derived directly from stored records (AGENTS.md rule 3).

### Criteria file contract

`web/_data/criteria.json` is authored JSON formatted in RFC-0012 canonical style (G3 `FMT-1`), validated against `schema/criteria/1.schema.json` (`$id`: `https://inference-proofs.org/schema/criteria/1.schema.json`, Draft 2020-12, requiring `"schema": {"const": "criteria/1"}`).

RFC-0012 §Schema catalogue entry added by the implementing pull request:

| Name | File | Kind | Path of instances | Owner RFC |
|---|---|---|---|---|
| `criteria` | `schema/criteria/1.schema.json` | authored JSON | `web/_data/criteria.json` | RFC-0016 |

`web/_data/criteria.json` is added to RFC-0013 §G2 inputs (and `G2_GLOBS` in `harness/src/iproofs/validate/tree.py`).

Document shape (all objects set `additionalProperties: false`; `Text` is a non-empty string; `{}` mirrors `yes`; `Quote` is described below):

```json
{
  "schema": "criteria/1",
  "rfc": "RFC-0016",
  "date": "YYYY-MM-DD",
  "release": "v0.1",
  "note": "Text",
  "order": ["weights_hidden", "model_bound", "whole_output", "formally_verified", "security_level", "no_trusted_party"],
  "states": {"yes": {"word": "Yes", "meaning": "Text"}, "partly": {}, "no": {}, "not_stated": {}},
  "properties": [
    {"id": "weights_hidden", "name": "Weights hidden", "question": "Text", "not_here": "Text",
     "rules": {"yes": "Text", "partly": "Text", "no": "Text", "not_stated": "Text"},
     "card_fields": ["zero_knowledge.claimed", "zero_knowledge.hidden"]}
  ],
  "pins": {"owner/repo": "<40-hex>"},
  "rows": [
    {"id": "sash", "name": "Text", "family": "proved", "tab": "benchmarked",
     "source_class": "claim_card_at_pin",
     "card": {"system": "sash", "configuration": "sound-defaults", "card_version": "1"},

     "cells": {"weights_hidden": {"state": "not_stated", "reason": "Text", "quotes": [],
                                  "sources_read": [{"repo": "owner/repo", "commit": "<40-hex>", "paths": ["README.md"]}],
                                  "note": "Text", "conflict": false,
                                  "aside": {"words": "Text", "quotes": ["Quote"]},
                                  "outside_pin": {"reason": "Text", "quotes": ["Quote"]}},
               "whole_output": {"state": "no", "stated": "yes", "reason": "Text", "quotes": ["Quote"],
                                "contradicted_by": [{"control": "C1", "run_id": "<run-id>"}]}}},
    {"id": "ref-recompute", "source_class": "reference_rfc_0015", "tab": "benchmarked",
     "workloads": ["fp-maverick-w1024-b1", "fp-maverick-w1024-b24"], "cells": {}},
    {"id": "tinfoil", "source_class": "public_sources", "tab": "not_benchmarked",
     "own_sources": [{"domain": "docs.tinfoil.sh", "how": "Text"}, {"repo": "owner/repo", "how": "Text"}], "cells": {}}
  ]
}
```

- `card_version` is encoded as a numeric string because `criteria.json` forbids number-typed values (INV-GLYPH-2); its value matches the card's integer version.
- `rfc` names this RFC.
- Quotes come in three kinds (`repository`, `this_repository`, and `web`). All carry `kind`, verbatim `text`, `label`, `decides` (boolean), `checked: true`, and `checked_how` (`Text`). `repository` and `this_repository` (replacing prototype `ours`) add `repo`, 40-hex `commit`, `path`, `lines` (`^L[0-9]+(-L[0-9]+)?$`), and `url` (containing `commit`). `web` adds `url`, `retrieved`, and either `archive_url` or `copy: {path, sha256}`, omitting `repo`, `commit`, `path`, and `lines`. Quotes inside `aside` and `outside_pin` set `decides: false`.
- `aside` (`{words, quotes}`) holds notes printed beside a cell for limits counted elsewhere (ST-5) or claims about other configurations (SRC-1) without affecting state, merging the prototype's `aside.quote` and `aside.also` into `aside.quotes`.
- `outside_pin` (`{reason, quotes}`) appears on card rows only and carries no `state` (SRC-3).
- `release` (optional) names the target release directory `releases/<release>/` containing a `release.yaml` (OVR-5). Omitted before the first frozen release, in which case no runs are read and no cells are overridden.
- `stated` and `contradicted_by` appear together (or not at all) on card rows only (OVR-4). `stated` is `yes` or `partly`, forcing `state` to `no`. `contradicted_by` is a non-empty, duplicate-free array of `{control, run_id}` sorted by `control` then `run_id`, where `control` maps to the property in the [control map](#negative-control-override) and `run_id` is an RFC-0012 run ID. Values are derived strictly from stored `controls.json` files and never hand-edited to disagree.
- `conflict` is `true` only on cells resolved under ST-8 and omitted otherwise.
- `sources_read` entries take `{repo, commit, paths}` (paths or globs consulted) for repositories or `{url, retrieved}` for web pages.
- `not_copied: true` MAY stand in for `sources_read` on a `not_stated` public-source cell that has not yet been reviewed ([Q2](#decisions)).
- `workloads` (required on reference rows) lists workload IDs from the reference system's `system.yaml` (SRC-6). `own_sources` (required and non-empty on public-source rows) lists entries with `how` plus one of `repo`, `domain`, or `url` (SRC-8).
- Keys dropped from the prototype: `test_mapping`, `rows[].states`, and `rows[].pencil` (all derived from cells and `source_class`); `quote_check` (unverified hand-typed count); `contrast` and `states.*.fill`/`.ink`/`.mark` (presentation styling owned by `web/words.css`); `status`; `this_repository_commit` (moved into `pins`); `rules` and `risks` (now normative text and dispositions in this RFC); `outside_pin.state` (SRC-3); and null repository keys on web quotes.

### Data flow and lifecycle

1. Reviewers edit `web/_data/criteria.json` via pull request, citing sources at the commits permitted by each row class.
2. `iproofs validate` enforces schema gate G2 and formatting gate G3.
3. Any claim-card update (new `card_version`) triggers a re-read of that row to match the new version; any RFC-0015 edit moving a quoted sentence updates the reference table and quotes in tandem.
4. When freezing a release (RFC-0009 §Freeze algorithm), the site-build pull request sets `release` and populates every `stated` and `contradicted_by` entry mandated by OVR-3 through OVR-5. Later corrections (OVR-5) update the file in the subsequent release's pull request.
5. `web/build.py` reads cell states directly and pins the file's SHA-256 in the site footer.

Determinism: override resolution reads exclusively from `criteria.json` plus `release.yaml`, `run.json`, and `controls.json` for the named releases, using release IDs for ordering with no clock or network access.

### Failure modes

| Failure | Response |
|---|---|
| A coloured cell lacks a deciding quote | caught in review |
| A quote uses a short or unpinned commit | schema rejects short commits; review catches unpinned commits |
| A quoted web page changes or disappears later | `archive_url` or `copy` preserves the quoted text until a reviewer re-reads the page |
| A web quote lacks both archive and copy | caught in review; cell reverts to `not_stated` with URL in `sources_read`, or adds an archive |
| A deciding quote comes from a third-party page | caught in review; quote moves to `sources_read` or `aside` |
| A Not stated cell records nothing | caught in review |
| A card-row quote cites a different repository or commit | caught in review; quote moves to `outside_pin` or is replaced from the pin |
| A card-row state cites another configuration of the system | caught in review (SRC-1) against the card-fields table |
| A claim-card change contradicts a cell (e.g., `zero_knowledge.claimed` becomes `false` while cell stays `yes`) | caught in review against the card-fields table |
| RFC-0015 edits invalidate a reference quote | quote, commit, and (if needed) the reference table are updated together (SRC-5) |
| A reviewer's inference is used as a deciding quote | caught in review (ST-3); quotes must be the system's own words |
| A score, count, or number is added to `criteria.json` | schema rejects it (`additionalProperties`) |
| A stated Yes remains after a mapped control was accepted in a read run | pull request is blocked until cell flips to `no` with `stated` and `contradicted_by` |
| An override is manually added, kept, or dropped in conflict with stored runs (missing record, superseded/replaced run, wrong configuration, or future release) | caught in review |
| A Not stated cell is flipped to `no` by an accepted control | caught in review (OVR-4, Q5); outcome prints on the system page instead |
| An override is applied to Weights hidden, Formally verified, Security level, or No trusted party, or triggered by C5, C6, C8, or a system-specific control | caught in review (OVR-2) |
| A card row has no run for its configuration in the release | caught in review (OVR-5); row is removed or the run is added |
| A system team disputes an overridden cell | cell changes only via a correction run or a new configuration |
| A release run directory or `controls.json` is missing from the tree | caught in review |

## Alternatives Considered

- **Retain design-inference clauses ("or the design rules it out").** Tempting when a design obviously precludes a property (such as recompute holding weights), but rejected because it makes the benchmark assert properties the system did not state, violating AGENTS.md rule 9. Every real case in the dataset already has an explicit document quote (recompute's rests on RFC-0015).
- **Evaluate Formally verified and Security level at the protocol level regardless of the verifier run.** Rejected because RFC-0002 §Configuration identity 5 makes the verifier part of configuration identity whenever verifiers carry different security claims. Applying FlashProve's Lean-verifier claims to its `cp_verify` card row would contradict the card itself (SRC-1).
- **Derive all card-row states automatically from claim-card fields.** Attractive because CI could recompute the entire glyph without reviewer judgment, but rejected as the default ([Q3](#decisions)) because Whole output checked has no structured field to derive from, Formally verified can only rule out `yes`, and distinguishing Yes from Partly on three properties requires reading free text. Allowed-state sets automate what can be derived safely.
- **Cap public-source rows at Partly (R1).** Rejected under AGENTS.md rule 9 (SRC-10).
- **Allow outside-pin publications or companion repositories to set card-row states (R2, SASH).** Rejected under AGENTS.md rule 9 and INV-CLAIM-3 (SRC-2, SRC-3), leaving open a future RFC-0002 amendment for pinned companion repositories.
- **Keep the label "Whole output proved".** Rejected because reference rows prove nothing and attested checks are not proofs; calling them "proved: Yes" misuses terminology (AGENTS.md rule 10). "Checked" applies accurately across every row.
- **Add a fifth "does not apply" state for reference rows (R14).** Rejected to preserve a single four-state vocabulary; `no` paired with "no security argument, by definition" conveys the same meaning.
- **Compute a per-row score or count of Yes cells.** Rejected because the benchmark measures rather than ranking across unlike properties ([PRD §5](../docs/PRD.md#5-non-goals)), and a count would treat six distinct properties as equal.
- **Display benchmark-assigned security levels on the glyph.** Rejected per RFC-0002 §Alternatives Considered as out-of-scope certification that hides exact assumptions.
- **Accept unarchived web URLs from any site.** Rejected because web pages change and third-party commentary is not system documentation.
- **Audit properties directly via human or AI reviewers.** Rejected because certification is a non-goal ([PRD §5](../docs/PRD.md#5-non-goals)), violates AGENTS.md rule 9, cannot be recomputed from stored files, and exceeds the benchmark team's mandate. Instead, the benchmark checks documentation, configuration match, and negative controls, publishing all underlying evidence.
- **Drop the glyph and show measured numbers only.** Rejected because systems prove vastly different statements ("Inference proofs make different statements, so the claim has to travel with every number", [PRD §2](../docs/PRD.md#2-vision)), and comparing raw headlines without claim context misleads readers ([PRD §1](../docs/PRD.md#1-problem)).
- **Display contradictions as a note beside the stated state.** Rejected under OVR-4 because the overview displays states alone, which would leave Yes visible on a configuration whose verifier accepted a mutated input.
- **Add a fifth "Contradicted" state.** Rejected to keep one four-state vocabulary (SRC-7); `no` with `contradicted_by` accurately reflects the measured outcome.
- **Allow passing controls to raise states or confirm Yes.** Rejected because a passing control only proves one mutation was rejected (RFC-0008 §Non-Goals), never certifying the property (OVR-3).
- **Map C5, C6, and C8 to Model bound and Whole output checked.** Rejected because an accepted corrupted proof does not identify which semantic property failed, making any mapping an inference (OVR-2).
- **Clear contradictions when a later run rejects the control.** Rejected because the accepted mutation remains reproducible from its seed (INV-CTRL-3), and clearing on a later pass would invite cherry-picking (OVR-5). Only a documented correction run replacing the contradicting run clears it.
- **Relocate `criteria.json` out of `web/` (e.g. to `methodology/criteria.json`).** Deferred to avoid churn while `web/build.py` and the footer depend on its current path; #320 MAY relocate it alongside the generator refactor.

## Drawbacks

- Re-reading documentation whenever claim cards or web sources update requires ongoing reviewer effort.
- Detailed systems often collect Partly cells while silent systems show Not stated (R1, R11). This RFC preserves that fidelity to source text, placing the burden on the site to clarify that Not stated does not mean better than Partly.
- Requiring explicit statements for No and scoping card rows strictly to their run configuration moves several cells to Not stated (see [Migration / Rollout](#migration--rollout)), showing fewer filled states than a design-based reading would.
- Reference-row states defined "by definition" where RFC-0015 lacks a literal sentence require readers to trust the project's specification of its own baselines.
- Card-row states remain reviewer-authored with no automated semantic check beyond the schema and card-fields table.
- Negative controls cover only two of the six properties; Weights hidden, Formally verified, Security level, and No trusted party remain purely documentation-based, as disclosed on every system page (OVR-7).
- Overrides are one-directional and coarse: passing controls check only a few seeded mutations (RFC-0008 §Drawbacks), while an accepted control forces No even when documentation describes a tolerance or subset policy that might cover the mutation (Q6).

## Conflicts of Interest

This RFC was drafted with Claude, an AI assistant built by Anthropic, which publishes FlashProve (`anthropics/FlashProve`), one of the two systems with a claim-card row. Reviewers should scrutinize decisions affecting FlashProve with that context in mind, especially SRC-1 on R3 (evaluating FlashProve strictly under `exact-match-cp-verify`, which removes Yes from Formally verified and Security level where the prototype cited the Lean verifier) and ST-7/Q1 on R6. The control map (OVR-2) and Q5 through Q9 apply uniformly to all card rows; Model bound and Whole output checked are testable for both FlashProve and SASH, and SASH's registered controls are the ones left unmapped by Q7.

## Migration / Rollout

This specification shipped across two pull requests (issue #318). The first added the RFC and index entries. The second added the `criteria/1` schema and examples, the validator's control map, `harness/tests/unit/test_criteria.py`, the RFC-0012 catalogue entry, and the RFC-0013 G2 input; migrated `web/_data/criteria.json` to `criteria/1` (updating keys, quote types, `sources_read`, `workloads`, and `own_sources`); updated `web/README.md` and `docs/spec/10-glossary.md` (the six properties and four states); rebuilt the site; and listed every changed state and edited cell in its pull-request description.

Counts in the original committed file (SHA-256 prefix `4ced468b` at `356949a5ee8afe328ee2cb0d68b18be1b1d82453`) were verified with:

```sh
python3 -I -c 'import json;d=json.load(open("web/_data/criteria.json"));c=[(r,c) for r in d["rows"] for c in r["cells"].values()];print(sum(1 for r,x in c if x["state"]!="grey" and x["quotes"] and all(q["kind"]=="web" for q in x["quotes"])), sum(1 for r,x in c if x["state"]=="grey" and not x.get("searched")))'
```

That command prints `13 65`. Across 138 total cells (23 rows × 6 properties): card rows held 4 Yes, 5 Partly, and 3 Not stated; reference rows held 3 Yes and 9 No; and public-source rows held 14 Yes, 7 Partly, 3 No, and 90 Not stated.

Dispositions of the prototype's open risks:

| Risk | Disposition |
|---|---|
| R1 cap public-source rows | settled by SRC-10 (AGENTS.md rule 9): no cap |
| R2 publication outside the pin | settled by SRC-3 (AGENTS.md rule 9, INV-CLAIM-3): shown beside the cell with no state, sets nothing |
| R3 FlashProve Model bound by policy | settled by SRC-1 (state evaluated per card configuration, verifier included) |
| R4 one Lean fact, two cells | superseded on the FlashProve row by SRC-1 (item 5); the two property rules remain distinct (a hand-proved bound earns Yes on Security level without earning Yes on Formally verified) |
| R5 SASH "conjectured" | kept: uses SASH's own wording |
| R6 fixed public parameters | Q1, default option (b) (ST-7) |
| R7 plain serving No on Weights hidden | kept: ST-4 and SRC-7, reason reads "By definition: no checker, so nothing to hide from" |
| R8 recompute by configuration | settled by SRC-6 (`workloads`, one row per substitution case) |
| R9 FlashProve short replies | kept: reason states the limit |
| R10 zkPyTorch product page | re-read in the second pull request (item 6) and verified against `own_sources` (item 2) |
| R11 mostly Not stated rows | accepted: reflects what the sources state |
| R12 inks | out of scope: site drawing (#319), subject to INV-GLYPH-1 |
| R13 VerInf | re-read in the second pull request (item 6) |
| R14 recompute has no argument | settled by ST-4 and SRC-7 |

No claim cards changed, and no schemas changed version beyond introducing `criteria/1`.

## Testing Strategy

Schema fixtures in `schema/criteria/examples/` (each invalid fixture paired with a `.reason` file):

- `valid/committed-shape.json`: one card row, one reference row, and one public-source row matching the committed file shape with `aside` and `outside_pin`; passes.
- `valid/not-copied.json`: a public-source `not_stated` cell with `not_copied: true`; passes.
- `valid/web-quote-archived.json`: a Yes cell decided by a web quote carrying `retrieved` and `archive_url`; passes.
- `valid/overridden-cell.json`: a card row with `release` and a Whole output checked cell carrying `state: "no"`, `stated: "yes"`, and one `contradicted_by` entry; passes.
- `invalid/state-outside-four.json`: `state: "green"`; rejected by enum.
- `invalid/property-number.json`: `"n": 1` on a property; rejected by `additionalProperties`.
- `invalid/total-key.json`: top-level `total`; rejected by `additionalProperties`.
- `invalid/score-key.json`: row-level `score`; rejected by `additionalProperties`.
- `invalid/web-quote-no-retrieved.json`: web quote missing `retrieved`; rejected by `required`.
- `invalid/short-commit.json`: repository quote with `commit: "9e2bdd8f"`; rejected by pattern.
- `invalid/missing-rule.json`: property `rules` missing `not_stated`; rejected by `required`.
- `invalid/outside-pin-state.json`: `outside_pin` containing `state`; rejected by `additionalProperties`.
- `invalid/reference-no-workloads.json`: reference row missing `workloads`; rejected by `required`.
- `invalid/stated-not-stated.json`: `stated: "not_stated"`; rejected by enum.
- `invalid/contradicted-by-empty.json`: `contradicted_by: []`; rejected by `minItems`.
- `invalid/contradicted-by-trial-number.json`: `contradicted_by` entry with `"trial": 0`; rejected by `additionalProperties`.

Repository verification: `uv run iproofs validate --all` validates both the schema and all examples.

## Decisions

- Q1. Fixed public parameters chosen before hashing set Partly on No trusted party only when documentation explicitly states that its proved statement excludes a provider who tuned them (ST-7, R6), rather than treating them as a generic prose caveat. This directly mirrors explicit source text ("that you grant", FlashProve `guide/what-is-proved.md` L288 to L289 at `9e2bdd8f`) instead of erasing a stated caveat. The trade-off is that a system stating this condition receives Partly while a silent system receives Not stated; the reason text explains this, and other teams are encouraged to document their assumptions.
- Q2. "Not copied yet" remains state `not_stated` within the four-state vocabulary and adds `not_copied: true` so the data distinguishes unread sources from reviewed silent sources. The printed word stays "Not stated", leaving any UI distinction to the site (#319). Treating both identically in data would falsely imply unread sources were checked, while adding a fifth state was rejected under SRC-7.
- Q3. Card-row states are authored by reviewers from quotes within the allowed sets of the card-fields table (SRC-4) rather than fully derived from claim-card fields, because Whole output checked lacks a structured card field, Formally verified only excludes `yes`, and three properties require interpreting free text.
- Q4. Conflicting quotes from allowed sources resolve deterministically via the ST-8 precedence table (`yes` + `partly` -> `partly`; `yes` + `no` or `partly` + `no` -> `no`), setting `conflict: true` and quoting both. Every resulting state still matches a verbatim system quote without reviewer discretion and never overstates the more qualified claim, whereas picking manually or collapsing to Not stated would either inject subjectivity or hide conflicting statements.
- Q5. Contradicting controls leave `not_stated` cells unchanged (OVR-4), displaying the accepted control alongside the cell on the system page. Because a silent system makes no claim to contradict, forcing `no` would let the benchmark assert an unstated property against AGENTS.md rule 9. Although a silent system with an accepted control displays Not stated where an explicit system displays No, every accepted control is published prominently on both the system page and the Controls page (OVR-7, RFC-0009 §Site, RFC-0008 §Reporting).
- Q6. Overrides still apply even when documentation mentions a limit that might cover the mutation (such as a tolerance policy admitting a one-unit C3 perturbation or a subset check omitting the token C1 alters), with the system page printing the stated limit beside the control (OVR-4). Expected outcome sets belong to RFC-0008 uniformly across systems; letting reviewers decide whether a limit excuses a mutation would break the mechanical nature of overrides when RFC-0008 already flags such acceptances as potential defects.
- Q7. System-specific controls contradict no glyph properties (OVR-2) and are reported on the system page. `system-controls/1` specifies no property, `weakened_prover` controls expect `accepted`, and failures contradict the claim card's binding table rather than a single glyph property. A future RFC-0008 amendment MAY add a pinned upstream property field to `system-controls/1`, and this table will then follow it.
- Q9. OVR-2 maps C1, C2, C4, and C7 solely to Whole output checked, and C3, P1, and P2 solely to Model bound, matching each control to the property whose Yes rule names its mutated input. A single property per control keeps overrides mechanical without diagnosing why a verifier accepted. The trade-off is that an accepted C1, C4, or C7 could also reflect unbound weights without lowering Model bound, avoiding penalizing a second property not uniquely identified by the outcome.
- Q10. A numeric security level stated for the row's configuration without specifying whether it is proven or conjectured maps to Partly. Not stated would hide a published number, while Yes requires documentation stating the level is proven. This case arose when reviewing Attestable's blog post ("uphold 100 bits of security", #336), whose cell note cites this rule.

## References

- [RFC-0002](0002-claim-card.md) §File and identity, §Fields, §Rules (INV-CLAIM-2, INV-CLAIM-3), §Configuration identity, §Alternatives Considered.
- [RFC-0008](0008-negative-controls.md) §Shared controls, verifier side, §Shared controls, prover side, §Honest twins, §Outcomes, §controls.json, §System-specific controls, §Disclosure, §Non-Goals, INV-CTRL-2, INV-CTRL-3.
- [RFC-0009](0009-results-and-publication.md) for the site, §Storage, §Append-only rule and corrections, §Release record; amended for the live site by #319.
- [RFC-0010](0010-harness-runner.md) error kinds (`config`, `integrity`, `environment`).
- [RFC-0012](0012-schemas-and-serialization.md) §Schema catalogue, §The `schema` field, §YAML subset for authored files (dates), §JSON writer.
- [RFC-0013](0013-validation-and-ci.md) §G2 Schema validation, §G3 JSON format check.
- [RFC-0015](0015-reference-rows.md) §Reference systems, §Plain serving, §Recompute, §Precision matching, §Feasibility on the profile.
- AGENTS.md hard rules 3, 9, and 10. [PRD](../docs/PRD.md) §1, §2, and §5.
- `systems/sash/controls.yaml` (`system-controls/1`).
- `web/_data/criteria.json` (prototype criteria, SHA-256 starting `4ced468b`); at `356949a5`, the `glyph` object of the site's data snapshot under `web/_data/`, `web/build.py` L41 to L44, L505 to L523, L912, L969, and L1516 to L1535, and `web/README.md` §Data; since #320, `iproofs.site.inputs.load_criteria`.
- `systems/flashprove/claim.yaml` and `systems/sash/claim.yaml` (card version 1 each); `systems/ref-serve/system.yaml` and `systems/ref-recompute/system.yaml`.
- `.github/workflows/ci.yml` (`validate` job, `fetch-depth: 0`).
- FlashProve at `9e2bdd8ff5bf9c62f18263d7dac189b0400b260c`; SASH `zk-inference-prover` at `eb95bfa887299d1637550228d42086c27cbb2b3b`; SASH `zk-inference-results` at `11decec3c0b62c707618aab5deb82750b355d202`.
- Issues #318 (this RFC), #319, #320, #321, #42, #69.
