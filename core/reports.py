from functools import lru_cache
from datetime import datetime, timedelta
from core.domain import Task

# --- Правила SLA (например, задачи, просроченные > 7 дней)
class Rule:
    def __init__(self, max_days: int = 7):
        self.max_days = max_days


@lru_cache(maxsize=None)
def overdue_tasks(tasks: tuple[Task, ...], rules: tuple[Rule, ...], index: int = 0) -> tuple[Task, ...]:
    """
    Рекурсивная функция с мемоизацией:
    Возвращает кортеж задач, которые просрочены по SLA.
    """
    # --- Базовый случай (конец рекурсии)
    if index >= len(tasks):
        return ()

    # --- Рекурсивный шаг
    t = tasks[index]
    rest = overdue_tasks(tasks, rules, index + 1)  # рекурсивный вызов

    # --- Проверка просрочки
    rule = rules[0] if rules else Rule()
    try:
        updated_date = datetime.strptime(t.updated, "%Y-%m-%d")
    except ValueError:
        return rest  # если формат даты неверный — пропустить

    if (datetime.now() - updated_date).days > rule.max_days and t.status != "done":
        return (t,) + rest  # добавить текущую задачу в результат
    else:
        return rest  # пропустить и вернуть оставшиеся
