# Benchmark release

Use this checklist to cut a benchmark release (`v<release>`), following [docs/spec/09-release-and-versioning.md §Release checklists](../spec/09-release-and-versioning.md#release-checklists). Complete the steps in order; if any step fails, stop the release until it is resolved. Each item links to the governing RFC section.

1. Record the RFC commit hash in `release.yaml` ([RFC-0009 §Release record](../../rfcs/0009-results-and-publication.md#release-record)).
2. Merge the reference file with the GPU price, pricing date, and pinned driver, CUDA, and runtime versions ([RFC-0006 §Reference file](../../rfcs/0006-reference-hardware-and-cost.md#reference-file), [RFC-0006 §Cost basis](../../rfcs/0006-reference-hardware-and-cost.md#cost-basis)).
3. Merge all run records. Confirm that every run is either eligible or explicitly listed as ineligible with its reason ([RFC-0014 §Eligibility](../../rfcs/0014-provenance-and-integrity.md#eligibility)).
4. List all claim cards by digest in the release record ([RFC-0002 §Claim class](../../rfcs/0002-claim-card.md#claim-class), [RFC-0009 §Release record](../../rfcs/0009-results-and-publication.md#release-record)).
5. Write the release report using [reports/TEMPLATE.md](../../reports/TEMPLATE.md) ([RFC-0009 §Reports](../../rfcs/0009-results-and-publication.md#reports)).
6. Run `iproofs release freeze`, merge `index.json`, and tag that commit as `v<release>` ([RFC-0009 §Freeze algorithm](../../rfcs/0009-results-and-publication.md#freeze-algorithm)).
7. Run `iproofs site build` to generate `web/` from the frozen release, then publish the site from the tagged commit ([RFC-0009 §Site](../../rfcs/0009-results-and-publication.md#site)).
