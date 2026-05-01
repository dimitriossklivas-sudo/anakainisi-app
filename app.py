import base64
import io
import time
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Methana Earth & Fire v2", layout="wide")
APP_VERSION = "v2.3"
APP_BUILDER = "ΣΚΛΙΒΑΣ Σ. ΔΗΜΗΤΡΙΟΣ"


# -----------------------------
# Google Sheets Connection
# -----------------------------
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


# -----------------------------
# Theme
# -----------------------------
def inject_v23_theme():
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
            --cream: #fbfaf8;
            --soft-cream: #f3f0ea;
            --ink: #202326;
            --olive-sea: #3f7d6b;
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
            margin-bottom: 14px;
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

        .dashboard-section-title {{
            font-size: 1.08rem;
            font-weight: 800;
            color: #1f2328;
            margin-top: 10px;
            margin-bottom: 8px;
        }}

        .dashboard-section-subtitle {{
            font-size: 0.9rem;
            color: #6a6763;
            margin-bottom: 10px;
        }}

        .visual-card {{
            background: #ffffff;
            border: 1px solid rgba(47, 52, 55, 0.10);
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        }}

        .visual-card-title {{
            font-size: 1rem;
            font-weight: 700;
            color: #1f2328;
            margin-bottom: 4px;
        }}

        .visual-card-subtitle {{
            font-size: 0.86rem;
            color: #6d6a67;
            margin-bottom: 10px;
        }}

        .progress-row {{
            margin-bottom: 10px;
        }}

        .progress-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            font-size: 0.87rem;
            color: #2a2d30;
            margin-bottom: 4px;
        }}

        .progress-track {{
            width: 100%;
            height: 13px;
            border-radius: 999px;
            background: #e8dfd2;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        .fill-total {{ background: linear-gradient(90deg, #c9a96b 0%, #dcc18f 100%); }}
        .fill-me {{ background: linear-gradient(90deg, #3f7d6b 0%, #63a593 100%); }}
        .fill-father {{ background: linear-gradient(90deg, #915f35 0%, #ba8357 100%); }}
        .fill-remain {{ background: linear-gradient(90deg, #7b3333 0%, #b55252 100%); }}

        .group-chip {{
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            background: #efe5d7;
            color: #5d4733;
            margin-right: 6px;
            margin-bottom: 6px;
        }}

        .stApp [data-testid="stMetricLabel"] p,
        .stApp [data-testid="stMetricValue"] div,
        .stApp [data-testid="stMetricDelta"] div {{
            color: #1f2328 !important;
        }}

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
            .visual-card {{
                background: #1f2428 !important;
                border: 1px solid rgba(233, 237, 241, 0.16) !important;
            }}
            .app-watermark {{
                color: rgba(233, 237, 241, 0.78) !important;
                background: rgba(20, 24, 28, 0.52) !important;
                border: 1px solid rgba(233, 237, 241, 0.2) !important;
            }}
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


# -----------------------------
# Sheets
# -----------------------------
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
FEE_COLUMNS = ["_id", "Κατηγορία", "Περιγραφή", "Συνολικό_Ποσό", "Συμμετοχή_Εγώ", "Συμμετοχή_Πατέρας", "Σημειώσεις"]
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
TASK_PRIORITIES = ["Χαμηλή", "Μεσαία", "Υψηλή"]
OFFER_CATEGORIES = EXPENSE_CATEGORIES[:]
CONTACT_ROLES = ["Υδραυλικός", "Ηλεκτρολόγος", "Πλακάς", "Ελαιοχρωματιστής", "Προμηθευτής", "Κατάστημα", "Άλλο"]
MATERIAL_UNITS = ["τεμ", "μέτρα", "m2", "κιλά", "λίτρα", "σακιά", "κουτιά", "Άλλο"]
MATERIAL_STATUS = ["Προς αγορά", "Παραγγέλθηκε", "Αγοράστηκε", "Παραδόθηκε"]
IMAGE_TYPES = ["Before", "After", "Progress", "Material"]

PLOTLY_TEMPLATE = "plotly_white"
CHART_COLORS = ["#c9a96b", "#915f35", "#2e6f95", "#3f7d6b", "#6e5d52", "#d4af37"]


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


def parse_date_safe(value, default=None):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return default
    return parsed


def normalize_task_df(df):
    local = df.copy()
    for col in TASK_COLUMNS:
        if col not in local.columns:
            local[col] = ""
    return local[TASK_COLUMNS]


def normalize_fee_df(df):
    local = df.copy()
    if "Ποσό" not in local.columns:
        local["Ποσό"] = ""
    if "Συνολικό_Ποσό" not in local.columns:
        local["Συνολικό_Ποσό"] = ""

    local["Συνολικό_Ποσό"] = local.apply(
        lambda r: to_money(r["Συνολικό_Ποσό"]) if to_money(r["Συνολικό_Ποσό"]) > 0 else to_money(r["Ποσό"]),
        axis=1,
    )

    if "Συμμετοχή_Εγώ" not in local.columns:
        local["Συμμετοχή_Εγώ"] = ""
    if "Συμμετοχή_Πατέρας" not in local.columns:
        local["Συμμετοχή_Πατέρας"] = ""

    local["Συμμετοχή_Εγώ"] = local.apply(
        lambda r: to_money(r["Συμμετοχή_Εγώ"]) if to_money(r["Συμμετοχή_Εγώ"]) > 0 else to_money(r["Συνολικό_Ποσό"]) / 2,
        axis=1,
    )
    local["Συμμετοχή_Πατέρας"] = local.apply(
        lambda r: to_money(r["Συμμετοχή_Πατέρας"]) if to_money(r["Συμμετοχή_Πατέρας"]) > 0 else to_money(r["Συνολικό_Ποσό"]) / 2,
        axis=1,
    )

    for col in FEE_COLUMNS:
        if col not in local.columns:
            local[col] = ""
    return local[FEE_COLUMNS]


def safe_read(sheet_name, columns, ttl_seconds=60, optional_columns=None):
    optional_columns = optional_columns or []
    candidates = [sheet_name] + SHEET_ALIASES.get(sheet_name, [])
    last_error = None

    for worksheet_name in candidates:
        try:
            df = conn.read(worksheet=worksheet_name, ttl=ttl_seconds)
            if df is None or df.empty:
                return pd.DataFrame(columns=columns)
            df = df.dropna(how="all")
            all_columns = list(dict.fromkeys(columns + optional_columns))
            for col in all_columns:
                if col not in df.columns:
                    df[col] = ""
            if "_id" not in df.columns:
                df["_id"] = ""
            df["_id"] = df["_id"].astype(str)
            return df[all_columns]
        except Exception as exc:
            last_error = exc
            if "404" in str(exc):
                continue
            st.warning(f"Αδυναμία ανάγνωσης sheet '{worksheet_name}': {exc}")
            return pd.DataFrame(columns=columns)

    st.warning(f"Αδυναμία ανάγνωσης sheet '{sheet_name}'. Ελέγξτε το worksheet. ({last_error})")
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
                is_transient_server = "500" in message or "503" in message or "UNAVAILABLE" in message or "INTERNAL" in message
                is_not_found = "404" in message

                if (is_rate_limited or is_transient_server) and attempt < retries - 1:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                if is_not_found:
                    break

                st.error(f"Σφάλμα εγγραφής στο '{worksheet_name}': {exc}")
                return False

    st.error(f"Αποτυχία εγγραφής στο '{sheet_name}'. ({last_error})")
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
    num_cols = num_cols or []
    df_local = ensure_ids(df.copy())
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


def clamp_pct(value, total):
    total_val = to_money(total)
    if total_val <= 0:
        return 0
    return max(0, min(100, (to_money(value) / total_val) * 100))


def render_progress_line(label, value, total, color_class, right_text=None):
    pct = clamp_pct(value, total)
    right = right_text or f"{format_currency(value)} / {format_currency(total)}"
    st.markdown(
        f"""
        <div class="progress-row">
            <div class="progress-top">
                <span>{label}</span>
                <span>{right}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill {color_class}" style="width: {pct:.2f}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_visual_card(title, subtitle, total_amount, paid_me, paid_father, target_me=None, target_father=None):
    total_amount = to_money(total_amount)
    paid_me = to_money(paid_me)
    paid_father = to_money(paid_father)
    total_paid = paid_me + paid_father
    remaining = max(total_amount - total_paid, 0)

    st.markdown(
        f"""
        <div class="visual-card">
            <div class="visual-card-title">{title}</div>
            <div class="visual-card-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )

    render_progress_line(
        "Σύνολο καλυμμένο",
        total_paid,
        total_amount,
        "fill-total",
        f"{format_currency(total_paid)} / {format_currency(total_amount)}",
    )

    if target_me is not None:
        target_me = to_money(target_me)
        remain_me = max(target_me - paid_me, 0)
        render_progress_line(
            "Εγώ",
            paid_me,
            target_me,
            "fill-me",
            f"{format_currency(paid_me)} από {format_currency(target_me)} | Υπόλοιπο {format_currency(remain_me)}",
        )
    else:
        render_progress_line("Εγώ", paid_me, total_amount, "fill-me", format_currency(paid_me))

    if target_father is not None:
        target_father = to_money(target_father)
        remain_father = max(target_father - paid_father, 0)
        render_progress_line(
            "Πατέρας",
            paid_father,
            target_father,
            "fill-father",
            f"{format_currency(paid_father)} από {format_currency(target_father)} | Υπόλοιπο {format_currency(remain_father)}",
        )
    else:
        render_progress_line("Πατέρας", paid_father, total_amount, "fill-father", format_currency(paid_father))

    render_progress_line("Απομένει", remaining, total_amount, "fill-remain", format_currency(remaining))
    st.markdown("</div>", unsafe_allow_html=True)


def apply_expense_filters(df, filters):
    if df.empty:
        return df
    local = df.copy()
    local["Ποσό"] = money_series(local, "Ποσό")

    if filters.get("categories"):
        local = local[local["Κατηγορία"].isin(filters["categories"])]
    if filters.get("payers"):
        local = local[local["Πληρωτής"].isin(filters["payers"])]

    if "Ημερομηνία" in local.columns:
        parsed_dates = pd.to_datetime(local["Ημερομηνία"], errors="coerce")
        start = filters.get("start_date")
        end = filters.get("end_date")
        if start is not None:
            local = local[parsed_dates >= pd.Timestamp(start)]
        if end is not None:
            local = local[parsed_dates <= pd.Timestamp(end)]

    search = filters.get("search", "").strip().lower()
    if search:
        cat_series = local["Κατηγορία"].astype(str)
        type_series = local["Είδος"].astype(str)
        notes_series = local["Σημειώσεις"].astype(str)
        payer_series = local["Πληρωτής"].astype(str)
        combined = (cat_series + " " + type_series + " " + notes_series + " " + payer_series).str.lower()
        local = local[combined.str.contains(search, na=False)]

    return local


def apply_material_filters(df, filters):
    if df.empty:
        return df
    local = df.copy()
    local["Σύνολο"] = money_series(local, "Σύνολο")

    if filters.get("categories"):
        local = local[local["Κατηγορία"].isin(filters["categories"])]
    if filters.get("payers") and "Πληρωτής" in local.columns:
        local = local[local["Πληρωτής"].isin(filters["payers"])]

    search = filters.get("search", "").strip().lower()
    if search:
        material_series = local["Υλικό"].astype(str)
        supplier_series = local["Προμηθευτής"].astype(str)
        notes_series = local["Σημειώσεις"].astype(str)
        combined = (material_series + " " + supplier_series + " " + notes_series).str.lower()
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


def calculate_fee_status(df_fee, df_exp):
    if df_fee.empty:
        return pd.DataFrame()

    local_fee = normalize_fee_df(df_fee)
    local_exp = df_exp.copy()
    if not local_exp.empty:
        local_exp["Ποσό"] = money_series(local_exp, "Ποσό")

    results = []
    for _, fee in local_fee.iterrows():
        cat = str(fee.get("Κατηγορία", "")).strip()
        if not cat:
            continue

        total = to_money(fee.get("Συνολικό_Ποσό", 0))
        share_me = to_money(fee.get("Συμμετοχή_Εγώ", 0))
        share_father = to_money(fee.get("Συμμετοχή_Πατέρας", 0))

        relevant = (
            local_exp[(local_exp["Κατηγορία"] == cat) & (local_exp["Είδος"] == "Αμοιβή")]
            if not local_exp.empty
            else pd.DataFrame()
        )

        paid_me = money_series(relevant[relevant["Πληρωτής"] == "Εγώ"], "Ποσό").sum()
        paid_father = money_series(relevant[relevant["Πληρωτής"] == "Πατέρας"], "Ποσό").sum()

        results.append(
            {
                "_id": fee.get("_id", ""),
                "Κατηγορία": cat,
                "Περιγραφή": fee.get("Περιγραφή", f"Αμοιβή {cat}"),
                "Συνολικό_Ποσό": total,
                "Συμμετοχή_Εγώ": share_me,
                "Συμμετοχή_Πατέρας": share_father,
                "Πλήρωσα Εγώ": paid_me,
                "Πλήρωσε Πατέρας": paid_father,
                "Υπόλοιπο Εγώ": max(share_me - paid_me, 0),
                "Υπόλοιπο Πατέρας": max(share_father - paid_father, 0),
                "Σημειώσεις": fee.get("Σημειώσεις", ""),
            }
        )
    return pd.DataFrame(results)


def calculate_material_split(df_material):
    if df_material.empty:
        return pd.DataFrame()

    local = df_material.copy()
    local["Σύνολο"] = money_series(local, "Σύνολο")
    summary = []

    for cat in sorted(local["Κατηγορία"].dropna().astype(str).unique()):
        sub = local[local["Κατηγορία"] == cat]
        summary.append(
            {
                "Κατηγορία": cat,
                "Σύνολο": sub["Σύνολο"].sum(),
                "Εγώ": sub[sub["Πληρωτής"] == "Εγώ"]["Σύνολο"].sum(),
                "Πατέρας": sub[sub["Πληρωτής"] == "Πατέρας"]["Σύνολο"].sum(),
                "Κοινό": sub[sub["Πληρωτής"] == "Κοινό"]["Σύνολο"].sum(),
            }
        )
    return pd.DataFrame(summary)


def calculate_total_spend_breakdown(df_exp):
    local = df_exp.copy()
    if local.empty:
        return {
            "fees_me": 0.0,
            "fees_father": 0.0,
            "fees_other": 0.0,
            "materials_me": 0.0,
            "materials_father": 0.0,
            "materials_other": 0.0,
            "other_types_total": 0.0,
            "total_me": 0.0,
            "total_father": 0.0,
        }

    local["Ποσό"] = money_series(local, "Ποσό")

    fees = local[local["Είδος"] == "Αμοιβή"].copy()
    mats = local[local["Είδος"] == "Υλικά"].copy()
    others = local[~local["Είδος"].isin(["Αμοιβή", "Υλικά"])].copy()

    def split_by_payer(local_df):
        if local_df.empty:
            return 0.0, 0.0, 0.0
        me = local_df[local_df["Πληρωτής"] == "Εγώ"]["Ποσό"].sum()
        father = local_df[local_df["Πληρωτής"] == "Πατέρας"]["Ποσό"].sum()
        common = local_df[local_df["Πληρωτής"] == "Κοινό"]["Ποσό"].sum()
        other = local_df[~local_df["Πληρωτής"].isin(["Εγώ", "Πατέρας", "Κοινό"])]["Ποσό"].sum()
        return me + common / 2, father + common / 2, other

    fees_me, fees_father, fees_other = split_by_payer(fees)
    mats_me, mats_father, mats_other = split_by_payer(mats)
    other_total = others["Ποσό"].sum() if not others.empty else 0.0

    return {
        "fees_me": fees_me,
        "fees_father": fees_father,
        "fees_other": fees_other,
        "materials_me": mats_me,
        "materials_father": mats_father,
        "materials_other": mats_other,
        "other_types_total": other_total,
        "total_me": fees_me + mats_me,
        "total_father": fees_father + mats_father,
    }


def prepare_timeline(df_tasks):
    if df_tasks.empty:
        return pd.DataFrame()
    local = normalize_task_df(df_tasks)
    rows = []

    for _, row in local.iterrows():
        name = str(row.get("Εργασία", "")).strip()
        if not name:
            continue

        start = parse_date_safe(row.get("Ημερομηνία_Έναρξης"), pd.Timestamp(date.today()))
        end = parse_date_safe(row.get("Ημερομηνία_Λήξης"), pd.Timestamp(date.today() + timedelta(days=1)))

        if pd.isna(start):
            start = pd.Timestamp(date.today())
        if pd.isna(end) or end < start:
            end = start + pd.Timedelta(days=1)

        rows.append(
            {
                "Task": name,
                "Start": start,
                "End": end,
                "Status": row.get("Κατάσταση", "To Do"),
                "Room": row.get("Χώρος", ""),
                "Assignee": row.get("Ανάθεση", ""),
                "Priority": row.get("Προτεραιότητα", ""),
            }
        )
    return pd.DataFrame(rows)


def delete_ui_from_labels(df, label_builder, label_key, button_key, title):
    if df.empty:
        st.info(f"Δεν υπάρχουν εγγραφές για {title.lower()}.")
        return df, False

    labels = {}
    for _, row in df.iterrows():
        row_id = str(row.get("_id", ""))
        labels[row_id] = label_builder(row)

    selected_id = st.selectbox(title, list(labels.keys()), format_func=lambda x: labels.get(x, x), key=label_key)
    if st.button("🗑️ Διαγραφή", key=button_key):
        return delete_by_id(df, selected_id), True
    return df, False


# -----------------------------
# Load Data
# -----------------------------
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = normalize_fee_df(safe_read(SHEET_FEES, FEE_COLUMNS, optional_columns=["Ποσό"]))
df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
df_tasks = normalize_task_df(safe_read(SHEET_TASKS, TASK_COLUMNS))
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)


# -----------------------------
# Pages
# -----------------------------
def render_dashboard(df_exp, df_fee, df_material, df_task):
    st.title("🏠 Dashboard Ανακαίνισης")

    total_actual_paid = money_series(df_exp, "Ποσό").sum()
    total_material_register = money_series(df_material, "Σύνολο").sum()
    fee_status = calculate_fee_status(df_fee, df_exp)
    material_status = calculate_material_split(df_material)
    spend_breakdown = calculate_total_spend_breakdown(df_exp)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Σύνολο πραγματικών πληρωμών", format_currency(total_actual_paid))
    col2.metric("Σύνολο καταχωρήσεων εξόδων", len(df_exp))
    col3.metric("Σύνολο καταχωρήσεων υλικών", len(df_material))
    col4.metric("Εργασίες planning", len(df_task))

    if st.button("Ανάλυση συνεισφοράς", key="open_total_spend_breakdown"):
        st.session_state["show_total_spend_breakdown"] = not st.session_state.get("show_total_spend_breakdown", False)

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
        st.write(f"- Μη αντιστοιχισμένα σε Εγώ/Πατέρα: {format_currency(other_paid)}")
        st.write(f"- Άλλα είδη εξόδων: {format_currency(spend_breakdown['other_types_total'])}")
        st.caption("Ο πληρωτής 'Κοινό' μοιράζεται 50%-50% σε Εγώ και Πατέρα.")

    st.markdown('<div class="dashboard-section-title">Κάρτα αμοιβών συνεργείων</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-section-subtitle">Μία κάρτα ανά κατηγορία με σύνολο καλυμμένο, Εγώ, Πατέρας και υπόλοιπο.</div>',
        unsafe_allow_html=True,
    )

    if fee_status.empty:
        st.info("Δεν υπάρχουν αμοιβές.")
    else:
        fee_cols = st.columns(2)
        for i, (_, row) in enumerate(fee_status.iterrows()):
            with fee_cols[i % 2]:
                render_visual_card(
                    f"Κάρτα {row['Κατηγορία']}",
                    row["Περιγραφή"],
                    row["Συνολικό_Ποσό"],
                    row["Πλήρωσα Εγώ"],
                    row["Πλήρωσε Πατέρας"],
                    row["Συμμετοχή_Εγώ"],
                    row["Συμμετοχή_Πατέρας"],
                )

    st.markdown('<div class="dashboard-section-title">Κάρτα υλικών</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="dashboard-section-subtitle">Μία κάρτα ανά κατηγορία από το Materials sheet, όπως στο σκίτσο σου.</div>',
        unsafe_allow_html=True,
    )

    if material_status.empty:
        st.info("Δεν υπάρχουν υλικά.")
    else:
        mat_cols = st.columns(2)
        for i, (_, row) in enumerate(material_status.iterrows()):
            with mat_cols[i % 2]:
                render_visual_card(
                    f"Κάρτα {row['Κατηγορία']}",
                    "Σύνολο αγορών υλικών",
                    row["Σύνολο"],
                    row["Εγώ"] + row["Κοινό"] / 2,
                    row["Πατέρας"] + row["Κοινό"] / 2,
                )

    st.markdown('<div class="dashboard-section-title">🗓️ Timeline / Gantt</div>', unsafe_allow_html=True)
    timeline = prepare_timeline(df_task)
    if timeline.empty:
        st.info("Δεν υπάρχουν εργασίες στο planning.")
    else:
        fig = px.timeline(
            timeline,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Status",
            hover_data=["Room", "Assignee", "Priority"],
            color_discrete_map={
                "To Do": "#c9a96b",
                "Doing": "#2e6f95",
                "Done": "#3f7d6b",
            },
        )
        fig.update_layout(height=430)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)


def render_expenses(df):
    st.subheader("💰 Έξοδα")

    raw_df = df.copy()
    filtered_df = raw_df.copy()

    c1, c2, c3, c4 = st.columns(4)
    search_local = c1.text_input("Αναζήτηση", key="search_expenses_local")
    selected_categories = c2.multiselect("Κατηγορίες", EXPENSE_CATEGORIES, key="filter_exp_cat")
    selected_payers = c3.multiselect("Πληρωτής", PAYERS, key="filter_exp_payer")
    selected_type = c4.selectbox("Είδος", ["Όλα"] + EXPENSE_TYPES, key="filter_exp_type")

    if search_local.strip() or selected_categories or selected_payers:
        filtered_df = apply_expense_filters(
            raw_df,
            {
                "categories": selected_categories,
                "payers": selected_payers,
                "start_date": None,
                "end_date": None,
                "search": search_local,
            },
        )
    if selected_type != "Όλα" and not filtered_df.empty:
        filtered_df = filtered_df[filtered_df["Είδος"] == selected_type]

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
                updated = append_row(raw_df, new, EXPENSE_COLUMNS)
                with st.spinner("Αποθήκευση..."):
                    ok = safe_write(SHEET_EXPENSES, updated)
                if ok:
                    st.toast("Αποθηκεύτηκε", icon="✅")
                    st.rerun()

    st.markdown("### Ομαδοποίηση εξόδων")
    if not filtered_df.empty:
        group_view = filtered_df.copy()
        group_view["Ποσό"] = money_series(group_view, "Ποσό")
        grouped = (
            group_view.groupby(["Κατηγορία", "Είδος", "Πληρωτής"], as_index=False)["Ποσό"]
            .sum()
            .sort_values(["Κατηγορία", "Είδος", "Πληρωτής"])
        )
        st.dataframe(grouped, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εγγραφές για το τρέχον φίλτρο.")

    tabs = st.tabs(["Αναλυτικά", "Επεξεργασία", "Διαγραφή"])

    with tabs[0]:
        show_table(filtered_df)

    with tabs[1]:
        edited = editable_sheet(raw_df, EXPENSE_COLUMNS, "expenses_editor", num_cols=["Ποσό"])
        if st.button("💾 Αποθήκευση αλλαγών", key="save_exp"):
            if safe_write(SHEET_EXPENSES, edited):
                st.success("Οι αλλαγές αποθηκεύτηκαν.")
                st.rerun()

    with tabs[2]:
        delete_source = filtered_df if not filtered_df.empty else raw_df
        new_df, should_delete = delete_ui_from_labels(
            delete_source,
            lambda row: f"{row.get('Ημερομηνία', '')} | {row.get('Κατηγορία', '')} | {row.get('Είδος', '')} | {format_currency(row.get('Ποσό', 0))} | {row.get('Πληρωτής', '')}",
            "del_exp_label",
            "del_exp_btn",
            "Επέλεξε καταχώρηση εξόδων",
        )
        if should_delete:
            full_new_df = delete_by_id(raw_df, new_df["_id"].astype(str).tolist()[0]) if len(new_df) == len(delete_source) - 1 and not delete_source.empty else delete_by_id(raw_df, st.session_state.get("del_exp_label"))
            # ασφαλής επαναϋπολογισμός από το selected id
            selected_id = st.session_state.get("del_exp_label")
            if selected_id:
                full_new_df = delete_by_id(raw_df, selected_id)
                if safe_write(SHEET_EXPENSES, full_new_df):
                    st.success("Η εγγραφή διαγράφηκε.")
                    st.rerun()


def render_fees(df_fee, df_exp):
    st.subheader("💼 Αμοιβές")
    raw_df = normalize_fee_df(df_fee.copy())

    with st.expander("➕ Νέα αμοιβή"):
        with st.form("fee_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                total_amount = st.number_input("Συνολικό ποσό (€)", min_value=0.0, step=100.0)
            with col2:
                share_me = st.number_input("Συμμετοχή Εγώ (€)", min_value=0.0, step=50.0)
                share_father = st.number_input("Συμμετοχή Πατέρας (€)", min_value=0.0, step=50.0)
            desc = st.text_input("Περιγραφή")
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση"):
                if share_me == 0 and share_father == 0 and total_amount > 0:
                    share_me = total_amount / 2
                    share_father = total_amount / 2

                new = {
                    "Κατηγορία": cat,
                    "Περιγραφή": desc,
                    "Συνολικό_Ποσό": total_amount,
                    "Συμμετοχή_Εγώ": share_me,
                    "Συμμετοχή_Πατέρας": share_father,
                    "Σημειώσεις": notes,
                }
                updated = append_row(raw_df, new, FEE_COLUMNS)
                if safe_write(SHEET_FEES, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()

    status = calculate_fee_status(raw_df, df_exp)
    if status.empty:
        st.info("Δεν υπάρχουν αμοιβές.")
        return

    show_table(status.drop(columns=["_id"], errors="ignore"))

    st.markdown("### Visual κάρτες αμοιβών")
    cols = st.columns(2)
    for i, (_, row) in enumerate(status.iterrows()):
        with cols[i % 2]:
            render_visual_card(
                f"Κάρτα {row['Κατηγορία']}",
                row["Περιγραφή"],
                row["Συνολικό_Ποσό"],
                row["Πλήρωσα Εγώ"],
                row["Πλήρωσε Πατέρας"],
                row["Συμμετοχή_Εγώ"],
                row["Συμμετοχή_Πατέρας"],
            )


def render_materials(df):
    st.subheader("📦 Υλικά")

    raw_df = df.copy()
    filtered_df = raw_df.copy()

    c1, c2, c3 = st.columns(3)
    search_local = c1.text_input("Αναζήτηση υλικών", key="search_materials_local")
    selected_categories = c2.multiselect("Κατηγορίες υλικών", EXPENSE_CATEGORIES, key="filter_mat_cat")
    selected_payers = c3.multiselect("Πληρωτής υλικών", PAYERS, key="filter_mat_payer")

    if search_local.strip() or selected_categories or selected_payers:
        filtered_df = apply_material_filters(
            raw_df,
            {"categories": selected_categories, "payers": selected_payers, "search": search_local},
        )

    with st.expander("➕ Νέο υλικό"):
        with st.form("material_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                name = st.text_input("Υλικό")
                qty = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
                payer = st.selectbox("Πληρωτής", PAYERS)
            with col2:
                unit = st.selectbox("Μονάδα", MATERIAL_UNITS)
                price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
                supplier = st.text_input("Προμηθευτής")
                status = st.selectbox("Κατάσταση", MATERIAL_STATUS)
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
                    "Κατάσταση": status,
                    "Σημειώσεις": notes,
                }
                updated = append_row(raw_df, new, MATERIAL_COLUMNS)
                if safe_write(SHEET_MATERIALS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()

    tabs = st.tabs(["Αναλυτικά", "Ομαδοποιημένα", "Επεξεργασία", "Διαγραφή"])

    with tabs[0]:
        show_table(filtered_df)

    with tabs[1]:
        if not filtered_df.empty:
            grouped = calculate_material_split(filtered_df)
            st.dataframe(grouped, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν εγγραφές για το τρέχον φίλτρο.")

    with tabs[2]:
        edited = editable_sheet(raw_df, MATERIAL_COLUMNS, "materials_editor", num_cols=["Ποσότητα", "Τιμή_Μονάδας", "Σύνολο"])
        edited["Σύνολο"] = edited["Ποσότητα"].apply(to_money) * edited["Τιμή_Μονάδας"].apply(to_money)
        if st.button("💾 Αποθήκευση αλλαγών", key="save_mat"):
            if safe_write(SHEET_MATERIALS, edited):
                st.success("Οι αλλαγές αποθηκεύτηκαν.")
                st.rerun()

    with tabs[3]:
        delete_source = filtered_df if not filtered_df.empty else raw_df
        new_df, should_delete = delete_ui_from_labels(
            delete_source,
            lambda row: f"{row.get('Υλικό', '')} | {row.get('Κατηγορία', '')} | {format_currency(row.get('Σύνολο', 0))}",
            "del_mat_label",
            "del_mat_btn",
            "Επέλεξε υλικό",
        )
        if should_delete:
            selected_id = st.session_state.get("del_mat_label")
            if selected_id:
                full_new_df = delete_by_id(raw_df, selected_id)
                if safe_write(SHEET_MATERIALS, full_new_df):
                    st.success("Η εγγραφή διαγράφηκε.")
                    st.rerun()


def render_contacts(df):
    st.subheader("📞 Επαφές")
    with st.expander("➕ Νέα επαφή"):
        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Όνομα")
                role = st.selectbox("Ρόλος", CONTACT_ROLES)
            with col2:
                phone = st.text_input("Τηλέφωνο")
                email = st.text_input("Email")
            area = st.text_input("Περιοχή")
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and name:
                new = {
                    "Όνομα": name,
                    "Ρόλος": role,
                    "Τηλέφωνο": phone,
                    "Email": email,
                    "Περιοχή": area,
                    "Σημειώσεις": notes,
                }
                updated = append_row(df, new, CONTACT_COLUMNS)
                if safe_write(SHEET_CONTACTS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)


def render_loans(df):
    st.subheader("🏦 Δάνειο")
    current_df = df.copy()

    with st.expander("➕ Νέο δάνειο"):
        with st.form("loan_form"):
            col1, col2 = st.columns(2)
            with col1:
                desc = st.text_input("Περιγραφή")
                principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, step=1000.0)
                start_date = st.date_input("Ημερομηνία έναρξης", value=date.today())
            with col2:
                rate = st.number_input("Επιτόκιο (%)", min_value=0.0, step=0.1)
                months = st.number_input("Μήνες", min_value=1, step=1)
                status = st.selectbox("Κατάσταση", ["Ενεργό", "Υπό εξέταση", "Εξοφλήθηκε"])
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση"):
                clean_desc = desc.strip()
                months_int = int(months)
                principal_val = to_money(principal)
                rate_val = to_money(rate)

                if not clean_desc:
                    st.warning("Συμπλήρωσε περιγραφή δανείου.")
                elif months_int <= 0:
                    st.warning("Οι μήνες πρέπει να είναι > 0.")
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
                        "Κατάσταση": status,
                        "Σημειώσεις": notes,
                    }
                    updated = append_row(current_df, new, LOAN_COLUMNS)
                    if safe_write(SHEET_LOANS, updated):
                        st.success("Το δάνειο αποθηκεύτηκε.")
                        st.rerun()

    show_table(current_df)


def render_timeline_page(df):
    st.subheader("🗓️ Timeline / Gantt")
    current_df = normalize_task_df(df.copy())

    with st.expander("➕ Νέα εργασία planning"):
        with st.form("task_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Εργασία")
                room = st.selectbox("Χώρος", ROOMS)
                status = st.selectbox("Κατάσταση", TASK_STATUSES)
                priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES)
            with col2:
                start = st.date_input("Έναρξη")
                end = st.date_input("Λήξη")
                assignee = st.text_input("Ανάθεση")
                cost = st.number_input("Κόστος (€)", min_value=0.0, step=10.0)
            notes = st.text_input("Σημειώσεις")

            if st.form_submit_button("Αποθήκευση"):
                clean_name = name.strip()
                if not clean_name:
                    st.warning("Συμπλήρωσε όνομα εργασίας.")
                elif end < start:
                    st.error("Η λήξη δεν μπορεί να είναι πριν την έναρξη.")
                else:
                    new = {
                        "Εργασία": clean_name,
                        "Χώρος": room,
                        "Κατάσταση": status,
                        "Ημερομηνία_Έναρξης": str(start),
                        "Ημερομηνία_Λήξης": str(end),
                        "Κόστος": cost,
                        "Προτεραιότητα": priority,
                        "Ανάθεση": assignee.strip(),
                        "Σημειώσεις": notes,
                    }
                    updated = append_row(current_df, new, TASK_COLUMNS)
                    if safe_write(SHEET_TASKS, updated):
                        st.success("Η εργασία αποθηκεύτηκε.")
                        st.rerun()

    timeline = prepare_timeline(current_df)
    if not timeline.empty:
        fig = px.timeline(
            timeline,
            x_start="Start",
            x_end="End",
            y="Task",
            color="Status",
            hover_data=["Room", "Assignee", "Priority"],
            color_discrete_map={
                "To Do": "#c9a96b",
                "Doing": "#2e6f95",
                "Done": "#3f7d6b",
            },
        )
        fig.update_layout(height=470)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    show_table(current_df)


def render_tasks(df):
    st.subheader("📋 Εργασίες")
    show_table(normalize_task_df(df))


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
                desc = st.text_input("Περιγραφή")
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and provider:
                new = {
                    "Πάροχος": provider,
                    "Περιγραφή": desc,
                    "Ποσό": amount,
                    "Κατηγορία": cat,
                    "Σημειώσεις": notes,
                }
                updated = append_row(df, new, OFFER_COLUMNS)
                if safe_write(SHEET_OFFERS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)


def render_gallery(df):
    st.subheader("📸 Gallery")
    st.caption("Για πολλά αρχεία, προτίμησε URL αντί για base64 στο sheet.")
    with st.expander("➕ Νέα εικόνα"):
        with st.form("gallery_form"):
            room = st.selectbox("Χώρος", ROOMS)
            title = st.text_input("Τίτλος")
            img_type = st.selectbox("Τύπος", IMAGE_TYPES)
            uploaded = st.file_uploader("Εικόνα", type=["jpg", "png", "jpeg"])
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and uploaded:
                img = Image.open(uploaded).convert("RGB")
                img.thumbnail((800, 800))
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=75)
                img_data = base64.b64encode(buffer.getvalue()).decode()
                new = {
                    "Χώρος": room,
                    "Τίτλος": title,
                    "Τύπος": img_type,
                    "Image_URL": "",
                    "Image_Data": img_data,
                    "Σημειώσεις": notes,
                }
                updated = append_row(df, new, GALLERY_COLUMNS)
                if safe_write(SHEET_GALLERY, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()

    if not df.empty:
        preview = df.tail(10)
        cols = st.columns(3)
        for i, (_, row) in enumerate(preview.iterrows()):
            with cols[i % 3]:
                if row.get("Image_Data"):
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", use_container_width=True)
                st.caption(f"{row.get('Χώρος', '')} - {row.get('Τίτλος', '')}")


def render_analytics(df_exp, df_material, df_fee):
    st.subheader("📊 Αναλύσεις")

    actual_total = money_series(df_exp, "Ποσό").sum()
    material_register_total = money_series(df_material, "Σύνολο").sum()

    c1, c2 = st.columns(2)
    c1.metric("Σύνολο πραγματικών πληρωμών", format_currency(actual_total))
    c2.metric("Σύνολο materials register", format_currency(material_register_total))

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
        st.info("Δεν υπάρχουν budget αμοιβών.")
    else:
        fee_budget = normalize_fee_df(df_fee)
        fee_budget["Συνολικό_Ποσό"] = fee_budget["Συνολικό_Ποσό"].apply(to_money)
        budget_by_cat = fee_budget.groupby("Κατηγορία", as_index=False)["Συνολικό_Ποσό"].sum().rename(columns={"Συνολικό_Ποσό": "Budget"})

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
inject_v23_theme()
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
        fee_df = normalize_fee_df(safe_read(SHEET_FEES, FEE_COLUMNS, optional_columns=["Ποσό"]))
        mat_df = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
        task_df = normalize_task_df(safe_read(SHEET_TASKS, TASK_COLUMNS))
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
    exp_filtered = apply_expense_filters(df_expenses, global_filters)
    mat_filtered = apply_material_filters(df_materials, global_filters)
    render_dashboard(exp_filtered, df_fees, mat_filtered, df_tasks)
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
    render_timeline_page(df_tasks)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "📸 Gallery":
    render_gallery(df_gallery)
elif menu == "📊 Αναλύσεις":
    exp_filtered = apply_expense_filters(df_expenses, global_filters)
    mat_filtered = apply_material_filters(df_materials, global_filters)
    render_analytics(exp_filtered, mat_filtered, df_fees)
elif menu == "🧮 Calculator":
    render_calculator()

