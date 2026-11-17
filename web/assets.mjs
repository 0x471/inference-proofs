// Deployment assets only; committed JSON keeps RFC-0012's canonical serialization.
import { build } from 'esbuild';
import { readFileSync, writeFileSync } from 'node:fs';

await build({
  entryPoints: ['words.css', 'words.js'], outdir: 'public',
  minify: true, legalComments: 'none',
});
writeFileSync('public/search.json', JSON.stringify(JSON.parse(readFileSync('search.json', 'utf8'))));
