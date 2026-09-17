# test
> The verify-fast suite: every Level 0 check plus the tool unit tests. Zero-token, no network.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`chat/`](chat/CONTEXT.md) | T1 coverage for the chat tool: what an audio line must keep, what noise must go, and what must never reach a versioned file. |
| [`files/`](files/CONTEXT.md) | T1 coverage for files and drive sync tooling. |
| [`law/`](law/CONTEXT.md) | Level 0: what a file is, what a name may be, and how big a session may get. |
| [`video/`](video/CONTEXT.md) | T1 unit tests for the video tool. Fixtures live here; network-marked cases are excluded from verify-fast. |
| [`workspace/`](workspace/CONTEXT.md) | Level 0 workspace-wide invariants: pointers resolve, .gitignore self-heals, imports do not shadow. |
| [`wos/`](wos/CONTEXT.md) | What the workspace declares about itself, and what the session-close ritual really does. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`conftest.py`](conftest.py) | [`conftest.pyi`](conftest.pyi) | `floor_of`, `git_lines`, `needs`, `carries`, `pytest_configure` | conftest.py — the one place the suite learns where things are: workspace root, core/tools, and the enforcement layer. Also registers the network marker for the video tests. |
| [`test_caveman_compress.py`](test_caveman_compress.py) | [`test_caveman_compress.pyi`](test_caveman_compress.pyi) | — | T1 caveman compress: model output reaches disk as a text file, and the default id has one home. |
| [`test_docs.py`](test_docs.py) | [`test_docs.pyi`](test_docs.pyi) | `paragraph` | T1 docs: an index a document reports must still mean that place when the edit is applied. |
| [`test_forms.py`](test_forms.py) | [`test_forms.pyi`](test_forms.pyi) | — | T1 forms: a form written as JSON must reach the API as the form that was written. |
| [`test_gauth.py`](test_gauth.py) | [`test_gauth.pyi`](test_gauth.pyi) | `accounts` | T1 auth recovery: a dead Google token must hand Lucas a runnable fix, not a traceback. |
| [`test_links.py`](test_links.py) | [`test_links.pyi`](test_links.pyi) | `mapfile` | T1 links: a short name stays sayable, a private thing never gets one, and a live link never moves. |
| [`test_notion.py`](test_notion.py) | [`test_notion.pyi`](test_notion.pyi) | `block` | T1 notion: an id survives any form it is pasted in, and a failure hands back a runnable fix. |
| [`test_notion_write.py`](test_notion_write.py) | [`test_notion_write.pyi`](test_notion_write.pyi) | — | T1 notion write: a batch lands whole or not at all, and a link keeps the name it shows. |
| [`test_secret_law.py`](test_secret_law.py) | [`test_secret_law.pyi`](test_secret_law.pyi) | `scan` | T1 secret law: every shape of credential is found, and the near-misses that would make anyone switch the gate off are not. Zero-token, no network. |
| [`test_slides.py`](test_slides.py) | [`test_slides.pyi`](test_slides.pyi) | — | T1 slides: the geometry a deck reports must be the geometry the write path accepts. |
<!-- routing:end -->
