#!/usr/bin/env python3
# Does a list assign a vendor's model where it should assign a level? Zero-token, deterministic.
#
# Lucas, 2026-08-17, reading a step assignment: "nothing in WOS should be tied to a specific
# vendor/company/model." The sweep that followed moved 26 directives from `model: sonnet` /
# `model: opus` to `level: high|medium|low`; this is the guard that keeps them there, and it was the
# unbuilt half for three days — long enough for one directive to survive in a list nobody swept.
#
# THE CHECK READS POSITION, NOT PRESENCE, and that is the whole design. A bare model name is
# legitimate as DATA — a measured split in a cost report, a stale model id quoted in a bug, prose
# explaining what a provider's frontmatter resolves to — and illegitimate as a DIRECTIVE. A flat
# token ban would fire on every honest use and be switched off within a week. So what is forbidden
# is the assignment SHAPE the lists use for level: `**model: …**`, the bolded directive that sits
# beside `→ **level: medium**`. Backticked prose about a model name passes, because it is not
# telling anyone which model to run.
import re

# `→ **model: opus** for the contract` — the bolded assignment. `\*\*model:` is the entire
# discriminator: the directive is bold, the data never is.
DIRECTIVE = re.compile(r'\*\*model:\s*([^*]+)\*\*')

# Which files are lists, by NAME rather than by path, so a ROADMAP-<name>.md in any repo under
# the workspace is covered without enumeration. Same rule as checks/citation-gate.py.
LIST_NAME = re.compile(r'^ROADMAP(-[a-z0-9-]+)?\.md$')


def is_list(path) -> bool:
    return bool(LIST_NAME.match(path.name))


def vendor_directive_hits(files: list, exempt: set) -> list:
    """List lines telling a reader which MODEL to run, instead of which level."""
    hits = []
    for path in files:
        if not is_list(path) or path.resolve() in exempt:
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if match := DIRECTIVE.search(line):
                hits.append(
                    f'{path}: names a model where it should name a level (line {number}).\n'
                    f'   `model: {match.group(1).strip()}` → `level: low|medium|high`. Which KIND\n'
                    f'   of work earns which level is core/levels.txt; which model FILLS a level is\n'
                    f'   data — core/tools/wos/levels per harness, core/flows/craft/routing.md per\n'
                    f'   provider.')
    return hits
