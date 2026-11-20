# deck_sample.py — Ingestion, progressive clustering and visual sampling for slide decks
from __future__ import annotations

import json, pathlib, re, shutil, subprocess, sys, urllib.request

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1] / "hooks"))
import platform_law  # noqa: E402

SLIDE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{30,}$")
URL_ID_PATTERN = re.compile(r"/presentation/d/([a-zA-Z0-9_-]+)")


def parse_slide_target(target: str) -> dict:
    clean = target.strip()
    match = URL_ID_PATTERN.search(clean)
    if match:
        return {"kind": "google_slides", "id": match.group(1), "path": None}
    if SLIDE_ID_PATTERN.match(clean) and not pathlib.Path(clean).exists():
        return {"kind": "google_slides", "id": clean, "path": None}
    local = pathlib.Path(clean).expanduser().resolve()
    if local.is_file():
        ext = local.suffix.lower()
        if ext == ".pdf":
            return {"kind": "local_pdf", "id": None, "path": local}
        if ext in (".pptx", ".ppt"):
            return {"kind": "local_pptx", "id": None, "path": local}
    return {"kind": "unknown", "id": None, "path": None}


def download_public_export(presentation_id: str, out_path: pathlib.Path, format: str = "pdf") -> pathlib.Path:
    url = f"https://docs.google.com/presentation/d/{presentation_id}/export/{format}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            if "text/html" in resp.headers.get("Content-Type", ""):
                raise RuntimeError("Google Slides export returned HTML instead of document. Check link sharing.")
            with open(out_path, "wb") as f:
                shutil.copyfileobj(resp, f)
    except urllib.error.HTTPError as err:
        msg = "Access denied" if err.code in (401, 403) else f"HTTP error {err.code}"
        raise RuntimeError(f"{msg} downloading export for {presentation_id}: {err.reason}") from err
    except Exception as err:
        if isinstance(err, RuntimeError): raise
        raise RuntimeError(f"Failed to download export from {url}: {err}") from err
    return out_path


def _poppler(*args: str) -> str:
    """A PDF is opened raw only inside core/tools/pdf; slides asks that family's leaf, like gmail does."""
    cmd = [platform_law.interpreter(), str(platform_law.WORKSPACE_ROOT / "core/tools/pdf/poppler"), *args]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"core/run tools/pdf/poppler {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def render_pages(pdf_path: pathlib.Path, prefix: pathlib.Path, pages: list[int] | None = None, dpi: int = 150) -> list[pathlib.Path]:
    """Each page as `<prefix>-<n>.png`, in page order."""
    span = ["--pages", ",".join(map(str, pages))] if pages else []
    out = _poppler("render", str(pdf_path), "--prefix", str(prefix), "--dpi", str(dpi), *span)
    return [pathlib.Path(line) for line in out.splitlines() if line]


def extract_slide_texts(pdf_path: pathlib.Path) -> list[str]:
    pages = _poppler("text", str(pdf_path)).split("\x0c")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def clean_slide_lines(text: str, noise_tokens: set[str] | None = None) -> list[str]:
    noise = noise_tokens or set()
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().isdigit() and ln.strip() not in noise]


def _lexical_similarity(words1: set[str], words2: set[str]) -> float:
    if not words1 and not words2: return 1.0
    if not words1 or not words2: return 0.0
    return len(words1 & words2) / len(words1 | words2)


