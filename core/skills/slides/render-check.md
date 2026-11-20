# render-check
> Render → critique → fix, at most two rounds: overlap, overflow, off-grid, small images.

`lint` first (zero tokens: small text, off the slide, over the template, off the footer line), then `preview` for what only an eye sees — the footer and margins on a crop at ≥150 dpi. Checks, never designs. A future texpace checker would plug in here, optional.

**Performance is pass/fail.** Students watch on weak laptops and phones, and the animations must reach them, not only the PDF: a slide that loads, stalls or runs the fan fails, whatever the render looks like. The per-slide budgets live in `lint`.

Refs: `pptx-skill` · `slide-self-verify`
