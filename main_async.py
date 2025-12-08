#!/usr/bin/env python3
"""
main_async.py
End-to-end асинхронный pipeline:
    загрузка -> ленивые фильтры -> async pipeline -> события (AsyncEventStream) -> отчёты

Запуск: python main_async.py
Требует: Python 3.8+ (рекомендую 3.10+), aiofiles
Установка: pip install aiofiles
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import AsyncIterable, Iterable, Callable, Any, Dict, Optional

# Optional: если хотите использовать свои модули, импортируйте их вместо локальных реализаций.
# from core.services import load_tasks_async
# from core.filters import by_priority, by_status, async_by_assignee
# from core.frp import AsyncEventStream
# from core.reports import overdue_async
# from core.functional.pipelines import async_pipeline

import aiofiles

# ------------------------
# 1) Асинхронная загрузка
# ------------------------
async def load_tasks_async(path: Path) -> tuple:
    """
    Ожидает JSON вида {"tasks": [ {..task..}, ... ]}
    Возвращает tuple задач (immutable-ish)
    """
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        txt = await f.read()
    data = json.loads(txt)
    tasks = tuple(data.get("tasks", []))
    return tasks

# ------------------------
# 2) Утилиты для итераторов
# ------------------------
async def to_async_iter(obj: Any) -> AsyncIterable:
    """
    Преобразует sync Iterable -> async generator, оставляет async iterable как есть.
    """
    if hasattr(obj, "__aiter__"):
        # already async iterable
        async for x in obj:
            yield x
        return

    if hasattr(obj, "__iter__"):
        for x in obj:
            yield x
        return

    # single value
    yield obj

# tiny helper to detect async generator
def is_async_iter(obj: Any) -> bool:
    return hasattr(obj, "__aiter__")

# ------------------------
# 3) Ленивые фильтры (async)
# ------------------------
# Фильтрная функция: Callable[[AsyncIterable], AsyncIterable]
def mk_async_filter(predicate: Callable[[Dict], bool]) -> Callable[[AsyncIterable], AsyncIterable]:
    async def _filter(ait: AsyncIterable):
        async for t in to_async_iter(ait):
            try:
                if predicate(t):
                    yield t
            except Exception:
                # безопасно пропустить ошибочную задачу
                continue
    return _filter

def by_priority(priority: str):
    return mk_async_filter(lambda t: t.get("priority") == priority)

def by_status(status: str):
    return mk_async_filter(lambda t: t.get("status") == status)

# Пример асинхронного фильтра (имитирует IO, например, запрос к DB)
def async_by_assignee(assignee: str):
    async def _filter(ait: AsyncIterable):
        async for t in to_async_iter(ait):
            # имитация асинхронной операции (например, валидации)
            await asyncio.sleep(0)  # yield control
            if t.get("assignee") == assignee:
                yield t
    return _filter

# ------------------------
# 4) Асинхронный pipeline (композитор)
# ------------------------
def async_pipeline(*stages: Callable[[AsyncIterable], AsyncIterable]):
    """
    Возвращает функцию run(input_iterable) -> AsyncIterable
    Каждый stage принимает AsyncIterable и возвращает AsyncIterable.
    """
    async def run(input_iterable: AsyncIterable):
        current = input_iterable
        for stage in stages:
            # Если stage - корутина возвращающая AsyncIterable, вызываем её
            # (но по контракту мы ожидаем stage быть Callable[[AsyncIterable], AsyncIterable])
            current = stage(current)
        # гарантируем async iterable
        async for item in to_async_iter(current):
            yield item
    return run

# ------------------------
# 5) Async FRP / Event stream
# ------------------------
class AsyncEventStream:
    """
    Небольшая обёртка над async iterable, добавляющая map/filter/subscribe.
    """
    def __init__(self, agen: AsyncIterable):
        self.agen = agen

    def amap(self, fn: Callable[[Any], Any]) -> "AsyncEventStream":
        async def gen():
            async for x in to_async_iter(self.agen):
                try:
                    res = fn(x)
                    # поддержка coro return
                    if asyncio.iscoroutine(res):
                        res = await res
                    yield res
                except Exception:
                    continue
        return AsyncEventStream(gen())

    def afilter(self, pred: Callable[[Any], bool]) -> "AsyncEventStream":
        async def gen():
            async for x in to_async_iter(self.agen):
                try:
                    ok = pred(x)
                    if asyncio.iscoroutine(ok):
                        ok = await ok
                    if ok:
                        yield x
                except Exception:
                    continue
        return AsyncEventStream(gen())

    async def subscribe(self, handler: Callable[[Any], Any]):
        """
        handler может быть sync или async. Подписка выполнится до исчерпания стрима.
        """
        async for x in to_async_iter(self.agen):
            res = handler(x)
            if asyncio.iscoroutine(res):
                await res

# ------------------------
# 6) Асинхронные отчёты
# ------------------------
async def overdue_async(tasks_ait: AsyncIterable):
    """
    Генерирует задачи с просроченной датой 'due' (в формате ISO 8601 или timestamp).
    """
    now = datetime.now()
    async for t in to_async_iter(tasks_ait):
        due_raw = t.get("due")
        if not due_raw:
            continue
        # поддержка строк ISO или числового timestamp
        try:
            if isinstance(due_raw, (int, float)):
                due = datetime.fromtimestamp(due_raw)
            else:
                # ожидаем ISO-like
                due = datetime.fromisoformat(due_raw)
        except Exception:
            # невалидный формат — пропускаем
            continue
        if due < now:
            yield t

# ------------------------
# 7) Демонстрационный main
# ------------------------
DATA_PATH = Path("data/seed.json")  # положите здесь ваш файл, либо измените путь

async def main():
    if not DATA_PATH.exists():
        # fallback: создаём минимальный seed.json для демонстрации
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        demo = {
            "tasks": [
                {"id": "t1", "title": "Fix bug", "priority": "high", "status": "open", "assignee": "alice", "due": (datetime.now().isoformat())},
                {"id": "t2", "title": "Write tests", "priority": "low", "status": "open", "assignee": "bob", "due": (datetime.now().isoformat())},
                {"id": "t3", "title": "Old task", "priority": "high", "status": "open", "assignee": "alice", "due": (datetime.fromtimestamp(0).isoformat())}
            ]
        }
        async with aiofiles.open(DATA_PATH, "w", encoding="utf-8") as f:
            await f.write(json.dumps(demo, indent=2, ensure_ascii=False))
        print(f"[init] created demo {DATA_PATH}")

    # 1) load
    tasks = await load_tasks_async(DATA_PATH)   # tuple of dicts

    # 2) build pipeline: примеры фильтров
    pipe = async_pipeline(
        by_priority("high"),      # sync predicate wrapped to async
        by_status("open"),        # another
        async_by_assignee("alice")# async filter (simulated IO)
    )

    # 3) run pipeline -> async iterable
    filtered_ait = pipe(tasks)  # это AsyncIterable

    # 4) event stream: помечаем событием просмотр каждой задачи
    stream = AsyncEventStream(filtered_ait).amap(lambda t: {"event": "TASK_SEEN", "task": t})

    # 5) optional: логируем события асинхронно (subscribe)
    async def logger(evt):
        # имитация асинхронной логики
        await asyncio.sleep(0)
        print("[event]", evt["event"], "->", evt["task"]["id"])

    # Запускаем подписчика в фоне чтобы параллельно собрать отчёт (демонстрация)
    subscriber_task = asyncio.create_task(stream.subscribe(logger))

    # 6) отчёт: берем stream.agen (async iterable) и достаём из него tasks для отчёта
    # Важно: stream уже "потреблен" частично subscriber-ом; для реального мульти-консьюмера
    # нужно применять мультиплексацию или создавать независимые потоки (см. замечание ниже).
    # Для простоты мы создаём новый pipeline: применим те же фильтры к исходным tasks для отчёта.
    report_pipe = async_pipeline(
        by_priority("high"),
        by_status("open"),
        # не фильтруем по assignee, чтобы показать разные варианты
    )
    report_source = report_pipe(tasks)
    overdue = overdue_async(report_source)

    print("\nOverdue tasks:")
    async for t in overdue:
        print(" -", t["id"], t.get("title"))

    # дождёмся логгера
    await subscriber_task

# ------------------------
# 8) Заметки / рекомендации по интеграции в ваш проект
# ------------------------
# - Если в вашем проекте уже есть асинхронные функции (core.async_ops или core.services),
#   используйте их: import и подставьте вместо load_tasks_async.
# - Если хотите, чтобы один поток событий обслуживался несколькими подписчиками,
#   нужно реализовать мультиплексор: буферизовать события и давать каждому подписчику свой async iterator.
# - Для параллельных CPU-bound задач используйте ProcessPoolExecutor, для IO-bound — ThreadPoolExecutor,
#   но обычно асинхронность + await достаточно для IO-heavy workloads.
# - Проверьте формат поля "due" в ваших данных; код ожидает ISO-строку или timestamp.
# ------------------------

if __name__ == "__main__":
    asyncio.run(main())
