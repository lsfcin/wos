ROW: int
HUB_GAP: int
LABEL_W: int
LINK_W: int
PAD: int
BAR: int
HUB_MIN: int

def render_graph(points: list, dangling: list) -> str: ...
def render_bars(points: list, dangling: list, grain: str) -> str: ...
def legend() -> str: ...
