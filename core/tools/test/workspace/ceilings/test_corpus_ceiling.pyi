from _typeshed import Incomplete

HEAD_WARN: Incomplete
FINISHED_CEILING: int
UNDESCRIBED_CEILING: int
MISPLACED_CEILING: int
ROUTING_CEILING: int
FINISHED_SLACK: int
UNDESCRIBED_SLACK: int
MISPLACED_SLACK: int
ROUTING_SLACK: int

def test_prose_describing_finished_work_does_not_grow() -> None: ...
def test_unanswered_placeholders_do_not_grow() -> None: ...
def test_routing_tables_pointing_at_untracked_files_do_not_grow() -> None: ...
def test_constraints_in_context_heads_do_not_grow() -> None: ...
def test_the_ceilings_are_not_stale() -> None: ...
