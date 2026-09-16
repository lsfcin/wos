# tool_law.py — the feature switch for core/tools features: the one guard every CLI entrypoint calls
#
# Shares the tools root with attachments_util.py for the same reason: more than one family
# imports it. It adds nothing to feature_law and restates no rule — it only carries the
# sys.path hop from a tool to core/hooks, so a tool's entrypoint spends one line on
# being switchable instead of six.
#
# WHY A TOOL GUARDS AT ITS ENTRYPOINT. core/SPECS.md § AD-14 groups skills and
# tools together as the rows with nowhere to put a call, and for skills that is
# exactly true: a skill is markdown, calls no function, and the only real way to switch it
# off is the mirror refusing to publish it. A tool is not markdown. It is a CLI this
# workspace owns, so it HAS a moment of its own — the moment it is invoked — and refusing
# there is a stronger observable than anything a shared publisher could offer. So these
# rows take a guard per family rather than a group boundary, and the behavioural check in
# test_features.py gets a per-row answer instead of one answer covering seven.
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1] / 'hooks'))
import feature_law  # noqa: E402

# sysexits.h EX_UNAVAILABLE. Deliberately not 1: an ablation arm has to tell "switched off"
# apart from "ran and failed", and every tool here already exits 1 on a real error.
OFF_EXIT = 69


def require(name: str) -> None:
    """Stop the tool when its feature is switched off, naming the name and the way back.

    Called at the top of a CLI entrypoint, before any work. `feature_law.is_enabled` fails
    OPEN on an unknown name, so a typo here leaves the tool behaving exactly as it did
    before this module existed — a feature is never lost to a bad line of data.
    """
    if feature_law.is_enabled(name):
        return
    _sys.stderr.write(
        f"{name}: switched off for this workspace.\n"
        f"  core/profile.txt holds the versioned answer; WOS_FEATURES_OFF subtracts for one run.\n"
    )
    raise SystemExit(OFF_EXIT)
