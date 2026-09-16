#!/usr/bin/env python3
# Pre-commit duplication gate — jscpd over the repo; blocks when a clone involves a staged
# file. No baseline: touching a file with a legacy clone means extracting it now (ROADMAP-verify.md W2).
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_law import rel as _rel  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402

MIN_TOKENS = '75'
MIN_LINES = '10'
FORMATS = 'typescript,tsx,javascript,jsx,python,dart'
IGNORE = ','.join([
	'**/node_modules/**', '**/dist/**', '**/.git/**', '**/.codegraph/**',
	'**/*.d.ts', '**/*.pyi', '**/*.min.js', '**/goldens/**', '**/__pycache__/**',
])


def main() -> int:
	if not feature_law.is_enabled('duplication-gate'):
		return 0  # switched off: a disabled gate does not block, and does not pretend it ran
	staged = {line.strip() for line in sys.stdin if line.strip()}
	if not staged:
		return 0
	repo_root = Path(subprocess.check_output(
		['git', 'rev-parse', '--show-toplevel'], text=True, encoding='utf-8').strip())
	out_dir = Path(tempfile.mkdtemp(prefix='jscpd-'))
	try:
		result = subprocess.run(
			['npx', '--yes', 'jscpd', str(repo_root),
			 '--min-tokens', MIN_TOKENS, '--min-lines', MIN_LINES,
			 '--format', FORMATS, '--ignore', IGNORE,
			 '--reporters', 'json', '--output', str(out_dir), '--silent'],
			capture_output=True, text=True, timeout=120, encoding='utf-8')
		report_file = out_dir / 'jscpd-report.json'
		if not report_file.exists():
			print(f'⚠  jscpd produced no report — duplication check skipped.\n{result.stderr[-300:]}')
			return 0
		report = json.loads(report_file.read_text(encoding='utf-8'))
	except FileNotFoundError:
		print('⚠  npx/jscpd not available — duplication check skipped.')
		return 0
	except subprocess.TimeoutExpired:
		print('⚠  jscpd timed out — duplication check skipped.')
		return 0
	finally:
		shutil.rmtree(out_dir, ignore_errors=True)

	def rel(name: str) -> str:
		p = Path(name)
		try:
			return _rel(p.resolve(), repo_root)
		except ValueError:
			return name

	offenders = []
	for dup in report.get('duplicates', []):
		first, second = rel(dup['firstFile']['name']), rel(dup['secondFile']['name'])
		if first in staged or second in staged:
			offenders.append((first, dup['firstFile']['start'], second,
			                  dup['secondFile']['start'], dup.get('lines', '?')))
	if not offenders:
		return 0

	print('⛔ DUPLICATION GATE — staged files contain duplicated blocks:')
	for f1, l1, f2, l2, lines in offenders:
		print(f'   {f1}:{l1} ↔ {f2}:{l2}  ({lines} lines)')
	print('   Extract the shared logic into one module and import it from both sites.')
	print('   Override (emergencies only): git commit --no-verify')
	return 1


sys.exit(main())
