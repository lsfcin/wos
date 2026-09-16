# Frontmatter validation for every layer of the agent library — skills, flows, the flow
# composition DAG, and agents. The law is core/SCHEMA.md and core/SCHEMA-layers.md; this only
# enforces it. A LIBRARY, not an entrypoint — core/tools/wos/sync-skills owns the CLI.
#
# Every function takes its root as an ARGUMENT and returns what it found. The bash read $WORKSPACE
# from whoever sourced it and printed as it went, so testing one rule meant spawning a
# `bash -c 'WORKSPACE=…; source …; validate_x'` against a throwaway tree.
from __future__ import annotations

import re
from pathlib import Path

from mirror import is_skill

FLOW_TYPES = ('research-brief', 'utility', 'domain')
CONFIRMS = ('plan', 'none')
LEVELS = ('low', 'medium', 'high', 'max')


def _lines(path: Path) -> list:
    """The file as lines, with the CR of a CRLF clone dropped. NOT COSMETIC: the bash asked
    `[[ "$(head -1 "$f")" != "---" ]]`, and MSYS strips a trailing CR inside command substitution
    while GNU bash does not — so a CRLF source passes here and reads as having no frontmatter at
    all on Linux. Removing the per-OS axis is the point of the port.
    """
    return path.read_text(encoding='utf-8', errors='replace').replace('\r\n', '\n').split('\n')


def frontmatter(path: Path) -> list | None:
    """The leading YAML block's lines, or None when the file does not open with one."""
    lines = _lines(path)
    if not lines or lines[0].strip() != '---':
        return None
    block = []
    for line in lines[1:]:
        if line.strip() == '---':
            break
        block.append(line)
    return block


def _field(block: list, key: str) -> str:
    """Every match joined, so a duplicated key fails its enum rather than silently taking one."""
    return '\n'.join(m.group(1) for m in
                     (re.match(rf'^{key}:[ \t]*(\S+)', line) for line in block) if m)


def _missing(block: list, path: Path, layer: str, keys, empty=(), prefix='') -> list:
    """One message shape for every required field, across all three layers."""
    return [f'INVALID {layer} ({prefix}missing {key}:): {path}' for key in keys
            if not any(re.match(rf'^{key}:[ \t]*(\S|$)' if key in empty
                                else rf'^{key}:[ \t]*\S', line) for line in block)]


def _enum(block: list, path: Path, layer: str, key: str, allowed) -> list:
    value = _field(block, key)
    if value in allowed:
        return []
    return [f'INVALID {layer} ({key} must be {"|".join(allowed)}, got '
            f"'{value or '<missing>'}'): {path}"]


def validate_skills(src: Path) -> list:
    """YAML frontmatter with name + description — what keeps a non-skill doc (status note, ADR)
    from leaking into the mirrors."""
    problems = []
    for path in sorted(src.glob('*.md')):
        if not is_skill(path.stem):
            continue
        block = frontmatter(path)
        if block is None:
            problems.append(f'INVALID skill (no YAML frontmatter — not a skill): {path}')
            continue
        problems += _missing(block, path, 'skill', ('name', 'description'), empty=('description',))
    return problems


def _flow_files(workspace: Path) -> list:
    return sorted((workspace / 'core' / 'flows').rglob('*.md'))


def validate_flows(workspace: Path) -> list:
    """description, args, type ∈ enum, confirm ∈ enum (core/SCHEMA-layers.md § Layer: flow).

    Exempt: CONTEXT.md, and flows/craft/ — the engineering cluster declares level routing directly
    and has no `type` in the enum. A DOT-DIRECTORY under flows/ is a STORE, not a flow: nothing in
    it is invocable, and without the exemption core/flows/.craft-skills/ blocked every commit.
    """
    problems = []
    for path in _flow_files(workspace):
        parents = path.parts[:-1]
        if 'craft' in parents or any(p.startswith('.') for p in parents):
            continue
        if path.stem == 'CONTEXT':
            continue
        block = frontmatter(path)
        if block is None:
            problems.append(f'INVALID flow (no YAML frontmatter): {path}')
            continue
        problems += _missing(block, path, 'flow', ('description', 'args'))
        problems += _enum(block, path, 'flow', 'type', FLOW_TYPES)
        problems += _enum(block, path, 'flow', 'confirm', CONFIRMS)
    return problems


