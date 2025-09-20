# Pottery Maker Manager — Complete Prototype
# Enhanced with Portfolio Management and Studio Journal
# Run with: streamlit run pottery_maker_manager.py

import uuid
import os
import base64
import calendar
import time
from datetime import datetime, date, time as dt_time, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
import pandas as pd
import streamlit as st
from PIL import Image
import io

APP_TITLE = "Pottery Maker Manager"
APP_VERSION = "1.0.0"
EVENTS_PATH = "data/events.csv"
JOURNAL_PATH = "data/journal_entries.csv"
PORTFOLIO_PATH = "data/finished_works.csv"
GOALS_PATH = "data/goals.csv"
TIMETRACK_PATH = "data/time_tracking.csv"
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

TIME_CATEGORIES = [
    "🏺 Studio Work", "🎨 Creative Planning", "📚 Learning/Research", 
    "💼 Business/Admin", "🍽️ Meals", "😴 Sleep", "🚿 Personal Care",
    "🏃‍♀️ Exercise", "👥 Social", "📱 Social Media", "📺 Entertainment",
    "🛒 Errands", "🧹 Household", "🚗 Travel", "💭 Other"
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

@st.cache_data  
def load_goals(path: str = GOALS_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["created_date", "target_date", "completed_date"], keep_default_na=False)
        return df
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "id", "title", "description", "category", "status", "priority", 
            "created_date", "target_date", "completed_date", "progress_notes",
            "frankl_why", "time_awareness_note", "linked_pieces", "tags"
        ])
        # Ensure proper datetime types
        df["created_date"] = pd.to_datetime(df["created_date"])
        df["target_date"] = pd.to_datetime(df["target_date"])
        df["completed_date"] = pd.to_datetime(df["completed_date"])
        return df

@st.cache_data  
def load_timetrack(path: str = TIMETRACK_PATH) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, parse_dates=["start_time", "end_time"], keep_default_na=False)
        return df
    except FileNotFoundError:
        df = pd.DataFrame(columns=[
            "id", "category", "activity", "start_time", "end_time", 
            "duration_minutes", "notes", "date", "frankl_reflection"
        ])
        # Ensure proper datetime types
        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])
        df["date"] = pd.to_datetime(df["date"])
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
    elif "goals" in path:
        load_goals.clear()
    elif "timetrack" in path:
        load_timetrack.clear()

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
        until_dt = datetime.combine(until, dt_time(23, 59, 59))
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
        start_month = datetime.combine(date(year, month, 1), dt_time(0, 0))
        if month == 12:
            end_month = datetime.combine(date(year + 1, 1, 1), dt_time(0, 0))
        else:
            end_month = datetime.combine(date(year, month + 1, 1), dt_time(0, 0))
        
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

def render_year_calendar(events_df, current_date):
    """Render a year calendar overview"""
    year = current_date.year
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("◀ Previous Year", key="prev_year"):
            st.session_state.calendar_date = date(year - 1, current_date.month, 1)
            st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{year}</h3>", unsafe_allow_html=True)
    
    with col3:
        if st.button("Next Year ▶", key="next_year"):
            st.session_state.calendar_date = date(year + 1, current_date.month, 1)
            st.rerun()
    
    # Year events summary
    if not events_df.empty:
        year_start = datetime.combine(date(year, 1, 1), dt_time(0, 0))
        year_end = datetime.combine(date(year + 1, 1, 1), dt_time(0, 0))
        year_events = events_df[(events_df["start"] >= year_start) & (events_df["start"] < year_end)]
        
        # Year stats
        if not year_events.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Events", len(year_events))
            with col2:
                studio_count = len(year_events[year_events["category"] == "Studio"])
                st.metric("Studio Sessions", studio_count)
            with col3:
                community_count = len(year_events[year_events["category"] == "Community"])  
                st.metric("Community Events", community_count)
            with col4:
                public_count = len(year_events[year_events["category"] == "Public"])
                st.metric("Public Events", public_count)
    
    # 12-month mini calendar grid
    st.markdown("### Monthly Overview")
    
    # Render 3 rows of 4 months each
    for row in range(3):
        cols = st.columns(4)
        for col in range(4):
            month_num = row * 4 + col + 1
            month_date = date(year, month_num, 1)
            
            with cols[col]:
                # Month header
                month_name = month_date.strftime("%B")
                is_current_month = month_num == current_date.month and year == date.today().year
                header_style = "background: #e3f2fd; border-radius: 4px; margin-bottom: 5px;" if is_current_month else "margin-bottom: 5px;"
                
                st.markdown(f"<div style='{header_style} padding: 5px; text-align: center; font-weight: bold;'>{month_name}</div>", unsafe_allow_html=True)
                
                # Mini month calendar
                month_dates = get_calendar_dates(year, month_num)
                
                # Filter events for this month
                month_events = pd.DataFrame()
                if not events_df.empty:
                    month_start = datetime.combine(date(year, month_num, 1), dt_time(0, 0))
                    if month_num == 12:
                        month_end = datetime.combine(date(year + 1, 1, 1), dt_time(0, 0))
                    else:
                        month_end = datetime.combine(date(year, month_num + 1, 1), dt_time(0, 0))
                    month_events = events_df[(events_df["start"] >= month_start) & (events_df["start"] < month_end)]
                
                # Create mini calendar HTML
                mini_cal = "<div style='font-size: 10px;'>"
                
                # Day headers
                mini_cal += "<div style='display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; margin-bottom: 2px;'>"
                for day_name in ["M", "T", "W", "T", "F", "S", "S"]:
                    mini_cal += f"<div style='text-align: center; font-weight: bold;'>{day_name}</div>"
                mini_cal += "</div>"
                
                # Calendar days
                mini_cal += "<div style='display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px;'>"
                for day_date in month_dates:
                    if day_date is None:
                        mini_cal += "<div style='height: 15px;'></div>"
                    else:
                        # Check if this day has events
                        day_has_events = False
                        if not month_events.empty:
                            day_has_events = len(month_events[month_events["start"].dt.date == day_date]) > 0
                        
                        is_today = day_date == date.today()
                        
                        cell_style = "height: 15px; text-align: center; font-size: 9px;"
                        if is_today:
                            cell_style += " background: #2196F3; color: white; border-radius: 2px;"
                        elif day_has_events:
                            cell_style += " background: #4CAF50; color: white; border-radius: 2px;"
                        
                        mini_cal += f"<div style='{cell_style}'>{day_date.day}</div>"
                
                mini_cal += "</div></div>"
                
                # Show event count for this month
                if not month_events.empty:
                    mini_cal += f"<div style='text-align: center; font-size: 10px; color: #666; margin-top: 3px;'>{len(month_events)} events</div>"
                
                st.markdown(mini_cal, unsafe_allow_html=True)
                
                # Click to navigate to month
                if st.button(f"View {month_name}", key=f"goto_month_{month_num}", help=f"Switch to {month_name} {year}"):
                    st.session_state.calendar_date = month_date
                    st.session_state.calendar_view_mode = "Month"
                    st.rerun()

