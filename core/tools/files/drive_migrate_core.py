#!/usr/bin/env python3
"""
Auth, config, and low-level Drive ops shared by drive_migrate.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from googleapiclient.errors import HttpError  # noqa: F401 (re-exported for drive_migrate.py)
# Drive read+write ops live in the shared boundary; re-exported for drive_migrate.py.
from drive_core import (  # noqa: F401
    get_service,
    list_folder,
    find_or_create_folder,
    copy_file,
    SCOPES_READ,
    SCOPES_WRITE,
)

# ── Config ───────────────────────────────────────────────────────────────────

CIN_DISCIPLINAS_ID = "1xihkjDlbpIxjRmAJeCWIrBvFT37Qe6IM"

# Named for slides because that is all it copied until 2026-08-26, when the AI4Good migration
# came up nine files short: three spreadsheets, a document and a form were never presentations,
# so the filter never saw them. A discipline's material is not only its decks.
SLIDE_MIMETYPES = {
    "application/vnd.google-apps.presentation",               # native Google Slides
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    "application/vnd.ms-powerpoint",                          # .ppt
    "application/vnd.google-apps.document",                   # native Google Docs
    "application/vnd.google-apps.spreadsheet",                # native Google Sheets
    "application/vnd.google-apps.form",                       # native Google Forms
}

FOLDER_MAP = {
    "Tec. na Educação":                 "techedu",
    "AI4Good":                          "ai4good",
    "P1":                               "programacao-1",
    "Computação Gráfica":               "computacao-grafica",
    "Motores Gráficos":                 "motores-graficos",
    "IA":                               "inteligencia-artificial",
    "P2":                               "programacao-2",
    "PGP":                              "gerencia-de-projetos",
    "PI1":                              "projeto-interdisciplinar-1",
    "PI2":                              "projeto-interdisciplinar-2",
    "PI3":                              "projeto-interdisciplinar-3",
    "Intro à Informática (Ed. Física)": "info-ed-fisica",
    "Apps p/ Gastro":                   "apps-gastronomia",
}

STATE_FILE = Path("academy_migration_state.json")
MAP_FILE   = Path("academy_migration_map.json")

# ── Auth (migration-specific account wrappers over the shared boundary) ────────────

def get_cin_service():
    return get_service("cin")                 # cin = source, read-only

def get_personal_service():
    return get_service("personal", write=True)  # personal = destination, write
