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


def with_status(self, new_status):
    return Task(
        id=self.id,
        project_id=self.project_id,
        title=self.title,
        desc=self.desc,
        status=new_status,
        priority=self.priority,
        assignee=self.assignee,
        created=self.created,
        updated=time.time()
    )
