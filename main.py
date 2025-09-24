import streamlit as st
import json
from pathlib import Path
from core.domain import Task
from core.filters import by_priority, by_assignee, by_date_range
from core.transforms import filter_by_status

def load_data():
    path = Path(__file__).parent.parent / "data" / "seed.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    tasks = [Task(**t) for t in data["tasks"]]
    return data, tasks

def page_overview():
    data, tasks = load_data()
    projects = data["projects"]
    users = data["users"]

    st.title("📊 Overview")

    c1, c2, c3 = st.columns(3)
    c1.metric("Projects", len(projects))
    c2.metric("Users", len(users))
    c3.metric("Tasks", len(tasks))

    st.subheader("📌 Tasks by Status")
    status_counts = {
        s: len(filter_by_status(tuple(tasks), s))
        for s in ["todo", "in_progress", "review", "done"]
    }
    st.bar_chart(status_counts)

def page_filters():
    _, tasks = load_data()
    st.title("🔎 Task Filters")

    with st.expander("Filter options", expanded=True):
        c1, c2, c3 = st.columns(3)


        priority = c1.selectbox(
            "Priority", ["all", "low", "medium", "high", "critical"]
        )
        if priority != "all":
            tasks = list(filter(by_priority(priority), tasks))

        # Assignee filter
        assignee = c2.text_input("Assignee (user_id)")
        if assignee:
            tasks = list(filter(by_assignee(assignee), tasks))

        # Date filter
        start = c3.date_input("Start date")
        end = c3.date_input("End date")
        if start and end:
            tasks = list(filter(by_date_range(str(start), str(end)), tasks))

    st.subheader("📋 Filtered Tasks")
    if tasks:
        st.dataframe(
            [
                {
                    "ID": t.id,
                    "Title": t.title,
                    "Status": t.status,
                    "Priority": t.priority,
                    "Assignee": t.assignee,
                    "Created": t.created,
                }
                for t in tasks
            ],
            use_container_width=True,
        )
    else:
        st.info("No tasks match the filter ❌")


def main():
    st.set_page_config(page_title="Task Tracker", page_icon="✅", layout="wide")

    st.sidebar.title("📂 Navigation")
    page = st.sidebar.radio("Go to", ["Overview", "Filters"])

    if page == "Overview":
        page_overview()
    elif page == "Filters":
        page_filters()


if __name__ == "__main__":
    main()
