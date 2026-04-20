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

st.title("🏗️ Renovation Manager V2")

# =========================
# ΟΝΟΜΑΤΑ SHEETS
# Άλλαξέ τα μόνο αν τα tabs στο Google Sheet έχουν άλλα ονόματα
# =========================
SHEET_EXPENSES = "Expenses"
SHEET_TASKS = "Tasks"
SHEET_OFFERS = "Offers"

# =========================
# ΣΤΑΘΕΡΕΣ
# =========================
MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "📋 Εργασίες",
    "📊 Αναλύσεις",
    "💼 Προσφορές",
    "🏦 Δάνειο",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["Ημερομηνία", "Κατηγορία", "Ποσό", "Πληρωτής"]
TASK_COLUMNS = ["Εργασία", "Κατάσταση", "Κόστος"]
OFFER_COLUMNS = ["Πάροχος", "Περιγραφή", "Ποσό"]

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
def empty_df(columns):
    return pd.DataFrame(columns=columns)

def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return empty_df(columns)

    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = None

    return df[columns]

def safe_read(sheet_name: str, columns: list[str]) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return empty_df(columns)
        df = df.dropna(how="all")
        return ensure_columns(df, columns)
    except Exception:
        return empty_df(columns)

def safe_write(sheet_name: str, df: pd.DataFrame) -> bool:
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης στο '{sheet_name}': {e}")
        return False

def append_row(df: pd.DataFrame, row_data: dict, columns: list[str]) -> pd.DataFrame:
    df = ensure_columns(df, columns)
    new_row = pd.DataFrame([row_data])
    new_row = ensure_columns(new_row, columns)
    return pd.concat([df, new_row], ignore_index=True)

def delete_row_by_index(df: pd.DataFrame, index_to_delete: int) -> pd.DataFrame:
    if df.empty or index_to_delete not in df.index:
        return df
    return df.drop(index=index_to_delete).reset_index(drop=True)

def to_numeric_series(df: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column_name], errors="coerce").fillna(0)

def show_dataframe_or_info(df: pd.DataFrame, empty_message: str):
    if df.empty:
        st.info(empty_message)
    else:
        st.dataframe(df, use_container_width=True)

# =========================
# ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ
# =========================
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)

# =========================
# ΣΕΛΙΔΕΣ
# =========================
def render_dashboard(df_exp: pd.DataFrame, df_tasks_data: pd.DataFrame, df_off: pd.DataFrame):
    st.subheader("🏠 Dashboard")

    budget = st.number_input("💼 Συνολικό Budget (€)", min_value=0.0, value=30000.0)

    total_spent = to_numeric_series(df_exp, "Ποσό").sum()
    remaining = budget - total_spent
    usage_percent = (total_spent / budget * 100) if budget > 0 else 0.0

    task_count = len(df_tasks_data)
    done_count = 0
    if "Κατάσταση" in df_tasks_data.columns and not df_tasks_data.empty:
        done_count = (df_tasks_data["Κατάσταση"] == "Done").sum()

    best_offer_value = None
    if not df_off.empty and "Ποσό" in df_off.columns:
        offer_amounts = pd.to_numeric(df_off["Ποσό"], errors="coerce").dropna()
        if not offer_amounts.empty:
            best_offer_value = offer_amounts.min()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Έξοδα", f"{total_spent:,.2f} €")
    c2.metric("📊 Budget %", f"{usage_percent:.1f}%")
    c3.metric("📉 Υπόλοιπο", f"{remaining:,.2f} €")

    c4, c5, c6 = st.columns(3)
    c4.metric("📋 Σύνολο Εργασιών", task_count)
    c5.metric("✅ Ολοκληρωμένες", int(done_count))
    c6.metric("🏆 Καλύτερη Προσφορά", f"{best_offer_value:,.2f} €" if best_offer_value is not None else "-")

