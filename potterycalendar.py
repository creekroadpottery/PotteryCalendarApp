# Pottery Maker Manager — Complete Prototype
# Enhanced with Portfolio Management and Studio Journal
# Run with: streamlit run pottery_maker_manager.py

import uuid
import os
import base64
import calendar
from datetime import datetime, date, time, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
import pandas as pd
import streamlit as st
from PIL import Image
import io

APP_TITLE = "Pottery Maker Manager"
EVENTS_PATH = "data/events.csv"
JOURNAL_PATH = "data/journal_entries.csv"
PORTFOLIO_PATH = "data/finished_works.csv"
IMAGES_DIR = "data/images"

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

CATEGORY_OPTIONS = ["Studio", "Community", "Public"]
TASK_OPTIONS = [
    "Throwing", "Trimming", "Glazing", "Bisque Firing", "Glaze Firing",
    "Inventory", "Delivery", "Workshop", "Show", "Open Studio",
    "Drop Release", "Meeting", "Other"
]

PIECE_TYPES = [
    "Mug", "Bowl", "Plate", "Vase", "Sculpture", "Tile", "Planter", 
    "Teapot", "Pitcher", "Serving Dish", "Decorative", "Other"
]

GLAZE_TYPES = [
    "Cone 04 Clear", "Cone 6 Clear", "Cone 10 Clear", "Celadon", 
    "Temmoku", "Shino", "Ash Glaze", "Crystalline", "Matte", 
    "Satin", "Raw Clay", "Terra Sigillata", "Other"
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

def generate_id():
    return str(uuid.uuid4())

def save_image(uploaded_file, piece_id):
    """Save uploaded image and return filename"""
    if uploaded_file is not None:
        # Generate filename
        file_extension = uploaded_file.name.split('.')[-1]
        filename = f"{piece_id}_{_now_tzless().strftime('%Y%m%d_%H%M%S')}.{file_extension}"
        filepath = os.path.join(IMAGES_DIR, filename)
        
        # Save file
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getvalue())
        return filename
    return None

def load_image(filename):
    """Load image from file"""
    if filename and os.path.exists(os.path.join(IMAGES_DIR, filename)):
        return Image.open(os.path.join(IMAGES_DIR, filename))
    return None

# ---------- Data Loading ----------

