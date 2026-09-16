#!/usr/bin/env python3
# Pre-Write hook: list existing facade exports before creating a new file in the same module.
#
# core/hooks/SPECS.md classes this hook "Informs", and for as long as it existed it informed
# nobody: it printed to stdout on exit 0, which Claude Code shows in transcript mode only.
# `hookSpecificOutput.additionalContext` is the one non-blocking channel that reaches the
# model — `systemMessage` addresses Lucas, and exit-0 stdout addresses no one. Ported
# 2026-08-16, following heredoc-gate.py, where the channel was verified end to end.
#
# The class of bug this belonged to: a gate that looks installed and is not doing its job.
# It never errored, so nothing ever said so — which is why "what does this produce, and does
# it arrive?" beats reading the code for a raised exception.
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from hook_input import capability, parse_stdin
from platform_law import WORKSPACE_ROOT  # noqa: E402

FACADE_FOR = {
    '.ts': 'index.ts', '.tsx': 'index.tsx',
    '.js': 'index.js', '.jsx': 'index.jsx',
    '.py': '__init__.py',
    '.dart': 'index.dart',
}

# The advisory third of facade-discipline: it names the exports a new sibling should reach for,
# where facade-gate.py forces the read and check-facade-imports.py blocks the bypass. All three
# answer to one switch, so turning the feature off leaves none of them talking.
if not feature_law.is_enabled('facade-discipline'):
    sys.exit(0)

_, tool, data, _, _ = parse_stdin()
# By capability, never by name. An Edit is a write too, and is filtered a line below by the
# file already existing — this hook is about a file being CREATED beside a facade.
if capability(tool, data) != 'write':
    sys.exit(0)

file_path = Path(data.get('file_path', ''))

# Only new files under code/
if file_path.exists() or 'code' not in file_path.parts:
    sys.exit(0)

facade_name = FACADE_FOR.get(file_path.suffix)
if not facade_name:
    sys.exit(0)

facade = file_path.parent / facade_name
# Skip if facade doesn't exist or we're writing the facade itself
if not facade.exists() or facade.resolve() == file_path.resolve():
    sys.exit(0)

content = facade.read_text(encoding='utf-8', errors='ignore')
exports = []

if file_path.suffix == '.py':
    m = re.search(r'__all__\s*=\s*\[([^\]]+)\]', content, re.DOTALL)
    if m:
        exports = re.findall(r'["\'](\w+)["\']', m.group(1))
    else:
        for line in content.splitlines():
            m2 = re.match(r'^from\s+\S+\s+import\s+(.+)', line)
            if m2:
                exports += [x.strip().split(' as ')[-1].strip() for x in m2.group(1).split(',')]
else:
    for block in re.findall(r'export\s+\{([^}]+)\}', content, re.DOTALL):
        for item in block.split(','):
            name = item.strip().split(' as ')[-1].strip().rstrip(';').strip()
            if name and re.match(r'^\w+$', name):
                exports.append(name)
    named = re.findall(
        r'export\s+(?:default\s+)?(?:type\s+)?(?:const|function|class|interface|enum)\s+(\w+)',
        content,
    )
    exports += named

exports = sorted(set(e for e in exports if e and re.match(r'^\w+$', e)))

try:
    rel = facade.relative_to(WORKSPACE_ROOT)
except ValueError:
    rel = facade

if exports:
    message = (f"📦 {rel} exports: {', '.join(exports)}. "
               f"Verify the new file adds functionality not already covered above.")
else:
    message = (f"📦 {rel} exists but exports nothing yet — "
               f"ensure the new file gets re-exported there.")

print(json.dumps({'hookSpecificOutput': {
    'hookEventName': 'PreToolUse',
    'additionalContext': message,
}}))

sys.exit(0)
