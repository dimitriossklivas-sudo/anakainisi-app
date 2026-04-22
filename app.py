import base64
import io
import uuid
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Renovation Manager V5.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(212,175,55,0.12), transparent 24%),
            radial-gradient(circle at bottom right, rgba(120,90,40,0.06), transparent 18%),
            linear-gradient(180deg, #fbf6ee 0%, #f4ecdf 100%);
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    .hero {
        background: linear-gradient(135deg, #3f2f22 0%, #5a4330 50%, #7a5a3d 100%);
        color: #fffaf2;
        padding: 30px 32px;
        border-radius: 26px;
        margin-bottom: 20px;
        box-shadow: 0 18px 40px rgba(62, 45, 28, 0.24);
        border: 1px solid rgba(255,255,255,0.06);
        position: relative;
        overflow: hidden;
    }

    .hero::after {
        content: "Σκλίβας Δημήτριος";
        position: absolute;
        right: 24px;
        bottom: 10px;
        font-size: 1rem;
        opacity: 0.16;
        letter-spacing: 2px;
        font-weight: 700;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.6rem;
        line-height: 1.05;
    }

    .hero p {
        margin: 10px 0 0 0;
        color: rgba(255,250,242,0.88);
        font-size: 1rem;
    }

    .mini-card {
        background: rgba(255, 250, 242, 0.92);
        border: 1px solid rgba(90, 67, 48, 0.08);
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(90, 67, 48, 0.06);
        margin-bottom: 14px;
    }

    .section-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #4c3826;
    }

    .maker {
        margin-top: 24px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(255,250,242,0.88);
        border: 1px solid rgba(90,67,48,0.08);
        color: #5a4330;
        font-size: 0.95rem;
    }

    .gallery-note {
        padding: 10px 12px;
        background: rgba(255,248,238,0.95);
        border-radius: 12px;
        border: 1px solid rgba(90,67,48,0.07);
        margin-top: 8px;
        margin-bottom: 12px;
    }

    .room-badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        background: #eadcc7;
        color: #4c3826;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-bottom: 8px;
    }

    .watermark-box {
        position: relative;
        overflow: hidden;
    }

    .watermark-box::after {
        content: "Σκλίβας Δημήτριος";
        position: absolute;
        right: 12px;
        bottom: 8px;
        font-size: 0.85rem;
        opacity: 0.13;
        font-weight: 700;
        letter-spacing: 1px;
        color: #5a4330;
        pointer-events: none;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,250,242,0.98);
        border-radius: 18px;
        padding: 14px;
        box-shadow: 0 10px 24px rgba(90,67,48,0.08);
        border-top: 4px solid #c9a96b;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f3e8d9 0%, #efe1cd 100%);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255,250,242,0.9);
        border-radius: 12px;
        padding: 8px 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🏗️ Renovation Manager V5.2</h1>
        <p>Οικονομική παρακολούθηση, gallery προόδου, before/after και οπτικό dashboard ανακαίνισης.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

SHEET_EXPENSES = "Expenses"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "📋 Εργασίες",
    "💼 Προσφορές",
    "📸 Gallery",
    "📊 Αναλύσεις",
    "🏦 Δάνειο",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
TASK_COLUMNS = ["_id", "Εργασία", "Κατάσταση", "Κόστος", "Προτεραιότητα", "Ανάθεση", "Σημειώσεις"]
OFFER_COLUMNS = ["_id", "Πάροχος", "Περιγραφή", "Ποσό", "Κατηγορία", "Σημειώσεις"]
GALLERY_COLUMNS = ["_id", "Χώρος", "Τίτλος", "Τύπος", "Image_URL", "Image_Data", "Σημειώσεις"]

EXPENSE_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Κουφώματα", "Μπάνιο", "Άλλο"]
EXPENSE_TYPES = ["Αμοιβή", "Υλικά"]
PAYERS = ["Εγώ", "Πατέρας", "Κοινό", "Άλλο"]

TASK_STATUSES = ["To Do", "Doing", "Done"]
TASK_PRIORITIES = ["Χαμηλή", "Μεσαία", "Υψηλή"]

OFFER_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Μπάνιο", "Άλλο"]

