# Search and agent discovery

`iproofs site build` generates search metadata, the XML sitemap, `robots.txt`, and `llms.txt` directly from the same rendered pages, with search copy and topic mappings defined in `draw/chrome.py`. Figures, styling, interactive behavior, and share-card images are unaffected. Note that the policy article discusses a hypothetical US-China agreement, and the serving rule specifies NVIDIA H200 hardware.

| Search intent | Destination | Scope |
|---|---|---|
| Provable inference, verifiable inference, LLM benchmarks | `/` | Results within each model rung |
| Proving cost, proof size, verification time | `/scale`, system pages | Recorded figures and their conditions |
| AI verification, model commitments | `/proof-of-inference`, `/how-a-check-works` | What a proof establishes and its limits |
| International AI agreements, AI treaty verification | `/deployment` | Hypothetical agreements, sampling, and trust requirements |
| AI safety and governance | `/deployment`, `/proof-of-inference` | Verification as one technical input; passing checks is not safety certification |
| Zero knowledge, soundness, quantization, fidelity | `/glossary`, `/statement` | Definitions and stated scope |
| Sumcheck, proving a forward pass | `/forward-pass` | Walkthrough of the proved computation |
| US-China AI agreements | `/deployment` | An explicitly hypothetical bilateral deal, not an existing treaty |
| NVIDIA H200 | `/`, `/scale`, `/checks` | The serving baseline GPU; the checks page spells out the manufacturer |
| AI arms race, strategic competition | Content gap | Requires sourced, visible page content before adding these topics to metadata. |

Every indexable page specifies a single canonical URL, matching social metadata, topic entities, a website identity, image metadata, and (on all pages except home) a breadcrumb trail. Structured data includes only topics actually covered on that page, and system descriptions are derived directly from the current board file without inventing treaty endorsements, ratings, or safety claims. Section headings that carry IDs also populate `hasPart` entries and links in the agent guide using the rendered heading text, allowing direct section citations.

The agent guide (`llms.txt`) links every public page along with the repository's specification and level rules. It serves strictly as an optional navigation aid rather than a ranking signal or indexing requirement, pulling its page descriptions from the generated JSON-LD. The sitemap excludes 404 and alias URLs. Retired editorial routes return permanent redirects, while system routes whose targets depend on the active release return temporary redirects.

For performance, the site delivers static HTML, deferred JavaScript, subset font preloads, content-hashed asset URLs, and immutable asset caching. `styles.mjs` runs the pinned `esbuild` version to bundle CSS sections into `styles.json`, and the renderer inlines only the rules each page needs while preserving cascade order, responsive breakpoints, and no-script rendering. Learn and Scale styles are excluded from other pages, and detail styles are omitted from the home page, while shared card typography, chart axes, and glossary previews remain common. The build verifies the CSS source hash recorded in the manifest and halts if it is stale. The Content Security Policy (CSP) allowlists exact inline style hashes rather than permitting arbitrary inline styles. `assets.mjs` also minifies the deployed search index while leaving the committed JSON in RFC-0012's canonical format.

Clean URLs are handled through explicit rewrites. Legacy URLs, `.html` extensions, and trailing slashes redirect straight to their final canonical URL in a single hop rather than relying on automatic normalization. Because Vercel performs its HTTP-to-HTTPS redirect before project routing, requests to the bare HTTP domain still incur that redirect before forwarding to HTTPS `www`; linking directly to the canonical HTTPS `www` URL avoids both hops. Vercel handles response compression and edge caching for static files automatically.

## Verify and publish

Before pushing, run `uv run iproofs site build`, `uv run pytest web -q`, and the full repository validation gates. Whenever you modify CSS, run `npm ci --include=dev --ignore-scripts` and `npm run styles` inside `web/`, then rebuild the site. During deployment, Vercel copies `llms.txt`, `robots.txt`, and `sitemap.xml` into `public/`. After deploying, confirm that public files return HTTP 200, unknown routes return 404, and redirects land directly on their canonical targets. Submit the sitemap through the site owner's Google Search Console and Bing Webmaster Tools accounts, inspect a system page and the deployment page, and monitor impressions and referral traffic. Local checks alone cannot confirm search indexing, traffic growth, or inclusion in AI answers. The local preview server exposes `llms.txt` under the same allowlist as the other discovery files.

References: [Google's AI search guidance](https://developers.google.com/search/docs/appearance/ai-features) and [structured-data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies).
