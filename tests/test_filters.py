# test_frp.py
import pytest
from frp import EventBus, InProgressTasks, CriticalBugs, ActiveComments


# ----------------------------------------------------------
# 1. Тест EventBus
# ----------------------------------------------------------
def test_bus_publish_calls_subscribers():
    bus = EventBus()
    called = []

    def handler(event):
        called.append(event.name)

    bus.subscribe("TEST_EVENT", handler)
    bus.publish("TEST_EVENT", {"x": 123})

    assert called == ["TEST_EVENT"]


# ----------------------------------------------------------
# 2. Тест витрины InProgressTasks
# ----------------------------------------------------------
def test_in_progress_tasks_updates():
    bus = EventBus()
    store = InProgressTasks()

    bus.subscribe("STATUS_CHANGED", store.handle_status)

    task = {"id": 1, "status": "in_progress", "priority": "normal"}

    # должно появиться
    bus.publish("STATUS_CHANGED", task)
    assert 1 in store.tasks

    # перевод в done → исчезает
    task_done = {"id": 1, "status": "done", "priority": "normal"}
    bus.publish("STATUS_CHANGED", task_done)
    assert 1 not in store.tasks


# ----------------------------------------------------------
# 3. Тест витрины CriticalBugs
# ----------------------------------------------------------
def test_critical_bugs_updates():
    bus = EventBus()
    bugs = CriticalBugs()

    bus.subscribe("PRIORITY_CHANGED", bugs.handle_priority)

    task = {"id": 7, "priority": "critical", "status": "todo"}

    # появляется
    bus.publish("PRIORITY_CHANGED", task)
    assert 7 in bugs.bugs

    # падает в normal → пропадает
    task2 = {"id": 7, "priority": "normal", "status": "todo"}
    bus.publish("PRIORITY_CHANGED", task2)

    assert 7 not in bugs.bugs


# ----------------------------------------------------------
# 4. Тест витрины ActiveComments
# ----------------------------------------------------------
def test_active_comments_limit():
    bus = EventBus()
    comments = ActiveComments(limit=3)

    bus.subscribe("COMMENT_ADDED", comments.handle_comment)

    for i in range(5):
        bus.publish("COMMENT_ADDED", {"task_id": 1, "text": f"msg{i}", "author": "me"})

    # только последние 3
    assert len(comments.comments) == 3
    assert comments.comments[0]["text"] == "msg2"
    assert comments.comments[1]["text"] == "msg3"
    assert comments.comments[2]["text"] == "msg4"


# ----------------------------------------------------------
# 5. Интеграционный тест FRP (собираем вручную)
# ----------------------------------------------------------
def test_full_frp_flow():
    bus = EventBus()

    progress = InProgressTasks()
    bugs = CriticalBugs()
    comments = ActiveComments()

    # подписки
    bus.subscribe("STATUS_CHANGED", progress.handle_status)
    bus.subscribe("PRIORITY_CHANGED", bugs.handle_priority)
    bus.subscribe("COMMENT_ADDED", comments.handle_comment)

    # создаём задачу
    task = {"id": 10, "status": "todo", "priority": "normal"}

    # переводим в работу
    task["status"] = "in_progress"
    bus.publish("STATUS_CHANGED", task)
    assert 10 in progress.tasks

    # делаем критической
    task["priority"] = "critical"
    bus.publish("PRIORITY_CHANGED", task)
    assert 10 in bugs.bugs

    # добавляем комментарий
    bus.publish("COMMENT_ADDED", {"task_id": 10, "text": "Hello", "author": "A"})
    assert len(comments.comments) == 1
    assert comments.comments[0]["text"] == "Hello"
