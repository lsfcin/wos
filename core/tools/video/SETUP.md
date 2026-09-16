# video tool — setup
> Dependencies for `core/tools/video/video` (link → navigable text). See goal workspace-os / TODO:121.

## Installed (M1 — L0 metadata + L1 captions)
- `yt-dlp` — in workspace venv: `"$(sh core/run --python)" -m pip install yt-dlp` ✓ (2026.07.04)

## Pending (M2 speech + M3 OCR) — need system installs (sudo)
```bash
sudo apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-por
"$(sh core/run --python)" -m pip install faster-whisper pytesseract
```
- `ffmpeg` — audio extraction (M2) + frame sampling (M3)
- `faster-whisper` — local transcription backend (model name is config data, default `base`)
- `tesseract-ocr` + `-por` — burned-in text OCR (M3), Portuguese language pack

## M4 — Instagram cookies (login-gated posts)
`video_core._run` auto-attaches `--cookies <path>` when a cookies file exists at
`~/.config/workspace-video/cookies.txt` (Netscape format, outside repo — never gitignore
needed since it's outside the workspace). No file → tool behaves exactly as before.

To populate — **no browser extension needed**, yt-dlp reads the browser profile directly
(Lucas is logged into Instagram in Brave, not Firefox):

```bash
"$(sh core/run --script yt-dlp)" --cookies-from-browser brave \
  --cookies ~/.config/workspace-video/cookies.txt \
  --skip-download --print id "<any public IG url>"
chmod 600 ~/.config/workspace-video/cookies.txt
```

Rerun that command when the session expires. The file holds live session credentials in
plaintext — keep it at mode `600` and outside the repo.

**Hard prerequisite, cost a full session to find (2026-07-23):** `secretstorage` must be
installed in the venv. Chromium-family browsers on Linux encrypt the cookie DB against the
system keyring; without the module yt-dlp fails with
`ERROR: secretstorage not available` + `failed to decrypt cookie (AES-CBC) ... Possibly the
key is wrong?` — which reads like a wrong-password bug, not a missing dependency.
Fix: `"$(sh core/run --python)" -m pip install secretstorage`.

Verified (2026-07-23): auth works end-to-end, `DZLABeVx3qk` returns metadata + description.
Note `DbBDnp6DcKV` is an **image carousel** — yt-dlp reports "No video formats found" per
sub-item; that is not an auth failure, it needs the L3 OCR / L4 VLM image path.

## M4 — L4 visual captioning (pure-visual content, no speech/on-screen text)
`caption_frames()` in `video_media.py`, wired as the `visual` level in `assemble()`
(escalates after OCR fails / with `--level visual` or `full`).

Model: `Qwen/Qwen3-VL-2B-Instruct` (Apache-2.0), natively supported by `transformers`
(`Qwen3VLForConditionalGeneration` — no `trust_remote_code`, so it won't break when the
shared workspace venv's `transformers` gets upgraded by another tool).

Rejected: `moondream2` / `moondream-2b-*-4bit` — smaller (2.3-4GB VRAM vs Qwen3-VL's
~4.3GB) but both revisions' `trust_remote_code` custom modeling files are already broken
by workspace's `transformers==5.9.0` (API drift: `int4_weight_only` removed from
`torchao`, `all_tied_weights_keys` renamed upstream). Not worth chasing pinned-version
compat in a shared venv other tools also upgrade.

Deps (already in venv as of 2026-07-22, only `accelerate`/`torchao` were missing):
```bash
"$(sh core/run --python)" -m pip install accelerate      # required for device_map=
```
`torch`, `transformers`, `pillow` already present (whisper/general deps).

Measured on RTX 3050 6GB Laptop: ~4.3GB VRAM peak, fp16, ~1.7s/frame after model load
(first load downloads ~4GB weights, cached after in `~/.cache/huggingface`). Model is
config data (`model_id` param), swap freely.

## Image posts / carousels — the gallery-dl path
`video_images.py`. yt-dlp is a *video* downloader: an Instagram `/p/` carousel checks as a hard
failure ("No video formats found" per sub-item), which read like an auth problem for days but
never was. `assemble()` now retries through **gallery-dl** whenever the yt-dlp check fails, so the
fallback costs nothing on video links and needs no flag.

gallery-dl carries its own metadata (`-j`): description, uploader, image count — so image posts
get a real L0 and `--level auto` usually stops there, free. Deeper levels download the images
(capped at `MAX_IMAGES = 10`) and run the same OCR (L3) and VLM captioning (L4) the video path
uses, one pass per image, each line tagged `[n/total]` so a slide deck stays ordered.

Same cookie jar as yt-dlp (`~/.config/workspace-video/cookies.txt`), attached the same way.

```bash
"$(sh core/run --python)" -m pip install gallery-dl
core/run tools/video/video "https://www.instagram.com/p/<id>/"              # description, free
core/run tools/video/video "https://www.instagram.com/p/<id>/" --level ocr  # + slide text per image
```

A carousel post returns its full caption at `auto` and one OCR block per slide at `--level ocr`.

## Rejected — automatic goal relevance
An embedding ranker (`video_relevance.py`, `--goals` flag, multilingual e5) scored the extracted
text against every `brain/goals/*.md` to suggest a route. It was built, dogfooded over ten real
INBOX links, and does not exist any more. Recorded here only so nobody rebuilds it.

Why it failed: two goals acted as false attractors — `rpg-isoroll` took #1 for nearly any
technical clip (PDF parsing, compiler tuning) because its file is long and vocabulary-diverse,
and `smartphone-addiction` surfaced on anything screen-adjacent. Swapping e5-small→e5-base and
lengthening the input helped a little; neither fixed it. A hubness correction (subtracting each
goal's mean similarity to the others) was tested and made one case worse. Truncating goal text to
title-plus-first-paragraph also ranked badly.

The deeper reason it can't be patched: an agent reading the extracted text routes correctly and
is already in the loop for every `/inbox` run, so the ranker duplicated a job something else does
better while adding a confident-looking wrong answer. Its only non-duplicated use would be
tagging a capture with **no agent present** (aiwbot on the phone, where capture is deliberately
$0). If that need ever appears, start from this note — not from the assumption that embeddings
over whole goal files will work.

Code: workspace commit `a9cadd5`. `sentence-transformers` and the cached e5 weights were removed
with it.

## Test
```bash
verify.py fast     # T0+T1, no network — the contract the pre-commit gate discovers and runs
verify.py full     # adds the network-marked cases: live yt-dlp against real URLs
```
