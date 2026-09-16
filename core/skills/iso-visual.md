---
name: iso-visual
description: Isoroll visual-semantics reference: image-to-text conventions, known model failure modes, and how to verify visual output. Load before touching isoroll guides, kits, sprites or scenes.
---

# /iso-visual

> First `[visual-semantics]` artifact (goal: brain/goals/craft-flows.md). Spec twin:
> `code/isoroll-content/SCENE-CREATION.md`.

## THE HARD RULE

**Geometry lives in TEXT and is verified by CODE. Model eyes never assert geometry.**

- Source of geometric truth: layout DSL → massing boxes → manifests
  (`code/isoroll-content/src/pipeline/{layout_parse,layout_massing}.py`; scene manifest ↔
  `isoroll-module/src/walls/wall-types.d.ts`).
- Verification: `sheet_qc.py` (silhouette IoU ≥ 0.9, mark residue count), cross-view dimension checks, wall-count
  round-trips, `isoroll.dumpZOrderJSON()` in-Foundry.
- Read-image (agent vision) is allowed ONLY for coarse sanity: file renders, not blank, not obviously rotated/empty.
  Never for "is the wall in the right place", "which object is in front", "are these two views consistent".
- STYLE is judged by the human (Lucas) — gitflow eyeball gate before visual merges. Never mark a visual task done on
  model judgment.

Why: empirically confirmed failure modes (see below) — models, including frontier ones, misjudge spatial relations and
report bad visual results as fine.

## Conventions (guide/kit images ↔ text)

| Convention | Meaning |
|---|---|
| Grayscale face ramp | screen-role pre-shading, lit-from-above: `FACE_TOP` light / `FACE_LONG` mid / `FACE_CAP` dark (`tile_guide_render.py`). Face identity is by label, not hue. |
| Magenta linework | layout/grid lines; postproc detects grid from it (NB may recolor near-white — `sheet_grid.py` handles both) |
| Cyan marks | registration marks, tile/kit-sheet scale ONLY (scene scale = PARKED, see kill-log) |
| Facing vocabulary | `N NE E SE S SW W NW TOP` — module `Facing` type (`src/resolver/asset-resolver.ts`); file naming `{name}_{stance}_{facing}.{ext}` |
| Projection | dimetric 2:1 (26.57°); stage transform rotation −45°, skew 18.435°, ratio 2.0 |
| Cardinal reference | unfolded-net convention (TOP folded flat above body) from the hand-drawn deck `src/pipeline/prompts/reference/isometric_images.pdf` — reverse-engineered in `make_tile_guide.py`, verified vs 2 deck pages |
| Rotation | ALWAYS cell remapping, NEVER sprite mirroring (mirror flips chirality: door hinges, stair spirals) |
| Orientation band | dark band on pivot edge of chiral pieces (door hinge, stairs newel) — the visual handedness signal |
| Scale | px-per-voxel `s` comes from the manifest, never re-measured from pixels; one `s` per sheet (SCENE-CREATION.md § Scale-consistency) |
| Anchors | tile anchor in [0,1]² (`wall-coords.ts::defToCanvas`); sprite anchor = pre-defined ground-cell point, adjustable |

## Known model failure modes (evidence-backed — design around them)

1. **Scene-scale geometry loss**: image models hold geometry at TILE scale, not SCENE scale. Test-to-kill 2026-07-08:
   5-panel scene → footprint diverged per panel, NE was a different room. → kit assembly: generator only paints
   tile-sized pieces.
2. **E↔W / mirror flips**: multi-view generation swaps east/west or mirrors instead of rotating. → rotation-as-remapping
   + orientation bands + cross-view QC.
3. **Marks read as content**: floating symbols re-interpreted as legend/callouts; hallucinated captions. → marks only in
   validated tile-scale regime; caption cell absorbs watermark.
4. **Handedness ignores prompts**: prompt-only chirality pins FAILED (NB matched the guide's mirror); only a visual cue
   in the guide (band) works. → never rely on text alone to control geometry in image output.
5. **Agent overconfidence on visuals**: agents (all models) report wrong stacking/order/placement as correct — the
   simplest things (what's on top of what). → THE HARD RULE above.
6. **Agent overcomplication**: agent solutions for spatial features drift more complex than the human design
   (`[simplicity-gap]`). → architecture loop + adversarial review mandatory for spatial features.

## Checklist for any isoroll visual loop

1. Load this skill + `/foundry` (if touching module code).
2. Identify the TEXT source of truth for the geometry you're changing (layout/massing/manifest/WallDef).
3. Write/extend the CODE check that proves your output (QC metric, round-trip count, golden diff, dumpZOrderJSON).
4. Read-image only for coarse sanity; flag anything for human eyeball explicitly in the loop return.
5. Never mirror sprites; never re-measure scale from pixels; never invent facings outside the vocabulary.