@st.cache_data
def load_events(path: str = EVENTS_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["start", "end"], keep_default_na=False)
        if "all_day" in df:
            df["all_day"] = df["all_day"].astype(bool)
        return df
    except FileNotFoundError:
        # Create empty DataFrame with proper column types
        df = pd.DataFrame(columns=[
            "id", "title", "category", "task_type", "start", "end",
            "all_day", "location", "notes", "created_at", "updated_at"
        ])
        # Ensure proper datetime types for empty DataFrame
        df["start"] = pd.to_datetime(df["start"])
        df["end"] = pd.to_datetime(df["end"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["updated_at"] = pd.to_datetime(df["updated_at"])
        df["all_day"] = df["all_day"].astype(bool)
        return df

@st.cache_data
def load_journal(path: str = JOURNAL_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["entry_date", "created_at"], keep_default_na=False)
        return df
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "id", "entry_date", "title", "content", "mood", "techniques_practiced",
            "materials_used", "linked_event_id", "created_at", "frankl_reflection", 
            "time_awareness_reflection"
        ])
        # Ensure proper datetime types
        df["entry_date"] = pd.to_datetime(df["entry_date"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        return df

@st.cache_data  
def load_portfolio(path: str = PORTFOLIO_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["completion_date", "created_at", "bisque_fire_date", "glaze_fire_date", "refire_date"], keep_default_na=False)
        return df
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "id", "title", "piece_type", "completion_date", "clay_body", "glaze_combo",
            "firing_temp", "dimensions", "weight", "time_invested", "materials_cost",
            "who_for", "what_for", "change_intended", "observations", "challenges",
            "successes", "would_change", "image_filename", "linked_event_id", "created_at",
            # Technical timeline
            "bisque_fire_date", "glaze_fire_date", "refire_date", "cone_temp", 
            "actual_clay_type", "actual_glaze",
            # Design elements (checkboxes)
            "silhouette", "size", "form_shape", "symmetry", "harmony", "color", 
            "texture", "asymmetry", "negative_space", "pattern", "functionality", 
            "line", "emotion", "symbols", "weight_element", "sound",
            # Overall ratings
            "technical_success", "artistic_success", "functionality_rating", "personal_satisfaction"
        ])
        # Ensure proper datetime types
        df["completion_date"] = pd.to_datetime(df["completion_date"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["bisque_fire_date"] = pd.to_datetime(df["bisque_fire_date"])
        df["glaze_fire_date"] = pd.to_datetime(df["glaze_fire_date"])
        df["refire_date"] = pd.to_datetime(df["refire_date"])
        return df

def save_data(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)
    # Clear relevant cache
    if "events" in path:
        load_events.clear()
    elif "journal" in path:
        load_journal.clear()
    elif "portfolio" in path:
        load_portfolio.clear()

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

# ---------- Portfolio Functions ----------

def render_portfolio_piece(piece_row, show_full=False):
    """Render a single portfolio piece"""
    with st.container(border=True):
        col1, col2 = st.columns([1, 2] if show_full else [1, 3])
        
        with col1:
            # Display image if available
            if piece_row.get("image_filename"):
                img = load_image(piece_row["image_filename"])
                if img:
                    st.image(img, use_container_width=True)
                else:
                    st.info("🏺 Image not found")
            else:
                st.info("🏺 No image")
        
        with col2:
            st.markdown(f"**{piece_row['title']}**")
            st.caption(f"{piece_row['piece_type']} • Completed: {piece_row['completion_date'].strftime('%Y-%m-%d') if pd.notna(piece_row['completion_date']) else 'Unknown'}")
            
            if show_full:
                # The Big Questions
                if piece_row.get("who_for"):
                    st.markdown(f"**Who's it for?** {piece_row['who_for']}")
                if piece_row.get("what_for"):
                    st.markdown(f"**What's it for?** {piece_row['what_for']}")
                if piece_row.get("change_intended"):
                    st.markdown(f"**What change?** {piece_row['change_intended']}")
                
                # Technical details
                if piece_row.get("clay_body"):
                    st.caption(f"Clay: {piece_row['clay_body']}")
                if piece_row.get("glaze_combo"):
                    st.caption(f"Glaze: {piece_row['glaze_combo']}")
                if piece_row.get("firing_temp"):
                    st.caption(f"Firing: {piece_row['firing_temp']}")
                    
                # Professional ratings (if available)
                if pd.notna(piece_row.get("technical_success")) and piece_row.get("technical_success") > 0:
                    ratings = []
                    if piece_row.get("technical_success"):
                        ratings.append(f"Technical: {piece_row['technical_success']}/5")
                    if piece_row.get("artistic_success"):
                        ratings.append(f"Artistic: {piece_row['artistic_success']}/5")
                    if piece_row.get("personal_satisfaction"):
                        ratings.append(f"Satisfaction: {piece_row['personal_satisfaction']}/5")
                    if ratings:
                        st.caption("⭐ " + " • ".join(ratings))
                
                # Design elements achieved (show checked ones)
                achieved_elements = []
                design_elements = ["silhouette", "harmony", "form_shape", "color", "texture", "functionality", "emotion"]
                for element in design_elements:
                    if piece_row.get(element) == True:
                        achieved_elements.append(element.replace("_", " ").title())
                if achieved_elements:
                    st.caption(f"✨ Achieved: {', '.join(achieved_elements[:4])}{'...' if len(achieved_elements) > 4 else ''}")
                    
                # Reflections
                if piece_row.get("observations"):
                    st.markdown(f"**Observations:** {piece_row['observations']}")
            else:
                # Compact view
                details = []
                if piece_row.get("clay_body"):
                    details.append(piece_row["clay_body"])
                if piece_row.get("glaze_combo"):
                    details.append(piece_row["glaze_combo"])
                if details:
                    st.caption(" • ".join(details))
                
                # Show ratings in compact view
                if pd.notna(piece_row.get("personal_satisfaction")) and piece_row.get("personal_satisfaction") > 0:
                    satisfaction = piece_row.get("personal_satisfaction", 0)
                    stars = "⭐" * int(satisfaction)
                    st.caption(f"Satisfaction: {stars} ({satisfaction}/5)")

# ---------- Calendar View Functions ----------

def get_calendar_dates(year, month):
    """Get all dates for a calendar month view including padding"""
    import calendar
    cal = calendar.monthcalendar(year, month)
    dates = []
    for week in cal:
        for day in week:
            if day == 0:
                dates.append(None)  # Padding for previous/next month
            else:
                dates.append(date(year, month, day))
    return dates

def render_month_calendar(events_df, current_date):
    """Render a month calendar grid view"""
    year, month = current_date.year, current_date.month
    
    # Calendar header
    month_name = current_date.strftime("%B %Y")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Previous", key="prev_month"):
            if month == 1:
                st.session_state.calendar_date = date(year - 1, 12, 1)
            else:
                st.session_state.calendar_date = date(year, month - 1, 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{month_name}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next ▶", key="next_month"):
            if month == 12:
                st.session_state.calendar_date = date(year + 1, 1, 1)
            else:
                st.session_state.calendar_date = date(year, month + 1, 1)
            st.rerun()
    
    # Day headers
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, day_name in enumerate(day_names):
        with cols[i]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; padding: 5px;'>{day_name}</div>", unsafe_allow_html=True)
    
    # Get calendar dates
    dates = get_calendar_dates(year, month)
    
    # Filter events for this month - handle empty DataFrame
    month_events = pd.DataFrame()
    if not events_df.empty:
        start_month = datetime.combine(date(year, month, 1), time(0, 0))
        if month == 12:
            end_month = datetime.combine(date(year + 1, 1, 1), time(0, 0))
        else:
            end_month = datetime.combine(date(year, month + 1, 1), time(0, 0))
        
        month_events = events_df[(events_df["start"] >= start_month) & (events_df["start"] < end_month)]
    
    # Render calendar grid
    for week_start in range(0, len(dates), 7):
        cols = st.columns(7)
        for i in range(7):
            day_date = dates[week_start + i]
            with cols[i]:
                if day_date is None:
                    # Empty cell for padding
                    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                else:
                    # Day cell
                    day_events = pd.DataFrame()
                    if not month_events.empty:
                        day_events = month_events[month_events["start"].dt.date == day_date]
                    
                    # Day number
                    is_today = day_date == date.today()
                    day_style = "background: #e3f2fd; border-radius: 4px;" if is_today else ""
                    
                    cell_content = f"<div style='min-height: 80px; border: 1px solid #ddd; padding: 2px; {day_style}'>"
                    cell_content += f"<div style='font-weight: bold; text-align: right; margin-bottom: 2px;'>{day_date.day}</div>"
                    
                    # Add events
                    if not day_events.empty:
                        for _, event in day_events.head(3).iterrows():  # Max 3 events shown
                            color = CATEGORY_COLORS.get(event["category"], "#6B7280")
                            cell_content += f"""
                            <div style='background: {color}; color: white; font-size: 10px; 
                                       padding: 1px 3px; margin: 1px 0; border-radius: 2px; 
                                       white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
                                {event["title"][:20]}{'...' if len(event["title"]) > 20 else ''}
                            </div>
                            """
                        
                        if len(day_events) > 3:
                            cell_content += f"<div style='font-size: 10px; color: #666;'>+{len(day_events) - 3} more</div>"
                    
                    cell_content += "</div>"
                    st.markdown(cell_content, unsafe_allow_html=True)

def render_week_calendar(events_df, current_date):
    """Render a week calendar view"""
    # Get start of week (Monday)
    days_since_monday = current_date.weekday()
    week_start = current_date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Previous Week", key="prev_week"):
            st.session_state.calendar_date = current_date - timedelta(days=7)
            st.rerun()
    
    with col2:
        week_range = f"{week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}"
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{week_range}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Week ▶", key="next_week"):
            st.session_state.calendar_date = current_date + timedelta(days=7)
            st.rerun()
    
    # Week grid
    cols = st.columns(7)
    for i in range(7):
        day = week_start + timedelta(days=i)
        
        # Get day events - handle empty DataFrame
        day_events = pd.DataFrame()
        if not events_df.empty:
            day_events = events_df[events_df["start"].dt.date == day]
        
        with cols[i]:
            is_today = day == date.today()
            header_style = "background: #e3f2fd; padding: 5px; border-radius: 4px;" if is_today else "padding: 5px;"
            
            st.markdown(f"""
            <div style='{header_style}'>
                <div style='font-weight: bold; text-align: center;'>{day.strftime('%a')}</div>
                <div style='text-align: center; font-size: 18px;'>{day.day}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Events for this day
            if not day_events.empty:
                for _, event in day_events.iterrows():
                    color = CATEGORY_COLORS.get(event["category"], "#6B7280")
                    time_str = "All day" if event["all_day"] else event["start"].strftime("%I:%M %p")
                    
                    st.markdown(f"""
                    <div style='background: {color}; color: white; padding: 4px; margin: 2px 0; 
                               border-radius: 4px; font-size: 12px;'>
                        <div style='font-weight: bold;'>{event["title"]}</div>
                        <div style='opacity: 0.9;'>{time_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

def render_day_calendar(events_df, current_date):
    """Render a single day detailed view"""
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Previous Day", key="prev_day"):
            st.session_state.calendar_date = current_date - timedelta(days=1)
            st.rerun()
    
    with col2:
        day_name = current_date.strftime("%A, %B %d, %Y")
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{day_name}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Day ▶", key="next_day"):
            st.session_state.calendar_date = current_date + timedelta(days=1)
            st.rerun()
    
    # Day events - handle empty DataFrame
    day_events = pd.DataFrame()
    if not events_df.empty:
        day_events = events_df[events_df["start"].dt.date == current_date].sort_values("start")
    
    if not day_events.empty:
        for _, event in day_events.iterrows():
            color = CATEGORY_COLORS.get(event["category"], "#6B7280")
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{event['title']}**")
                    time_str = "All day" if event["all_day"] else f"{event['start'].strftime('%I:%M %p')} - {event['end'].strftime('%I:%M %p')}"
                    st.caption(f"{event['category']} • {event['task_type']} • {time_str}")
                    if event.get("location"):
                        st.caption(f"📍 {event['location']}")
                    if event.get("notes"):
                        st.write(event["notes"])
                with col2:
                    badge(event["category"], color)
    else:
        st.info("No events scheduled for this day")
        st.markdown("Perfect time for some studio work! 🏺")
        
        # Quick add event for this day
        if st.button("➕ Add Event for This Day", key="quick_add_day"):
            st.session_state.quick_add_date = current_date
            st.session_state.show_quick_add = True

def filter_events_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filter events DataFrame based on sidebar filters"""
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
    """Render agenda list view"""
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
                        st.caption(f"📍 {row['location']}")
                    if row.get("notes"):
                        st.write(row["notes"]) 
                with c2:
                    badge(row["category"], color)

# ---------- Main App ----------

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

with st.sidebar:
    st.subheader("🏺 Creek Road Pottery")
    st.markdown("*Complete maker management*")
    
    # Time Scarcity Awareness
    with st.expander("⏰ Time Awareness", expanded=False):
        st.markdown("**Living with Intention**")
        birth_year = st.number_input("Birth Year (optional)", min_value=1920, max_value=2010, value=1980, help="For time awareness calculation")
        if birth_year:
            current_age = date.today().year - birth_year
            remaining_days = (90 - current_age) * 365
            remaining_years = 90 - current_age
            
            if remaining_days > 0:
                st.markdown(f"**If you live to 90, you may have roughly:**")
                st.markdown(f"🗓️ **{remaining_days:,} days** remaining")
                st.markdown(f"📅 **{remaining_years} years** remaining")
                st.caption("Each day in the studio matters.")
            else:
                st.markdown("🎉 **Every day is bonus time!**")
                st.caption("You've exceeded the 90-year mark - what a gift!")
    
    st.subheader("Quick Filters")
    selected_month = st.date_input("Month", value=date.today().replace(day=1))
    cat_filter = st.multiselect("Categories", CATEGORY_OPTIONS, default=CATEGORY_OPTIONS)
    task_filter = st.multiselect("Task Type", TASK_OPTIONS)
    show_past = st.toggle("Show past events", value=True)
    
    st.markdown("---")
    st.caption("Data saved to /data folder")

# Load all data
if "events_df" not in st.session_state:
    st.session_state.events_df = load_events()
if "journal_df" not in st.session_state:
    st.session_state.journal_df = load_journal()
if "portfolio_df" not in st.session_state:
    st.session_state.portfolio_df = load_portfolio()

# Initialize calendar date if not exists
if "calendar_date" not in st.session_state:
    st.session_state.calendar_date = date.today()

# Tabs
tab_calendar, tab_portfolio, tab_journal, tab_studio, tab_comm, tab_public, tab_all = st.tabs([
    "📅 Calendar", "🏺 Portfolio", "📓 Journal", "🎨 Studio", "🤝 Community", "🌍 Public", "📋 All Events",
])

# ---------- Calendar Tab (Add Event) ----------
with tab_calendar:
    # Calendar view controls
    calendar_col1, calendar_col2, calendar_col3 = st.columns([2, 2, 1])
    
    with calendar_col1:
        calendar_view = st.radio(
            "Calendar View", 
            ["Month", "Week", "Day", "Agenda"], 
            horizontal=True,
            key="calendar_view_mode"
        )
    
    with calendar_col2:
        # Date picker for quick navigation
        selected_date = st.date_input("Jump to date", value=st.session_state.calendar_date)
        if selected_date != st.session_state.calendar_date:
            st.session_state.calendar_date = selected_date
            st.rerun()
    
    with calendar_col3:
        if st.button("Today", key="go_to_today"):
            st.session_state.calendar_date = date.today()
            st.rerun()
    
    st.markdown("---")
    
    # Display calendar based on selected view
    if calendar_view == "Month":
        section_header("📅 Month View")
        render_month_calendar(st.session_state.events_df, st.session_state.calendar_date)
        
    elif calendar_view == "Week":
        section_header("📅 Week View")
        render_week_calendar(st.session_state.events_df, st.session_state.calendar_date)
        
    elif calendar_view == "Day":
        section_header("📅 Day View")
        render_day_calendar(st.session_state.events_df, st.session_state.calendar_date)
        
    elif calendar_view == "Agenda":
        section_header("📅 Agenda View")
        filtered_events = filter_events_df(st.session_state.events_df)
        render_agenda(filtered_events)
    
    st.markdown("---")
    
    # Add new event form (moved below calendar views)
    section_header("➕ Schedule Studio Time")
    with st.form("add_event_form", clear_on_submit=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            title = st.text_input("Title", placeholder="Example: Glaze firing Cone 6")
            category = st.selectbox("Category", CATEGORY_OPTIONS)
            task_type = st.selectbox("Task Type", TASK_OPTIONS)
            location = st.text_input("Location", placeholder="Studio, Gallery, Fairgrounds")
        with c2:
            all_day = st.checkbox("All day event", value=False)
            
            # Use quick add date if available
            default_start_date = date.today()
            if hasattr(st.session_state, 'quick_add_date') and st.session_state.get('show_quick_add'):
                default_start_date = st.session_state.quick_add_date
            
            start_date = st.date_input("Start date", value=default_start_date)
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
                df = st.session_state.events_df
                st.session_state.events_df = pd.concat([df, pd.DataFrame(instances)], ignore_index=True)
                save_data(st.session_state.events_df, EVENTS_PATH)
                st.success(f"Added {len(instances)} event(s)")
                
                # Clear quick add state
                if hasattr(st.session_state, 'show_quick_add'):
                    st.session_state.show_quick_add = False

# ---------- Portfolio Tab ----------
with tab_portfolio:
    section_header("Studio Portfolio")
    
    # Add new piece form
    with st.expander("➕ Document New Finished Piece", expanded=False):
        with st.form("add_portfolio_piece"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                piece_title = st.text_input("Piece Title", placeholder="Morning Coffee Mug #3")
                piece_type = st.selectbox("Type", PIECE_TYPES)
                completion_date = st.date_input("Completion Date", value=date.today())
                
                # Link to calendar event
                recent_events = st.session_state.events_df.tail(20)
                event_options = ["None"] + [f"{row['title']} ({row['start'].strftime('%m/%d')})" for _, row in recent_events.iterrows()]
                linked_event = st.selectbox("Link to Calendar Event", event_options)
                
            with col2:
                # Image upload
                uploaded_image = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
                if uploaded_image:
                    st.image(uploaded_image, width=200)
                
            # The Big Questions
            st.markdown("### The Big Questions")
            who_for = st.text_input("Who's it for?", placeholder="Client name, gift recipient, gallery, personal use...")
            what_for = st.text_area("What's it for?", placeholder="Daily coffee ritual, wedding gift, artistic statement, skill practice...")
            change_intended = st.text_area("What change are you trying to make?", placeholder="Building confidence, mastering technique, growing business, healing...")
            
            # Technical details
            st.markdown("### Technical Details")
            t1, t2, t3 = st.columns(3)
            with t1:
                clay_body = st.text_input("Clay Body", placeholder="B-Mix, Porcelain, Stoneware...")
                firing_temp = st.text_input("Firing Temp", placeholder="Cone 6, 1240°C, Reduction...")
            with t2:
                glaze_combo = st.text_input("Glaze Combination", placeholder="Temmoku over Shino...")
                dimensions = st.text_input("Dimensions", placeholder="4\"H x 3.5\"W")
            with t3:
                time_invested = st.number_input("Time Invested (hours)", min_value=0.0, step=0.5)
                weight = st.text_input("Weight", placeholder="1.2 lbs, 550g")
                
            # Professional Analysis
            st.markdown("### Professional Analysis")
            
            # Technical Tracking
            st.markdown("**Technical Timeline**")
            tech_col1, tech_col2, tech_col3 = st.columns(3)
            with tech_col1:
                bisque_fire_date = st.date_input("Bisque Fire Date", value=None)
                glaze_fire_date = st.date_input("Glaze Fire Date", value=None)
            with tech_col2:
                refire_date = st.date_input("Re-fire Date", value=None)
                cone_temp = st.text_input("Cone Temp", placeholder="Cone 6, ^04, etc.")
            with tech_col3:
                actual_clay_type = st.text_input("Actual Clay Used", placeholder="Final clay body used")
                actual_glaze = st.text_input("Final Glaze", placeholder="Final glaze combination")
            
            # Design Elements Assessment
            st.markdown("**Design Elements Assessment**")
            st.caption("Check the elements that were successfully achieved in this piece")
            
            # Create columns for checkboxes
            elem_col1, elem_col2, elem_col3, elem_col4 = st.columns(4)
            
            with elem_col1:
                st.markdown("**Form & Structure**")
                silhouette = st.checkbox("Silhouette")
                size = st.checkbox("Size")
                form_shape = st.checkbox("Form/Shape")
                symmetry = st.checkbox("Symmetry")
                
            with elem_col2:
                st.markdown("**Visual Elements**")
                harmony = st.checkbox("Harmony")
                color = st.checkbox("Color")
                texture = st.checkbox("Texture")
                asymmetry = st.checkbox("Asymmetry")
                
            with elem_col3:
                st.markdown("**Design Principles**")
                negative_space = st.checkbox("Negative Space")
                pattern = st.checkbox("Pattern")
                functionality = st.checkbox("Functionality")
                line = st.checkbox("Line")
                
            with elem_col4:
                st.markdown("**Expressive Quality**")
                emotion = st.checkbox("Emotion")
                symbols = st.checkbox("Symbols")
                weight_design = st.checkbox("Weight")
                sound = st.checkbox("Sound")
            
            # Overall Assessment
            st.markdown("**Overall Assessment**")
            overall_col1, overall_col2 = st.columns(2)
            with overall_col1:
                technical_success = st.slider("Technical Success", 1, 5, 3, help="1=Major issues, 5=Flawless execution")
                artistic_success = st.slider("Artistic Success", 1, 5, 3, help="1=Didn't achieve vision, 5=Exceeded expectations")
            with overall_col2:
                functionality_rating = st.slider("Functionality", 1, 5, 3, help="1=Not functional, 5=Perfect for intended use")
                personal_satisfaction = st.slider("Personal Satisfaction", 1, 5, 3, help="1=Disappointed, 5=Thrilled")
            
            # Reflection
            st.markdown("### Reflection")
            observations = st.text_area("Observations", placeholder="How did the piece turn out? What surprised you?")
            challenges = st.text_area("Challenges Encountered", placeholder="What went wrong or was difficult?")
            successes = st.text_area("Successes", placeholder="What worked really well?")
            would_change = st.text_area("What Would You Change?", placeholder="Next time I would...")
            
            submitted_piece = st.form_submit_button("Add to Portfolio")
            
            if submitted_piece and piece_title.strip():
                piece_id = generate_id()
                
                # Save image if uploaded
                image_filename = None
                if uploaded_image:
                    image_filename = save_image(uploaded_image, piece_id)
                
                # Get linked event ID
                linked_event_id = None
                if linked_event != "None" and not recent_events.empty:
                    event_index = event_options.index(linked_event) - 1  # -1 for "None" offset
                    if 0 <= event_index < len(recent_events):
                        linked_event_id = recent_events.iloc[event_index]["id"]
                
                new_piece = {
                    "id": piece_id,
                    "title": piece_title.strip(),
                    "piece_type": piece_type,
                    "completion_date": completion_date,
                    "clay_body": clay_body.strip(),
                    "glaze_combo": glaze_combo.strip(),
                    "firing_temp": firing_temp.strip(),
                    "dimensions": dimensions.strip(),
                    "weight": weight.strip(),
                    "time_invested": time_invested,
                    "materials_cost": 0.0,  # Could integrate with cost analysis later
                    "who_for": who_for.strip(),
                    "what_for": what_for.strip(),
                    "change_intended": change_intended.strip(),
                    "observations": observations.strip(),
                    "challenges": challenges.strip(),
                    "successes": successes.strip(),
                    "would_change": would_change.strip(),
                    "image_filename": image_filename,
                    "linked_event_id": linked_event_id,
                    "created_at": _now_tzless(),
                    # Technical timeline
                    "bisque_fire_date": bisque_fire_date,
                    "glaze_fire_date": glaze_fire_date,
                    "refire_date": refire_date,
                    "cone_temp": cone_temp.strip(),
                    "actual_clay_type": actual_clay_type.strip(),
                    "actual_glaze": actual_glaze.strip(),
                    # Design elements
                    "silhouette": silhouette,
                    "size": size,
                    "form_shape": form_shape,
                    "symmetry": symmetry,
                    "harmony": harmony,
                    "color": color,
                    "texture": texture,
                    "asymmetry": asymmetry,
                    "negative_space": negative_space,
                    "pattern": pattern,
                    "functionality": functionality,
                    "line": line,
                    "emotion": emotion,
                    "symbols": symbols,
                    "weight_element": weight_design,  # Design element checkbox
                    "sound": sound,
                    # Overall ratings
                    "technical_success": technical_success,
                    "artistic_success": artistic_success,
                    "functionality_rating": functionality_rating,
                    "personal_satisfaction": personal_satisfaction,
                }
                
                st.session_state.portfolio_df = pd.concat([
                    st.session_state.portfolio_df, 
                    pd.DataFrame([new_piece])
                ], ignore_index=True)
                save_data(st.session_state.portfolio_df, PORTFOLIO_PATH)
                st.success("✨ Added to portfolio!")
                st.rerun()
    
    # Display portfolio
    portfolio_df = st.session_state.portfolio_df.sort_values("completion_date", ascending=False)
    
    if not portfolio_df.empty:
        # Portfolio filters
        col1, col2, col3 = st.columns(3)
        with col1:
            type_filter = st.multiselect("Filter by Type", PIECE_TYPES, default=PIECE_TYPES)
        with col2:
            search_term = st.text_input("Search", placeholder="Search titles, glazes, notes...")
        with col3:
            view_mode = st.radio("View Mode", ["Gallery", "Detail"], horizontal=True)
        
        # Apply filters
        filtered_df = portfolio_df.copy()
        if type_filter:
            filtered_df = filtered_df[filtered_df["piece_type"].isin(type_filter)]
        if search_term:
            # Simple text search across multiple columns
            search_cols = ["title", "glaze_combo", "observations", "who_for", "what_for"]
            mask = filtered_df[search_cols].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_df = filtered_df[mask]
        
        # Display pieces
        if view_mode == "Gallery":
            # Grid view - 3 columns
            for i in range(0, len(filtered_df), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(filtered_df):
                        with col:
                            piece = filtered_df.iloc[i + j]
                            render_portfolio_piece(piece, show_full=False)
        else:
            # Detailed list view
            for _, piece in filtered_df.iterrows():
                render_portfolio_piece(piece, show_full=True)
                
        # Export button
        st.download_button(
            "📋 Export Portfolio CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_portfolio_{date.today().isoformat()}.csv",
            mime="text/csv"
        )
    else:
        st.info("🏺 No finished pieces yet. Document your first piece above!")

# ---------- Journal Tab ----------
with tab_journal:
    section_header("Studio Journal")
    
    # Add journal entry
    with st.expander("✏️ New Journal Entry", expanded=True):
        with st.form("add_journal_entry"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                journal_title = st.text_input("Entry Title", placeholder="Morning throwing session insights")
                journal_content = st.text_area("Journal Entry", placeholder="What happened in the studio today? What did you learn?", height=150)
            
            with col2:
                entry_date = st.date_input("Date", value=date.today())
                mood = st.selectbox("Studio Mood", ["😊 Great", "😌 Good", "😐 Okay", "😕 Tough", "😤 Frustrated"])
                
            # Optional connections
            techniques_practiced = st.text_input("Techniques Practiced", placeholder="Pulling handles, trimming feet, wax resist...")
            materials_used = st.text_input("Materials Used", placeholder="B-Mix, Temmoku glaze, wax...")
            
            # Viktor Frankl Reflection
            st.markdown("---")
            st.markdown("### 🤔 Daily Reflection")
            st.markdown('*"Live as if you were living already for the second time and as if you had acted the first time as wrongly as you are about to act now!"*')
            st.caption("— Viktor Frankl")
            
            frankl_reflection = st.text_area(
                "If you were living today for the second time, what would you do differently?",
                placeholder="What choices would I make differently in the studio? How would I approach my craft with more intention? What would I prioritize?",
                height=100,
                help="Reflect on today's studio time through the lens of living it again - what would you change?"
            )
            
            # Time awareness reflection
            time_awareness = st.text_area(
                "Knowing your remaining days are finite, how does this change your approach to today's work?",
                placeholder="How does time scarcity influence my creative choices? What becomes more important when I remember life is limited?",
                height=80,
                help="Connect your creative work to the reality of limited time"
            )
            
            # Link to event
            recent_events = st.session_state.events_df.tail(10)
            event_options = ["None"] + [f"{row['title']} ({row['start'].strftime('%m/%d')})" for _, row in recent_events.iterrows()]
            linked_journal_event = st.selectbox("Link to Calendar Event", event_options)
            
            submitted_journal = st.form_submit_button("Add Entry")
            
            if submitted_journal and journal_content.strip():
                linked_event_id = None
                if linked_journal_event != "None" and not recent_events.empty:
                    event_index = event_options.index(linked_journal_event) - 1
                    if 0 <= event_index < len(recent_events):
                        linked_event_id = recent_events.iloc[event_index]["id"]
                
                new_entry = {
                    "id": generate_id(),
                    "entry_date": entry_date,
                    "title": journal_title.strip() if journal_title.strip() else f"Studio Notes - {entry_date}",
                    "content": journal_content.strip(),
                    "mood": mood,
                    "techniques_practiced": techniques_practiced.strip(),
                    "materials_used": materials_used.strip(),
                    "linked_event_id": linked_event_id,
                    "created_at": _now_tzless(),
                    "frankl_reflection": frankl_reflection.strip(),
                    "time_awareness_reflection": time_awareness.strip(),
                }
                
                st.session_state.journal_df = pd.concat([
                    st.session_state.journal_df,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                save_data(st.session_state.journal_df, JOURNAL_PATH)
                st.success("📝 Journal entry saved!")
                st.rerun()
    
    # Display journal entries
    journal_df = st.session_state.journal_df.sort_values("entry_date", ascending=False)
    
    if not journal_df.empty:
        st.markdown("### Recent Entries")
        for _, entry in journal_df.head(10).iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{entry['title']}**")
                    st.markdown(entry["content"])
                    if entry.get("techniques_practiced"):
                        st.caption(f"🎨 Techniques: {entry['techniques_practiced']}")
                    if entry.get("materials_used"):
                        st.caption(f"🧱 Materials: {entry['materials_used']}")
                with col2:
                    st.caption(entry["entry_date"].strftime("%Y-%m-%d"))
                    st.markdown(entry["mood"])
    else:
        st.info("📓 Start your first studio journal entry above!")

# Studio Tab
with tab_studio:
    section_header("Studio Schedule")
    studio_df = st.session_state.events_df[st.session_state.events_df["category"] == "Studio"]
    filtered_studio = filter_events_df(studio_df)
    render_agenda(filtered_studio)

# Community Tab
with tab_comm:
    section_header("Community Events")
    comm_df = st.session_state.events_df[st.session_state.events_df["category"] == "Community"]
    filtered_comm = filter_events_df(comm_df)
    render_agenda(filtered_comm)

# Public Tab
with tab_public:
    section_header("Public Events")
    public_df = st.session_state.events_df[st.session_state.events_df["category"] == "Public"]
    filtered_public = filter_events_df(public_df)
    render_agenda(filtered_public)

# All Events Tab
with tab_all:
    section_header("All Events")
    filtered_all = filter_events_df(st.session_state.events_df)
    render_agenda(filtered_all)
    
    st.download_button(
        "📋 Export All Events CSV",
        data=filtered_all.to_csv(index=False).encode("utf-8"),
        file_name=f"pottery_calendar_{date.today().isoformat()}.csv",
        mime="text/csv"
    )
