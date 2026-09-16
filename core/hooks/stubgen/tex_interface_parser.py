#!/usr/bin/env python3
# tex_interface_parser.py: LaTeX source parser for tex-interface-gen.py.
# Extracts structure, equations, floats, citations, labels, and inputs.

from __future__ import annotations

import re
from pathlib import Path

# ─── Environment sets ─────────────────────────────────────────────────────────

EQ_ENVS = {
    'equation', 'equation*', 'align', 'align*', 'alignat', 'alignat*',
    'cases', 'multline', 'multline*', 'gather', 'gather*', 'eqnarray', 'eqnarray*',
    'subequations', 'flalign', 'flalign*',
}
FLOAT_ENVS = {'figure', 'figure*', 'table', 'table*', 'wrapfigure', 'wraptable'}
LISTING_ENVS = {'lstlisting', 'minted', 'verbatim', 'code', 'Verbatim'}

# ─── Helpers ──────────────────────────────────────────────────────────────────


def line_of(text: str, pos: int) -> int:
    return text[:pos].count('\n') + 1


def extract_braced(text: str, open_pos: int) -> str:
    depth, buf = 0, []
    for c in text[open_pos:]:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                break
        if depth > 0:
            buf.append(c)
    return ''.join(buf)


def extract_caption(body: str) -> str | None:
    m = re.search(r'\\caption\{', body)
    if not m:
        return None
    open_brace = body.find('{', m.start() + len('\\caption') - 1)
    return extract_braced(body, open_brace).strip() if open_brace != -1 else None


def first_prose_snippet(text: str, after_pos: int, until_pos: int, n: int = 10) -> str | None:
    for line in text[after_pos:until_pos].splitlines():
        s = line.strip()
        if s and not s.startswith('%') and not s.startswith('\\') and len(s) > 10:
            words = s.split()[:n]
            return ' '.join(words) + ('...' if len(s.split()) > n else '')
    return None


def find_paper_root(path: Path) -> Path | None:
    p = path if path.is_dir() else path.parent
    while True:
        if (p / 'main.tex').exists() or (p / '.latexmkrc').exists():
            return p
        parent = p.parent
        if parent == p:
            return None
        p = parent


def word_count(text: str) -> int:
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('%') or s.startswith('\\begin') or s.startswith('\\end'):
            continue
        count += len(s.split())
    return count


# ─── Parser ───────────────────────────────────────────────────────────────────


def parse_tex(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='ignore')
    result: dict = {
        'loc': len(text.splitlines()), 'words': word_count(text),
        'struct_points': [], 'openings': {}, 'content_items': [],
        'citations': set(), 'todos': [], 'inputs': [],
        'defined_labels': [], 'used_refs': [],
    }

    sec_re = re.compile(r'\\((?:sub){0,2}section)\*?\{([^}]+)\}')
    sec_positions: list[tuple[int, int, str]] = []
    for m in sec_re.finditer(text):
        level = {'section': 1, 'subsection': 2, 'subsubsection': 3}[m.group(1)]
        title = m.group(2).strip()
        lnum = line_of(text, m.start())
        result['struct_points'].append({'line': lnum, 'level': level, 'title': title})
        sec_positions.append((m.start(), level, title))

    for i, (pos, level, title) in enumerate(sec_positions):
        next_pos = sec_positions[i + 1][0] if i + 1 < len(sec_positions) else len(text)
        brace_end = text.find('}', pos)
        after = brace_end + 1 if brace_end != -1 else pos + 30
        snippet = first_prose_snippet(text, after, next_pos)
        if snippet:
            result['openings'][(level, title)] = snippet

    todo_re = re.compile(r'%\s*TODO[:\s]+(.+)', re.IGNORECASE)
    for i, line in enumerate(text.splitlines(), 1):
        m = todo_re.search(line)
        if m:
            result['todos'].append({'line': i, 'text': m.group(1).strip()})

    for m in re.finditer(r'\\cite\w*\{([^}]+)\}', text):
        for key in m.group(1).split(','):
            if k := key.strip():
                result['citations'].add(k)

    for m in re.finditer(r'\\(?:ref|eqref|pageref|autoref|cref)\{([^}]+)\}', text):
        result['used_refs'].append({'ref': m.group(1).strip(), 'line': line_of(text, m.start())})

    for m in re.finditer(r'\\input\{([^}]+)\}', text):
        result['inputs'].append({'path': m.group(1).strip(), 'line': line_of(text, m.start())})

    env_re = re.compile(r'\\begin\{(\w+\*?)\}(.*?)\\end\{\1\}', re.DOTALL)
    for m in env_re.finditer(text):
        env, body = m.group(1), m.group(2)
        env_line = line_of(text, m.start())
        label_m = re.search(r'\\label\{([^}]+)\}', body)
        label = label_m.group(1).strip() if label_m else None
        caption = extract_caption(body)
        if env in EQ_ENVS:
            content = re.sub(r'\\label\{[^}]+\}', '', body).strip()
            result['content_items'].append({'line': env_line, 'kind': 'equation',
                                            'data': {'env': env, 'label': label, 'content': content}})
            if label:
                result['defined_labels'].append({'label': label, 'type': 'equation', 'line': env_line})
        elif env in FLOAT_ENVS:
            float_type = 'figure' if 'figure' in env else 'table'
            result['content_items'].append({'line': env_line, 'kind': float_type,
                                            'data': {'label': label, 'caption': caption}})
            if label:
                result['defined_labels'].append({'label': label, 'type': float_type, 'line': env_line})
        elif env in LISTING_ENVS:
            opts_m = re.search(r'\\begin\{' + re.escape(env) + r'\}\[([^\]]*)\]', m.group(0))
            lang = cap = lbl = None
            if opts_m:
                opts = opts_m.group(1)
                if lm := re.search(r'language\s*=\s*(\w+)', opts): lang = lm.group(1)
                if cm := re.search(r'caption\s*=\s*\{([^}]*)\}', opts): cap = cm.group(1)
                if lbm := re.search(r'label\s*=\s*\{([^}]*)\}', opts): lbl = lbm.group(1)
            body_lines = body.strip().splitlines()
            final_label = lbl or label
            result['content_items'].append({'line': env_line, 'kind': 'listing', 'data': {
                'label': final_label, 'caption': cap or caption,
                'lang': lang, 'loc': len(body_lines), 'preview': body_lines[:5],
            }})
            if final_label:
                result['defined_labels'].append({'label': final_label, 'type': 'listing', 'line': env_line})

    already = {e['label'] for e in result['defined_labels']}
    for m in re.finditer(r'\\label\{([^}]+)\}', text):
        if (lbl := m.group(1).strip()) not in already:
            lbl_line = line_of(text, m.start())
            nearby = text[max(0, m.start() - 80):m.start()]
            ltype = 'section' if ('\\section' in nearby or '\\subsection' in nearby) else 'other'
            result['defined_labels'].append({'label': lbl, 'type': ltype, 'line': lbl_line})
            already.add(lbl)

    return result
