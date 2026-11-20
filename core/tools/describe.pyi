from _typeshed import Incomplete
from typing import NamedTuple

ROOT: Incomplete
THRESHOLD: float
MAX_SIDE: int
TIMEOUT: int
MIN_WORDS: int
MIN_CONFIDENCE: int
OCR_SCALES: Incomplete
CHAINS: Incomplete
DESCRIBERS: Incomplete
LOCAL_MODEL: Incomplete
CLAUDE_LEVEL: str
FIGURE_PROMPT: str
FRAME_PROMPT: str
WORD: Incomplete

class Description(NamedTuple):
    text: str
    by: str | None
    overlap: float | None
    needs_review: bool

def ocr(image, lang: str = 'por+eng') -> str: ...
def overlap(ocr_text: str, description: str) -> float | None: ...
def agy_logged_in() -> bool: ...

BACKENDS: Incomplete

def describe(image, describer: str = 'agy', ocr_text: str = '', prompt: str = ..., backends: dict | None = None) -> Description: ...
