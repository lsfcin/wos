# video
> Link to navigable text — metadata, captions, transcript, OCR, VLM caption.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SETUP.md`](SETUP.md) | — | — | Dependencies for `core/tools/video/video` (link → navigable text). See goal workspace-os / TODO:121. |
| [`video`](video) | — | — | extract navigable text (metadata/captions/transcript/OCR/VLM caption) from video/image links; a link with no media falls back to core/tools/web/fetch |
| [`video_core.py`](video_core.py) | [`video_core.pyi`](video_core.pyi) | `source_of`, `metadata`, `clean_vtt`, `get_captions`, `assemble` | video_core.py — extract navigable text (metadata, captions, transcript) from video/image URLs; whisper/OCR backends are config data |
| [`video_images.py`](video_images.py) | [`video_images.pyi`](video_images.pyi) | `metadata`, `download_images`, `gather` | video_images.py — image-post path (Instagram carousels etc): gallery-dl metadata + image download, then OCR/VLM per image. yt-dlp reads video only and returns nothing for these. |
| [`video_media.py`](video_media.py) | [`video_media.pyi`](video_media.pyi) | `download_audio`, `download_video`, `transcribe`, `ocr_image`, `sample_frames` | video_media.py — heavy layers for the video tool: audio download + local transcription (L2), frame OCR (L3), frame description (L4). Whisper model + tesseract langs are config data, not names. |
<!-- routing:end -->
