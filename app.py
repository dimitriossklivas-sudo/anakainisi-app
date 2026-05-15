import base64
import io
import time
import uuid
from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Methana Earth & Fire v3", layout="wide")
APP_VERSION = "v3.0"
DEFAULT_SHEET_TTL_SECONDS = 180
APP_BUILDER = "ΣΚΛΙΒΑΣ Σ. ΔΗΜΗΤΡΙΟΣ"


# -----------------------------
# Google Sheets Connection
# -----------------------------
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


def clear_gsheet_read_cache():
    st.session_state["_sheet_cache"] = {}


def get_sheet_cache_store():
    return st.session_state.setdefault("_sheet_cache", {})


def build_sheet_cache_key(sheet_name, columns, optional_columns=None):
    optional_columns = optional_columns or []
    all_columns = list(dict.fromkeys(columns + optional_columns))
    return f"{sheet_name}|{'|'.join(all_columns)}"


def get_cached_sheet(sheet_name, columns, ttl_seconds, optional_columns=None):
    cache_key = build_sheet_cache_key(sheet_name, columns, optional_columns)
    cached = get_sheet_cache_store().get(cache_key)
    if not cached:
        return None
    if ttl_seconds is not None and ttl_seconds >= 0:
        age = time.time() - cached["timestamp"]
        if age > ttl_seconds:
            return None
    return cached["df"].copy()


def set_cached_sheet(sheet_name, columns, df, optional_columns=None):
    cache_key = build_sheet_cache_key(sheet_name, columns, optional_columns)
    get_sheet_cache_store()[cache_key] = {
        "timestamp": time.time(),
        "df": df.copy(),
    }


def refresh_cached_sheet_timestamp(sheet_name, columns, optional_columns=None):
    cache_key = build_sheet_cache_key(sheet_name, columns, optional_columns)
    cached = get_sheet_cache_store().get(cache_key)
    if cached:
        cached["timestamp"] = time.time()


def invalidate_sheet_cache(sheet_name):
    cache_store = get_sheet_cache_store()
    keys_to_delete = [key for key in cache_store if key.startswith(f"{sheet_name}|")]
    for key in keys_to_delete:
        del cache_store[key]


