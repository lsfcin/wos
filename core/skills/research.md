---
name: research
description: >
  Execute a research workflow from the workspace Core research system.
flow: literature, sota, scout, review, draft, compare, audit, replicate, recipe, summarize, explore, watch
---

Execute a research workflow from the workspace Core research system.

Arguments: $ARGUMENTS

Parse the arguments as `<workflow> [query or path]`. If no workflow is given, print the menu below and stop.
The flow filename is the command tail: `research <workflow>` → `core/flows/research/<workflow>.md`.
Back-compat aliases: `deep`/`deepresearch`→`sota`, `autoresearch`/`auto`→`explore`, `lit`→`literature`
(resolve to the canonical command).

## Workflows

| Command | Flow file | Use when |
|---------|-----------|----------|
| `literature` | `core/flows/research/literature.md` | literature review on a topic (alias: `lit`) |
| `sota` | `core/flows/research/sota.md` | map the state of the art of a **field**: fill `refs/REFS.md` + one review yaml per kept paper, emit a ≤200-line decision summary (aliases: `deep`, `deepresearch`) |
| `scout` | `core/flows/research/scout.md` | `sota` **plus** a plan: research a topic in rounds, then write a model-tiered, impact-flagged action plan into the target ROADMAP (use when the research serves a decision about our own system) |
| `review` | `core/flows/research/review.md` | peer-review simulation of a document or claim |
| `draft` | `core/flows/research/draft.md` | draft a section or document from evidence |
| `compare` | `core/flows/research/compare.md` | compare two papers or approaches |
| `audit` | `core/flows/research/audit.md` | source and citation audit |
| `replicate` | `core/flows/research/replicate.md` | attempt to replicate a method |
| `recipe` | `core/flows/research/recipe.md` | step-by-step research recipe |
| `summarize` | `core/flows/research/summarize.md` | summarize a document |
| `explore` | `core/flows/research/explore.md` | autonomous try-ideas loop — run, measure, keep winners (aliases: `auto`, `autoresearch`) |
| `watch` | `core/flows/research/watch.md` | monitor a topic for new developments |

## Execution protocol

1. Read the flow file for the requested workflow (`core/flows/research/<workflow>.md`; resolve aliases
   `deep`/`deepresearch`→`sota`, `autoresearch`/`auto`→`explore`, `lit`→`literature` first).
2. Read `core/tools/CONTEXT.md` to know which tools are available and how to call them.
3. Execute the workflow step by step. Use bash to invoke tools:
   - `core/tools/paper/papers "<query>"` — arXiv / Semantic Scholar
   - `core/tools/web/search "<query>"` — unified web search (Exa if `~/.feynman/web-search.json` keyed, else ddgr
     zero-key fallback; flags: `--n`, `--type neural|keyword`, `--since`, `--domains`, `--content`, `--backend
     auto|exa|ddgr`)
   - `core/tools/web/fetch "<url>"` — fetch a URL
   - `core/tools/paper/parse <file>` — extract text from PDF/DOCX
   - `core/tools/web/code list|read|search <owner/repo>` — GitHub
   - `core/tools/paper/annotate set|get|list <id> [note]` — annotation store
4. **Source discipline** — arXiv is the easiest surface to search, so an unguarded pass
   returns almost only preprints, which are *not peer reviewed*. Every round must also hit
   published venues (ACL/EMNLP anthology, ACM DL, IEEE, OpenReview with an accepted venue).
   `core/tools/paper/papers --ss` reports `venue` + `peer_reviewed` per hit; `--reviewed` drops
   preprints, `--min-cit N` drops noise. Tag every delivered reference with its level and
   record it in the relevant `refs/REFS.md`. Level table + full rule: [`core/refs/CONTEXT.md`](../refs/CONTEXT.md).
5. For steps that require specialist agents, spawn workers using:
   - `core/agents/researcher.md` — evidence gathering
   - `core/agents/reviewer.md` — peer review
   - `core/agents/verifier.md` — citation verification
   - `core/agents/writer.md` — synthesis and drafting
6. Deliver the output in the format the flow specifies.
