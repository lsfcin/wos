# session_commands.py — what the agent actually RAN in bash, by shape rather than by tool.
#
# The fifth question beside price (`usage`), what filled the window (`context`), what was read
# (`reads`) and what a session DID (`trace`). Lucas asked it on 2026-09-15: 7,507 bash calls are on
# disk and nobody had ever looked at their FORM, so nobody could say whether something more atomic
# than rtk was available. `loudest` ranks what a tool returned; this ranks what we keep typing.
#
# NOTHING HERE IS NEW CAPTURE. Every command is already in the transcript as the `tool_use` input.
# The three regexes that decide what a command names live in session_trace.py and are imported, not
# restated — a second copy of that rule is the drift the law modules exist to catch.
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_log import _result_chars, blocks
from session_trace import OURS, RUNNERS, SEGMENT
from session_turns import paths_for

# A second word is a SUBCOMMAND only when it is a bare word — no slash, no dot, no leading dash.
# `git status` and `npm run` are two tools; `ls -la core/` and `sed -n 1,200p file` are one tool
# each, and folding their arguments into the name gives every invocation a row of its own. Declared
# as a shape rule rather than a list of verbs, so a command nobody thought of still lands somewhere.
SUBCOMMAND = re.compile(r'^[a-z][\w-]*$')

# A heredoc body and a quoted string are DATA the command carries, never commands themselves, and
# both routinely span newlines — which SEGMENT splits on. Left in, the first run of this report
# filed `import sys`, `from pathlib`, `Co-Authored-By:` and a bare `"` among its busiest shapes and
# counted 12,899 distinct ones, nearly all of them lines out of a python script or a commit message.
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1\n.*?^\2$", re.DOTALL | re.MULTILINE)
QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"", re.DOTALL)


def _strip_data(command: str) -> str:
	"""The command with everything it CARRIES removed, so only what it RUNS is left."""
	return QUOTED.sub('ARG', HEREDOC.sub('<<ARG', command))


def shape(command: str) -> list:
	"""The SHAPES one Bash call is made of — what was run, with every argument dropped.

	A pipeline is as many shapes as it has stages: `git log | head` is one call that ran two
	programs, and counting it as `git log` alone hides every `head` we pay for. Our own tools keep
	their whole path, because `core/run tools/wos/size` is already one atom and `core` is not a name.

	Nothing is inferred beyond the two rules above. The point of the report is to find a shape that
	repeats often enough to deserve a command of its own, and a normaliser that guessed would be
	inventing the very repetition it claims to have found.
	"""
	found = []
	for segment in SEGMENT.split(_strip_data(command)):
		bare = RUNNERS.sub('', segment.strip())
		if ours := OURS.match(bare):
			found.append(f'core/tools/{ours.group(1).split("::")[0].rstrip("/")}')
			continue
		words = bare.split()
		if not words:
			continue
		head = words[0].rsplit('/', 1)[-1]
		if len(words) > 1 and SUBCOMMAND.match(words[1]):
			head = f'{head} {words[1]}'
		found.append(head)
	return found


def commands(project: str, session: str = '') -> tuple:
	"""([(shape, stages, chars)], calls) — every bash call a session made, grouped by shape.

	TWO COUNTS, because a call and a stage are not the same thing. `stages` counts every program
	run, so a pipeline contributes once per stage; `chars` is credited ONLY to a call's LAST stage,
	the one whose output actually reached the context. Crediting every stage would report one result
	as many, and crediting the first would credit `git log` for what `head` printed.

	`calls` is returned beside the rows so a reader can reconcile: it must equal the Bash call count
	`trace` already prints, and a mismatch means the walk lost records rather than that the tree
	changed.
	"""
	stages: dict = defaultdict(int)
	chars: dict = defaultdict(int)
	calls = 0
	for path in paths_for(project, session):
		last: dict = {}
		for line in path.open(errors='replace', encoding='utf-8'):
			try:
				event = json.loads(line)
			except json.JSONDecodeError:
				continue
			if event.get('isSidechain'):
				continue
			for block in blocks(event.get('message') or {}):
				if block.get('type') == 'tool_use' and block.get('name') == 'Bash':
					calls += 1
					found = shape(str((block.get('input') or {}).get('command', '')))
					for name in found:
						stages[name] += 1
					if found:
						last[block.get('id')] = found[-1]
				elif block.get('type') == 'tool_result' and block.get('tool_use_id') in last:
					chars[last[block['tool_use_id']]] += _result_chars(block)
	rows = sorted(((s, n, chars[s]) for s, n in stages.items()), key=lambda row: -row[1])
	return rows, calls
