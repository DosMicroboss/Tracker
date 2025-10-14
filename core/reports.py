from functools import lru_cache
from datetime import datetime, timedelta
from core.domain import Task

class Rule:
    def __init__(self, max_days: int = 1):
        self.max_days = max_days


@lru_cache(maxsize=None)
def overdue_tasks(tasks: tuple[Task, ...], rules: tuple[Rule, ...], index: int = 0) -> tuple[Task, ...]:
    if index >= len(tasks):
        return ()

    t = tasks[index]
    rest = overdue_tasks(tasks, rules, index + 1)

    rule = rules[0] if rules else Rule()
    try:
        updated_date = datetime.strptime(t.updated, "%Y-%m-%d")
    except ValueError:
        return rest

    if (datetime.now() - updated_date).days > rule.max_days and t.status != "done":
        return (t,) + rest
    else:
        return rest