def inject_v3_theme():
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
            --app-fg: #1f2328;
            --subtle-fg: #6a6763;
            --card-bg: #ffffff;
            --card-border: rgba(47, 52, 55, 0.10);
            --progress-fg: #2a2d30;
            --progress-track-bg: #e8dfd2;
            --badge-bg: #f0e5d6;
            --badge-fg: #6b533c;
            --badge-border: rgba(93, 71, 51, 0.14);
        }}
        html[data-theme="dark"],
        body[data-theme="dark"],
        .stApp[data-theme="dark"],
        [data-theme="dark"] {{
            --app-fg: #f5f7fa;
            --subtle-fg: #c7d0d8;
            --card-bg: #1f2428;
            --card-border: rgba(233, 237, 241, 0.16);
            --progress-fg: #e9edf1;
            --progress-track-bg: #313840;
            --badge-bg: #2a3238;
            --badge-fg: #f0e5d2;
            --badge-border: rgba(233, 237, 241, 0.14);
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
        .dashboard-section-title {{
            font-size: 1.08rem;
            font-weight: 800;
            color: var(--app-fg);
            margin-top: 14px;
            margin-bottom: 8px;
        }}
        .dashboard-section-subtitle {{
            font-size: 0.9rem;
            color: var(--subtle-fg);
            margin-bottom: 10px;
        }}
        .visual-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 14px 14px 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        }}
        .visual-card-title {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--app-fg);
            margin-bottom: 4px;
        }}
        .visual-card-subtitle {{
            font-size: 0.86rem;
            color: var(--subtle-fg);
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
            color: var(--progress-fg);
            margin-bottom: 4px;
        }}
        .progress-track {{
            width: 100%;
            height: 13px;
            border-radius: 999px;
            background: var(--progress-track-bg);
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
            background: var(--badge-bg);
            color: var(--badge-fg);
            border: 1px solid var(--badge-border);
            margin-right: 6px;
            margin-bottom: 6px;
        }}
        .check-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 12px 14px;
            margin-bottom: 12px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        }}
        .check-card-title {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--app-fg);
            margin-bottom: 8px;
        }}
        .check-room-badge {{
            display: inline-block;
            padding: 6px 10px;
            background: var(--badge-bg);
            color: var(--badge-fg);
            border: 1px solid var(--badge-border);
            font-size: 0.78rem;
            border-radius: 999px;
            margin-right: 6px;
            margin-bottom: 6px;
            font-weight: 700;
        }}
        .stApp, .stApp * {{
            font-family: "Aptos", "Segoe UI", "Tahoma", sans-serif;
        }}
        h1, h2, h3, .methana-hero .title, .page-banner-title {{
            font-family: "Constantia", "Georgia", serif;
        }}
        .hero-pill-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 10px;
        }}
        .page-banner {{
            position: relative;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            gap: 18px;
            padding: 22px 24px;
            margin: 6px 0 18px 0;
            border-radius: 22px;
            overflow: hidden;
            color: #ffffff;
            background:
                radial-gradient(circle at top right, rgba(201, 169, 107, 0.28), transparent 34%),
                linear-gradient(135deg, rgba(28, 27, 26, 0.98) 0%, rgba(63, 71, 79, 0.95) 52%, rgba(46, 111, 149, 0.92) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 22px 42px rgba(20, 24, 27, 0.16);
        }}
        .page-banner::after {{
            content: "";
            position: absolute;
            right: -40px;
            top: -44px;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.08);
        }}
        .page-banner-eyebrow {{
            position: relative;
            z-index: 1;
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            opacity: 0.8;
            margin-bottom: 6px;
            font-weight: 700;
        }}
        .page-banner-title {{
            position: relative;
            z-index: 1;
            font-size: 1.55rem;
            line-height: 1.15;
            font-weight: 800;
            letter-spacing: 0.2px;
        }}
        .page-banner-subtitle {{
            position: relative;
            z-index: 1;
            margin-top: 8px;
            font-size: 0.95rem;
            max-width: 760px;
            opacity: 0.92;
        }}
        .page-banner-pills {{
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
        }}
        .hero-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.76rem;
            font-weight: 700;
            color: #f8f4ed;
            background: rgba(255, 255, 255, 0.11);
            border: 1px solid rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(3px);
        }}
        .stat-strip {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 6px 0 16px 0;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.05);
        }}
        .stat-label {{
            font-size: 0.76rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--subtle-fg);
            font-weight: 700;
        }}
        .stat-value {{
            margin-top: 5px;
            font-size: 1.28rem;
            line-height: 1.15;
            color: var(--app-fg);
            font-weight: 800;
        }}
        .stat-note {{
            margin-top: 5px;
            font-size: 0.84rem;
            color: var(--subtle-fg);
        }}
        .sync-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin: 2px 0 14px 0;
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(46, 111, 149, 0.10);
            color: #1e4b67;
            border: 1px solid rgba(46, 111, 149, 0.18);
            font-size: 0.84rem;
            font-weight: 700;
        }}
        .subtle-panel {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 14px 16px;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04);
        }}
        .stButton > button {{
            border-radius: 12px;
            border: 1px solid rgba(47, 52, 55, 0.14);
            background: linear-gradient(180deg, #ffffff 0%, #f4efe6 100%);
            color: #1f2328;
            font-weight: 700;
            box-shadow: 0 8px 16px rgba(47, 52, 55, 0.08);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }}
        .stButton > button:hover {{
            transform: translateY(-1px);
            border-color: rgba(46, 111, 149, 0.32);
            box-shadow: 0 10px 22px rgba(46, 111, 149, 0.12);
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 999px;
            padding: 8px 14px;
            border: 1px solid rgba(47, 52, 55, 0.12);
            background: rgba(255, 255, 255, 0.62);
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(135deg, #2f3437 0%, #2e6f95 100%) !important;
            color: #ffffff !important;
            border-color: transparent !important;
        }}
        .stExpander {{
            border: 1px solid var(--card-border) !important;
            border-radius: 18px !important;
            background: rgba(255, 255, 255, 0.52) !important;
            overflow: hidden;
        }}
        .stExpander details summary {{
            padding-top: 2px;
            padding-bottom: 2px;
        }}
        .stApp [data-baseweb="select"] > div,
        .stApp [data-baseweb="input"] > div,
        .stApp [data-baseweb="textarea"] > div,
        .stDateInput > div > div,
        .stNumberInput > div > div {{
            border-radius: 12px !important;
            border: 1px solid rgba(47, 52, 55, 0.14) !important;
            background: rgba(255, 255, 255, 0.88) !important;
            box-shadow: none !important;
        }}
        .stApp div[data-testid="stDataFrame"],
        .stApp div[data-testid="stTable"] {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 18px;
            padding: 6px;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.04);
        }}
        .stApp div[data-testid="stAlert"] {{
            border-radius: 16px;
        }}
        .sidebar-brand {{
            border-radius: 18px;
            padding: 14px 14px 12px 14px;
            margin-bottom: 10px;
            background: linear-gradient(145deg, rgba(201,169,107,0.18) 0%, rgba(255,255,255,0.08) 100%);
            border: 1px solid rgba(255,255,255,0.12);
        }}
        .sidebar-brand-title {{
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 4px;
        }}
        .sidebar-brand-subtitle {{
            font-size: 0.82rem;
            opacity: 0.9;
            line-height: 1.4;
        }}
        .sidebar-brand-meta {{
            margin-top: 10px;
            font-size: 0.74rem;
            opacity: 0.82;
            letter-spacing: 0.03em;
        }}

        @media (prefers-color-scheme: dark) {{
            .stApp {{
                background: linear-gradient(180deg, #111416 0%, #161b1f 100%) !important;
            }}
            .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
                color: #e9edf1 !important;
            }}
            :root {{
                --app-fg: #f5f7fa;
                --subtle-fg: #c7d0d8;
                --card-bg: #1f2428;
                --card-border: rgba(233, 237, 241, 0.16);
                --progress-fg: #e9edf1;
                --progress-track-bg: #313840;
                --badge-bg: #2a3238;
                --badge-fg: #f0e5d2;
                --badge-border: rgba(233, 237, 241, 0.14);
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
            .stat-card,
            .subtle-panel {{
                box-shadow: 0 12px 26px rgba(0, 0, 0, 0.24) !important;
            }}
            .sync-badge {{
                color: #d6e9f5 !important;
                background: rgba(46, 111, 149, 0.22) !important;
                border: 1px solid rgba(127, 183, 220, 0.30) !important;
            }}
            .stButton > button,
            .stTabs [data-baseweb="tab"] {{
                background: linear-gradient(180deg, #20262b 0%, #182026 100%) !important;
                color: #f5f7fa !important;
                border: 1px solid rgba(233, 237, 241, 0.14) !important;
            }}
            .stExpander,
            .stApp [data-baseweb="select"] > div,
            .stApp [data-baseweb="input"] > div,
            .stApp [data-baseweb="textarea"] > div,
            .stDateInput > div > div,
            .stNumberInput > div > div {{
                background: rgba(24, 30, 35, 0.92) !important;
                border: 1px solid rgba(233, 237, 241, 0.14) !important;
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
            <div class="hero-pill-row">
                <span class="hero-pill">Methana renovation suite</span>
                <span class="hero-pill">Version {APP_VERSION}</span>
                <span class="hero-pill">Built by {APP_BUILDER}</span>
            </div>
            <div class="title">Methana Earth & Fire</div>
            <div class="subtitle">Operational clarity for budget, checklist tracking, and renovation progress.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_banner(title, subtitle, pills=None):
    pills_html = "".join(f'<span class="hero-pill">{escape(str(item))}</span>' for item in (pills or []))
    st.markdown(
        f"""
        <div class="page-banner">
            <div>
                <div class="page-banner-eyebrow">Renovation control room</div>
                <div class="page-banner-title">{escape(str(title))}</div>
                <div class="page-banner-subtitle">{escape(str(subtitle))}</div>
            </div>
            <div class="page-banner-pills">{pills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_strip(items):
    cards = []
    for item in items:
        label = escape(str(item.get("label", "")))
        value = escape(str(item.get("value", "")))
        note = escape(str(item.get("note", "")))
        cards.append(
            f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-note">{note}</div>
            </div>
            """
        )
    st.markdown(f'<div class="stat-strip">{"".join(cards)}</div>', unsafe_allow_html=True)


def count_unique_nonempty(df, column):
    if df.empty or column not in df.columns:
        return 0
    values = df[column].dropna().astype(str).str.strip()
    return int((values != "").sum() if column == "_id" else values[values != ""].nunique())


def count_selected_filters(*groups):
    total = 0
    for group in groups:
        if isinstance(group, str):
            total += 1 if group.strip() else 0
        elif group is not None:
            total += len(group)
    return total


SHEET_EXPENSES = "Expenses"
SHEET_FEES = "Fees"
SHEET_CONTACTS = "Contacts"
SHEET_MATERIALS = "Materials"
SHEET_LOANS = "Loan"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"
SHEET_CHECKLIST = "Checklist"

SHEET_ALIASES = {
    "Expenses": ["Expense", "Έξοδα"],
    "Fees": ["Fee", "Αμοιβές"],
    "Contacts": ["Contact", "Επαφές"],
    "Materials": ["Material", "Υλικά"],
    "Loan": ["Loans", "Δάνειο"],
    "Progress": ["Tasks", "Timeline", "Χρονοδιάγραμμα"],
    "Offers": ["Offer", "Προσφορές"],
    "Gallery": ["Photos", "Φωτογραφίες"],
    "Checklist": ["Check List", "ToDo", "Λίστα Ελέγχου"],
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
CHECKLIST_COLUMNS = ["_id", "Χώρος", "Εργασία", "Ολοκληρώθηκε", "Προτεραιότητα", "Σημειώσεις"]
CHECK_COL_ROOM = CHECKLIST_COLUMNS[1]
CHECK_COL_TASK = CHECKLIST_COLUMNS[2]
CHECK_COL_DONE = CHECKLIST_COLUMNS[3]
CHECK_COL_PRIORITY = CHECKLIST_COLUMNS[4]
CHECK_COL_NOTES = CHECKLIST_COLUMNS[5]
TASK_COL_NAME = TASK_COLUMNS[1]
TASK_COL_ROOM = TASK_COLUMNS[2]
TASK_COL_STATUS = TASK_COLUMNS[3]
TASK_COL_START = TASK_COLUMNS[4]
TASK_COL_END = TASK_COLUMNS[5]
TASK_COL_COST = TASK_COLUMNS[6]
TASK_COL_PRIORITY = TASK_COLUMNS[7]
TASK_COL_ASSIGNEE = TASK_COLUMNS[8]
TASK_COL_NOTES = TASK_COLUMNS[9]
CHECKLIST_SYNC_TAG = "[checklist-sync]"

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

CHECKLIST_TEMPLATE = [
    {"Χώρος": "Μπάνιο", "Εργασία": "Υδραυλικά", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Τοποθέτηση πλακάκια", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Αγορά υλικών (τσιμέντο - άμμος)", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Έπιπλο μπάνιου", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Λεκάνη", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Είδη μπάνιου (πετσέτας)", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Χαμηλή", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Ηλεκτρολογικά", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Μπάνιο", "Εργασία": "Μπαταρίες ντουζιέρας - νιπτήρα", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Υδραυλικά", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Ηλεκτρολογικά", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Τοποθέτηση κουζίνας", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Πλακάκια", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Μπαταρία νεροχύτη", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Κουζίνα", "Εργασία": "Φούρνος και εστία", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Μεσαία", "Σημειώσεις": ""},
    {"Χώρος": "Δωμάτια", "Εργασία": "Σοβάτισμα", "Ολοκληρώθηκε": False, "Προτεραιότητα": "Υψηλή", "Σημειώσεις": ""},
]


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


def normalize_checklist_bool(value):
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in ["true", "1", "yes", "y", "ναι", "checked", "done", "completed", "ok"]


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def prepare_checklist_df(df):
    local = df.copy()
    for col in CHECKLIST_COLUMNS:
        if col not in local.columns:
            local[col] = ""
    if local.empty:
        return pd.DataFrame(columns=CHECKLIST_COLUMNS)
    local["_id"] = local["_id"].astype(str)
    local["Ολοκληρώθηκε"] = local["Ολοκληρώθηκε"].apply(normalize_checklist_bool)
    return local[CHECKLIST_COLUMNS]


def serialize_checklist_df(df):
    local = prepare_checklist_df(df.copy())
    if local.empty:
        return pd.DataFrame(columns=CHECKLIST_COLUMNS)
    local["Ολοκληρώθηκε"] = local["Ολοκληρώθηκε"].apply(
        lambda x: "TRUE" if normalize_checklist_bool(x) else "FALSE"
    )
    return local[CHECKLIST_COLUMNS]


def build_checklist_task_note(notes):
    clean_notes = normalize_text(notes)
    if clean_notes:
        return f"{CHECKLIST_SYNC_TAG}\n{clean_notes}"
    return CHECKLIST_SYNC_TAG


def strip_checklist_sync_tag(notes):
    text = normalize_text(notes)
    if not text.startswith(CHECKLIST_SYNC_TAG):
        return text
    return text[len(CHECKLIST_SYNC_TAG):].lstrip(" \n:-|")


def is_synced_checklist_task(row):
    return normalize_text(row.get(TASK_COL_NOTES, "")).startswith(CHECKLIST_SYNC_TAG)


def prepare_task_display_df(df):
    local = normalize_task_df(df.copy())
    if TASK_COL_NOTES in local.columns:
        local[TASK_COL_NOTES] = local[TASK_COL_NOTES].apply(strip_checklist_sync_tag)
    return local


def sync_checklist_to_progress(checklist_df, tasks_df):
    checklist_local = ensure_ids(prepare_checklist_df(checklist_df.copy()))
    tasks_local = normalize_task_df(tasks_df.copy()) if not tasks_df.empty else pd.DataFrame(columns=TASK_COLUMNS)
    existing_by_id = {
        str(row.get("_id", "")): row.to_dict()
        for _, row in tasks_local.iterrows()
    }
    checklist_ids = set(checklist_local["_id"].astype(str))
    preserved_tasks = tasks_local[
        (~tasks_local["_id"].astype(str).isin(checklist_ids))
        & (~tasks_local.apply(is_synced_checklist_task, axis=1))
    ].copy() if not tasks_local.empty else pd.DataFrame(columns=TASK_COLUMNS)

    today_iso = date.today().isoformat()
    synced_rows = []

    for _, item in checklist_local.iterrows():
        row_id = str(item.get("_id", ""))
        existing = existing_by_id.get(row_id, {})
        is_done = normalize_checklist_bool(item.get(CHECK_COL_DONE, False))
        current_start = normalize_text(existing.get(TASK_COL_START, ""))
        current_end = normalize_text(existing.get(TASK_COL_END, ""))
        synced_rows.append(
            {
                "_id": row_id,
                TASK_COL_NAME: normalize_text(item.get(CHECK_COL_TASK, "")),
                TASK_COL_ROOM: normalize_text(item.get(CHECK_COL_ROOM, "")),
                TASK_COL_STATUS: TASK_STATUSES[2] if is_done else TASK_STATUSES[0],
                TASK_COL_START: current_start or (today_iso if is_done else ""),
                TASK_COL_END: current_end or (today_iso if is_done else ""),
                TASK_COL_COST: existing.get(TASK_COL_COST, ""),
                TASK_COL_PRIORITY: normalize_text(item.get(CHECK_COL_PRIORITY, "")),
                TASK_COL_ASSIGNEE: normalize_text(existing.get(TASK_COL_ASSIGNEE, "")),
                TASK_COL_NOTES: build_checklist_task_note(item.get(CHECK_COL_NOTES, "")),
            }
        )

    synced_df = pd.DataFrame(synced_rows, columns=TASK_COLUMNS)
    combined = pd.concat([preserved_tasks[TASK_COLUMNS], synced_df[TASK_COLUMNS]], ignore_index=True)
    return normalize_task_df(combined)


def persist_checklist_and_progress(checklist_df):
    checklist_local = ensure_ids(prepare_checklist_df(checklist_df.copy()))
    current_progress = normalize_task_df(
        safe_read(SHEET_TASKS, TASK_COLUMNS, ttl_seconds=DEFAULT_SHEET_TTL_SECONDS, force_refresh=True)
    )
    synced_progress = sync_checklist_to_progress(checklist_local, current_progress)

    checklist_ok = safe_write(SHEET_CHECKLIST, serialize_checklist_df(checklist_local))
    if not checklist_ok:
        return False

    progress_ok = safe_write(SHEET_TASKS, synced_progress)
    if not progress_ok:
        st.error("Το checklist αποθηκεύτηκε, αλλά το Progress δεν ενημερώθηκε σωστά.")
        return False
    return True


def safe_read(sheet_name, columns, ttl_seconds=DEFAULT_SHEET_TTL_SECONDS, optional_columns=None, force_refresh=False):
    optional_columns = optional_columns or []
    all_columns = list(dict.fromkeys(columns + optional_columns))
    if not force_refresh:
        cached_df = get_cached_sheet(sheet_name, columns, ttl_seconds, optional_columns)
        if cached_df is not None:
            return cached_df
    candidates = [sheet_name] + SHEET_ALIASES.get(sheet_name, [])
    last_error = None
    retries = 3
    stale_df = get_cached_sheet(sheet_name, columns, None, optional_columns)

    for worksheet_name in candidates:
        for attempt in range(retries):
            try:
                read_ttl = 0 if force_refresh else max(int(ttl_seconds or DEFAULT_SHEET_TTL_SECONDS), 30)
                df = conn.read(worksheet=worksheet_name, ttl=read_ttl)
                if df is None or df.empty:
                    empty_df = pd.DataFrame(columns=columns)
                    set_cached_sheet(sheet_name, columns, empty_df, optional_columns)
                    return empty_df
                df = df.dropna(how="all")
                for col in all_columns:
                    if col not in df.columns:
                        df[col] = ""
                if "_id" not in df.columns:
                    df["_id"] = ""
                df["_id"] = df["_id"].astype(str)
                normalized_df = df[all_columns]
                set_cached_sheet(sheet_name, columns, normalized_df, optional_columns)
                return normalized_df
            except Exception as exc:
                last_error = exc
                message = str(exc)
                is_rate_limited = "429" in message or "RATE_LIMIT_EXCEEDED" in message or "RESOURCE_EXHAUSTED" in message
                is_transient_server = "500" in message or "503" in message or "UNAVAILABLE" in message or "INTERNAL" in message
                is_not_found = "404" in message

                if (is_rate_limited or is_transient_server) and attempt < retries - 1:
                    time.sleep(0.8 * (attempt + 1))
                    continue
                if is_not_found:
                    break
                if (is_rate_limited or is_transient_server) and stale_df is not None:
                    refresh_cached_sheet_timestamp(sheet_name, columns, optional_columns)
                    st.info(f"Προσωρινή χρήση cached δεδομένων για το sheet '{sheet_name}' λόγω ορίου Google Sheets.")
                    return stale_df
                st.warning(f"Αδυναμία ανάγνωσης sheet '{worksheet_name}': {exc}")
                if stale_df is not None:
                    return stale_df
                return pd.DataFrame(columns=columns)

    if stale_df is not None:
        refresh_cached_sheet_timestamp(sheet_name, columns, optional_columns)
        st.info(f"Χρήση cached δεδομένων για το sheet '{sheet_name}' έως να επανέλθει το Google Sheets quota.")
        return stale_df

    st.warning(f"Αδυναμία ανάγνωσης sheet '{sheet_name}'. Ελέγξτε το worksheet. ({last_error})")
    return pd.DataFrame(columns=columns)

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
                invalidate_sheet_cache(sheet_name)
                set_cached_sheet(sheet_name, list(df.columns), df.copy())
                return True
            except Exception as exc:
                last_error = exc
                message = str(exc)
                is_rate_limited = "429" in message or "RATE_LIMIT_EXCEEDED" in message or "RESOURCE_EXHAUSTED" in message
                is_transient_server = "500" in message or "503" in message or "UNAVAILABLE" in message or "INTERNAL" in message
                is_not_found = "404" in message
                is_permission_denied = "403" in message or "PERMISSION_DENIED" in message or "does not have permission" in message

                if (is_rate_limited or is_transient_server) and attempt < retries - 1:
                    time.sleep(0.4 * (attempt + 1))
                    continue
                if is_not_found:
                    break
                if is_permission_denied:
                    st.error(
                        f"Σφάλμα δικαιωμάτων στο '{worksheet_name}'. "
                        "Το app μπορεί να διαβάζει ή να βλέπει το sheet, αλλά δεν έχει δικαίωμα εγγραφής. "
                        "Έλεγξε ότι το Google Sheet είναι shared με δικαίωμα Editor στο service account / connection "
                        "και ότι το tab ή το range δεν είναι protected."
                    )
                    return False

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


def editable_sheet(df, columns, key, num_cols=None, bool_cols=None):
    num_cols = num_cols or []
    bool_cols = bool_cols or []
    df_local = ensure_ids(df.copy())
    column_config = {"_id": st.column_config.TextColumn(disabled=True)}
    for col in bool_cols:
        column_config[col] = st.column_config.CheckboxColumn(col)

    edited = st.data_editor(
        df_local,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        num_rows="fixed",
        key=key,
    )
    if "_id" not in edited.columns:
        edited["_id"] = df_local["_id"]
    for col in num_cols:
        if col in edited.columns:
            edited[col] = edited[col].apply(to_money)
    for col in bool_cols:
        if col in edited.columns:
            edited[col] = edited[col].apply(normalize_checklist_bool)
    for col in columns:
        if col not in edited.columns:
            edited[col] = ""
    return edited[columns]


def render_progress_line(label, value, total, color_class, right_text=None):
    total_val = to_money(total)
    pct = (to_money(value) / total_val * 100) if total_val > 0 else 0
    right = right_text or f"{format_currency(value)} / {format_currency(total)}"
    st.markdown(
        f"""
        <div class="progress-row">
            <div class="progress-top">
                <span>{label}</span>
                <span>{right}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill {color_class}" style="width: {min(100, pct):.2f}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_visual_card(title, subtitle, total_amount, paid_me, paid_father, target_me=None, target_father=None):
    st.markdown(
        f"""
        <div class="visual-card">
            <div class="visual-card-title">{title}</div>
            <div class="visual-card-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )

    total_paid = to_money(paid_me) + to_money(paid_father)
    remaining = max(to_money(total_amount) - total_paid, 0)

    render_progress_line("Σύνολο καλυμμένο", total_paid, total_amount, "fill-total")

    if target_me is not None:
        render_progress_line(
            "Εγώ",
            paid_me,
            target_me,
            "fill-me",
            f"{format_currency(paid_me)} από {format_currency(target_me)} | Υπόλοιπο {format_currency(max(to_money(target_me) - to_money(paid_me), 0))}",
        )
    else:
        render_progress_line("Εγώ", paid_me, total_amount, "fill-me", format_currency(paid_me))

    if target_father is not None:
        render_progress_line(
            "Πατέρας",
            paid_father,
            target_father,
            "fill-father",
            f"{format_currency(paid_father)} από {format_currency(target_father)} | Υπόλοιπο {format_currency(max(to_money(target_father) - to_money(paid_father), 0))}",
        )
    else:
        render_progress_line("Πατέρας", paid_father, total_amount, "fill-father", format_currency(paid_father))

    render_progress_line("Απομένει", remaining, total_amount, "fill-remain", format_currency(remaining))
    st.markdown("</div>", unsafe_allow_html=True)


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
                "Συνολικό_Ποσό": to_money(fee.get("Συνολικό_Ποσό", 0)),
                "Συμμετοχή_Εγώ": to_money(fee.get("Συμμετοχή_Εγώ", 0)),
                "Συμμετοχή_Πατέρας": to_money(fee.get("Συμμετοχή_Πατέρας", 0)),
                "Πλήρωσα Εγώ": paid_me,
                "Πλήρωσε Πατέρας": paid_father,
                "Υπόλοιπο Εγώ": max(to_money(fee.get("Συμμετοχή_Εγώ", 0)) - paid_me, 0),
                "Υπόλοιπο Πατέρας": max(to_money(fee.get("Συμμετοχή_Πατέρας", 0)) - paid_father, 0),
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
        dates = pd.to_datetime(local["Ημερομηνία"], errors="coerce")
        start = filters.get("start_date")
        end = filters.get("end_date")
        if start is not None:
            local = local[dates >= pd.Timestamp(start)]
        if end is not None:
            local = local[dates <= pd.Timestamp(end)]
    search = filters.get("search", "").strip().lower()
    if search:
        combined = (
            local["Κατηγορία"].astype(str)
            + " "
            + local["Είδος"].astype(str)
            + " "
            + local["Πληρωτής"].astype(str)
            + " "
            + local["Σημειώσεις"].astype(str)
        ).str.lower()
        local = local[combined.str.contains(search, na=False)]
    return local


def apply_material_filters(df, filters):
    if df.empty:
        return df
    local = df.copy()
    local["Σύνολο"] = money_series(local, "Σύνολο")
    if filters.get("categories"):
        local = local[local["Κατηγορία"].isin(filters["categories"])]
    if filters.get("payers"):
        local = local[local["Πληρωτής"].isin(filters["payers"])]
    search = filters.get("search", "").strip().lower()
    if search:
        combined = (
            local["Υλικό"].astype(str)
            + " "
            + local["Προμηθευτής"].astype(str)
            + " "
            + local["Σημειώσεις"].astype(str)
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
    local = normalize_task_df(df_tasks)
    rows = []
    for _, row in local.iterrows():
        name = str(row.get("Εργασία", "")).strip()
        if not name:
            continue
        has_explicit_dates = normalize_text(row.get("Ημερομηνία_Έναρξης", "")) or normalize_text(row.get("Ημερομηνία_Λήξης", ""))
        if is_synced_checklist_task(row) and not has_explicit_dates:
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
                "TaskLabel": f"{row.get('Χώρος', '')} • {name}" if str(row.get("Χώρος", "")).strip() else name,
                "Start": start,
                "End": end,
                "Status": row.get("Κατάσταση", "To Do"),
                "Room": row.get("Χώρος", ""),
                "Assignee": row.get("Ανάθεση", ""),
                "Priority": row.get("Προτεραιότητα", ""),
            }
        )
    return pd.DataFrame(rows)


def checklist_summary(df):
    if df.empty:
        return pd.DataFrame(columns=["Χώρος", "Σύνολο", "Ολοκληρωμένα", "Υπόλοιπα", "Ποσοστό", "Κατάσταση"])
    rows = []
    for room in sorted(df["Χώρος"].dropna().astype(str).unique()):
        sub = df[df["Χώρος"] == room]
        total = len(sub)
        done = int(sub["Ολοκληρώθηκε"].apply(normalize_checklist_bool).sum())
        pct = (done / total * 100) if total > 0 else 0
        pending = total - done
        if done == 0:
            status = "Δεν ξεκίνησε"
        elif done == total:
            status = "Ολοκληρώθηκε"
        else:
            status = "Σε πρόοδο"
        rows.append(
            {
                "Χώρος": room,
                "Σύνολο": total,
                "Ολοκληρωμένα": done,
                "Υπόλοιπα": pending,
                "Ποσοστό": pct,
                "Κατάσταση": status,
            }
        )
    return pd.DataFrame(rows)


def build_default_checklist_df():
    rows = []
    for item in CHECKLIST_TEMPLATE:
        row = item.copy()
        row["_id"] = str(uuid.uuid4())[:8]
        rows.append(row)
    return pd.DataFrame(rows, columns=CHECKLIST_COLUMNS)


def render_checklist_visual(df):
    summary = checklist_summary(df)
    if summary.empty:
        st.info("Δεν υπάρχει checklist ακόμη.")
        return

    room_cols = st.columns(3)
    for idx, (_, row) in enumerate(summary.iterrows()):
        with room_cols[idx % 3]:
            st.markdown(
                f"""
                <div class="check-card">
                    <div class="check-card-title">{row['Χώρος']}</div>
                    <div class="visual-card-subtitle">{row['Κατάσταση']} • Υπόλοιπα: {int(row['Υπόλοιπα'])}</div>
                """,
                unsafe_allow_html=True,
            )
            render_progress_line(
                "Πρόοδος χώρου",
                row["Ολοκληρωμένα"],
                row["Σύνολο"],
                "fill-total",
                f"{int(row['Ολοκληρωμένα'])}/{int(row['Σύνολο'])} ({row['Ποσοστό']:.0f}%)",
            )
            room_items = df[df["Χώρος"] == row["Χώρος"]]
            for _, item in room_items.iterrows():
                icon = "✅" if normalize_checklist_bool(item["Ολοκληρώθηκε"]) else "⬜"
                st.write(f"{icon} {item['Εργασία']}")
            st.markdown("</div>", unsafe_allow_html=True)


def delete_ui_from_labels(df, label_builder, label_key, button_key, title):
    if df.empty:
        st.info(f"Δεν υπάρχουν εγγραφές για {title.lower()}.")
        return None, False
    labels = {}
    for _, row in df.iterrows():
        row_id = str(row.get("_id", ""))
        labels[row_id] = label_builder(row)
    selected_id = st.selectbox(title, list(labels.keys()), format_func=lambda x: labels.get(x, x), key=label_key)
    if st.button("🗑️ Διαγραφή", key=button_key):
        return selected_id, True
    return None, False


# -----------------------------
# Load Data
# -----------------------------
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = normalize_fee_df(safe_read(SHEET_FEES, FEE_COLUMNS, optional_columns=["Ποσό"]))
df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
df_tasks = normalize_task_df(safe_read(SHEET_TASKS, TASK_COLUMNS, ttl_seconds=DEFAULT_SHEET_TTL_SECONDS))
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)
df_checklist = prepare_checklist_df(safe_read(SHEET_CHECKLIST, CHECKLIST_COLUMNS, ttl_seconds=DEFAULT_SHEET_TTL_SECONDS))


# -----------------------------
# Pages
# -----------------------------
def render_dashboard(df_exp, df_fee, df_material, df_task, df_check):
    total_actual_paid = money_series(df_exp, "Ποσό").sum()
    material_register_total = money_series(df_material, "Σύνολο").sum()
    spend_breakdown = calculate_total_spend_breakdown(df_exp)
    fees = calculate_fee_status(df_fee, df_exp)
    materials = calculate_material_split(df_material)
    checks = checklist_summary(df_check)
    checklist_total = int(checks["Σύνολο"].sum()) if not checks.empty else 0
    checklist_done = int(checks["Ολοκληρωμένα"].sum()) if not checks.empty else 0
    checklist_pct = (checklist_done / checklist_total * 100) if checklist_total > 0 else 0
    rooms_in_progress = checks[checks["Κατάσταση"] == "Σε πρόοδο"]["Χώρος"].tolist() if not checks.empty else []
    completed_rooms = checks[checks["Κατάσταση"] == "Ολοκληρώθηκε"]["Χώρος"].tolist() if not checks.empty else []
    timeline_rows = prepare_timeline(df_task)
    scheduled_items = len(timeline_rows)

    render_page_banner(
        "Dashboard Ανακαίνισης",
        "Ζωντανή εικόνα για πληρωμές, υλικά, checklist και το progress των εργασιών σε ένα σημείο.",
        [
            f"Checklist {checklist_pct:.0f}%",
            f"{len(rooms_in_progress)} χώροι ενεργοί" if rooms_in_progress else "Καμία ενεργή πρόοδος",
            f"{scheduled_items} scheduled items",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Σύνολο πληρωμών",
                "value": format_currency(total_actual_paid),
                "note": f"{len(df_exp)} κινήσεις στο Expenses",
            },
            {
                "label": "Materials register",
                "value": format_currency(material_register_total),
                "note": f"{len(df_material)} γραμμές υλικών",
            },
            {
                "label": "Checklist progress",
                "value": f"{checklist_done}/{checklist_total}" if checklist_total else "0/0",
                "note": f"{checklist_pct:.0f}% ολοκλήρωση",
            },
            {
                "label": "Progress board",
                "value": str(len(df_task)),
                "note": f"{scheduled_items} εμφανίζονται στο timeline",
            },
        ]
    )

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
        st.caption("Τα ποσά με πληρωτή 'Κοινό' μοιράζονται αυτόματα 50%-50%.")

    st.markdown('<div class="dashboard-section-title">Κάρτα αμοιβών συνεργείων</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-section-subtitle">Μία κάρτα ανά κατηγορία με σύνολο, Εγώ, Πατέρας και υπόλοιπο.</div>', unsafe_allow_html=True)
    if fees.empty:
        st.info("Δεν υπάρχουν αμοιβές")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(fees.iterrows()):
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

    st.markdown('<div class="dashboard-section-title">Κάρτα υλικών</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-section-subtitle">Μία κάρτα ανά κατηγορία από το Materials sheet.</div>', unsafe_allow_html=True)
    if materials.empty:
        st.info("Δεν υπάρχουν υλικά")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(materials.iterrows()):
            with cols[i % 2]:
                render_visual_card(
                    f"Κάρτα {row['Κατηγορία']}",
                    "Σύνολο αγορών υλικών",
                    row["Σύνολο"],
                    row["Εγώ"] + row["Κοινό"] / 2,
                    row["Πατέρας"] + row["Κοινό"] / 2,
                )

    st.markdown('<div class="dashboard-section-title">✅ Checklist χώρων</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-section-subtitle">Γρήγορη εικόνα για το τι έχει ολοκληρωθεί σε Μπάνιο, Κουζίνα και Δωμάτια.</div>', unsafe_allow_html=True)
    if checks.empty:
        st.info("Δεν υπάρχει checklist ακόμη.")
    else:
        st.write(f"Συνολικά ολοκληρωμένα checklist items: {checklist_done}/{checklist_total}")
        if rooms_in_progress:
            st.write(f"Χώροι σε πρόοδο τώρα: {', '.join(rooms_in_progress)}")
        elif completed_rooms:
            st.write(f"Ολοκληρωμένοι χώροι: {', '.join(completed_rooms)}")
        for _, row in checks.iterrows():
            st.markdown(
                f'<span class="check-room-badge">{row["Χώρος"]}: {int(row["Ολοκληρωμένα"])}/{int(row["Σύνολο"])} ({row["Ποσοστό"]:.0f}%) • {row["Κατάσταση"]}</span>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="dashboard-section-title">🗓️ Timeline / Gantt</div>', unsafe_allow_html=True)
    if not timeline_rows.empty:
        fig = px.timeline(timeline_rows, x_start="Start", x_end="End", y="TaskLabel", color="Status")
        fig.update_layout(height=400)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)


def render_expenses(df):
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

    filtered_total = money_series(filtered_df, "Ποσό").sum() if not filtered_df.empty else 0.0
    active_filter_count = count_selected_filters(
        search_local,
        selected_categories,
        selected_payers,
        [] if selected_type == "Όλα" else [selected_type],
    )
    render_page_banner(
        "Expense Ledger",
        "Καταγραφή πληρωμών με γρήγορο φιλτράρισμα, grouping και inline επεξεργασία για πιο καθαρό οικονομικό έλεγχο.",
        [
            f"{len(filtered_df)} visible rows",
            f"{active_filter_count} active filters" if active_filter_count else "All expenses visible",
            f"Σύνολο {format_currency(filtered_total)}",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Σύνολο εγγραφών",
                "value": str(len(raw_df)),
                "note": "Αποθηκευμένα έξοδα",
            },
            {
                "label": "Φιλτραρισμένο ποσό",
                "value": format_currency(filtered_total),
                "note": "Με βάση το τρέχον view",
            },
            {
                "label": "Κατηγορίες στο view",
                "value": str(count_unique_nonempty(filtered_df, "Κατηγορία")),
                "note": "Μοναδικές κατηγορίες",
            },
            {
                "label": "Πληρωτές στο view",
                "value": str(count_unique_nonempty(filtered_df, "Πληρωτής")),
                "note": "Κατανομή συμμετοχών",
            },
        ]
    )

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

    st.markdown("### Ομαδοποιημένες καταχωρήσεις εξόδων")
    if not filtered_df.empty:
        group_view = filtered_df.copy()
        group_view["Ποσό"] = money_series(group_view, "Ποσό")
        grouped = group_view.groupby(["Κατηγορία", "Είδος", "Πληρωτής"], as_index=False)["Ποσό"].sum().sort_values(["Κατηγορία", "Είδος", "Πληρωτής"])
        st.dataframe(grouped, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εγγραφές για το φίλτρο.")

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
        selected_id, should_delete = delete_ui_from_labels(
            filtered_df if not filtered_df.empty else raw_df,
            lambda row: f"{row.get('Ημερομηνία', '')} | {row.get('Κατηγορία', '')} | {row.get('Είδος', '')} | {format_currency(row.get('Ποσό', 0))} | {row.get('Πληρωτής', '')}",
            "del_exp_label",
            "del_exp_btn",
            "Επέλεξε καταχώρηση εξόδων",
        )
        if should_delete and selected_id:
            new_df = delete_by_id(raw_df, selected_id)
            if safe_write(SHEET_EXPENSES, new_df):
                st.success("Η εγγραφή διαγράφηκε.")
                st.rerun()


def render_fees(df_fee, df_exp):
    raw_df = normalize_fee_df(df_fee.copy())
    render_page_banner(
        "Contractor Fees",
        "Παρακολούθηση budget αμοιβών, συμμετοχών και πραγματικών πληρωμών ανά κατηγορία συνεργείου.",
        [
            f"{len(raw_df)} fee records",
            f"{count_unique_nonempty(raw_df, 'Κατηγορία')} categories",
            "Budget vs actual",
        ],
    )

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

    total_budget = status["Συνολικό_Ποσό"].apply(to_money).sum()
    total_paid = status["Πλήρωσα Εγώ"].apply(to_money).sum() + status["Πλήρωσε Πατέρας"].apply(to_money).sum()
    total_remaining = max(total_budget - total_paid, 0)
    render_stat_strip(
        [
            {
                "label": "Budget αμοιβών",
                "value": format_currency(total_budget),
                "note": "Συνολικό συμβατικό ποσό",
            },
            {
                "label": "Πληρωμένο",
                "value": format_currency(total_paid),
                "note": "Από Expenses / είδος Αμοιβή",
            },
            {
                "label": "Υπόλοιπο",
                "value": format_currency(total_remaining),
                "note": "Απομένει να καλυφθεί",
            },
            {
                "label": "Κάρτες",
                "value": str(len(status)),
                "note": "Ενεργές κατηγορίες αμοιβών",
            },
        ]
    )

    tabs = st.tabs(["Αναλυτικά", "Visual κάρτες", "Επεξεργασία", "Διαγραφή"])

    with tabs[0]:
        show_table(status.drop(columns=["_id"], errors="ignore"))

    with tabs[1]:
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

    with tabs[2]:
        edited = editable_sheet(
            raw_df,
            FEE_COLUMNS,
            "fees_editor",
            num_cols=["Συνολικό_Ποσό", "Συμμετοχή_Εγώ", "Συμμετοχή_Πατέρας"],
        )
        edited["Συνολικό_Ποσό"] = edited["Συνολικό_Ποσό"].apply(to_money)
        edited["Συμμετοχή_Εγώ"] = edited["Συμμετοχή_Εγώ"].apply(to_money)
        edited["Συμμετοχή_Πατέρας"] = edited["Συμμετοχή_Πατέρας"].apply(to_money)

        for idx in edited.index:
            total_amount = to_money(edited.at[idx, "Συνολικό_Ποσό"])
            share_me = to_money(edited.at[idx, "Συμμετοχή_Εγώ"])
            share_father = to_money(edited.at[idx, "Συμμετοχή_Πατέρας"])
            if total_amount > 0 and share_me == 0 and share_father == 0:
                edited.at[idx, "Συμμετοχή_Εγώ"] = total_amount / 2
                edited.at[idx, "Συμμετοχή_Πατέρας"] = total_amount / 2

        if st.button("💾 Αποθήκευση αλλαγών αμοιβών", key="save_fees"):
            if safe_write(SHEET_FEES, edited):
                st.success("Οι αλλαγές στις αμοιβές αποθηκεύτηκαν.")
                st.rerun()

    with tabs[3]:
        selected_id, should_delete = delete_ui_from_labels(
            raw_df,
            lambda row: f"{row.get('Κατηγορία', '')} | {row.get('Περιγραφή', '')} | {format_currency(row.get('Συνολικό_Ποσό', 0))}",
            "del_fee_label",
            "del_fee_btn",
            "Επέλεξε αμοιβή",
        )
        if should_delete and selected_id:
            new_df = delete_by_id(raw_df, selected_id)
            if safe_write(SHEET_FEES, new_df):
                st.success("Η αμοιβή διαγράφηκε.")
                st.rerun()


def render_materials(df):
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
    filtered_total = money_series(filtered_df, "Σύνολο").sum() if not filtered_df.empty else 0.0
    pending_count = len(filtered_df[filtered_df["Κατάσταση"] != "Παραδόθηκε"]) if not filtered_df.empty and "Κατάσταση" in filtered_df.columns else 0
    render_page_banner(
        "Materials Register",
        "Κεντρικός πίνακας για υλικά, ποσότητες, προμηθευτές και κατάσταση παραγγελίας με πιο γρήγορη επιχειρησιακή εικόνα.",
        [
            f"{len(filtered_df)} visible materials",
            f"{count_unique_nonempty(filtered_df, 'Προμηθευτής')} suppliers",
            f"Σύνολο {format_currency(filtered_total)}",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Γραμμές υλικών",
                "value": str(len(raw_df)),
                "note": "Ολικό register",
            },
            {
                "label": "Τρέχον κόστος view",
                "value": format_currency(filtered_total),
                "note": "Με βάση τα φίλτρα",
            },
            {
                "label": "Pending / in transit",
                "value": str(pending_count),
                "note": "Όσα δεν έχουν παραδοθεί",
            },
            {
                "label": "Κατηγορίες",
                "value": str(count_unique_nonempty(filtered_df, "Κατηγορία")),
                "note": "Μοναδικές στο current view",
            },
        ]
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
            st.info("Δεν υπάρχουν εγγραφές για το φίλτρο.")
    with tabs[2]:
        edited = editable_sheet(raw_df, MATERIAL_COLUMNS, "materials_editor", num_cols=["Ποσότητα", "Τιμή_Μονάδας", "Σύνολο"])
        edited["Σύνολο"] = edited["Ποσότητα"].apply(to_money) * edited["Τιμή_Μονάδας"].apply(to_money)
        if st.button("💾 Αποθήκευση αλλαγών", key="save_mat"):
            if safe_write(SHEET_MATERIALS, edited):
                st.success("Οι αλλαγές αποθηκεύτηκαν.")
                st.rerun()
    with tabs[3]:
        selected_id, should_delete = delete_ui_from_labels(
            filtered_df if not filtered_df.empty else raw_df,
            lambda row: f"{row.get('Υλικό', '')} | {row.get('Κατηγορία', '')} | {format_currency(row.get('Σύνολο', 0))}",
            "del_mat_label",
            "del_mat_btn",
            "Επέλεξε υλικό",
        )
        if should_delete and selected_id:
            new_df = delete_by_id(raw_df, selected_id)
            if safe_write(SHEET_MATERIALS, new_df):
                st.success("Η εγγραφή διαγράφηκε.")
                st.rerun()


def render_contacts(df):
    render_page_banner(
        "Contacts Book",
        "Συγκεντρωμένες επαφές συνεργείων, προμηθευτών και καταστημάτων για γρήγορη επιχειρησιακή πρόσβαση.",
        [
            f"{len(df)} contacts",
            f"{count_unique_nonempty(df, 'Ρόλος')} roles",
            f"{count_unique_nonempty(df, 'Περιοχή')} areas",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Επαφές",
                "value": str(len(df)),
                "note": "Συνολικό address book",
            },
            {
                "label": "Ρόλοι",
                "value": str(count_unique_nonempty(df, "Ρόλος")),
                "note": "Εξειδικεύσεις / συνεργεία",
            },
            {
                "label": "Emails",
                "value": str(count_unique_nonempty(df, "Email")),
                "note": "Μη κενές email εγγραφές",
            },
            {
                "label": "Περιοχές",
                "value": str(count_unique_nonempty(df, "Περιοχή")),
                "note": "Γεωγραφική κάλυψη",
            },
        ]
    )
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
    current_df = df.copy()
    principal_total = money_series(current_df, "Κεφάλαιο").sum() if not current_df.empty else 0.0
    installment_total = money_series(current_df, "Μηνιαία_Δόση").sum() if not current_df.empty else 0.0
    active_loans = len(current_df[current_df["Κατάσταση"] == "Ενεργό"]) if not current_df.empty and "Κατάσταση" in current_df.columns else 0
    render_page_banner(
        "Loan Planner",
        "Παρακολούθηση χρηματοδότησης, μηνιαίων δόσεων και κατάστασης για πιο καθαρό cash planning.",
        [
            f"{len(current_df)} loan records",
            f"{active_loans} active",
            f"Μηνιαία βάση {format_currency(installment_total)}",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Σύνολο κεφαλαίου",
                "value": format_currency(principal_total),
                "note": "Καταγεγραμμένο principal",
            },
            {
                "label": "Μηνιαίες δόσεις",
                "value": format_currency(installment_total),
                "note": "Άθροισμα από όλα τα δάνεια",
            },
            {
                "label": "Ενεργά",
                "value": str(active_loans),
                "note": "Records σε κατάσταση Ενεργό",
            },
            {
                "label": "Σύνολο εγγραφών",
                "value": str(len(current_df)),
                "note": "Loan scenarios / πραγματικά δάνεια",
            },
        ]
    )
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
    current_df = normalize_task_df(df.copy())
    display_df = prepare_task_display_df(current_df)
    active_count = len(current_df[current_df["Κατάσταση"] == "Doing"]) if not current_df.empty else 0
    done_count = len(current_df[current_df["Κατάσταση"] == "Done"]) if not current_df.empty else 0
    timeline_preview = prepare_timeline(current_df)
    render_page_banner(
        "Timeline & Gantt",
        "Ο προγραμματισμός εργασιών σε ημερομηνίες, με σαφή εικόνα για active tasks, ολοκληρώσεις και scheduled items.",
        [
            f"{len(current_df)} total tasks",
            f"{active_count} active now",
            f"{len(timeline_preview)} scheduled on chart",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Εργασίες",
                "value": str(len(current_df)),
                "note": "Συνολικά records στο Progress",
            },
            {
                "label": "Σε πρόοδο",
                "value": str(active_count),
                "note": "Status = Doing",
            },
            {
                "label": "Ολοκληρωμένες",
                "value": str(done_count),
                "note": "Status = Done",
            },
            {
                "label": "Scheduled",
                "value": str(len(timeline_preview)),
                "note": "Εμφανίζονται στο Gantt",
            },
        ]
    )
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
                        st.success("Η εργασία αποθηκεύτηκε")
                        st.rerun()

    timeline = prepare_timeline(current_df)
    active_tasks = current_df[current_df["Κατάσταση"] == "Doing"].copy() if not current_df.empty else pd.DataFrame()
    if not active_tasks.empty:
        st.markdown("### Σε progress τώρα")
        progress_preview = active_tasks[["Χώρος", "Εργασία", "Ανάθεση", "Ημερομηνία_Λήξης"]].copy()
        st.dataframe(progress_preview, use_container_width=True)

    if not timeline.empty:
        fig = px.timeline(
            timeline,
            x_start="Start",
            x_end="End",
            y="TaskLabel",
            color="Status",
            hover_data=["Room", "Assignee", "Priority"],
        )
        fig.update_layout(height=470)
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    show_table(display_df)


def render_tasks(df):
    display_df = prepare_task_display_df(df)
    doing_count = len(display_df[display_df["Κατάσταση"] == "Doing"]) if not display_df.empty else 0
    done_count = len(display_df[display_df["Κατάσταση"] == "Done"]) if not display_df.empty else 0
    todo_count = len(display_df[display_df["Κατάσταση"] == "To Do"]) if not display_df.empty else 0
    render_page_banner(
        "Tasks Board",
        "Καθαρή λίστα όλων των εργασιών του project με έμφαση στην κατάσταση και την προτεραιότητα.",
        [
            f"{len(display_df)} tasks",
            f"{doing_count} doing",
            f"{done_count} done",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "To Do",
                "value": str(todo_count),
                "note": "Έτοιμες για εκτέλεση",
            },
            {
                "label": "Doing",
                "value": str(doing_count),
                "note": "Τρέχουν αυτή τη στιγμή",
            },
            {
                "label": "Done",
                "value": str(done_count),
                "note": "Ολοκληρωμένες εργασίες",
            },
            {
                "label": "Χώροι",
                "value": str(count_unique_nonempty(display_df, "Χώρος")),
                "note": "Κάλυψη χώρων",
            },
        ]
    )
    show_table(display_df)


def render_checklist(df):
    current_df = prepare_checklist_df(df.copy())
    current_summary = checklist_summary(current_df) if not current_df.empty else pd.DataFrame()
    current_done = int(current_df[CHECK_COL_DONE].sum()) if not current_df.empty else 0
    current_total = len(current_df)
    active_rooms_preview = (
        current_summary[current_summary["Κατάσταση"] == "Σε πρόοδο"]["Χώρος"].tolist()
        if not current_summary.empty
        else []
    )

    render_page_banner(
        "Checklist Control",
        "Κάθε αποθήκευση συγχρονίζει αυτόματα το Checklist με το Progress για να φαίνονται οι ενέργειες και στην παρακολούθηση εργασιών.",
        [
            "Auto-sync to Progress",
            f"{current_done}/{current_total} done" if current_total else "Empty board",
            f"{len(active_rooms_preview)} χώροι σε πρόοδο" if active_rooms_preview else "Ready to track",
        ],
    )
    st.markdown(
        '<div class="sync-badge">Auto-sync ενεργό: κάθε save ή διαγραφή ενημερώνει και το sheet Progress.</div>',
        unsafe_allow_html=True,
    )

    top1, top2 = st.columns([1.3, 1])
    with top1:
        st.caption("Οργάνωση ανά χώρο με έτοιμο template για Μπάνιο, Κουζίνα και Δωμάτια.")
    with top2:
        if current_df.empty and st.button("Φόρτωση προτεινόμενου checklist", key="seed_checklist"):
            seeded_df = build_default_checklist_df()
            if persist_checklist_and_progress(seeded_df):
                st.success("Το αρχικό checklist δημιουργήθηκε και συγχρονίστηκε στο Progress.")
                st.rerun()

    with st.expander("➕ Νέο custom item"):
        with st.form("checklist_form"):
            col1, col2 = st.columns(2)
            with col1:
                room = st.selectbox("Χώρος", ["Μπάνιο", "Κουζίνα", "Δωμάτια", "Άλλο"])
                task_name = st.text_input("Εργασία")
            with col2:
                priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES)
                done = st.checkbox("Ολοκληρώθηκε")
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση item") and task_name.strip():
                base_df = current_df.copy() if not current_df.empty else pd.DataFrame(columns=CHECKLIST_COLUMNS)
                updated = append_row(
                    base_df,
                    {
                        "Χώρος": room,
                        "Εργασία": task_name.strip(),
                        "Ολοκληρώθηκε": done,
                        "Προτεραιότητα": priority,
                        "Σημειώσεις": notes,
                    },
                    CHECKLIST_COLUMNS,
                )
                if persist_checklist_and_progress(updated):
                    st.success("Το item προστέθηκε και εμφανίζεται πλέον και στο Progress.")
                    st.rerun()

    if current_df.empty:
        st.info("Δεν υπάρχει checklist ακόμη. Πάτησε 'Φόρτωση προτεινόμενου checklist'.")
        return

    summary = checklist_summary(current_df)
    active_rooms = summary[summary["Κατάσταση"] == "Σε πρόοδο"]["Χώρος"].tolist() if not summary.empty else []
    render_stat_strip(
        [
            {
                "label": "Σύνολο εργασιών",
                "value": str(len(current_df)),
                "note": "Checklist items",
            },
            {
                "label": "Ολοκληρωμένες",
                "value": str(int(current_df[CHECK_COL_DONE].sum())),
                "note": f"{len(current_df) - int(current_df[CHECK_COL_DONE].sum())} απομένουν",
            },
            {
                "label": "Ποσοστό ολοκλήρωσης",
                "value": f"{(current_df[CHECK_COL_DONE].sum() / len(current_df) * 100):.0f}%",
                "note": "Από το συνολικό checklist",
            },
            {
                "label": "Sync status",
                "value": "Live",
                "note": "Checklist -> Progress",
            },
        ]
    )
    if active_rooms:
        st.write(f"Χώροι που βρίσκονται σε πρόοδο: {', '.join(active_rooms)}")
    else:
        st.write("Δεν υπάρχει χώρος σε ενεργή πρόοδο αυτή τη στιγμή.")

    st.markdown("### Αποθηκευμένη κατάσταση checklist")
    status_preview = current_df[["Χώρος", "Εργασία", "Ολοκληρώθηκε", "Προτεραιότητα"]].copy()
    st.dataframe(status_preview, use_container_width=True)

    render_checklist_visual(current_df)

    tabs = st.tabs(["Checklist editor", "Διαγραφή"])
    with tabs[0]:
        edited = editable_sheet(
            current_df,
            CHECKLIST_COLUMNS,
            "checklist_editor",
            bool_cols=["Ολοκληρώθηκε"],
        )
        if st.button("💾 Αποθήκευση checklist", key="save_checklist"):
            if persist_checklist_and_progress(edited):
                st.success("Το checklist αποθηκεύτηκε και συγχρονίστηκε στο Progress.")
                st.rerun()

    with tabs[1]:
        selected_id, should_delete = delete_ui_from_labels(
            current_df,
            lambda row: f"{row.get('Χώρος', '')} | {row.get('Εργασία', '')}",
            "del_check_label",
            "del_check_btn",
            "Επέλεξε item checklist",
        )
        if should_delete and selected_id:
            new_df = delete_by_id(current_df, selected_id)
            if persist_checklist_and_progress(new_df):
                st.success("Το item διαγράφηκε και αφαιρέθηκε από το Progress.")
                st.rerun()