def render_expenses(df_exp: pd.DataFrame):
    st.subheader("💰 Καταγραφή Εξόδων")

    with st.expander("➕ Νέο Έξοδο"):
        with st.form("expense_form", clear_on_submit=True):
            expense_date = st.date_input("Ημερομηνία")
            category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
            amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            payer = st.selectbox("Πληρωτής", PAYERS)

            submitted = st.form_submit_button("Αποθήκευση")

            if submitted:
                updated_df = append_row(
                    df_exp,
                    {
                        "Ημερομηνία": str(expense_date),
                        "Κατηγορία": category,
                        "Ποσό": amount,
                        "Πληρωτής": payer,
                    },
                    EXPENSE_COLUMNS,
                )
                if safe_write(SHEET_EXPENSES, updated_df):
                    st.success("✔ Το έξοδο αποθηκεύτηκε.")
                    st.rerun()

    if df_exp.empty:
        st.info("Δεν υπάρχουν καταχωρημένα έξοδα.")
    else:
        st.dataframe(df_exp, use_container_width=True)

        selected_index = st.selectbox(
            "Διάλεξε έξοδο για διαγραφή",
            options=df_exp.index.tolist(),
            format_func=lambda x: f"{x} - {df_exp.loc[x, 'Κατηγορία']} - {df_exp.loc[x, 'Ποσό']} €",
            key="delete_expense_select",
        )

        if st.button("🗑️ Διαγραφή εξόδου"):
            updated_df = delete_row_by_index(df_exp, selected_index)
            if safe_write(SHEET_EXPENSES, updated_df):
                st.success("✔ Το έξοδο διαγράφηκε.")
                st.rerun()

def render_tasks(df_tasks_data: pd.DataFrame):
    st.subheader("📋 Διαχείριση Εργασιών")

    with st.expander("➕ Νέα Εργασία"):
        with st.form("task_form", clear_on_submit=True):
            task_name = st.text_input("Εργασία")
            status = st.selectbox("Κατάσταση", TASK_STATUSES)
            estimated_cost = st.number_input("Εκτιμώμενο Κόστος (€)", min_value=0.0, step=10.0)

            submitted = st.form_submit_button("Προσθήκη")

            if submitted:
                if not task_name.strip():
                    st.warning("Η εργασία δεν μπορεί να είναι κενή.")
                else:
                    updated_df = append_row(
                        df_tasks_data,
                        {
                            "Εργασία": task_name.strip(),
                            "Κατάσταση": status,
                            "Κόστος": estimated_cost,
                        },
                        TASK_COLUMNS,
                    )
                    if safe_write(SHEET_TASKS, updated_df):
                        st.success("✔ Η εργασία προστέθηκε.")
                        st.rerun()

    if df_tasks_data.empty:
        st.info("Δεν υπάρχουν καταχωρημένες εργασίες.")
    else:
        st.dataframe(df_tasks_data, use_container_width=True)

        selected_index = st.selectbox(
            "Διάλεξε εργασία για διαγραφή",
            options=df_tasks_data.index.tolist(),
            format_func=lambda x: f"{x} - {df_tasks_data.loc[x, 'Εργασία']} - {df_tasks_data.loc[x, 'Κατάσταση']}",
            key="delete_task_select",
        )

        if st.button("🗑️ Διαγραφή εργασίας"):
            updated_df = delete_row_by_index(df_tasks_data, selected_index)
            if safe_write(SHEET_TASKS, updated_df):
                st.success("✔ Η εργασία διαγράφηκε.")
                st.rerun()

def render_analytics(df_exp: pd.DataFrame, df_tasks_data: pd.DataFrame):
    st.subheader("📊 Αναλύσεις")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Έξοδα ανά κατηγορία")
        if df_exp.empty or "Κατηγορία" not in df_exp.columns or "Ποσό" not in df_exp.columns:
            st.info("Δεν υπάρχουν αρκετά δεδομένα για ανάλυση εξόδων.")
        else:
            analytics_df = df_exp.copy()
            analytics_df["Ποσό"] = pd.to_numeric(analytics_df["Ποσό"], errors="coerce").fillna(0)
            summary = analytics_df.groupby("Κατηγορία", as_index=False)["Ποσό"].sum()
            st.dataframe(summary, use_container_width=True)
            if not summary.empty:
                st.bar_chart(summary.set_index("Κατηγορία"))

    with col2:
        st.markdown("### Εργασίες ανά κατάσταση")
        if df_tasks_data.empty or "Κατάσταση" not in df_tasks_data.columns:
            st.info("Δεν υπάρχουν αρκετά δεδομένα για ανάλυση εργασιών.")
        else:
            task_summary = df_tasks_data["Κατάσταση"].value_counts().rename_axis("Κατάσταση").reset_index(name="Πλήθος")
            st.dataframe(task_summary, use_container_width=True)
            if not task_summary.empty:
                st.bar_chart(task_summary.set_index("Κατάσταση"))

