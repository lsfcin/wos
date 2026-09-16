# T0 the shim contract (core/hooks/SPECS.md): every canonical script a provider shim spawns
# must exist. Zero-token, verify-fast.
#
# WHAT THIS PROVES, AND WHAT IT DOES NOT. It proves a path RESOLVES. It does not prove the gate
# fires, which is behavioural and a different test -- so green here means the shim can reach the
# gate, never that the gate works. Said plainly because this workspace's own rule is that a check
# proving a name is present is the weaker kind, and one of ours once passed wrongly on that shape.
#
# WHY IT EXISTS. The 2026-07-31 split moved scripts into read/, checks/ and facade/. All eleven of
# opencode's spawns kept pointing at core/hooks/<script> and were dead for weeks; nothing could
# have noticed, because a second runtime's coverage was claimed in a table rather than checked.
# Repointed 2026-08-18. When this test was written on 2026-08-19 it immediately found THREE MORE,
# in the Copilot shim, from the same split: read/facade-{tracker,gate,scan}.py. Two shims, one
# cause, found a day apart -- which is the argument for a test rather than for another careful
# reading.
import re

from conftest import WORKSPACE_ROOT

CORE = WORKSPACE_ROOT / 'core'
HOOKS = CORE / 'hooks'

# One entry per shim: the files it spawns from, and how a spawn names its script. Derived by
# reading each shim, because the conventions genuinely differ -- opencode interpolates
# `${HOOKS}/`, Copilot passes a relative string to gate() or joins onto a HOOKS Path.
SHIMS = {
    'opencode': (
        [WORKSPACE_ROOT / '.opencode/plugins/workspace-policy.js',
         WORKSPACE_ROOT / '.opencode/wp-helpers.js'],
        re.compile(r'\$\{HOOKS\}/([A-Za-z0-9_./-]+\.(?:py|sh))'),
    ),
    'copilot': (
        [HOOKS / 'copilot/copilot-pre-tool.py',
         HOOKS / 'copilot/copilot-post-tool.py',
         HOOKS / 'copilot/copilot-session-start.py',
         HOOKS / 'copilot/copilot_shared.py'],
        # `*`, not `+`, since 2026-09-05: the shim's one gate spawn is `"dispatch.py"`, which sits
        # at core/hooks/ and carries no directory. Requiring a slash made the pattern blind to the
        # only path that now matters.
        re.compile(r'["\']((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.(?:py|sh))["\']'),
    ),
    # Direct registration, no adapter: both configs spawn canonical scripts through
    # core/run, which resolves this clone's interpreter. The project-dir variable is expanded
    # by the harness, so the same string is correct on every machine and neither file is rewritten
    # at install time. Each config names its own harness's spelling — `${CLAUDE_PROJECT_DIR}` in
    # the claude shim, `${ZCODE_PROJECT_DIR}` in the zcode shim (documented synonyms, so either
    # would expand, but the registration should not wear another harness's name). Trusted
    # 2026-09-04 and firing — see core/experiments/zcode-hook-protocol.md.
    #
    # `.claude/settings.json` was NOT in this table until 2026-08-28, and that gap is why it could
    # carry twenty commands naming a directory that existed on one machine only. The shim this file
    # was written to guard was the one shim it did not read.
    #
    # The captured group is core-relative (`hooks/read/chain.py`) since 2026-08-29, when the
    # launcher moved up to core/run so a tool could be spawned the same way a gate is. HOOKS below
    # is therefore no longer the right base for these two — CORE is.
    'claude': (
        [WORKSPACE_ROOT / '.claude/settings.json'],
        re.compile(r'\$\{CLAUDE_PROJECT_DIR\}/core/run ([A-Za-z0-9_./-]+\.(?:py|sh))'),
    ),
    'zcode': (
        [WORKSPACE_ROOT / '.zcode/config.json'],
        re.compile(r'\$\{ZCODE_PROJECT_DIR\}/core/run ([A-Za-z0-9_./-]+\.(?:py|sh))'),
    ),
    'antigravity': (
        [HOOKS / 'antigravity/antigravity_policy.py'],
        re.compile(r'["\']((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_-]+\.(?:py|sh))["\']'),
    ),
}


# THE REGISTRATION A HARNESS READS, as opposed to the adapter it reaches. Copilot and Antigravity
# both delegate to a shim, so neither config names a gate — what has to be true of them is that
# they spawn through the launcher and that the adapter they name is on disk. Neither file was read
# by anything until 2026-09-06, which is how .github/hooks/workspace-policy.json carried three
# `python3` registrations for weeks past a ratchet that core/hooks/SPECS.md names as their enforcer
# (b20260905). The same self-indictment as the `.claude/settings.json` note above, one shim over.
REGISTRATIONS = {
    '.github/hooks/workspace-policy.json': 'copilot',
    '.agents/hooks.json': 'antigravity',
}


