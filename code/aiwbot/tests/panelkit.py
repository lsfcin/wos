# panelkit.py — shared panel-test scaffolding: a fake backend plus keyboard readers.
from backend import Capabilities

FAVS = ["opencode/a", "opencode/b", "opencode/c", "opencode/d"]
CAPS = Capabilities(modes=["build", "plan"], favourites=FAVS,
                    groups={"opencode": FAVS, "big": [f"big/m{i}" for i in range(20)]})


class Fake:
    """A backend that declares a shortlist plus one big provider, and an effort vocabulary only
    once a model is chosen — which is the opencode shape the panel has to handle."""

    def capabilities(self):
        return CAPS

    def efforts(self, model=None):
        return ["low", "high", "max"] if model else []


def labels(markup):
    """Rows of button text, for assertions about layout."""
    out = []
    for row in markup.inline_keyboard:
        line = [button.text for button in row]
        out.append(line)
    return out


def texts(markup):
    flat = []
    for row in markup.inline_keyboard:
        for button in row:
            flat.append(button.text)
    return flat


def data(markup):
    flat = []
    for row in markup.inline_keyboard:
        for button in row:
            flat.append(button.callback_data)
    return flat
