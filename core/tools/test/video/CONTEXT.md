# video
> T1 unit tests for the video tool. Fixtures live here; network-marked cases are excluded from verify-fast.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`fixtures/ytdlp_dump.json`](fixtures/ytdlp_dump.json) | — | — | One recorded `yt-dlp -J` answer — what the video tool's metadata read parses, without the network. |
| [`test_video_cli.py`](test_video_cli.py) | [`test_video_cli.pyi`](test_video_cli.pyi) | `bundle` | test_video_cli.py — T1 unit tests for the video CLI's batch path (no network, injected runners) |
| [`test_video_core.py`](test_video_core.py) | [`test_video_core.pyi`](test_video_core.pyi) | `FakeProc`, `FakeMedia`, `ExplodingMedia`, `download_audio`, `transcribe` | test_video_core.py — T0/T1 unit tests for video_core (no network; fixtures + injected runners) |
| [`test_video_images.py`](test_video_images.py) | [`test_video_images.pyi`](test_video_images.pyi) | `FakeProc`, `FakeMedia`, `FakeImages`, `ocr_image`, `caption_image` | test_video_images.py — T1 unit tests for the image-post path (no network, injected runners) |
<!-- routing:end -->
