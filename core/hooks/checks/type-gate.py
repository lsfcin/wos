#!/usr/bin/env python3
# Level 0 gate (core/SCHEMA.md § The .md type system): a staged file must be a known .md type or a
# well-shaped instance, must sit where its type is allowed to live, must give the routing table
# something to write about it, and a CONTEXT.md must not hand-list files. Zero-token, no LLM.
#
# The law is PARSED from core/SCHEMA.md by schema_law.py, never restated here. It was
# already duplicated across three files before this gate existed, which is the exact drift
# class the gate is meant to catch — a second copy in the checker would be the same bug
# wearing a lab coat.
#
# Ratchet, like the spec-drive gate (core/hooks/pre-commit 1d): only files this commit ADDS
# are blocked. Pre-existing violations are reported by the entropy dashboard
# (entropy-dashboard.py), not by failing every commit in a repo that
# inherited them.
import re
import sys
from pathlib import Path

# The law is one level up; the checks this gate runs live in entropy/.
_HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HOOKS))
sys.path.insert(0, str(_HOOKS / 'entropy'))

import feature_law  # noqa: E402
from entropy_context import (check_description, check_goal_link,  # noqa: E402
                             check_inventory)
from entropy_corpus import (enforcement_paths, staged_added_files,  # noqa: E402
                            wiki_exempt_paths)
from entropy_fields import field_hits  # noqa: E402
from entropy_list import (finished_work_hits, goal_vocabulary,  # noqa: E402
                            wiki_link_hits)
from entropy_naming import check_dirs, check_placement, check_shape  # noqa: E402
from entropy_stores import experiment_hits, ref_level_hits  # noqa: E402
from schema_law import SCHEMA, WORKSPACE_ROOT, load_law, load_scopes  # noqa: E402

# CLAUDE.md and GEMINI.md are mandated by their respective harnesses, not chosen by us; a gate cannot un-invent them.
HARNESS_MANDATED = {'CLAUDE.md', 'GEMINI.md'}

UPPERCASE_MD = re.compile(r'^[A-Z][A-Z0-9_.-]*\.md$')


def check_name(path: Path, allowed: set, exempt: set) -> str | None:
    name = path.name
    if not UPPERCASE_MD.match(name):
        return None
    if name in allowed or name in exempt or name in HARNESS_MANDATED:
        return None
    return (f"{path}: '{name}' is not a known .md type.\n"
            f"   Route it (core/SCHEMA.md § The four disposal routes): generated or plain\n"
            f"   content -> lowercase instance; a constraint -> SPECS.md; or add it to the\n"
            f"   allowlist in core/SCHEMA.md § The `.md` type system if you mean it.")


def failures_for(path: Path, allowed: set, exempt: set, scopes: dict,
                 vocabulary: set) -> list:
    found = [f for f in (check_name(path, allowed, exempt),
                         check_inventory(path) if path.name == 'CONTEXT.md' else None,
                         check_description(path),
                         check_goal_link(path),
                         check_shape(path, allowed),
                         check_dirs(path, WORKSPACE_ROOT),
                         check_placement(path, scopes, WORKSPACE_ROOT)) if f]
    return (found
            + wiki_link_hits([path], vocabulary, wiki_exempt_paths(WORKSPACE_ROOT))
            # Completion is deletion, and until this line the rule was detected by the dashboard
            # and enforced by nobody. Ratcheted like everything else here: a file this commit ADDS
            # may not arrive already describing work that landed. The inherited queue stays the
            # dashboard's, on the ceiling in test_corpus_ratchet.py.
            + finished_work_hits([path], enforcement_paths(WORKSPACE_ROOT))
            # The two doubt stores are small, closed and clean today, so this one goes in total
            # rather than on a ratchet: a new experiment or a newly judged reference arrives with
            # the discipline or does not arrive (core/SPECS.md § AD-16 band 1).
            + experiment_hits([path]) + ref_level_hits([path])
            # A header field naming our own code is a claim about our own tree, and the tree is
            # right here (core/SCHEMA.md § Every field that names our own code is verified). Total like the stores above:
            # the declarations are clean today, so a new one arrives resolving or does not arrive.
            # `governs` is left to the dashboard — its list mixes paths with prose, and a token
            # misread there would stop a commit instead of printing a line.
            + field_hits([path], mixed=False))


def main() -> int:
    if not feature_law.is_enabled('type-gate'):
        return 0  # switched off: a disabled gate does not block, and does not pretend it ran
    if not SCHEMA.exists():
        return 0  # not the workspace repo; nothing to enforce against
    allowed, exempt = load_law(SCHEMA)
    scopes = load_scopes(SCHEMA)
    vocabulary = goal_vocabulary(WORKSPACE_ROOT / 'brain/goals')
    failures = []
    for path in staged_added_files():
        if path.exists():
            failures.extend(failures_for(path, allowed, exempt, scopes, vocabulary))
    if failures:
        print('⛔ type gate:')
        for failure in failures:
            print(f'   {failure}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
