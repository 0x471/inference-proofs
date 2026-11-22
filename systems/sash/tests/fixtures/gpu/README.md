# SASH GPU fixtures

`commit.out.json`, `prove.out.json`, and `verify.out.json` are adapter outputs captured from a single `sash-l31-8b-c1024` job on a rented H100 SXM (hosted execution, RFC-0006) on 2026-11-05.

- The image was an unpushed development build of `systems/sash/Dockerfile` at adapter commit `9c07cd84ffa6675ed13e507cbf00ba444fd3c6f8`, built in a Docker VM.
- `commit` ran through the harness.
- The initial `prove` step hit the issues later fixed in #283 (crate file permissions) and #289 (program path mapping). `prove` and `verify` were then run manually against the same commitment using the updated entrypoint from `main`, mirroring how the hosted runner invokes them.
- `prove.out.json` lists all 1,639 part files from the single grid; the part files themselves (42 GB) are not stored here.
- Upstream text lines are preserved exactly as reported by the adapter, with no manual edits.

Release-eligible runs use the pinned image and are stored under `results/`.
