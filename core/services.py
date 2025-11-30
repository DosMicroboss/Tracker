# core/services/services.py

from core.functional.either import Either


# ============================================================
#                 TaskService
# ============================================================

class TaskService:
    """
    TaskService — фасад над функциональными валидаторами.
    validators: [validator(Task) -> Either[error, Task]]
    """

    def __init__(self, validators: list):
        self.validators = validators

    def create_task(self, task) -> Either:
        """
        Прогоняет задачу через все валидаторы.
        Возвращает Either[error, Task]
        """
        result = None
        for validator in self.validators:
            result = validator(task)
            if result.is_left():
                return result
            task = result.get()  # подхватываем обновлённый Task (если валидатор что-то меняет)

        return result


# ============================================================
#                 StatusService
# ============================================================

class StatusService:
    """
    StatusService — фасад для смены статуса задачи.
    updaters: [update_fn(task, new_status) -> Task]
    """

    def __init__(self, updaters: list):
        self.updaters = updaters

    def change_status(self, task, new_status: str):
        """
        Последовательно применяет все update-функции.
        """
        updated = task
        for upd in self.updaters:
            updated = upd(updated, new_status)

        return updated


# ============================================================
#                 ReportService
# ============================================================

class ReportService:
    """
    ReportService — фасад для сборки отчётов.
    aggregators: [agg(project_id) -> dict]
    """

    def __init__(self, aggregators: list):
        self.aggregators = aggregators

    def project_report(self, project_id: str) -> dict:
        """
        Объединяет результаты всех агрегаторов в один dict.
        """
        report = {}

        for agg in self.aggregators:
            data = agg(project_id)
            if isinstance(data, dict):
                report.update(data)

        return report
