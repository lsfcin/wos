# publish
> What crosses into the public repo his students clone, what no feature claims, and the refusal
> that runs before the first byte is copied.

```
core/run tools/wos/publish/repo             # what crosses, what does not, what escapes
core/run tools/wos/publish/repo --orphans   # the audit list, one path per line
core/run tools/wos/publish/repo --check     # exit 1 if anything crossing carries a credential
```

The floor — which trees are eligible at all, and where the target is checked out — is [`../../../public.txt`](../../../public.txt), which carries its own reasons. Why nothing crosses by default and what the orphan list is for: the head of [`crossing.py`](crossing.py). Why the credential check refuses rather than redacts: the head of [`repo`](repo), and [`../../secret_law.py`](../../secret_law.py).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`crossing.py`](crossing.py) | [`crossing.pyi`](crossing.pyi) | `Floor`, `floor`, `tracked`, `eligible`, `Claim` | crossing.py — what crosses into the public repo and what does not: the floor, the claims, and the import closure that turns a claim on one file into the files it cannot run without. |
| [`rebuild.py`](rebuild.py) | [`rebuild.pyi`](rebuild.pyi) | `leaves`, `generators` | rebuild.py — what the DESTINATION runs after the copy, so what it generates describes ITS tree. |
| [`repo`](repo) | — | — | what crosses into the public repo, what no feature claims, and whether anything crossing carries a credential |
<!-- routing:end -->
