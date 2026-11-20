# files
> Remote file storage: list, search, download, upload. Provider leaves: `gdrive`, `onedrive` (rclone).

`onedrive put deck.pptx --to slides` prints the private web link that opens the deck in PowerPoint online; `onedrive pdf slides/deck.pptx --out d.pdf` is Office's own render of it (the fonts online really has); `link` is the PUBLIC one, and `rclone link --unlink` does NOT revoke it on a personal drive: DELETE the anonymous permission through Graph. Login lives in `~/.config/workspace-onedrive/`.

Auth is two tokens, not one: reads use the `drive` token (`drive.readonly`), and `mkdir` / `put` use a separate `drive-write` one. A read re-consent therefore leaves the write token dead —
`gdrive auth <alias> --write --reauth` is a different command, and the recovery message says so.
Downloads land in `Downloads/workspace-drive` at the workspace root. The workspace's Google account is `personal`: every one-account command (gdrive, gdocs, gslides, gforms) without `--account` goes there — `gauth.home_alias()`, the first in `accounts.json`. Never ask which.

`put --sheet` imports a CSV in the account's locale: `personal` is pt-BR, so write `"414,36"`, not `414.36` — a dot decimal lands as text and every `=formula` over it reads `#VALUE!`.

`drive_migrate.py` is not part of the CLI — it is a standing account-to-account copy (`cin` → `personal`), idempotent, run by path.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`drive_core.py`](drive_core.py) | [`drive_core.pyi`](drive_core.pyi) | `get_service`, `list_files`, `search_files`, `recent_files`, `download_file` | drive_core.py — Google Drive read+write boundary (account-agnostic) for Core/tools/files/gdrive |
| [`drive_migrate.py`](drive_migrate.py) | [`drive_migrate.pyi`](drive_migrate.pyi) | `migrate_recursive`, `run` | Migrate CIn Drive Disciplinas → personal Drive Academy/Teaching/ |
| [`drive_migrate_core.py`](drive_migrate_core.py) | [`drive_migrate_core.pyi`](drive_migrate_core.pyi) | `get_cin_service`, `get_personal_service` | Auth, config, and low-level Drive ops shared by drive_migrate.py. |
| [`drive_sync.py`](drive_sync.py) | [`drive_sync.pyi`](drive_sync.pyi) | `load_config`, `save_config`, `load_cache`, `save_cache`, `is_debounce_active` | drive_sync.py — Google Drive hybrid sync engine with debounce and manifest caching |
| [`gdrive`](gdrive) | — | — | Google Drive read+write CLI for workspace OS — commands: auth, recent, list, search, download, mkdir, put, copy, rename, perms, share, rm, sync |
| [`onedrive`](onedrive) | — | — | OneDrive through rclone: upload, download, list, delete to the recycle bin, the web link that opens a .pptx in PowerPoint online, and Office's own PDF of it |
<!-- routing:end -->
