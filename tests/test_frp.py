from typing import Dict, List
from unittest.mock import Mock

# Импортируем классы из вашего кода
from core.frp import Event, EventBus, InProgressTasks, CriticalBugs, ActiveComments


class TestEvent:
    def test_event_creation(self):
        payload = {"id": 1, "name": "test"}
        event = Event("TEST_EVENT", payload)

        assert event.name == "TEST_EVENT"
        assert event.payload == payload


class TestEventBus:
    def test_subscribe_and_publish(self):
        bus = EventBus()
        mock_handler = Mock()

        bus.subscribe("TEST_EVENT", mock_handler)

        payload = {"data": "test"}
        bus.publish("TEST_EVENT", payload)

        mock_handler.assert_called_once()
        event_arg = mock_handler.call_args[0][0]
        assert isinstance(event_arg, Event)
        assert event_arg.name == "TEST_EVENT"
        assert event_arg.payload == payload

    def test_multiple_subscribers(self):
        bus = EventBus()
        mock_handler1 = Mock()
        mock_handler2 = Mock()

        bus.subscribe("TEST_EVENT", mock_handler1)
        bus.subscribe("TEST_EVENT", mock_handler2)

        payload = {"data": "test"}
        bus.publish("TEST_EVENT", payload)

        mock_handler1.assert_called_once()
        mock_handler2.assert_called_once()

    def test_no_subscribers(self):
        bus = EventBus()

        bus.publish("NON_EXISTENT_EVENT", {"data": "test"})

    def test_multiple_events(self):
        bus = EventBus()
        mock_handler1 = Mock()
        mock_handler2 = Mock()

        bus.subscribe("EVENT_TYPE_1", mock_handler1)
        bus.subscribe("EVENT_TYPE_2", mock_handler2)

        bus.publish("EVENT_TYPE_1", {"data": "1"})
        bus.publish("EVENT_TYPE_2", {"data": "2"})

        mock_handler1.assert_called_once()
        mock_handler2.assert_called_once()


class TestInProgressTasks:
    def test_task_created_in_progress(self):
        bus = EventBus()
        tracker = InProgressTasks(bus)

        task = {"id": 1, "status": "IN_PROGRESS", "type": "TASK"}
        bus.publish("TASK_CREATED", task)

        assert 1 in tracker.tasks
        assert tracker.tasks[1] == task

    def test_task_status_changed_to_in_progress(self):
        bus = EventBus()
        tracker = InProgressTasks(bus)

        task = {"id": 1, "status": "TODO", "type": "TASK"}
        bus.publish("TASK_CREATED", task)
        assert 1 not in tracker.tasks

        task["status"] = "IN_PROGRESS"
        bus.publish("STATUS_CHANGED", task)

        assert 1 in tracker.tasks
        assert tracker.tasks[1]["status"] == "IN_PROGRESS"

    def test_task_status_changed_from_in_progress(self):
        bus = EventBus()
        tracker = InProgressTasks(bus)

        task = {"id": 1, "status": "IN_PROGRESS", "type": "TASK"}
        bus.publish("TASK_CREATED", task)
        assert 1 in tracker.tasks

        task["status"] = "DONE"
        bus.publish("STATUS_CHANGED", task)

        assert 1 not in tracker.tasks

    def test_multiple_tasks(self):
        bus = EventBus()
        tracker = InProgressTasks(bus)

        task1 = {"id": 1, "status": "IN_PROGRESS", "type": "TASK"}
        task2 = {"id": 2, "status": "TODO", "type": "TASK"}
        task3 = {"id": 3, "status": "IN_PROGRESS", "type": "TASK"}

        bus.publish("TASK_CREATED", task1)
        bus.publish("TASK_CREATED", task2)
        bus.publish("TASK_CREATED", task3)

        assert 1 in tracker.tasks
        assert 2 not in tracker.tasks
        assert 3 in tracker.tasks
        assert len(tracker.tasks) == 2


