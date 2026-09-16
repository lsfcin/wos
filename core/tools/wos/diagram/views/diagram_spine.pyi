ROW: int
INDENT: int
PAD: int
LABEL_DY: int

def render(nodes: dict, edges: list, max_depth: int = 3) -> str: ...
def legend(coverage: dict) -> str: ...
