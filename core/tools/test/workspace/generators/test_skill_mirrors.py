# Skill mirrors retain dependencies, resolve relocated links, and remove stale generated files.
import importlib.util
from pathlib import Path

from conftest import WORKSPACE_ROOT


def mirror():
    path = WORKSPACE_ROOT / 'core/tools/wos/skills/mirror.py'
    spec = importlib.util.spec_from_file_location('tested_mirror', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_suite_files_and_links_survive_relocation(tmp_path):
    src, dst = tmp_path / 'source', tmp_path / 'mirror'
    (src / 'lesson/refs').mkdir(parents=True)
    (src / 'lesson.md').write_text('# Lesson\n[Leaf](lesson/leaf.md)\n', encoding='utf-8', newline='\n')
    (src / 'lesson/leaf.md').write_text('# Leaf\n[Reference](refs/source.txt)\n', encoding='utf-8', newline='\n')
    (src / 'lesson/refs/source.txt').write_text('evidence', encoding='utf-8', newline='\n')
    m = mirror()
    m.sync_mirror(dst, src, ['lesson'])
    assert (dst / 'lesson/lesson/refs/source.txt').read_text(encoding='utf-8') == 'evidence'
    assert m.check_mirror(dst, src, ['lesson']) == []
    import re
    for path in dst.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            assert (path.parent / target).resolve().is_file(), (path, target)
    (dst / 'lesson/lesson/leaf.md').write_text('stale', encoding='utf-8', newline='\n')
    assert m.check_mirror(dst, src, ['lesson'])
    (src / 'lesson/refs/source.txt').unlink()
    m.sync_mirror(dst, src, ['lesson'])
    assert not (dst / 'lesson/lesson/refs/source.txt').exists()
    assert m.check_mirror(dst, src, ['lesson']) == []


def test_disabled_suite_is_pruned_and_global_directory_is_not_duplicated(tmp_path, monkeypatch):
    src, dst, commands = tmp_path / 'src', tmp_path / 'dst', tmp_path / 'commands'
    (src / 'global').mkdir(parents=True)
    (src / 'global/SKILL.md').write_text('# Global\n', encoding='utf-8', newline='\n')
    (src / 'lesson.md').write_text('# Lesson\n', encoding='utf-8', newline='\n')
    m = mirror()
    monkeypatch.setattr(m, 'disabled', lambda: set())
    assert m.list_skills(src) == ['lesson']
    m.sync_mirror(dst, src, ['lesson'])
    monkeypatch.setattr(m, 'disabled', lambda: {'lesson'})
    assert m.list_skills(src) == []
    assert m.orphans(True, [dst], commands, src)
    assert not (dst / 'lesson').exists()
