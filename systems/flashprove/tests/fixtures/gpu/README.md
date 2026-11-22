# FlashProve GPU fixtures

`commit.out.json`, `prove.out.json`, and `verify.out.json` are adapter outputs captured from a single `fp-maverick-w1024-b1` job on a rented H100 SXM (hosted execution, RFC-0006) on 2026-11-05.

- The image was an unpushed development build of `systems/flashprove/Dockerfile` at adapter commit `a03797986cd880e5d54508e200194768f105f8fc`, built in a Docker VM.
- `setup` and `commit` ran through the harness. The fit matched both published digests, and `cp_commit` finished with "complete and can be handed out".
- In that job, `prove` hit the key-directory permission issue fixed in #281. `prove` and `verify` were then run manually against the same commitment using the updated entrypoint from #281, mirroring how the hosted runner invokes them.
- Upstream text lines are preserved exactly as reported by the adapter, with no manual edits.

Release-eligible runs use the pinned image and are stored under `results/`.
