# files
> T1 coverage for files and drive sync tooling.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_drive_sync.py`](test_drive_sync.py) | [`test_drive_sync.pyi`](test_drive_sync.pyi) | — | T1 drive_sync: manifest config, cache with debounce, query diffing, and 4 pillars handling |
| [`test_gdrive_home.py`](test_gdrive_home.py) | [`test_gdrive_home.pyi`](test_gdrive_home.pyi) | `load` | T1 home account: a one-account Google command without --account lands on the workspace's own account (the first configured), never asks. |
<!-- routing:end -->
