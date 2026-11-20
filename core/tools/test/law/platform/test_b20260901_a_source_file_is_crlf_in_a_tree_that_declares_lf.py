# b20260901 regression — a file the tree declares LF is LF, in the index AND on this disk.
#
# `.gitattributes` says `* text=auto eol=lf`, and its own head says LF is not "the Linux ending"
# here but the workspace's. Nothing checked it. test_encoding_ceiling.py comes closest and reads
# CALL SITES via AST — every open() naming `newline=` — which cannot see a file that is already
# wrong, so the rule had a policy, a rationale, and no instrument.
#
# WHY THE WORKING TREE IS HALF THE CHECK, and the half that is hard to want. Git normalises on
# read, so a CRLF working file whose blob is LF leaves `git status` CLEAN: the difference is
# invisible to every command an operator runs. That is exactly how core/skills/install.md came to
# be CRLF on the Windows clone and LF here — one skill spelled differently from the other sixteen,
# on one machine, found only because a port's equivalence diff compared bytes. Checking `i/` alone
# would pass on that machine and prove nothing.
#
# CONSEQUENCE, SAID OUT LOUD: this is green on this clone and will be RED on any clone whose
# working tree carries CRLF, until that tree is renormalised (`git add --renormalize .` and a fresh
# checkout). That is the check doing its job on the machine that has the defect, not a regression.
#
# WHAT IT FOUND on 2026-09-05: 18 tracked files, none of them the one the bug names. Fifteen were
# the unzipped members of a .docx under academy/administration/pda/template_extracted/ — `*.docx
# binary` covers the archive and says nothing about its contents once extracted — now declared
# `-text` and skipped here. Three were Google Forms CSV exports whose record separators were CRLF
# while their in-field newlines were already LF; those were renormalised, and their row and column
# counts are asserted below because a line-ending pass over a CSV is a data change if it is wrong.
import subprocess

import pytest
from conftest import WORKSPACE_ROOT, needs

RESPONSES = WORKSPACE_ROOT / 'academy/teaching/classes/techedu/respostas'
# What each export held before the renormalisation, counted with the csv module. A pass that
# rewrote a quoted field's newline would change these, and nothing else in the suite would notice.
EXPORTS = {'avaliacao-do-pitch.csv': (5, 58),
           'avaliacao-por-pares-intergrupo.csv': (28, 27),
           'avalie-o-seu-grupo-intragrupo.csv': (377, 70)}

# `i/none` is a file with no line ending at all; `i/-text` is content git reads as binary. Neither
# is a CRLF file, and neither is something an authoring rule about line endings has an opinion on.
FINE = ('lf', 'none', '-text')

# The worktree arm has a fourth answer the index arm does not: `w/` comes back EMPTY when there is
# no file on this disk at all — a staged delete, or a sparse checkout. Reading blank as "not LF"
# made this check name three DELETED files as CRLF on 2026-09-20, and the failure text then told an
# operator to renormalise paths that were not there. A check that reports a cause the tree cannot
# hold is worse than one that stays silent. Absence belongs to the index arm, which sees it as a
# deletion; this arm only ever asks what the bytes on disk end with.
ON_DISK = FINE + ('',)


def eol_rows() -> list:
    """(index ending, worktree ending, attributes, path) for every tracked file."""
    done = subprocess.run(['git', 'ls-files', '--eol'], cwd=WORKSPACE_ROOT,
                          capture_output=True, text=True, encoding='utf-8')
    rows = []
    for line in done.stdout.splitlines():
        marks, _, path = line.partition('\t')
        fields = marks.split()
        if len(fields) < 3:
            continue
        index, work = fields[0].removeprefix('i/'), fields[1].removeprefix('w/')
        rows.append((index, work, ' '.join(fields[2:]), path.strip()))
    return rows


def declared_lf() -> list:
    """Only the files the tree actually claims are LF text — never the ones it exempts."""
    return [row for row in eol_rows() if 'eol=lf' in row[2] and '-text' not in row[2]]


def wrong_endings(rows: list, arm: int, fine: tuple) -> list:
    """Paths whose ending in `arm` (0 the index, 1 this disk) is neither LF nor an exemption."""
    return sorted(row[3] for row in rows if row[arm] not in fine)


def test_the_tree_declares_lf_for_something() -> None:
    """The guard's floor. A parser that read no attributes would pass every file in the repo."""
    assert len(declared_lf()) > 100, 'read no eol=lf declarations — the parser, not the tree'


def test_a_path_with_no_file_on_this_disk_is_not_reported_as_crlf() -> None:
    """b20260920 regression — a staged delete leaves `w/` empty, and blank is not a line ending."""
    rows = [('lf', '', 'text=auto eol=lf', 'deleted.md'),
            ('lf', 'crlf', 'text=auto eol=lf', 'really-crlf.md')]
    assert wrong_endings(rows, 1, ON_DISK) == ['really-crlf.md']


def test_no_declared_text_file_is_crlf_in_the_index() -> None:
    """The half git will tell you about, once something asks."""
    wrong = wrong_endings(declared_lf(), 0, FINE)
    assert not wrong, (
        f'{len(wrong)} tracked blob(s) are not LF: {wrong[:10]}. `.gitattributes` declares '
        '`* text=auto eol=lf`. Fix with `git add --renormalize <path>`, or declare the path '
        '`-text` if it is extracted or vendored payload rather than something we author.')


def test_no_declared_text_file_is_crlf_in_this_working_tree() -> None:
    """The half nothing reports. Normalisation on read keeps `git status` clean over exactly this,
    which is why install.md sat CRLF on one clone for days with every check green."""
    wrong = wrong_endings(declared_lf(), 1, ON_DISK)
    assert not wrong, (
        f'{len(wrong)} file(s) are not LF on this disk though their blob is: {wrong[:10]}. '
        '`git status` cannot see this. Fix with `git add --renormalize .`, then delete and '
        '`git checkout` the paths so the working tree is rewritten from the normalised blob.')


@pytest.mark.parametrize('name, shape', sorted(EXPORTS.items()))
def test_a_renormalised_export_still_parses_to_the_same_table(name, shape) -> None:
    """Line endings are data in a CSV whose free-text answers contain newlines of their own."""
    needs('academy/teaching')
    import csv
    import io
    raw = (RESPONSES / name).read_bytes()
    assert b'\r' not in raw, f'{name} still carries a carriage return'
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8'))))
    assert (len(rows), len(rows[0])) == shape, f'{name} changed shape under renormalisation'
