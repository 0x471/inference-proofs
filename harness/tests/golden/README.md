# Golden files

| File | Inputs |
|---|---|
| `corpus-window-v1-seed0-count3-L8.jsonl` | Output of `corpus_window_v1` over `fixtures/prompts/corpus-a.txt` followed by `corpus-b.txt` (read as text and joined by a single LF), using the toy tokenizer `fixtures/prompts/tokenizer.json` with count 3, length 8, and seed 0. |
| `index/v0.1.json` | Output of `iproofs release freeze v0.1` over `fixtures/release_tree.py` `build(root)` (5 runs: 3 eligible, 1 dirty, and 1 superseded). Regenerate with `uv run pytest --update-golden` whenever the harness version or index format changes. |
| `site/**` | Output of `iproofs site build` over `fixtures/placeholder_release.py` `build_placeholder(root, extras=True)` after running `iproofs release freeze v0.1` (covering the deployed placeholder release plus test-only cases: a pending disclosure, an override, a second workload and card, an ineligible run, a withdrawn run, a failed run, an unexpected control, a target, and a reply). Includes generated build outputs (`*.html`, `search.json`, `vercel.json`, `og/*.html`, `og/icon.svg`), excluding copied static assets (`words.css`, `words.js`, fonts, and images). Regenerate with `uv run pytest harness/tests/golden/test_site_golden.py --update-golden` when the renderer, view, placeholder release, or a static asset's hash changes, and explain the diff in the pull request. |

The prompt-set golden file is only updated alongside a new generator version (RFC-0003 rule 4).
