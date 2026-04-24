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
    page_title="Methana Earth & Fire",
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
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }
    .hero {
        background: linear-gradient(135deg, #3f2f22 0%, #5a4330 50%, #7a5a3d 100%);
        color: #fffaf2;
        padding: 28px 30px;
        border-radius: 24px;
        margin-bottom: 18px;
        box-shadow: 0 18px 40px rgba(62, 45, 28, 0.24);
        border: 1px solid rgba(255,255,255,0.06);
        position: relative;
        overflow: hidden;
    }
    .hero::after {
        content: "Σκλίβας Δημήτριος";
        position: absolute;
        right: 22px;
        bottom: 10px;
        font-size: 1rem;
        opacity: 0.15;
        letter-spacing: 2px;
        font-weight: 700;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.3rem;
        line-height: 1.05;
        letter-spacing: 0.4px;
    }
    .hero p {
        margin: 10px 0 0 0;
        color: rgba(255,250,242,0.88);
        font-size: 1rem;
        letter-spacing: 0.2px;
    }
    .mini-card {
        background: rgba(255, 250, 242, 0.94);
        border: 1px solid rgba(90, 67, 48, 0.08);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(90, 67, 48, 0.06);
        margin-bottom: 14px;
    }
    .section-title {
        font-size: 1.05rem;
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
        font-size: 0.82rem;
        opacity: 0.12;
        font-weight: 700;
        letter-spacing: 1px;
        color: #5a4330;
        pointer-events: none;
    }
    .split-card {
        background: rgba(255,250,242,0.95);
        border: 1px solid rgba(90,67,48,0.08);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(90,67,48,0.06);
        margin-bottom: 14px;
    }
    .split-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: baseline;
        margin-bottom: 6px;
    }
    .split-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #4c3826;
    }
    .split-sub {
        color: #7a5a3d;
        font-size: 0.92rem;
        margin-bottom: 10px;
    }
    .split-line {
        margin-bottom: 10px;
    }
    .split-line-top {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        font-size: 0.92rem;
        color: #4c3826;
        margin-bottom: 5px;
    }
    .split-track {
        height: 14px;
        border-radius: 999px;
        background: #eadfce;
        overflow: hidden;
        position: relative;
    }
    .split-fill {
        height: 100%;
        border-radius: 999px;
    }
    .split-total { background: linear-gradient(90deg, #c9a96b 0%, #d9bd87 100%); }
    .split-me { background: linear-gradient(90deg, #3f7d6b 0%, #5da08c 100%); }
    .split-father { background: linear-gradient(90deg, #915f35 0%, #b37c4e 100%); }
    .split-remaining { background: linear-gradient(90deg, #8a3b3b 0%, #b44c4c 100%); }
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
    div[data-testid="stSidebar"] .stSelectbox label {
        font-weight: 700;
        color: #4c3826;
    }
    div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background: rgba(255,250,242,0.95);
        border-radius: 14px;
        border: 1px solid rgba(90,67,48,0.08);
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

LOGO_PATH = "assets/logo.png"

header_left, header_right = st.columns([0.9, 5.1])

with header_left:
    try:
        st.image(LOGO_PATH, width=120)
    except Exception:
        pass

with header_right:
    st.markdown(
        """
        <div class="hero">
            <h1>Methana Earth & Fire</h1>
            <p>Personal Renovation Project by Σκλίβας Δημήτριος</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

SHEET_EXPENSES = "Expenses"
SHEET_FEES = "Fees"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "💼 Αμοιβές",
    "📋 Εργασίες",
    "💼 Προσφορές",
    "📸 Gallery",
    "📊 Αναλύσεις",
    "🏦 Δάνειο",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
FEE_COLUMNS = ["_id", "Κατηγορία", "Περιγραφή", "Συνολικό_Ποσό", "Συμμετοχή_Εγώ", "Συμμετοχή_Πατέρας", "Σημειώσεις"]
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
CHART_COLORS = ["#c9a96b", "#6b4f3a", "#3f7d6b", "#b07d4f", "#8d6e63", "#d4af37", "#7b5e57"]


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


def build_labels(df: pd.DataFrame, id_col: str, label_builder):
    labels = {}
    if df.empty or id_col not in df.columns:
        return labels
    for _, row in df.iterrows():
        row_id = safe_text(row.get(id_col, ""))
        if row_id:
            labels[row_id] = label_builder(row)
    return labels


def clamp_percent(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, (value / total) * 100))


def render_progress_line(label: str, value: float, total: float, css_class: str, right_text: str | None = None):
    pct = clamp_percent(value, total)
    right = right_text or f"{format_currency(value)} / {format_currency(total)}"
    st.markdown(
        f"""
        <div class="split-line">
            <div class="split-line-top">
                <span>{label}</span>
                <span>{right}</span>
            </div>
            <div class="split-track">
                <div class="split-fill {css_class}" style="width:{pct:.2f}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_split_card(title: str, subtitle: str, total_amount: float, paid_me: float, paid_father: float, target_me: float | None = None, target_father: float | None = None):
    total_paid = paid_me + paid_father
    remaining = max(total_amount - total_paid, 0)

    st.markdown(
        f"""
        <div class="split-card">
            <div class="split-head">
                <div class="split-title">{title}</div>
                <div><strong>{format_currency(total_amount)}</strong></div>
            </div>
            <div class="split-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )

    render_progress_line("Σύνολο καλυμμένο", total_paid, total_amount, "split-total", f"{format_currency(total_paid)} / {format_currency(total_amount)}")

    if target_me is not None and target_me > 0:
        remain_me = max(target_me - paid_me, 0)
        render_progress_line("Εγώ", paid_me, target_me, "split-me", f"{format_currency(paid_me)} από {format_currency(target_me)} | Υπόλοιπο {format_currency(remain_me)}")
    else:
        render_progress_line("Εγώ", paid_me, total_amount, "split-me", f"{format_currency(paid_me)}")

    if target_father is not None and target_father > 0:
        remain_father = max(target_father - paid_father, 0)
        render_progress_line("Πατέρας", paid_father, target_father, "split-father", f"{format_currency(paid_father)} από {format_currency(target_father)} | Υπόλοιπο {format_currency(remain_father)}")
    else:
        render_progress_line("Πατέρας", paid_father, total_amount, "split-father", f"{format_currency(paid_father)}")

    render_progress_line("Απομένει", remaining, total_amount, "split-remaining", f"{format_currency(remaining)}")
    st.markdown("</div>", unsafe_allow_html=True)


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


def calculate_fee_status(df_fees: pd.DataFrame, df_expenses: pd.DataFrame) -> pd.DataFrame:
    if df_fees.empty:
        return pd.DataFrame()

    result_rows = []
    exp = df_expenses.copy()
    if not exp.empty:
        exp["Ποσό"] = money_series(exp, "Ποσό")

    for _, fee in df_fees.iterrows():
        category = safe_text(fee["Κατηγορία"])
        description = safe_text(fee["Περιγραφή"])
        total_amount = pd.to_numeric(pd.Series([fee["Συνολικό_Ποσό"]]), errors="coerce").fillna(0).iloc[0]
        share_me = pd.to_numeric(pd.Series([fee["Συμμετοχή_Εγώ"]]), errors="coerce").fillna(0).iloc[0]
        share_father = pd.to_numeric(pd.Series([fee["Συμμετοχή_Πατέρας"]]), errors="coerce").fillna(0).iloc[0]

        relevant = exp[
            (exp["Κατηγορία"] == category) &
            (exp["Είδος"] == "Αμοιβή")
        ].copy() if not exp.empty else pd.DataFrame()

        paid_me = relevant.loc[relevant["Πληρωτής"] == "Εγώ", "Ποσό"].sum() if not relevant.empty else 0
        paid_father = relevant.loc[relevant["Πληρωτής"] == "Πατέρας", "Ποσό"].sum() if not relevant.empty else 0

        total_paid = paid_me + paid_father
        result_rows.append({
            "_id": safe_text(fee["_id"]),
            "Κατηγορία": category,
            "Περιγραφή": description,
            "Συνολικό Ποσό": total_amount,
            "Στόχος Εγώ": share_me,
            "Στόχος Πατέρας": share_father,
            "Πλήρωσα Εγώ": paid_me,
            "Πλήρωσε Πατέρας": paid_father,
            "Υπόλοιπο Εγώ": max(share_me - paid_me, 0),
            "Υπόλοιπο Πατέρας": max(share_father - paid_father, 0),
            "Συνολικό Υπόλοιπο": max(total_amount - total_paid, 0),
            "Σημειώσεις": safe_text(fee["Σημειώσεις"]),
        })

    return pd.DataFrame(result_rows)


def calculate_non_fee_expense_split(df_expenses: pd.DataFrame) -> pd.DataFrame:
    if df_expenses.empty:
        return pd.DataFrame()

    exp = df_expenses.copy()
    exp["Ποσό"] = money_series(exp, "Ποσό")
    exp = exp[exp["Είδος"] != "Αμοιβή"].copy()
    if exp.empty:
        return pd.DataFrame()

    rows = []
    for category in sorted(exp["Κατηγορία"].dropna().astype(str).unique()):
        subset = exp[exp["Κατηγορία"] == category]
        total = subset["Ποσό"].sum()
        paid_me = subset.loc[subset["Πληρωτής"] == "Εγώ", "Ποσό"].sum()
        paid_father = subset.loc[subset["Πληρωτής"] == "Πατέρας", "Ποσό"].sum()
        paid_common = subset.loc[subset["Πληρωτής"] == "Κοινό", "Ποσό"].sum()
        rows.append({
            "Κατηγορία": category,
            "Σύνολο": total,
            "Εγώ": paid_me,
            "Πατέρας": paid_father,
            "Κοινό": paid_common,
            "Λοιποί": max(total - paid_me - paid_father - paid_common, 0),
        })

    return pd.DataFrame(rows).sort_values("Σύνολο", ascending=False)


df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)


def render_dashboard(df_exp: pd.DataFrame, df_fee: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame, df_gal: pd.DataFrame):
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

    fee_status_df = calculate_fee_status(df_fee, df_exp)
    if not fee_status_df.empty:
        st.markdown("### Αμοιβές με Διαμερισμό")
        a1, a2, a3 = st.columns(3)
        a1.metric("Υπόλοιπο Εγώ", format_currency(fee_status_df["Υπόλοιπο Εγώ"].sum()))
        a2.metric("Υπόλοιπο Πατέρας", format_currency(fee_status_df["Υπόλοιπο Πατέρας"].sum()))
        a3.metric("Συνολικό Υπόλοιπο Αμοιβών", format_currency(fee_status_df["Συνολικό Υπόλοιπο"].sum()))

        fee_cols = st.columns(2)
        for idx, (_, row) in enumerate(fee_status_df.iterrows()):
            with fee_cols[idx % 2]:
                render_split_card(
                    safe_text(row["Κατηγορία"]),
                    safe_text(row["Περιγραφή"]),
                    float(row["Συνολικό Ποσό"]),
                    float(row["Πλήρωσα Εγώ"]),
                    float(row["Πλήρωσε Πατέρας"]),
                    float(row["Στόχος Εγώ"]),
                    float(row["Στόχος Πατέρας"]),
                )

    other_split_df = calculate_non_fee_expense_split(df_exp)
    if not other_split_df.empty:
        st.markdown("### Λοιπά Έξοδα με Διαμερισμό")
        other_cols = st.columns(2)
        for idx, (_, row) in enumerate(other_split_df.iterrows()):
            with other_cols[idx % 2]:
                render_split_card(
                    safe_text(row["Κατηγορία"]),
                    "Υλικά και λοιπά έξοδα της κατηγορίας",
                    float(row["Σύνολο"]),
                    float(row["Εγώ"]),
                    float(row["Πατέρας"]),
                )

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

    split_df = calculate_non_fee_expense_split(df_exp)
    if not split_df.empty:
        st.markdown("### Μπάρες Διαμερισμού για Υλικά και Λοιπά Έξοδα")
        split_cols = st.columns(2)
        for idx, (_, row) in enumerate(split_df.iterrows()):
            with split_cols[idx % 2]:
                render_split_card(
                    safe_text(row["Κατηγορία"]),
                    "Κατανομή ανά πληρωτή",
                    float(row["Σύνολο"]),
                    float(row["Εγώ"]),
                    float(row["Πατέρας"]),
                )


def render_fees(df_fee: pd.DataFrame, df_exp: pd.DataFrame):
    st.subheader("💼 Αμοιβές")

    with st.expander("➕ Νέα συνολική αμοιβή"):
        with st.form("fee_add_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES, key="fee_category")
                description = st.text_input("Περιγραφή", key="fee_description")
                total_amount = st.number_input("Συνολικό ποσό (€)", min_value=0.0, step=10.0, key="fee_total")
            with c2:
                share_me = st.number_input("Συμμετοχή Εγώ (€)", min_value=0.0, step=10.0, key="fee_me")
                share_father = st.number_input("Συμμετοχή Πατέρας (€)", min_value=0.0, step=10.0, key="fee_father")
                notes = st.text_input("Σημειώσεις", key="fee_notes")

            if st.form_submit_button("Αποθήκευση αμοιβής"):
                updated_df = append_row(
                    df_fee,
                    {
                        "Κατηγορία": category,
                        "Περιγραφή": description.strip(),
                        "Συνολικό_Ποσό": total_amount,
                        "Συμμετοχή_Εγώ": share_me,
                        "Συμμετοχή_Πατέρας": share_father,
                        "Σημειώσεις": notes.strip(),
                    },
                    FEE_COLUMNS,
                )
                if safe_write(SHEET_FEES, updated_df):
                    st.success("Η αμοιβή αποθηκεύτηκε.")
                    st.rerun()

    status_df = calculate_fee_status(df_fee, df_exp)
    if status_df.empty:
        st.info("Δεν υπάρχουν καταχωρημένες αμοιβές.")
        return

    show_table(status_df)
    st.markdown("### Μπάρες Διαμερισμού Αμοιβών")
    fee_cols = st.columns(2)
    for idx, (_, row) in enumerate(status_df.iterrows()):
        with fee_cols[idx % 2]:
            render_split_card(
                safe_text(row["Κατηγορία"]),
                safe_text(row["Περιγραφή"]),
                float(row["Συνολικό Ποσό"]),
                float(row["Πλήρωσα Εγώ"]),
                float(row["Πλήρωσε Πατέρας"]),
                float(row["Στόχος Εγώ"]),
                float(row["Στόχος Πατέρας"]),
            )

    fee_labels = build_labels(
        status_df,
        "_id",
        lambda row: f"{safe_text(row['Κατηγορία'])} | {safe_text(row['Περιγραφή'])} | {format_currency(row['Συνολικό Ποσό'])}",
    )
    fee_ids = list(fee_labels.keys())
    if fee_ids:
        selected_id = st.selectbox(
            "Επιλογή αμοιβής για διαγραφή",
            options=fee_ids,
            format_func=lambda rid: fee_labels.get(rid, "Άγνωστη αμοιβή"),
        )
        if st.button("🗑️ Διαγραφή αμοιβής"):
            updated_df = delete_row_by_id(df_fee, selected_id)
            if safe_write(SHEET_FEES, updated_df):
                st.success("Η αμοιβή διαγράφηκε.")
                st.rerun()


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
                st.info("Το slideshow mode είναι ενεργό. Μετακίνησε τον slider για γρήγορη προβολή.")

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


def render_analytics(df_exp: pd.DataFrame, df_fee: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame):
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

        card_start("Αμοιβές και Συμμετοχές")
        fee_status_df = calculate_fee_status(df_fee, df_exp)
        if not fee_status_df.empty:
            st.dataframe(
                fee_status_df[[
                    "Κατηγορία",
                    "Περιγραφή",
                    "Συνολικό Ποσό",
                    "Πλήρωσα Εγώ",
                    "Πλήρωσε Πατέρας",
                    "Υπόλοιπο Εγώ",
                    "Υπόλοιπο Πατέρας",
                ]],
                use_container_width=True,
            )
        else:
            st.info("Δεν υπάρχουν αμοιβές.")
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

        card_start("Μέσο Ποσό Προσφορών ανά Κατηγορία")
        if not df_off.empty:
            temp = df_off.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].mean().rename(columns={"Ποσό": "Μέσο Ποσό"})
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατηγορία", "Μέσο Ποσό", "Μέσο κόστος προσφορών"), use_container_width=True)
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
    else:
        wall_area = st.number_input("m² Τοίχου", min_value=0.0, value=50.0)
        coats = st.number_input("Χέρια", min_value=1, value=2)
        coverage = st.number_input("Απόδοση (m²/λίτρο)", min_value=1.0, value=12.0)
        liters = (wall_area * coats) / coverage
        st.metric("Λίτρα χρώματος", f"{liters:.1f} L")


st.sidebar.markdown("### Πλοήγηση")
menu = st.sidebar.selectbox("Μενού", MENU_OPTIONS, index=0)
st.sidebar.markdown("---")
st.sidebar.caption(f"Τελευταία ενημέρωση: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("Κατασκευαστής εφαρμογής: Σκλίβας Δημήτριος")

if menu == "🏠 Dashboard":
    render_dashboard(df_expenses, df_fees, df_tasks, df_offers, df_gallery)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "💼 Αμοιβές":
    render_fees(df_fees, df_expenses)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "📸 Gallery":
    render_gallery(df_gallery)
elif menu == "📊 Αναλύσεις":
    render_analytics(df_expenses, df_fees, df_tasks, df_offers)
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
