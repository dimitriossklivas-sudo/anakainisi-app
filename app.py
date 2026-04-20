import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# =========================
# ΒΑΣΙΚΕΣ ΡΥΘΜΙΣΕΙΣ
# =========================
st.set_page_config(page_title="Renovation Manager V2", layout="wide")

st.markdown(
    """
    <style>
    .main { background-color: #f4f6f9; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.1);
        border-left: 5px solid #D4AF37;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Renovation Manager V2")

# =========================
# ΣΤΑΘΕΡΕΣ
# =========================
SHEET_EXPENSES = "Expenses"
SHEET_TASKS = "Tasks"
SHEET_OFFERS = "Offers"

MENU_OPTIONS = [
    "Dashboard",
    "Έξοδα",
    "Εργασίες",
    "Αναλύσεις",
    "Προσφορές",
    "Δάνειο",
    "Calculator",
]

EXPENSE_CATEGORIES = [
    "Υδραυλικά",
    "Ηλεκτρολογικά",
    "Πλακάκια",
    "Κουζίνα",
    "Άλλο",
]

PAYERS = ["Εγώ", "Πατέρας"]
TASK_STATUSES = ["To Do", "Doing", "Done"]


# =========================
# ΣΥΝΔΕΣΗ
# =========================
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


# =========================
# ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# =========================
def safe_read(sheet_name: str) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        return df.dropna(how="all")
    except Exception as e:
        st.warning(f"Δεν ήταν δυνατή η φόρτωση του φύλλου '{sheet_name}': {e}")
        return pd.DataFrame()


def safe_write(sheet_name: str, df: pd.DataFrame) -> bool:
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης στο '{sheet_name}': {e}")
        return False


def to_numeric_series(df: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column_name], errors="coerce").fillna(0)


def append_row(df: pd.DataFrame, row_data: dict) -> pd.DataFrame:
    new_row = pd.DataFrame([row_data])
    if df.empty:
        return new_row
    return pd.concat([df, new_row], ignore_index=True)


def show_dataframe_or_info(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.info(empty_message)
    else:
        st.dataframe(df, use_container_width=True)


# =========================
# ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ
# =========================
df_expenses = safe_read(SHEET_EXPENSES)
df_tasks = safe_read(SHEET_TASKS)
df_offers = safe_read(SHEET_OFFERS)


# =========================
# ΣΕΛΙΔΕΣ
# =========================
def render_dashboard(df_exp: pd.DataFrame):
    st.subheader("Dashboard")

    budget = st.number_input("Συνολικό Budget (€)", min_value=0.0, value=30000.0)

    total_spent = 0.0
    if not df_exp.empty:
        total_spent = to_numeric_series(df_exp, "Ποσό").sum()

        remaining = budget - total_spent
    usage_percent = (total_spent / budget * 100) if budget > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.metric("Έξοδα", f"{total_spent:,.2f} €")
    c2.metric("Budget %", f"{usage_percent:.1f}%")
    c3.metric("Υπόλοιπο", f"{remaining:,.2f} €")

