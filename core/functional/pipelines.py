from typing import Tuple
from core.domain import Task, Rule
from core.functional.maybe import Maybe
from core.functional.either import Either
from typing import Callable, Any, Iterable
import time

from typing import Iterable, Iterator


def create_pipeline(tasks: tuple[Task, ...], t: Task, rules: tuple[Rule, ...]) -> Either[dict, Tuple[Task, ...]]:
    from core.reports import validate_task
    validation = validate_task(t, rules)

    return (
        validation.map(lambda valid_task: tasks + (valid_task,))
    )
def iter_tasks(tasks: tuple[Task, ...], pred) -> Iterable[Task]:
    for t in tasks:
        if pred(t):
            yield t



def compose(*functions: Callable) -> Callable:
    def inner(arg):
        for f in reversed(functions):
            arg = f(arg)
        return arg
    return inner

def pipe(value: Any, *functions: Callable) -> Any:
    """pipe(x, f, g, h) = h(g(f(x)))"""
    for f in functions:
        value = f(value)
    return value

# -------------------------
# Lazy status stream (для пайплайна)
# -------------------------
def lazy_status_stream(tasks: Iterable[Task]):
    """Генерирует статус-стрим в стиле FRP/ленивый"""
    stats = {}
    statuses = ["todo", "in_progress", "review", "done"]
    for t in tasks:
        stats[t.status] = stats.get(t.status, 0) + 1
        for s in statuses:
            yield (s, stats.get(s, 0))
        time.sleep(0.1)  # имитация обновления


TASKS: dict[str, list[Task]] = {}   # project_id → list[Task]

def save_task(t: Task):
    TASKS.setdefault(t.project_id, []).append(t)
    return t

