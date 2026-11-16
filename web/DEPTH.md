# Depth: the site is an iceberg

Read this before you add a line to a page. RFC-0018 SI-8 is the rule; this file is its map.

The site is read from the top down. The top shows the result. Each step down shows more of how the result was taken, to a reader who has chosen to look. A reader at the surface knows nothing about the method and should not need to. A reader three steps down already knows where they are and what the site does, and wants the exact thing.

So a line is placed by one question: how deep is the reader who needs it? What a figure is belongs high. How, when and on how many runs it was taken belongs lower. Nothing is deleted to make a page lighter: it moves to its depth and stays one step from where it was.

## The depths

| Depth | Where | The reader already knows | The question they are asking |
|---|---|---|---|
| 0. Glance | share cards, link previews, page titles and descriptions | nothing | What is this, and where does this system stand? |
| 1. Surface | the ladder (home), the Scale page | that this is a table of systems that prove a model's reply | Can it be proved, on what size of model, did it pass, at what cost? |
| 2. System, top | a system's page: its band and its Figures row | one system on one model, and its result | What did this system get, and what holds it back? |
| 3. System, body | a system's page: Glyph, Checks, Cost, Fidelity, Sessions | the result and the words for it | How was each state and figure taken, and on which record? |
| 4. Rules | Checks, Mandate, the glossary | what was measured | What does the rule say, who set it, who runs this? |
| 5. Records | the repository: board file, run records, level file, RFCs | the rule | Can I recompute it? |

Two things sit beside the depths, not in them:

- **Learn** is a way in for a reader who wants the subject explained. It is not a step between the ladder and a system. Its pages follow their own order (a policy track, a track for prover teams and engineers), and a figure there is printed with its labels, since the page is read alone. One of them, "How a check works", draws the request, who holds what, the six checks and the headline fraction; the home lead and the Checks page link it.
- **The footer** is the same on every page. It holds names only (the level, the release with its date, the licence, who builds the site), each a link: the level to the mandate's line on it, the release to its board file, the licence to its text in the repository. It carries no date of a rule and no hash.

## Three laws

1. **Down, never out.** Content moves to its depth; it is not removed. Each depth links to the next: a ladder row to its system's page, a ladder figure to its section there (the multiple, its two rates, the proof size and the verify time to Cost, Fidelity to Fidelity), a word to its definition, a state to its evidence, an evidence line to its record.
2. **A bad result never moves down.** "Failed", "not decided", "Not passed yet", "not measured", "not run" stay at the surface, in words, beside the system they concern. Only the explanation of the result moves down.
3. **A hover title is a shaft, not a home.** A figure's title carries its labels (scope, n, grade, tier, record) at any depth. It is never the only place they are: a phone and a keyboard have no hover, so the same labels are printed in visible text one step down.

## What goes where

The shallowest depth where each kind of content may be printed, and its form there. Deeper, it may appear in full.

