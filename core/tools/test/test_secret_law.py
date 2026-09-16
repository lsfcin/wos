# T1 secret law: every shape of credential is found, and the near-misses that would make anyone
# switch the gate off are not. Zero-token, no network.
#
# THE NEGATIVE CASES ARE THE POINT. A scanner that flags every long random string finds every
# credential and also every git SHA, every base64 blob and every hash in the tree — and the first
# person to hit that adds an exception, then a second, then stops running it. So each positive
# case below is paired with the thing it must NOT catch.
from __future__ import annotations
import pathlib
import pytest
import secret_law
from conftest import TOOLS


def scan(text: str) -> list[str]:
    return [f.kind for f in secret_law.scan_text(text, pathlib.Path('sample.md'))]


# Synthetic throughout, and deliberately so: a test that pins a real leak keeps the leak alive,
# because fixing it would turn the test red.
@pytest.mark.parametrize('kind, sample', [
    ('CPF', 'o CPF é 047.529.214-64'),
    ('CNPJ', 'CNPJ 12.345.678/0001-95'),
    ('GitHub token', 'remote ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5'),
    ('Overleaf token', 'https://git:olp_A1b2C3d4E5f6G7h8I9j0K1l2@git.overleaf.com/abc'),
    ('Google API key', 'key=AIzaSyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6q'),
    ('OpenAI key', 'sk-A1b2C3d4E5f6G7h8I9j0K1l2M3n4'),
    ('Slack token', 'xoxb-1234567890-abcdefghij'),
    ('private key', '-----BEGIN OPENSSH PRIVATE KEY-----'),
    ('credential in a URL', 'https://user:hunter2hunter2@example.com/repo.git'),
    ('assigned secret', 'api_key = "A1b2C3d4E5f6G7h8I9j0"'),
])
def test_every_declared_shape_is_found(kind, sample):
    assert kind in scan(sample)


@pytest.mark.parametrize('innocent', [
    # A git SHA is forty hex chars and appears in nearly every document here.
    'fixed in 4ba92a77e21a0ac1c495c9af5ac856ca9dd7accf',
    # So does a base64-ish blob, and neither is assigned to a secret-sounding name.
    'hash: aGVsbG8gd29ybGQgdGhpcyBpcyBub3QgYSBzZWNyZXQ=',
    # The catch-all needs a LONG value, or every boolean setting becomes a credential.
    'token: yes',
    'password = ""',
    # A bare eleven-digit run with nothing around it saying CPF is a phone number.
    'ligue para 81999887766 se precisar',
])
def test_the_near_misses_are_left_alone(innocent):
    assert scan(innocent) == []


def test_a_bare_cpf_is_found_only_where_the_context_says_so():
    """Same window the redactor uses, and for the same reason: in a chat the number arrives a turn
    after the request. A line-local test misses the real case, and a context-free one calls every
    phone number a CPF."""
    assert 'CPF' in scan('Me informa o seu CPF\no meu é 04752921464')
    assert scan('meu telefone\no meu é 04752921464') == []


def test_the_file_name_alone_is_a_finding(tmp_path):
    """A tree that carries a segredos.env has said in the workspace's own vocabulary that the
    contents must not be published, so no pattern has to match inside it."""
    secret = tmp_path / secret_law.SECRET_FILE
    secret.write_text('NOTHING_SECRET_LOOKING=1\n', encoding='utf-8', newline='\n')
    assert [f.kind for f in secret_law.scan(secret)] == [f'named {secret_law.SECRET_FILE}']


def test_a_file_that_is_not_text_carries_no_finding(tmp_path):
    """A binary is refused by the crossing rule, not by this one. Guessing at bytes here would
    produce findings nobody can act on."""
    blob = tmp_path / 'logo.png'
    blob.write_bytes(b'\x89PNG\r\n\x1a\n\xff\xfe\xfd')
    assert secret_law.scan(blob) == []


def test_a_finding_never_quotes_the_value():
    """A report that prints the secret copies it into wherever the report lands — a terminal
    scrollback, a CI log, a pasted message. It names the kind and the line instead."""
    finding = secret_law.scan_text('ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5',
                                   pathlib.Path('sample.md'))[0]
    assert 'ghp_' not in str(finding)
    assert 'sample.md:1' in str(finding)


def test_the_enforcement_layer_is_clean_today():
    """The case that will actually catch a regression: the day a credential lands in core/tools,
    this goes red before anything can publish it."""
    # The two tests OF the redaction carry its shapes as fixtures, and cannot not. They are named
    # here one by one, never matched by a pattern: a pattern-shaped exemption would silently cover
    # the third file that grows a credential, which is the file this test exists to catch.
    fixtures = {(TOOLS / 'test/test_secret_law.py').resolve(),
                (TOOLS / 'test/chat/test_chat_stitch.py').resolve()}
    files = [p for p in TOOLS.rglob('*')
             if p.is_file() and p.suffix in ('.py', '.txt', '.md')
             and '.venv' not in p.parts and p.resolve() not in fixtures]
    assert secret_law.scan_all(files) == []
