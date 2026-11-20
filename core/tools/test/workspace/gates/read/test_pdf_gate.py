# T0 the PDF read gate: a PDF is read through its twin, by Read and by a raw reader in the shell alike, and reading the twin is what unlocks the PDF. Zero-token, runs in verify-fast.
#
# The gate and the tracker that clears it are driven together, as this directory's head asks: the
# unlock is a mark the TRACKER writes when the twin is read, and a gate tested against a mark planted
# by hand would pass while the real pair never met (b20260901).
import json
import subprocess
import uuid

import pytest

import pdf_meta
import pdf_twin
from conftest import WORKSPACE_ROOT
from platform_law import interpreter, venv_script

GATE = WORKSPACE_ROOT / 'core/hooks/read/pdf-gate.py'
TRACKER = WORKSPACE_ROOT / 'core/hooks/read/context-tracker.py'


def _run(hook, tool_input: dict, session: str, tool='Read', **extra) -> subprocess.CompletedProcess:
	payload = {'tool_name': tool, 'tool_input': tool_input, 'session_id': session, 'cwd': str(WORKSPACE_ROOT), **extra}
	return subprocess.run([interpreter(), str(hook)], input=json.dumps(payload),
	                      capture_output=True, text=True, check=False, encoding='utf-8')


def _pdf(tmp_path, twin=True):
	"""The gate hashes bytes and never parses them, so a PDF here needs no body."""
	pdf = tmp_path / 'res.pdf'
	pdf.write_bytes(b'%PDF-1.4 res\n')
	if twin:
		pdf_meta.twin_of(pdf).parent.mkdir()
		pdf_meta.twin_of(pdf).write_text(pdf_meta.render_frontmatter({'sha256': pdf_meta.sha256(pdf)}) + 'body\n',
		                                 encoding='utf-8', newline='\n')
	return pdf


@pytest.fixture
def session():
	return f'test-pdf-{uuid.uuid4()}'


def test_a_fresh_twin_blocks_the_pdf_until_the_twin_is_read(tmp_path, session):
	pdf = _pdf(tmp_path)
	first = _run(GATE, {'file_path': str(pdf)}, session)
	assert first.returncode == 2 and 'PDF TWIN FIRST' in first.stderr and str(pdf_meta.twin_of(pdf)) in first.stderr
	_run(TRACKER, {'file_path': str(pdf_meta.twin_of(pdf))}, session)
	assert _run(GATE, {'file_path': str(pdf)}, session).returncode == 0, 'reading the twin must unlock the PDF'


ENGINE = venv_script('python', pdf_twin.ENGINE_VENV).exists()


@pytest.mark.skipif(not ENGINE, reason='no .venv-pdf here: a refusal would name a command that cannot run')
@pytest.mark.parametrize('state', ['absent', 'stale'])
def test_no_fresh_twin_is_refused_with_the_command_that_makes_it(tmp_path, session, state):
	pdf = _pdf(tmp_path, twin=state == 'stale')
	if state == 'stale':
		pdf.write_bytes(pdf.read_bytes() + b'% edited\n')
	result = _run(GATE, {'file_path': str(pdf)}, session)
	assert result.returncode == 2 and f'({state})' in result.stderr
	assert f'core/run tools/pdf/docling {pdf}' in result.stderr


@pytest.mark.parametrize('command', ['pdftotext {pdf} -', 'pdftoppm -png {pdf} /tmp/p',
                                     "python -c 'import fitz; fitz.open(\"{pdf}\")'",
                                     "python - <<'EOF'\nfrom pypdf import PdfReader\nPdfReader('{pdf}')\nEOF",
                                     'core/run tools/pdf/poppler text {pdf}', 'docling {pdf}'])
def test_a_raw_reader_in_the_shell_gets_the_same_verdict(tmp_path, session, command):
	pdf = _pdf(tmp_path)
	assert _run(GATE, {'command': command.format(pdf=pdf)}, session, tool='Bash').returncode == 2


@pytest.mark.parametrize('command', ['ls -la {pdf}', 'git add {pdf}', 'core/run tools/pdf/docling {pdf}',
                                     'core/run tools/pdf/pymupdf {pdf} --review',
                                     "git commit -F - <<'EOF'\nslides stop calling pdftotext {pdf}\nEOF"])
def test_a_command_that_only_names_a_pdf_passes(tmp_path, session, command):
	pdf = _pdf(tmp_path)
	assert _run(GATE, {'command': command.format(pdf=pdf)}, session, tool='Bash').returncode == 0


def test_a_subagent_is_gated_too_and_handed_only_the_twin(tmp_path, session):
	pdf = _pdf(tmp_path)
	result = _run(GATE, {'file_path': str(pdf)}, session, agent_id='worker-1')
	assert result.returncode == 2 and 'CONTEXT.md' not in result.stderr


@pytest.mark.skipif(ENGINE, reason='.venv-pdf is installed here, so the twin can be made')
def test_no_engine_lets_a_pdf_without_a_twin_through(tmp_path, session):
	assert _run(GATE, {'file_path': str(_pdf(tmp_path, twin=False))}, session).returncode == 0


def test_pdf_off_lets_a_pdf_without_a_twin_through(tmp_path, session, monkeypatch):
	"""features.txt: pdf-twin-reads needs pdf. Nothing can make the twin, so nothing is refused."""
	monkeypatch.setenv('WOS_FEATURES_OFF', 'pdf')
	assert _run(GATE, {'file_path': str(_pdf(tmp_path, twin=False))}, session).returncode == 0


def test_no_read_tracking_lets_a_fresh_twin_through(tmp_path, session, monkeypatch):
	"""features.txt: pdf-twin-reads needs subtree-read-tracking. Nothing marks the twin read, so the
	gate would block forever."""
	monkeypatch.setenv('WOS_FEATURES_OFF', 'subtree-read-tracking')
	assert _run(GATE, {'file_path': str(_pdf(tmp_path))}, session).returncode == 0
