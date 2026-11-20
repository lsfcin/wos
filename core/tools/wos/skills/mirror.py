# Mirror generation for the skill library: listing, copy mirrors, command-file copies, and orphan
# pruning. A LIBRARY, not an entrypoint — core/tools/wos/sync-skills drives it and owns the CLI.
#
# PORTED FROM BASH 2026-09-01. The bash spent ~300 forks per run (a `basename` per skill per
# mirror, a `cmp` per copy, and one whole Python interpreter per command file inside
# render_command) which cost 22 s on a Windows clone at ~48 ms a fork. Nothing here forks.
from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]   # skills → wos → tools → core → workspace
sys.path.insert(0, str(ROOT / 'core' / 'hooks'))

import feature_law as law  # noqa: E402  — path is set above, which is the house pattern


def is_skill(name: str) -> bool:
    """Skill name is the basename without .md, excluding non-skill files.

    AGENTS.md: UPPERCASE.md is a TYPE, lowercase.md is an instance. A skill is an instance, so no
    type is ever one — this used to name CONTEXT alone, and the first SPECS.md written inside
    core/skills/ was read as a skill with no frontmatter and failed the commit for every staged
    core/skills/*.md, not just its own.
    """
    return not (name == '_template' or name[:1].isupper() or name.endswith('.original'))


def is_command(name: str, src: Path) -> bool:
    """A command (slash command) is a top-level skill — NOT a sub-skill.

    Sub-skills have names like "foundry-canvas" where "foundry" is also a skill; they're reference
    docs loaded by the parent router, not invocable commands.
    """
    if '-' not in name:
        return True
    prefix = name.split('-', 1)[0]
    return not (is_skill(prefix) and (src / f'{prefix}.md').is_file())


def disabled() -> set:
    """The whole `skills` group's wiring point (core/SPECS.md § AD-14). A skill is markdown and
    calls no function, so its only real "off" is the mirror declining to publish it — which means
    one filter here switches all fourteen rows, and the honesty test is a behavioural check rather
    than a grep for a call site that could not exist.

    Asked fresh rather than cached: the ablation switch is an environment variable, and a module
    that remembered the first answer would report the pre-ablation set for the rest of the process.
    It is two small text files, so the cache the bash needed to avoid a subprocess buys nothing.
    """
    return set(law.disabled())


def list_skills(src: Path) -> list:
    off = disabled()
    return [f.stem for f in sorted(src.glob('*.md'))
            if is_skill(f.stem) and f.stem not in off]


def list_commands(src: Path) -> list:
    return [name for name in list_skills(src) if is_command(name, src)]


def payload(src: Path, name: str, destination: Path) -> dict:
    """A flat router and its source-relative dependency tree; links target canonical files."""
    sources = {Path('SKILL.md'): src / f'{name}.md'}
    tree = src / name
    if tree.is_dir():
        for path in sorted(tree.rglob('*')):
            if path.is_file() and not any(part.startswith(('.', '_')) for part in path.relative_to(tree).parts):
                sources[Path(name) / path.relative_to(tree)] = path
    return {relative: (render_command(source, source.parent, (destination / relative).parent).encode('utf-8')
                       if source.suffix == '.md' else source.read_bytes())
            for relative, source in sources.items()}


def sync_mirror(mirror: Path, src: Path, names: list) -> None:
    for name in names:
        destination = mirror / name
        expected = payload(src, name, destination)
        for path in destination.rglob('*'):
            if path.is_file() and path.relative_to(destination) not in expected:
                path.unlink()
        for relative, body in expected.items():
            path = destination / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.is_file() or path.read_bytes() != body:
                path.write_bytes(body)


def check_mirror(mirror: Path, src: Path, names: list) -> list:
    problems = []
    for name in names:
        destination = mirror / name
        expected = payload(src, name, destination)
        for relative, body in expected.items():
            path = destination / relative
            if not path.is_file():
                problems.append(f'MISSING mirror: {path}')
            elif path.read_bytes() != body:
                problems.append(f'STALE mirror: {path}')
        for path in destination.rglob('*'):
            if path.is_file() and path.relative_to(destination) not in expected:
                problems.append(f'ORPHAN mirror file: {path}')
    return problems


# Code spans and fences quote syntax rather than link to it — `[what it is](url)` in
# core/skills/inbox.md is the shape a ref entry must take, not a path to fix.
PROTECTED_OR_LINK = re.compile(r'(```.*?```|`[^`\n]+`)|\]\(([^)\s]+)\)', re.DOTALL)


def render_command(source: Path, src_dir: Path, dst_dir: Path) -> str:
    """Rebase Markdown links against their canonical source, preserving code and line endings."""
    def rewrite(match: re.Match) -> str:
        if match.group(1):
            return match.group(0)
        path, sep, frag = match.group(2).partition('#')
        if not path or path.startswith(('http://', 'https://', 'mailto:')):
            return match.group(0)
        absolute = os.path.normpath(os.path.join(str(src_dir), path))
        rebased = Path(os.path.relpath(absolute, str(dst_dir))).as_posix()
        return '](' + rebased + sep + frag + ')'

    with open(source, encoding='utf-8', newline='') as handle:
        return PROTECTED_OR_LINK.sub(rewrite, handle.read())


def sync_commands(commands_dir: Path, src: Path, names: list) -> None:
    commands_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        with open(commands_dir / f'{name}.md', 'w', encoding='utf-8', newline='') as handle:
            handle.write(render_command(src / f'{name}.md', src, commands_dir))


def check_commands(commands_dir: Path, src: Path, names: list) -> list:
    problems = []
    for name in names:
        command, source = commands_dir / f'{name}.md', src / f'{name}.md'
        if not command.is_file():
            problems.append(f'MISSING command: {command}')
            continue
        with open(command, encoding='utf-8', newline='') as handle:
            if handle.read() != render_command(source, src, commands_dir):
                problems.append(f'STALE command: {command} (differs from rendered {source})')
    return problems


def orphans(prune: bool, mirrors: list, commands_dir: Path, src: Path) -> list:
    """A mirror dir or command file with no corresponding source skill is an orphan. Orphans are
    the failure that dangles symlinks and breaks opencode startup.

    A switched-off skill's leftover mirror is an orphan too: publishing is the only thing "off"
    means here, so a stale copy would leave the feature half-disabled.
    """
    off, lines = disabled(), []
    for mirror in mirrors:
        for entry in sorted(p for p in mirror.glob('*') if p.is_dir()):
            name = entry.name
            if is_skill(name) and (src / f'{name}.md').is_file() and name not in off:
                continue
            if prune:
                shutil.rmtree(entry)
                lines.append(f'pruned orphan mirror: {entry}{os.sep}')
            else:
                lines.append(f'ORPHAN mirror (no source skill): {entry}{os.sep}')
    for command in sorted(commands_dir.glob('*.md')):
        name = command.stem
        if (src / f'{name}.md').is_file() and is_command(name, src) and name not in off:
            continue
        if prune:
            command.unlink()
            lines.append(f'pruned orphan command: {command}')
        else:
            lines.append(f'ORPHAN command (no source skill): {command}')
    return lines
