# Search and agent discovery

`iproofs site build` generates the search metadata, sitemap, robots policy and
`llms.txt` from the same pages. `draw/chrome.py` owns search copy and topic mappings.
Figures, styles, interactions and share-card images remain unchanged. The policy
article includes a hypothetical US-China agreement, and the serving rule names NVIDIA H200.

| Search intent | Destination | Scope |
|---|---|---|
| Provable inference, verifiable inference, LLM benchmarks | `/` | Results within each model rung |
| Proving cost, proof size, verification time | `/scale`, system pages | Recorded figures and their conditions |
| AI verification, model commitments | `/proof-of-inference`, `/how-a-check-works` | What a proof shows and its limits |
| International AI agreements, AI treaty verification | `/deployment` | Hypothetical agreements, sampling and trust requirements |
| AI safety and governance | `/deployment`, `/proof-of-inference` | Verification is one technical input; passing is not safety certification |
| Zero knowledge, soundness, quantization, fidelity | `/glossary`, `/statement` | Definitions and stated scope |
| Sumcheck, proving a forward pass | `/forward-pass` | The explained computation |
| US-China AI agreements | `/deployment` | An explicitly hypothetical bilateral deal, not an existing treaty |
| NVIDIA H200 | `/`, `/scale`, `/checks` | The serving baseline GPU; the checks page spells out the manufacturer |
| AI arms race, strategic competition | Content gap | Add sourced visible coverage before assigning these topics in metadata. |

Each indexable page has one canonical URL, matching social metadata, topic entities,
a website identity, image metadata and (except home) a breadcrumb path. Only topics
covered by a page belong in its structured data. System descriptions still derive
from the current board. There are no invented treaty endorsements, ratings or safety claims.
Section headings with IDs also supply `hasPart` entries and agent-guide links, so
readers can cite a section directly. These links reuse the rendered heading text.

The agent guide links every public page and the repository's specification and
level rules. It is an optional navigation aid, not a ranking signal or an indexing
requirement. Its descriptions come from the generated JSON-LD. The sitemap excludes
404 and alias URLs. Removed editorial routes redirect permanently; system routes
whose destinations depend on the current release redirect temporarily.

Performance retains static HTML, deferred scripts, subset font preloads, hashed
asset URLs and immutable asset caching. `styles.mjs` uses the pinned esbuild to
prepare the existing CSS sections in `styles.json`. The renderer inlines each
page's rules, preserving their cascade, responsive states and no-script rendering.
It omits Learn and Scale sections elsewhere, and the detail section on the home
page. Shared card typography, chart axes and glossary previews stay shared.
The manifest records the CSS source hash; a stale manifest stops the build. The
CSP permits the exact inline style hashes, without allowing arbitrary inline styles.
`assets.mjs` also compacts the deployed search index; committed JSON keeps RFC-0012's format.

Clean routes use explicit rewrites. Legacy, `.html` and trailing-slash addresses
redirect directly to their final canonical route, without an automatic normalization
hop. Vercel's HTTP-to-HTTPS redirect happens before project routing: the HTTP bare
domain still needs that hop followed by its configured redirect to HTTPS `www`.
The canonical HTTPS `www` address avoids both. Vercel already compresses the text
responses and caches the static documents at its edge.

## Verify and publish

Run `uv run iproofs site build`, `uv run pytest web -q` and the repository gates
before pushing. After changing CSS, run `npm ci --include=dev --ignore-scripts` and
`npm run styles` in `web/`, then rebuild the pages. The Vercel build copies
`llms.txt`, robots and sitemap into `public`.
After deployment, check the public files return 200, unknown pages return 404,
and redirects point to their canonical destination. Submit the sitemap through the
site owner's Google Search Console and Bing Webmaster Tools accounts, inspect a
system page and the deployment page, and track impressions and referred visits.
Local checks cannot establish indexing, traffic growth or inclusion in AI answers.
The local preview serves `llms.txt` under the same allowlist as the other discovery files.

References: [Google's AI search guidance](https://developers.google.com/search/docs/appearance/ai-features)
and [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
