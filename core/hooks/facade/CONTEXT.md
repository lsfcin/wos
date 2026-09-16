# facade
> The facade discipline: read the facade before editing, never import around it.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`check-facade-imports.py`](check-facade-imports.py) | [`check-facade-imports.pyi`](check-facade-imports.pyi) | `ts_violations`, `py_violations`, `dart_violations`, `check` | Blocks cross-module imports that bypass facade files (index.ts / __init__.py). |
| [`facade-gate.py`](facade-gate.py) | [`facade-gate.pyi`](facade-gate.pyi) | `find_nearest_facade`, `main` | PreToolUse: Edit|Write — block code/ module edits until the module's facade has been read. |
| [`facade-scan.py`](facade-scan.py) | [`facade-scan.pyi`](facade-scan.pyi) | — | Pre-Write hook: list existing facade exports before creating a new file in the same module. |
| [`facade-tracker.py`](facade-tracker.py) | [`facade-tracker.pyi`](facade-tracker.pyi) | `main` | PostToolUse: Read — record facade file reads to session state for facade-gate.py. |
<!-- routing:end -->
