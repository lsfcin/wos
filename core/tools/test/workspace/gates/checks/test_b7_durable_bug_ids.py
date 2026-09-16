# B7 regression — a bug id is a durable id, and never borrowed.
#
# Ids here used to be positional; completion deleted them and every close renumbered, so a
# citation of "B6" resolved to a bug that no longer was the one meant (the ZCode trust gate
# citation was the sighting). Since 2026-08-31 new ids are ids, `b<YYYYMMDD>-<name>`; a numeric
# id dies with its fix. The gate matches ids to specs across the hyphen/underscore boundary — a id
# id and its test_b<...> file name are the same string in two notations — and an id ends at a
# non-alphanumeric boundary, so b1 never borrows b19's proof.
from issues_gate_harness import edit_issue, repo_with, spec_file

ID = 'b20260831-google-skills-split'
SECTION = f'## {ID} — a bug\n\n**Symptom:** x.\n'


def test_a_id_id_is_a_valid_id(tmp_path):
    issues = repo_with(tmp_path, SECTION)
    out = edit_issue(tmp_path, issues, old=SECTION, new='')
    assert out.returncode == 2, out.stdout + out.stderr
    assert ID in out.stderr, 'the message must name the id, not an eaten version of it'


def test_a_id_spec_satisfies_its_id_across_the_notation_boundary(tmp_path):
    issues = repo_with(tmp_path, SECTION)
    spec_file(tmp_path, f'test_{ID.replace("-", "_")}.py')
    out = edit_issue(tmp_path, issues, old=SECTION, new='')
    assert out.returncode == 0, out.stderr


def test_a_numeric_spec_does_not_pay_a_ids_debt(tmp_path):
    issues = repo_with(tmp_path, SECTION)
    spec_file(tmp_path, 'test_b20260831_google.py')
    out = edit_issue(tmp_path, issues, old=SECTION, new='')
    assert out.returncode == 2, out.stderr
