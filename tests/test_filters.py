from core.domain import Task, Comment
from core.filters import by_priority, by_assignee, by_date_range, walk_comments, traverse_tasks


def test_by_priority():
    print("\nТест: фильтр по приоритету")
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-01", "2025-09-01")
    res = list(filter(by_priority("low"), [t1, t2]))
    print("Ожидаем [t1], получили:", res)
    assert res == [t1]


def test_by_assignee():
    print("\n Тест: фильтр по исполнителю")
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-01", "2025-09-01")
    res = list(filter(by_assignee("u2"), [t1, t2]))
    print("Ожидаем [t2], получили:", res)
    assert res == [t2]


def test_by_date_range():
    print("Тест: фильтр по дате")
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-05", "2025-09-06")
    res = list(filter(by_date_range("2025-09-01", "2025-09-03"), [t1, t2]))
    print("Ожидаем [t1], получили:", res)
    assert res == [t1]


def test_walk_comments():
    print("\nТест: фильтр комментариев по задаче ")
    c1 = Comment("c1", "t1", "u1", "Hello", "2025-09-01")
    c2 = Comment("c2", "t2", "u2", "World", "2025-09-01")
    c3 = Comment("c3", "t1", "u3", "Again", "2025-09-02")
    comments = (c1, c2, c3)
    res = walk_comments(comments, "t1")
    print("Ожидаем (c1, c3), получили:", res)
    assert res == (c1, c3)


def test_traverse_tasks():
    print("Тест: обход задач по статусу")
    t1 = Task("t1", "p1", "Title1", "Desc", "todo", "low", "u1", "2025-09-01", "2025-09-01")
    t2 = Task("t2", "p1", "Title2", "Desc", "done", "high", "u2", "2025-09-01", "2025-09-01")
    t3 = Task("t3", "p1", "Title3", "Desc", "in_progress", "medium", "u1", "2025-09-02", "2025-09-02")
    status_order = ("todo", "in_progress", "done")
    res = traverse_tasks((t1, t2, t3), status_order)
    print("Ожидаем ('t1','t3','t2'), получили:", res)
    assert res == ("t1", "t3", "t2")