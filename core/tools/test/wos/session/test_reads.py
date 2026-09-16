# T1 the read instrument: a Read costs what it was SERVED, and a stub is not a source.
#
# The lens exists to answer whether our own gates cause re-reads, so the two things it must never
# get wrong are (a) sizing a read by its arguments instead of its result — an offset read of a huge
# file would then look huge, which is the opposite of what the interface-first gate does — and
# (b) classifying what was served, since the whole finding is "the chain is 1.0/session, the list
# is 3.0/session" and that collapses if the buckets blur.
import json
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/session'))
import session_reads


def transcript(tmp_path: Path, records: list) -> Path:
    project = tmp_path / 'proj'
    project.mkdir()
    (project / 'abc123.jsonl').write_text(
        '\n'.join(json.dumps(r) for r in records), encoding='utf-8', newline='\n')
    return project


def read_pair(uid: str, target: str, served: str, sidechain: bool = False) -> list:
    return [
        {'type': 'assistant', 'isSidechain': sidechain,
         'message': {'content': [{'type': 'tool_use', 'id': uid, 'name': 'Read',
                                  'input': {'file_path': target, 'offset': 1, 'limit': 5}}]}},
        {'type': 'user', 'isSidechain': sidechain,
         'message': {'content': [{'type': 'tool_result', 'tool_use_id': uid,
                                  'content': served}]}},
    ]


def _serve(monkeypatch, project: Path) -> None:
    monkeypatch.setattr(session_reads, 'paths_for',
                        lambda *_a, **_k: sorted(project.glob('*.jsonl')))


def test_a_read_is_sized_by_what_it_served(tmp_path, monkeypatch):
    _serve(monkeypatch, transcript(tmp_path, read_pair('a', '/w/big.py', 'x' * 120)))
    files, sessions = session_reads.file_reads('proj')
    assert files['/w/big.py']['chars'] == 120, 'the tool_result is the cost, not the arguments'
    assert files['/w/big.py']['count'] == 1
    assert sessions == {'abc123'}


def test_the_same_file_twice_is_a_re_read(tmp_path, monkeypatch):
    _serve(monkeypatch, transcript(
        tmp_path, read_pair('a', '/w/x.md', 'aa') + read_pair('b', '/w/x.md', 'bbb')))
    files, _ = session_reads.file_reads('proj')
    assert files['/w/x.md'] == {'count': 2, 'chars': 5, 'sessions': {'abc123'}}


def test_a_subagent_read_is_not_the_parent_sessions(tmp_path, monkeypatch):
    """Workers bill in their own transcripts; counting them here would double the population."""
    _serve(monkeypatch, transcript(tmp_path, read_pair('a', '/w/x.md', 'aa', sidechain=True)))
    files, _ = session_reads.file_reads('proj')
    assert files == {}


def test_what_was_served_is_classified_by_the_gate_it_belongs_to():
    assert session_reads.kind_of('/w/core/CONTEXT.md') == 'CONTEXT.md chain'
    assert session_reads.kind_of('/w/core/hooks/file_law.pyi') == 'interface stub'
    assert session_reads.kind_of('/w/core/hooks/file_law.py') == 'source'
    assert session_reads.kind_of('/w/ROADMAP.md') == 'other UPPERCASE.md'
    assert session_reads.kind_of('/w/notes/thing.md') == 'prose'
