# short_name.py — the one line a tool spends on offering `--short-name`: mint a short link for what it created
#
# Shares the tools root with tool_law.py for the same reason and in the same shape: more than one
# family imports it, and core/tools/SPECS.md § Naming says such a module belongs here rather than
# inside any one family. It restates nothing from links_core — it carries the sys.path hop from a
# creating tool to core/tools/links, so gforms, gslides, gdocs and gdrive each spend one line on
# being able to name what they just made instead of six.
#
# WHY THE CREATING TOOL IS WHERE THIS BELONGS. core/tools/SPECS.md § "A step an agent must never
# skip has to cost one call": a shortener that runs as a separate pass is a pass someone has to
# remember, and the evidence in that section is that emphatic prose does not make a step happen —
# a cheaper tool does. The moment a link exists is the only moment its name is obvious, so that
# is where the flag lives.
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent / 'links'))
import links_core  # noqa: E402

Refused = links_core.Refused


def mint(short_name: str, url: str, owner: str = '', home: str = '') -> str:
    """Add the short name and return the line to print. Refusals reach the caller as `Refused`."""
    links_core.add(short_name, url, owner=owner, home=home)
    return (f"  short:   {links_core.base()}/{short_name}"
            f"  (live after: core/run tools/links/cfpages build --push)")
