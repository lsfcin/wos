---
name: slides
description: >
  Make slide decks that look and teach well — lectures, talks, conference/defense, pitch — router.
  Loads the craft subskills, and the provider leaf (gslides) to read and edit decks.
---

# /slides

Arguments: $ARGUMENTS

Deck content comes out in the deck's language; this skill is only the instruction. The owner's own
terms (`enigma`, `kickoff`, `gatilho da prática`, `aula de hoje`) are quoted, never translated.

## Protocol

1. **`taste` opens.** Pick the profile (`grep slides-profiles core/profile.txt` names where they
   live; no setting → interview, then offer to save one). Write the brief. Never skipped.
2. Load only the subskills the deck needs from the tree below; `taste` settles any conflict.
3. Edit through the provider leaf ([`slides/gslides.md`](slides/gslides.md)).
4. **`render-check`**, bounded: render → critique → fix, at most two rounds.
5. **`taste` closes**: the refinement pass. The owner's visual OK before advancing.

## Tree (`core/skills/slides/`)

| Subskill | Load when |
|---|---|
| [`taste`](slides/taste.md) | always — first and last |
| [`narrative`](slides/narrative.md) → `structure` · `visual-story` | ordering a deck, or telling it with images |
| [`word-choice`](slides/word-choice.md) | any text on a slide |
| [`speaker-notes`](slides/speaker-notes.md) | what is said vs shown |
| [`style-system`](slides/style-system.md) | before content: lock the tokens |
| [`accessibility`](slides/accessibility.md) | every deck, before `render-check` |
| [`render-check`](slides/render-check.md) | after every edit batch |
| [`backup-and-qa`](slides/backup-and-qa.md) | defense, conference, pitch |
| [`visuals`](slides/visuals.md) → `one-idea` · `layout` · `typography` · `color-and-imagery` | composing any slide |
| [`formats`](slides/formats.md) → `charts` · `infographics` · `diagrams` · `formulas` · `papers-and-evidence` · `animation` · `video` · `interactivity` · `live-code` | a content type appears; 3 formats per concept |

Refs: one `.yaml` per ref in [`slides/refs/`](slides/refs/CONTEXT.md); each subskill names its keys.
Neighbours: [`/prof`](prof.md) owns the pedagogy; [`/accessible-deck`](accessible-deck.md) turns a deck into a study guide.
