from typing import Callable, Dict, List

class Event:
    def __init__(self, name: str, payload: dict):
        self.name = name
        self.payload = payload



class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, name: str, handler: Callable[[Event], None]):
        self.subscribers.setdefault(name, []).append(handler)

    def publish(self, name: str, payload: dict):
        event = Event(name, payload)
        for handler in self.subscribers.get(name, []):
            handler(event)

class InProgressTasks:
    def __init__(self, bus: EventBus):
        self.tasks: Dict[int, dict] = {}
        bus.subscribe("TASK_CREATED", self.on_event)
        bus.subscribe("STATUS_CHANGED", self.on_event)

    def on_event(self, event: Event):
        task = event.payload
        tid = task["id"]

        if task["status"] == "IN_PROGRESS":
            self.tasks[tid] = task
        else:
            self.tasks.pop(tid, None)


class CriticalBugs:
    def __init__(self, bus: EventBus):
        self.bugs: Dict[int, dict] = {}
        bus.subscribe("TASK_CREATED", self.on_event)
        bus.subscribe("PRIORITY_CHANGED", self.on_event)

    def on_event(self, event: Event):
        task = event.payload
        tid = task["id"]

        is_critical_bug = (
            task.get("type") == "BUG"
            and task.get("priority") == "CRITICAL"
        )

        if is_critical_bug:
            self.bugs[tid] = task
        else:
            self.bugs.pop(tid, None)


class ActiveComments:
    def __init__(self, bus: EventBus, limit: int = 10):
        self.comments: List[dict] = []
        self.limit = limit

        bus.subscribe("COMMENT_ADDED", self.on_comment)

    def on_comment(self, event: Event):
        self.comments.append(event.payload)

        if len(self.comments) > self.limit:
            self.comments = self.comments[-self.limit:]