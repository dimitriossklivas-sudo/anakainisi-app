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
FEE_COLUMNS = ["_id", "Κατηγορία", "Περιγραφή", "Συνολικό_Ποσό", "Συμμετοχή_Εγώ", "Συμμετοχή_Πατέρας", "Σημειώσεις"]
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


def calculate_fee_status(df_fees: pd.DataFrame, df_expenses: pd.DataFrame) -> pd.DataFrame:
 if df_fees.empty:
     return pd.DataFrame()
     exp = df_expenses.copy()
 if not exp.empty:
     exp["Ποσό"] = money_series(exp, "Ποσό")
     rows = []
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
         rows.append({
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
         return pd.DataFrame(rows)


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
         rows.append({
         "Κατηγορία": category,
         "Σύνολο": total,
         "Εγώ": paid_me,
         "Πατέρας": paid_father,
         "Υπόλοιπο": max(total - paid_me - paid_father, 0),
         })
         return pd.DataFrame(rows).sort_values("Σύνολο", ascending=False)


def calculate_material_summary(df_materials: pd.DataFrame) -> pd.DataFrame:
 if df_materials.empty:
     return pd.DataFrame()
     materials = df_materials.copy()
     materials["Σύνολο"] = money_series(materials, "Σύνολο")
     return materials.groupby("Κατηγορία", as_index=False)["Σύνολο"].sum().sort_values("Σύνολο", ascending=False)


def calculate_material_split_from_expenses(df_expenses: pd.DataFrame) -> pd.DataFrame:
 if df_expenses.empty:
     return pd.DataFrame()
     exp = df_expenses.copy()
     exp["Ποσό"] = money_series(exp, "Ποσό")
     exp = exp[exp["Είδος"] == "Υλικά"].copy()
 if exp.empty:
     return pd.DataFrame()
     rows = []
     for category in sorted(exp["Κατηγορία"].dropna().astype(str).unique()):
         subset = exp[exp["Κατηγορία"] == category]
         total = subset["Ποσό"].sum()
         paid_me = subset.loc[subset["Πληρωτής"] == "Εγώ", "Ποσό"].sum()
         paid_father = subset.loc[subset["Πληρωτής"] == "Πατέρας", "Ποσό"].sum()
         rows.append({
         "Κατηγορία": category,
         "Σύνολο": total,
         "Εγώ": paid_me,
         "Πατέρας": paid_father,
         "Υπόλοιπο": max(total - paid_me - paid_father, 0),
        })
         return pd.DataFrame(rows).sort_values("Σύνολο", ascending=False)


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
 if df_tasks.empty:
     return pd.DataFrame()
     rows =    []
     for _, row in df_tasks.iterrows():
         task_name = safe_text(row["Εργασία"])
 if not task_name:
     continue
     start = parse_date(row.get("Ημερομηνία_Έναρξης"), date.today())
     end = parse_date(row.get("Ημερομηνία_Λήξης"), start + timedelta(days=1) if start else date.today() + timedelta(days=1))
 if start and end and end < start:
     end = start
     rows.append({
     "Εργασία": task_name,
     "Χώρος": safe_text(row.get("Χώρος"), "Άλλο"),
     "Κατάσταση": safe_text(row.get("Κατάσταση"), "To Do"),
     "Start": start,
     "End": end,
     "Ανάθεση": safe_text(row.get("Ανάθεση"), ""),
     })
     return pd.DataFrame(rows)


def render_dashboard_section_title(title: str, subtitle: str):
 st.markdown(f'<div class="dashboard-block-title">{title}</div>', unsafe_allow_html=True)
 st.markdown(f'<div class="dashboard-block-subtitle">{subtitle}</div>', unsafe_allow_html=True)
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)


def render_dashboard(df_exp: pd.DataFrame, df_fee: pd.DataFrame, df_material: pd.DataFrame, df_loan: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame, df_gal: pd.DataFrame):
 st.subheader("🏠 Dashboard")
 budget = st.number_input("Συνολικό Budget (€)", min_value=0.0, value=30000.0, step=1000.0)
 spent = money_series(df_exp, "Ποσό").sum()
 materials_total = money_series(df_material, "Σύνολο").sum()
 fee_status_df = calculate_fee_status(df_fee, df_exp)
 material_split_df = calculate_material_split_from_expenses(df_exp)
 timeline_df = prepare_timeline_df(df_task)
 top1, top2, top3, top4 = st.columns(4)
 top1.metric("Σύνολο εξόδων", format_currency(spent))
 top2.metric("Υπόλοιπο budget", format_currency(budget - spent))
 top3.metric("Σύνολο υλικών", format_currency(materials_total))
 top4.metric("Ενεργές εργασίες", int((df_task["Κατάσταση"] == "Doing").sum()) if not df_task.empty else 0)
 render_dashboard_section_title("Κάρτα αμοιβών συνεργείων", "Ακριβώς όπως το σκίτσο σου: μία κάρτα ανά κατηγορία με σύνολο, Εγώ, Πατέρας.")
 if fee_status_df.empty:
     st.info("Δεν υπάρχουν ακόμη αμοιβές.")
 else:
     fee_cols = st.columns(2)
     for idx, (_, row) in enumerate(fee_status_df.iterrows()):
         with fee_cols[idx % 2]:
             render_split_card(
             f"Κάρτα {safe_text(row['Κατηγορία'])}",
             safe_text(row["Περιγραφή"]),
             float(row["Συνολικό Ποσό"]),
             float(row["Πλήρωσα Εγώ"]),
             float(row["Πλήρωσε Πατέρας"]),
             float(row["Στόχος Εγώ"]),
             float(row["Στόχος Πατέρας"]),
             )    
             render_dashboard_section_title("Κάρτα υλικών", "Μία κάρτα ανά κατηγορία για υλικά και λοιπά έξοδα.")
 if material_split_df.empty:
     st.info("Δεν υπάρχουν ακόμη καταχωρημένα υλικά στα έξοδα.")
 else:
     material_cols = st.columns(2)
     for idx, (_, row) in enumerate(material_split_df.iterrows()):
         with material_cols[idx % 2]:
             render_split_card(
             f"Κάρτα {safe_text(row['Κατηγορία'])}",
             "Υλικά κατηγορίας",
             float(row["Σύνολο"]),
             float(row["Εγώ"]),
             float(row["Πατέρας"]),
             )
             render_dashboard_section_title("Timeline / Gantt", "Το project planning σε χρονογραμμή για να βλέπεις τι ξεκινά και τι λήγει.")
 if timeline_df.empty:
     st.info("Δεν υπάρχουν ακόμη εργασίες με timeline.")
 else:
     gantt = px.timeline(
     timeline_df,
     x_start="Start",
     x_end="End",
     y="Εργασία",
     color="Κατάσταση",
     hover_data=["Χώρος", "Ανάθεση"],
     color_discrete_map={"To Do": "#c9a96b", "Doing": "#3f7d6b", "Done": "#915f35"},
     title="Project Timeline",
     )
     gantt.update_layout(height=420, margin=dict(l=10, r=10, t=55, b=10))
     gantt.update_yaxes(autorange="reversed")
     st.plotly_chart(gantt, use_container_width=True)


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
 if df_exp.empty:
     st.info("Δεν υπάρχουν έξοδα.")
     return
     temp = df_exp.copy()
     temp["Ποσό"] = money_series(temp, "Ποσό")
     st.markdown("### Ομαδοποιημένες καταχωρήσεις")
     group_view = temp.groupby(["Κατηγορία", "Είδος", "Πληρωτής"], as_index=False)["Ποσό"].sum().sort_values(["Κατηγορία", "Είδος", "Πληρωτής"])
     st.dataframe(group_view, use_container_width=True)
     tabs = st.tabs(["Αναλυτικά", "Ομαδοποιημένα ανά κατηγορία", "Διαγραφή"])
 with tabs[0]:
     show_table(temp)
 with tabs[1]:
     grouped_category = temp.groupby(["Κατηγορία", "Είδος"], as_index=False)["Ποσό"].sum().sort_values("Ποσό", ascending=False)
     st.dataframe(grouped_category, use_container_width=True)
     st.plotly_chart(make_bar_chart(grouped_category, "Κατηγορία", "Ποσό", "Έξοδα ανά κατηγορία"), use_container_width=True)
 with tabs[2]:
     labels = {}
     for _, row in temp.iterrows():
         row_id = safe_text(row["_id"])
         labels[row_id] = f"{safe_text(row['Ημερομηνία'])} | {safe_text(row['Κατηγορία'])} | {safe_text(row['Είδος'])} | {format_currency(row['Ποσό'])} | {safe_text(row['Πληρωτής'])}"
         selected_id = st.selectbox(
         "Επιλογή εξόδου για διαγραφή",
         options=list(labels.keys()),
         format_func=lambda rid: labels.get(rid, "Άγνωστη εγγραφή"),
         )
 if st.button("🗑️ Διαγραφή εξόδου"):
     updated_df = delete_row_by_id(df_exp, selected_id)
 if safe_write(SHEET_EXPENSES, updated_df):
     st.success("Η καταχώρηση εξόδων διαγράφηκε.")
     st.rerun()
# ✅ FIX Bug 1: Προστέθηκε df_material ως 1ο argument στο append_row
# ✅ FIX Bug 2: Αφαιρέθηκε το αδέσποτο df_material, στο τέλος


def render_materials(df_material: pd.DataFrame):
    st.subheader("📦 Υλικά")
    with st.expander("➕ Νέο υλικό"):
        with st.form("material_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES, key="material_category")
                material_name = st.text_input("Υλικό")
                supplier = st.text_input("Προμηθευτής")
            with c2:
                quantity = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
                unit = st.selectbox("Μονάδα", MATERIAL_UNITS)
                unit_price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
            with c3:
                status = st.selectbox("Κατάσταση", MATERIAL_STATUS)
                total = st.number_input("Σύνολο (€)", min_value=0.0, step=1.0, value=0.0)
                notes = st.text_input("Σημειώσεις")
            final_total = total if total > 0 else quantity * unit_price
            if st.form_submit_button("Αποθήκευση υλικού") and material_name.strip():
                updated_df = append_row(
                    df_material,
                    {
                        "Κατηγορία": category,
                        "Υλικό": material_name.strip(),
                        "Ποσότητα": quantity,
                        "Μονάδα": unit,
                        "Τιμή_Μονάδας": unit_price,
                        "Σύνολο": final_total,
                        "Προμηθευτής": supplier.strip(),
                        "Κατάσταση": status,
                        "Σημειώσεις": notes.strip(),
                    },
                    MATERIAL_COLUMNS,
                )
                if safe_write(SHEET_MATERIALS, updated_df):
                    st.success("Το υλικό αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_material)
    summary = calculate_material_summary(df_material)
    if not summary.empty:
        st.plotly_chart(make_bar_chart(summary, "Κατηγορία", "Σύνολο", "Κόστος υλικών"), use_container_width=True)


def render_contacts(df_contact: pd.DataFrame):
    st.subheader("📞 Επαφές")
    with st.expander("➕ Νέα επαφή"):
        with st.form("contact_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                name = st.text_input("Όνομα")
                role = st.selectbox("Ρόλος", CONTACT_ROLES)
            with c2:
                phone = st.text_input("Τηλέφωνο")
                email = st.text_input("Email")
            with c3:
                area = st.text_input("Περιοχή")
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση επαφής") and name.strip():
                updated_df = append_row(
                    df_contact,
                    {
                        "Όνομα": name.strip(),
                        "Ρόλος": role,
                        "Τηλέφωνο": phone.strip(),
                        "Email": email.strip(),
                        "Περιοχή": area.strip(),
                        "Σημειώσεις": notes.strip(),
                    },
                    CONTACT_COLUMNS,
                )
                if safe_write(SHEET_CONTACTS, updated_df):
                    st.success("Η επαφή αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_contact)


def render_loans(df_loan: pd.DataFrame):
    st.subheader("🏦 Δάνειο")
    with st.expander("➕ Νέα καταχώρηση δανείου"):
        with st.form("loan_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                description = st.text_input("Περιγραφή")
                principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, step=100.0)
                start_date = st.date_input("Έναρξη")
            with c2:
                rate = st.number_input("Επιτόκιο (%)", min_value=0.0, step=0.1)
                months = st.number_input("Μήνες", min_value=1, step=1)
                status = st.selectbox("Κατάσταση", LOAN_STATUS)
            with c3:
                installment = calculate_loan_installment(principal, rate, int(months))
                st.metric("Υπολογισμένη δόση", format_currency(installment))
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση δανείου") and description.strip():
                updated_df = append_row(
                    df_loan,
                    {
                        "Περιγραφή": description.strip(),
                        "Κεφάλαιο": principal,
                        "Επιτόκιο": rate,
                        "Μήνες": int(months),
                        "Μηνιαία_Δόση": installment,
                        "Έναρξη": str(start_date),
                        "Κατάσταση": status,
                        "Σημειώσεις": notes.strip(),
                    },
                    LOAN_COLUMNS,
                )
                if safe_write(SHEET_LOANS, updated_df):
                    st.success("Το δάνειο αποθηκεύτηκε.")
                    st.rerun()
    show_table(df_loan)


def render_timeline(df_task: pd.DataFrame):
    st.subheader("🗓️ Timeline / Gantt")
    with st.expander("➕ Νέα εργασία planning"):
        with st.form("timeline_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                task_name = st.text_input("Εργασία", key="timeline_task_name")
                room = st.selectbox("Χώρος", ROOMS, key="timeline_room")
                status = st.selectbox("Κατάσταση", TASK_STATUSES, key="timeline_status")
            with c2:
                start = st.date_input("Ημερομηνία έναρξης", key="timeline_start")
                end = st.date_input("Ημερομηνία λήξης", key="timeline_end")
            with c3:
                cost = st.number_input("Κόστος (€)", min_value=0.0, step=10.0, key="timeline_cost")
                priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES, key="timeline_priority")
                assignee = st.text_input("Ανάθεση", key="timeline_assignee")
                notes = st.text_input("Σημειώσεις", key="timeline_notes")
            if st.form_submit_button("Αποθήκευση στο planning") and task_name.strip():
                updated_df = append_row(
                    df_task,
                    {
                        "Εργασία": task_name.strip(),
                        "Χώρος": room,
                        "Κατάσταση": status,
                        "Ημερομηνία_Έναρξης": str(start),
                        "Ημερομηνία_Λήξης": str(end),
                        "Κόστος": cost,
                        "Προτεραιότητα": priority,
                        "Ανάθεση": assignee.strip(),
                        "Σημειώσεις": notes.strip(),
                    },
                    TASK_COLUMNS,
                )
                if safe_write(SHEET_TASKS, updated_df):
                    st.success("Η εργασία μπήκε στο planning.")
                    st.rerun()
    timeline_df = prepare_timeline_df(df_task)
    if timeline_df.empty:
        st.info("Δεν υπάρχουν εργασίες για timeline.")
        return
    gantt = px.timeline(
        timeline_df,
        x_start="Start",
        x_end="End",
        y="Εργασία",
        color="Κατάσταση",
        hover_data=["Χώρος", "Ανάθεση"],
        color_discrete_map={"To Do": "#c9a96b", "Doing": "#3f7d6b", "Done": "#915f35"},
        title="Project Planning",
    )
    gantt.update_layout(height=520, margin=dict(l=10, r=10, t=55, b=10))
    gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(gantt, use_container_width=True)
    show_table(df_task)


def render_tasks(df_task: pd.DataFrame):
    st.subheader("📋 Εργασίες")
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
        st.info("Δεν υπάρχουν εικόνες.")
        return
    preview = df_gal.tail(6)
    cols = st.columns(3)
    for idx, (_, row) in enumerate(preview.iterrows()):
        with cols[idx % 3]:
            src = image_source_from_row(row)
            if src:
                st.image(src, use_container_width=True)
            st.caption(f"{safe_text(row['Χώρος'])} | {safe_text(row['Τίτλος'])}")
    def render_analytics(df_exp: pd.DataFrame, df_fee: pd.DataFrame, df_material: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame):
    st.subheader("📊 Αναλύσεις")
    left, right = st.columns(2)
    with left:
        card_start("Έξοδα ανά κατηγορία")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().sort_values("Ποσό", ascending=False)
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατηγορία", "Ποσό", "Σύνολο ανά κατηγορία"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα.")
        card_end()
        card_start("Υλικά ανά κατηγορία")
        material_summary = calculate_material_summary(df_material)
        if not material_summary.empty:
            st.dataframe(material_summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(material_summary, "Κατηγορία", "Σύνολο", "Κόστος υλικών"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν υλικά.")
        card_end()
    with right:
        card_start("Αμοιβές και συμμετοχές")
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
        card_start("Εργασίες ανά κατάσταση")
        if not df_task.empty:
            summary = df_task["Κατάσταση"].value_counts().rename_axis("Κατάσταση").reset_index(name="Πλήθος")
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατάσταση", "Πλήθος", "Κατανομή εργασιών"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν εργασίες.")
        card_end()


def render_calculator():
    st.subheader("🧮 Calculator")
    mode = st.selectbox("Τύπος υπολογισμού", ["Πλακάκια", "Χρώματα"])
    if mode == "Πλακάκια":
        area = st.number_input("m2 Επιφάνειας", min_value=0.0, value=10.0)
        width = st.number_input("Πλάτος πλακιδίου (cm)", min_value=0.1, value=60.0)
        height = st.number_input("Ύψος πλακιδίου (cm)", min_value=0.1, value=120.0)
        waste = st.number_input("Ποσοστό φύρας (%)", min_value=0.0, value=10.0)
        tile_area = (width * height) / 10000
        pieces = area / tile_area if tile_area > 0 else 0
        pieces = int(pieces * (1 + waste / 100)) + 1
        st.metric("Τεμάχια που θα χρειαστείς", pieces)
    else:
        wall_area = st.number_input("m2 Τοίχου", min_value=0.0, value=50.0)
        coats = st.number_input("Χέρια", min_value=1, value=2)
        coverage = st.number_input("Απόδοση (m2/λίτρο)", min_value=1.0, value=12.0)
        liters = (wall_area * coats) / coverage
        st.metric("Λίτρα χρώματος", f"{liters:.1f} L")


# ── Sidebar & Routing ──
st.sidebar.markdown("### Πλοήγηση")
menu = st.sidebar.selectbox("Μενού", MENU_OPTIONS, index=0)
st.sidebar.markdown("---")
st.sidebar.caption(f"Τελευταία ενημέρωση: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("Κατασκευαστής εφαρμογής: Σκλίβας Δημήτριος")

if menu == "🏠 Dashboard":
    render_dashboard(df_expenses, df_fees, df_materials, df_loans, df_tasks, df_offers, df_gallery)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "💼 Αμοιβές":
    render_fees(df_fees, df_expenses)
elif menu == "📦 Υλικά":
    render_materials(df_materials)
elif menu == "📞 Επαφές":
    render_contacts(df_contacts)
elif menu == "🏦 Δάνειο":
    render_loans(df_loans)
elif menu == "🗓️ Timeline":
    render_timeline(df_tasks)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "📸 Gallery":
    render_gallery(df_gallery)
elif menu == "📊 Αναλύσεις":
    render_analytics(df_expenses, df_fees, df_materials, df_tasks, df_offers)
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
