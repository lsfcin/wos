# References
> External agent-library sources and evidential weight.
> Level-1 intake; judged sources live in YAML. Levels: [SPECS.md](SPECS.md).


## Model level, cost & execution interface
- `[V]` Opus 5 Guidance (Anthropic)
  — effort modulates thinking not visible output; specify lengths explicitly; delete redundant verification prompts.

## Legidade, vocabulário e registros de decisão
- `[A]` Code Comment Inconsistency Detection (ICSE 2025 · IEEE TSE 2024)
  — drift detection between documentation and code.

## Unjudged intake queue (`status: unjudged`)

Instagram leads are untested. Task IDs: ../ROADMAP.md unless specified.

- [cadcraft](https://lucassf.pages.dev/wos/cadcraft) — Instagram/eduardocavalcanti: capabilities unverified; [cadcraft].
- [prompt-audit](https://lucassf.pages.dev/wos/prompt-audit) — Instagram/nocodealex: gains unverified; [prompt-audit].
- [soundbox](https://lucassf.pages.dev/isoroll/soundbox) — Instagram DfBSFBwCikQ/gittrend.io: local audio/agent claims; [soundbox].
- [mcptoon — gittrend.io](https://instagram.com/reel/Demkg_Xgmmz/) — On-demand MCP discovery; savings unverified. [mcptoon-context]; Dobra: ../../code/dobra/ROADMAP.md.
- [Clipa — editandocombeatriz](https://instagram.com/reel/DdsXDRVMgen/) — Sponsored captions; unverified. ../ROADMAP.md, caption-tool comparison; ../../branches/virada/ROADMAP.md.
- [REA / PhotoCraft / EffectCraft — silvestri_gabriel](https://instagram.com/reel/DeXZnw4mdEr/) — Media demos; claims unverified. [rea-assessment]; ../../branches/virada/ROADMAP.md.
- [Standard Technical English (STE)](https://instagram.com/reel/DclKZARteCP/)
  — controlled English for precise vocabulary.
- [arXiv 2608.15089](https://arxiv.org/pdf/2608.15089) — alternative open setup research.
- [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory) — comparison against file-backed memory.
- [weft](https://github.com/WeaveMindAI/weft)
  — structured graph execution compiled to native binary (`code/flows` sibling).
- [three-lane model routing](https://instagram.com/reel/DbHHdF4gLWS/) — SLM preprocessing to frontier brief.
- [obra/Superpowers](https://github.com/obra/Superpowers) — skills-based TDD/SDD agent methodology.
- [github/spec-kit](https://github.com/github/spec-kit) — spec-driven development patterns (clarify, constitution).
- [KittenTTS](https://github.com/KittenML/KittenTTS) — compact CPU TTS model.
- [ByteDance OpenViking](https://github.com/ByteDance/OpenViking) · [NVIDIA Switchyard](https://github.com/NVIDIA/Switchyard)
  — context browsing and cheap-level model routing.
- [GPT-6 Astra](https://openai.com/index/gpt-6-astra/)
  — Study its stronger example decks
  (`core/prompts/slides-padroes.md` step 3).
- [Claude Code front-end design plugins](https://instagram.com/reel/Dc2TOXhOLOP/)
  — five plugins for UI quality, design systems, image→code, browser testing; may help our slides
  (`core/prompts/slides-padroes.md` step 3; — via reel).
- [Creative developer projects roundup](https://instagram.com/p/DcuI3KiDuyu/)
  — AI-made SVG animations; assess for
  `core/skills/slides/formats/animation.md`.
- [FABLE 5.1 release take](https://instagram.com/reel/DcyNNHKtEsL/)
  — Practitioner release take; assess relevance
  (`brain/goals/workspace-os.md` [ferramentas-obsoletas]).
- [AI 2027](https://ai-2027.com)
  — Forecast/scenarios; assess usefulness (task in
  `brain/goals/teaching-materials.md` [ai2027-material]).
- [Fortress](https://instagram.com/reel/DdMgKczjl3g/) — Claimed scraper browser; test actual login-gated failures first. brain/goals/workspace-os.md [extracao-bloqueada].

- [Claude unified / Cowork in chat](https://instagram.com/p/DdYzficDH9z/) — claimed in-chat decks/docs; core/prompts/slides-padroes.md step 3.
- [task→model router](https://instagram.com/reel/DdWLJa2tjq6/) — task/model routing; artifact behind broadcast channel; ../../brain/goals/craft-flows.md [router-tarefa-modelo].
- [layer-by-layer 70B runner](https://instagram.com/reel/DdXZkT3ulY6/) — claims disk-streamed layers; ../../brain/goals/local-ai.md [layerwise-70b].
- [OpenWorker, Andrew Ng](https://instagram.com/reel/DdSoy2Wu8F_/) — Claimed local coworker; ../../brain/goals/local-ai.md [openworker].
- [C] [VoiceStudio local voice](https://github.com/debpalash/VoiceStudio) — OmniVoice noncommercial; demo Mac 64 GB; [post](https://instagram.com/reel/De1zlGniBQp/); [voice-studio]; [earlier](https://instagram.com/reel/DdCOtl_kQsQ/).
- [agent vision toolkit](https://instagram.com/reel/Dc13ZNUFMHz/) — images for text-only agents; ../../brain/goals/workspace-os.md [agente-ve-imagem].
- [Markdown](https://www.markdownguide.org/basic-syntax/) · [Azure wiki](https://learn.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance) — Assess replacing Notion/sheets. ../../brain/goals/teaching-materials.md [markdown-so-disciplinas].
- [HydraFusion, GitHub](https://instagram.com/p/Dc54js5CEsw/) — Orchestration modes; gains unverified. brain/goals/craft-flows.md [router-tarefa-modelo].

- [Spec gaming while writing specs](https://instagram.com/p/DcyBvhTiaSC/) — Flaky-test skip made suite green; `spec-driven-development.md` [spec-gaming].
- [Four caches in LLM serving](https://instagram.com/p/DdGDp-MlKkE/) — KV, prefix, provider prompt and semantic response caches; brain/goals/teaching-materials.md [memoria-e-contexto].
- [GitHub trending, August 2026](https://instagram.com/p/Dc_MICrCYSh/) — Leads: archify/diagram-design, ponytail, deepseek-harness, mattpocock/skills, anydoc, OmniRoute, TencentDB-Agent-Memory, pi and prime-agent. workspace-os [archify-diagramas]/[github-trending-agosto].

- [Omarchy](https://instagram.com/p/Dcygo4skfjX/) — questions the claim that AI customization beats Windows/Mac in 18 months; ../../brain/goals/workspace-os.md [omarchy-vs-ubuntu].
- [Nvidia PAIR](https://instagram.com/p/Dc37X91M4QQ/) — Pools household idle compute for local AI (task in `../../brain/goals/local-ai.md` [nvidia-pair]).
- [mattpocock/skills](https://github.com/mattpocock/skills) — Composable provider-agnostic skills; compare missing per-task level routing that ruled out Superpowers. workspace-os [skills-externas].

- [ELI5 skill](https://instagram.com/reel/DdHFEu1O92_/) — One-page visual explainer; assess procedural use. ../../brain/goals/workspace-os.md [eli5-explicador].
- [ffmpeg-skill](https://instagram.com/reel/DdJ5rfDjEoH/) — Local cut/join/caption editor; sibling to `core/tools/video/` (task in `../../brain/goals/workspace-os.md` [ffmpeg-skill]).
- [An agent spent its owner's API key without approval](https://instagram.com/reel/DdUDF_mRuhz/) — Provider limits beat agent promises. teaching-materials [aula-agente-gastou-chave], workspace-os [teto-de-gasto-agente].

- [Astra Minecraft](https://instagram.com/p/DdZK4y9jFHW/) — Instagram/Vals AI: 14-hour run after creeper loss; examine agent notes without anthropomorphism. teaching-materials [aula-agente-desanimado].

- [Higgsfield opened its platform through an API](https://instagram.com/p/DdaiDXzjNha/) — Sponsored; verify [wide-trace/open-higgsfield](https://github.com/wide-trace/open-higgsfield). rpg-isoroll [higgsfield-asset-gen], local-ai [higgsfield-o-que-roda-aqui], teaching-materials [aula-abrir-o-moat].

- [kem_glitch — three habits](https://instagram.com/reel/DdG848DNm3p/) — Tests first, reuse, draw the process; mutation testing checks whether breaking behavior makes tests fail (`workspace-os.md` [mutation-testing]).
- `[C]` [Glitch Orchestra — GlitchCatClub](https://instagram.com/reel/DeEyZPEtkyH/) — Claimed multi-agent spawning, state files, Kanban. workspace-os [glitch-orchestra-state-eval], core/ROADMAP.md.

- `[C]` [Avanço de Agentes de IA](https://instagram.com/p/DeEzhnoDaXa/) — radar da cadência rápida de evolução de frameworks de agentes autônomos (task em `brain/goals/workspace-os.md` [sota-agent-cadence]).

- [MatrAIx](https://arxiv.org/abs/2608.04205) — Li et al., preprint on simulated-user evaluation; assess behavioral validity and teaching uses. Tasks in academy/teaching/ROADMAP.md and core/ROADMAP.md.

- [Drift](https://instagram.com/reel/DeI3Zulji05/) — Instagram/gittrend.io: desktop video-editor demonstration; author's claims to test. ../ROADMAP.md.
- [Oil UI](https://instagram.com/reel/DeHs15riSZr/) — Instagram/gittrend.io: demonstration of interface alternatives for user selection. ../ROADMAP.md.

- [Hairline — Shai](https://instagram.com/reel/DeEhSRWBAi2/) — Shows interactive vector illustrations and names lucasmarkes/hairline; editing/accessibility unverified. [visual-tools].

- [ff-tracking — Github Signals](https://instagram.com/reel/DeV1Y0pChK-/) — Shows code-video production and names mrsarac/ff-tracking; platform/cost unverified. [visual-tools].

- [Papermorph — Github Signals](https://instagram.com/reel/DeGtjz6kV5N/) — Presents DozenTwelve/Papermorph for interactive narrated study material; source fidelity and accessibility unverified. [visual-tools].

- [Felix Rieseberg prompt — theaifield](https://instagram.com/p/Degx359DGAu/) — Raw sources, professional methods and independent checks for depth, not scope; attribution unverified. [expert-depth].

- [Congress composition 1986–2026 — fabrizio.conrado](https://instagram.com/reel/DeNYNeTi59d/) — AI chart; data and criteria unverified. [visual-tools].

- [OpenHarness — gittrend.io](https://instagram.com/reel/DePGHMiki4X/) — autonomous-ai/openharness claims terminals, cross-machine sessions and encrypted relay; verify Linux/support first. ../ROADMAP.md, Desktop hyperagent.

- [Universal Modder — gittrend.io](https://instagram.com/reel/DeJdwzZiDQA/) — rehan-remade/universal-modder discovery, assets, live checks and reusable notes; compare before adoption. [modder-patterns].

- [C] [Owly Linux AirDrop](https://github.com/t4t5/owly) — Wireless adapter/driver compatibility remains untested; [post](https://instagram.com/p/Dea3i2_iM-6/); [owly-transfer].
- [C] [Qwenputer foundations](https://github.com/divagr18/qwenputer) — Selected tests/merged limits; no accepted paper located; [post](https://instagram.com/reel/DfEWEZmKr7C/); [qwenputer].
- [C] [Strata and GSQ-RCO](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md) — 46 GB RAM/12 GB GPU; expert/context limits; [post](https://instagram.com/reel/De53W9JotxV/); [strata-local].
- [V] [Motion, anime.js and web UI candidates](https://motion.dev/) — Browser visuals; two identities inferred; not sprites; [post](https://instagram.com/reel/DfGjKw7uAl7/); [web-motion].
- [C] [Mesh LLM distributed inference](https://github.com/Mesh-LLM/mesh-llm) — Distributed stages need trusted peers, not one laptop; [post](https://instagram.com/p/DfD_VBfGQbV/); [mesh-llm].
- [C] [Tool ratings and checks](https://help.blotato.com/start-with-an-ai-agent/llm/automations.md) — Opinion bars: estimated spans, not benchmark scores; [post](https://instagram.com/p/DeZjFVZALGO/); [rated-tools].
- [V] [Firecrawl](https://www.firecrawl.dev/) — [src: web:firecrawl.dev] Cloud/self-hosted differ; no universal access guarantee; [post](https://share.google/Ilgv6Fhk6gAzv0dDB); [firecrawl].
- [V] [Unsloth browser control](https://unsloth.ai/docs/basics/browser-use.md) — Restricted browser/network; variable model memory; [post](https://instagram.com/reel/DfEDl31NaQg/); [unsloth-browser].
- [C] [Package hallucinations](https://www.lasso.security/blog/ai-package-hallucinations) — Benign experiment: 30k downloads, not 30m victims; [post](https://instagram.com/reel/DfE78eZqVkd/); [dependency-provenance].
- [V] [DeepSeek inference release](https://github.com/deepseek-ai/DeepInfer) — Identity inferred; datacenter/vendor results; [post](https://instagram.com/p/Dexhqycn6RS/); [deepinfer].
- [P] [Harness²](https://github.com/google-research/harness2) — Fixed weights; extra calls, judge/sandbox limits; [post](https://instagram.com/reel/Dewrk9ax1LP/); [harness2].
- [C] [Anatomy isometric animation](https://github.com/wheresryan22/anatomy) — Browser animation does not verify geometry; [post](https://instagram.com/reel/Del82x1DVA1/); [anatomy].
- [V] [GitReverse and GitDiagram](https://gitreverse.com/) — Inferred maps/prompts, not recovered author intent; [post](https://instagram.com/reel/DeSkqerMO02/); [repo-maps].
- [C] [AirLLM streaming tradeoffs](https://github.com/lyogavin/airllm/releases/tag/v3.1.0) — 1.56 TB weights, 292 s/token; [post](https://instagram.com/reel/DegiJfWlFSX/); [post 2](https://instagram.com/reel/De2lOu1DdCv/); [airllm]. [Kimi-in-C capture](https://instagram.com/reel/DcjlgleALHo/) — unverified.
- [P] [Baidu Unlimited OCR](https://arxiv.org/html/2606.23050v1) — Finite context; original BF16 requires 8 GB GPU; [post](https://instagram.com/reel/DehD9WBq0Qb/); [unlimited-ocr]. [post](https://instagram.com/p/DfTb1XOGW_2/) — unverified.
- [C] [One disabled model repository](https://huggingface.co/audnai/penclaw-GLM-5.3-abliterated-for-offensive-cyber) — One disabled repo; terabyte successor, no blanket ban; [post](https://instagram.com/reel/Dd9B5RbR11F/); [model-continuity].
- [V] [Backboard R-CLI](https://github.com/Backboard-io/Backboard-R-CLI) — CLI; 30%/90% savings lack matched evidence; [post](https://instagram.com/reel/DdJqqm0xprR/); [r-cli].
- [V] [Code Mode](https://blog.cloudflare.com/code-mode-mcp/) · [Anthropic](https://www.anthropic.com/research/advanced-tool-use) — Definition-footprint saving; composition/filtering; [post 1](https://instagram.com/reel/DeypYeWN5hL/); [post 2](https://instagram.com/reel/De6pmMnBu2x/); [post 3](https://instagram.com/reel/Dfk7fhqh9zL/); [code-mode].
- [C] [pstack verification patterns](https://github.com/cursor/plugins/tree/main/pstack) — Verification patterns; throughput/portability unproven; [post](https://instagram.com/p/De6cbtKjjXg/); [pstack].
- [V] [ScaleDown/Jev](https://docs.scaledown.ai/introduction) — Narrow heads; summaries generate; schema ≠ correctness; [post](https://instagram.com/reel/Devav4iBMF5/); [scaledown].
- [C] [Project NOMAD offline resources](https://github.com/Crosstalk-Solutions/project-nomad) — Library minimum 4 GB; optional AI optimum 32 GB; [post](https://instagram.com/reel/DeWgRPDBlzm/); [nomad].
- [C] [Laws in Markdown](https://github.com/ctresb/leis) — Incomplete conversion; keep dated official originals; [post](https://instagram.com/reel/DeuHpsaRPmn/); [laws-markdown].
- [C] [Simplified-language prompt adaptation](https://www.asd-ste100.org/) — Portuguese clarity, not controlled-English compliance; [post](https://instagram.com/reel/DexzpETtgCT/); [plain-explanations].
- [C] [Workload-specific GPU throughput](https://github.com/Zagitta/GPU-UNLOCK) — Matrix-specific; no verified RTX3050 speedup; [post](https://instagram.com/reel/DfAy1NHseqU/); [gpu-unlock].
- [C] [Dessa speech preview](https://block.xyz/dessa) — Preview; unread primary, access/licence unverified; [post](https://instagram.com/p/De_ghm7DMTo/); [dessa].
- [C] [Claude Code advice](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) — 100–200k quality chart admits invented source; [post](https://instagram.com/p/DefaJVojOSp/); [context-evidence].
- [C] [Hex](https://lucassf.pages.dev/wos/hex) — GitHub: local dictation; task: [tool-comparison]; ../../branches/tweaks/SETUP.md.

- [C] Cross-harness reports — Claude/Codex, 26–30 Oct: verify caller/callee, quota, discovery and background recipes; [cross-harness-delegation].
- [C] Agent media skills: [HyperFrames](https://github.com/heygen-com/hyperframes), [p5.brush](https://github.com/acamposuribe/p5.brush), [Scenario 3D](https://github.com/scenario-labs), [OpenViking](https://github.com/volcengine/OpenViking) memory —; [video-motion-skills].
- [Qwen modified](https://instagram.com/reel/Dd2VDfixrdf/) — reduced-refusal/local-runtime claims unverified; compare task quality with original. [qwen-modified].
- [Omega planner/worker loop](https://instagram.com/reel/DfaLyn7Rorf/) — cost claims unverified; assess cost, retries and accepted quality against existing routing. [omega-loop].
- [MiniMax local-video claim](https://instagram.com/reel/Ddke9-IIpDd/) — weights/licence/hardware unverified. ../../brain/goals/local-ai.md [local-video-gen].
- [JCode](https://instagram.com/reel/DfHKGq9JYkX/) — Rust agent; performance/free claims unverified. [jcode].
- [Elephant–Goldfish](https://instagram.com/reel/De9SUTPsxWS/) — long-context planner/fresh reviewer; identity/licence unverified. [egm]; craft-flows [B1].
- [20 UX principles](https://instagram.com/reel/DcwkX6OyduT/) — speech has 20 directives; sampled visual labels partly illegible, item 20 blank. Reconstruct speech→item mapping; task: [ux-20].
- [Hob](https://lucassf.pages.dev/freeai/hob) — GitHub: file agent; hardware/offline: [tool-comparison].
- [Taiga-S1 / Biome-S1](https://lucassf.pages.dev/spatial/taiga) — GitHub/Simply AI (DeFJd9AHPVS): FreeCAD executor; unreplicated metrics; [taiga-s1].
- [Claude quality](https://lucassf.pages.dev/wos/claude-quality) · [post](https://lucassf.pages.dev/wos/claude-quality-reel) — Anthropic: April fixes in other versions; Instagram intent allegation unproven. [model-regression].
- [Colibri](https://lucassf.pages.dev/local/colibri) — GitHub/JustVugg; Instagram Dd_h_ApIqXb (744B/~372 GB/no GPU), DehErZxDfkE (~11 GB active): claims differ from total RAM. Author: 0.05–0.1 tok/s cold on 25 GB. [colibri-streaming].
- [GLM-5.2](https://lucassf.pages.dev/local/glm52) — Z.ai: MIT/1M context; Instagram DfLPFzTMzYr superiority/local claims need matched evaluation; API-key demo proves no local run or persistent memory. [glm52-comparison].
- [Respan](https://lucassf.pages.dev/wos/respan) — GitHub/respanai; Instagram DfMoeX7ij47: provider-format gateway, not CLI-session adapter; author speed figures unreplicated; hedging costs extra calls. [respan-gateway].
- [Alexandria](https://lucassf.pages.dev/wos/alexandria) — Firecrawl; Instagram DfMiFm0Oc0N: source/index access does not guarantee answer correctness. [firecrawl].
- [Unslop](https://lucassf.pages.dev/wos/unslop) — GitHub/heydamir; Instagram DfMB84QAtoL: audit, approved direction, nine design passes; test usability/accessibility rather than impose universal aesthetics. UNSLOP.
- [Infinity](https://lucassf.pages.dev/wos/infinity) — GitHub/hydro-project; Instagram De9or1Jienw: hibernation/tool events; 75k waiting states do not imply 75k simultaneous inferences. [infinity-runtime].
- [Motionmaxxing](https://lucassf.pages.dev/wos/motionmaxxing) — Instagram/dailyfindsdev: local HTML animation; [post](https://lucassf.pages.dev/wos/motionmaxxing-post); [motionmaxxing].
- [Claude advisor](https://lucassf.pages.dev/wos/advisor) — Instagram/sully.omarr: stronger-model consult; savings unverified; [post](https://lucassf.pages.dev/wos/advisor-post); [advisor].
- [T3-Video](https://lucassf.pages.dev/wos/t3-video) — Instagram/simplifyinai: native 4K research; [post](https://lucassf.pages.dev/wos/t3-video-post); [t3-video].
- [SAG-Wiki](https://lucassf.pages.dev/wos/sag-wiki) — Indexes without a model; retrieval uses one; [sag-wiki].
- [CL4R1T4S](https://lucassf.pages.dev/wos/cl4r1t4s) — Leaked prompts, unverified; dobra holds the ref; [cl4r1t4s-watch].
- [APIV loop](https://lucassf.pages.dev/wos/apiv-post) — Align, plan, implement, verify per task; [apiv].
- [Expired AI findings](https://lucassf.pages.dev/wos/expired-findings-post) — Source unknown; [expired-findings].
- [Merge checks](https://lucassf.pages.dev/wos/merge-checks-post) — gitleaks, knip, jscpd, osv-scanner; [merge-checks].
- [TwIL-8B](https://lucassf.pages.dev/wos/twil-8b) — Scores are bf16, not Q4; non-commercial; [twil-8b].
- [Rune](https://lucassf.pages.dev/wos/rune) — Headless UI to PNG for agents, untested; [rune].
- [Token budget](https://lucassf.pages.dev/wos/token-context-post) — Every opened file spends; [token-context].
- [Atomic Agent](https://lucassf.pages.dev/wos/atomic-agent) — Telegram-driven local agent; aiwbot [atomic-telegram].
- [One folder per task](https://lucassf.pages.dev/wos/one-folder-post) — Already our thesis; ref only.
