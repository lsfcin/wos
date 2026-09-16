# web
> Reach the open web: search, fetch a page as text, browse and search code hosts.

<!-- routing:start -->
## Routing

| File | Description |
|------|-------------|
| [`code`](code) | browse and search GitHub repository files; returns JSON or raw text |
| [`code-search`](code-search) | search code examples and technical documentation via Exa (default) or GitHub code search (--gh); returns JSON |
| [`fetch`](fetch) | fetch a URL and return readable plain text; falls back to raw for non-HTML |
| [`hf`](hf) | query HuggingFace Hub metadata and file contents; returns JSON |
| [`search`](search) | unified web search; Exa (keyed) by default, ddgr (no-key) fallback; returns normalized JSON array [{title, url, abstract, score?}] |
<!-- routing:end -->