def test_every_registration_spawns_its_shim_through_the_launcher():
    for rel, family in sorted(REGISTRATIONS.items()):
        text = (WORKSPACE_ROOT / rel).read_text(encoding='utf-8')
        named = re.findall(r'sh core/run (hooks/[A-Za-z0-9_./-]+\.(?:py|sh))', text)
        assert named, (
            f'{rel} registers no hook through `sh core/run`, so it spells an interpreter itself. '
            'That is the spelling that reaches a Store alias on Windows and fails green.')
        dead = sorted(p for p in named if not (CORE / p).exists())
        assert not dead, f'{rel} registers paths that do not resolve: {dead}'
        assert any(family in p for p in named), f'{rel} no longer reaches the {family} shim'


def _spawned(shim: str) -> set:
    sources, pattern = SHIMS[shim]
    found = set()
    for source in sources:
        assert source.exists(), f'{shim}: shim file is gone -- {source}'
        found |= set(pattern.findall(source.read_text(encoding='utf-8')))
    return found


def test_every_shim_names_at_least_one_canonical_script():
    """Guards the guard: a regex that stopped matching would make both cases below vacuous."""
    for shim in SHIMS:
        count = len(_spawned(shim))
        assert count >= 2, (
            f'{shim}: found {count} script paths. The shim was rewritten and this pattern no '
            'longer reads it, so the resolution checks are passing on an empty set.'
        )


def test_every_shim_reaches_the_dispatcher():
    """The floor above was five scripts until 2026-09-05, and five was the real check: a shim that
    stopped naming the gates would fall under it. Every PreToolUse gate hangs off ONE entrypoint
    now (core/hooks/dispatch.py, selecting from gates.txt), so the count fell and this case is what
    the count was standing in for. A shim missing it is a harness running with no gates at all,
    reading as correct — the silent-weakening shape b20260901 cost a day to find."""
    for shim in SHIMS:
        assert any(p.endswith('dispatch.py') for p in _spawned(shim)), (
            f'{shim}: names no dispatch.py, so none of the gates in core/hooks/gates.txt reach it'
        )


def test_opencode_spawns_only_scripts_that_exist():
    dead = sorted(p for p in _spawned('opencode') if not (HOOKS / p).exists())
    assert not dead, f'opencode shim spawns paths that do not resolve: {dead}'


def test_copilot_spawns_only_scripts_that_exist():
    dead = sorted(p for p in _spawned('copilot') if not (HOOKS / p).exists())
    assert not dead, f'copilot shim spawns paths that do not resolve: {dead}'


def test_zcode_spawns_only_scripts_that_exist():
    dead = sorted(p for p in _spawned('zcode') if not (CORE / p).exists())
    assert not dead, f'zcode shim spawns paths that do not resolve: {dead}'


def test_claude_spawns_only_scripts_that_exist():
    dead = sorted(p for p in _spawned('claude') if not (CORE / p).exists())
    assert not dead, f'claude shim spawns paths that do not resolve: {dead}'


def test_antigravity_spawns_only_scripts_that_exist():
    dead = sorted(p for p in _spawned('antigravity') if not (HOOKS / p).exists())
    assert not dead, f'antigravity shim spawns paths that do not resolve: {dead}'


def test_opencode_shim_resolves_the_interpreter_through_the_boundary():
    """The positive half of the ban: this shim must still ASK, not merely fail to spell.

    The prohibition itself moved out on 2026-09-06. It was a `spawnSync('python3')` search over
    these two files alone, and b20260905 was the same defect one shim over, in a file type nobody
    grepped. `test_no_shell_hook_spawns_the_bare_word_python3` now covers every registration and
    plugin type in the tree, which is strictly wider — keeping a second copy here would be the
    drift this workspace's checks exist to catch. What it cannot say is this: a shim that stopped
    calling `core/run --python` would spell nothing and pass the ban while resolving nothing."""
    for source in SHIMS['opencode'][0]:
        text = source.read_text(encoding='utf-8')
        assert 'core/run' in text and '--python' in text, (
            f'{source.name} no longer resolves the interpreter through the platform boundary'
        )


def test_the_launcher_every_shim_goes_through_is_there():
    """Both direct shims name `core/run` before naming a gate, so its absence would break
    every gate at once while each individual path above still resolved."""
    launcher = CORE / 'run'
    assert launcher.exists(), f'the shim launcher is gone -- {launcher}'
