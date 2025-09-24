from typing import Callable
from .domain import Task, Comment


# ----------------------------
# 1. Замыкания-фильтры (Closures)
# ----------------------------
def by_priority(priority: str) -> Callable[[Task], bool]:
    """Фильтр по приоритету"""
    return lambda t: t.priority == priority


def by_assignee(user_id: str) -> Callable[[Task], bool]:
    """Фильтр по исполнителю"""
    return lambda t: t.assignee == user_id


def by_date_range(start: str, end: str) -> Callable[[Task], bool]:
    """Фильтр по диапазону дат (created)"""
    return lambda t: start <= t.created <= end


# ----------------------------
# 2. Рекурсивные функции
# ----------------------------
def walk_comments(
    comments: tuple[Comment, ...], task_id: str, idx: int = 0
) -> tuple[Comment, ...]:
    """Рекурсивный проход по комментариям задачи"""
    if idx >= len(comments):
        return ()
    current = comments[idx]
    rest = walk_comments(comments, task_id, idx + 1)
    if current.task_id == task_id:
        return (current,) + rest
    return rest


def traverse_tasks(
    tasks: tuple[Task, ...], status_order: tuple[str, ...], idx: int = 0
) -> tuple[str, ...]:
    """Рекурсивный проход по задачам в порядке статусов"""
    if idx >= len(status_order):
        return ()
    status = status_order[idx]
    filtered = tuple(t.id for t in tasks if t.status == status)
    return filtered + traverse_tasks(tasks, status_order, idx + 1)