def cluster_and_sample(slides_text: list[str], max_samples: int = 25) -> list[dict]:
    if not slides_text: return []
    info = []
    for idx, raw in enumerate(slides_text, 1):
        lines = clean_slide_lines(raw)
        info.append({
            "idx": idx, "lines": lines, "title": lines[0] if lines else f"Slide {idx}",
            "words": set(re.findall(r"\w+", raw.lower())),
        })

    clusters: list[list[dict]] = [[info[0]]]
    for i in range(1, len(info)):
        prev, curr = clusters[-1][-1], info[i]
        same_title = prev["title"].strip().lower() == curr["title"].strip().lower() and len(prev["title"].strip()) > 3
        is_sub = prev["words"] and prev["words"].issubset(curr["words"]) and len(curr["words"]) > len(prev["words"])
        if same_title or is_sub or _lexical_similarity(prev["words"], curr["words"]) >= 0.70:
            clusters[-1].append(curr)
        else:
            clusters.append([curr])

    results = []
    for c_idx, cluster in enumerate(clusters, 1):
        key = sorted(cluster, key=lambda s: len(s["lines"]), reverse=True)[0]["idx"]
        results.append({
            "cluster_id": c_idx, "title": cluster[0]["title"], "slides": [s["idx"] for s in cluster],
            "key_slide": key, "summary": " | ".join(cluster[-1]["lines"][:3]) or cluster[0]["title"],
        })

    if len(results) <= max_samples:
        return results

    step = (len(results) - 1) / (max_samples - 1)
    chosen = {0, len(results) - 1} | {int(round(i * step)) for i in range(1, max_samples - 1)}
    downsampled = [results[i] for i in sorted(chosen)]
    for n_idx, c in enumerate(downsampled, 1): c["cluster_id"] = n_idx
    return downsampled


def render_sample_images(pdf_path: pathlib.Path, slide_numbers: list[int], out_dir: pathlib.Path, dpi: int = 150) -> dict[int, pathlib.Path]:
    imgs = out_dir / "imgs"
    imgs.mkdir(parents=True, exist_ok=True)
    rendered = {}
    for s in slide_numbers:
        prefix = imgs / f"slide_{s:03d}"
        try:
            matches = render_pages(pdf_path, prefix, [s], dpi)
        except Exception:
            continue
        if matches:
            dest = imgs / f"slide_{s:03d}.png"
            if dest.exists(): dest.unlink()
            matches[0].rename(dest)
            rendered[s] = dest
    return rendered


def sample_deck(target: str, out_dir: pathlib.Path | None = None, dpi: int = 150, max_samples: int = 25, keep_pdf: bool = True) -> dict:
    parsed = parse_slide_target(target)
    kind = parsed["kind"]
    if kind == "unknown":
        raise ValueError(f"Target '{target}' not recognized. Pass Google Slides URL/ID or local PDF.")
    name = parsed["id"] or (parsed["path"].stem if parsed["path"] else "deck_sample")
    out = out_dir or pathlib.Path.cwd() / f"sample_{name}"
    out.mkdir(parents=True, exist_ok=True)

    if kind == "google_slides":
        pdf = download_public_export(parsed["id"], out / "deck.pdf", format="pdf")
    elif kind == "local_pdf":
        pdf = parsed["path"]
    else:
        raise NotImplementedError("Direct local PPTX requires conversion to PDF.")

    texts = extract_slide_texts(pdf)
    clusters = cluster_and_sample(texts, max_samples=max_samples)
    rendered = render_sample_images(pdf, [c["key_slide"] for c in clusters], out, dpi=dpi)
    for c in clusters:
        ks = c["key_slide"]
        c["image"] = platform_law.rel(rendered[ks], out) if ks in rendered else None

    manifest = {"target": target, "kind": kind, "presentation_id": parsed["id"],
                "total_slides": len(texts), "sample_count": len(clusters), "dpi": dpi, "clusters": clusters}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")

    summary = [f"# Slide Sampling Summary: {target}", f"Total Slides: {len(texts)} | Key Slides: {len(clusters)}", ""]
    for c in clusters:
        summary.extend([f"- Cluster {c['cluster_id']:02d} [Slides {', '.join(map(str, c['slides']))}] (Key: {c['key_slide']})",
                        f"  Title: {c['title']}", f"  Snippet: {c['summary']}", ""])
    (out / "slides_summary.txt").write_text("\n".join(summary), encoding="utf-8", newline="\n")
    return manifest
