from functools import lru_cache
from datetime import datetime, timedelta
from core.domain import Task
from core.functional.maybe import Maybe
from core.functional.either import Either
from core.functional.pipelines import TASKS


class RuleResult:
    def __init__(self, ok: bool, msg: str = ""):
        self.ok = ok
        self.msg = msg


class Rule:
    def __init__(self, max_days: int = 1):
        self.max_days = max_days
        self.name = "max_days_rule"

    def check(self, t: Task) -> RuleResult:
        try:
            updated_date = datetime.strptime(t.updated, "%Y-%m-%d")
        except Exception:
            return RuleResult(False, "Invalid updated date format (YYYY-MM-DD required)")

        days = (datetime.now() - updated_date).days

        if days > self.max_days and t.status != "done":
            return RuleResult(False, f"Task overdue by {days - self.max_days} days")

        return RuleResult(True)


#@lru_cache(maxsize=None)
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

def safe_task(tasks: tuple[Task, ...], tid: str) -> Maybe[Task]:
    for t in tasks:
        if t.tid == tid:
            return Maybe(t)
    return Maybe(None)


def validate_task(t: Task, rules: tuple[Rule, ...]) -> Either[dict, Task]:
    errors = {}
    for rule in rules:
        res = rule.check(t)
        if not res.ok:
            errors[rule.name] = res.msg
    if errors:
        return Either.left(errors)
    return Either.right(t)


def create_pipeline(tasks: tuple[Task, ...], t: Task, rules: tuple[Rule, ...]):
    return (
        validate_task(t, rules)
        .map(lambda valid_task: tasks + (valid_task,))
    )
def report_count_by_status(tasks: tuple[Task, ...]) -> dict:
    counts = {}
    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1
    return counts