def render_offers(df):
    total_offers = money_series(df, "Ποσό").sum() if not df.empty else 0.0
    render_page_banner(
        "Offers Desk",
        "Συγκέντρωση προσφορών από παρόχους και γρήγορη σύγκριση κόστους ανά κατηγορία εργασίας.",
        [
            f"{len(df)} offers",
            f"{count_unique_nonempty(df, 'Πάροχος')} providers",
            f"Σύνολο {format_currency(total_offers)}",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Προσφορές",
                "value": str(len(df)),
                "note": "Καταγεγραμμένα quotes",
            },
            {
                "label": "Providers",
                "value": str(count_unique_nonempty(df, "Πάροχος")),
                "note": "Μοναδικοί πάροχοι",
            },
            {
                "label": "Κατηγορίες",
                "value": str(count_unique_nonempty(df, "Κατηγορία")),
                "note": "Work scopes",
            },
            {
                "label": "Ονομαστικό σύνολο",
                "value": format_currency(total_offers),
                "note": "Άθροισμα ποσών",
            },
        ]
    )
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
    render_page_banner(
        "Visual Gallery",
        "Before, after και progress snapshots για να έχεις οπτικό ιστορικό της ανακαίνισης μέσα στο ίδιο control room.",
        [
            f"{len(df)} images",
            f"{count_unique_nonempty(df, 'Χώρος')} rooms covered",
            f"{count_unique_nonempty(df, 'Τύπος')} image types",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Εικόνες",
                "value": str(len(df)),
                "note": "Συνολικό οπτικό αρχείο",
            },
            {
                "label": "Χώροι",
                "value": str(count_unique_nonempty(df, "Χώρος")),
                "note": "Με διαθέσιμο φωτογραφικό υλικό",
            },
            {
                "label": "Progress shots",
                "value": str(len(df[df["Τύπος"] == "Progress"])) if not df.empty and "Τύπος" in df.columns else "0",
                "note": "Καταγραφή εξέλιξης",
            },
            {
                "label": "Latest window",
                "value": str(min(len(df), 10)),
                "note": "Προβάλλονται τα πιο πρόσφατα",
            },
        ]
    )
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


