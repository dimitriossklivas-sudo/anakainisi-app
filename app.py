import base64
import io
import uuid
from datetime import date, datetime, timedelta

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
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1480px;
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
        opacity: 0.14;
        letter-spacing: 2px;
        font-weight: 700;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
        line-height: 1.05;
    }
    .hero p {
        margin: 10px 0 0 0;
        color: rgba(255,250,242,0.88);
        font-size: 1rem;
    }
    .mini-card {
        background: rgba(255,250,242,0.95);
        border: 1px solid rgba(90,67,48,0.08);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(90,67,48,0.06);
        margin-bottom: 14px;
    }
    .section-title {
        font-size: 1.06rem;
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
        background: rgba(255,250,242,0.96);
        border: 1px solid rgba(90,67,48,0.08);
        border-radius: 18px;
        padding: 16px 18px;
        box-shadow: 0 10px 24px rgba(90,67,48,0.06);
        margin-bottom: 14px;
    }
    .split-title {
        font-size: 1.04rem;
        font-weight: 700;
        color: #4c3826;
        margin-bottom: 4px;
    }
    .split-sub {
        font-size: 0.92rem;
        color: #7a5a3d;
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
        margin-bottom: 4px;
    }
    .split-track {
        height: 14px;
        border-radius: 999px;
        background: #eadfce;
        overflow: hidden;
    }
    .split-fill {
        height: 100%;
        border-radius: 999px;
    }
    .split-total { background: linear-gradient(90deg, #c9a96b 0%, #dec18e 100%); }
    .split-me { background: linear-gradient(90deg, #3f7d6b 0%, #5fa391 100%); }
    .split-father { background: linear-gradient(90deg, #915f35 0%, #b67d4d 100%); }
    .split-remaining { background: linear-gradient(90deg, #8a3b3b 0%, #be5a5a 100%); }
    .dashboard-block-title {
        font-size: 1.18rem;
        font-weight: 800;
        color: #4c3826;
        margin: 18px 0 8px 0;
    }
    .dashboard-block-subtitle {
        color: #7a5a3d;
        margin-bottom: 12px;
        font-size: 0.95rem;
    }
    .group-table-label {
        font-size: 1rem;
        font-weight: 700;
        color: #4c3826;
        margin: 10px 0 8px 0;
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

header_left, header_right = st.columns([0.85, 5.15])
with header_left:
    try:
        st.image(LOGO_PATH, width=112)
    except Exception:
        pass
with header_right:
    st.markdown(
        """
        <div class="hero">
            <h1>Methana Earth & Fire</h1>
            <p>Project dashboard για ανακαίνιση, κόστος, συνεργεία, υλικά και planning.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


SHEET_EXPENSES = "Expenses"
SHEET_FEES = "Fees"
SHEET_CONTACTS = "Contacts"
SHEET_MATERIALS = "Materials"
SHEET_LOANS = "Loan"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "💼 Αμοιβές",
    "📦 Υλικά",
    "📞 Επαφές",
    "🏦 Δάνειο",
    "🗓️ Timeline",
    "📋 Εργασίες",
    "💼 Προσφορές",
    "📸 Gallery",
    "📊 Αναλύσεις",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
FEE_COLUMNS = ["_id", "Κατηγορία", "Περιγραφή", "Ποσό", "Σημειώσεις"]
CONTACT_COLUMNS = ["_id", "Όνομα", "Ρόλος", "Τηλέφωνο", "Email", "Περιοχή", "Σημειώσεις"]
MATERIAL_COLUMNS = ["_id", "Κατηγορία", "Υλικό", "Ποσότητα", "Μονάδα", "Τιμή_Μονάδας", "Σύνολο", "Προμηθευτής", "Κατάσταση", "Σημειώσεις"]
LOAN_COLUMNS = ["_id", "Περιγραφή", "Κεφάλαιο", "Επιτόκιο", "Μήνες", "Μηνιαία_Δόση", "Έναρξη", "Κατάσταση", "Σημειώσεις"]
TASK_COLUMNS = ["_id", "Εργασία", "Χώρος", "Κατάσταση", "Ημερομηνία_Έναρξης", "Ημερομηνία_Λήξης", "Κόστος", "Προτεραιότητα", "Ανάθεση", "Σημειώσεις"]
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
CONTACT_ROLES = ["Υδραυλικός", "Ηλεκτρολόγος", "Πλακάς", "Ελαιοχρωματιστής", "Προμηθευτής", "Κατάστημα", "Άλλο"]
MATERIAL_UNITS = ["τεμ", "μέτρα", "m2", "σακιά", "κιλά", "λίτρα", "κουτιά", "Άλλο"]
MATERIAL_STATUS = ["Προς αγορά", "Παραγγέλθηκε", "Αγοράστηκε", "Παραδόθηκε"]
LOAN_STATUS = ["Ενεργό", "Υπό εξέταση", "Εξοφλήθηκε"]

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


def safe_text(value, fallback=""):
    if pd.isna(value):
        return fallback
    return str(value)


def safe_float(value, default=0.0):
    """Ασφαλής μετατροπή σε float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def format_currency(value) -> str:
    try:
        return f"{float(value):,.2f} €"
    except Exception:
        return "0.00 €"


def parse_date(value, fallback: date | None = None) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return fallback
    return parsed.date()


def show_table(df: pd.DataFrame, hide_id: bool = True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return
    display_df = df.copy()
    if hide_id and "_id" in display_df.columns:
        display_df = display_df.drop(columns=["_id"])
    st.dataframe(display_df, use_container_width=True)


def card_start(title: str):
    st.markdown(
        f'<div class="mini-card watermark-box"><div class="section-title">{title}</div>',
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


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
            <div class="split-title">{title}</div>
            <div class="split-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )
    
    # Συνολική πρόοδος
    render_progress_line("Σύνολο καλυμμένο", total_paid, total_amount, "split-total", 
                        f"{format_currency(total_paid)} / {format_currency(total_amount)}")
    
    # Πρόοδος Εγώ
    if target_me is not None and target_me > 0:
        render_progress_line("Εγώ", paid_me, target_me, "split-me", 
                            f"{format_currency(paid_me)} από {format_currency(target_me)}")
    else:
        render_progress_line("Εγώ", paid_me, total_amount, "split-me", 
                            f"{format_currency(paid_me)}")
    
    # Πρόοδος Πατέρας
    if target_father is not None and target_father > 0:
        render_progress_line("Πατέρας", paid_father, target_father, "split-father", 
                            f"{format_currency(paid_father)} από {format_currency(target_father)}")
    else:
        render_progress_line("Πατέρας", paid_father, total_amount, "split-father", 
                            f"{format_currency(paid_father)}")
    
    # Υπόλοιπο
    render_progress_line("Απομένει", remaining, total_amount, "split-remaining", 
                        format_currency(remaining))
    
    st.markdown("</div>", unsafe_allow_html=True)


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


def calculate_fee_status(df_fee: pd.DataFrame, df_exp: pd.DataFrame) -> pd.DataFrame:
    """Υπολογίζει την πρόοδο πληρωμών για κάθε κατηγορία αμοιβής"""
    if df_fee.empty:
        return pd.DataFrame()
    
    results = []
    for _, fee in df_fee.iterrows():
        cat = safe_text(fee.get("Κατηγορία", ""))
        if not cat:
            continue
            
        total = safe_float(fee.get("Ποσό", 0))
        
        # Βρες όλες τις αμοιβές αυτής της κατηγορίας
        relevant = df_exp[
            (df_exp["Κατηγορία"] == cat) & 
            (df_exp["Είδος"] == "Αμοιβή")
        ] if not df_exp.empty else pd.DataFrame()
        
        paid_me = money_series(relevant[relevant["Πληρωτής"] == "Εγώ"], "Ποσό").sum()
        paid_father = money_series(relevant[relevant["Πληρωτής"] == "Πατέρας"], "Ποσό").sum()
        
        results.append({
            "Κατηγορία": cat,
            "Συνολικό Ποσό": total,
            "Πλήρωσα Εγώ": paid_me,
            "Πλήρωσε Πατέρας": paid_father,
            "Στόχος Εγώ": total / 2,
            "Στόχος Πατέρας": total / 2,
            "Περιγραφή": safe_text(fee.get("Περιγραφή"), f"Αμοιβή {cat}")
        })
    
    return pd.DataFrame(results)


def calculate_material_split_from_expenses(df_exp: pd.DataFrame) -> pd.DataFrame:
    """Υπολογίζει το split πληρωμών ανά κατηγορία για Υλικά"""
    if df_exp.empty:
        return pd.DataFrame()
    
    # Φιλτράρουμε μόνο Υλικά
    materials = df_exp[df_exp["Είδος"] == "Υλικά"].copy()
    if materials.empty:
        return pd.DataFrame()
    
    materials["Ποσό"] = money_series(materials, "Ποσό")
    
    # Group by κατηγορία και υπολόγισε σύνολα
    summary = []
    for category in materials["Κατηγορία"].unique():
        cat_mats = materials[materials["Κατηγορία"] == category]
        total = cat_mats["Ποσό"].sum()
        paid_me = cat_mats[cat_mats["Πληρωτής"] == "Εγώ"]["Ποσό"].sum()
        paid_father = cat_mats[cat_mats["Πληρωτής"] == "Πατέρας"]["Ποσό"].sum()
        
        summary.append({
            "Κατηγορία": category,
            "Σύνολο": total,
            "Εγώ": paid_me,
            "Πατέρας": paid_father,
            "Υπόλοιπο": total - paid_me - paid_father
        })
    
    return pd.DataFrame(summary).sort_values("Σύνολο", ascending=False)


def calculate_material_summary(df_materials: pd.DataFrame) -> pd.DataFrame:
    if df_materials.empty:
        return pd.DataFrame()
    materials = df_materials.copy()
    materials["Σύνολο"] = money_series(materials, "Σύνολο")
    return materials.groupby("Κατηγορία", as_index=False)["Σύνολο"].sum().sort_values("Σύνολο", ascending=False)


def calculate_loan_installment(principal: float, annual_rate: float, months: int) -> float:
    if months <= 0:
        return 0.0
    monthly_rate = annual_rate / 100 / 12
    if monthly_rate == 0:
        return principal / months
    return principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)


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


def prepare_timeline_df(df_tasks: pd.DataFrame) -> pd.DataFrame:
    """Προετοιμάζει τα δεδομένα για το Gantt chart"""
    if df_tasks.empty:
        return pd.DataFrame()
    
    rows = []
    for _, row in df_tasks.iterrows():
        task_name = safe_text(row.get("Εργασία", ""))
        if not task_name:
            continue
        
        start = parse_date(row.get("Ημερομηνία_Έναρξης"), date.today())
        default_end = start + timedelta(days=1) if start else date.today() + timedelta(days=1)
        end = parse_date(row.get("Ημερομηνία_Λήξης"), default_end)
        
        rows.append({
            "Task": task_name,
            "Start": start,
            "End": end,
            "Resource": safe_text(row.get("Κατάσταση", "Εκκρεμεί")),
            "Χώρος": safe_text(row.get("Χώρος"), "Άλλο"),
            "Ανάθεση": safe_text(row.get("Ανάθεση"), "")
        })
    
    return pd.DataFrame(rows)


# ============================================
# RENDER FUNCTIONS
# ============================================

def render_dashboard(df_exp: pd.DataFrame, df_fee: pd.DataFrame, df_material: pd.DataFrame, df_loan: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame, df_gal: pd.DataFrame):
    st.markdown('<div class="dashboard-block-title">🏠 Dashboard Ανακαίνισης</div>', unsafe_allow_html=True)
    
    # Συνολικό Budget
    col_budget, col_spent, col_remaining, col_tasks = st.columns(4)
    with col_budget:
        budget = st.number_input("Συνολικό Budget (€)", min_value=0.0, value=30000.0, step=1000.0, key="global_budget")
    with col_spent:
        total_spent = money_series(df_exp, "Ποσό").sum()
        st.metric("Σύνολο Εξόδων", format_currency(total_spent), delta=f"{((total_spent/budget)*100):.1f}%" if budget > 0 else None)
    with col_remaining:
        remaining = budget - total_spent
        st.metric("Υπόλοιπο Budget", format_currency(remaining), delta_color="inverse" if remaining < 0 else "normal")
    with col_tasks:
        active_tasks = len(df_task[df_task["Κατάσταση"] == "Doing"]) if not df_task.empty else 0
        st.metric("Ενεργές Εργασίες", active_tasks)
    
    st.markdown("---")
    
    # ============================================
    # 1. ΚΑΡΤΕΣ ΑΜΟΙΒΩΝ ΣΥΝΕΡΓΕΙΩΝ (Fees)
    # ============================================
    st.markdown('<div class="dashboard-block-title">💰 Αμοιβές Συνεργείων</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-block-subtitle">Ανά κατηγορία εργασιών (Υδραυλικός, Ηλεκτρολόγος, Πλακάς, κλπ.)</div>', unsafe_allow_html=True)
    
    fee_cards = calculate_fee_status(df_fee, df_exp)
    
    if fee_cards.empty:
        st.info("📋 Δεν υπάρχουν ακόμη καταχωρημένες αμοιβές συνεργείων. Προσθέστε από το μενού '💼 Αμοιβές'.")
    else:
        fee_cols = st.columns(2)
        for idx, (_, card) in enumerate(fee_cards.iterrows()):
            with fee_cols[idx % 2]:
                category = card.get("Κατηγορία", "Άγνωστη")
                total = float(card.get("Συνολικό Ποσό", 0))
                paid_me = float(card.get("Πλήρωσα Εγώ", 0))
                paid_father = float(card.get("Πλήρωσε Πατέρας", 0))
                target_me = float(card.get("Στόχος Εγώ", total / 2))
                target_father = float(card.get("Στόχος Πατέρας", total / 2))
                description = card.get("Περιγραφή", f"Αμοιβή {category}")
                
                render_split_card(
                    title=f"👷 {category}",
                    subtitle=description,
                    total_amount=total,
                    paid_me=paid_me,
                    paid_father=paid_father,
                    target_me=target_me,
                    target_father=target_father
                )
    
    st.markdown("---")
    
    # ============================================
    # 2. ΚΑΡΤΕΣ ΥΛΙΚΩΝ & ΛΟΙΠΩΝ ΕΞΟΔΩΝ
    # ============================================
    st.markdown('<div class="dashboard-block-title">📦 Υλικά & Λοιπά Έξοδα</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-block-subtitle">Ανά κατηγορία υλικών (πλακάκια, ηλεκτρολογικά, υδραυλικά, κλπ.)</div>', unsafe_allow_html=True)
    
    material_cards = calculate_material_split_from_expenses(df_exp)
    
    if material_cards.empty:
        st.info("📦 Δεν υπάρχουν ακόμη καταχωρημένα υλικά. Προσθέστε έξοδα με Είδος='Υλικά' από το μενού '💰 Έξοδα'.")
    else:
        material_cols = st.columns(2)
        for idx, (_, card) in enumerate(material_cards.iterrows()):
            with material_cols[idx % 2]:
                category = card.get("Κατηγορία", "Άλλη")
                total = float(card.get("Σύνολο", 0))
                paid_me = float(card.get("Εγώ", 0))
                paid_father = float(card.get("Πατέρας", 0))
                
                render_split_card(
                    title=f"🔨 {category}",
                    subtitle="Υλικά και αναλώσιμα",
                    total_amount=total,
                    paid_me=paid_me,
                    paid_father=paid_father,
                    target_me=None,
                    target_father=None
                )
    
    st.markdown("---")
    
    # ============================================
    # 3. TIMELINE / GANTT
    # ============================================
    st.markdown('<div class="dashboard-block-title">🗓️ Χρονοδιάγραμμα Εργασιών</div>', unsafe_allow_html=True)
    
    timeline_df = prepare_timeline_df(df_task)
    if timeline_df.empty:
        st.info("📅 Δεν υπάρχουν ακόμη εργασίες με ημερομηνίες. Προσθέστε από το μενού '🗓️ Timeline'.")
    else:
        gantt = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Resource",
            color_discrete_map={
                "To Do": "#c9a96b",
                "Doing": "#3f7d6b", 
                "Done": "#915f35",
                "Εκκρεμεί": "#c9a96b"
            },
            title="Πρόοδος Εργασιών"
        )
        gantt.update_layout(height=450, margin=dict(l=10, r=10, t=50, b=10))
        gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(gantt, use_container_width=True)
        
        with st.expander("📋 Αναλυτική λίστα εργασιών"):
            show_table(df_task)


def render_expenses(df_exp: pd.DataFrame):
    st.subheader("💰 Έξοδα")
    
    with st.expander("➕ Νέο έξοδο", expanded=False):
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
                notes = st.text_input("Σημειώ
