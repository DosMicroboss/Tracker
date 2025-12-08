import asyncio
from core.domain import Task, User


async def bulk_update_status(tasks: list[Task], status: str) -> list[Task]:
    async def update_one(task: Task) -> Task:

        await asyncio.sleep(3)
        # возвращаем НОВЫЙ Task
        return Task(**{**task.__dict__, "status": status})

    # параллельное выполнение
    return await asyncio.gather(*(update_one(t) for t in tasks))


import asyncio
from collections import Counter


async def _count_by_status(tasks: list[Task]) -> dict:
    await asyncio.sleep(0.01)
    return dict(Counter(t.status for t in tasks))


async def _count_by_assignee(tasks: list[Task], users) -> dict:
    await asyncio.sleep(0.01)

    # users может быть:
    # - dict (как USERS)
    # - list[dict]
    # - list[User]
    # приводим всё к единому списку dict/объектов
    if isinstance(users, dict):
        users = users.values()

    user_map = {}

    for u in users:
        if isinstance(u, User):
            # это настоящий объект User
            user_map[u.id] = u.name
        else:
            # это dict из JSON
            user_map[u["id"]] = u.get("name", u["id"])

    # считаем по исполнителям
    return dict(Counter(user_map.get(t.assignee, "unknown") for t in tasks))


async def _count_by_priority(tasks: list[Task]) -> dict:
    await asyncio.sleep(0.01)
    return dict(Counter(t.priority for t in tasks))


async def project_overview_async(tasks: list[Task], users: list[User]) -> dict:
    by_status, by_assignee, by_priority = await asyncio.gather(
        _count_by_status(tasks),
        _count_by_assignee(tasks, users),
        _count_by_priority(tasks),
    )

    return {
        "by_status": by_status,
        "by_assignee": by_assignee,
        "by_priority": by_priority,
    }
