# References — Specs
> What each level marker means, and the citation discipline that keeps REFS.md honest.

## Source levels

| Level | Meaning | Weight |
|------|---------|--------|
| `[A]` | Peer-reviewed, excellence venue — ICSE · TSE · ACL · EMNLP · NAACL · NeurIPS · ICLR · ICML · AAAI · CHI · UIST · CSCW · SOSP · USENIX Security · IEEE S&P · CCS · TMLR · TACL | Citable as established |
| `[B]` | Peer-reviewed, other venue / workshop / journal outside the top level | Citable, note the venue |
| `[P]` | Preprint — arXiv, OpenReview submission, SSRN. Not reviewed | Provisional. Never the sole basis for a workspace policy change |
| `[V]` | Vendor / lab engineering post (Anthropic, Google, OpenAI) | Authoritative about *their* product, not independent evidence |
| `[C]` | Community / practitioner — blog, repo, spec draft | Signal about practice, not evidence |

## Citation rules

A query round that returns only `[P]` is incomplete: re-run it against a venue-aware source before
concluding. `core/tools/paper/papers --ss` reports `venue` and `peer_reviewed` per hit; `--reviewed`
drops preprints, `--min-cit N` drops noise. Web search often surfaces the published version
(`aclanthology.org`, `dl.acm.org`, `openreview.net` with a venue) when arXiv shows only the
preprint — prefer that URL.

A preprint that later gets accepted keeps its arXiv id: upgrade the level marker in place when you
notice it, rather than adding a second line.

**The marker itself is enforced**, by
[`core/hooks/entropy/entropy_stores.py`](../hooks/entropy/entropy_stores.py): a bullet carrying a
link opens with a level or the commit is rejected. The `Unjudged` section is exempt by name, read
from the heading rather than from a list — capture stays free, and the level is what promotion buys.
Which level a line deserves is a judgement no check makes.
