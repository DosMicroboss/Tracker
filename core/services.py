# core/services.py
from __future__ import annotations
from typing import Callable, Iterable
from core.domain import Task
from core.functional.either import Either
import inspect
from core.async_ops import bulk_update_status, project_overview_async

class TaskService:
    """
    Фасад создания задач.
    validators: список функций (task, rules) -> Either[errors, Task]
    rules: правила валидации
    """

    def __init__(self, validators: list[Callable], rules):
        self.validators = validators
        self.rules = rules

    def create_task(self, task: Task) -> Either:
        for validate in self.validators:
            res = validate(task, self.rules)
            if not res.is_right:  # <-- исправлено
                return res
            task = res.value

        return Either.right(task)


class StatusService:
    """
    Изменение статуса задач.
    updaters: список функций (task, new_status) -> Task
    Но апдейтеры могут иметь разную сигнатуру (bound-method, function и т.п.).
    Поэтому пробуем несколько вариантов вызова.
    """

    def __init__(self, updaters: list[Callable]):
        self.updaters = updaters

    def _call_updater(self, updater: Callable, task: Task, status: str) -> Task:
        """
        Попробовать корректно вызвать updater, поддерживая несколько сигнатур:
        - updater(task, status)
        - updater(status)               (если updater — bound method, привязанный к task)
        - updater(task)                 (если updater инвертирован — возвращает функцию, использующая новый статус иначе)
        """
        # Попытка 1: стандартный вызов (task, status)
        try:
            return updater(task, status)
        except TypeError as e1:
            # попытка 2: bound method / callable, ожидающий только new_status (updater привязан к экземпляру)
            try:
                return updater(status)
            except TypeError:
                # попытка 3: callable, ожидающий только task (менее вероятно, но безопасно пробуем)
                try:
                    return updater(task)
                except TypeError:
                    # если всё упало — пробуем собрать диагностическое сообщение и пробросить исходную ошибку
                    # для удобства отладки включаем информацию о сигнатуре
                    sig = None
                    try:
                        sig = inspect.signature(updater)
                    except Exception:
                        sig = "<no-signature>"
                    raise TypeError(
                        f"Updater {updater!r} has incompatible signature {sig}. "
                        "Tried updater(task,status), updater(status), updater(task)."
                    ) from e1

    def change_status(self, task: Task, status: str) -> Task:
        for updater in self.updaters:
            task = self._call_updater(updater, task, status)
        return task


class ReportService:
    """
    Агрегация отчётов.
    aggregators: список функций (project_id) -> dict
    """

    def __init__(self, aggregators: list[Callable]):
        self.aggregators = aggregators

    def project_report(self, project_id: str) -> dict:
        result = {}
        for agg in self.aggregators:
            part = agg(project_id)
            if isinstance(part, dict):
                result.update(part)
        return result
