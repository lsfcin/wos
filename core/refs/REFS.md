# References
> What external material exists for the workspace-os / agent-library scaffold, and how much weight does each hold?
> One line per ref, carrying level markers `[A] [B] [P] [V] [C]`. Citation discipline: [CONTEXT.md](CONTEXT.md).

## Context engineering & progressive disclosure
- `[V]` [Effective context
  engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
  (Anthropic, 2025-09) — attention budget, context rot, JIT retrieval via file paths, compaction.
- `[V]` [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
  (Anthropic) — SKILL.md spec, always-loaded description + on-demand body.
- `[V]` [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)
  (Anthropic) — tool definitions as code cut token overhead vs schema dumps.
- `[P]` [Is Progressive Disclosure All You Need?](https://arxiv.org/abs/2607.17598)
  (arXiv 2607.17598, 2026-07) — 1 disclosure level ≥ 2; flat pack ≈ 2× accuracy at ½ tokens; index is cache-friendly.
- `[P]` [Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988)
  (Gloaguen et al., ETH Zurich, 2026-02) — generated context files cost >20% inference without raising success.
- `[C]` [When AGENTS.md Backfires](https://notchrisgroves.com/when-agents-md-backfires/)
  — curated context cuts runtime 28.6% and output tokens 16.6% (Lulla et al.); avoid generated bloat.
- `[P]` [CodeCompass](https://arxiv.org/abs/2602.20048)
  (arXiv 2602.20048, 2026-02) — graph-structured dependency navigation (99.4% vs 76.2% vanilla) beats flat symbol lists.
- `[P]` [Agentic Context Engineering (ACE)](https://arxiv.org/abs/2510.04618)
  (Stanford/SambaNova, 2026-03) — contexts as evolving playbooks updated by incremental deltas.
- `[P]` [Self-Improvements in Modern Agentic Systems](https://arxiv.org/abs/2607.13104)
  (KAUST, 2026-07) — agent = model + scaffold (prompts, memory, tools, control logic); self-improvement updates
  scaffold.
- `[A]` [Voyager](https://arxiv.org/abs/2305.16291)
  (TMLR 2023) — lifelong skill library persisted outside model weights.
- `[A]` [Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/)
  (TACL 2024) — positional degradation underlying context rot.

## Model level, cost & execution interface
- `[A]` [SWE-agent](https://arxiv.org/abs/2405.15793)
  (NeurIPS 2024) — agent-computer interfaces enable automated SWE; executable enforcement/gates beat prose instructions.
- `[A]` [Token-Budget-Aware Reasoning](https://aclanthology.org/2412.18547)
  (ACL Findings 2025) — dynamic per-task budgets beat fixed caps; wrong budgets degrade accuracy.
- `[A]` [Harness Engineering for Coding Tools](https://arxiv.org/abs/2602.14690)
  (AIware 2026) — empirical survey across 2,853 repos showing executable hooks are rare and high-leverage.
- `[P]` [A Unified Approach to Routing and Cascading](https://arxiv.org/abs/2410.10347)
  — multi-level model cascading foundations.
- `[P]` [UCCI: Calibrated Uncertainty for Cascade Routing](https://arxiv.org/abs/2605.18796)
  (2026) — escalate on calibrated uncertainty rather than static labels.
- `[V]` Opus 5 Guidance (Anthropic)
  — effort modulates thinking not visible output; specify lengths explicitly; delete redundant verification prompts.

## Legibility, vocabulary & decision records
- `[A]` Code Comment Inconsistency Detection (ICSE 2025 · IEEE TSE 2024)
  — drift detection between documentation and code.
- `[A]` [ISO 704 / DDD Ubiquitous Language](https://www.iso.org/standard/38109.html)
  — term selection prioritizes semantic clarity; one canonical glossary (`core/SCHEMA.md`).
- `[C]` [ADR Pattern](https://adr.github.io/) (Nygard)
  — immutable record per decision (Status/Context/Decision/Consequences); superseding over editing history.
- `[C]` [Deterministic Enforcement in LLM
  Systems](https://medium.com/neuralnotions/deterministic-enforcement-in-probabilistic-llm-systems-the-engineering-case-for-claude-code-hooks-64a4196c7d32)
  — case for deterministic hook gates.

## Agent memory & security
- `[A]` [How Memory Management Impacts LLM Agents](https://arxiv.org/abs/2505.16067)
  (ACL 2025) — memory management policy dominates agent performance over raw capacity.
- `[P]` [MemGPT](https://arxiv.org/abs/2310.08560) · [MemOS](https://arxiv.org/abs/2505.22101) ·
  [AIOS](https://arxiv.org/abs/2403.16971)
  — operating system primitives for agent memory.
- `[P]` [Memory Poisoning in LLM Agents](https://arxiv.org/abs/2606.04329)
  (arXiv 2606.04329, 2026-06) — untrusted inputs persist across sessions via compaction channels.
- `[P]` [Origin-Bound Authority for Long-Term Memory](https://arxiv.org/abs/2606.24322)
  (2026-06) — cryptographic provenance tagging for external memory ingest.
- `[P]` [Defeating Prompt Injections by Design (CaMeL)](https://arxiv.org/abs/2503.18813)
  (Google DeepMind, 2025) — data/code capability separation.
- `[A]` [Red-Teaming Multi-Agent Systems](https://arxiv.org/abs/2502.14847)
  (ACL 2025) — communication trust boundaries in multi-agent setups.

## Tooling, visualization & evaluation
- `[A]` [Readability of Node-Link vs Matrix Graphs](https://journals.sagepub.com/doi/10.1057/palgrave.ivs.9500092)
  (Ghoniem et al., 2005) — matrix views beat node-link graphs past ~20 nodes.
- `[A]` [Hierarchical Edge Bundles](https://www.cs.jhu.edu/~misha/ReadingSeminar/Papers/Holten06.pdf)
  (Holten, 2006) — visual bundling of cross-tree dependencies.
- `[A]` [Software Systems as Cities](https://si.usi.ch/assets/publications/conf/icse/icse2011/WettelLR11.pdf)
  (ICSE 2011) — overview visualizations yield +24% correctness in system spread/impact questions.
- `[A]` [Graphical
  Perception](https://notes.billmill.org/images/Cleveland%20and%20McGill%201985%20-%20Graphical%20Perception%20and%20Graphical%20Methods%20for%20Analyzing%20Scientific%20Data.pdf)
  (Cleveland & McGill, 1985) — position/magnitude beats color/glyphs.
- `[C]` [Mermaid](https://mermaid.js.org/) + `git log --numstat`
  — zero-binary self-contained dependency & evolution diagram generation.
- `[C]` [agenteval](https://github.com/lukasmetzler/agenteval) · [instrlint](https://github.com/jed1978/instrlint)
  — instruction and harness evaluation tools.

## Unjudged intake queue (`status: unjudged`)
- [Standard Technical English (STE)](https://www.instagram.com/reel/DclKZARteCP/)
  — controlled English grammar for precision vocabulary.
- [arXiv 2608.15089](https://arxiv.org/pdf/2608.15089) — alternative open setup research.
- [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) — comparison against file-backed memory.
- [weft](https://github.com/WeaveMindAI/weft)
  — structured graph execution compiled to native binary (`code/flows` sibling).
- [three-lane model routing](https://www.instagram.com/reel/DbHHdF4gLWS/) — SLM preprocessing to frontier brief.
- [obra/Superpowers](https://github.com/obra/Superpowers) — skills-based TDD/SDD agent methodology.
- [github/spec-kit](https://github.com/github/spec-kit) — spec-driven development patterns (clarify, constitution).
- [opendataloader-pdf](https://github.com/opendataloader-project/opendataloader-pdf)
  — high-speed CPU PDF parser candidate for `core/tools/paper/parse`.
- [KittenTTS](https://github.com/KittenML/KittenTTS) — compact CPU TTS model.
- [ByteDance OpenViking](https://github.com/ByteDance/OpenViking) · [NVIDIA
  Switchyard](https://github.com/NVIDIA/Switchyard)
  — context browsing and cheap-level model routing.
- [GPT-6 Astra](https://openai.com/index/gpt-6-astra/)
  — flagship OpenAI release; its example slide decks are far better than ours — study what makes
  them better (assessment task in `brain/goals/teaching-materials.md` [astra-slides]).
- [Claude Code front-end design plugins](https://www.instagram.com/reel/Dc2TOXhOLOP/)
  — five plugins for UI quality, design systems, image→code, browser testing — may help our slides
  (assessment task in `brain/goals/teaching-materials.md` [front-design-plugins]; — via reel).
- [Creative developer projects roundup](https://www.instagram.com/p/DcuI3KiDuyu/)
  — includes polished AI-made SVG animations; material for the animation question in
  `brain/goals/teaching-materials.md` [research-tools] (— via aiwbot).
- [FABLE 5.1 release take](https://www.instagram.com/reel/DcyNNHKtEsL/)
  — practitioner read on the biggest-impact change in FABLE 5.1; evaluate whether it applies here
  (`brain/goals/workspace-os.md` [ferramentas-obsoletas]; — via aiwbot).
- [AI 2027](https://ai-2027.com)
  — forecast/scenario site; Lucas asks whether it serves us (task in
  `brain/goals/teaching-materials.md` [ai2027-material]).
- [Fortress](https://www.instagram.com/reel/DdMgKczjl3g/) — [src: web:instagram.com] pitched as a browser engine that
  keeps scrapers from being blocked, the fixes inside the browser and one line to change. Test it against the failure
  that found it: 8 INBOX links died on Instagram login-gating, 2026-09-14 (task in
  `brain/goals/workspace-os.md` [extracao-bloqueada]; — via aiwbot).
- [Claude unified / Cowork in chat](https://www.instagram.com/p/DdYzficDH9z/) — [src: web:instagram.com] reports
  Anthropic folding Cowork into the main Claude, with documents and presentations created, edited, presented and
  exported inside the conversation (task in `brain/goals/teaching-materials.md` [claude-slides-nativo]; — via aiwbot).
- [task→model router](https://www.instagram.com/reel/DdWLJa2tjq6/) — [src: web:instagram.com] a router that sends each
  task to the model that fits; the artifact itself sits behind a broadcast channel (task in
  `brain/goals/craft-flows.md` [router-tarefa-modelo]; — via aiwbot).
- [layer-by-layer 70B runner](https://www.instagram.com/reel/DdXZkT3ulY6/) — [src: web:instagram.com] open-source
  Python lib claimed to run 70B models off disk one layer at a time, memory nearly flat (task in
  `brain/goals/local-ai.md` [layerwise-70b]; — via aiwbot).
- [OpenWorker, Andrew Ng](https://www.instagram.com/reel/DdSoy2Wu8F_/) — [src: web:instagram.com] local AI co-worker
  that completes tasks, 40+ app connectors, any model (task in `brain/goals/local-ai.md` [openworker]; — via aiwbot).
- [VoiceStudio](https://www.instagram.com/reel/DdCOtl_kQsQ/) — [src: web:instagram.com] open-source local alternative
  to ElevenLabs — voice cloning, dubbing, audiobooks; sibling of the [tts-local] question (curation task in
  `brain/goals/teaching-materials.md` [curadoria-techs-git]; — via aiwbot).
- [agent vision toolkit](https://www.instagram.com/reel/Dc13ZNUFMHz/) — [src: web:instagram.com] gives text-only agents
  images and screenshots (task in `brain/goals/workspace-os.md` [agente-ve-imagem]; — via aiwbot).
- [Markdown basic syntax](https://www.markdownguide.org/basic-syntax/) · [Azure DevOps wiki
  markdown](https://learn.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance) — how much markdown actually
  supports; the ground under dropping Notion and the spreadsheets (task in
  `brain/goals/teaching-materials.md` [markdown-so-disciplinas]).
- [HydraFusion, GitHub](https://www.instagram.com/p/Dc54js5CEsw/) — [src: web:instagram.com] coding-agent orchestration
  in three workflows — SINGLE, CASCADE (cheap model first, stronger one takes over), CRITIQUE (one writes, another
  reviews, the first revises); reported 67% lower cost at higher verified quality on one benchmark and slightly lower
  on two others (task in `brain/goals/craft-flows.md` [router-tarefa-modelo]; — via aiwbot).
- [Spec gaming while writing specs](https://www.instagram.com/p/DcyBvhTiaSC/) — [src: web:instagram.com] a suite
  reported green because a flaky test had been turned into a skip; five practices offered against it, including a
  reviewing subagent that never saw the plan written and pre-commit as the only reliable drift fix (task in
  `brain/goals/spec-driven-development.md` [spec-gaming]; — via aiwbot).
- [Four caches in LLM serving](https://www.instagram.com/p/DdGDp-MlKkE/) — [src: web:instagram.com] KV, prefix, the
  provider's prompt cache, and a semantic cache that skips the call when a new question means an answered one (feeds
  `brain/goals/teaching-materials.md` [memoria-e-contexto]; — via aiwbot).
- [GitHub trending, August 2026](https://www.instagram.com/p/Dc_MICrCYSh/) — [src: web:instagram.com] the month's top
  ten, all one layer above the model: `tt-ali/archify` + `cathrynlavery/diagram-design` (English → html/svg
  architecture diagrams), `DietrichGebert/ponytail` (stops the agent over-engineering, 54% less code),
  `deepseek-ai/deepseek-harness`, `mattpocock/skills`, `firecrawl/anydoc`, `diegosouzapw/OmniRoute` (352 providers),
  `TencentCloud/TencentDB-Agent-Memory`, `earendil-works/pi`, `PrimeIntellect-ai/prime-agent`. **The names are only on
  the slides, not in the caption** (tasks in `brain/goals/workspace-os.md` [archify-diagramas] and
  [github-trending-agosto]; — via aiwbot).
- [Omarchy](https://www.instagram.com/p/Dcygo4skfjX/) — [src: web:instagram.com] an OS claimed to pass Windows and Mac
  in 18 months because AI lets anyone customize their computer; the reel itself asks whether the hype holds (task in
  `brain/goals/workspace-os.md` [omarchy-vs-ubuntu]; — via aiwbot).
- [Nvidia PAIR](https://www.instagram.com/p/Dc37X91M4QQ/) — [src: web:instagram.com] open tool pooling idle compute
  across machines in one home for local AI (task in `brain/goals/local-ai.md` [nvidia-pair]; — via aiwbot).
- [mattpocock/skills](https://github.com/mattpocock/skills) — small, composable, model-agnostic agent skills, shipped
  both as a Claude Code plugin and as editable copies. Lucas: *"talvez seja útil pra gente, avaliar"* — weigh against
  the ruling that rejected `obra/Superpowers` for carrying no per-task level routing (task in
  `brain/goals/workspace-os.md` [skills-externas]).
- [ELI5 skill](https://www.instagram.com/reel/DdHFEu1O92_/) — [src: web:instagram.com] a skill that turns a document
  into a one-page picture explainer, big diagrams and almost no text. Lucas: *"talvez até pra trocar a forma como
  fazemos alguns procedimentos"* (task in `brain/goals/workspace-os.md` [eli5-explicador]; — via aiwbot).
- [ffmpeg-skill](https://www.instagram.com/reel/DdJ5rfDjEoH/) — [src: web:instagram.com] gives an agent a local video
  editor — cut, join, caption. Sibling to `core/tools/video/` (task in `brain/goals/workspace-os.md` [ffmpeg-skill];
  — via aiwbot).
- [kem_glitch — three habits](https://www.instagram.com/reel/DdG848DNm3p/) — [src: web:instagram.com] tests first,
  never start from scratch, have the model draw the process. Two we already do; the third is new here — **mutation
  testing**: break a passing test on purpose, and a suite that stays green has no teeth (task in
  `brain/goals/workspace-os.md` [mutation-testing]; — via aiwbot).
