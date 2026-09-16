# links — Specs
> Why the redirect is Cloudflare's and not GitHub's, why a private folder gets no short name, and what
> makes a map that grows forever stay cheap.

Companion to [`CONTEXT.md`](CONTEXT.md), which says what this family *is* and how to call it.

## A redirect is public, so a private thing gets no short name

Anyone who types a short name is sent wherever it points. That is harmless when the target needs a
Google login — they hit a permission wall. It is **not** harmless for a document shared as "anyone
with the link", because a guessable short name turns *unlisted* into *discoverable*, and the `branches/`
notary, health and finance documents are exactly the kind shared that way.

**The refusal keys on the short name and on the file recording the link, never on the URL.** A Drive URL
looks identical whoever it is shared with, so the URL cannot answer the question. The name Lucas
chose can, and so can the path he is writing it into — `--for branches/...` is refused.

**The hyphen is a word boundary here, not just the slash.** A flat hyphenated short name is how a one-off
is named, so `casinhas-planta` is precisely the shape the refusal exists for. Matching whole
segments alone let that through on this check's first run; the test that now pins it says so.

Refusals, not warnings: the failure is silent and permanent — nothing ever tells you a stranger
guessed the short name.

## Cloudflare Pages, because GitHub Pages cannot actually redirect

GitHub Pages serves static files and reads no redirect config, so each short name would be an HTML stub
with a `<meta http-equiv=refresh>`: a blank flash on the way through, and a back button that lands
on the stub and bounces forward again. Cloudflare Pages reads a `_redirects` file and returns a
real 30x. The whole product is a link that behaves like a link.

**302 and not 301.** A 301 is cached by the browser forever, so a short name pointed at the wrong
document once would keep going there on Lucas's own machine long after the map was fixed.

**Deployed by `git push`, not by `wrangler`.** Wrangler would need an `npm` dependency kind that
[`../deps.txt`](../deps.txt) does not have — its `kind` column knows `pip`, `apt`, `binary` and
`system` — so the git route adds **zero dependencies**. It also means Cloudflare is connected to a
public repo of redirects and to nothing else; the workspace repo is never connected. The publish
repo holds only generated content, which is why it is a target and not a project: no `ISSUES.md`,
no pre-commit, and `build` rebuilds it whole from `links.txt`.

**The published root is a dead end on purpose.** An index listing every short name would hand a stranger
the whole map, which is the one thing the refusal above exists to prevent.

## The map grows forever, and that is fine

One row per short name, and nothing ever prunes it on a schedule. It stays cheap because it is **data a
tool queries, not writing a session reads**: `find` greps it and prints the matching rows, so no
context ever holds the whole file. That is the same bargain [`../deps.txt`](../deps.txt) and
[`../../features.txt`](../../features.txt) make.

`check` is what keeps it honest, and it reads the file rather than trusting `add` — rows can arrive
by hand-edit, which is the one path `add`'s refusals do not cover. `build` runs `check` first and
refuses on any finding, because a bad row here is a wrong link handed to a room.