ROOMS = ["Κουζίνα", "Μπάνιο", "Σαλόνι", "Υπνοδωμάτιο", "Μπαλκόνι", "Διάδρομος", "Άλλο"]
IMAGE_TYPES = ["Before", "After", "Progress", "Material"]

PLOTLY_TEMPLATE = "plotly_white"
CHART_COLORS = ["#c9a96b", "#6b4f3a", "#b07d4f", "#8d6e63", "#a1887f", "#d4af37", "#7b5e57"]


@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


def empty_df(columns):
    return pd.DataFrame(columns=columns)


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return empty_df(columns)
    fixed = df.copy()
    for col in columns:
        if col not in fixed.columns:
            fixed[col] = ""
    return fixed[columns]


def normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    fixed = df.copy()
    if "_id" not in fixed.columns:
        fixed["_id"] = ""
    fixed["_id"] = fixed["_id"].astype(str)
    missing = fixed["_id"].isin(["", "nan", "None"])
    if missing.any():
        fixed.loc[missing, "_id"] = [str(uuid.uuid4())[:8] for _ in range(missing.sum())]
    return fixed


def safe_read(sheet_name: str, columns: list[str]) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return empty_df(columns)
        df = df.dropna(how="all")
        df = ensure_columns(df, columns)
        df = normalize_ids(df)
        return df
    except Exception:
        return empty_df(columns)


def safe_write(sheet_name: str, df: pd.DataFrame) -> bool:
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης στο '{sheet_name}': {type(e).__name__} - {e}")
        return False


def append_row(df: pd.DataFrame, row_data: dict, columns: list[str]) -> pd.DataFrame:
    row_data["_id"] = str(uuid.uuid4())[:8]
    current = ensure_columns(df, columns)
    new_row = ensure_columns(pd.DataFrame([row_data]), columns)
    return pd.concat([current, new_row], ignore_index=True)


def delete_row_by_id(df: pd.DataFrame, row_id: str) -> pd.DataFrame:
    if df.empty:
        return df
    updated = df[df["_id"].astype(str) != str(row_id)].copy()
    return updated.reset_index(drop=True)


def money_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def parse_date_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype="datetime64[ns]")
    return pd.to_datetime(df[col], errors="coerce")


def show_table(df: pd.DataFrame, hide_id: bool = True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return
    display_df = df.copy()
    if hide_id and "_id" in display_df.columns:
        display_df = display_df.drop(columns=["_id"])
    st.dataframe(display_df, use_container_width=True)


def format_currency(value) -> str:
    try:
        return f"{float(value):,.2f} €"
    except Exception:
        return "0.00 €"


def make_bar_chart(df: pd.DataFrame, x: str, y: str, title: str):
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=x,
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=55, b=10), height=360)
    return fig


def make_donut_chart(df: pd.DataFrame, names: str, values: str, title: str):
    fig = px.pie(
        df,
        names=names,
        values=values,
        hole=0.58,
        title=title,
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), height=360)
    return fig


def card_start(title: str):
    st.markdown(
        f'<div class="mini-card watermark-box"><div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def safe_text(value, fallback=""):
    if pd.isna(value):
        return fallback
    return str(value)


def image_to_base64(uploaded_file, max_size=(1400, 1400), quality=74) -> str:
    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail(max_size)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def image_source_from_row(row: pd.Series):
    image_url = safe_text(row.get("Image_URL", ""))
    image_data = safe_text(row.get("Image_Data", ""))
    if image_url:
        return image_url
    if image_data:
        return f"data:image/jpeg;base64,{image_data}"
    return None


def room_progress_summary(df_gal: pd.DataFrame) -> pd.DataFrame:
    if df_gal.empty:
        return pd.DataFrame(columns=["Χώρος", "Πρόοδος"])
    rows = []
    for room in sorted(df_gal["Χώρος"].dropna().astype(str).unique()):
        room_df = df_gal[df_gal["Χώρος"] == room]
        before_count = len(room_df[room_df["Τύπος"] == "Before"])
        after_count = len(room_df[room_df["Τύπος"] == "After"])
        progress_count = len(room_df[room_df["Τύπος"] == "Progress"])
        material_count = len(room_df[room_df["Τύπος"] == "Material"])
        score = min(100, after_count * 55 + progress_count * 20 + material_count * 10 + before_count * 5)
        rows.append({"Χώρος": room, "Πρόοδος": score})
    return pd.DataFrame(rows)


df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)


