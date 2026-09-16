#!/usr/bin/env python3
"""
Migrate CIn Drive Disciplinas → personal Drive Academy/Teaching/

Prerequisite: CIn Disciplinas folder shared with lsf.cin@gmail.com (viewer).

Usage:
  python3 core/tools/files/drive_migrate.py --dry-run   # preview what will be copied
  python3 core/tools/files/drive_migrate.py             # execute migration
  python3 core/tools/files/drive_migrate.py             # re-run skips already-copied files (idempotent)

Output:
  academy_migration_map.json  — cin_id → personal_id + URL for each file
                                (used later to generate slides.md per discipline)
"""

import argparse
import json
import time

from drive_migrate_core import (
    CIN_DISCIPLINAS_ID,
    FOLDER_MAP,
    MAP_FILE,
    STATE_FILE,
    SLIDE_MIMETYPES,
    HttpError,
    copy_file,
    find_or_create_folder,
    get_cin_service,
    get_personal_service,
    list_folder,
)

# ── Recursive migration ───────────────────────────────────────────────────────

def migrate_recursive(cin_svc, personal_svc, cin_folder_id: str, personal_parent_id: str,
                      state: dict, dry_run: bool, indent: int = 0) -> list:
    pad = "  " * indent
    items = list_folder(cin_svc, cin_folder_id)
    results = []

    for item in items:
        name   = item["name"]
        cin_id = item["id"]
        mime   = item["mimeType"]

        if mime == "application/vnd.google-apps.folder":
            personal_sub = find_or_create_folder(personal_svc, name, personal_parent_id, dry_run)
            print(f"{pad}📁  {name}/")
            children = migrate_recursive(
                cin_svc, personal_svc, cin_id, personal_sub, state, dry_run, indent + 1)
            if children:
                results.append({
                    "type": "folder", "name": name,
                    "cin_id": cin_id, "personal_id": personal_sub,
                    "children": children,
                })
        elif mime not in SLIDE_MIMETYPES:
            pass  # skip non-presentation files
        else:
            if cin_id in state.get("copied", {}):
                print(f"{pad}↷  {name}  (skipped — already copied)")
                results.append(state["copied"][cin_id])
                continue

            if dry_run:
                print(f"{pad}→  {name}")
                results.append({"name": name, "cin_id": cin_id})
            else:
                print(f"{pad}→  {name} ...", end="", flush=True)
                try:
                    copied = copy_file(personal_svc, cin_id, name, personal_parent_id)
                    entry = {
                        "type": "file",
                        "name": name,
                        "cin_id": cin_id,
                        "personal_id": copied["id"],
                        "url": copied.get("webViewLink", ""),
                    }
                    state.setdefault("copied", {})[cin_id] = entry
                    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
                    print(f" ✓")
                    results.append(entry)
                    time.sleep(0.3)  # stay under quota
                except HttpError as e:
                    print(f" ✗ {e}")
                    results.append({"name": name, "cin_id": cin_id, "error": str(e)})

    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def run(dry_run: bool) -> None:
    print("Authenticating cin (read)...")
    cin_svc = get_cin_service()
    print("Authenticating personal (write) — browser will open for first-time auth...")
    personal_svc = get_personal_service()

    state = json.loads(STATE_FILE.read_text(encoding='utf-8')) if STATE_FILE.exists() else {}

    print("\nCreating Academy/Teaching in personal Drive...")
    academy_id  = find_or_create_folder(personal_svc, "Academy",  "root", dry_run)
    teaching_id = find_or_create_folder(personal_svc, "Teaching", academy_id, dry_run)

    print(f"\nListing CIn Disciplinas...")
    cin_items   = list_folder(cin_svc, CIN_DISCIPLINAS_ID)
    cin_folders = {f["name"]: f for f in cin_items
                   if f["mimeType"] == "application/vnd.google-apps.folder"}

    full_map = {}

    for cin_name, ws_name in FOLDER_MAP.items():
        if cin_name not in cin_folders:
            print(f"\n⚠  Not found in CIn: '{cin_name}'  (skipping)")
            continue

        cin_folder = cin_folders[cin_name]
        print(f"\n── {cin_name}  →  {ws_name}")

        personal_folder_id = find_or_create_folder(
            personal_svc, ws_name, teaching_id, dry_run)

        files = migrate_recursive(
            cin_svc, personal_svc,
            cin_folder["id"], personal_folder_id,
            state, dry_run, indent=1)

        full_map[ws_name] = {
            "cin_folder_id":      cin_folder["id"],
            "personal_folder_id": personal_folder_id,
            "files":              files,
        }

    MAP_FILE.write_text(json.dumps(full_map, indent=2, ensure_ascii=False), encoding='utf-8', newline='\n')
    tag = "DRY RUN — " if dry_run else ""
    print(f"\n{tag}Done. Map saved to {MAP_FILE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — no files copied, no folders created")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
