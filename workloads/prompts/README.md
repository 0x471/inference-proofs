# Prompt corpus

`corpus.yaml` lists the source texts used by every v0.1 workload to generate prompts (RFC-0003 §Prompt corpus). Because the `corpus-window/1` generator samples windows at seeded offsets across the concatenated corpus, a given prompt can come from any of these texts.

## The texts

| Id | Title | Author | First published | Gutenberg release |
|---|---|---|---|---|
| `gutenberg-1342` | Pride and Prejudice | Jane Austen | 1813 | eBook #1342 |
| `gutenberg-2701` | Moby Dick; Or, The Whale | Herman Melville | 1851 | eBook #2701 |
| `gutenberg-84` | Frankenstein; or, The Modern Prometheus | Mary Wollstonecraft Shelley | 1818 | eBook #84 |
| `gutenberg-11` | Alice's Adventures in Wonderland | Lewis Carroll | 1865 | eBook #11 |
| `gutenberg-1661` | The Adventures of Sherlock Holmes | Arthur Conan Doyle | 1892 | eBook #1661 |
| `gutenberg-98` | A Tale of Two Cities | Charles Dickens | 1859 | eBook #98 |
| `gutenberg-74` | The Adventures of Tom Sawyer | Mark Twain | 1876 | eBook #74 |
| `gutenberg-345` | Dracula | Bram Stoker | 1897 | eBook #345 |

## Why these

- **Licence basis.** Every work was first published before 1929 and is therefore in the public domain in the United States. Project Gutenberg distributes each file as a US public-domain eBook (noted by the "public domain in the USA" statement in each file's header). This repository stores only the URLs and hashes, never the text files themselves.
- **Size.** Combined, the eight texts total 5,411,405 bytes of English prose (the sum of their `bytes` fields), which is well over a single 4,096-token prompt under any v0.1 tokenizer. Since RFC-0003's generator draws windows at random offsets, the corpus only needs to be larger than one prompt; its size provides a mix of styles and vocabulary (novels, short stories, dialogue, and both archaic and modern spelling) rather than supplying a fixed count of distinct prompts.
- **Stability.** The URLs point to Project Gutenberg's plain-text cache paths by eBook number. Every hash was computed on 2026-11-03 and confirmed against a second fresh download on the same day. If Gutenberg later updates a file and its bytes change, `iproofs prompts build` will fail with an `integrity` error, and updating the corpus requires a new version via pull request (since the corpus digest is part of every workload's identity).

## Corpus digest

`sha256:cedd5c414e7c70b99348140c4ddfde8754446c3d3085f77d5d29a4e7324f639a` is the SHA-256 hash over the lines `<id>\t<sha256>\n`, sorted by ID bytes (RFC-0003) and computed by `iproofs.provenance.corpus_digest`. Every v0.1 workload pins this digest in `prompts.corpus_digest` (#49).
