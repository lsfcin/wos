# links
> A link gets a name a room can be told out loud. Provider leaf: `cfpages` (Cloudflare Pages).

```bash
core/run tools/links/cfpages add ai4good/setup <url>   # mint a short name
core/run tools/links/cfpages find ai4                  # query the map — never read it whole
core/run tools/links/cfpages rm ai4good/setup
core/run tools/links/cfpages build --push              # regenerate _redirects and deploy
core/run tools/links/cfpages check                     # what is untrue about the map
```

Named short names, not codes — `ai4good`, not `x7f2q`. A short name is said out loud and typed from memory.

```
lucassf.pages.dev/ai4good        a course home
lucassf.pages.dev/ai4good/setup  something inside it — one level
lucassf.pages.dev/rva-chico      a one-off, flat and hyphenated
```

[`links.txt`](links.txt) records every short name's target, one tab-separated row, queried with `find`.
`gforms new`, `gslides new`, `gdocs new` and `gdrive share` each take `--short-name`, through
[`../short_name.py`](../short_name.py), so a link is named where it is created.

The short name grammar, the private-folder refusal, why Cloudflare rather than GitHub Pages, and what
`check` watches: [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | Why the redirect is Cloudflare's and not GitHub's, why a private folder gets no short name, and what makes a map that grows forever stay cheap. |
| [`cfpages`](cfpages) | — | — | named short links: add, find, rm, build, check |
| [`links.txt`](links.txt) | — | — | Every short link this workspace hands out: the short name someone is told out loud, and where it really goes. Read by core/tools/links/links_core.py; published as _redirects by `cfpages build`. |
| [`links_core.py`](links_core.py) | [`links_core.pyi`](links_core.pyi) | `base`, `Refused`, `load`, `preamble`, `save` | links_core.py — the short name map read+write boundary, and the redirect file it emits, for links/cfpages |
<!-- routing:end -->
