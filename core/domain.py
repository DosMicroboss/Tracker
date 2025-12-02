from dataclasses import dataclass
from typing import Optional
import time


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    owner: str


@dataclass(frozen=True)
class User:
    id: str
    name: str
    role: str


@dataclass(frozen=True)
class Task:
    id: str
    project_id: str
    title: str
    desc: str
    status: str
    priority: str
    assignee: Optional[str]
    created: str
    updated: str


@dataclass(frozen=True)
class Comment:
    id: str
    task_id: str
    author: str
    text: str
    ts: str


@dataclass(frozen=True)
class Event:
    id: str
    ts: str
    name: str
    payload: dict


@dataclass(frozen=True)
class Rule:
    id: str
    kind: str
    payload: dict


# -----------------------------
#  Правильный updater-функционал
# -----------------------------
def with_status(task: Task, new_status: str) -> Task:
    """Функция-трансформер: возвращает новую задачу с обновлённым статусом."""
    return Task(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        desc=task.desc,
        status=new_status,
        priority=task.priority,
        assignee=task.assignee,
        created=task.created,
        updated=time.time(),
    )
