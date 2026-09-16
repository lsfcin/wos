# Caveman memory compression orchestrator: compress, back up, validate, retry, restore.
"""
Usage:
    python3 -m scripts <filepath>

The valuable part is the failure handling, not the compression: the original is
only overwritten after a verified backup readback, and a failed validation run
restores it. Prompts live in prompts.py, the secret-file denylist in safety.py,
the checks in validate.py.
"""

import os
import subprocess
from pathlib import Path

from .detect import should_compress
from .prompts import build_compress_prompt, build_fix_prompt
from .safety import is_sensitive_path, strip_llm_wrapper
from .validate import validate

MAX_RETRIES = 2
MAX_FILE_SIZE = 500_000  # 500KB

# The id the SDK path falls back to, overridable with CAVEMAN_MODEL. Named here as DATA —
# it is which model this call goes to, not an instruction to any agent reading the file.
# The level is upstream's choice and is kept: compression is mechanical, and moving it is a
# spend decision that belongs to whoever runs the tool, not to the session that repaired
# the id. What was broken is only that `claude-sonnet-4-5` no longer resolves.
DEFAULT_MODEL = "claude-sonnet-5"


def call_claude(prompt: str) -> str:
    """SDK when ANTHROPIC_API_KEY is set, else the `claude` CLI (desktop auth)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get("CAVEMAN_MODEL", DEFAULT_MODEL),
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return strip_llm_wrapper(msg.content[0].text.strip())
        except ImportError:
            pass  # anthropic not installed, fall back to CLI
    try:
        result = subprocess.run(
            ["claude", "--print"],
            input=prompt,
            text=True,
            capture_output=True,
            check=True, encoding='utf-8'
        )
        return strip_llm_wrapper(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Claude call failed:\n{e.stderr}")


def _check_input(filepath: Path) -> None:
    """Raise unless the file is safe to read and ship. Refusals are loud by design."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if filepath.stat().st_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large to compress safely (max 500KB): {filepath}")
    if is_sensitive_path(filepath):
        raise ValueError(
            f"Refusing to compress {filepath}: filename looks sensitive "
            "(credentials, keys, secrets, or known private paths). "
            "Compression sends file contents to the Anthropic API. "
            "Rename the file if this is a false positive."
        )


def _reject_bad_output(compressed: str, original_text: str) -> bool:
    """True when the model's output must not be written. Original stays untouched."""
    if compressed is None or not compressed.strip():
        print("❌ Compression aborted: Claude returned an empty response.")
        print("   Original file is untouched (no backup created).")
        return True
    if compressed.strip() == original_text.strip():
        print("❌ Compression aborted: output is identical to input.")
        print("   Likely causes: Claude refused, returned the prompt verbatim, or the file is")
        print("   already in caveman form. Original file is untouched (no backup created).")
        return True
    return False


def _write_verified_backup(backup_path: Path, original_text: str) -> bool:
    """Write the backup and read it back. A short write here would cost the original."""
    backup_path.write_text(original_text, encoding='utf-8', newline='\n')
    if backup_path.read_text(errors="ignore", encoding='utf-8') == original_text:
        return True
    print(f"❌ Backup write verification failed: {backup_path}")
    print("   In-memory original differs from on-disk backup. Aborting before touching the input file.")
    try:
        backup_path.unlink()
    except OSError:
        pass
    return False


def _write_compressed(filepath: Path, compressed: str) -> None:
    """Write model output as a text file — which means it ends in a newline.

    `call_claude` strips the response, because a model that answers with a leading blank
    line or a trailing fence would otherwise write that into the file. Stripping the
    trailing newline too is a side effect, not the intent: every compressed file came out
    without its final newline, so `git diff` reported `\\ No newline at end of file` on a
    pass whose whole job was to leave the file otherwise intact. Restored here, at the one
    place model output reaches the disk, rather than in `call_claude` — the strip there is
    still what we want from a response.
    """
    filepath.write_text(compressed.rstrip('\n') + '\n', encoding='utf-8', newline='\n')


def _validate_with_retries(filepath: Path, backup_path: Path, compressed: str,
                           original_text: str) -> bool:
    """Validate, and on failure ask for targeted fixes. Restore the original if it never passes."""
    for attempt in range(MAX_RETRIES):
        print(f"\nValidation attempt {attempt + 1}")
        result = validate(backup_path, filepath)

        if result.is_valid:
            print("Validation passed")
            return True

        print("❌ Validation failed:")
        for err in result.errors:
            print(f"   - {err}")

        if attempt == MAX_RETRIES - 1:
            filepath.write_text(original_text, encoding='utf-8', newline='\n')
            backup_path.unlink(missing_ok=True)
            print("❌ Failed after retries — original restored")
            return False

        print("Fixing with Claude...")
        compressed = call_claude(build_fix_prompt(original_text, compressed, result.errors))
        _write_compressed(filepath, compressed)
    return True


def compress_file(filepath: Path) -> bool:
    filepath = filepath.resolve()
    _check_input(filepath)

    print(f"Processing: {filepath}")
    if not should_compress(filepath):
        print("Skipping (not natural language)")
        return False

    original_text = filepath.read_text(errors="ignore", encoding='utf-8')
    if not original_text.strip():
        print("❌ Refusing to compress: file is empty or whitespace-only.")
        return False

    backup_path = filepath.with_name(filepath.stem + ".original.md")
    if backup_path.exists():
        print(f"⚠️ Backup file already exists: {backup_path}")
        print("The original backup may contain important content.")
        print("Aborting to prevent data loss. Please remove or rename the backup file if you want to proceed.")
        return False

    print("Compressing with Claude...")
    compressed = call_claude(build_compress_prompt(original_text))
    if _reject_bad_output(compressed, original_text):
        return False

    if not _write_verified_backup(backup_path, original_text):
        return False
    _write_compressed(filepath, compressed)

    return _validate_with_retries(filepath, backup_path, compressed, original_text)
