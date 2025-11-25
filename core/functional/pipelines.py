from typing import Tuple
from core.domain import Task, Rule
from core.functional.maybe import Maybe
from core.functional.either import Either

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


def lazy_status_stream(stream: Iterable[Task]) -> Iterator[tuple[str, int]]:
    counts = {}
    for t in stream:
        status = t.status
        counts[status] = counts.get(status, 0) + 1
        yield (status, counts[status])