import streamlit as st
import json
import uuid
from datetime import datetime
from pathlib import Path
import random
import time
import sys
import asyncio

from core.async_ops import project_overview_async, bulk_update_status
from core.frp import EventBus, Event

sys.path.append('F:/adk/core')

from core.domain import Task
from core.filters import by_priority, by_assignee, by_date_range
from core.transforms import filter_by_status, add_task, remove_task
from core.reports import overdue_tasks, Rule

from core.functional.pipelines import create_pipeline, lazy_status_stream, compose, pipe

import streamlit as st
import uuid
from datetime import datetime
from core.domain import Task
from core.services import TaskService, StatusService, ReportService
from core.reports import (
    validate_task,
    overdue_tasks,
    report_count_by_status
)
from dataclasses import replace
from core.domain import with_status



DATA_PATH = Path(__file__).parent.parent / "data" / "seed.json"

USERS = {
    "admin": {"role": "admin", "id": "u_admin"},
    "user1": {"role": "user", "id": "u_1"},
    "user2": {"role": "user", "id": "u_2"},
}

def local_css(file_name: str):
    with open(file_name, "r", encoding="utf-8") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

    st.set_page_config(page_title="Трекер задач", page_icon="", layout="wide")

    # ЗАГРУЗКА CSS
    css_path = Path(__file__).parent / "styles.css"
    local_css(css_path)

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
        st.warning("Сначала войдите в систему.")
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
            st.warning(f"Задача {remove_id} удалена!")
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

def page_lazy_demo():
    st.title("Поток задач")
    data_file = "data/seed.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = tuple(
        Task(
            id=t["id"],
            project_id=t["project_id"],
            title=t["title"],
            desc=t.get("desc", ""),
            status=t.get("status", "todo"),
            priority=t.get("priority", "low"),
            assignee=t.get("assignee"),
            created=t.get("created", datetime.now().strftime("%Y-%m-%d")),
            updated=t.get("updated", datetime.now().strftime("%Y-%m-%d")),
        )
        for t in data.get("tasks", [])
    )

    st.subheader(f"Загружено задач: {len(tasks)}")

    st.divider()

    st.subheader("Онлайн-обновление статистики статусов")

    output_area = st.empty()
    stream = lazy_status_stream(tasks)
    stats = {}

    for status, count in stream:
        stats[status] = count
        output_area.write(
            "\n".join([f"**{s}** — {c}" for s, c in stats.items()])
        )
        time.sleep(1.0)

    st.success("Поток завершён!")

def page_frp():

    from core.frp import (
        EventBus,
        InProgressTasks,
        CriticalBugs,
        ActiveComments,
    )

    st.title("Async / FRP — EventBus Demo")

    if "bus" not in st.session_state:
        st.session_state.bus = EventBus()
        st.session_state.in_progress = InProgressTasks(st.session_state.bus)
        st.session_state.critical = CriticalBugs(st.session_state.bus)
        st.session_state.comments = ActiveComments(st.session_state.bus)

        st.session_state.event_log = []

    bus = st.session_state.bus

    st.subheader("Генерация событий")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Создать задачу"):
            task = {
                "id": random.randint(1000, 9999),
                "title": "Новая задача",
                "status": "IN_PROGRESS",
                "priority": "LOW",
                "type": "TASK",
                "created": time.time(),
            }
            bus.publish("TASK_CREATED", task)
            st.session_state.event_log.append(("TASK_CREATED", task))


    with col2:
        if st.button("Изменить статус задачи"):
            if st.session_state.in_progress.tasks:
                t = next(iter(st.session_state.in_progress.tasks.values()))
                t["status"] = "DONE"
                bus.publish("STATUS_CHANGED", t)
                st.session_state.event_log.append(("STATUS_CHANGED", t))
            else:
                st.warning("Нет задач в работе")

    with col3:
        if st.button("Создать критический баг"):
            bug = {
                "id": random.randint(5000, 9000),
                "title": "Падение приложения",
                "status": "IN_PROGRESS",
                "priority": "CRITICAL",
                "type": "BUG",
            }
            bus.publish("PRIORITY_CHANGED", bug)
            st.session_state.event_log.append(("PRIORITY_CHANGED", bug))

    with col4:
        if st.button("Добавить комментарий"):
            c = {"text": f"Комментарий {len(st.session_state.comments.comments) + 1}"}
            bus.publish("COMMENT_ADDED", c)
            st.session_state.event_log.append(("COMMENT_ADDED", c))

    st.divider()

    st.subheader("Витрины (Reactive Views)")

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### Задачи в работе")
        st.write(st.session_state.in_progress.tasks)

        st.markdown("### Критические баги")
        st.write(st.session_state.critical.bugs)

    with colB:
        st.markdown("### Последние комментарии")
        st.write(st.session_state.comments.comments)

        st.markdown("### Лог событий")
        st.write(st.session_state.event_log)

