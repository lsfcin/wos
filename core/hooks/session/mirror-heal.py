#!/usr/bin/env python3
# SessionStart — regenerate the generated content that a `git pull` cannot bring with it, and
# report the generated content that must NOT regenerate itself.
#
# WHY THIS HOOK EXISTS (ISSUES.md, 2026-09-01). The ruling that let the skill mirrors leave git is
# in core/hooks/postedit/sync.sh: generated content may be untracked PROVIDED regeneration is
# automatic. The same comment enumerates where that happens -- install, edit, create, and delete
# one commit behind. Every one of those moments belongs to the machine that AUTHORS. None belongs
# to the machine that RECEIVES. So the premise held on exactly half of a two-machine workspace, and
# the Windows clone arrived with no skill mirrors at all: no /inbox, /compass, /roundup, /craft or
# /install, every source present, and every check that could run saying nothing.
#
# WHY SessionStart AND NOT A GIT post-merge (ruled by Lucas). Both would run on the receiving
# machine, so that is not the discriminator. The consumer of a mirror is the SESSION, and a pull
# that lands while a session is open is a change arriving after the harness has already read its
# skill list. Registering here catches both.
#
# WHY IT COULD NOT BE BUILT UNTIL NOW: `sync-skills --check` cost 22 s while it was bash, and a
# SessionStart hook may not. It is 0.3 s ported, which is what unblocked this file.
#
# SKILLS ARE HEALED IN SILENCE, PERMISSIONS ARE ONLY REPORTED. A mirror is a derived copy of a
# source already in the tree, so rewriting one can lose nothing. A permission level is a CHOICE,
# and one that arrived over the network should not apply itself to this machine without Lucas
# seeing it. Same class of drift, opposite answer, and the asymmetry is the point.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from platform_law import WORKSPACE_ROOT  # noqa: E402

RUN = ['sh', str(WORKSPACE_ROOT / 'core' / 'run')]
TIMEOUT = 120


def _tool(*args) -> subprocess.CompletedProcess:
    """A tool, through the launcher, never through a spelled interpreter. Output is captured
    because this hook decides what reaches the session; the tools print for a terminal."""
    return subprocess.run([*RUN, *args], cwd=WORKSPACE_ROOT, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, encoding='utf-8', errors='replace',
                          timeout=TIMEOUT)


def heal_skills() -> str:
    """Regenerate the mirrors when they disagree with core/skills/. One line, only when it acted."""
    if _tool('tools/wos/sync-skills', '--check').returncode == 0:
        return ''
    done = _tool('tools/wos/sync-skills')
    if done.returncode != 0:
        return ('⚠  skill mirrors are stale and could not be regenerated — run '
                '`core/run tools/wos/sync-skills` to see why.')
    return f'↑ skill mirrors regenerated ({done.stdout.strip()})'


def report_permissions() -> str:
    """Never writes. A level arriving over the network is Lucas's call, not this hook's."""
    if _tool('tools/wos/permissions', '--check').returncode == 0:
        return ''
    return ('⚠  harness permission configs no longer match core/profile.txt — run '
            '`core/run tools/wos/permissions --check` to see the drift, then '
            '`--set <level>` if the profile is right.')


def main() -> int:
    """Never blocks and never raises: this runs before the session exists, and a traceback where a
    verdict belonged is the failure mode core/hooks/SPECS.md names for every reporting hook."""
    if not feature_law.is_enabled('skill-mirrors'):
        return 0
    lines = []
    for step in (heal_skills, report_permissions):
        try:
            said = step()
        except Exception as failure:                                  # noqa: BLE001
            said = f'⚠  {step.__name__} did not run ({type(failure).__name__}).'
        if said:
            lines.append(said)
    if lines:
        sys.stdout.write('\n'.join(lines) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
