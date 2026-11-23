// Prepare the existing CSS sections for the Python renderer, without a Node runtime at render time.
import { transform } from 'esbuild';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';

const source = readFileSync('words.css', 'utf8');
const sections = [];
for (const part of source.split(/(?=\/\* -{64} )/)) {
  const heading = part.split('\n')[0];
  const scope = heading.includes('the Learn pages:') ? 'learn'
    : heading.includes('the overview page:') ? 'overview'
    : heading.includes('the partners:') ? 'partners'
    : heading.endsWith("a page's sections */") ? 'details' : 'shared';
  const { code } = await transform(part, { loader: 'css', minify: true, legalComments: 'none' });
  sections.push({ css: code.trim(), scope });
}
for (const scope of ['learn', 'overview', 'details', 'partners']) {
  if (sections.filter(s => s.scope === scope).length !== 1) throw new Error(`Missing or duplicate ${scope} CSS section`);
}
writeFileSync('styles.json', JSON.stringify({ sections, source: createHash('sha256').update(source).digest('hex') }, null, 2) + '\n');