def render_dashboard(df_exp: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame, df_gal: pd.DataFrame):
    st.subheader("🏠 Dashboard")

    budget = st.number_input("💼 Συνολικό Budget (€)", min_value=0.0, value=30000.0, step=1000.0)
    spent = money_series(df_exp, "Ποσό").sum()
    remaining = budget - spent
    usage = (spent / budget * 100) if budget > 0 else 0.0

    tasks_total = len(df_task)
    tasks_done = int((df_task["Κατάσταση"] == "Done").sum()) if not df_task.empty else 0
    tasks_doing = int((df_task["Κατάσταση"] == "Doing").sum()) if not df_task.empty else 0

    best_offer = money_series(df_off, "Ποσό").min() if not df_off.empty else 0.0
    best_offer_display = format_currency(best_offer) if best_offer > 0 else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Συνολικά Έξοδα", format_currency(spent))
    c2.metric("📉 Υπόλοιπο", format_currency(remaining))
    c3.metric("📊 Χρήση Budget", f"{usage:.1f}%")
    c4.metric("🏆 Καλύτερη Προσφορά", best_offer_display)

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("📋 Σύνολο Εργασιών", tasks_total)
    c6.metric("🛠️ Σε Εξέλιξη", tasks_doing)
    c7.metric("✅ Ολοκληρωμένες", tasks_done)
    c8.metric("📸 Φωτογραφίες", len(df_gal))

    st.progress(min(max(usage / 100, 0.0), 1.0))
    if usage > 100:
        st.error("Το budget έχει ξεπεραστεί.")
    elif usage > 80:
        st.warning("Το budget πλησιάζει το όριο.")
    else:
        st.success("Το budget είναι σε ελεγχόμενο επίπεδο.")

    top_left, top_right = st.columns([1.2, 1])

    with top_left:
        card_start("Visual Progress")
        if not df_gal.empty:
            progress_imgs = df_gal[df_gal["Τύπος"].isin(["Progress", "After", "Before"])].copy()
            if not progress_imgs.empty:
                latest = progress_imgs.tail(1).iloc[0]
                src = image_source_from_row(latest)
                if src:
                    st.image(src, use_container_width=True)
                st.markdown(
                    f"""
                    <div class="gallery-note">
                    <strong>{safe_text(latest["Χώρος"])}</strong><br>
                    {safe_text(latest["Τίτλος"])}<br>
                    <small>{safe_text(latest["Σημειώσεις"])}</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.info("Δεν υπάρχουν φωτογραφίες προόδου.")
        else:
            st.info("Δεν υπάρχουν φωτογραφίες.")
        card_end()

    with top_right:
        card_start("Έξοδα ανά Κατηγορία")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            by_cat = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().sort_values("Ποσό", ascending=False)
            if not by_cat.empty:
                st.plotly_chart(make_bar_chart(by_cat, "Κατηγορία", "Ποσό", "Κατανομή εξόδων"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν έξοδα.")
        card_end()

    row1, row2, row3 = st.columns(3)

    with row1:
        card_start("Αμοιβή / Υλικά")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            by_type = temp.groupby("Είδος", as_index=False)["Ποσό"].sum()
            if not by_type.empty:
                st.plotly_chart(make_donut_chart(by_type, "Είδος", "Ποσό", "Ανάλυση δαπανών"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα.")
        card_end()

    with row2:
        card_start("Πρόοδος ανά Χώρο")
        room_summary = room_progress_summary(df_gal)
        if not room_summary.empty:
            st.dataframe(room_summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(room_summary, "Χώρος", "Πρόοδος", "Οπτική πρόοδος"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν ακόμα στοιχεία gallery.")
        card_end()

    with row3:
        card_start("Πρόσφατες Εικόνες")
        if not df_gal.empty:
            preview = df_gal.tail(3)
            for _, row in preview.iterrows():
                src = image_source_from_row(row)
                if src:
                    st.image(src, use_container_width=True)
                    st.caption(f"{safe_text(row['Χώρος'])} - {safe_text(row['Τίτλος'])}")
        else:
            st.info("Δεν υπάρχουν εικόνες.")
        card_end()


def render_expenses(df_exp: pd.DataFrame):
    st.subheader("💰 Έξοδα")
    with st.expander("➕ Νέο έξοδο"):
        with st.form("expense_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                expense_date = st.date_input("Ημερομηνία")
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
            with c2:
                expense_type = st.selectbox("Είδος", EXPENSE_TYPES)
                payer = st.selectbox("Πληρωτής", PAYERS)
            with c3:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση"):
                updated_df = append_row(
                    df_exp,
                    {
                        "Ημερομηνία": str(expense_date),
                        "Κατηγορία": category,
                        "Είδος": expense_type,
                        "Ποσό": amount,
                        "Πληρωτής": payer,
                        "Σημειώσεις": notes.strip(),
                    },
                    EXPENSE_COLUMNS,
                )
                if safe_write(SHEET_EXPENSES, updated_df):
                    st.success("Το έξοδο αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_exp)


def render_tasks(df_task: pd.DataFrame):
    st.subheader("📋 Εργασίες")
    with st.expander("➕ Νέα εργασία"):
        with st.form("task_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                task_name = st.text_input("Εργασία")
                status = st.selectbox("Κατάσταση", TASK_STATUSES)
            with c2:
                cost = st.number_input("Κόστος (€)", min_value=0.0, step=10.0)
                priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES)
            with c3:
                assignee = st.text_input("Ανάθεση")
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση") and task_name.strip():
                updated_df = append_row(
                    df_task,
                    {
                        "Εργασία": task_name.strip(),
                        "Κατάσταση": status,
                        "Κόστος": cost,
                        "Προτεραιότητα": priority,
                        "Ανάθεση": assignee.strip(),
                        "Σημειώσεις": notes.strip(),
                    },
                    TASK_COLUMNS,
                )
                if safe_write(SHEET_TASKS, updated_df):
                    st.success("Η εργασία αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_task)


def render_offers(df_off: pd.DataFrame):
    st.subheader("💼 Προσφορές")
    with st.expander("➕ Νέα προσφορά"):
        with st.form("offer_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                provider = st.text_input("Πάροχος")
                category = st.selectbox("Κατηγορία", OFFER_CATEGORIES)
            with c2:
                description = st.text_input("Περιγραφή")
            with c3:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση") and provider.strip():
                updated_df = append_row(
                    df_off,
                    {
                        "Πάροχος": provider.strip(),
                        "Περιγραφή": description.strip(),
                        "Ποσό": amount,
                        "Κατηγορία": category,
                        "Σημειώσεις": notes.strip(),
                    },
                    OFFER_COLUMNS,
                )
                if safe_write(SHEET_OFFERS, updated_df):
                    st.success("Η προσφορά αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_off)


def render_gallery(df_gal: pd.DataFrame):
    st.subheader("📸 Gallery")

    with st.expander("➕ Νέα εικόνα", expanded=False):
        with st.form("gallery_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                room = st.selectbox("Χώρος", ROOMS)
            with c2:
                title = st.text_input("Τίτλος")
            with c3:
                image_type = st.selectbox("Τύπος", IMAGE_TYPES)

            uploaded_image = st.file_uploader("Ανέβασε εικόνα", type=["png", "jpg", "jpeg", "webp"], key="gallery_upload")
            image_url = st.text_input("ή Image URL")
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση εικόνας"):
                image_data = ""
                final_url = image_url.strip()

                if uploaded_image is not None:
                    try:
                        image_data = image_to_base64(uploaded_image)
                    except Exception as e:
                        st.error(f"Σφάλμα επεξεργασίας εικόνας: {e}")
                        st.stop()

                if not final_url and not image_data:
                    st.warning("Βάλε είτε upload εικόνας είτε Image URL.")
                else:
                    updated_df = append_row(
                        df_gal,
                        {
                            "Χώρος": room,
                            "Τίτλος": title.strip(),
                            "Τύπος": image_type,
                            "Image_URL": final_url,
                            "Image_Data": image_data,
                            "Σημειώσεις": notes.strip(),
                        },
                        GALLERY_COLUMNS,
                    )
                    if safe_write(SHEET_GALLERY, updated_df):
                        st.success("Η εικόνα αποθηκεύτηκε.")
                        st.rerun()

    if df_gal.empty:
        st.info("Δεν υπάρχουν εικόνες ακόμα.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        room_filter = st.selectbox("Φίλτρο χώρου", ["Όλοι"] + ROOMS)
    with c2:
        type_filter = st.selectbox("Φίλτρο τύπου", ["Όλα"] + IMAGE_TYPES)
    with c3:
        slideshow_mode = st.checkbox("Slideshow mode")

    filtered = df_gal.copy()
    if room_filter != "Όλοι":
        filtered = filtered[filtered["Χώρος"] == room_filter]
    if type_filter != "Όλα":
        filtered = filtered[filtered["Τύπος"] == type_filter]

    room_summary = room_progress_summary(filtered)
    if not room_summary.empty:
        st.markdown("### Rooms")
        for _, row in room_summary.iterrows():
            st.markdown(
                f'<span class="room-badge">{safe_text(row["Χώρος"])}: {int(row["Πρόοδος"])}%</span>',
                unsafe_allow_html=True,
            )

    tabs = st.tabs(["Gallery Grid", "Before / After", "Slideshow", "Διαχείριση", "Δεδομένα"])

    with tabs[0]:
        if filtered.empty:
            st.info("Δεν βρέθηκαν εικόνες με αυτά τα φίλτρα.")
        else:
            cols = st.columns(3)
            for idx, (_, row) in enumerate(filtered.iterrows()):
                with cols[idx % 3]:
                    src = image_source_from_row(row)
                    if src:
                        st.image(src, use_container_width=True)
                    st.markdown(
                        f"""
                        <div class="gallery-note">
                        <strong>{safe_text(row["Τίτλος"])}</strong><br>
                        Χώρος: {safe_text(row["Χώρος"])}<br>
                        Τύπος: {safe_text(row["Τύπος"])}<br>
                        <small>{safe_text(row["Σημειώσεις"])}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tabs[1]:
        room_options = sorted(filtered["Χώρος"].dropna().astype(str).unique().tolist())
        if not room_options:
            st.info("Δεν υπάρχουν διαθέσιμες εικόνες before/after.")
        else:
            selected_room = st.selectbox("Επιλογή χώρου", room_options, key="before_after_room")
            room_df = filtered[filtered["Χώρος"] == selected_room]

            before_df = room_df[room_df["Τύπος"] == "Before"]
            after_df = room_df[room_df["Τύπος"] == "After"]

            col_before, col_after = st.columns(2)

            with col_before:
                st.markdown("### Before")
                if not before_df.empty:
                    before_row = before_df.tail(1).iloc[0]
                    src = image_source_from_row(before_row)
                    if src:
                        st.image(src, use_container_width=True)
                    st.caption(safe_text(before_row["Τίτλος"]))
                else:
                    st.info("Δεν υπάρχει εικόνα Before.")

            with col_after:
                st.markdown("### After")
                if not after_df.empty:
                    after_row = after_df.tail(1).iloc[0]
                    src = image_source_from_row(after_row)
                    if src:
                        st.image(src, use_container_width=True)
                    st.caption(safe_text(after_row["Τίτλος"]))
                else:
                    st.info("Δεν υπάρχει εικόνα After.")

    with tabs[2]:
        if filtered.empty:
            st.info("Δεν υπάρχουν εικόνες για slideshow.")
        else:
            img_index = st.slider("Επιλογή εικόνας", 0, len(filtered) - 1, 0)
            row = filtered.reset_index(drop=True).iloc[img_index]
            src = image_source_from_row(row)
            if src:
                st.image(src, use_container_width=True)
            st.markdown(
                f"""
                <div class="gallery-note">
                <strong>{safe_text(row["Τίτλος"])}</strong><br>
                Χώρος: {safe_text(row["Χώρος"])}<br>
                Τύπος: {safe_text(row["Τύπος"])}<br>
                <small>{safe_text(row["Σημειώσεις"])}</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if slideshow_mode:
                st.info("Το slideshow mode είναι ενεργό. Μετακίνησε τον slider για γρήγορη προβολή διαφανειών.")

    with tabs[3]:
        labels = {
            safe_text(row["_id"]): f"{safe_text(row['Χώρος'])} | {safe_text(row['Τίτλος'])} | {safe_text(row['Τύπος'])}"
            for _, row in filtered.iterrows()
        }
        if labels:
            selected_id = st.selectbox(
                "Επιλογή εικόνας για διαγραφή",
                options=list(labels.keys()),
                format_func=lambda rid: labels.get(rid, "Άγνωστη εικόνα"),
            )
            if st.button("🗑️ Διαγραφή εικόνας"):
                updated_df = delete_row_by_id(df_gal, selected_id)
                if safe_write(SHEET_GALLERY, updated_df):
                    st.success("Η εικόνα διαγράφηκε.")
                    st.rerun()
        else:
            st.info("Δεν υπάρχουν εικόνες για διαχείριση.")

    with tabs[4]:
        show_table(filtered)


def render_analytics(df_exp: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame):
    st.subheader("📊 Αναλύσεις")

    left, right = st.columns(2)

    with left:
        card_start("Έξοδα ανά Κατηγορία")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().sort_values("Ποσό", ascending=False)
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατηγορία", "Ποσό", "Σύνολο ανά κατηγορία"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα.")
        card_end()

    with right:
        card_start("Εργασίες ανά Κατάσταση")
        if not df_task.empty:
            summary = df_task["Κατάσταση"].value_counts().rename_axis("Κατάσταση").reset_index(name="Πλήθος")
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατάσταση", "Πλήθος", "Κατανομή εργασιών"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα.")
        card_end()


def render_loan():
    st.subheader("🏦 Υπολογιστής Δόσης")
    principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, value=10000.0)
    annual_rate = st.number_input("Ετήσιο Επιτόκιο (%)", min_value=0.0, value=4.5)
    months = st.number_input("Μήνες Εξόφλησης", min_value=1, value=60)

    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        installment = principal / months
    else:
        installment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    total_paid = installment * months
    interest_paid = total_paid - principal

    c1, c2, c3 = st.columns(3)
    c1.metric("Μηνιαία Δόση", format_currency(installment))
    c2.metric("Συνολικό Πληρωτέο", format_currency(total_paid))
    c3.metric("Συνολικοί Τόκοι", format_currency(interest_paid))


def render_calculator():
    st.subheader("🧮 Calculator")
    mode = st.selectbox("Τύπος υπολογισμού", ["Πλακάκια", "Χρώματα"])

    if mode == "Πλακάκια":
        area = st.number_input("m² Επιφάνειας", min_value=0.0, value=10.0)
        width = st.number_input("Πλάτος πλακιδίου (cm)", min_value=0.1, value=60.0)
        height = st.number_input("Ύψος πλακιδίου (cm)", min_value=0.1, value=120.0)
        waste = st.number_input("Ποσοστό φύρας (%)", min_value=0.0, value=10.0)
        tile_area = (width * height) / 10000
        pieces = area / tile_area if tile_area > 0 else 0
        pieces = int(pieces * (1 + waste / 100)) + 1
        st.metric("Τεμάχια που θα χρειαστείς", pieces)

    elif mode == "Χρώματα":
        wall_area = st.number_input("m² Τοίχου", min_value=0.0, value=50.0)
        coats = st.number_input("Χέρια", min_value=1, value=2)
        coverage = st.number_input("Απόδοση (m²/λίτρο)", min_value=1.0, value=12.0)
        liters = (wall_area * coats) / coverage
        st.metric("Λίτρα χρώματος", f"{liters:.1f} L")


st.sidebar.markdown("### Πλοήγηση")
menu = st.sidebar.radio("Μενού", MENU_OPTIONS)
st.sidebar.markdown("---")
st.sidebar.caption(f"Τελευταία ενημέρωση: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("Κατασκευαστής εφαρμογής: Σκλίβας Δημήτριος")

if menu == "🏠 Dashboard":
    render_dashboard(df_expenses, df_tasks, df_offers, df_gallery)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "📸 Gallery":
    render_gallery(df_gallery)
elif menu == "📊 Αναλύσεις":
    render_analytics(df_expenses, df_tasks, df_offers)
elif menu == "🏦 Δάνειο":
    render_loan()
elif menu == "🧮 Calculator":
    render_calculator()

st.markdown(
    """
    <div class="maker">
        Κατασκευαστής εφαρμογής: <strong>Σκλίβας Δημήτριος</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

