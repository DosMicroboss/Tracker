import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path

import sys
sys.path.append('F:/adk/core')

from core.domain import Task
from core.filters import by_priority, by_assignee, by_date_range
from core.transforms import filter_by_status, add_task, remove_task
from core.reports import overdue_tasks, Rule



DATA_PATH = Path(__file__).parent.parent / "data" / "seed.json"

USERS = {
    "admin": {"role": "admin", "id": "u_admin"},
    "user1": {"role": "user", "id": "u_1"},
    "user2": {"role": "user", "id": "u_2"},
}

def login():
    st.sidebar.title("Вход")
    username = st.sidebar.selectbox("Выберите пользователя", list(USERS.keys()))
    if st.sidebar.button("Войти"):
        st.session_state["user"] = USERS[username]
        st.success(f"Вы вошли как {username}")

def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    tasks = [Task(**t) for t in data["tasks"]]
    return data, tasks


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def page_overview():
    data, tasks = load_data()
    projects = data["projects"]
    users = data["users"]

    st.title("Обзор")

    c1, c2, c3 = st.columns(3)
    c1.metric("Проекты", len(projects))
    c2.metric("Пользователи", len(users))
    c3.metric("Задачи", len(tasks))

    st.subheader("Задачи по статусам")
    status_counts = {
        s: len(filter_by_status(tuple(tasks), s))
        for s in ["todo", "in_progress", "review", "done"]
    }
    st.bar_chart(status_counts)


def page_filters():
    _, tasks = load_data()
    st.title("Фильтр задач")

    with st.expander("Настройки фильтра", expanded=True):
        c1, c2, c3 = st.columns(3)

        priority = c1.selectbox(
            "Приоритет", ["все", "низкий", "средний", "высокий", "критический"]
        )
        if priority != 'все':
            tasks = list(filter(by_priority(priority), tasks))

        assignee = c2.text_input("(user_id)")
        if assignee:
            tasks = list(filter(by_assignee(assignee), tasks))

        start = c3.date_input("Начало даты")
        end = c3.date_input("Конец даты")
        if start and end:
            tasks = list(filter(by_date_range(str(start), str(end)), tasks))

    st.subheader("Фильтрованные задачи")
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
        st.info("Нет задач, соответствующих фильтру")


def persist_and_reload(data, tasks_all):
    data["tasks"] = [t.__dict__ for t in tasks_all]
    save_data(data)
    return list(tasks_all)

def manage_tasks():
    data, tasks_all = load_data()
    st.title("Управление задачами")

    if "user" not in st.session_state:
        st.warning("⚠ Сначала войдите в систему.")
        return
    current_user = st.session_state["user"]

    if current_user["role"] != "admin":
        tasks_view = [t for t in tasks_all if t.assignee == current_user["id"]]
    else:
        tasks_view = list(tasks_all)

    st.subheader("Добавить или обновить задачу")
    with st.form("add_form"):
        title = st.text_input("Заголовок")
        desc = st.text_area("Описание")
        status = st.selectbox("Статус", ["todo", "in_progress", "review", "done"])
        priority = st.selectbox("Приоритет", ["низкий", "средний", "высокий", "критический"])

        if current_user["role"] == "admin":
            assignee = st.text_input("Исполнитель (user_id)")
        else:
            assignee = current_user["id"]
            st.text_input("Исполнитель (user_id)", value=assignee, disabled=True)

        submitted = st.form_submit_button("Сохранить")
        if submitted:
            now = datetime.now().strftime("%Y-%m-%d")
            existing = next((t for t in tasks_all if t.title == title), None)
            if existing:
                updated_task = Task(
                    id=existing.id,
                    project_id=existing.project_id,
                    title=title,
                    desc=desc,
                    status=status,
                    priority=priority,
                    assignee=assignee,
                    created=existing.created,
                    updated=now,
                )
                tasks_all = tuple(t if t.id != existing.id else updated_task for t in tasks_all)
                st.info(f"Задача '{title}' обновлена.")
            else:
                new_task = Task(
                    id=str(uuid.uuid4())[:8],
                    project_id="p1",
                    title=title,
                    desc=desc,
                    status=status,
                    priority=priority,
                    assignee=assignee,
                    created=now,
                    updated=now,
                )
                tasks_all = add_task(tuple(tasks_all), new_task)
                st.success(f"Задача '{title}' добавлена как {new_task.id}.")

            tasks_all = tuple(tasks_all)
            persist_and_reload(data, tasks_all)
            if current_user["role"] != "admin":
                tasks_view = [t for t in tasks_all if t.assignee == current_user["id"]]
            else:
                tasks_view = list(tasks_all)

    st.subheader("Удалить задачу")
    if tasks_view:
        remove_choice = st.selectbox("Выберите задачу для удаления", [f"{t.id} | {t.title}" for t in tasks_view])
        if st.button("Удалить"):
            remove_id = remove_choice.split(" | ")[0]
            tasks_all = remove_task(tuple(tasks_all), remove_id)
            persist_and_reload(data, tasks_all)
            st.warning(f"🗑 Задача {remove_id} удалена!")
            if current_user["role"] != "admin":
                tasks_view = [t for t in tasks_all if t.assignee == current_user["id"]]
            else:
                tasks_view = list(tasks_all)
    else:
        st.info("Нет задач для удаления")

    st.subheader("Текущие задачи")
    st.dataframe(
        [
            {"ID": t.id, "Title": t.title, "Status": t.status, "Priority": t.priority, "Assignee": t.assignee}
            for t in tasks_view
        ],
        use_container_width=True,
    )

def page_reports():
    data, tasks = load_data()
    st.title("Reports")
    st.subheader("Overdue tasks (cached)")


    rules = (Rule(7),)
    tasks_tuple = tuple(tasks)

    if st.button("Посчитать просроченные задачи"):
        import time
        start = time.perf_counter()
        result = overdue_tasks(tasks_tuple, rules)
        duration = time.perf_counter() - start

        st.write(f"Время выполнения: {duration:.6f} сек.")
        st.write(f"Найдено просроченных задач: {len(result)}")

        if result:
            st.dataframe(
                [
                    {
                        "ID": t.id,
                        "Title": t.title,
                        "Status": t.status,
                        "Priority": t.priority,
                        "Updated": t.updated,
                    }
                    for t in result
                ],
                use_container_width=True,
            )
        else:
            st.info("Нет просроченных задач")




def main():
    st.set_page_config(page_title="Трекер задач", page_icon="", layout="wide")

    st.set_page_config(page_title="Трекер задач", layout="wide")
    login()

    #css_path = Path(__file__).parent / "style.css"
    #if css_path.exists():
    #    with open(css_path, "r", encoding="utf-8") as f:
    #        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    #else:
    #    st.warning("style.css не найден — помести файл рядом с main.py")

    st.sidebar.title("Навигация")
    page = st.sidebar.radio("Перейти", ["Обзор", "Фильтры", "Управление задачами", "Отчеты"])

    if page == "Обзор":
        page_overview()
    elif page == "Фильтры":
        page_filters()
    elif page == "Управление задачами":
        manage_tasks()
    elif page == "Отчеты":
        from core.reports import overdue_tasks, Rule
        _, tasks = load_data()
        rules = (Rule(7),)
        result = overdue_tasks(tuple(tasks), rules)

        st.title("Overdue tasks (cached)")
        st.write(f"Просроченных задач: **{len(result)}**")
        st.dataframe(
         [
                {"ID": t.id, "Title": t.title, "Status": t.status, "Updated": t.updated}
                for t in result
            ]
     )


if __name__ == "__main__":
    main()
