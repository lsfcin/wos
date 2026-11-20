# style-system
> Lock colour, font, size and spacing tokens before any content, and hold every slide to them.

Tokens are decided in [`design-system.md`](design-system.md) — the one file that holds their values; each `visuals/` child applies them.

What repeats on every slide lives in the template (master/layouts), never pasted per slide. Boxes snap to the content column; footer text shares one size, bottom edge and anchor (`lint`); a source link is short, centred on the footer line.

Refs: `theme-factory` · `grid-8pt`
