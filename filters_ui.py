import streamlit as st
import json
from pathlib import Path
from core.domain import Task
from core.filters import by_priority, by_assignee, by_date_range


def load_tasks():
    path = Path(__file__).parent.parent / "data" / "seed.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [Task(**t) for t in data["tasks"]]


def filters_ui():
    st.title("Task Filters")

    tasks = load_tasks()

    # --- фильтр по приоритету
    priority = st.selectbox("Filter by priority", ["all", "low", "medium", "high", "critical"])
    if priority != "all":
        tasks = list(filter(by_priority(priority), tasks))

    # --- фильтр по исполнителю
    assignee = st.text_input("Filter by assignee (user_id)")
    if assignee:
        tasks = list(filter(by_assignee(assignee), tasks))

    # --- фильтр по дате
    start = st.date_input("Start date")
    end = st.date_input("End date")
    if start and end:
        tasks = list(filter(by_date_range(str(start), str(end)), tasks))

    st.subheader("Filtered Tasks")
    for t in tasks:
        st.write(f"{t.id} | {t.title} | {t.status} | {t.priority} | {t.assignee}")


if __name__ == "__main__":
    filters_ui()