def page_functional_core():
    st.title("Управление задачами")

    # --------------------------
    # Загружаем данные
    # --------------------------
    data, tasks_all = load_data()

    if "rules" not in st.session_state:
        st.session_state.rules = (Rule(max_days=1),)


    if "user" not in st.session_state:
        st.warning("Сначала войдите в систему.")
        return
    current_user = st.session_state["user"]

    if current_user["role"] != "admin":
        tasks_view = [t for t in tasks_all if t.assignee == current_user["id"]]
    else:
        tasks_view = list(tasks_all)



    if "task_service" not in st.session_state:
        st.session_state.task_service = TaskService(
            validators=[validate_task],
            rules=st.session_state.rules
        )

    if "status_service" not in st.session_state:
        st.session_state.status_service = StatusService(
            updaters=[with_status]
        )

    if "report_service" not in st.session_state:
        st.session_state.report_service = ReportService(
            aggregators=[
                lambda pid: {"count_by_status":
                             report_count_by_status(tasks_all)},
                lambda pid: {"overdue":
                                 [t.id for t in overdue_tasks(tasks_all,[tuple(r) if isinstance(r, list) else r for r in st.session_state.rules])]}
            ]
        )

    ts: TaskService = st.session_state.task_service
    ss: StatusService = st.session_state.status_service
    rs: ReportService = st.session_state.report_service

    # -------------------------------------
    # 1. Создание задачи
    # -------------------------------------
    st.subheader("Создать задачу")

    title = st.text_input("Заголовок")
    desc = st.text_area("Описание")
    status = st.selectbox("Статус", ["todo", "in_progress", "review", "done"])
    priority = st.selectbox("Приоритет", ["низкий", "средний", "высокий", "критический"])

    # вот здесь вставляем проверку роли
    if current_user["role"] == "admin":
        assignee = st.text_input("Исполнитель (user_id)")
    else:
        assignee = current_user["id"]
        st.text_input("Исполнитель (user_id)", value=assignee, disabled=True)

    if st.button("Создать задачу"):
        now = datetime.now().strftime("%Y-%m-%d")

        task = Task(
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

        result = ts.create_task(task)

        if result.is_left:
            st.error(result.value)
        else:
            tasks_all = tuple([*tasks_all, result.value])
            persist_and_reload(data, tasks_all)
            st.success(f"Задача создана: {result.value.id}")

    st.subheader("Изменить статус")

    if tasks_all:
        tid = st.selectbox("Выберите задачу", [t.id for t in tasks_all])
        new_status = st.selectbox("Новый статус",
                                  ["todo", "in_progress", "review", "done"])

        if st.button("Обновить статус"):
            task = next(t for t in tasks_all if t.id == tid)
            updated = ss.change_status(task, new_status)

            updated = replace(updated, updated=datetime.now().strftime("%Y-%m-%d"))

            tasks_all = tuple(t if t.id != tid else updated for t in tasks_all)
            persist_and_reload(data, tasks_all)

            st.success(f"Статус обновлён: {tid} → {new_status}")

            tasks_all = tuple(t if t.id != tid else updated for t in tasks_all)
            persist_and_reload(data, tasks_all)

            st.success(f"Статус обновлён: {tid} → {new_status}")
    st.subheader("Отчёт по проекту")

    pid = st.text_input("Project ID", "p1")
    if st.button("Сформировать отчёт"):
        report = rs.project_report(pid)
        st.json(report)

    st.subheader("Удалить задачу")
    if tasks_view:
        remove_choice = st.selectbox("Выберите задачу для удаления", [f"{t.id} | {t.title}" for t in tasks_view])
        if st.button("Удалить"):
            remove_id = remove_choice.split(" | ")[0]
            tasks_all = remove_task(tuple(tasks_all), remove_id)
            persist_and_reload(data, tasks_all)
            st.warning(f"Задача {remove_id} удалена!")
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

def page_async_demo():
    st.markdown("""
        <style>
            .card {
                padding: 20px;
                border-radius: 14px;
                border: 1px solid rgba(180,180,180,0.35);
                margin: 15px 0;
                background: rgba(250,250,250,0.85);
            }
            .card h3 {
                margin-top: 0;
                font-size: 1.4rem;
            }
            .metric-block {
                display: flex;
                gap: 25px;
                margin-bottom: 15px;
            }
            .metric {
                background: #f1f3f5;
                padding: 14px 18px;
                border-radius: 10px;
                font-size: 1rem;
                text-align: center;
                min-width: 130px;
                border: 1px solid #e0e0e0;
            }
            .metric span {
                display: block;
                font-size: 1.3rem;
                font-weight: bold;
                margin-top: 4px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Async Operations Demo")
    st.caption("Асинхронные операции: массовые обновления и быстрый анализ данных")

    data, tasks = load_data()
    users = data.get("users", USERS)

    st.markdown('<div class="metric-block">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">Задач<span>{len(tasks)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">Пользователей<span>{len(users)}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric">Проектов<span>{len({t.project_id for t in tasks})}</span></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("Массовое обновление статуса")

    status_options = ["todo", "in_progress", "review", "done"]
    new_status = st.selectbox("Выберите новый статус:", status_options)

    if st.button("Обновить все задачи"):
        with st.spinner("Обновление выполняется..."):
            async def do_bulk_update():
                updated = await bulk_update_status(list(tasks), new_status)

                data["tasks"] = [t.__dict__ for t in updated]
                save_data(data)

                st.success(f"Готово! Обновлено {len(updated)} задач")
                st.dataframe(
                    [{"ID": t.id, "Title": t.title, "Status": t.status} for t in updated],
                    use_container_width=True
                )
            asyncio.run(do_bulk_update())
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("Асинхронный отчёт по проекту")

    if st.button("Показать статистику"):
        with st.spinner("Считаем..."):
            async def do_overview():
                overview = await project_overview_async(list(tasks), users)
                st.json(overview)
                st.markdown("Статусы")
                cols = st.columns(len(overview["by_status"]))
                for (status, count), col in zip(overview["by_status"].items(), cols):
                    col.metric(status, count)
                st.markdown("Исполнители")
                st.dataframe(
                    [{"Assignee": name, "Tasks": cnt} for name, cnt in overview["by_assignee"].items()],
                    use_container_width=True
                )
            asyncio.run(do_overview())

    st.markdown("</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Трекер задач", page_icon="", layout="wide")

    st.set_page_config(page_title="Трекер задач", layout="wide")
    login()

    st.sidebar.title("Навигация")
    page = st.sidebar.radio("Перейти", ["Обзор", "Фильтры", "Управление задачами", "Отчеты", "Pypeline", "FRP", "Async"])
    if page == "Обзор":
        page_overview()
    elif page == "Фильтры":
        page_filters()
    elif page == "Управление задачами":
        page_functional_core()
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
    elif page == "Pypeline":
        page_lazy_demo()
    elif page == "FRP":
        page_frp()
    elif page == "Async":
        page_async_demo()

if __name__ == "__main__":
    main()
