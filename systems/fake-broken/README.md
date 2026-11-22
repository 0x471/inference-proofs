# fake-broken

This test system exists specifically to trigger control failures. It is identical to `systems/fake` except for one deliberate bug: `verify` returns `accept` (exit code 0) for every proof, including tampered ones ([RFC-0005 §Reference implementations](../../rfcs/0005-adapter-contract.md#reference-implementations)).

CI runs `fake-broken` through the negative-control suite and asserts that every applicable verifier-side control returns `accepted`. If the suite ever reports a rejection here, the bug is in the controls or the harness rather than the verifier (RFC-0013 §G10). Because an accept-all verifier is a valid benchmark outcome, its run records validate normally, though test systems are never included in a release (`kind: test`).

Its entrypoint delegates directly to `systems/fake/entrypoint` with the accept-all switch enabled, so the prover logic is shared with `systems/fake`. Build the image using `systems/` as the Docker context and the commit pinned in `system.yaml`: `docker build --build-arg IPROOFS_FAKE_UPSTREAM=<commit> -f systems/fake-broken/Dockerfile systems`.
