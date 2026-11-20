from dataclasses import dataclass, field
from pathlib import Path

HASH_SIDE: int
DECORATIVE_PAGES: int
PREVIEW_SIDE: int
PREVIEW_QUALITY: int
EMBEDDED_MIN_SIDE: int

@dataclass
class Figure:
    name: str
    page: int
    source: Path
    look: str
    same_as: str | None = ...
    decorative: bool = ...
    pages: set = field(default_factory=set)

def look(image: Path) -> str: ...
def name_all(engine_figures: list[dict], total_pages: int) -> list[Figure]: ...
def embedded_count(pdf: Path) -> int: ...
def save(fig: Figure, img_dir: Path, preview: bool) -> str: ...
def block(fig: Figure, link: str, description=None, ocr_text: str = '') -> str: ...
