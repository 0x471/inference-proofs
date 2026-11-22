# Benchmark release v<release>: report

Copy this template to `reports/<release>.md` ([RFC-0009 §Reports](../rfcs/0009-results-and-publication.md#reports)), keeping the sections below in the same order.

Copy every number directly from `index.json`, include its unit, timing scope, grade, and evidence tier, and link back to its row. Do not compute new numbers in the report: if you need an additional ratio, add it to the derivation code first (AGENTS.md rule 3). Write in neutral language throughout (AGENTS.md rule 10).

## What changed since the last release

Summarize methodology changes along with their RFC numbers, any systems or pins added or removed, and updates to workloads, the reference file, or pricing.

## What failed

List failed runs (including exit codes and last output lines) and any unexpected control outcomes, linking each item to its underlying record.

## What the numbers do not show

Document the limitations of these measurements, including every RISK that remains open in the RFCs.
