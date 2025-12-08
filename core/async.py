import asyncio
from datetime import datetime
import json
from pathlib import Path

# --- core modules ---
from core.domain import Task, User, Rule
from core.filters import filter_by_status, by_priority, by_assignee
from core.reports import overdue_tasks, report_count_by_status
from core.async_ops import bulk_update_status, project_overview_async
from core.frp import EventBus, Event

# ---------- LOAD DATA ----------
DATA_PATH = Path(__file__).parent.parent / "data" / "seed.json"

def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    tasks = tuple(Task(**t) for t in data.get("tasks", []))
    users = [User(**u) for u in data.get("users", [])]
    return tasks, users

# ---------- PIPELINE ----------
def run_pipeline():
    tasks, users = load_data()

    print("=== Total tasks loaded:", len(tasks))

    # --- 1. FILTERS ---
    filtered = tuple(filter(filter_by_status("open"), tasks))
    filtered = tuple(filter(by_priority("high"), filtered))
    filtered = tuple(filter(by_assignee("user_1"), filtered))  # пример user_id

    print("=== Tasks after filters:", len(filtered))

    # --- 2. LAZY GENERATOR: overdue tasks ---
    def overdue_gen(tasks):
        for t in tasks:
            try:
                updated = datetime.strptime(t.updated, "%Y-%m-%d")
            except Exception:
                continue
            if (datetime.now() - updated).days > 0 and t.status != "done":
                yield t

    gen = overdue_gen(filtered)

    # --- 3. EVENT STREAM ---
    bus = EventBus()

    def on_overdue(event: Event):
        print(f"EVENT: {event.name} for task {event.payload['id']}")

    bus.subscribe("TASK_OVERDUE", on_overdue)

    for t in gen:
        bus.publish("TASK_OVERDUE", t.__dict__)

    # --- 4. SYNCHRONOUS REPORT ---
    rules = (Rule(),)
    overdue = overdue_tasks(filtered, rules)
    print("=== Overdue tasks count:", len(overdue))
    print("=== Report by status:", report_count_by_status(filtered))

    # --- 5. ASYNC REPORT ---
    async def async_report():
        overview = await project_overview_async(list(filtered), users)
        print("=== Project Overview (Async):", overview)

    asyncio.run(async_report())

# ---------- MAIN ----------
if __name__ == "__main__":
    run_pipeline()
