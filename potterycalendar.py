# Pottery Calendar App — Streamlit Prototype
# Reuses layout ideas from the Pottery Cost Analysis app
# Run with: streamlit run pottery_calendar_app.py

import uuid
from datetime import datetime, date, time, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
import pandas as pd
import streamlit as st

APP_TITLE = "Pottery Calendar App"
DATA_PATH = "events.csv"

CATEGORY_OPTIONS = ["Studio", "Community", "Public"]
TASK_OPTIONS = [
    "Throwing", "Trimming", "Glazing", "Bisque Firing", "Glaze Firing",
    "Inventory", "Delivery", "Workshop", "Show", "Open Studio",
    "Drop Release", "Meeting", "Other"
]
RECURRENCE_MAP = {
    "None": None,
    "Daily": DAILY,
    "Weekly": WEEKLY,
    "Monthly": MONTHLY,
    "Yearly": YEARLY,
}
CATEGORY_COLORS = {
    "Studio": "#3B82F6",
    "Community": "#10B981",
    "Public": "#EF4444",
}

# ---------- Utilities ----------

def _now_tzless():
    return datetime.now().replace(tzinfo=None, microsecond=0)

@st.cache_data
def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["start", "end"], keep_default_na=False)
        # Ensure types
        if "all_day" in df:
            df["all_day"] = df["all_day"].astype(bool)
        return df
    except FileNotFoundError:
        cols = [
            "id", "title", "category", "task_type", "start", "end",
            "all_day", "location", "notes", "created_at", "updated_at"
        ]
        return pd.DataFrame(columns=cols)

def save_data(df: pd.DataFrame, path: str = DATA_PATH):
    df.to_csv(path, index=False)
    load_data.clear()

def generate_id():
    return str(uuid.uuid4())

# Expand recurrence into concrete instances

def expand_recurrence(base_event: dict, freq_name: str, count: int | None, until: date | None):
    rule = RECURRENCE_MAP.get(freq_name)
    if rule is None:
        return [base_event]

    start_dt = base_event["start"]
    end_dt = base_event["end"]

    kwargs = {}
    if count and count > 0:
        kwargs["count"] = count
    if until:
        # Make until inclusive for all day events
        until_dt = datetime.combine(until, time(23, 59, 59))
        kwargs["until"] = until_dt

    instances = []
    for i, dt in enumerate(rrule(rule, dtstart=start_dt, **kwargs)):
        delta = end_dt - start_dt
        inst = base_event.copy()
        inst["id"] = generate_id()
        inst["start"] = dt
        inst["end"] = dt + delta
        inst["title"] = base_event["title"] if i == 0 else f"{base_event['title']} ({i+1})"
        instances.append(inst)
    return instances

# ---------- UI Helpers ----------

def badge(text: str, color: str):
    st.markdown(
        f"""
        <span style='display:inline-block;padding:2px 8px;border-radius:999px;background:{color};color:white;font-size:12px;'>
            {text}
        </span>
        """,
        unsafe_allow_html=True,
    )

def section_header(title: str):
    st.markdown(
        f"""
        <div style='display:flex;align-items:center;gap:10px;margin:8px 0 2px 0;'>
            <h3 style='margin:0'>{title}</h3>
        </div>
        <hr style='margin-top:6px;margin-bottom:12px'/>
        """,
        unsafe_allow_html=True,
    )

# ---------- App ----------

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

with st.sidebar:
    st.subheader("Quick Filters")
    selected_month = st.date_input("Month", value=date.today().replace(day=1))
    cat_filter = st.multiselect("Categories", CATEGORY_OPTIONS, default=CATEGORY_OPTIONS)
    task_filter = st.multiselect("Task Type", TASK_OPTIONS)
    show_past = st.toggle("Show past events", value=True)
    st.caption("Data saved to events.csv in the app folder")

# Load data
if "df" not in st.session_state:
    st.session_state.df = load_data()

