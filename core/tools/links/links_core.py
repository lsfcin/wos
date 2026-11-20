# links_core.py — the short name map read+write boundary, and the redirect file it emits, for links/cfpages
#
# The mapping is the source of truth and lives HERE, in the workspace, versioned like every other
# registry in core/ (features.txt, profile.txt, deps.txt, harnesses.txt are the same shape). What
# gets published is generated from it and owned by nobody: a `_redirects` file in a throwaway
# public repo. Delete that repo and one `build` rebuilds it; delete this file and the short names are
# gone, which is the asymmetry that decides where it lives.
import datetime
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'hooks'))
import feature_law  # noqa: E402

MAP = HERE / 'links.txt'
HEADER = ('short_name', 'url', 'owner', 'added')


def base() -> str:
    """The published domain, read from core/profile.txt rather than held here.

    A `pages.dev` name is globally unique across every Cloudflare account, so the one this
    workspace gets is whatever was still free the day the project was made — `lsf` was taken,
    which is a fact about a stranger's account and cannot live in shared code.
    """
    return feature_law.setting('links-base', 'https://example.pages.dev')

# A short name is what Lucas says out loud to a room, so the grammar is what survives being spoken and
# typed from memory: lowercase, digits, hyphen, and AT MOST ONE slash. The one level is for a
# course — `ai4good/setup` — because the things he hands out cluster by course and nothing else
# clusters at all. A second level would be a directory tree nobody can recite.
SHORT_NAME_RE = re.compile(r'^[a-z0-9][a-z0-9-]*(/[a-z0-9][a-z0-9-]*)?$')

# WHY THESE ARE REFUSED, AND WHY THE CHECK IS ON THE SHORT NAME RATHER THAN THE URL.
# A redirect is public: anyone who types a short name is sent wherever it points. That is harmless when
# the target needs a Google login — they hit a permission wall. It is NOT harmless for a document
# shared as "anyone with the link", because a guessable short name turns *unlisted* into *discoverable*,
# and the branches/ notary, health and finance documents are exactly the kind shared that way.
# The URL cannot answer this — a Drive URL looks identical whoever it is shared with — so the
# guard keys on the two things that CAN answer: the name Lucas chose, and the file he is
# recording the link in. Both are refusals, not warnings, because the failure is silent and
# permanent: nothing ever tells you a stranger guessed the short name.
PRIVATE = ('branches', 'casinhas', 'saude', 'financas')


class Refused(Exception):
    """A refusal that names its own fix. Printed as-is; never a traceback."""


def _rows(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        parts = line.split('\t')
        if tuple(parts[:4]) == HEADER:
            continue
        out.append(dict(zip(HEADER, (parts + ['', '', '', ''])[:4])))
    return out


def load(path: pathlib.Path = MAP) -> list[dict]:
    if not path.exists():
        return []
    return _rows(path.read_text(encoding='utf-8'))


def preamble(path: pathlib.Path = MAP) -> list[str]:
    """The leading `#` block — what the file is. A whole-file rewrite must not eat it."""
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.startswith('#'):
            break
        out.append(line)
    return out


def save(rows: list[dict], path: pathlib.Path = MAP) -> None:
    """Rewritten whole and sorted by short name, so a diff shows the one row that changed."""
    lines = preamble(path) + ['\t'.join(HEADER)]
    lines += ['\t'.join(r[k] for k in HEADER) for r in sorted(rows, key=lambda r: r['short_name'])]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def validate_short_name(short_name: str) -> None:
    if not SHORT_NAME_RE.match(short_name):
        raise Refused(
            f"'{short_name}' is not a sayable short name.\n"
            f"  lowercase, digits and hyphen, with at most one '/' for a course:\n"
            f"    ai4good        a course home\n"
            f"    ai4good/setup  something inside it\n"
            f"    rva-chico      a one-off, flat and hyphenated"
        )


def check_private(short_name: str, home: str = '') -> None:
    """Refuse a short name that would publish a private thing. `home` is the file recording the link."""
    # The hyphen is a word boundary here, not just the slash: a flat short name is how a one-off is
    # named, so `casinhas-planta` is exactly the shape the refusal is for. Matching whole
    # segments alone let that through on the first run of this check.
    head = short_name.split('/')[0]
    if head in PRIVATE or head.split('-')[0] in PRIVATE:
        raise Refused(
            f"'{short_name}' names a private subtree, so it gets no short name.\n"
            f"  A redirect is public — a guessable short name turns an 'anyone with the link'\n"
            f"  document into a discoverable one. Hand out the canonical URL instead."
        )
    if home and pathlib.PurePosixPath(home).parts[:1] == ('branches',):
        raise Refused(
            f"{home} is under branches/, so its links get no short name.\n"
            f"  Same reason: the redirect is public and the sharing on those documents is not.\n"
            f"  Hand out the canonical URL instead."
        )


def add(short_name: str, url: str, owner: str = '', home: str = '',
        path: pathlib.Path = MAP) -> dict:
    """Mint one short name. Refuses rather than overwrites — a live link must not silently move."""
    validate_short_name(short_name)
    check_private(short_name, home)
    if not url.startswith(('http://', 'https://')):
        raise Refused(f"'{url}' is not a URL. A short name points somewhere reachable or nowhere.")
    rows = load(path)
    for r in rows:
        if r['short_name'] == short_name:
            raise Refused(
                f"'{short_name}' is taken — it points at {r['url']}\n"
                f"  Pick another name, or `cfpages rm {short_name}` first if that link is dead."
            )
    row = {'short_name': short_name, 'url': url, 'owner': owner or short_name.split('/')[0],
           'added': datetime.date.today().isoformat()}
    rows.append(row)
    save(rows, path)
    return row


def remove(short_name: str, path: pathlib.Path = MAP) -> dict:
    rows = load(path)
    kept = [r for r in rows if r['short_name'] != short_name]
    if len(kept) == len(rows):
        raise Refused(f"'{short_name}' is not in the map. `cfpages find {short_name}` to look for a near miss.")
    save(kept, path)
    return next(r for r in rows if r['short_name'] == short_name)


def find(term: str, path: pathlib.Path = MAP) -> list[dict]:
    """Query, never read whole. This is what keeps a file that grows forever cheap to consult."""
    t = term.lower()
    return [r for r in load(path) if t in r['short_name'].lower() or t in r['url'].lower()
            or t in r['owner'].lower()]


def redirects(rows: list[dict], code: int = 302) -> str:
    """Cloudflare Pages' `_redirects`: `<from> <to> <status>`, one per line, longest match wins.

    302 and not 301: a 301 is cached by the browser forever, so a short name pointed at the wrong
    document once would keep going there on Lucas's own machine long after the map was fixed.
    """
    lines = [f"/{r['short_name']} {r['url']} {code}" for r in sorted(rows, key=lambda r: r['short_name'])]
    return '\n'.join(lines) + '\n'


def check(rows: list[dict]) -> list[str]:
    """Everything that is untrue about the map, one finding per line."""
    findings, seen = [], {}
    for r in rows:
        try:
            validate_short_name(r['short_name'])
            check_private(r['short_name'])
        except Refused as e:
            findings.append(f"{r['short_name']}: {str(e).splitlines()[0]}")
        if r['short_name'] in seen:
            findings.append(f"{r['short_name']}: listed twice")
        seen[r['short_name']] = r
        if not r['url'].startswith(('http://', 'https://')):
            findings.append(f"{r['short_name']}: target is not a URL ({r['url']})")
    return findings
