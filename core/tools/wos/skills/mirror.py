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


# A MIRROR IS A COPY, AND THE CHECK ASKS ABOUT ITS CONTENT.
#
# These were symlinks, and `ln -s` under Git Bash silently COPIES unless MSYS=winsymlinks:
# nativestrict, which needs Developer Mode. So the writer produced files, the checker demanded
# links, and every mirror reported `MISSING link` — the skills stage of the pre-commit pipeline
# then refused every commit that touched a skill. It is the only gate in the workspace that can
# refuse a commit for a reason the commit did not cause. Worse, git had already materialised the
# tracked mirrors as ordinary files holding their target's PATH TEXT, eleven characters where a
# skill body belonged, so the library was dark in this clone while every file was present and every
# link check that could run said nothing.
#
# Copying removes the per-OS axis instead of adding an arm for it — the port's own thesis, and
# ISSUES.md B8's decision. What a symlink bought was freshness, and freshness is now a regeneration
# at the moments that change a skill, not a property of the file kind.
#
# BYTES, NOT TEXT, on both the write and the compare. The sources are CRLF in a Windows clone and
# LF in a POSIX one; a text-mode copy would rewrite line endings and make every mirror read as
# stale exactly once per machine, on a difference no reader of a skill can see.
def sync_mirror(mirror: Path, src: Path, names: list) -> None:
    for name in names:
        (mirror / name).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src / f'{name}.md', mirror / name / 'SKILL.md')


def check_mirror(mirror: Path, src: Path, names: list) -> list:
    problems = []
    for name in names:
        copy, source = mirror / name / 'SKILL.md', src / f'{name}.md'
        if not copy.is_file():
            problems.append(f'MISSING mirror: {copy}')
        elif copy.read_bytes() != source.read_bytes():
            problems.append(f'STALE mirror: {copy} (differs from {source})')
    return problems


# Code spans and fences quote syntax rather than link to it — `[what it is](url)` in
# core/skills/inbox.md is the shape a ref entry must take, not a path to fix.
PROTECTED_OR_LINK = re.compile(r'(```.*?```|`[^`\n]+`)|\]\(([^)\s]+)\)', re.DOTALL)


def render_command(source: Path, src_dir: Path, dst_dir: Path) -> str:
    """A command file is the skill body relocated to a different directory depth, so a straight
    copy leaves every relative link pointing at nothing: `../flows/x.md` in core/skills/ means
    core/flows/x.md, but from .claude/commands/ it resolves to .claude/flows/x.md. All 6 relative
    links across the mirrors were dead this way (found 2026-07-30). Rewrite them against the source
    dir on the way out; the staleness check compares the same rendered form, or every file reads as
    stale.

    newline='' on the read, and on every write of this text: the rewrite is about link targets, and
    a function that also silently normalised line endings would make the whole corpus look stale
    the first time it ran on either machine.

    as_posix() ON THE RESULT, AND THIS IS THE BUG THE PORT CAME FOR (found 2026-09-01). A markdown
    link separator is `/` everywhere; `os.path.relpath` returns the OS-native one. So on a Windows
    clone this function published `](..\\..\\core\\skills\\roundup.md)` -- 16 dead links across 5
    command files, which is the SAME failure this function exists to fix, reintroduced by the
    operating system underneath it. It read as fixed because the machine that authored the fix
    spells the separator the way markdown wants.
    """
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
