# core/services.py
from __future__ import annotations
from typing import Callable, Iterable
from core.domain import Task
from core.functional.either import Either


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
    """

    def __init__(self, updaters: list[Callable]):
        self.updaters = updaters

    def change_status(self, task: Task, status: str) -> Task:
        for updater in self.updaters:
            task = updater(task, status)
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
