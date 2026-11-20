# links — Specs
> Why the redirect is Cloudflare's and not GitHub's, why a private folder gets no short name, and what
> makes a map that grows forever stay cheap.

Companion to [`CONTEXT.md`](CONTEXT.md), which says what this family *is* and how to call it.

## A redirect is public, so a private thing gets no short name

Anyone who types a short name is sent wherever it points. That is harmless when the target needs a Google login — they hit a permission wall. It is **not** harmless for a document shared as "anyone with the link", because a guessable short name turns *unlisted* into *discoverable*, and the `branches/` notary, health and finance documents are exactly the kind shared that way.

**The refusal keys on the short name and on the file recording the link, never on the URL.** A Drive URL looks identical whoever it is shared with, so the URL cannot answer the question. The name Lucas chose can, and so can the path he is writing it into — `--for branches/...` is refused.

**The hyphen is a word boundary here, not just the slash.** A flat hyphenated short name is how a one-off is named, so `casinhas-planta` is precisely the shape the refusal exists for. Matching whole segments alone let that through on this check's first run; the test that now pins it says so.

Refusals, not warnings: the failure is silent and permanent — nothing ever tells you a stranger guessed the short name.

## Cloudflare Pages, because GitHub Pages cannot actually redirect

GitHub Pages serves static files and reads no redirect config, so each short name would be an HTML stub with a `<meta http-equiv=refresh>`: a blank flash on the way through, and a back button that lands on the stub and bounces forward again. Cloudflare Pages reads a `_redirects` file and returns a real 30x. The whole product is a link that behaves like a link.

**302 and not 301.** A 301 is cached by the browser forever, so a short name pointed at the wrong document once would keep going there on Lucas's own machine long after the map was fixed.

**Deployed by `git push`, not by `wrangler`.** Wrangler would need an `npm` dependency kind that [`../deps.txt`](../deps.txt) does not have — its `kind` column knows `pip`, `apt`, `binary` and `system` — so the git route adds **zero dependencies**. It also means Cloudflare is connected to a public repo of redirects and to nothing else; the workspace repo is never connected. The publish repo is a target and not a project: no `ISSUES.md`, no pre-commit, and `build` rebuilds `_redirects` whole from `links.txt`. Its only source is the site's own code — `viewer.js`, `lib/`, `functions/` — tested by `node --test test/site.test.mjs`. A standalone site (`13ou22`, `ufrpe`) is the exception: `npx wrangler` direct upload, because its source repo is not ours to connect (or is the workspace) — so it never updates on push, and its own CONTEXT names the redeploy. No dashboard; the token is `CLOUDFLARE_TOKEN` in `segredos.env`:
```bash
set -a; . core/tools/links/segredos.env; set +a; export CLOUDFLARE_API_TOKEN=$CLOUDFLARE_TOKEN CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNT
export NODE_OPTIONS=--dns-result-order=ipv4first   # without it wrangler dies with "fetch failed" here (2026-10-30)
npx -y wrangler@3.114.0 pages project create <project> --production-branch main   # once
npx -y wrangler@3.114.0 pages deploy <dir> --project-name <project> --branch main   # every update
```

## The site is written from two places, and the workspace still owns it

The browser edits a page (`editar`, password `EDIT_PASSWORD`) and students fill their delivery slots (matrícula, from the `TURMAS` secret); both commit straight to the publish repo through a Pages Function. The workspace stays the source because **`publish` and `build` run `pull` first**: a file the site changed comes home by a three-way merge — the last version both sides agreed on is the base — and is committed in its own repo, by path. The same or neighbouring lines changed on both sides refuse before anything is written. Without this, the next `mirror` copies the workspace over a browser edit and nobody is told.

**The panel declares the slots; `entregas.tsv` beside it holds the links.** A slot is a code in a student's `painel:dados` row; a separate `## entregue` list repeated the panel and cost ~3k characters, so `painel.js` makes the panel itself clickable, redrawing painel.py's exact text with spans (a test holds the two equal). A box without a link stays ◻: nothing to grade. Writing the links into the page itself was tried first and refused by the size cap with the slots still empty — 240 URLs are data, not prose. The tsv is mirrored and pulled like a page, and so is `pareceres.tsv`, the teacher's note per student and code, written only with the password and read by everyone. Each delivery costs a deploy (~1 min before others see it); there is no counter for wrong guesses, so each one waits 2 s.

**The secrets are the workspace's.** `cfpages secrets` builds all three from `segredos.env` files — `TURMAS` from each course's `MATRICULA_<NAME>` lines and `DUPLAS` — so the host holds a copy it can lose, never the original.

**The published root is a dead end on purpose.** An index listing every short name would hand a stranger the whole map, which is the one thing the refusal above exists to prevent.

## The map grows forever, and that is fine

One row per short name, and nothing ever prunes it on a schedule. It stays cheap because it is **data a tool queries, not writing a session reads**: `find` greps it and prints the matching rows, so no context ever holds the whole file. That is the same bargain [`../deps.txt`](../deps.txt) and [`../../features.txt`](../../features.txt) make.

`check` is what keeps it honest, and it reads the file rather than trusting `add` — rows can arrive by hand-edit, which is the one path `add`'s refusals do not cover. `build` runs `check` first and refuses on any finding, because a bad row here is a wrong link handed to a room.
