import asyncio
from core.domain import Task, User
from collections import Counter

async def bulk_update_status(tasks: list[Task], status: str) -> list[Task]:
    async def update_one(task: Task) -> Task:

        await asyncio.sleep(3)
        return Task(**{**task.__dict__, "status": status})

    # параллельное выполнение
    return await asyncio.gather(*(update_one(t) for t in tasks))




async def _count_by_status(tasks: list[Task]) -> dict:
    await asyncio.sleep(3)
    return dict(Counter(t.status for t in tasks))


async def _count_by_assignee(tasks: list[Task], users) -> dict:
    await asyncio.sleep(5)
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


from typing import List, Dict, AsyncGenerator
from core.domain import Task, User
from collections import Counter


# -------------------------------
# Ленивые генераторы
# -------------------------------
async def async_iter(tasks: List[Task]) -> AsyncGenerator[Task, None]:
    """Асинхронный генератор по задачам"""
    for task in tasks:
        await asyncio.sleep(0)  # yield control
        yield task


async def filter_tasks(tasks: List[Task], predicate) -> AsyncGenerator[Task, None]:
    """Асинхронный ленивый фильтр"""
    async for task in async_iter(tasks):
        if predicate(task):
            yield task


# -------------------------------
# Подсчёты
# -------------------------------
async def count_by_status(tasks: AsyncGenerator[Task, None]) -> Dict[str, int]:
    counter = Counter()
    async for t in tasks:
        counter[t.status] += 1
    return dict(counter)


async def count_by_priority(tasks: AsyncGenerator[Task, None]) -> Dict[str, int]:
    counter = Counter()
    async for t in tasks:
        counter[t.priority] += 1
    return dict(counter)


async def count_by_assignee(tasks: AsyncGenerator[Task, None], users) -> Dict[str, int]:
    if isinstance(users, dict):
        users = users.values()
    user_map = {}
    for u in users:
        if isinstance(u, User):
            user_map[u.id] = u.name
        else:
            user_map[u["id"]] = u.get("name", u["id"])

    counter = Counter()
    async for t in tasks:
        counter[user_map.get(t.assignee, "unknown")] += 1
    return dict(counter)


# -------------------------------
# End-to-end overview
# -------------------------------
async def project_overview_async(tasks: List[Task], users: List[User]) -> Dict:
    filtered_list = [t async for t in filter_tasks(tasks, lambda t: t.status != "done")]

    by_status, by_assignee, by_priority = await asyncio.gather(
        _count_by_status(filtered_list),
        _count_by_assignee(filtered_list, users),
        _count_by_priority(filtered_list)
    )
    return {
        "by_status": by_status,
        "by_assignee": by_assignee,
        "by_priority": by_priority
    }


