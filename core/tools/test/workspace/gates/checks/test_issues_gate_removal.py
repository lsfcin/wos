# Regression — the issues gate reads removals, not only FIXED flips.
#
# A session deleted four fixed bug sections and one OPEN one from the workspace ISSUES.md; the
# gate only fired on the literal word FIXED, so an open bug (B4) left the list without a fix or
# a spec. Since 2026-08-31 a section may not leave ISSUES.md — by deletion or by a FIXED flip —
# without a matching regression spec, and a spec for B19 does not pay B1's debt: the id ends at
# the name boundary.
from issues_gate_harness import edit_issue, repo_with, spec_file

SECTION = '## B7 — a bug\n\n**Symptom:** x.\n'
B1_SECTION = '## B1 — another bug\n\n**Symptom:** y.\n'


def test_deleting_an_open_bug_without_a_spec_blocks(tmp_path):
    issues = repo_with(tmp_path, SECTION)
    out = edit_issue(tmp_path, issues, old=SECTION, new='')
    assert out.returncode == 2, out.stdout + out.stderr
    assert 'b7' in out.stderr


def test_deleting_with_a_spec_passes(tmp_path):
    issues = repo_with(tmp_path, SECTION)
    spec_file(tmp_path, 'b7-the-bug-is-gone.py')
    out = edit_issue(tmp_path, issues, old=SECTION, new='')
    assert out.returncode == 0, out.stderr


def test_a_b19_spec_does_not_pay_b1s_debt(tmp_path):
    issues = repo_with(tmp_path, B1_SECTION)
    spec_file(tmp_path, 'b19-some-other-bug.py')
    out = edit_issue(tmp_path, issues, old=B1_SECTION, new='')
    assert out.returncode == 2, out.stdout + out.stderr
    assert 'b1' in out.stderr


def test_a_fixed_flip_with_a_spec_passes(tmp_path):
    # fixed_ids used to return whole heading lines (FIXED_RE had no capture group), and a whole
    # heading can never match a spec filename -- every flip blocked forever, spec or no spec.
    # Found 2026-09-04 by the first real flip (B5).
    issues = repo_with(tmp_path, SECTION)
    spec_file(tmp_path, 'b7-the-bug-is-gone.py')
    out = edit_issue(tmp_path, issues, old=SECTION,
                     new='## b7-the-bug-is-gone — FIXED\n\nThe measurement lives elsewhere.\n')
    assert out.returncode == 0, out.stderr
