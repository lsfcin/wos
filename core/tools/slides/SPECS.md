# Google Slides API — facts worth not rediscovering
> What the API actually returns, learned the expensive way — read alongside `CONTEXT.md`.

## Slidev is gone (2026-08-14)

This family used to be a Slidev CLI plus a Google-Slides→Slidev port pipeline (`slides_port`,
`slides_shapes`, `slides_style`, `slides_text`). Lucas retired it once remote editing into the
live deck was confirmed working: the reason to port decks out was that the source of truth could
not be edited from here, and it can. **Resurrecting a local presentation format needs that reason
to come back first** — what survived is `slides_geom.py`, the transform algebra below.

## Auth

Two grants: `slides` (`presentations.readonly`) and `slides-write` (`presentations`), the same
split as [`../files/`](../files/CONTEXT.md). A read prefers the write token when the alias has
one — the edit consent already contains the read consent, so demanding a second browser trip
would buy no safety and just create two tokens that can die independently.

**The two grants live in two directories, and the write one is easy to miss.** A read token is
`~/.config/workspace-slides/<alias>.token.json`; a write token is
`~/.config/workspace-slides-**write**/<alias>.token.json` — the grant name *is* the directory
suffix, via `gauth.config_dir(kind)`. Checking the read directory to see whether a write grant
landed answers **no** forever, no matter how many times the consent succeeds. That failure ran four
times in one session on 2026-08-17, while `gslides auth` printed the real path on its own last line
each time. **Read the tool's output, not a directory you inferred the name of.**

## Geometry

- **Slide dimensions: `9144000 × 5143500` EMU** (standard 16:9). `slides_geom.py` reports every
  position and size as a fraction of these, and the write path takes the same fraction back.
- **A stored `size` is a base size, not the rendered one.** The rendered box is `size × scale`
  from the transform. An ordinary API-created text box comes back at `scaleY ≈ 0.26`.
- **Rotation lives in the matrix, not in a field**: `atan2(shearY, scaleX)`.
- **`scaleX` of exactly `0.0` is meaningful** — it is what a quarter turn stores. Coalescing it
  with `or 1.0` reports those elements as 45°, which is the bug the geometry tests now pin.
- **Group members carry transforms relative to their group**, so a member's absolute position is
  `compose_transforms(group, member)`.

## Ghosts

Slides keeps hidden animation states as **zero-scaled copies** of real elements, and their
stored `size` is normal — so a size check cannot find them, only a scale check can. The old port
used `eff_scale < 0.4` on either axis. **That threshold was wrong outside ported decks**: real
elements routinely sit below it (see above), so it silently ate live content. Anything filtering
ghosts needs near-zero on *both* axes, and `read` does not filter at all — hiding a real element
is worse than showing a hidden one.

## Colors and fills

- `shapeBackgroundFill.propertyState = "INHERIT"` means "use the theme default", and it means
  two different things by context: on master elements it is decoration that should stay
  invisible; on a slide element with no text and no outline it is a visible accent box relying
  on the theme color.
- Lines with no explicit `solidFill.color` have **no color**, not black. Defaulting them to black
  renders invisible connector lines as spurious diagonals.
- `CENTERED_TITLE` placeholders do not store paragraph alignment — it is inherited from the theme.

## Writing

- **Object ids must be at least 5 characters.** A shorter one fails the whole batch with
  `Invalid requests[N]: The object ID (x) length should not be less than 5`.
- **`batchUpdate` is atomic and ordered**: requests apply in sequence, and one rejection rolls
  back the batch. Create-then-modify in a single call is safe.
- **`duplicateObject` takes an `objectIds` map**, so a copy's children get ids you chose instead
  of generated ones — this is what makes a generated frame sequence addressable.
- **Duplicates are inserted directly after their source**, so duplicating one slide N times
  leaves the copies in reverse order. `updateSlidesPosition` in the same batch fixes it.
- **Per-frame motion is the two facts above, chained**: `duplicateObject` +
  `updatePageElementTransform` in one `batchUpdate` authors position/velocity/acceleration
  sampled into frames, and it survives PDF export (confirmed 2026-08-14).