def filter_events_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filter events DataFrame based on sidebar filters"""
    if df.empty:
        return df
    df = df.copy()
    # Time window for selected month
    start_month = datetime.combine(selected_month.replace(day=1), dt_time(0, 0))
    if selected_month.month == 12:
        next_month = date(selected_month.year + 1, 1, 1)
    else:
        next_month = date(selected_month.year, selected_month.month + 1, 1)
    end_month = datetime.combine(next_month, dt_time(0, 0))

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
if "goals_df" not in st.session_state:
    st.session_state.goals_df = load_goals()
if "timetrack_df" not in st.session_state:
    st.session_state.timetrack_df = load_timetrack()

# Initialize timer state
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "timer_start" not in st.session_state:
    st.session_state.timer_start = None
if "timer_category" not in st.session_state:
    st.session_state.timer_category = None

# Initialize calendar date if not exists
if "calendar_date" not in st.session_state:
    st.session_state.calendar_date = date.today()

# Tabs
tab_calendar, tab_tracker, tab_goals, tab_portfolio, tab_journal, tab_search, tab_studio, tab_comm, tab_public, tab_all, tab_about = st.tabs([
    "📅 Calendar", "⏱️ Time Tracker", "🎯 Goals", "🏺 Portfolio", "📝 Journal", "🔍 Search", "🎨 Studio", "🤝 Community", "🌍 Public", "📋 All Events", "ℹ️ About",
])

# ---------- Calendar Tab (Add Event) ----------
with tab_calendar:
    # Calendar view controls
    calendar_col1, calendar_col2, calendar_col3 = st.columns([2, 2, 1])
    
    with calendar_col1:
        calendar_view = st.radio(
            "Calendar View", 
            ["Month", "Week", "Day", "Year", "Agenda"], 
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
        
    elif calendar_view == "Year":
        section_header("📅 Year View")
        render_year_calendar(st.session_state.events_df, st.session_state.calendar_date)
        
    elif calendar_view == "Agenda":
        section_header("📅 Agenda View")
        filtered_events = filter_events_df(st.session_state.events_df)
        render_agenda(filtered_events)
    
    st.markdown("---")
    
    # Add new event form (moved below calendar views)
    section_header("➕ Schedule Event")
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
                start_time = dt_time(9, 0)
                end_date = st.date_input("End date", value=start_date)
                end_time = dt_time(17, 0)
            else:
                start_time = st.time_input("Start time", value=dt_time(9, 0))
                end_date = st.date_input("End date", value=start_date)
                end_time = st.time_input("End time", value=dt_time(12, 0))

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
                    end_dt = datetime.combine(end_date, dt_time(23, 59))
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
    
    # Event management section
    st.markdown("---")
    section_header("⚙️ Manage Existing Events")
    
    if not st.session_state.events_df.empty:
        # Show recent events for editing
        recent_events = st.session_state.events_df.sort_values("start", ascending=False).head(20)
        
        edit_col1, edit_col2 = st.columns([2, 1])
        with edit_col1:
            selected_event_options = [f"{row['title']} - {row['start'].strftime('%m/%d %I:%M %p')}" for _, row in recent_events.iterrows()]
            selected_event_display = st.selectbox("Select Event to Edit/Delete", ["None"] + selected_event_options)
        
        if selected_event_display != "None":
            event_index = selected_event_options.index(selected_event_display)
            selected_event = recent_events.iloc[event_index]
            
            with edit_col2:
                action_col1, action_col2 = st.columns(2)
                with action_col1:
                    edit_event = st.button("✏️ Edit", key="edit_selected_event")
                with action_col2:
                    delete_event = st.button("🗑️ Delete", key="delete_selected_event", type="secondary")
            
            # Delete confirmation
            if delete_event:
                st.error("⚠️ Confirm deletion:")
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Yes, Delete", key="confirm_delete", type="primary"):
                        # Remove event from dataframe
                        st.session_state.events_df = st.session_state.events_df[
                            st.session_state.events_df["id"] != selected_event["id"]
                        ]
                        save_data(st.session_state.events_df, EVENTS_PATH)
                        st.success("🗑️ Event deleted!")
                        st.rerun()
                with confirm_col2:
                    if st.button("❌ Cancel", key="cancel_delete"):
                        st.rerun()
            
            # Edit form
            if edit_event or st.session_state.get("editing_event", False):
                st.session_state.editing_event = True
                
                with st.form("edit_event_form"):
                    st.markdown(f"**Editing: {selected_event['title']}**")
                    
                    edit_col1, edit_col2 = st.columns([2, 1])
                    with edit_col1:
                        edit_title = st.text_input("Title", value=selected_event['title'])
                        edit_category = st.selectbox("Category", CATEGORY_OPTIONS, index=CATEGORY_OPTIONS.index(selected_event['category']))
                        edit_task_type = st.selectbox("Task Type", TASK_OPTIONS, index=TASK_OPTIONS.index(selected_event['task_type']) if selected_event['task_type'] in TASK_OPTIONS else 0)
                        edit_location = st.text_input("Location", value=selected_event.get('location', ''))
                    
                    with edit_col2:
                        edit_all_day = st.checkbox("All day event", value=bool(selected_event['all_day']))
                        
                        # Parse existing dates/times
                        original_start = pd.to_datetime(selected_event['start'])
                        original_end = pd.to_datetime(selected_event['end'])
                        
                        edit_start_date = st.date_input("Start date", value=original_start.date())
                        if not edit_all_day:
                            edit_start_time = st.time_input("Start time", value=original_start.time())
                            edit_end_date = st.date_input("End date", value=original_end.date())
                            edit_end_time = st.time_input("End time", value=original_end.time())
                        else:
                            edit_start_time = dt_time(9, 0)
                            edit_end_date = st.date_input("End date", value=original_end.date())
                            edit_end_time = dt_time(17, 0)
                    
                    edit_notes = st.text_area("Notes", value=selected_event.get('notes', ''))
                    
                    form_col1, form_col2 = st.columns(2)
                    with form_col1:
                        update_event = st.form_submit_button("💾 Update Event", type="primary")
                    with form_col2:
                        cancel_edit = st.form_submit_button("❌ Cancel")
                    
                    if update_event:
                        # Update the event
                        start_dt = datetime.combine(edit_start_date, edit_start_time)
                        if edit_all_day:
                            end_dt = datetime.combine(edit_end_date, dt_time(23, 59))
                        else:
                            end_dt = datetime.combine(edit_end_date, edit_end_time)
                        
                        # Find and update the event in the dataframe
                        event_idx = st.session_state.events_df.index[st.session_state.events_df["id"] == selected_event["id"]][0]
                        st.session_state.events_df.loc[event_idx, "title"] = edit_title
                        st.session_state.events_df.loc[event_idx, "category"] = edit_category
                        st.session_state.events_df.loc[event_idx, "task_type"] = edit_task_type
                        st.session_state.events_df.loc[event_idx, "start"] = start_dt
                        st.session_state.events_df.loc[event_idx, "end"] = end_dt
                        st.session_state.events_df.loc[event_idx, "all_day"] = edit_all_day
                        st.session_state.events_df.loc[event_idx, "location"] = edit_location
                        st.session_state.events_df.loc[event_idx, "notes"] = edit_notes
                        st.session_state.events_df.loc[event_idx, "updated_at"] = _now_tzless()
                        
                        save_data(st.session_state.events_df, EVENTS_PATH)
                        st.session_state.editing_event = False
                        st.success("✏️ Event updated!")
                        st.rerun()
                    
                    if cancel_edit:
                        st.session_state.editing_event = False
                        st.rerun()
    else:
        st.info("📅 No events to manage yet. Create your first event above!")

# ---------- Time Tracker Tab ----------
with tab_tracker:
    section_header("⏱️ Where Does My Time Go?")
    st.markdown("*Curious about your daily time patterns?*")
    
    # Current timer status with LIVE CLOCK
    if st.session_state.timer_running:
        # Create a dramatic live timer display
        timer_container = st.empty()
        # Always-visible Stop button near the live clock
        stop_top = st.button("⏹️ Stop Timer", key="stop_timer_top", type="secondary")
        if stop_top:
            end_time = datetime.now()
            duration = end_time - st.session_state.timer_start
            duration_minutes = duration.total_seconds() / 60

            new_entry = {
                "id": generate_id(),
                "category": st.session_state.timer_category,
                "activity": st.session_state.timer_category,
                "start_time": st.session_state.timer_start,
                "end_time": end_time,
                "duration_minutes": duration_minutes,
                "notes": "",
                "date": date.today(),
                "frankl_reflection": ""
            }
            st.session_state.timetrack_df = pd.concat(
                [st.session_state.timetrack_df, pd.DataFrame([new_entry])],
                ignore_index=True,
            )
            save_data(st.session_state.timetrack_df, TIMETRACK_PATH)

            # Reset timer state
            st.session_state.timer_running = False
            st.session_state.timer_start = None
            st.session_state.timer_category = None

            st.success(f"Logged {duration_minutes:.1f} minutes")
            st.rerun()

        
        elapsed = datetime.now() - st.session_state.timer_start
        elapsed_seconds = int(elapsed.total_seconds())
        elapsed_minutes = elapsed_seconds // 60
        display_seconds = elapsed_seconds % 60
        elapsed_hours = elapsed_minutes // 60
        display_minutes = elapsed_minutes % 60
        
        # Color coding based on time elapsed
        if elapsed_minutes < 30:
            timer_color = "#00FF00"  # Green - just started
            pulse_color = "🟢"
        elif elapsed_minutes < 120:  # Less than 2 hours
            timer_color = "#FFA500"  # Orange - getting going
            pulse_color = "🟡"
        else:
            timer_color = "#FF4444"  # Red - long session
            pulse_color = "🔴"
        
        # Dramatic live clock display
        with timer_container.container():
            st.markdown(f"""
            <div style='
                background: linear-gradient(45deg, {timer_color}22, {timer_color}11);
                border: 2px solid {timer_color};
                border-radius: 15px;
                padding: 20px;
                text-align: center;
                margin: 10px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            '>
                <h2 style='color: {timer_color}; margin: 0; font-size: 24px;'>
                    ⏱️ TIMER ACTIVE: {st.session_state.timer_category}
                </h2>
                <div style='font-size: 48px; font-weight: bold; color: {timer_color}; margin: 10px 0; font-family: monospace;'>
                    {elapsed_hours:02d}:{display_minutes:02d}:{display_seconds:02d}
                </div>
                <p style='color: {timer_color}; font-size: 18px; margin: 5px 0;'>
                    {pulse_color} {elapsed_minutes} minutes and counting...
                </p>
                <p style='color: #666; font-size: 14px; margin: 0;'>
                    Started at {st.session_state.timer_start.strftime('%I:%M %p')}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Auto-refresh every second to update the clock
        import time
        time.sleep(1)
        st.rerun()
    
    # Timer controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Timer controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if not st.session_state.timer_running:
            st.info("⏱️ Ready to track some time?")
    
    with col2:
        if not st.session_state.timer_running:
            timer_category = st.selectbox("Activity", TIME_CATEGORIES, key="start_timer_category")
            if st.button("▶️ Start Timer", type="primary"):
                st.session_state.timer_running = True
                st.session_state.timer_start = datetime.now()
                st.session_state.timer_category = timer_category
                st.success(f"Started timer for {timer_category}")
                st.rerun()
        else:
            if st.button("⏹️ Stop Timer", type="secondary"):
                # Calculate duration and save
                end_time = datetime.now()
                duration = end_time - st.session_state.timer_start
                duration_minutes = duration.total_seconds() / 60
                
                new_entry = {
                    "id": generate_id(),
                    "category": st.session_state.timer_category,
                    "activity": st.session_state.timer_category,
                    "start_time": st.session_state.timer_start,
                    "end_time": end_time,
                    "duration_minutes": duration_minutes,
                    "notes": "",
                    "date": date.today(),
                    "frankl_reflection": ""
                }
                
                st.session_state.timetrack_df = pd.concat([
                    st.session_state.timetrack_df,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                save_data(st.session_state.timetrack_df, TIMETRACK_PATH)
                
                # Reset timer state
                st.session_state.timer_running = False
                st.session_state.timer_start = None
                st.session_state.timer_category = None
                
                st.success(f"Logged {duration_minutes:.1f} minutes")
                st.rerun()
    
    with col3:
        # Quick manual entry
        if st.button("➕ Quick Entry"):
            st.session_state.show_manual_entry = True
    
    # Manual time entry form
    if st.session_state.get("show_manual_entry", False):
        with st.form("manual_time_entry"):
            st.markdown("### ⏰ Manual Time Entry")
            
            entry_col1, entry_col2 = st.columns(2)
            with entry_col1:
                manual_category = st.selectbox("Activity Category", TIME_CATEGORIES)
                manual_activity = st.text_input("Specific Activity", placeholder="Throwing bowls, checking Instagram...")
                manual_date = st.date_input("Date", value=date.today())
            
            with entry_col2:
                manual_start = st.time_input("Start Time", value=dt_time(9, 0))
                manual_end = st.time_input("End Time", value=dt_time(10, 0))
                manual_notes = st.text_input("Notes", placeholder="What did you accomplish?")
            
            # Quick reflection for time entries
            frankl_time_reflection = st.text_area(
                "Looking back, how do you feel about how you spent this time?",
                placeholder="Was this time well spent? Would you do it differently next time?",
                height=60
            )
            
            form_col1, form_col2 = st.columns(2)
            with form_col1:
                if st.form_submit_button("💾 Log Time"):
                    start_dt = datetime.combine(manual_date, manual_start)
                    end_dt = datetime.combine(manual_date, manual_end)
                    duration_minutes = (end_dt - start_dt).total_seconds() / 60
                    
                    if duration_minutes > 0:
                        new_entry = {
                            "id": generate_id(),
                            "category": manual_category,
                            "activity": manual_activity if manual_activity.strip() else manual_category,
                            "start_time": start_dt,
                            "end_time": end_dt,
                            "duration_minutes": duration_minutes,
                            "notes": manual_notes.strip(),
                            "date": manual_date,
                            "frankl_reflection": frankl_time_reflection.strip()
                        }
                        
                        st.session_state.timetrack_df = pd.concat([
                            st.session_state.timetrack_df,
                            pd.DataFrame([new_entry])
                        ], ignore_index=True)
                        save_data(st.session_state.timetrack_df, TIMETRACK_PATH)
                        st.session_state.show_manual_entry = False
                        st.success(f"Logged {duration_minutes:.0f} minutes of {manual_category}")
                        st.rerun()
                    else:
                        st.error("End time must be after start time")
            
            with form_col2:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.show_manual_entry = False
                    st.rerun()
    
    # Today's time breakdown
    st.markdown("---")
    section_header("📊 Today's Breakdown")
    
    if not st.session_state.timetrack_df.empty:
        # Ensure proper date handling
        timetrack_df = st.session_state.timetrack_df.copy()
        if not timetrack_df["date"].empty:
            today_data = timetrack_df[
                pd.to_datetime(timetrack_df["date"]).dt.date == date.today()
            ]
        else:
            today_data = pd.DataFrame()
        
        if not today_data.empty:
            # Calculate time by category for today
            today_summary = today_data.groupby("category")["duration_minutes"].sum().sort_values(ascending=False)
            
            summary_col1, summary_col2 = st.columns(2)
            
            with summary_col1:
                st.markdown("**Time by Activity Today:**")
                total_tracked = today_summary.sum()
                
                for category, minutes in today_summary.items():
                    hours = minutes / 60
                    percentage = (minutes / total_tracked * 100) if total_tracked > 0 else 0
                    
                    # Color code based on category
                    if "Studio" in category or "Creative" in category:
                        color = "🟢"
                    elif "Social Media" in category or "Entertainment" in category:
                        color = "🔴"
                    elif "Sleep" in category or "Meals" in category:
                        color = "🟡"
                    else:
                        color = "⚪"
                    
                    st.markdown(f"{color} **{category}:** {hours:.1f}h ({percentage:.0f}%)")
                
                st.markdown(f"**Total Tracked:** {total_tracked/60:.1f} hours")
                st.caption(f"Untracked time: {24 - (total_tracked/60):.1f} hours")
            
            with summary_col2:
                st.markdown("**The Numbers Don't Lie:**")
                
                # Reality check calculations
                studio_time = today_summary.get("🏺 Studio Work", 0) + today_summary.get("🎨 Creative Planning", 0)
                distraction_time = today_summary.get("📱 Social Media", 0) + today_summary.get("📺 Entertainment", 0)
                
                if studio_time > 0:
                    st.success(f"🏺 **{studio_time/60:.1f} hours** on pottery/creative work")
                else:
                    st.info("🏺 **0 hours** on pottery today")
                
                if distraction_time > 0:
                    st.warning(f"📱 **{distraction_time/60:.1f} hours** on social media/entertainment")
                    
                    if studio_time > 0:
                        ratio = distraction_time / studio_time
                        if ratio > 2:
                            st.error(f"📊 Distractions won {ratio:.1f} to 1 today")
                        elif ratio > 1:
                            st.warning(f"📊 Distractions ahead {ratio:.1f}:1")
                        else:
                            st.success(f"💪 Pottery time wins!")
                
                # Gentle Frankl nudge (way less preachy)
                if studio_time < 60:  # Less than 1 hour
                    st.markdown("---")
                    st.markdown("**🤔 Just wondering:**")
                    st.markdown("*If this day repeated, would you want more studio time?*")
        else:
            st.info("⏱️ No time tracked today yet. Hit start on a timer above!")
    else:
        st.info("⏱️ No time data yet. Ready to see where your hours actually go?")
    
    # Weekly summary
    if not st.session_state.timetrack_df.empty:
        st.markdown("---")
        section_header("📈 This Week's Pattern")
        
        # Get this week's data - safer date handling
        week_start = date.today() - timedelta(days=date.today().weekday())
        timetrack_df = st.session_state.timetrack_df.copy()
        
        if not timetrack_df["date"].empty:
            week_data = timetrack_df[
                (pd.to_datetime(timetrack_df["date"]).dt.date >= week_start) & 
                (pd.to_datetime(timetrack_df["date"]).dt.date <= date.today())
            ]
        else:
            week_data = pd.DataFrame()
        
        if not week_data.empty:
            week_summary = week_data.groupby("category")["duration_minutes"].sum().sort_values(ascending=False)
            
            week_col1, week_col2 = st.columns(2)
            
            with week_col1:
                st.markdown("**Weekly Totals:**")
                for category, minutes in week_summary.items():
                    hours = minutes / 60
                    st.markdown(f"• **{category}:** {hours:.1f} hours")
            
            with week_col2:
                # Weekly insights
                studio_weekly = week_summary.get("🏺 Studio Work", 0) + week_summary.get("🎨 Creative Planning", 0)
                days_tracked = len(pd.to_datetime(week_data["date"]).dt.date.unique())
                
                st.markdown("**Weekly Insights:**")
                st.metric("🏺 Studio Hours This Week", f"{studio_weekly/60:.1f}")
                st.metric("📊 Days Tracked", days_tracked)
                
                if studio_weekly > 0:
                    avg_daily = studio_weekly / 7
                    st.caption(f"Average: {avg_daily/60:.1f} hours/day on pottery")
                
                # Gentler weekly insight
                if studio_weekly < 420:  # Less than 7 hours per week
                    st.info("💡 Less than 1 hour/day average on pottery this week")
        else:
            st.info("📊 Start tracking to see weekly patterns!")
    
    # Export time tracking data
    if not st.session_state.timetrack_df.empty:
        st.download_button(
            "📋 Export Time Data CSV",
            data=st.session_state.timetrack_df.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_time_tracking_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# ---------- Goals Tab ----------
with tab_goals:
    section_header("🎯 Intentional Goals")
    st.markdown("*Transform procrastination into purposeful action*")
    
    # Add new goal
    with st.expander("➕ Create New Goal", expanded=False):
        with st.form("add_goal_form"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                goal_title = st.text_input("Goal Title", placeholder="Master pulling handles")
                goal_description = st.text_area("Description", placeholder="What specifically do you want to achieve?", height=100)
                
                # Goal category
                goal_category = st.selectbox("Category", [
                    "Technical Skill", "Artistic Development", "Business Growth", 
                    "Studio Efficiency", "Personal Growth", "Community Engagement"
                ])
                
                # Tags for searchability
                goal_tags = st.text_input("Tags (comma-separated)", placeholder="handles, mugs, technique, practice")
                
            with col2:
                goal_priority = st.selectbox("Priority", ["🔴 High", "🟡 Medium", "🟢 Low"])
                target_date = st.date_input("Target Date", value=date.today() + timedelta(days=30))
                
            # Viktor Frankl integration
            st.markdown("### 🤔 The Deeper Why")
            frankl_why = st.text_area(
                "Why does this goal matter? What meaning will achieving it bring to your life?",
                placeholder="How does this goal connect to your larger purpose? What change will it make in the world?",
                height=80
            )
            
            time_awareness_note = st.text_area(
                "How does your finite time influence this goal's importance?",
                placeholder="Given your remaining days, why prioritize this over other possibilities?",
                height=60
            )
            
            submitted_goal = st.form_submit_button("Create Goal")
            
            if submitted_goal and goal_title.strip():
                new_goal = {
                    "id": generate_id(),
                    "title": goal_title.strip(),
                    "description": goal_description.strip(),
                    "category": goal_category,
                    "status": "Active",
                    "priority": goal_priority,
                    "created_date": date.today(),
                    "target_date": target_date,
                    "completed_date": None,
                    "progress_notes": "",
                    "frankl_why": frankl_why.strip(),
                    "time_awareness_note": time_awareness_note.strip(),
                    "linked_pieces": "",
                    "tags": goal_tags.strip()
                }
                
                st.session_state.goals_df = pd.concat([
                    st.session_state.goals_df,
                    pd.DataFrame([new_goal])
                ], ignore_index=True)
                save_data(st.session_state.goals_df, GOALS_PATH)
                st.success("🎯 Goal created!")
                st.rerun()
    
    # Display goals
    goals_df = st.session_state.goals_df.sort_values("created_date", ascending=False)
    
    if not goals_df.empty:
        # Goal filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.multiselect("Status", ["Active", "Completed", "On Hold"], default=["Active"])
        with col2:
            category_filter = st.multiselect("Category", goals_df["category"].unique().tolist())
        with col3:
            priority_filter = st.multiselect("Priority", ["🔴 High", "🟡 Medium", "🟢 Low"])
        
        # Apply filters
        filtered_goals = goals_df.copy()
        if status_filter:
            filtered_goals = filtered_goals[filtered_goals["status"].isin(status_filter)]
        if category_filter:
            filtered_goals = filtered_goals[filtered_goals["category"].isin(category_filter)]
        if priority_filter:
            filtered_goals = filtered_goals[filtered_goals["priority"].isin(priority_filter)]
            
        # Display goals
        for _, goal in filtered_goals.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{goal['title']}** {goal['priority']}")
                    st.markdown(goal["description"])
                    
                    if goal.get("frankl_why") and goal["frankl_why"].strip():
                        st.markdown("**Why it matters:**")
                        st.markdown(f"*{goal['frankl_why']}*")
                    
                    if goal.get("target_date") and pd.notna(goal["target_date"]):
                        days_remaining = (goal["target_date"].date() - date.today()).days
                        if days_remaining > 0:
                            st.caption(f"🗓️ Target: {goal['target_date'].strftime('%Y-%m-%d')} ({days_remaining} days remaining)")
                        elif days_remaining == 0:
                            st.caption("🎯 **Due TODAY!**")
                        else:
                            st.caption(f"⚠️ Overdue by {abs(days_remaining)} days")
                    
                    if goal.get("tags") and goal["tags"].strip():
                        tags_list = [tag.strip() for tag in goal["tags"].split(",") if tag.strip()]
                        st.caption("🏷️ " + " • ".join(tags_list))
                
                with col2:
                    st.caption(f"**{goal['category']}**")
                    st.caption(f"Status: {goal['status']}")
                    
                    # Quick actions
                    if goal["status"] != "Completed":
                        if st.button("✅ Mark Complete", key=f"complete_{goal['id']}"):
                            # Update goal status
                            idx = st.session_state.goals_df.index[st.session_state.goals_df["id"] == goal["id"]][0]
                            st.session_state.goals_df.loc[idx, "status"] = "Completed"
                            st.session_state.goals_df.loc[idx, "completed_date"] = date.today()
                            save_data(st.session_state.goals_df, GOALS_PATH)
                            st.success("🎉 Goal completed!")
                            st.rerun()
                    
                    if st.button("📝 Add Progress", key=f"progress_{goal['id']}"):
                        st.session_state[f"show_progress_{goal['id']}"] = True
                
                # Progress note form (conditional)
                if st.session_state.get(f"show_progress_{goal['id']}", False):
                    with st.form(f"progress_form_{goal['id']}"):
                        progress_note = st.text_area("Progress Note", placeholder="What progress have you made toward this goal?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Add Note"):
                                # Update goal with progress note
                                idx = st.session_state.goals_df.index[st.session_state.goals_df["id"] == goal["id"]][0]
                                existing_notes = st.session_state.goals_df.loc[idx, "progress_notes"]
                                new_notes = f"{existing_notes}\n\n{date.today()}: {progress_note}".strip()
                                st.session_state.goals_df.loc[idx, "progress_notes"] = new_notes
                                save_data(st.session_state.goals_df, GOALS_PATH)
                                st.session_state[f"show_progress_{goal['id']}"] = False
                                st.success("Progress noted!")
                                st.rerun()
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state[f"show_progress_{goal['id']}"] = False
                                st.rerun()
    else:
        st.info("🎯 No goals yet. Create your first intentional goal above!")
        st.markdown("**Remember:** Goals without deadlines are just wishes. Goals with deep 'why' become reality.")
    
    # Export goals data
    if not goals_df.empty:
        st.download_button(
            "📋 Export Goals CSV", 
            data=goals_df.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_goals_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

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
                
        # Export portfolio data
        st.download_button(
            "📋 Export Portfolio CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_portfolio_{date.today().isoformat()}.csv",
            mime="text/csv"
        )
    else:
        st.info("🏺 No finished pieces yet. Document your first piece above!")
        
    # Always show export option for template
    if st.session_state.portfolio_df.empty:
        template_df = pd.DataFrame(columns=[
            "title", "piece_type", "completion_date", "clay_body", "glaze_combo",
            "who_for", "what_for", "change_intended", "observations"
        ])
        st.download_button(
            "📄 Download Portfolio Template",
            data=template_df.to_csv(index=False).encode("utf-8"),
            file_name="pottery_portfolio_template.csv",
            mime="text/csv",
            help="Download a template to get started"
        )

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
                    
                    # Show philosophical reflections if they exist
                    if entry.get("frankl_reflection") and entry["frankl_reflection"].strip():
                        st.markdown("---")
                        st.markdown("**🤔 Second Life Reflection:**")
                        st.markdown(f"*{entry['frankl_reflection']}*")
                    
                    if entry.get("time_awareness_reflection") and entry["time_awareness_reflection"].strip():
                        st.markdown("**⏰ Time Awareness:**")
                        st.markdown(f"*{entry['time_awareness_reflection']}*")
                    
                    if entry.get("techniques_practiced"):
                        st.caption(f"🎨 Techniques: {entry['techniques_practiced']}")
                    if entry.get("materials_used"):
                        st.caption(f"🧱 Materials: {entry['materials_used']}")
                with col2:
                    st.caption(entry["entry_date"].strftime("%Y-%m-%d"))
                    st.markdown(entry["mood"])
    else:
        st.info("📝 Start your first studio journal entry above!")
        
    # Export journal data
    if not journal_df.empty:
        st.download_button(
            "📋 Export Journal CSV",
            data=journal_df.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_journal_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# ---------- Search Tab ----------
with tab_search:
    section_header("🔍 Search Everything")
    q = st.text_input("Search term", placeholder="mug, shino, Cone 6, Harford Fair, goal title")
    scope = st.multiselect(
        "Search areas",
        ["Events", "Journal", "Portfolio", "Goals", "Time Tracking"],
        default=["Events", "Journal", "Portfolio", "Goals"],
    )

    if q.strip():
        st.markdown(f"**Results for:** {q}")

        # Events
        if "Events" in scope and not st.session_state.events_df.empty:
            st.markdown("#### 📅 Events")
            _df = st.session_state.events_df.copy()
            mask = _df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
            hits = _df[mask].sort_values("start")
            if not hits.empty:
                render_agenda(hits)
            else:
                st.caption("No events found")
        
        # Journal
        if "Journal" in scope and not st.session_state.journal_df.empty:
            st.markdown("#### 📝 Journal Entries")
            _df = st.session_state.journal_df.copy()
            mask = _df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
            hits = _df[mask].sort_values("entry_date", ascending=False)
            if not hits.empty:
                for _, entry in hits.head(5).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{entry['title']}** - {entry['entry_date'].strftime('%Y-%m-%d')}")
                        st.markdown(entry["content"][:200] + "..." if len(entry["content"]) > 200 else entry["content"])
            else:
                st.caption("No journal entries found")
        
        # Portfolio
        if "Portfolio" in scope and not st.session_state.portfolio_df.empty:
            st.markdown("#### 🏺 Portfolio Pieces")
            _df = st.session_state.portfolio_df.copy()
            mask = _df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
            hits = _df[mask].sort_values("completion_date", ascending=False)
            if not hits.empty:
                for _, piece in hits.head(5).iterrows():
                    render_portfolio_piece(piece, show_full=False)
            else:
                st.caption("No portfolio pieces found")
        
        # Goals
        if "Goals" in scope and not st.session_state.goals_df.empty:
            st.markdown("#### 🎯 Goals")
            _df = st.session_state.goals_df.copy()
            mask = _df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
            hits = _df[mask].sort_values("created_date", ascending=False)
            if not hits.empty:
                for _, goal in hits.head(5).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{goal['title']}** {goal['priority']} - {goal['status']}")
                        st.markdown(goal["description"])
            else:
                st.caption("No goals found")
        
        # Time Tracking
        if "Time Tracking" in scope and not st.session_state.timetrack_df.empty:
            st.markdown("#### ⏱️ Time Entries")
            _df = st.session_state.timetrack_df.copy()
            mask = _df.astype(str).apply(lambda c: c.str.contains(q, case=False, na=False)).any(axis=1)
            hits = _df[mask].sort_values("start_time", ascending=False)
            if not hits.empty:
                for _, entry in hits.head(5).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{entry['category']}** - {entry['activity']}")
                        st.caption(f"{entry['start_time'].strftime('%Y-%m-%d %I:%M %p')} ({entry['duration_minutes']:.0f} minutes)")
                        if entry.get("notes"):
                            st.caption(entry["notes"])
            else:
                st.caption("No time entries found")

# Studio Tab
with tab_studio:
    section_header("🎨 Studio Schedule")
    studio_df = st.session_state.events_df[st.session_state.events_df["category"] == "Studio"]
    filtered_studio = filter_events_df(studio_df)
    render_agenda(filtered_studio)
    
    if not filtered_studio.empty:
        st.download_button(
            "📋 Export Studio Events CSV",
            data=filtered_studio.to_csv(index=False).encode("utf-8"),
            file_name=f"studio_schedule_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# Community Tab
with tab_comm:
    section_header("🤝 Community Events")
    comm_df = st.session_state.events_df[st.session_state.events_df["category"] == "Community"]
    filtered_comm = filter_events_df(comm_df)
    render_agenda(filtered_comm)
    
    if not filtered_comm.empty:
        st.download_button(
            "📋 Export Community Events CSV",
            data=filtered_comm.to_csv(index=False).encode("utf-8"),
            file_name=f"community_events_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# Public Tab
with tab_public:
    section_header("🌍 Public Events")
    public_df = st.session_state.events_df[st.session_state.events_df["category"] == "Public"]
    filtered_public = filter_events_df(public_df)
    render_agenda(filtered_public)
    
    if not filtered_public.empty:
        st.download_button(
            "📋 Export Public Events CSV",
            data=filtered_public.to_csv(index=False).encode("utf-8"),
            file_name=f"public_events_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# All Events Tab
with tab_all:
    section_header("📋 All Events")
    filtered_all = filter_events_df(st.session_state.events_df)
    render_agenda(filtered_all)
    
    if not filtered_all.empty:
        st.download_button(
            "📋 Export All Events CSV",
            data=filtered_all.to_csv(index=False).encode("utf-8"),
            file_name=f"pottery_calendar_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

# ---------- About Tab ----------
with tab_about:
    section_header("ℹ️ About Pottery Maker Manager")
    
    # Hero section
    st.markdown(f"""
    <div style='
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
    '>
        <h1 style='margin: 0; font-size: 2.5em;'>🏺 Pottery Maker Manager</h1>
        <p style='margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;'>
            Complete studio management for intentional makers
        </p>
        <p style='margin: 5px 0 0 0; opacity: 0.7;'>
            Version {APP_VERSION} • Built with intention and clay dust
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # What makes this different
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 **Why This App Exists**")
        st.markdown("""
        Most calendar apps treat your time like it's infinite. Most portfolio trackers ignore the deeper questions. 
        Most productivity apps forget that creativity and meaning matter more than mere efficiency.
        
        **This app is different.** It's built on two foundational ideas:
        
        **1. Time Scarcity Creates Intentionality**  
        When you remember that your days are numbered, every studio session becomes precious. The time awareness features help you make choices that align with what truly matters.
        
        **2. The Big Questions Drive Better Work**  
        Instead of just tracking *what* you made, we ask *why* it matters. Who's it for? What change are you trying to make? These questions transform craft into purpose.
        """)
    
    with col2:
        st.markdown("### 🧠 **Philosophical Foundation**")
        st.markdown("""
        This app draws inspiration from **Viktor Frankl's logotherapy** - the idea that humans are primarily driven by the search for meaning. Frankl believed that when we understand our "why," we can endure any "how."
        
        **In pottery terms:** When you know why you're throwing that mug (to bring joy to someone's morning ritual) or why you're perfecting that glaze (to master something beautiful), the long hours of practice become purposeful rather than tedious.
        
        The reflection prompts throughout the app are designed to help you connect your daily studio work to your larger sense of purpose and meaning.
        """)
    
    # Feature overview
    st.markdown("---")
    st.markdown("### 🛠️ **What You Can Do**")
    
    # Feature grid
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        **📅 Smart Calendar**
        - Multiple view modes (Month, Week, Day, Year)
        - Studio, Community, and Public event categories
        - Recurring events with flexible patterns
        - Quick navigation and filtering
        
        **⏱️ Time Awareness Tracking**
        - Live timer with visual feedback
        - Reality-check insights on how you spend time
        - Weekly patterns and studio time analysis
        - Gentle nudges toward intentional choices
        """)
    
    with feature_col2:
        st.markdown("""
        **🏺 Professional Portfolio**
        - Document finished pieces with photos
        - Track technical details and firing schedules
        - Assess design elements and success ratings
        - The Big Questions: Who, What, Why framework
        
        **🎯 Meaningful Goals**
        - Connect goals to deeper purpose ("why")
        - Time-scarcity awareness integration
        - Progress tracking with reflection prompts
        - Categories from technical to personal growth
        """)
    
    with feature_col3:
        st.markdown("""
        **📝 Reflective Journal**
        - Daily studio reflections and insights
        - Mood tracking and technique documentation
        - Viktor Frankl-inspired reflection prompts
        - Link entries to calendar events
        
        **🔍 Universal Search**
        - Search across all data types
        - Find glazes, techniques, goals, and memories
        - Cross-reference your pottery journey
        - Export any data to CSV format
        """)
    
    # The philosophy section
    st.markdown("---")
    st.markdown("### 🤔 **The Deeper Questions**")
    
    philosophy_col1, philosophy_col2 = st.columns(2)
    
    with philosophy_col1:
        st.markdown("""
        **Traditional pottery tracking asks:**
        - What did you make?
        - What clay and glaze did you use?
        - What temperature did you fire to?
        
        **This app also asks:**
        - Who is this piece for, really?
        - What change are you trying to make in the world?
        - If you only had one year left, would you still make this?
        - How does this work connect to your larger purpose?
        """)
    
    with philosophy_col2:
        st.markdown("""
        **The result?** 
        Your pottery practice becomes more than just making objects. It becomes a practice of intentionality, meaning-making, and conscious creation.
        
        **Your portfolio** becomes a record not just of what you made, but why it mattered.
        
        **Your time tracking** becomes awareness of how your finite days are actually spent.
        
        **Your goals** become connected to your deepest values and sense of purpose.
        """)
    
    # Technical details
    st.markdown("---")
    st.markdown("### ⚙️ **Technical Details**")
    
    tech_col1, tech_col2 = st.columns(2)
    
    with tech_col1:
        st.markdown("""
        **Built With:**
        - Python 3.8+
        - Streamlit for the web interface
        - Pandas for data management
        - PIL for image handling
        - dateutil for calendar calculations
        
        **Data Storage:**
        - All data stored locally in CSV files
        - Images stored in local `data/images` folder
        - No cloud dependencies or privacy concerns
        - Full data ownership and portability
        """)
    
    with tech_col2:
        st.markdown("""
        **Features:**
        - Responsive design that works on mobile and desktop
        - Real-time timer with live updates
        - Comprehensive export functionality
        - Professional portfolio documentation
        - Philosophical reflection integration
        
        **File Structure:**
        ```
        data/
        ├── events.csv
        ├── journal_entries.csv
        ├── finished_works.csv
        ├── goals.csv
        ├── time_tracking.csv
        └── images/
        ```
        """)
    
    # Getting started
    st.markdown("---")
    st.markdown("### 🚀 **Getting Started**")
    
    start_col1, start_col2 = st.columns(2)
    
    with start_col1:
        st.markdown("""
        **For New Users:**
        1. Start with the **📅 Calendar** tab - schedule your next studio session
        2. Try the **⏱️ Time Tracker** - see where your time actually goes
        3. Set your first **🎯 Goal** - but include the deeper "why"
        4. Document a finished piece in **🏺 Portfolio** - answer the big questions
        5. Reflect in the **📝 Journal** about your studio practice
        
        **Remember:** This isn't just about productivity. It's about intentionality.
        """)
    
    with start_col2:
        st.markdown("""
        **Power User Tips:**
        - Use the **⏰ Time Awareness** sidebar to calculate your remaining creative days
        - Link calendar events to portfolio pieces and journal entries
        - Export your data regularly to create backups
        - Use the **🔍 Search** tab to find patterns in your work
        - Set recurring studio sessions to build consistent practice
        
        **The goal isn't to track everything. It's to track what matters.**
        """)
    
    # Footer with inspiration
    st.markdown("---")
    st.markdown("""
    <div style='
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-top: 20px;
    '>
        <p style='margin: 0; font-style: italic; color: #666;'>
            "Those who have a 'why' to live, can bear with almost any 'how'."<br>
            — Viktor Frankl
        </p>
        <p style='margin: 10px 0 0 0; color: #666; font-size: 0.9em;'>
            May your pottery practice be filled with intention, meaning, and beautiful imperfection.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Version and credits
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"**Version:** {APP_VERSION}")
        st.caption("**Created:** 2024")
    
    with col2:
        st.caption("**Philosophy:** Viktor Frankl's Logotherapy")
        st.caption("**Approach:** Time Scarcity + Meaning")
    
    with col3:
        st.caption("**For:** Intentional makers and creators")
        st.caption("**With:** Clay dust and purpose")