# Tabs
tab_add, tab_studio, tab_comm, tab_public, tab_all = st.tabs([
    "Add Event", "Studio", "Community", "Public", "All Events",
])

# ---------- Add Event ----------
with tab_add:
    section_header("Create an event")
    with st.form("add_event_form", clear_on_submit=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            title = st.text_input("Title", placeholder="Example: Glaze firing Cone 6")
            category = st.selectbox("Category", CATEGORY_OPTIONS)
            task_type = st.selectbox("Task Type", TASK_OPTIONS)
            location = st.text_input("Location", placeholder="Studio, Gallery, Fairgrounds")
        with c2:
            all_day = st.checkbox("All day event", value=False)
            start_date = st.date_input("Start date", value=date.today())
            if all_day:
                start_time = time(9, 0)
                end_date = st.date_input("End date", value=start_date)
                end_time = time(17, 0)
            else:
                start_time = st.time_input("Start time", value=time(9, 0))
                end_date = st.date_input("End date", value=start_date)
                end_time = st.time_input("End time", value=time(12, 0))

        # Recurrence
        st.markdown("**Recurrence**")
        r1, r2, r3 = st.columns(3)
        with r1:
            recur = st.selectbox("Repeats", list(RECURRENCE_MAP.keys()))
        with r2:
            recur_count = st.number_input("Repeat count", min_value=0, value=0, help="Leave 0 if using Until")
        with r3:
            recur_until = st.date_input("Repeat until", value=None)

        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Add to calendar")
        if submitted:
            if not title.strip():
                st.error("Title is required")
            else:
                start_dt = datetime.combine(start_date, start_time)
                if all_day:
                    # Make end exclusive next day 1 minute before midnight for clarity
                    end_dt = datetime.combine(end_date, time(23, 59))
                else:
                    end_dt = datetime.combine(end_date, end_time)

                base = {
                    "id": generate_id(),
                    "title": title.strip(),
                    "category": category,
                    "task_type": task_type,
                    "start": start_dt,
                    "end": end_dt,
                    "all_day": bool(all_day),
                    "location": location.strip(),
                    "notes": notes.strip(),
                    "created_at": _now_tzless(),
                    "updated_at": _now_tzless(),
                }
                instances = expand_recurrence(base, recur, int(recur_count) if recur_count else None, recur_until)
                df = st.session_state.df
                st.session_state.df = pd.concat([df, pd.DataFrame(instances)], ignore_index=True)
                save_data(st.session_state.df)
                st.success(f"Added {len(instances)} event(s)")

# ---------- Common views ----------

def filter_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    # Time window for selected month
    start_month = datetime.combine(selected_month.replace(day=1), time(0, 0))
    if selected_month.month == 12:
        next_month = date(selected_month.year + 1, 1, 1)
    else:
        next_month = date(selected_month.year, selected_month.month + 1, 1)
    end_month = datetime.combine(next_month, time(0, 0))

    df = df[(df["start"] < end_month) & (df["end"] >= start_month)]
    if not show_past:
        df = df[df["end"] >= _now_tzless()]
    if cat_filter:
        df = df[df["category"].isin(cat_filter)]
    if task_filter:
        df = df[df["task_type"].isin(task_filter)]
    return df.sort_values("start")


def render_agenda(df: pd.DataFrame):
    if df.empty:
        st.info("No events to show")
        return
    # Group by day
    df = df.copy()
    df["day"] = df["start"].dt.date

    for the_day, group in df.groupby("day"):
        st.markdown(f"### {the_day.isoformat()}")
        for _, row in group.sort_values("start").iterrows():
            color = CATEGORY_COLORS.get(row["category"], "#6B7280")
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{row['title']}**")
                    when = "All day" if row["all_day"] else f"{row['start'].strftime('%I:%M %p')} to {row['end'].strftime('%I:%M %p')}"
                    st.caption(f"{row['category']} • {row['task_type']} • {when}")
                    if row.get("location"):
                        st.caption(f"Location {row['location']}")
                    if row.get("notes"):
                        st.write(row["notes"]) 
                with c2:
                    badge(row["category"], color)


def render_editor(df: pd.DataFrame, category: str | None = None):
    view = df.copy()
    if category:
        view = view[view["category"] == category]
    view = filter_df(view)

    section_header("Agenda")
    render_agenda(view)

    section_header("Table view edit and export")
    edit_df = view.copy()
    # Ensure string columns for editor
    edit_df["start"] = edit_df["start"].dt.strftime("%Y-%m-%d %H:%M")
    edit_df["end"] = edit_df["end"].dt.strftime("%Y-%m-%d %H:%M")

    edited = st.data_editor(
        edit_df,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{category or 'all'}",
    )

    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("Save changes"):
            # Write edits back into session df by matching on id
            base = st.session_state.df.copy()
            # Parse times back
            for _, row in edited.iterrows():
                idx = base.index[base["id"] == row["id"]]
                if len(idx) == 0:
                    # New row added
                    try:
                        new_row = row.to_dict()
                        new_row["start"] = datetime.strptime(new_row["start"], "%Y-%m-%d %H:%M")
                        new_row["end"] = datetime.strptime(new_row["end"], "%Y-%m-%d %H:%M")
                        new_row["all_day"] = bool(new_row.get("all_day", False))
                        new_row["created_at"] = _now_tzless()
                        new_row["updated_at"] = _now_tzless()
                        if not new_row.get("id"):
                            new_row["id"] = generate_id()
                        base = pd.concat([base, pd.DataFrame([new_row])], ignore_index=True)
                    except Exception as e:
                        st.error(f"Could not add row {e}")
                else:
                    i = idx[0]
                    try:
                        base.loc[i, "title"] = row["title"]
                        base.loc[i, "category"] = row["category"]
                        base.loc[i, "task_type"] = row["task_type"]
                        base.loc[i, "start"] = datetime.strptime(row["start"], "%Y-%m-%d %H:%M")
                        base.loc[i, "end"] = datetime.strptime(row["end"], "%Y-%m-%d %H:%M")
                        base.loc[i, "all_day"] = bool(row["all_day"])
                        base.loc[i, "location"] = row.get("location", "")
                        base.loc[i, "notes"] = row.get("notes", "")
                        base.loc[i, "updated_at"] = _now_tzless()
                    except Exception as e:
                        st.error(f"Could not update row {e}")
            st.session_state.df = base
            save_data(base)
            st.success("Saved")
    with c2:
        # Delete by selection
        ids = edited["id"].tolist()
        delete_ids = st.multiselect("Select ids to delete", ids)
        if st.button("Delete selected"):
            base = st.session_state.df
            before = len(base)
            base = base[~base["id"].isin(delete_ids)]
            st.session_state.df = base
            save_data(base)
            st.success(f"Deleted {before - len(base)} event(s)")
    with c3:
        st.download_button(
            "Export CSV",
            data=view.to_csv(index=False).encode("utf-8"),
            file_name="calendar_export.csv",
            mime="text/csv",
        )

# ---------- Studio Tab ----------
with tab_studio:
    section_header("Studio schedule")
    render_editor(st.session_state.df, category="Studio")

# ---------- Community Tab ----------
with tab_comm:
    section_header("Community and shows")
    render_editor(st.session_state.df, category="Community")

# ---------- Public Tab ----------
with tab_public:
    section_header("Public events view")
    # Read only agenda plus export
    public_df = st.session_state.df.copy()
    public_df = public_df[public_df["category"] == "Public"]
    public_df = filter_df(public_df)
    render_agenda(public_df)
    st.download_button(
        "Export CSV",
        data=public_df.to_csv(index=False).encode("utf-8"),
        file_name="public_calendar.csv",
        mime="text/csv",
    )

# ---------- All Events Tab ----------
with tab_all:
    section_header("All events")
    render_editor(st.session_state.df, category=None)