DECLARES_LOOP = re.compile(
    r'^#+[ \t].*execution loops|iteration cap|^[*# ]*Loop [0-9]|\biterations?\b|\brepeat until\b',
    re.IGNORECASE)
HAS_CAP = re.compile(
    r'(iteration cap|round cap|at most|maximum([ \t]+of)?|max[A-Za-z]*)[^.\n]{0,40}[0-9]',
    re.IGNORECASE)


def validate_flow_loops(workspace: Path) -> list:
    """A step that declares a loop must declare its numeric cap (core/flows/CONTEXT.md; why the
    bound rather than the step is core/flows/craft/SPECS.md).

    Whole-file, because a cap stated once governs the flow. CONTEXT.md and SPECS.md STATE the rule
    so are not judged by it. The unit is the FLOW: a cut `<flow>-<name>.md` is still one flow
    with one cap, so a part is checked against its whole family.
    """
    problems = []
    for path in _flow_files(workspace):
        if path.name in ('CONTEXT.md', 'SPECS.md'):
            continue
        if not any(DECLARES_LOOP.search(line) for line in _lines(path)):
            continue
        family = [line for sibling in sorted(path.parent.glob(f'{path.stem.split("-")[0]}*.md'))
                  for line in _lines(sibling)]
        if any(HAS_CAP.search(line) for line in family):
            continue
        problems.append('INVALID flow (declares a loop with no numeric cap — an unbounded loop '
                        f'is a hang, see core/flows/CONTEXT.md): {path}')
    return problems


def validate_flow_dag(workspace: Path) -> list:
    """The `uses:` graph must be a DAG (core/SCHEMA-layers.md § Composition and cycles) — a
    definitional cycle never bottoms out. Definition-time only; execution loops are bounded above.
    """
    problems, uses, known = [], {}, set()
    for path in _flow_files(workspace):
        if path.stem in ('CONTEXT', 'TREE'):
            continue
        known.add(path.stem)
        block = frontmatter(path)
        if block is None:
            continue
        declared = [m.group(1) for m in
                    (re.match(r'^uses:[ \t]*(.*)$', line) for line in block) if m]
        uses[path.stem] = [u for line in declared for u in line.replace(',', ' ').split()]

    for name, targets in uses.items():
        problems += [f"INVALID flow ({name} uses unknown flow '{t}'): core/flows/**/{name}.md"
                     for t in targets if t not in known]

    # Iterative DFS, three-colour: 0 unvisited, 1 on the path, 2 done. sorted() is not tidiness:
    # bash walked `${!USES[@]}`, a HASH order, so which member of a cycle got named was unspecified.
    colour: dict = {}
    for start in sorted(uses):
        if colour.get(start, 0) != 0:
            continue
        stack = [start]
        while stack:
            node = stack[-1]
            if colour.get(node, 0) != 0:
                colour[node] = 2
                stack.pop()
                continue
            colour[node] = 1
            for target in (t for t in uses.get(node, []) if t in known):
                if colour.get(target, 0) == 1:
                    problems.append(
                        f"INVALID flow (uses: cycle — '{node}' uses '{target}', which leads back "
                        f"to '{node}'): the uses: graph must be a DAG, see core/SCHEMA.md")
                elif colour.get(target, 0) == 0:
                    stack.append(target)
    return problems


def validate_agents(workspace: Path) -> list:
    """name, description, level ∈ enum; workers also need tools + output. `lead` is the one
    orchestrator (level-only). _template excluded like skills."""
    problems = []
    for path in sorted((workspace / 'core' / 'agents').glob('*.md')):
        if path.stem in ('CONTEXT', '_template'):
            continue
        block = frontmatter(path)
        if block is None:
            problems.append(f'INVALID agent (no YAML frontmatter): {path}')
            continue
        problems += _missing(block, path, 'agent', ('name', 'description'))
        problems += _enum(block, path, 'agent', 'level', LEVELS)
        if any(re.match(r'^(model|thinking):', line) for line in block):
            problems.append('INVALID agent (model:/thinking: forbidden in core source — use '
                            f'level:): {path}')
        if path.stem != 'lead':
            problems += _missing(block, path, 'agent', ('tools', 'output'), prefix='worker ')
    return problems