class TestCriticalBugs:
    def test_critical_bug_created(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        bug = {"id": 1, "type": "BUG", "priority": "CRITICAL", "status": "TODO"}
        bus.publish("TASK_CREATED", bug)

        assert 1 in tracker.bugs
        assert tracker.bugs[1] == bug

    def test_non_critical_bug_not_tracked(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        bug = {"id": 1, "type": "BUG", "priority": "LOW", "status": "TODO"}
        bus.publish("TASK_CREATED", bug)

        assert 1 not in tracker.bugs

    def test_non_bug_not_tracked(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        task = {"id": 1, "type": "TASK", "priority": "CRITICAL", "status": "TODO"}
        bus.publish("TASK_CREATED", task)

        assert 1 not in tracker.bugs

    def test_priority_changed_to_critical(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        bug = {"id": 1, "type": "BUG", "priority": "LOW", "status": "TODO"}
        bus.publish("TASK_CREATED", bug)
        assert 1 not in tracker.bugs

        bug["priority"] = "CRITICAL"
        bus.publish("PRIORITY_CHANGED", bug)

        assert 1 in tracker.bugs

    def test_priority_changed_from_critical(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        bug = {"id": 1, "type": "BUG", "priority": "CRITICAL", "status": "TODO"}
        bus.publish("TASK_CREATED", bug)
        assert 1 in tracker.bugs

        bug["priority"] = "LOW"
        bus.publish("PRIORITY_CHANGED", bug)

        assert 1 not in tracker.bugs

    def test_type_changed_from_bug(self):
        bus = EventBus()
        tracker = CriticalBugs(bus)

        task = {"id": 1, "type": "BUG", "priority": "CRITICAL", "status": "TODO"}
        bus.publish("TASK_CREATED", task)
        assert 1 in tracker.bugs

        task["type"] = "TASK"
        bus.publish("PRIORITY_CHANGED", task)

        assert 1 not in tracker.bugs


class TestActiveComments:
    def test_comment_added(self):
        bus = EventBus()
        tracker = ActiveComments(bus)

        comment = {"id": 1, "text": "Test comment", "author": "user1"}
        bus.publish("COMMENT_ADDED", comment)

        assert len(tracker.comments) == 1
        assert tracker.comments[0] == comment

    def test_multiple_comments(self):
        bus = EventBus()
        tracker = ActiveComments(bus)

        comments = [
            {"id": 1, "text": "Comment 1", "author": "user1"},
            {"id": 2, "text": "Comment 2", "author": "user2"},
            {"id": 3, "text": "Comment 3", "author": "user3"},
        ]

        for comment in comments:
            bus.publish("COMMENT_ADDED", comment)

        assert len(tracker.comments) == 3
        assert tracker.comments == comments

    def test_limit_comments(self):
        bus = EventBus()
        tracker = ActiveComments(bus, limit=3)

        for i in range(5):
            comment = {"id": i, "text": f"Comment {i}", "author": f"user{i}"}
            bus.publish("COMMENT_ADDED", comment)

        assert len(tracker.comments) == 3
        assert tracker.comments[0]["id"] == 2
        assert tracker.comments[1]["id"] == 3
        assert tracker.comments[2]["id"] == 4

    def test_default_limit(self):
        bus = EventBus()
        tracker = ActiveComments(bus)

        for i in range(15):
            comment = {"id": i, "text": f"Comment {i}"}
            bus.publish("COMMENT_ADDED", comment)

        assert len(tracker.comments) == 10
        assert tracker.comments[0]["id"] == 5  # id=5
        assert tracker.comments[-1]["id"] == 14  # id=14


class TestIntegration:
    def test_multiple_subscribers_same_event(self):
        bus = EventBus()

        progress_tracker = InProgressTasks(bus)
        bug_tracker = CriticalBugs(bus)

        task = {
            "id": 1,
            "type": "BUG",
            "priority": "CRITICAL",
            "status": "IN_PROGRESS"
        }

        bus.publish("TASK_CREATED", task)

        assert 1 in progress_tracker.tasks
        assert 1 in bug_tracker.bugs

    def test_event_chain(self):
        bus = EventBus()
        progress_tracker = InProgressTasks(bus)

        task = {"id": 1, "status": "TODO", "type": "TASK"}
        bus.publish("TASK_CREATED", task)
        assert 1 not in progress_tracker.tasks

        task["status"] = "IN_PROGRESS"
        bus.publish("STATUS_CHANGED", task)
        assert 1 in progress_tracker.tasks

        task["status"] = "DONE"
        bus.publish("STATUS_CHANGED", task)
        assert 1 not in progress_tracker.tasks