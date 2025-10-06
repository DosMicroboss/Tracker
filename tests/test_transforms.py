import pytest
import sys
sys.path.append('F:/adk/core')
from core.domain import Task
from core.transforms import add_task, filter_by_status, avg_tasks_per_user


def test_add_task():
    tasks = ()
    t = Task("t1", "p1", "Title", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    print(t)
    print(f"[TEST] Тапсырма қосу: {t.id} - {t.title}")
    result = add_task(tasks, t)
    print(f"[RESULT] Қазіргі тапсырмалар: {[task.id for task in result]}")
    assert len(result) == 1
    assert result[0].id == "t1"


def test_filter_by_status():
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-01", "2025-09-01")
    tasks = (t1, t2)

    print(t1)
    print(t2)

    print(f"[TEST]'done' статусы бойынша тапсырмаларды сұрыптау")
    result = filter_by_status(tasks, "done")
    print(f"[RESULT] Табылды: {[task.id for task in result]}")
    assert len(result) == 1
    assert result[0].id == "t2"


def test_avg_tasks_per_user():
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-01", "2025-09-01")
    t3 = Task("t3", "p1", "Title3", "Desc", "done", "high", "u1", "2025-09-01", "2025-09-01")
    tasks = (t1, t2, t3)

    print(t1)
    print(t2)
    print(t3)

    print(f"[TEST] Қолданушыға орташа тапсырма саны")
    avg = avg_tasks_per_user(tasks)
    print(f"[RESULT] Орташа саны: {avg}")
    assert avg == pytest.approx(1.5)
