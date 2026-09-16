"""Caveman compress scripts.

This package provides tools to compress natural language markdown files
into caveman format to save input tokens.

Layering: cli → compress (orchestration) → {safety, prompts, detect, validate},
with validate → extract. Nothing imports upward.
"""

__all__ = ["cli", "compress", "detect", "extract", "prompts", "safety", "validate"]

__version__ = "1.0.0"
