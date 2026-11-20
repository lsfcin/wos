---
name: accessible-deck
description: >
  Transform slide presentations (Google Slides, PDF, PPTX) into accessible study guides and
  Google NotebookLM podcast scripts with diagram audio-descriptions and tri-block pedagogy.
---

# /accessible-deck

Transform slide presentations into rich, accessible study guides and NotebookLM podcast scripts paired with the deck's visual progression.

Arguments: `$ARGUMENTS` (Google Slides URL or presentation ID, or path to local `.pdf` / `.pptx`)

---

## 1. Commands

```bash
# Export presentation without requiring OAuth (public sharing fallback)
core/run tools/slides/gslides export <url_or_id> --format pdf --out /tmp/deck.pdf

# Ingest deck, cluster progressive animations and render keyframe thumbnails
core/run tools/slides/gslides sample <url_or_id_or_pdf> --out /tmp/deck_sample --max-samples 25

# Inspect outline directly if authenticated via Google Slides API
core/run tools/slides/gslides read --account personal <presentation_id>
```

---

## 2. Operational Protocol

### Step 1: Ingestion & Visual Sampling
1. Run `sample` against the target deck:
   ```bash
   core/run tools/slides/gslides sample "$ARGUMENTS" --out /tmp/sample_deck --max-samples 25
   ```
2. Read the generated `/tmp/sample_deck/manifest.json` and `/tmp/sample_deck/slides_summary.txt`.
3. The sampler clusters consecutive animation frames (e.g., progressive bullet points or diagram build-ups) and renders only the consolidated key slides into `/tmp/sample_deck/imgs/`.
4. Inspect the rendered PNG images using your visual/multimodal inspection tools to understand the exact visual geometry, equations, flowcharts and spatial layout.

### Step 2: Educational Node Mapping
Group the slides into coherent thematic modules according to the Didactic Tree ([`academy/teaching/SPECS-aulas.md`](../../academy/teaching/SPECS-aulas.md)). Each module typically covers 3 to 10 slides representing one conceptual milestone.

### Step 3: Authoring the Tri-Block Guide
Generate a Markdown document (recommended path: `academy/teaching/classes/<turma>/<nome>-guia-acessivel-slides.md`).
The file must strictly follow the **Tri-Block standard**:

- **Header & Meta:**
  - Title, Course, Instructor, Slide Link, Target Audience.
  - "How to Use This Material" section (Dual Coding, Screen Reader, NotebookLM).
  - Table of Contents linked to each Module.

- **For Each Module (Paired to Slides):**
  - `### Bloco 1: Resumo Principal`
    - Conceptual core: WHY (problem), WHAT (solution), HOW (mechanics).
    - Fully standalone explanation — no spatial crutches ("as seen above").
  - `### Bloco 2: Audiodescrição Estrutural & Diagramas`
    - Exact spatial translation of projected visuals (cardinal placement, boxes, colors, arrows).
    - 2D Cartesian plots: axes, ranges, curves, trajectories, discrete points.
    - Linear algebra & math in audible prose (verbalize vector elements and scalar products so a screen reader or TTS reads them seamlessly).
  - `### Bloco 3: Exemplos Práticos Extras & Analogias Sensoriais`
    - Concrete everyday metaphors (sensory, auditory, mechanical — not solely visual).
    - Real-world Portuguese language cases and domain applications expanding beyond the slides.

- **Appendices:**
  - `Apêndice A: Glossário Técnico Rápido para Leitor de Tela`
  - `Apêndice B: Dicas Pedagógicas de Acessibilidade em Sala & Sugestões para os Slides`

### Step 4: NotebookLM Audio Overview Optimization
Ensure the written text contains:
- Rhetorical questions and conversational bridges between sections.
- Conceptual contrast pairs (e.g., "RNN sequential bottleneck vs. Transformer parallel attention").
- Step-by-step instructions at the top for the user to upload the Markdown file + Slides PDF into [Google NotebookLM](https://notebooklm.google.com/) and generate an Audio Overview episode.

---

## 3. Audiodescription Heuristics

When describing complex diagrams for blind or low-vision students:
1. **Never use empty spatial references:** replace "look at this arrow" with "an arrow originating from the top of the Add & Norm box moves horizontally to the right, entering the Decoder".
2. **Read the math aloud:** write equations in clear text alongside LaTeX math (e.g., write "$t_0 = [1.0, -1.0, 1.0, -1.0]$" and describe which dimension has high vs. low frequency).
3. **Trace data flow from input to output:** state starting point (bottom/left), transformations (middle), and destination (top/right).

---

## 4. Reference Implementation

- Canonical production example: [`academy/teaching/classes/ai4good/transformers-guia-acessivel-slides.md`](../../academy/teaching/classes/ai4good/transformers-guia-acessivel-slides.md)
- Governed by: [`academy/teaching/SPECS-aulas.md`](../../academy/teaching/SPECS-aulas.md)
