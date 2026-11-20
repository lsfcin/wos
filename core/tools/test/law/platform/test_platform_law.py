# T0/T1 the platform boundary: the one module allowed to know what an operating system is, and until
# now the only law module with no test of its own.
#
# WHAT THESE CAN AND CANNOT ASSERT. A test running on one machine sees one arm of every branch here,
# so asserting "apt on Linux" from Windows is impossible and pretending otherwise would be the
# weaker kind of check this workspace names. What IS assertable everywhere is the property the boundary
# exists for: whatever machine this is, the answer is non-empty, it is the same shape, and callers
# never have to spell a platform themselves. That is what each case below pins.
import subprocess
import sys

import platform_law
from conftest import WORKSPACE_ROOT


def test_the_install_command_is_answered_on_whatever_machine_this_is():
    """The failure this guards is a boundary that silently has no answer for the host it runs on."""
    argv = platform_law.package_install('gh')
    assert argv and all(isinstance(part, str) and part for part in argv), argv
    assert argv[0] != 'gh', 'the first word is the package manager, not the package'
    assert 'gh' in argv, 'the package name has to survive into the command'


def test_one_dependency_name_serves_every_package_manager():
    """core/tools/deps.txt gives a dependency ONE name. The boundary is what makes that true.

    Its `name` column claims to be spelled "exactly as the install command spells it" -- a contract
    that held only while one kind of machine read the file. Three managers spell things three ways,
    so either every row forks per OS or the boundary absorbs it. This pins the second.
    """
    for name in ('gh', 'ffmpeg'):
        assert name in platform_law.package_install(name)


def test_the_interpreter_is_the_one_already_running():
    """`python3` is not a name Windows has; sys.executable needs no PATH to be right."""
    assert platform_law.interpreter() == sys.executable


def test_a_path_that_became_data_never_carries_a_backslash():
    """Two machines must agree byte-for-byte about their own contents -- see the module head."""
    spelled = platform_law.posix(WORKSPACE_ROOT / 'core' / 'hooks')
    assert '\\' not in spelled and spelled.endswith('core/hooks')
    assert platform_law.rel(WORKSPACE_ROOT / 'core' / 'hooks') == 'core/hooks'


def test_every_shell_hook_parses_including_the_ones_with_no_extension():
    """verify-fast runs `bash -n` over core/hooks/*.sh and core/hooks/*/*.sh only.

    pre-commit, post-commit and run carry no extension -- git dictates the first two names and the
    third is spawned by every harness shim -- so the three shell files with the widest blast radius
    in this workspace were the three nothing syntax-checked.
    """
    hooks = WORKSPACE_ROOT / 'core/hooks'
    scripts = [p for p in sorted(hooks.rglob('*'))
               if p.is_file() and (p.suffix == '.sh'
                                   or (not p.suffix and p.read_bytes()[:2] == b'#!'))]
    assert len(scripts) >= 4, f'found only {len(scripts)} shell scripts -- the scan stopped working'
    broken = []
    for script in scripts:
        done = subprocess.run(['bash', '-n', str(script)], capture_output=True, text=True, encoding='utf-8')
        if done.returncode != 0:
            broken.append(f'{script.relative_to(WORKSPACE_ROOT).as_posix()}: {done.stderr.strip()}')
    assert not broken, 'shell scripts that will not parse:\n' + '\n'.join(broken)


def _dot_git(tmp_path, kind):
    if kind == 'head':
        (tmp_path / '.git').mkdir()
        (tmp_path / '.git' / 'HEAD').write_text('ref: refs/heads/main\n', encoding='utf-8', newline='\n')
    elif kind == 'file':
        (tmp_path / '.git').write_text('gitdir: ../x\n', encoding='utf-8', newline='\n')
    elif kind == 'empty':
        (tmp_path / '.git').mkdir()


def test_a_repo_is_a_git_dir_with_a_head_or_a_git_file(tmp_path):
    """The Codex sandbox leaves EMPTY `.git` mount points; those are not repos."""
    for kind, expected in (('head', True), ('file', True), ('empty', False), ('none', False)):
        sub = tmp_path / kind
        sub.mkdir()
        _dot_git(sub, kind)
        assert platform_law.is_repo(sub) is expected, kind
        assert platform_law.is_repo(str(sub)) is expected, kind


def test_no_hook_tests_for_a_repo_by_whether_dot_git_exists():
    """One definition of "is a repo": grep the hooks for the bare test it replaces."""
    import re
    bare = re.compile(r"""['"]\.git['"]\)\.(exists|is_dir|is_file)\(""")
    hits = [p for p in (WORKSPACE_ROOT / 'core/hooks').rglob('*.py') if bare.search(p.read_text(encoding='utf-8'))]
    assert not hits, hits
    defs = [p for p in (WORKSPACE_ROOT / 'core').rglob('*.py')
            if re.search(r'^def is_repo\b', p.read_text(encoding='utf-8'), re.M)]
    assert len(defs) == 1, defs
