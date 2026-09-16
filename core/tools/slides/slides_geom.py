# slides_geom.py — Google Slides transform algebra: rotation, effective scale, composition, bounds
import math

# Standard 16:9 deck, in EMU. Everything here reports geometry as a fraction of these, which
# is also the unit the write path accepts — read a position, hand it straight back as an edit.
SLIDE_W, SLIDE_H = 9144000, 5143500


def _num(transform: dict, key: str, default: float) -> float:
    """Missing means default; present-but-zero means zero.

    `t.get(k, d) or d` reads the same until the value really is 0.0 — which is exactly what
    a quarter-turn stores in scaleX, and it silently reported those elements as 45°.
    """
    value = transform.get(key, default)
    return default if value is None else value


def rotation_deg(transform: dict) -> float:
    """Slides stores rotation inside the affine transform, never as an angle field."""
    return math.degrees(math.atan2(_num(transform, "shearY", 0.0),
                                   _num(transform, "scaleX", 1.0)))


def eff_scale(transform: dict) -> tuple[float, float]:
    """Magnitude of the transform's columns — the scale that survives rotation.

    Do not read a small value here as "hidden". Slides stores a base size plus a scale, so
    an ordinary API-created text box comes back at `scaleY≈0.26`. Only near-zero on both
    axes means an animation ghost — see SPECS.md § Ghosts for why the old 0.4 cut was wrong.
    """
    sx,  sy  = _num(transform, "scaleX", 1.0), _num(transform, "scaleY", 1.0)
    shx, shy = _num(transform, "shearX", 0.0), _num(transform, "shearY", 0.0)
    return math.sqrt(sx*sx + shy*shy), math.sqrt(sy*sy + shx*shx)


def compose_transforms(pt: dict, ct: dict) -> dict:
    """Parent ∘ child. Group members carry transforms relative to their group."""
    psx, psy   = _num(pt, "scaleX", 1.0), _num(pt, "scaleY", 1.0)
    pshx, pshy = _num(pt, "shearX", 0.0), _num(pt, "shearY", 0.0)
    ptx, pty   = _num(pt, "translateX", 0.0), _num(pt, "translateY", 0.0)
    csx, csy   = _num(ct, "scaleX", 1.0), _num(ct, "scaleY", 1.0)
    cshx, cshy = _num(ct, "shearX", 0.0), _num(ct, "shearY", 0.0)
    ctx, cty   = _num(ct, "translateX", 0.0), _num(ct, "translateY", 0.0)
    return {
        "scaleX": psx*csx + pshx*cshy,   "shearX": psx*cshx + pshx*csy,
        "shearY": pshy*csx + psy*cshy,   "scaleY": pshy*cshx + psy*csy,
        "translateX": psx*ctx + pshx*cty + ptx,
        "translateY": pshy*ctx + psy*cty + pty, "unit": "EMU",
    }


def bounds(element: dict) -> tuple[float, float, float, float]:
    """(x, y, w, h) as fractions of the slide, with scale applied to the stored size."""
    t = element.get("transform", {})
    s = element.get("size", {})
    esx, esy = eff_scale(t)
    return (
        _num(t, "translateX", 0.0) / SLIDE_W,
        _num(t, "translateY", 0.0) / SLIDE_H,
        s.get("width",  {}).get("magnitude", 0) * esx / SLIDE_W,
        s.get("height", {}).get("magnitude", 0) * esy / SLIDE_H,
    )
