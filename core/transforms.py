from functools import reduce
from .domain import Task

def add_task(tasks: tuple[Task, ...], t: Task) -> tuple[Task, ...]:
    return tasks + (t,)

def remove_task(tasks: tuple[Task, ...], task_id: str) -> tuple[Task, ...]:
    return tuple(t for t in tasks if t.id != task_id)

def filter_by_status(tasks: tuple[Task, ...], status: str) -> tuple[Task, ...]:
    return tuple(filter(lambda x: x.status == status, tasks))

def avg_tasks_per_user(tasks: tuple[Task, ...]) -> float:
    if not tasks: return 0.0
    user_task_counts = reduce( lambda acc, t: {**acc, t.assignee: acc.get(t.assignee, 0) + 1} if t.assignee else acc, tasks, {}, )
    if not user_task_counts:
        return 0.0
    return sum(user_task_counts.values()) / len(user_task_counts)