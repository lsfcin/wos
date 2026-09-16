# The page's honesty block: what this picture covered, what it inferred, and where to change it.
#
# Split from diagram_page.py by responsibility: the shell renders, this states what the rendering
# is worth. Every line here is a claim ABOUT the document above it, and a claim goes stale on a
# different schedule than the markup carrying it — which is why they are not edited together.
from html import escape


def _coverage(coverage: dict) -> str:
    unparsed = coverage['unparsed']
    return (f'<b>coverage</b> parsed {coverage["parsed"]} of {coverage["total"]} routing blocks'
            + (f' · <b>{len(unparsed)} unparsed:</b> {escape(", ".join(unparsed))}'
               if unparsed else ' · none unparsed'))


def _scope(scope: dict) -> str:
    return (f'<p><b>scope</b> the workspace repository. {scope["nested"]} repositories nested '
            'inside it are drawn as directories and no deeper: each is its own repository, and '
            'none carries a picture of its own.</p>')


def _sources() -> str:
    return ('<p><b>how to change it</b> edit the source, not this file: '
            '<code>core/features.txt</code> for the matrix, a directory\'s '
            '<code>CONTEXT.md</code> for the spine'
            '. Regenerated and committed by <code>/roundup</code> at every session close, so a '
            'stale picture is a bug in the close, not a fact of life.</p>')


def render(coverage: dict, scope: dict) -> str:
    return '\n'.join([
        '<footer>',
        f'<p>{_coverage(coverage)}</p>',
        _scope(scope),
        '<p><b>what is inferred</b> nothing, as of 2026-08-18. Every edge above renders declared '
        'or generated data, the firing moment included: '
        '<code>core/hooks/trigger/trigger_law.py</code> reads it from the registrations, the '
        'pre-commit dispatcher\'s own stage order and the install steps. What the registrations '
        'cannot place is counted as a gap instead of guessed at.</p>',
        _sources(),
        '</footer>'])