def render_analytics(df_exp, df_material, df_fee, df_check):
    exp_total = money_series(df_exp, "Ποσό").sum()
    mat_total = money_series(df_material, "Σύνολο").sum()
    render_page_banner(
        "Analytics Hub",
        "Συγκεντρωτικές αναλύσεις για πληρωμές, υλικά, checklist progress και αποκλίσεις budget έναντι actual.",
        [
            f"Payments {format_currency(exp_total)}",
            f"Materials {format_currency(mat_total)}",
            f"{len(df_check)} checklist rows",
        ],
    )
    render_stat_strip(
        [
            {
                "label": "Σύνολο πληρωμών",
                "value": format_currency(exp_total),
                "note": "Expenses filtered view",
            },
            {
                "label": "Materials register",
                "value": format_currency(mat_total),
                "note": "Materials filtered view",
            },
            {
                "label": "Budget lines",
                "value": str(len(df_fee)),
                "note": "Εγγραφές αμοιβών",
            },
            {
                "label": "Checklist rows",
                "value": str(len(df_check)),
                "note": "Συμμετέχουν στις αναλύσεις",
            },
        ]
    )

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

    if not df_check.empty:
        st.markdown("**Progress Checklist ανά χώρο**")
        st.dataframe(checklist_summary(df_check), use_container_width=True)

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
    render_page_banner(
        "Estimator & Calculator",
        "Γρήγορα εργαλεία για προεκτίμηση κόστους και μεταφορά έτοιμων γραμμών στο Materials sheet.",
        [
            "Material estimator",
            "Tile invoice model",
            "Export to Materials",
        ],
    )
    mode = st.selectbox(
        "Τύπος υπολογισμού",
        ["Απλός υπολογιστής υλικών", "Τιμολόγιο πλακιδίων"],
        key="calculator_mode",
    )
    render_stat_strip(
        [
            {
                "label": "Mode",
                "value": mode,
                "note": "Ενεργό εργαλείο υπολογισμού",
            },
            {
                "label": "Output",
                "value": "Live",
                "note": "Άμεσο recalculation στα inputs",
            },
            {
                "label": "Export",
                "value": "Materials-ready",
                "note": "Για το τιμολόγιο πλακιδίων",
            },
        ]
    )

    if mode == "Απλός υπολογιστής υλικών":
        st.caption("Υπολογιστής υλικών με εκτίμηση κόστους.")
        qty = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
        unit_price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
        waste = st.slider("Ποσοστό φύρας (%)", 0, 30, 10)
        adjusted_qty = qty * (1 + waste / 100)
        total = adjusted_qty * unit_price
        col1, col2 = st.columns(2)
        col1.metric("Ποσότητα με φύρα", f"{adjusted_qty:.2f}")
        col2.metric("Εκτιμώμενο κόστος", format_currency(total))
        return

    st.caption("Ανάλυση τιμολογίου υλικών για πλακάκια, κόλλες και σοβά σε τοίχους και πάτωμα.")

    c1, c2 = st.columns(2)
    with c1:
        wall_area = st.number_input("m² τοίχων", min_value=0.0, step=1.0, value=20.0)
        wall_tile_price = st.number_input("Τιμή πλακιδίου τοίχου ανά m² (€)", min_value=0.0, step=0.5, value=18.0)
        floor_area = st.number_input("m² πατώματος", min_value=0.0, step=1.0, value=8.0)
        floor_tile_price = st.number_input("Τιμή πλακιδίου πατώματος ανά m² (€)", min_value=0.0, step=0.5, value=22.0)
        tile_waste = st.slider("Φύρα πλακιδίων (%)", 0, 30, 10, key="tile_invoice_waste")

    with c2:
        tiled_total_area = wall_area + floor_area
        glue_area = st.number_input("m² για κόλλες", min_value=0.0, step=1.0, value=float(tiled_total_area))
        glue_price_per_m2 = st.number_input("Κόλλες ανά m² (€)", min_value=0.0, step=0.1, value=4.5)
        plaster_area = st.number_input("m² για σοβά", min_value=0.0, step=1.0, value=float(floor_area))
        plaster_price_per_m2 = st.number_input("Σοβάς ανά m² (€)", min_value=0.0, step=0.1, value=6.0)
        extra_materials = st.number_input("Λοιπά υλικά (€)", min_value=0.0, step=1.0, value=0.0)

    adjusted_wall_area = wall_area * (1 + tile_waste / 100)
    adjusted_floor_area = floor_area * (1 + tile_waste / 100)

    wall_tiles_cost = adjusted_wall_area * wall_tile_price
    floor_tiles_cost = adjusted_floor_area * floor_tile_price
    total_tiles_cost = wall_tiles_cost + floor_tiles_cost
    glue_cost = glue_area * glue_price_per_m2
    plaster_cost = plaster_area * plaster_price_per_m2
    grand_total = total_tiles_cost + glue_cost + plaster_cost + extra_materials

    summary1, summary2, summary3, summary4 = st.columns(4)
    summary1.metric("Πλακάκια τοίχου", format_currency(wall_tiles_cost))
    summary2.metric("Πλακάκια πατώματος", format_currency(floor_tiles_cost))
    summary3.metric("Κόλλες", format_currency(glue_cost))
    summary4.metric("Σοβάς", format_currency(plaster_cost))

    st.metric("Συνολικό τιμολόγιο υλικών", format_currency(grand_total))

    invoice_df = pd.DataFrame(
        [
            {
                "Κατηγορία": "Πλακάκια τοίχου",
                "m²": round(adjusted_wall_area, 2),
                "Τιμή ανά m²": wall_tile_price,
                "Σύνολο": wall_tiles_cost,
            },
            {
                "Κατηγορία": "Πλακάκια πατώματος",
                "m²": round(adjusted_floor_area, 2),
                "Τιμή ανά m²": floor_tile_price,
                "Σύνολο": floor_tiles_cost,
            },
            {
                "Κατηγορία": "Κόλλες",
                "m²": round(glue_area, 2),
                "Τιμή ανά m²": glue_price_per_m2,
                "Σύνολο": glue_cost,
            },
            {
                "Κατηγορία": "Σοβάς",
                "m²": round(plaster_area, 2),
                "Τιμή ανά m²": plaster_price_per_m2,
                "Σύνολο": plaster_cost,
            },
            {
                "Κατηγορία": "Λοιπά υλικά",
                "m²": 0.0,
                "Τιμή ανά m²": 0.0,
                "Σύνολο": extra_materials,
            },
        ]
    )

    if grand_total > 0:
        invoice_df["Ποσοστό Τιμολογίου"] = invoice_df["Σύνολο"].apply(lambda x: f"{(x / grand_total) * 100:.1f}%")
    else:
        invoice_df["Ποσοστό Τιμολογίου"] = "0.0%"

    st.markdown("### Ανάλυση τιμολογίου")
    st.dataframe(invoice_df, use_container_width=True)

    chart_df = invoice_df[invoice_df["Σύνολο"] > 0].copy()
    if not chart_df.empty:
        fig = px.bar(
            chart_df,
            x="Κατηγορία",
            y="Σύνολο",
            color="Κατηγορία",
            title="Διαχωρισμός εξόδων υλικών",
            template="plotly_white",
        )
        fig.update_layout(showlegend=False, height=380)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Χρήσιμες λεπτομέρειες")
    st.write(f"Συνολικά m² πλακιδίων πριν τη φύρα: {tiled_total_area:.2f}")
    st.write(f"Συνολικά m² πλακιδίων μετά τη φύρα: {(adjusted_wall_area + adjusted_floor_area):.2f}")

    st.markdown("### Πέρασμα στα Materials")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        export_category = st.selectbox(
            "Κατηγορία καταχώρησης",
            EXPENSE_CATEGORIES,
            index=EXPENSE_CATEGORIES.index("Πλακάκια") if "Πλακάκια" in EXPENSE_CATEGORIES else 0,
            key="calc_export_category",
        )
        export_room = st.selectbox("Χώρος", ROOMS, key="calc_export_room")
        export_payer = st.selectbox("Πληρωτής", PAYERS, key="calc_export_payer")
    with export_col2:
        export_supplier = st.text_input("Προμηθευτής", key="calc_export_supplier")
        export_status = st.selectbox("Κατάσταση", MATERIAL_STATUS, key="calc_export_status")
        export_notes = st.text_input("Σημειώσεις", key="calc_export_notes")

    export_rows = []
    if wall_tiles_cost > 0:
        export_rows.append(
            {
                "Κατηγορία": export_category,
                "Υλικό": f"Πλακάκια τοίχου ({export_room})",
                "Ποσότητα": round(adjusted_wall_area, 2),
                "Μονάδα": "m2",
                "Τιμή_Μονάδας": wall_tile_price,
                "Σύνολο": wall_tiles_cost,
                "Πληρωτής": export_payer,
                "Προμηθευτής": export_supplier,
                "Κατάσταση": export_status,
                "Σημειώσεις": export_notes,
            }
        )
    if floor_tiles_cost > 0:
        export_rows.append(
            {
                "Κατηγορία": export_category,
                "Υλικό": f"Πλακάκια πατώματος ({export_room})",
                "Ποσότητα": round(adjusted_floor_area, 2),
                "Μονάδα": "m2",
                "Τιμή_Μονάδας": floor_tile_price,
                "Σύνολο": floor_tiles_cost,
                "Πληρωτής": export_payer,
                "Προμηθευτής": export_supplier,
                "Κατάσταση": export_status,
                "Σημειώσεις": export_notes,
            }
        )
    if glue_cost > 0:
        export_rows.append(
            {
                "Κατηγορία": export_category,
                "Υλικό": f"Κόλλες πλακιδίων ({export_room})",
                "Ποσότητα": round(glue_area, 2),
                "Μονάδα": "m2",
                "Τιμή_Μονάδας": glue_price_per_m2,
                "Σύνολο": glue_cost,
                "Πληρωτής": export_payer,
                "Προμηθευτής": export_supplier,
                "Κατάσταση": export_status,
                "Σημειώσεις": export_notes,
            }
        )
    if plaster_cost > 0:
        export_rows.append(
            {
                "Κατηγορία": export_category,
                "Υλικό": f"Σοβάς ({export_room})",
                "Ποσότητα": round(plaster_area, 2),
                "Μονάδα": "m2",
                "Τιμή_Μονάδας": plaster_price_per_m2,
                "Σύνολο": plaster_cost,
                "Πληρωτής": export_payer,
                "Προμηθευτής": export_supplier,
                "Κατάσταση": export_status,
                "Σημειώσεις": export_notes,
            }
        )
    if extra_materials > 0:
        export_rows.append(
            {
                "Κατηγορία": export_category,
                "Υλικό": f"Λοιπά υλικά ({export_room})",
                "Ποσότητα": 1.0,
                "Μονάδα": "τεμ",
                "Τιμή_Μονάδας": extra_materials,
                "Σύνολο": extra_materials,
                "Πληρωτής": export_payer,
                "Προμηθευτής": export_supplier,
                "Κατάσταση": export_status,
                "Σημειώσεις": export_notes,
            }
        )

    export_df = pd.DataFrame(export_rows)
    if not export_df.empty:
        st.markdown("#### Έτοιμες γραμμές για Materials")
        st.dataframe(export_df, use_container_width=True)

        if st.button("Πέρασμα στα Materials", key="calc_export_to_materials"):
            updated_materials = df_materials.copy()
            for row in export_rows:
                updated_materials = append_row(updated_materials, row, MATERIAL_COLUMNS)
            if safe_write(SHEET_MATERIALS, updated_materials):
                st.success("Οι γραμμές πέρασαν στο Materials.")
                st.rerun()
    else:
        st.info("Δεν υπάρχουν ποσά για πέρασμα στα Materials.")