| Content | Shallowest depth | Form there |
|---|---|---|
| system and model names, model size | 0 | words |
| standing, and the checks not passed | 0 | words ("Not passed yet: Model check not decided") |
| the headline figure (cost vs serving) | 0 | figure with its unit |
| its two parts (generation, commit and proving) | 0, with the headline | figures with their units (see Exceptions); on the ladder the two rates print in their place (amended 2026-11-16) |
| the two rates the headline is made of (proved and served reply tokens per GPU-second, CO-8) | 1, with the headline | one line under the multiple on the ladder and in the Figures row, "2.03 tokens/s proved · 2,670 served, per H200", the GPU named; served ÷ proved and each rate's labels in its title, linked to Cost (amended 2026-11-16) |
| the glyph | 0 | drawn, with its petals' names; on the ladder each petal's hover title is its name, its step word and its plain sentence; each petal's step in words at 2; at 3 its row adds two short lines, the reason's first clause and the next step's first need, and one disclosure per petal holds the plain sentence, the full reason and next step, the scale and fact lines and the publisher's words (amended 2026-11-16) |
| a petal's field term ("soundness") and what it rests on ("tested by us", "stated", "read as") | 2 | words under its name and beside its step, on the system page; a Not decided petal has no basis word. Confidentiality's "Architecture: visible", Formally verified's "stated: <what is verified>" ("read as:" on a reading) and Fidelity's "proved: <bits and number format>" sit in the petal's disclosure at 3 (amended 2026-11-16) |
| a petal's next step (what the row lacks for the step above, and who acts) | 3 | its first need, the count of the others and who acts, one line under the reason's first clause; every need in the petal's disclosure (amended 2026-11-16) |
| soundness, zero knowledge and completeness for the row, in that order; the stated security; the scope card | 3 | three lines in view, each with where it is graded or tested and whom it protects, under the five petals (plain first); the publisher's security words verbatim and the card with one bound per row behind one disclosure under them (amended 2026-11-16) |
| verify time | 0 | figure with its unit |
| cost in USD | 3 | the Cost block's sheet only (amended 2026-11-16: not on the ladder, the Scale page, the band, the Figures row, a share card, a description or a search entry) |
| proof size | 0 (a share card), 1 (the ladder, Scale) | figure with its unit (amended 2026-11-16: the ladder's column in the place of USD) |
| a unit | wherever its figure is | beside the figure, always |
| fidelity | 1 | the Fidelity figure (the share of reply positions where the top token is the reply token, FI-10's mean as a percentage, SI-9) with what the row proves under it ("proved: 4.84-bit integer weights", the number format as the publisher states it, and "for part of the weights" where the bits cover a part), then the 8-bit and 4-bit copies' percentages; the copies' ids, the proved copy, why top-token agreement and the check's state in its title |
| the fidelity metrics (matched leading tokens, the bar, p, the controls, KL) | 3 | the Fidelity table, opened by a plain lead (what is compared with what, what 100 % means, what the 8-bit and 4-bit copies are, why top-token agreement), its rows named in words with the copy ids in parentheses; in the surface word's title above that |
| serving, the figure every multiple is over | 1 | figure with its unit, in the model's head |
| how the model was served (engine, GPUs, concurrency) | 3 | one line under Cost |
| what the proving ran on (the GPUs the counted sessions bound, SE-2) | 3 | the Proving line under Cost, with the whole sessions |
| a change to the publisher's code the row runs (a pull request, not merged upstream) | 2 | one line in the band, its record linked |
| what the verifier is given (from our commit record, the request, the proof), the decoding rule, what no call checks | 3 | the Statement block, the claim card's words linked |
| how the verify time was taken (the program, the verifier's CPUs, the host, a GPU visible), the serving ladder | 3 | one line each under Cost |
| the proved copy: its bits, how they were found, and its number format with the publisher's words | 3 | the Proved line at the head of Fidelity; Cost's Serving line links to it |
| the evidence tier ("our runs only, not rerun by anyone else") | 3 | one line under Cost (Evidence), once for the block, linked to the glossary; in every figure's title |
| reply tokens per GPU-second in full (CO-8: range, n, the GPUs bound) | 3 | one line under Cost, beside the session GPU time, with the GPUs named, the served rate beside it, the session's generation and commit-and-proving parts where they are timed apart, and what was not timed apart; at 1 and 2 only as the rate pair with the headline (above), never on the Scale page |
| what was counted (scope: "whole sessions of N replies", steady, verify) | 2 | once, under the band's figure (a phone's band leaves it to the Cost block); at 3 once for the Cost block, and under a figure whose scope differs |
| sample size (n) | 2 | once, beside the scope; at 3 beside the Cost block's scope, and under the system's own Fidelity figure (in replies) |
| pass thresholds, petal steps | 3 as the bar's row; 4 as rules | |
| the request (prompt and reply tokens, decoding) | 4 | the line that opens the six checks |
| the level's name | footer | a link to the mandate |
| the level's freeze date, its file and digest | 4 | the mandate's line on the level |
| the release | 0 (a card's stamp), footer | "Release v1.0, 2026-11-12": a card is a snapshot, and its date says of when |
| the publisher's repository (source), the share group | 2 | the band's facts and the strip; on a phone, the page's foot |
| publisher quotes | 3 | behind each petal's one disclosure ("Details", with the count of quotes), headed "The publisher's words (n)" |
| run records, failed runs | 3 | counts and links under Checks and Sessions |
| definitions | 4 | the checks page and the glossary; a head at 1 or 2 links to its definition |
| method prose | 4, Learn | prose |
| rule ids, file names, hashes, run directories | 5 | a link's target or title above that, never visible text at 0 to 2 |
| who builds the site | footer | names, linked |
| conflicts of interest | 4 | the mandate |

## Words follow depth

- **The surface names the property; deeper names the measure.** Depths 0 to 2 say "Fidelity", "Proof size", "Verify time" ("Cost" until 2026-11-16, when USD moved to depth 3). The exact metric ("leading tokens matching the original, mean", "KL to the original weights") first appears at depth 3, as a column head. The surface word links to it.
- **The head says what, the unit says per what.** "Cost" beside USD/reply, never "Cost per reply" beside USD/reply. `FIGURE_HEAD` in `draw/words.py` holds the heads; `beside_unit` trims a longer name where a unit follows it. A name printed with no unit (a definition's title, a sentence) keeps its full form.
- **Once per block.** What a block's figures share (scope, n, a model, a date) is said once for the block, not on each figure. A figure that differs from its block says so.
- **No bare fraction.** A figure is not framed "of N" unless N is what it is judged against. The mean matched prefix is judged against the model's bar, not against the reply's length, so it is printed with the bar or not at all.
- **A state keeps its word at every depth.** passed, failed, not decided for a check; Met, Mostly met, Partly met, Not met, Not stated, Failed, Not decided for a petal; Passed, Not passed, Not passed yet for a row. No word names an ink: the drawing does. An abstraction never softens a state.
- **No visible id above depth 3.** A rule id, a file name or a control's id is a link's title there.

## The test

Ask in this order; the first yes decides.

1. Would placing it deeper hide a failure, an undecided state, an unmeasured figure or a missing run? Then it stays at depth 0 or 1, as a word.
2. Does a reader who knows only that the benchmark exists need it to read which system passed on which model, and at what cost? Depth 0 or 1.
3. Does it say what one system got, or what holds it back? Depth 2.
4. Does it say how, when or on how many runs something was taken, or quote a source? Depth 3, and the figure's title above that.
5. Is it true of every system (a rule, a threshold, a definition, who and why)? Depth 4, linked from where it applies. Is it an id, a path or a hash? Depth 5, as a link.

Then, before printing it: does a head, a unit, the glyph or another block of the same page already say it? If so, link to that instead.

## Exceptions, each deliberate

- **The two parts of the multiple are on the band, the Scale page and a share card**, a depth above where the test puts them. Where a system generates its reply in a phase of its own, most of its multiple can be generation, not proving, and the headline read alone is taken for the cost of proving (RFC-0018 CO-7, Decision Q15). The parts change how the headline reads, so they travel with it. On the ladder the two rates stand in their place (amended 2026-11-16, Q39).
- **The two rates are on the ladder** (amended 2026-11-16, RFC-0018 CO-8, Q39), a depth above where a hardware-bound figure goes. Readers ask for tokens per second; read alone it depends on the GPU, so it prints only as the two numbers the multiple divides, proved and served on one GPU type, with the GPU named, in one line under the multiple.
- **The overview opens with a lead** (RFC-0018 SI-1, amended 2026-11-15 and 2026-11-16), a depth above where definitions go. A reader at the surface knows nothing of the method, so the band says what a proof of inference is, in one sentence, and links "How a check works". The line on what "passed" means was removed on 2026-11-16 (Q39) so the systems start high on the page; "Passed" on each row links to its definition on the checks page.
- **A share card carries the release and its date.** A card outlives the page it was made from; the date says which figures it shows.

## Known gaps

Places that do not yet follow the map, found by reading the built pages on 2026-11-13. Fix them as the pages are next touched.

- The "Systems not run" reasons on the ladder ("no configuration at the request", "a different statement") use the method's words. RFC-0018 SI-4 fixes the list and its place, and SI-4b (2026-11-15) the order a system's reason is chosen in, each printed with its source on the checks page; moving the list needs SI-4 amended.
