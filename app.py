import base64
import io
import time
import uuid
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Methana Earth & Fire v2", layout="wide")
APP_VERSION = "v2.2"
APP_BUILDER = "ΣΚΛΙΒΑΣ Σ. ΔΗΜΗΤΡΙΟΣ"


# -----------------------------
# Google Sheets Connection
# -----------------------------
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


def inject_v22_theme():
    st.markdown(
        f"""
        <style>
        :root {{
            --volcanic-black: #1c1b1a;
            --basalt-gray: #2f3437;
            --sulfur-gold: #c9a96b;
            --aegean-blue: #2e6f95;
            --sea-foam: #cfe8e6;
            --lava-rust: #915f35;
        }}
        .stApp {{
            background: linear-gradient(180deg, #fbfaf8 0%, #f3f0ea 100%);
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #1f2428 0%, #2f3437 100%);
        }}
        section[data-testid="stSidebar"] * {{
            color: #f3efe7 !important;
        }}
        div[data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid rgba(47, 52, 55, 0.12);
            border-radius: 14px;
            padding: 10px 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
        }}
        .methana-hero {{
            border-radius: 16px;
            padding: 14px 18px;
            margin-bottom: 10px;
            color: #ffffff;
            background:
                linear-gradient(120deg, rgba(145,95,53,0.95) 0%, rgba(47,52,55,0.94) 45%, rgba(46,111,149,0.95) 100%);
            box-shadow: 0 10px 24px rgba(25, 25, 25, 0.15);
        }}
        .methana-hero .title {{
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: 0.2px;
        }}
        .methana-hero .subtitle {{
            opacity: 0.92;
            font-size: 0.9rem;
            margin-top: 2px;
        }}
        .app-watermark {{
            position: fixed;
            bottom: 16px;
            right: 18px;
            z-index: 9999;
            font-size: 11px;
            letter-spacing: 0.5px;
            color: rgba(28, 27, 26, 0.28);
            pointer-events: none;
            user-select: none;
            font-weight: 600;
            background: rgba(255, 255, 255, 0.5);
            border: 1px solid rgba(47, 52, 55, 0.12);
            border-radius: 999px;
            padding: 4px 10px;
            backdrop-filter: blur(2px);
        }}
        .stApp [data-testid="stMetricLabel"] p,
        .stApp [data-testid="stMetricValue"] div,
        .stApp [data-testid="stMetricDelta"] div {{
            color: #1f2328 !important;
        }}

        /* Dark mode contrast fixes */
        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background: linear-gradient(180deg, #111416 0%, #161b1f 100%) !important;
            }}
            .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
                color: #e9edf1 !important;
            }}
            .stApp [data-testid="stMetric"] {{
                background: #1f2428 !important;
                border: 1px solid rgba(233, 237, 241, 0.16) !important;
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25) !important;
            }}
            .stApp [data-testid="stMetricLabel"] p,
            .stApp [data-testid="stMetricValue"] div,
            .stApp [data-testid="stMetricDelta"] div {{
                color: #f5f7fa !important;
            }}
            .stApp [data-baseweb="input"] input,
            .stApp [data-baseweb="textarea"] textarea {{
                color: #f5f7fa !important;
                -webkit-text-fill-color: #f5f7fa !important;
            }}
            .stApp [data-baseweb="select"] *,
            .stApp div[data-testid="stDataFrame"] * {{
                color: #e9edf1 !important;
            }}
            .app-watermark {{
                color: rgba(233, 237, 241, 0.78) !important;
                background: rgba(20, 24, 28, 0.52) !important;
                border: 1px solid rgba(233, 237, 241, 0.2) !important;
            }}
        }}

        /* Streamlit explicit dark theme attribute fallback */
        .stApp[data-theme="dark"] [data-testid="stMetricLabel"] p,
        .stApp[data-theme="dark"] [data-testid="stMetricValue"] div,
        .stApp[data-theme="dark"] [data-testid="stMetricDelta"] div {{
            color: #f5f7fa !important;
        }}
        </style>
        <div class="app-watermark">Κατασκευαστής app: {APP_BUILDER}</div>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header():
    st.markdown(
        f"""
        <div class="methana-hero">
            <div class="title">🌋 Methana Earth & Fire - Renovation Suite {APP_VERSION}</div>
            <div class="subtitle">Volcanic precision • Sea balance • Stone-solid tracking</div>
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

SHEET_ALIASES = {
    "Expenses": ["Expense", "Έξοδα"],
    "Fees": ["Fee", "Αμοιβές"],
    "Contacts": ["Contact", "Επαφές"],
    "Materials": ["Material", "Υλικά"],
    "Loan": ["Loans", "Δάνειο"],
    "Progress": ["Tasks", "Timeline", "Χρονοδιάγραμμα"],
    "Offers": ["Offer", "Προσφορές"],
    "Gallery": ["Photos", "Φωτογραφίες"],
}

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
FEE_COLUMNS = ["_id", "Κατηγορία", "Περιγραφή", "Ποσό", "Σημειώσεις"]
CONTACT_COLUMNS = ["_id", "Όνομα", "Ρόλος", "Τηλέφωνο", "Email", "Περιοχή", "Σημειώσεις"]
MATERIAL_COLUMNS = [
    "_id",
    "Κατηγορία",
    "Υλικό",
    "Ποσότητα",
    "Μονάδα",
    "Τιμή_Μονάδας",
    "Σύνολο",
    "Πληρωτής",
    "Προμηθευτής",
    "Κατάσταση",
    "Σημειώσεις",
]
LOAN_COLUMNS = ["_id", "Περιγραφή", "Κεφάλαιο", "Επιτόκιο", "Μήνες", "Μηνιαία_Δόση", "Έναρξη", "Κατάσταση", "Σημειώσεις"]
TASK_COLUMNS = ["_id", "Εργασία", "Χώρος", "Κατάσταση", "Ημερομηνία_Έναρξης", "Ημερομηνία_Λήξης", "Κόστος", "Προτεραιότητα", "Ανάθεση", "Σημειώσεις"]
OFFER_COLUMNS = ["_id", "Πάροχος", "Περιγραφή", "Ποσό", "Κατηγορία", "Σημειώσεις"]
GALLERY_COLUMNS = ["_id", "Χώρος", "Τίτλος", "Τύπος", "Image_URL", "Image_Data", "Σημειώσεις"]

EXPENSE_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Κουφώματα", "Μπάνιο", "Άλλο"]
EXPENSE_TYPES = ["Αμοιβή", "Υλικά", "Άλλο"]
PAYERS = ["Εγώ", "Πατέρας", "Κοινό", "Άλλο"]
TASK_STATUSES = ["To Do", "Doing", "Done"]
ROOMS = ["Κουζίνα", "Μπάνιο", "Σαλόνι", "Υπνοδωμάτιο", "Μπαλκόνι", "Διάδρομος", "Άλλο"]


# -----------------------------
# Helpers
# -----------------------------
def to_money(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    text = text.replace("€", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def money_series(df, col):
    if col not in df.columns or df.empty:
        return pd.Series(dtype="float64")
    return df[col].apply(to_money)


def format_currency(value):
    return f"{to_money(value):,.2f} €"


def safe_read(sheet_name, columns, ttl_seconds=60):
    candidates = [sheet_name] + SHEET_ALIASES.get(sheet_name, [])
    last_error = None
    for worksheet_name in candidates:
        try:
            df = conn.read(worksheet=worksheet_name, ttl=ttl_seconds)
            if df is None or df.empty:
                return pd.DataFrame(columns=columns)
            df = df.dropna(how="all")
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            if "_id" not in df.columns:
                df["_id"] = ""
            df["_id"] = df["_id"].astype(str)
            return df[columns]
        except Exception as exc:
            last_error = exc
            if "404" in str(exc):
                continue
            st.warning(f"Αδυναμία ανάγνωσης sheet '{worksheet_name}': {exc}")
            return pd.DataFrame(columns=columns)
    st.warning(f"Αδυναμία ανάγνωσης sheet '{sheet_name}'. Ελέγξτε το όνομα worksheet. ({last_error})")
    return pd.DataFrame(columns=columns)


def safe_write(sheet_name, df):
    retries = 4
    candidates = [sheet_name] + SHEET_ALIASES.get(sheet_name, [])
    last_error = None
    for worksheet_name in candidates:
        for attempt in range(retries):
            try:
                conn.update(worksheet=worksheet_name, data=df)
                return True
            except Exception as exc:
                last_error = exc
                message = str(exc)
                is_rate_limited = "429" in message or "RATE_LIMIT_EXCEEDED" in message or "RESOURCE_EXHAUSTED" in message
                is_transient_server = "500" in message or "INTERNAL" in message or "503" in message or "UNAVAILABLE" in message
                is_not_found = "404" in message
                if (is_rate_limited or is_transient_server) and attempt < retries - 1:
                    wait_seconds = 0.4 * (attempt + 1)
                    time.sleep(wait_seconds)
                    continue
                if is_not_found:
                    break
                st.error(f"Σφάλμα εγγραφής στο '{worksheet_name}': {exc}")
                return False
    st.error(
        f"Αποτυχία εγγραφής στο '{sheet_name}' μετά από επαναπροσπάθειες. "
        f"Πιθανό προσωρινό πρόβλημα Google Sheets. ({last_error})"
    )
    return False


def append_row(df, row_data, columns):
    row_data = dict(row_data)
    row_data["_id"] = str(uuid.uuid4())[:8]
    new_row = pd.DataFrame([row_data])
    for col in columns:
        if col not in new_row.columns:
            new_row[col] = ""
    return pd.concat([df, new_row[columns]], ignore_index=True)


def ensure_ids(df):
    if df.empty:
        return df
    local = df.copy()
    if "_id" not in local.columns:
        local["_id"] = ""
    mask = local["_id"].isna() | (local["_id"].astype(str).str.strip() == "")
    if mask.any():
        local.loc[mask, "_id"] = [str(uuid.uuid4())[:8] for _ in range(mask.sum())]
    return local


def delete_by_id(df, row_id):
    if df.empty or "_id" not in df.columns:
        return df
    return df[df["_id"].astype(str) != str(row_id)].reset_index(drop=True)


def show_table(df, hide_id=True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα")
        return
    display = df.copy()
    if hide_id and "_id" in display.columns:
        display = display.drop(columns=["_id"])
    st.dataframe(display, use_container_width=True)


def editable_sheet(df, columns, key, num_cols=None):
    if num_cols is None:
        num_cols = []
    df_local = ensure_ids(df)
    st.caption("Επεξεργασία απευθείας στον πίνακα και πάτημα αποθήκευση.")
    edited = st.data_editor(
        df_local,
        use_container_width=True,
        hide_index=True,
        column_config={"_id": st.column_config.TextColumn(disabled=True)},
        num_rows="fixed",
        key=key,
    )
    if "_id" not in edited.columns:
        edited["_id"] = df_local["_id"]
    for col in num_cols:
        if col in edited.columns:
            edited[col] = edited[col].apply(to_money)
    for col in columns:
        if col not in edited.columns:
            edited[col] = ""
    return edited[columns]


def render_progress_line(label, value, total, color):
    pct = (to_money(value) / to_money(total) * 100) if to_money(total) > 0 else 0
    st.markdown(
        f"""
    <div style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
            <span>{label}</span>
            <span>{format_currency(value)} / {format_currency(total)}</span>
        </div>
        <div style="background: #e0d5c5; border-radius: 10px; height: 12px; overflow: hidden;">
            <div style="background: {color}; width: {min(100, pct)}%; height: 100%; border-radius: 10px;"></div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def calculate_fee_status(df_fee, df_exp):
    if df_fee.empty:
        return pd.DataFrame()
    results = []
    for _, fee in df_fee.iterrows():
        cat = str(fee.get("Κατηγορία", "")).strip()
        if not cat:
            continue
        total = to_money(fee.get("Ποσό", 0))
        relevant = (
            df_exp[(df_exp["Κατηγορία"] == cat) & (df_exp["Είδος"] == "Αμοιβή")]
            if not df_exp.empty
            else pd.DataFrame()
        )
        paid_me = money_series(relevant[relevant["Πληρωτής"] == "Εγώ"], "Ποσό").sum()
        paid_father = money_series(relevant[relevant["Πληρωτής"] == "Πατέρας"], "Ποσό").sum()
        results.append(
            {
                "Κατηγορία": cat,
                "Συνολικό": total,
                "Πλήρωσα Εγώ": paid_me,
                "Πλήρωσε Πατέρας": paid_father,
                "Περιγραφή": fee.get("Περιγραφή", f"Αμοιβή {cat}"),
            }
        )
    return pd.DataFrame(results)


def calculate_material_split(df_material):
    if df_material.empty:
        return pd.DataFrame()
    local = df_material.copy()
    local["Σύνολο"] = money_series(local, "Σύνολο")
    summary = []
    for cat in sorted(local["Κατηγορία"].dropna().unique()):
        sub = local[local["Κατηγορία"] == cat]
        summary.append(
            {
                "Κατηγορία": cat,
                "Σύνολο": sub["Σύνολο"].sum(),
                "Εγώ": sub[sub["Πληρωτής"] == "Εγώ"]["Σύνολο"].sum(),
                "Πατέρας": sub[sub["Πληρωτής"] == "Πατέρας"]["Σύνολο"].sum(),
            }
        )
    return pd.DataFrame(summary)


def calculate_total_spend_breakdown(df_exp, df_material):
    fees = df_exp[df_exp["Είδος"] == "Αμοιβή"].copy() if not df_exp.empty else pd.DataFrame()
    mats_exp = df_exp[df_exp["Είδος"] == "Υλικά"].copy() if not df_exp.empty else pd.DataFrame()
    mats_sheet = df_material.copy() if not df_material.empty else pd.DataFrame()
    others_exp = (
        df_exp[~df_exp["Είδος"].isin(["Αμοιβή", "Υλικά"])].copy()
        if not df_exp.empty and "Είδος" in df_exp.columns
        else pd.DataFrame()
    )

    def split_by_payer(local_df, amount_col):
        if local_df.empty:
            return 0.0, 0.0, 0.0
        me = money_series(local_df[local_df["Πληρωτής"] == "Εγώ"], amount_col).sum()
        father = money_series(local_df[local_df["Πληρωτής"] == "Πατέρας"], amount_col).sum()
        common = money_series(local_df[local_df["Πληρωτής"] == "Κοινό"], amount_col).sum()
        other = money_series(
            local_df[~local_df["Πληρωτής"].isin(["Εγώ", "Πατέρας", "Κοινό"])],
            amount_col,
        ).sum()
        return me + (common / 2), father + (common / 2), other

    fees_me, fees_father, fees_other = split_by_payer(fees, "Ποσό")
    mats_exp_me, mats_exp_father, mats_exp_other = split_by_payer(mats_exp, "Ποσό")
    mats_sheet_me, mats_sheet_father, mats_sheet_other = split_by_payer(mats_sheet, "Σύνολο")

    materials_me = mats_exp_me + mats_sheet_me
    materials_father = mats_exp_father + mats_sheet_father
    materials_other = mats_exp_other + mats_sheet_other
    other_types_total = money_series(others_exp, "Ποσό").sum() if not others_exp.empty else 0.0

    return {
        "fees_me": fees_me,
        "fees_father": fees_father,
        "fees_other": fees_other,
        "materials_me": materials_me,
        "materials_father": materials_father,
        "materials_other": materials_other,
        "other_types_total": other_types_total,
        "total_me": fees_me + materials_me,
        "total_father": fees_father + materials_father,
    }


def apply_expense_filters(df, filters):
    if df.empty:
        return df
    local = df.copy()
    if "Ποσό" in local.columns:
        local["Ποσό"] = money_series(local, "Ποσό")
    if filters.get("categories") and "Κατηγορία" in local.columns:
        local = local[local["Κατηγορία"].isin(filters["categories"])]
    if filters.get("payers") and "Πληρωτής" in local.columns:
        local = local[local["Πληρωτής"].isin(filters["payers"])]
    if "Ημερομηνία" in local.columns:
        dates = pd.to_datetime(local["Ημερομηνία"], errors="coerce")
        start = filters.get("start_date")
        end = filters.get("end_date")
        if start is not None:
            local = local[dates >= pd.Timestamp(start)]
        if end is not None:
            local = local[dates <= pd.Timestamp(end)]
    search = filters.get("search", "").strip().lower()
    if search:
        cat_series = local["Κατηγορία"].astype(str) if "Κατηγορία" in local.columns else pd.Series("", index=local.index)
        type_series = local["Είδος"].astype(str) if "Είδος" in local.columns else pd.Series("", index=local.index)
        notes_series = local["Σημειώσεις"].astype(str) if "Σημειώσεις" in local.columns else pd.Series("", index=local.index)
        combined = (
            cat_series
            + " "
            + type_series
            + " "
            + notes_series
        ).str.lower()
        local = local[combined.str.contains(search, na=False)]
    return local


def apply_material_filters(df, filters):
    if df.empty:
        return df
    local = df.copy()
    if "Σύνολο" in local.columns:
        local["Σύνολο"] = money_series(local, "Σύνολο")
    if filters.get("categories") and "Κατηγορία" in local.columns:
        local = local[local["Κατηγορία"].isin(filters["categories"])]
    if filters.get("payers") and "Πληρωτής" in local.columns:
        local = local[local["Πληρωτής"].isin(filters["payers"])]
    search = filters.get("search", "").strip().lower()
    if search:
        material_series = local["Υλικό"].astype(str) if "Υλικό" in local.columns else pd.Series("", index=local.index)
        supplier_series = local["Προμηθευτής"].astype(str) if "Προμηθευτής" in local.columns else pd.Series("", index=local.index)
        notes_series = local["Σημειώσεις"].astype(str) if "Σημειώσεις" in local.columns else pd.Series("", index=local.index)
        combined = (
            material_series
            + " "
            + supplier_series
            + " "
            + notes_series
        ).str.lower()
        local = local[combined.str.contains(search, na=False)]
    return local


def build_excel_bytes(dataframes_by_sheet):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for sheet_name, df in dataframes_by_sheet.items():
            export_df = df.copy()
            if "_id" in export_df.columns:
                export_df = export_df.drop(columns=["_id"])
            export_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    buffer.seek(0)
    return buffer.getvalue()


def prepare_timeline(df_tasks):
    if df_tasks.empty:
        return pd.DataFrame()
    rows = []
    for _, row in df_tasks.iterrows():
        name = str(row.get("Εργασία", "")).strip()
        if not name:
            continue
        start = pd.to_datetime(row.get("Ημερομηνία_Έναρξης", date.today()), errors="coerce")
        end = pd.to_datetime(row.get("Ημερομηνία_Λήξης", date.today() + timedelta(days=1)), errors="coerce")
        if pd.isna(start):
            start = pd.Timestamp(date.today())
        if pd.isna(end) or end < start:
            end = start + pd.Timedelta(days=1)
        rows.append({"Task": name, "Start": start, "End": end, "Status": row.get("Κατάσταση", "To Do")})
    return pd.DataFrame(rows)


def delete_ui(df, label, key):
    if df.empty:
        return df, False
    ids = df["_id"].astype(str).tolist()
    chosen = st.selectbox(label, ids, key=key)
    if st.button("🗑️ Διαγραφή", key=f"{key}_btn"):
        return delete_by_id(df, chosen), True
    return df, False


# -----------------------------
# Pages
# -----------------------------
def render_dashboard(df_exp, df_fee, df_material, df_task):
    st.title("🏠 Dashboard Ανακαίνισης v2")

    total_expenses = money_series(df_exp, "Ποσό").sum()
    total_materials = money_series(df_material, "Σύνολο").sum()
    total_spent = total_expenses + total_materials
    spend_breakdown = calculate_total_spend_breakdown(df_exp, df_material)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Σύνολο Εξόδων", format_currency(total_spent))
        if st.button("Ανάλυση συνεισφοράς", key="open_total_spend_breakdown"):
            st.session_state["show_total_spend_breakdown"] = not st.session_state.get("show_total_spend_breakdown", False)
    col2.metric("Έξοδα (Expenses)", len(df_exp))
    col3.metric("Υλικά (Materials)", len(df_material))
    col4.metric("Εργασίες", len(df_task))

    if st.session_state.get("show_total_spend_breakdown", False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**👤 Εγώ**")
            st.write(f"- Αμοιβές: {format_currency(spend_breakdown['fees_me'])}")
            st.write(f"- Υλικά: {format_currency(spend_breakdown['materials_me'])}")
            st.write(f"- **Σύνολο: {format_currency(spend_breakdown['total_me'])}**")
        with c2:
            st.markdown("**👤 Πατέρας**")
            st.write(f"- Αμοιβές: {format_currency(spend_breakdown['fees_father'])}")
            st.write(f"- Υλικά: {format_currency(spend_breakdown['materials_father'])}")
            st.write(f"- **Σύνολο: {format_currency(spend_breakdown['total_father'])}**")
        other_paid = spend_breakdown["fees_other"] + spend_breakdown["materials_other"]
        known_total = spend_breakdown["total_me"] + spend_breakdown["total_father"] + other_paid + spend_breakdown["other_types_total"]
        gap = to_money(total_spent) - to_money(known_total)
        st.write(f"- Μη αντιστοιχισμένα σε Εγώ/Πατέρα (π.χ. Άλλο): {format_currency(other_paid)}")
        st.write(f"- Άλλα είδη εξόδων (εκτός Αμοιβές/Υλικά): {format_currency(spend_breakdown['other_types_total'])}")
        if abs(gap) > 0.01:
            st.warning(f"Υπάρχει υπόλοιπο που δεν κατηγοριοποιείται: {format_currency(gap)}")
        st.caption("Τα ποσά με πληρωτή 'Κοινό' μοιράζονται αυτόματα 50%-50% σε Εγώ και Πατέρα.")

    st.divider()
    st.subheader("💰 Αμοιβές Συνεργείων")

    fees = calculate_fee_status(df_fee, df_exp)
    if fees.empty:
        st.info("Δεν υπάρχουν αμοιβές")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(fees.iterrows()):
            with cols[i % 2]:
                st.markdown(f"**👷 {row['Κατηγορία']}**")
                st.caption(row["Περιγραφή"])
                per_person_target = to_money(row["Συνολικό"]) / 2
                render_progress_line("Σύνολο", row["Πλήρωσα Εγώ"] + row["Πλήρωσε Πατέρας"], row["Συνολικό"], "#c9a96b")
                render_progress_line("Εγώ", row["Πλήρωσα Εγώ"], per_person_target, "#3f7d6b")
                render_progress_line("Πατέρας", row["Πλήρωσε Πατέρας"], per_person_target, "#915f35")
                st.divider()

    st.subheader("📦 Υλικά")
    materials = calculate_material_split(df_material)
    if materials.empty:
        st.info("Δεν υπάρχουν υλικά")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(materials.iterrows()):
            with cols[i % 2]:
                st.markdown(f"**🔨 {row['Κατηγορία']}**")
                render_progress_line("Σύνολο", row["Εγώ"] + row["Πατέρας"], row["Σύνολο"], "#c9a96b")
                render_progress_line("Εγώ", row["Εγώ"], row["Σύνολο"], "#3f7d6b")
                render_progress_line("Πατέρας", row["Πατέρας"], row["Σύνολο"], "#915f35")
                st.divider()

    st.subheader("🗓️ Χρονοδιάγραμμα")
    timeline = prepare_timeline(df_task)
    if not timeline.empty:
        fig = px.timeline(timeline, x_start="Start", x_end="End", y="Task", color="Status")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def render_expenses(df):
    st.subheader("💰 Έξοδα")
    current_df = df.copy()
    search_local = st.text_input("Αναζήτηση στα έξοδα", key="search_expenses_local")
    display_df = current_df
    if search_local.strip():
        display_df = apply_expense_filters(
            current_df,
            {"categories": [], "payers": [], "start_date": None, "end_date": None, "search": search_local},
        )
        show_table(display_df)
    with st.expander("➕ Νέο έξοδο"):
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            with col1:
                date_val = st.date_input("Ημερομηνία")
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                typ = st.selectbox("Είδος", EXPENSE_TYPES)
            with col2:
                payer = st.selectbox("Πληρωτής", PAYERS)
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση"):
                new = {
                    "Ημερομηνία": str(date_val),
                    "Κατηγορία": cat,
                    "Είδος": typ,
                    "Ποσό": amount,
                    "Πληρωτής": payer,
                    "Σημειώσεις": notes,
                }
                updated = append_row(current_df, new, EXPENSE_COLUMNS)
                with st.spinner("Αποθήκευση..."):
                    ok = safe_write(SHEET_EXPENSES, updated)
                if ok:
                    st.toast("Αποθηκεύτηκε", icon="✅")
                    st.rerun()

    edited = editable_sheet(current_df, EXPENSE_COLUMNS, "expenses_editor", num_cols=["Ποσό"])
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Αποθήκευση αλλαγών", key="save_exp"):
            if safe_write(SHEET_EXPENSES, edited):
                st.success("Οι αλλαγές αποθηκεύτηκαν.")
                st.rerun()
    with col_b:
        new_df, should_delete = delete_ui(edited, "Επέλεξε _id για διαγραφή", "del_exp")
        if should_delete and safe_write(SHEET_EXPENSES, new_df):
            st.success("Η εγγραφή διαγράφηκε.")
            st.rerun()


def render_fees(df):
    st.subheader("💼 Αμοιβές")
    with st.expander("➕ Νέα αμοιβή"):
        with st.form("fee_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=100.0)
            with col2:
                desc = st.text_input("Περιγραφή")
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση"):
                new = {"Κατηγορία": cat, "Περιγραφή": desc, "Ποσό": amount, "Σημειώσεις": notes}
                updated = append_row(df, new, FEE_COLUMNS)
                if safe_write(SHEET_FEES, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)


def render_materials(df):
    st.subheader("📦 Υλικά")
    search_local = st.text_input("Αναζήτηση στα υλικά", key="search_materials_local")
    base_df = df
    if search_local.strip():
        base_df = apply_material_filters(
            df,
            {"categories": [], "payers": [], "start_date": None, "end_date": None, "search": search_local},
        )
        show_table(base_df)
    with st.expander("➕ Νέο υλικό"):
        with st.form("material_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                name = st.text_input("Υλικό")
                qty = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
                payer = st.selectbox("Πληρωτής", PAYERS)
            with col2:
                unit = st.selectbox("Μονάδα", ["τεμ", "μέτρα", "m2", "κιλά"])
                price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
                supplier = st.text_input("Προμηθευτής")
                notes = st.text_input("Σημειώσεις")
            total = qty * price
            st.caption(f"Σύνολο: {format_currency(total)}")
            if st.form_submit_button("Αποθήκευση") and name:
                new = {
                    "Κατηγορία": cat,
                    "Υλικό": name,
                    "Ποσότητα": qty,
                    "Μονάδα": unit,
                    "Τιμή_Μονάδας": price,
                    "Σύνολο": total,
                    "Πληρωτής": payer,
                    "Προμηθευτής": supplier,
                    "Κατάσταση": "Προς αγορά",
                    "Σημειώσεις": notes,
                }
                updated = append_row(df, new, MATERIAL_COLUMNS)
                if safe_write(SHEET_MATERIALS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()

    edited = editable_sheet(df, MATERIAL_COLUMNS, "materials_editor", num_cols=["Ποσότητα", "Τιμή_Μονάδας", "Σύνολο"])
    edited["Σύνολο"] = edited["Ποσότητα"].apply(to_money) * edited["Τιμή_Μονάδας"].apply(to_money)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Αποθήκευση αλλαγών", key="save_mat"):
            if safe_write(SHEET_MATERIALS, edited):
                st.success("Οι αλλαγές αποθηκεύτηκαν.")
                st.rerun()
    with col_b:
        if not edited.empty:
            st.caption("Γρήγορη διαγραφή υλικού")
            material_options = []
            for _, row in edited.iterrows():
                row_id = str(row.get("_id", ""))
                label = (
                    f"{row.get('Υλικό', '-')}"
                    f" | {row.get('Κατηγορία', '-')}"
                    f" | {format_currency(row.get('Σύνολο', 0))}"
                    f" | id:{row_id}"
                )
                material_options.append((row_id, label))
            selected_label = st.selectbox(
                "Επίλεξε εγγραφή",
                [opt[1] for opt in material_options],
                key="del_mat_label",
            )
            selected_id = next((row_id for row_id, label in material_options if label == selected_label), None)
            if st.button("🗑️ Διαγραφή υλικού", key="del_mat_btn") and selected_id:
                new_df = delete_by_id(edited, selected_id)
                if safe_write(SHEET_MATERIALS, new_df):
                    st.success("Η εγγραφή διαγράφηκε.")
                    st.rerun()


def render_contacts(df):
    st.subheader("📞 Επαφές")
    with st.expander("➕ Νέα επαφή"):
        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Όνομα")
                role = st.selectbox("Ρόλος", ["Υδραυλικός", "Ηλεκτρολόγος", "Πλακάς", "Προμηθευτής"])
            with col2:
                phone = st.text_input("Τηλέφωνο")
                email = st.text_input("Email")
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and name:
                new = {"Όνομα": name, "Ρόλος": role, "Τηλέφωνο": phone, "Email": email, "Περιοχή": "", "Σημειώσεις": notes}
                updated = append_row(df, new, CONTACT_COLUMNS)
                if safe_write(SHEET_CONTACTS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)


def render_loans(df):
    st.subheader("🏦 Δάνειο")
    current_df = st.session_state.get("loans_local_df", df)
    with st.expander("➕ Νέο δάνειο"):
        with st.form("loan_form"):
            col1, col2 = st.columns(2)
            with col1:
                desc = st.text_input("Περιγραφή")
                principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, step=1000.0)
            with col2:
                rate = st.number_input("Επιτόκιο (%)", min_value=0.0, step=0.1)
                months = st.number_input("Μήνες", min_value=1, step=1)
                start_date = st.date_input("Ημερομηνία έναρξης", value=date.today())
            if st.form_submit_button("Αποθήκευση"):
                clean_desc = desc.strip()
                months_int = int(months)
                principal_val = to_money(principal)
                rate_val = to_money(rate)
                if not clean_desc:
                    st.warning("Συμπλήρωσε περιγραφή δανείου.")
                elif months_int <= 0:
                    st.warning("Οι μήνες πρέπει να είναι μεγαλύτεροι από 0.")
                else:
                    monthly_rate = rate_val / 100 / 12
                    if monthly_rate == 0:
                        installment = principal_val / months_int
                    else:
                        installment = principal_val * (monthly_rate * (1 + monthly_rate) ** months_int) / ((1 + monthly_rate) ** months_int - 1)
                    new = {
                        "Περιγραφή": clean_desc,
                        "Κεφάλαιο": principal_val,
                        "Επιτόκιο": rate_val,
                        "Μήνες": months_int,
                        "Μηνιαία_Δόση": installment,
                        "Έναρξη": str(start_date),
                        "Κατάσταση": "Ενεργό",
                        "Σημειώσεις": "",
                    }
                    updated = append_row(current_df, new, LOAN_COLUMNS)
                    with st.spinner("Αποθήκευση δανείου..."):
                        ok = safe_write(SHEET_LOANS, updated)
                    if ok:
                        st.session_state["loans_local_df"] = updated
                        st.toast("Η καταχώρηση δανείου αποθηκεύτηκε", icon="✅")
                        st.rerun()
    show_table(current_df)


def render_timeline_page(df):
    st.subheader("🗓️ Timeline")
    current_df = st.session_state.get("tasks_local_df", df)
    with st.expander("➕ Νέα εργασία"):
        with st.form("task_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Εργασία")
                room = st.selectbox("Χώρος", ROOMS)
                status = st.selectbox("Κατάσταση", TASK_STATUSES)
            with col2:
                start = st.date_input("Έναρξη")
                end = st.date_input("Λήξη")
                assignee = st.text_input("Ανάθεση")
            if st.form_submit_button("Αποθήκευση"):
                clean_name = name.strip()
                if not clean_name:
                    st.warning("Συμπλήρωσε όνομα εργασίας.")
                elif end < start:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν την έναρξη.")
                else:
                    new = {
                        "Εργασία": clean_name,
                        "Χώρος": room,
                        "Κατάσταση": status,
                        "Ημερομηνία_Έναρξης": str(start),
                        "Ημερομηνία_Λήξης": str(end),
                        "Κόστος": 0,
                        "Προτεραιότητα": "Μεσαία",
                        "Ανάθεση": assignee.strip(),
                        "Σημειώσεις": "",
                    }
                    updated = append_row(current_df, new, TASK_COLUMNS)
                    with st.spinner("Αποθήκευση εργασίας..."):
                        ok = safe_write(SHEET_TASKS, updated)
                    if ok:
                        st.session_state["tasks_local_df"] = updated
                        st.toast("Η εργασία αποθηκεύτηκε", icon="✅")
                        st.rerun()

    timeline = prepare_timeline(current_df)
    if not timeline.empty:
        fig = px.timeline(timeline, x_start="Start", x_end="End", y="Task", color="Status")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
    show_table(current_df)


def render_tasks(df):
    st.subheader("📋 Εργασίες")
    show_table(df)


def render_offers(df):
    st.subheader("💼 Προσφορές")
    with st.expander("➕ Νέα προσφορά"):
        with st.form("offer_form"):
            col1, col2 = st.columns(2)
            with col1:
                provider = st.text_input("Πάροχος")
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
            with col2:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=100.0)
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and provider:
                new = {"Πάροχος": provider, "Περιγραφή": "", "Ποσό": amount, "Κατηγορία": cat, "Σημειώσεις": notes}
                updated = append_row(df, new, OFFER_COLUMNS)
                if safe_write(SHEET_OFFERS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)


def render_gallery(df):
    st.subheader("📸 Gallery")
    st.caption("Για μεγάλα volumes προτείνεται αποθήκευση με URL (Cloud Storage), όχι base64 στο Sheet.")
    with st.expander("➕ Νέα εικόνα"):
        with st.form("gallery_form"):
            room = st.selectbox("Χώρος", ROOMS)
            title = st.text_input("Τίτλος")
            img_type = st.selectbox("Τύπος", ["Before", "After", "Progress"])
            uploaded = st.file_uploader("Εικόνα", type=["jpg", "png", "jpeg"])
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and uploaded:
                img = Image.open(uploaded).convert("RGB")
                img.thumbnail((800, 800))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                img_data = base64.b64encode(buffer.getvalue()).decode()
                new = {"Χώρος": room, "Τίτλος": title, "Τύπος": img_type, "Image_URL": "", "Image_Data": img_data, "Σημειώσεις": notes}
                updated = append_row(df, new, GALLERY_COLUMNS)
                if safe_write(SHEET_GALLERY, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    if not df.empty:
        for _, row in df.tail(10).iterrows():
            if row.get("Image_Data"):
                st.image(f"data:image/jpeg;base64,{row['Image_Data']}", width=220)
                st.caption(f"{row.get('Χώρος', '')} - {row.get('Τίτλος', '')}")


def render_analytics(df_exp, df_material, df_fee):
    st.subheader("📊 Αναλύσεις")
    exp_total = money_series(df_exp, "Ποσό").sum()
    mat_total = money_series(df_material, "Σύνολο").sum()
    st.metric("Σύνολο Εξόδων", format_currency(exp_total + mat_total))

    if not df_exp.empty:
        exp_local = df_exp.copy()
        exp_local["Ποσό"] = money_series(exp_local, "Ποσό")
        by_cat_exp = exp_local.groupby("Κατηγορία", as_index=False)["Ποσό"].sum()
        st.markdown("**Έξοδα ανά κατηγορία (Expenses)**")
        st.dataframe(by_cat_exp, use_container_width=True)

    if not df_material.empty:
        mat_local = df_material.copy()
        mat_local["Σύνολο"] = money_series(mat_local, "Σύνολο")
        by_cat_mat = mat_local.groupby("Κατηγορία", as_index=False)["Σύνολο"].sum()
        st.markdown("**Υλικά ανά κατηγορία (Materials)**")
        st.dataframe(by_cat_mat, use_container_width=True)

    st.markdown("**Budget vs Actual (Αμοιβές)**")
    if df_fee.empty:
        st.info("Δεν υπάρχουν budget αμοιβών για σύγκριση.")
    else:
        fee_budget = df_fee.copy()
        fee_budget["Ποσό"] = money_series(fee_budget, "Ποσό")
        budget_by_cat = fee_budget.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().rename(columns={"Ποσό": "Budget"})

        actual_fees = pd.DataFrame(columns=["Κατηγορία", "Actual"])
        if not df_exp.empty:
            fee_exp = df_exp[df_exp["Είδος"] == "Αμοιβή"].copy()
            fee_exp["Ποσό"] = money_series(fee_exp, "Ποσό")
            actual_fees = fee_exp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().rename(columns={"Ποσό": "Actual"})

        compare = budget_by_cat.merge(actual_fees, on="Κατηγορία", how="left").fillna({"Actual": 0.0})
        compare["Διαφορά"] = compare["Actual"] - compare["Budget"]
        compare["% Απόκλιση"] = compare.apply(
            lambda r: ((r["Actual"] / r["Budget"]) - 1) * 100 if to_money(r["Budget"]) > 0 else 0.0,
            axis=1,
        )
        compare["Κατάσταση"] = compare["% Απόκλιση"].apply(
            lambda x: "⚠️ Υπέρβαση" if x > 10 else ("✅ Εντός" if x >= -10 else "⬇️ Κάτω budget")
        )
        st.dataframe(compare, use_container_width=True)
        overruns = compare[compare["% Απόκλιση"] > 10]
        if not overruns.empty:
            cats = ", ".join(overruns["Κατηγορία"].astype(str).tolist())
            st.warning(f"Υπέρβαση budget (>10%) στις κατηγορίες: {cats}")


def render_calculator():
    st.subheader("🧮 Calculator")
    st.caption("Υπολογιστής υλικών με εκτίμηση κόστους.")
    qty = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
    unit_price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
    waste = st.slider("Ποσοστό φύρας (%)", 0, 30, 10)
    adjusted_qty = qty * (1 + waste / 100)
    total = adjusted_qty * unit_price
    col1, col2 = st.columns(2)
    col1.metric("Ποσότητα με φύρα", f"{adjusted_qty:.2f}")
    col2.metric("Εκτιμώμενο κόστος", format_currency(total))


# -----------------------------
# MAIN
# -----------------------------
inject_v22_theme()
st.sidebar.markdown("### Πλοήγηση")
st.sidebar.caption(f"{APP_VERSION} • Κατασκευαστής: {APP_BUILDER}")

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

menu = st.sidebar.selectbox("Μενού", MENU_OPTIONS)
render_brand_header()

with st.sidebar.expander("🔎 Global Filters", expanded=False):
    filter_search = st.text_input("Αναζήτηση (γενική)", key="global_search")
    filter_categories = st.multiselect("Κατηγορίες", EXPENSE_CATEGORIES, key="global_categories")
    filter_payers = st.multiselect("Πληρωτής", PAYERS, key="global_payers")
    use_date_filter = st.checkbox("Φίλτρο ημερομηνίας (Έξοδα)", value=False, key="use_global_date")
    if use_date_filter:
        date_start = st.date_input("Από", value=date.today() - timedelta(days=90), key="global_date_start")
        date_end = st.date_input("Έως", value=date.today(), key="global_date_end")
    else:
        date_start = None
        date_end = None

global_filters = {
    "search": filter_search,
    "categories": filter_categories,
    "payers": filter_payers,
    "start_date": date_start,
    "end_date": date_end,
}

with st.sidebar.expander("📤 Export"):
    if st.button("Προετοιμασία Excel", key="prepare_excel_export"):
        exp_df = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
        fee_df = safe_read(SHEET_FEES, FEE_COLUMNS)
        mat_df = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
        task_df = safe_read(SHEET_TASKS, TASK_COLUMNS)
        loan_df = safe_read(SHEET_LOANS, LOAN_COLUMNS)
        st.session_state["excel_export_bytes"] = build_excel_bytes(
            {
                "Expenses": exp_df,
                "Fees": fee_df,
                "Materials": mat_df,
                "Tasks": task_df,
                "Loans": loan_df,
            }
        )
        st.success("Το αρχείο Excel είναι έτοιμο.")
    if "excel_export_bytes" in st.session_state:
        st.download_button(
            "Λήψη Excel",
            data=st.session_state["excel_export_bytes"],
            file_name=f"renovation_export_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

if menu == "🏠 Dashboard":
    df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
    df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
    df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
    df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
    df_expenses = apply_expense_filters(df_expenses, global_filters)
    df_materials = apply_material_filters(df_materials, global_filters)
    render_dashboard(df_expenses, df_fees, df_materials, df_tasks)
elif menu == "💰 Έξοδα":
    df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
    df_expenses = apply_expense_filters(df_expenses, global_filters)
    render_expenses(df_expenses)
elif menu == "💼 Αμοιβές":
    df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
    render_fees(df_fees)
elif menu == "📦 Υλικά":
    df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
    df_materials = apply_material_filters(df_materials, global_filters)
    render_materials(df_materials)
elif menu == "📞 Επαφές":
    df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
    render_contacts(df_contacts)
elif menu == "🏦 Δάνειο":
    df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
    render_loans(df_loans)
elif menu == "🗓️ Timeline":
    df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
    render_timeline_page(df_tasks)
elif menu == "📋 Εργασίες":
    df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
    render_offers(df_offers)
elif menu == "📸 Gallery":
    df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)
    render_gallery(df_gallery)
elif menu == "📊 Αναλύσεις":
    df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
    df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
    df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
    df_expenses = apply_expense_filters(df_expenses, global_filters)
    df_materials = apply_material_filters(df_materials, global_filters)
    render_analytics(df_expenses, df_materials, df_fees)
elif menu == "🧮 Calculator":
    render_calculator()
