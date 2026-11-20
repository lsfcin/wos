# Craft — Prior Art, Provenance, and Case Study
> Where this flow comes from, what evidence backs its routing decisions, and one worked failure it
> caught. **Nothing here is needed to run the flow** — load it when changing the flow, defending it,
> or writing about it.

## Research provenance

The (b-refined) level-alias + active-model-swap decision — strip `model:` provider short names from `.opencode/agents/craft-*.md`, keep `model: opus|sonnet|haiku` level aliases in `.claude/agents/craft-*.md`, resolve the active provider once at Loop 0, spawn each loop with `opencode run -m <resolved> --agent craft-<level> --auto` — is grounded in a deep-research run (2026-07-16) surveying academic routing/cascade papers (2023–2026) and production agent frameworks (Anthropic, OpenAI Agents SDK, AutoGen, CrewAI, Aider, OpenRouter, LangGraph). The dominant pattern across both corpora is **call-site/orchestrator-driven model injection**, not per-(role×model) pinning. Kulkarni&Kulkarni 2026 empirically refutes the role-parametric layout on cost-Pareto (reflexive 2.3× cost for 0.943 F1 vs hierarchical 1.15× for 0.921, hybrid routing recovers 89% at 1.15×). Anthropic's strategic "Building Effective Agents" endorses Routing/Orchestrator-Workers as named patterns; Anthropic's shipped Claude Code uses `model: opus` level-alias frontmatter — intra-Anthropic consistency confirms (b-refined). Voyager's single-GPT-4 pin is the negative case for level diversity; Aider's architect/editor is the closest production precedent to /craft (2-loop cross-provider cascade, benched).

Canonical artifacts (read before changing the routing):

- `outputs/agent-level-routing-agnostic.md` — the cited decision brief (22 sources, decision matrix, risk table, open niches)
- `outputs/agent-level-routing-agnostic.provenance.md` — provenance file (URL + access-date + decision-relevance per source)
- `core/flows/refs/agent-level-routing-REFS.md` — level-1 index pointing to per-source YAMLs in `core/flows/refs/`
- `core/flows/refs/research-summary.yaml` — synthesis-summary YAML (the solution bulleted into a single file)

## Prior Art

This flow is a production realization of three 2023 academic primitives. Citing them here so the next reader (human or AI assistant) recognizes the lineage:

- **Reflexion** (Shinn et al., 2023 — <https://arxiv.org/abs/2303.11366>): "language agents verbally reflect on task feedback signals, then maintain their own reflective text in an episodic memory buffer to induce better decision-making in subsequent trials." /craft instantiates this as the **append-only loop file** with attempt logs (4b `attempt 1:` / `attempt 2:`) and `FLAG: RETURN ... evidence=<one line>` self-reflection — but durable on disk, so it survives crashes and is `grep`-auditable post-hoc; Reflexion's memory is in-context only.
- **LATM (Large Language Models as Tool Makers)** (Cai et al., 2023 — <https://arxiv.org/abs/2305.17126>): "tool-making → powerful resource-intensive model; tool-using → lightweight model. Once-off cost spread over multiple instances, significantly reducing average costs while maintaining strong performance." This **is** the Autorouting table (`craft.md` § Autorouting) — generalized from tool-making/tool-using to loop-roles: Loop 1+3 (high, Opus) make the plan + architecture; Loops 4a/4b/5 (medium, Sonnet) use them; Loop 6 (low, Haiku) ships. The Carry block (`craft.md` § Carry) is LATM's *functional cache of decisions rather than responses*.
- **Voyager** (Wang et al., 2023 — <https://arxiv.org/abs/2305.16291>): "an iterative prompting mechanism that incorporates environment feedback, execution errors, and self-verification for program improvement," plus "an ever-growing skill library of executable code." /craft has environment feedback (Loop 4b green/red) and execution errors (attempt logs); its **two gaps vs. Voyager** = (a) *separate-context* self-verification (currently Loop 5 is same-model re-running e2e — see [`craft.md`](craft.md) § Field Practice) and (b) cross-run **skill library** —
  patterns die with their `.craft/<name>/` file. Closing both is
  [`craft-ship.md`](craft-ship.md) § Second-opinion verifier.

Open industry-frontier references: Anthropic — "Best practices for Claude Code" (<https://www.anthropic.com/engineering/claude-code-best-practices>); Cognition — "Don't Build Multi-Agents" (Yan, 2025 — <https://cognition.ai/blog/dont-build-multi-agents>); LangChain — "The rise of context engineering" (Chase, 2025 —
<https://blog.langchain.com/the-rise-of-context-engineering>). Cognition's two principles — *share context across
actions* and *actions carry implicit decisions* — are exactly what the Carry block + file-relay enforce; the craft flow was authored **before** that essay and is its structural implementation.

## Case Study — integration gap caught only at the user-test loop

The `export-manifest` run on `isoroll-content` (`code/isoroll-content/.craft/export-manifest/`, shipped commit `ce81655` on 2026-07) is the textbook demonstration of why the loop exists. Loop 5 (`5-user.md:52`) sonnet caught:
`build_manifest` imported `scene_assemble.load_kit`, which PIL-opens every kit piece PNG *before*
`wall_schema.validate_manifest` can emit its designed `[FAIL]+exit 1` — so a missing asset crashed with an uncaught `FileNotFoundError` instead of reaching the graceful validation path. The unit suite (Loop 4a) could not see this: T4 only fed `validate_manifest` a manually-mutated dict, never drove `build_manifest` against a kit_dir with a genuinely missing PNG. The orchestrator took the `RETURN loop=3 reason=integration-gap`, ruled inline at max level (`3-arch.md:93-122`), split `load_kit_meta` out of `load_kit`, the medium re-ran 4a→4b→5, all 6 e2e steps passed, ship.
This is **Cognition Principle 2 in the wild**: action A (`load_kit` reused in `build_manifest`) carried an implicit decision ("I will PIL-open every asset") that conflicted with T2's contract, and the flow caught it at the user-test loop — not in production.