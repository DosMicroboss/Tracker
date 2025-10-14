import pytest
from datetime import datetime, timedelta
from core.domain import Task
from core.reports import overdue_tasks, Rule

def test_overdue_tasks_recursion():
    today = datetime.now()
    old_date = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    new_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")

    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", old_date, old_date)

    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", new_date, new_date)
    t3 = Task("t3", "p1", "Title3", "Desc", "in_progress", "medium", "u3", old_date, old_date)
    tasks = (t1, t2, t3)
    rules = (Rule(7),)

    print(t1)
    print(t2)
    print(t3)

    result = overdue_tasks(tasks, rules)
    assert len(result) == 2

    print(result)

    assert all(isinstance(t, Task) for t in result)
