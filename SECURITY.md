# Security policy

This policy covers two types of private reports: vulnerabilities in this project's own codebase, and cases where a measured system's verifier accepts a tampered input. Neither should be disclosed in a public issue or pull request.

## Reporting channel

Submit reports privately through the hosting platform's private vulnerability reporting feature for this repository ("Report a vulnerability" on the Security tab).

## Vulnerabilities in this project

This covers the harness (`harness/`), the test systems (`systems/fake`, `systems/fake-broken`), the CI workflows, and the site generator. Examples include a container escape path, path traversal through adapter output, a secret or host identifier leaking into a run directory, or a way to bypass a validation gate.

- Maintainers aim to acknowledge reports within 7 days (this is a target, not a guarantee).
- Once resolved, maintainers publish a fix alongside an advisory.
- If a vulnerability could have affected published numbers, it is documented in the next release report under "what failed" along with the affected runs ([docs/spec/06-security.md §Harness vulnerabilities](docs/spec/06-security.md#harness-vulnerabilities)).

Vulnerabilities in a measured prover itself fall under that upstream project's security policy.

## A verifier that accepts a tampered input

If a negative control whose expected outcomes exclude `accept` is accepted on a real system, it indicates a potential soundness issue or adapter bug ([RFC-0008 §Disclosure](rfcs/0008-negative-controls.md#disclosure), [docs/spec/06-security.md §Accepted controls](docs/spec/06-security.md#accepted-controls-a6)).

1. Do not open a public pull request with that run. Report it privately to the system's maintainers using their published security channel (or another private upstream contact if they have no security policy), and also notify the benchmark maintainers through the channel above.
2. Follow the upstream system's embargo policy. If the project has none, the embargo lasts 90 days from the report date or until upstream publishes a fix or advisory, whichever comes first.
3. Once the embargo ends, the run is published in full with the outcome shown in the row.
4. The run is never discarded, and the result is never softened.

Before reporting a finding against a system, verify that the issue is not in the adapter itself. A bug in this repository's verdict mapping is fixed here and the run is repeated; it is not reported as a defect in the upstream system.