# -----------------------------
# MAIN
# -----------------------------
inject_v3_theme()
st.sidebar.markdown(
    f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">Methana Earth & Fire</div>
        <div class="sidebar-brand-subtitle">Renovation operations dashboard with budget, checklist, progress and material control.</div>
        <div class="sidebar-brand-meta">{APP_VERSION} • Κατασκευαστής: {APP_BUILDER}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("### Πλοήγηση")

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "💼 Αμοιβές",
    "📦 Υλικά",
    "✅ Checklist",
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
        exp_df = df_expenses
        fee_df = df_fees
        mat_df = df_materials
        task_df = df_tasks
        loan_df = df_loans
        check_df = df_checklist
        st.session_state["excel_export_bytes"] = build_excel_bytes(
            {
                "Expenses": exp_df,
                "Fees": fee_df,
                "Materials": mat_df,
                "Tasks": task_df,
                "Loans": loan_df,
                "Checklist": check_df,
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
    render_dashboard(exp_filtered, df_fees, mat_filtered, df_tasks, df_checklist)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "💼 Αμοιβές":
    render_fees(df_fees, df_expenses)
elif menu == "📦 Υλικά":
    render_materials(df_materials)
elif menu == "✅ Checklist":
    render_checklist(df_checklist)
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
    render_analytics(exp_filtered, mat_filtered, df_fees, df_checklist)
elif menu == "🧮 Calculator":
    render_calculator()

