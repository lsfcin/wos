#!/usr/bin/env python3
# The entropy report: what the dashboard's findings look like on the page.
#
# Split from entropy-dashboard.py 2026-07-30, when that file crossed the 150-line warn.
# A tool that reports size signals is a poor place to ignore one.
#
# Since 2026-08-20 it renders a delimited BLOCK rather than a whole file: the measurements live
# inside ISSUES.md, under hand-written issues, because both answer the same question — what is
# currently untrue that we know about (core/SCHEMA.md § The `.md` type system).
from datetime import date

from platform_law import rel

START = '<!-- entropy:start -->'
END = '<!-- entropy:end -->'

# Only used when ISSUES.md is missing entirely — a clone gets it from git. It carries the type's own
# head so the file is a legal ISSUES.md from its first line rather than from its first run.
SEED = ('# Workspace issues\n'
        '> What is currently untrue that we know about: hand-written issues first, every measured\n'
        '> number inside its own generated block.\n')


def local_seed(repo: str) -> str:
    """The same head, for a code repo's own list — created on the first scatter, then authored."""
    return (f'# {repo.split("/")[-1]} issues\n'
            '> What is currently untrue that we know about in this repo: hand-written issues\n'
            '> first, every measured number inside its own generated block.\n')


def _rel(path, root) -> str:
    return rel(path, root)


SECTIONS = (
    ('types', 'Off-allowlist `.md` types', 'route via core/SCHEMA.md § four disposal routes'),
    ('inventories', 'CONTEXT.md hand-written inventories', 'the routing block owns inventory'),
    ('naming', 'Naming and placement', 'kebab-case ASCII, types where their scope allows'),
    ('routing', 'Routing tables pointing at files git does not carry',
     'a clone gets the table and not the file — track the target, or stop routing to it'),
    ('goals', 'Projects not declaring their goal', 'line 3 of a code/ CONTEXT.md'),
    ('wiki', 'Wiki-links naming nothing', 'a [[name]] is a goal file or an item in one'),
    ('retired', 'Retired tokens still alive', 'a rename is unfinished until these are zero'),
    ('citations', 'Roadmap item numbers cited outside a roadmap',
     'a closed item is deleted — cite the SPECS.md/SCHEMA.md section that owns the rule'),
    ('duplicates', 'Items claimed by two lists', 'v1 criterion 2 — an item lives in one place'),
    ('size', 'Size signals', 'a signal for review, never a cap — do not summarize to fit'),
    ('stubs', 'Source files with no interface stub',
     'the read gate only fires when a stub exists — a missing one turns it off silently'),
    ('crowding', 'Directories holding too many files',
     'splitting costs one hop — pay it only when it removes more table than it adds'),
    ('finished', 'Prose describing finished work',
     'git is the history — cut it, or rewrite it as present-tense state'),
    ('undescribed', 'Unanswered scaffold placeholders',
     'a generator asked a question — answer it at the source, never by cutting the marker'),
    ('stores', 'Doubt stores missing their own discipline',
     'an experiment states its Method, Results, What changed and Limitations; a judged reference '
     'carries a source level'),
    ('vendor', 'Lists naming a model where they mean a level',
     'which kind of work earns a level is core/levels.txt; which model fills one is data — '
     'core/tools/wos/levels per harness, core/flows/craft/routing.md per provider'),
    ('fields', 'Header fields naming code that is not there',
     'a field naming our own tree is a claim, and it is checked before a later session inherits '
     'it as fact — core/SCHEMA.md § Every field that names our own code is verified'),
    ('truncated', 'Truncated routing descriptions',
     'the source wrote past the bound — shorten it there, never edit the table'),
    ('misplaced', 'Constraints trapped in a CONTEXT.md head',
     'the only enforced-read type — move the contract to a sibling SPECS.md'),
    ('branches', 'Local branches holding unpromoted work',
     'promote when the work is green, or say which reason applies — /roundup Phase 5'),
    ('unpushed', 'Work that exists on this disk and nowhere else',
     'two machines share this workspace — push it, or give the repo a remote to push to: '
     'code/SPECS-git.md § Push policy'),
    ('locals', 'Local branches already merged into their base',
     'safe to delete, and purely local — `git -C <repo> branch -d <branch>`'),
    ('remotes', 'Remote branches already merged into their base',
     'safe to delete, and outward-facing — `git -C <repo> push origin --delete <branch>`, Lucas'),
)


def render(findings: dict, scanned: int, root, name: str = '', trend: str = '') -> str:
    total = sum(len(findings[key]) for key, _, _ in SECTIONS)
    scope = f'`{name}`' if name else 'this repo'
    # THE HEADLINE IS THIS REPO'S COUNT, AND SINCE 2026-09-04 SO IS THE SCAN. A reader can act on
    # the number in front of them and on nothing else, so charging a nested project's findings here
    # made the figure grow with how many repos happened to be cloned (603 vs 33 on 2026-08-25).
    # Counting them at all was worse: those repos are IGNORED by this one's git, so the committed
    # block described a disk, and the clone without them read the same commit as red (b20260902).
    out = [START,
           '## Entropy',
           '',
           '> Generated by `core/hooks/entropy/dashboard/entropy-dashboard.py`, which scans '
           f'{scope} and no other. Never edit inside this block, and never copy a count out of it '
           '— a copied number is the drift these checks exist to catch.',
           '',
           f'{date.today().isoformat()} · {scanned} tracked files scanned · '
           f'**{total} findings here**{trend}', '',
           '| Check | Findings |', '|-------|----------|']
    out += [f'| {title} | {len(findings[key])} |' for key, title, _ in SECTIONS]
    out += ['', '*A check with no findings is the `0` in that table and nothing more. Only a check '
            'with something to show gets a section below.*']
    # A CLEAN CHECK GOT A SECTION UNTIL 2026-09-05, and it was the bulk of this file: 17 of the 23
    # sections said "Clean." under a heading and a restated note, ~102 lines repeating a table row
    # that already said 0. That is the shape core/hooks/SPECS.md forbids one layer up — a report
    # whose biggest part is not a problem teaches its reader to stop reading it — and it hid the
    # answer to "why is ISSUES.md 300 lines when five bugs are open?" behind a generated block.
    for key, title, note in SECTIONS:
        items = findings[key]
        if not items:
            continue
        out += ['', f'### {title}', '', f'*{note}*', '']
        out += [f'- {_rel(i.splitlines()[0], root)}' for i in sorted(items)]
    return '\n'.join(out + ['', END]) + '\n'