def render_offers(df_off: pd.DataFrame):
    st.subheader("💼 Προσφορές")

    with st.expander("➕ Νέα Προσφορά"):
        with st.form("offer_form", clear_on_submit=True):
            provider = st.text_input("Πάροχος")
            description = st.text_input("Περιγραφή")
            amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)

            submitted = st.form_submit_button("Αποθήκευση Προσφοράς")

            if submitted:
                if not provider.strip():
                    st.warning("Ο πάροχος δεν μπορεί να είναι κενός.")
                else:
                    updated_df = append_row(
                        df_off,
                        {
                            "Πάροχος": provider.strip(),
                            "Περιγραφή": description.strip(),
                            "Ποσό": amount,
                        },
                        OFFER_COLUMNS,
                    )
                    if safe_write(SHEET_OFFERS, updated_df):
                        st.success("✔ Η προσφορά αποθηκεύτηκε.")
                        st.rerun()

    if not df_off.empty:
        offers_numeric = df_off.copy()
        offers_numeric["Ποσό"] = pd.to_numeric(offers_numeric["Ποσό"], errors="coerce")
        offers_numeric = offers_numeric.dropna(subset=["Ποσό"])

        if not offers_numeric.empty:
            best_offer = offers_numeric.sort_values("Ποσό", ascending=True).iloc[0]
            st.info(f"🏆 Καλύτερη προσφορά: {best_offer['Πάροχος']} ({best_offer['Ποσό']:.2f} €)")

    if df_off.empty:
        st.info("Δεν υπάρχουν καταχωρημένες προσφορές.")
    else:
        st.dataframe(df_off, use_container_width=True)

        selected_index = st.selectbox(
            "Διάλεξε προσφορά για διαγραφή",
            options=df_off.index.tolist(),
            format_func=lambda x: f"{x} - {df_off.loc[x, 'Πάροχος']} - {df_off.loc[x, 'Ποσό']} €",
            key="delete_offer_select",
        )

        if st.button("🗑️ Διαγραφή προσφοράς"):
            updated_df = delete_row_by_index(df_off, selected_index)
            if safe_write(SHEET_OFFERS, updated_df):
                st.success("✔ Η προσφορά διαγράφηκε.")
                st.rerun()

def render_calculator():
    st.subheader("🧮 Υπολογισμοί")

    calc_type = st.selectbox("Τύπος", ["Πλακάκια", "Χρώματα"])

    if calc_type == "Πλακάκια":
        area_sq_m = st.number_input("m² Επιφάνειας", min_value=0.0, value=10.0)
        tile_width_cm = st.number_input("Πλάτος πλακιδίου (cm)", min_value=0.1, value=60.0)
        tile_height_cm = st.number_input("Ύψος πλακιδίου (cm)", min_value=0.1, value=120.0)

        tile_area_sq_m = (tile_width_cm * tile_height_cm) / 10000
        pieces_needed = int(area_sq_m / tile_area_sq_m) + 1 if tile_area_sq_m > 0 else 0

        st.metric("Τεμάχια που θα χρειαστείς", pieces_needed)

    elif calc_type == "Χρώματα":
        wall_area = st.number_input("m² Τοίχου", min_value=0.0, value=50.0)
        liters_needed = (wall_area * 2) / 12
        st.success(f"🎨 Θα χρειαστείς περίπου {liters_needed:.1f} λίτρα χρώμα.")

def render_loan():
    st.subheader("🏦 Υπολογιστής Δόσης")

    principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, value=10000.0)
    annual_rate = st.number_input("Ετήσιο Επιτόκιο (%)", min_value=0.0, value=4.5)
    months = st.number_input("Μήνες Εξόφλησης", min_value=1, value=60)

    monthly_rate = annual_rate / 100 / 12

    if principal > 0 and months > 0:
        if monthly_rate == 0:
            installment = principal / months
        else:
            installment = (
                principal
                * (monthly_rate * (1 + monthly_rate) ** months)
                / ((1 + monthly_rate) ** months - 1)
            )

        st.metric("Μηνιαία Δόση", f"{installment:.2f} €")

# =========================
# MENU
# =========================
menu = st.sidebar.radio("📂 Μενού", MENU_OPTIONS)

if menu == "🏠 Dashboard":
    render_dashboard(df_expenses, df_tasks, df_offers)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "📊 Αναλύσεις":
    render_analytics(df_expenses, df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "🏦 Δάνειο":
    render_loan()
elif menu == "🧮 Calculator":
    render_calculator()
