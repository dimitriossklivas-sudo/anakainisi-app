import json
import re
import tempfile
import uuid
from datetime import datetime

import pandas as pd
import pdfplumber
import plotly.express as px
import streamlit as st
from openai import OpenAI
from PIL import Image
from streamlit_gsheets import GSheetsConnection

try:
    import pytesseract
except Exception:
    pytesseract = None

st.set_page_config(
    page_title="Renovation Manager V4.2",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(212,175,55,0.10), transparent 24%),
            radial-gradient(circle at bottom right, rgba(30,41,59,0.08), transparent 18%),
            linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    }
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #334155 100%);
        color: white;
        padding: 30px 32px;
        border-radius: 24px;
        margin-bottom: 18px;
        box-shadow: 0 14px 36px rgba(15, 23, 42, 0.22);
        border: 1px solid rgba(255,255,255,0.06);
    }
    .hero h1 {
        margin: 0;
        font-size: 2.5rem;
        line-height: 1.1;
    }
    .hero p {
        margin: 10px 0 0 0;
        color: rgba(255,255,255,0.84);
        font-size: 1rem;
    }
    .mini-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid rgba(15,23,42,0.05);
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 8px 22px rgba(15,23,42,0.06);
        margin-bottom: 12px;
    }
    .section-title {
        font-size: 1.08rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #0f172a;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.96);
        border-radius: 18px;
        padding: 14px;
        box-shadow: 0 10px 24px rgba(15,23,42,0.08);
        border-top: 4px solid #D4AF37;
    }
    .maker {
        margin-top: 24px;
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(255,255,255,0.85);
        border: 1px solid rgba(15,23,42,0.06);
        color: #334155;
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🏗️ Renovation Manager V4.2</h1>
        <p>Διαχείριση εξόδων, εργασιών, προσφορών, budget και έξυπνη εισαγωγή προσφορών από εικόνα/PDF.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

SHEET_EXPENSES = "Expenses"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "📋 Εργασίες",
    "💼 Προσφορές",
    "📊 Αναλύσεις",
    "🏦 Δάνειο",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
TASK_COLUMNS = ["_id", "Εργασία", "Κατάσταση", "Κόστος", "Προτεραιότητα", "Ανάθεση", "Σημειώσεις"]
OFFER_COLUMNS = ["_id", "Πάροχος", "Περιγραφή", "Ποσό", "Κατηγορία", "Σημειώσεις"]

EXPENSE_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Κουφώματα", "Μπάνιο", "Άλλο"]
EXPENSE_TYPES = ["Αμοιβή", "Υλικά"]
PAYERS = ["Εγώ", "Πατέρας", "Κοινό", "Άλλο"]

TASK_STATUSES = ["To Do", "Doing", "Done"]
TASK_PRIORITIES = ["Χαμηλή", "Μεσαία", "Υψηλή"]

OFFER_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Μπάνιο", "Άλλο"]

PLOTLY_TEMPLATE = "plotly_white"
CHART_COLORS = ["#D4AF37", "#1E293B", "#38BDF8", "#22C55E", "#F97316", "#EF4444", "#8B5CF6"]


@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


conn = get_connection()
ai_client = get_openai_client()


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


def update_row_by_id(df: pd.DataFrame, row_id: str, new_data: dict, columns: list[str]) -> pd.DataFrame:
    updated = ensure_columns(df, columns).copy()
    mask = updated["_id"].astype(str) == str(row_id)
    if mask.any():
        for key, value in new_data.items():
            updated.loc[mask, key] = value
    return updated


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


def default_index(options: list[str], value: str) -> int:
    return options.index(value) if value in options else 0


def card_start(title: str):
    st.markdown(f'<div class="mini-card"><div class="section-title">{title}</div>', unsafe_allow_html=True)


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


def parse_json_text(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("Δεν βρέθηκε έγκυρο JSON στην απάντηση.")


def classify_offer_category(text: str) -> str:
    t = text.lower()
    mapping = {
        "Υδραυλικά": ["υδραυ", "σιφον", "μπαταρ", "σωλην", "αποχετ"],
        "Ηλεκτρολογικά": ["ηλεκτρο", "καλωδ", "πινακ", "ρευμα", "φωτισ"],
        "Πλακάκια": ["πλακα", "αρμο", "κεραμ"],
        "Κουζίνα": ["κουζιν", "ντουλαπ", "παγκος"],
        "Βάψιμο": ["βαψ", "χρωμ", "στοκος"],
        "Μπάνιο": ["μπαν", "λεκαν", "ντουζ", "καζανα"],
    }
    for category, keywords in mapping.items():
        if any(k in t for k in keywords):
            return category
    return "Άλλο"


def extract_amount_from_text(text: str) -> float:
    normalized = text.replace(",", ".")
    matches = re.findall(r"(\d+(?:\.\d{1,2})?)\s*(?:€|eur|euro)?", normalized, flags=re.IGNORECASE)
    values = []
    for m in matches:
        try:
            values.append(float(m))
        except Exception:
            pass
    return max(values) if values else 0.0


def extract_provider_from_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    return lines[0][:80]


def extract_description_from_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) >= 2:
        return lines[1][:120]
    if lines:
        return lines[0][:120]
    return ""


def extract_offer_from_text_basic(text: str) -> dict:
    provider = extract_provider_from_text(text)
    description = extract_description_from_text(text)
    amount = extract_amount_from_text(text)
    category = classify_offer_category(text)
    short_text = " ".join(text.split())[:1200]

    return {
        "Πάροχος": provider,
        "Περιγραφή": description,
        "Ποσό": amount,
        "Κατηγορία": category,
        "Σημειώσεις": f"OCR text: {short_text}",
    }


def extract_offer_from_image_with_ai(uploaded_file) -> dict:
    if ai_client is None:
        raise ValueError("Δεν έχει οριστεί OPENAI_API_KEY στα secrets.")

    file_bytes = uploaded_file.getvalue()
    suffix = ".jpg"
    lower = uploaded_file.name.lower()
    if lower.endswith(".png"):
        suffix = ".png"
    elif lower.endswith(".webp"):
        suffix = ".webp"
    elif lower.endswith(".jpeg"):
        suffix = ".jpeg"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        uploaded = ai_client.files.create(file=f, purpose="vision")

    response = ai_client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": """
Διάβασε την προσφορά από την εικόνα και επέστρεψε ΜΟΝΟ έγκυρο JSON.
Αν κάποιο πεδίο λείπει, βάλε κενό string ή 0.

{
  "provider": "",
  "description": "",
  "amount": 0,
  "category": "",
  "notes": "",
  "vat": "",
  "date": "",
  "line_items": [
    {
      "title": "",
      "amount": 0
    }
  ]
}
""",
                },
                {
                    "type": "input_image",
                    "file_id": uploaded.id,
                },
            ],
        }],
        text={"format": {"type": "json_object"}},
    )

    data = parse_json_text(response.output_text)

    return {
        "Πάροχος": str(data.get("provider", "")).strip(),
        "Περιγραφή": str(data.get("description", "")).strip(),
        "Ποσό": float(data.get("amount", 0) or 0),
        "Κατηγορία": str(data.get("category", "")).strip() or "Άλλο",
        "Σημειώσεις": (
            f"Ημ/νία: {data.get('date', '')} | "
            f"ΦΠΑ: {data.get('vat', '')} | "
            f"AI notes: {data.get('notes', '')} | "
            f"Line items: {data.get('line_items', [])}"
        ).strip(),
    }


def extract_offer_from_pdf_with_ai(uploaded_file) -> dict:
    if ai_client is None:
        raise ValueError("Δεν έχει οριστεί OPENAI_API_KEY στα secrets.")

    file_bytes = uploaded_file.getvalue()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        uploaded = ai_client.files.create(file=f, purpose="user_data")

    response = ai_client.responses.create(
        model="gpt-4.1-mini",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_file", "file_id": uploaded.id},
                {
                    "type": "input_text",
                    "text": """
Διάβασε το PDF της προσφοράς και επέστρεψε ΜΟΝΟ έγκυρο JSON.
Αν κάποιο πεδίο λείπει, βάλε κενό string ή 0.

{
  "provider": "",
  "description": "",
  "amount": 0,
  "category": "",
  "notes": "",
  "vat": "",
  "date": "",
  "line_items": [
    {
      "title": "",
      "amount": 0
    }
  ]
}
""",
                },
            ],
        }],
        text={"format": {"type": "json_object"}},
    )

    data = parse_json_text(response.output_text)

    return {
        "Πάροχος": str(data.get("provider", "")).strip(),
        "Περιγραφή": str(data.get("description", "")).strip(),
        "Ποσό": float(data.get("amount", 0) or 0),
        "Κατηγορία": str(data.get("category", "")).strip() or "Άλλο",
        "Σημειώσεις": (
            f"Ημ/νία: {data.get('date', '')} | "
            f"ΦΠΑ: {data.get('vat', '')} | "
            f"AI notes: {data.get('notes', '')} | "
            f"Line items: {data.get('line_items', [])}"
        ).strip(),
    }


def extract_offer_from_pdf_free(uploaded_file) -> dict:
    text_parts = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        return {
            "Πάροχος": "",
            "Περιγραφή": uploaded_file.name,
            "Ποσό": 0.0,
            "Κατηγορία": "Άλλο",
            "Σημειώσεις": "Δεν βρέθηκε αναγνώσιμο κείμενο στο PDF. Συμπλήρωσε χειροκίνητα τα στοιχεία.",
        }

    return extract_offer_from_text_basic(full_text)


def extract_offer_from_image_free(uploaded_file) -> dict:
    if pytesseract is None:
        return {
            "Πάροχος": "",
            "Περιγραφή": uploaded_file.name,
            "Ποσό": 0.0,
            "Κατηγορία": "Άλλο",
            "Σημειώσεις": "Δεν ήταν διαθέσιμο δωρεάν OCR εικόνας στο περιβάλλον. Συμπλήρωσε χειροκίνητα τα πεδία.",
        }

    try:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image, lang="eng+ell")
        if text.strip():
            return extract_offer_from_text_basic(text)
    except Exception:
        pass

    return {
        "Πάροχος": "",
        "Περιγραφή": uploaded_file.name,
        "Ποσό": 0.0,
        "Κατηγορία": "Άλλο",
        "Σημειώσεις": "Η εικόνα δεν αναγνωρίστηκε αυτόματα. Συμπλήρωσε χειροκίνητα τα στοιχεία.",
    }


def extract_offer_with_fallback(uploaded_file) -> tuple[dict, str]:
    is_pdf = uploaded_file.type == "application/pdf"

    if ai_client is not None:
        try:
            if is_pdf:
                return extract_offer_from_pdf_with_ai(uploaded_file), "AI"
            return extract_offer_from_image_with_ai(uploaded_file), "AI"
        except Exception as e:
            err = str(e)
            if "insufficient_quota" not in err and "429" not in err:
                raise

    if is_pdf:
        return extract_offer_from_pdf_free(uploaded_file), "FREE_PDF_OCR"

    return extract_offer_from_image_free(uploaded_file), "FREE_IMAGE_OCR"


df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)


def filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        category = st.selectbox("Κατηγορία", ["Όλες"] + EXPENSE_CATEGORIES, key="exp_cat_filter")
    with c2:
        expense_type = st.selectbox("Είδος", ["Όλα"] + EXPENSE_TYPES, key="exp_type_filter")
    with c3:
        payer = st.selectbox("Πληρωτής", ["Όλοι"] + PAYERS, key="exp_payer_filter")
    with c4:
        search = st.text_input("Αναζήτηση σημειώσεων", key="exp_search").strip().lower()

    if category != "Όλες":
        filtered = filtered[filtered["Κατηγορία"] == category]
    if expense_type != "Όλα":
        filtered = filtered[filtered["Είδος"] == expense_type]
    if payer != "Όλοι":
        filtered = filtered[filtered["Πληρωτής"] == payer]
    if search:
        filtered = filtered[filtered["Σημειώσεις"].astype(str).str.lower().str.contains(search, na=False)]
    return filtered


def filter_tasks(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    c1, c2, c3 = st.columns(3)
    with c1:
        status = st.selectbox("Κατάσταση", ["Όλες"] + TASK_STATUSES, key="task_status_filter")
    with c2:
        priority = st.selectbox("Προτεραιότητα", ["Όλες"] + TASK_PRIORITIES, key="task_priority_filter")
    with c3:
        search = st.text_input("Αναζήτηση εργασίας", key="task_search").strip().lower()

    if status != "Όλες":
        filtered = filtered[filtered["Κατάσταση"] == status]
    if priority != "Όλες":
        filtered = filtered[filtered["Προτεραιότητα"] == priority]
    if search:
        filtered = filtered[filtered["Εργασία"].astype(str).str.lower().str.contains(search, na=False)]
    return filtered


def filter_offers(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    c1, c2 = st.columns(2)
    with c1:
        category = st.selectbox("Κατηγορία", ["Όλες"] + OFFER_CATEGORIES, key="offer_cat_filter")
    with c2:
        search = st.text_input("Αναζήτηση παρόχου", key="offer_search").strip().lower()

    if category != "Όλες":
        filtered = filtered[filtered["Κατηγορία"] == category]
    if search:
        filtered = filtered[filtered["Πάροχος"].astype(str).str.lower().str.contains(search, na=False)]
    return filtered


def render_dashboard(df_exp: pd.DataFrame, df_task: pd.DataFrame, df_off: pd.DataFrame):
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

    c5, c6, c7 = st.columns(3)
    c5.metric("📋 Σύνολο Εργασιών", tasks_total)
    c6.metric("🛠️ Σε Εξέλιξη", tasks_doing)
    c7.metric("✅ Ολοκληρωμένες", tasks_done)

    st.progress(min(max(usage / 100, 0.0), 1.0))
    if usage > 100:
        st.error("Το budget έχει ξεπεραστεί.")
    elif usage > 80:
        st.warning("Το budget πλησιάζει το όριο.")
    else:
        st.success("Το budget είναι σε ελεγχόμενο επίπεδο.")

    col_left, col_right = st.columns(2)

    with col_left:
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

        card_start("Πρόσφατα Έξοδα")
        if not df_exp.empty:
            recent = df_exp.copy()
            recent["Ημερομηνία_sort"] = parse_date_series(recent, "Ημερομηνία")
            recent = recent.sort_values("Ημερομηνία_sort", ascending=False).head(5)
            show_table(recent.drop(columns=["Ημερομηνία_sort"]), hide_id=True)
        else:
            st.info("Δεν υπάρχουν έξοδα.")
        card_end()

    with col_right:
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

        card_start("Εργασίες που Εκκρεμούν")
        if not df_task.empty:
            pending = df_task[df_task["Κατάσταση"] != "Done"].copy()
            if pending.empty:
                st.success("Όλες οι εργασίες έχουν ολοκληρωθεί.")
            else:
                show_table(pending.head(8), hide_id=True)
        else:
            st.info("Δεν υπάρχουν εργασίες.")
        card_end()


def render_expenses(df_exp: pd.DataFrame):
    st.subheader("💰 Έξοδα")

    with st.expander("➕ Νέα καταχώρηση εξόδου"):
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

    st.markdown("### Φίλτρα")
    filtered = filter_expenses(df_exp)
    show_table(filtered)

    if filtered.empty:
        return

    expense_labels = build_labels(
        filtered,
        "_id",
        lambda row: f"{safe_text(row['Ημερομηνία'])} | {safe_text(row['Κατηγορία'])} | {safe_text(row['Είδος'])} | {format_currency(pd.to_numeric(pd.Series([row['Ποσό']]), errors='coerce').fillna(0).iloc[0])}",
    )
    expense_ids = list(expense_labels.keys())
    if not expense_ids:
        return

    selected_id = st.selectbox(
        "Επιλογή εγγραφής για edit / delete",
        options=expense_ids,
        format_func=lambda rid: expense_labels.get(rid, "Άγνωστη εγγραφή"),
    )

    row_df = df_exp[df_exp["_id"].astype(str) == str(selected_id)]
    if row_df.empty:
        return
    row = row_df.iloc[0]

    with st.expander("✏️ Edit εξόδου"):
        with st.form("expense_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_date = st.text_input("Ημερομηνία", value=safe_text(row["Ημερομηνία"]))
                new_category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES, index=default_index(EXPENSE_CATEGORIES, safe_text(row["Κατηγορία"])))
            with c2:
                new_type = st.selectbox("Είδος", EXPENSE_TYPES, index=default_index(EXPENSE_TYPES, safe_text(row["Είδος"])))
                new_payer = st.selectbox("Πληρωτής", PAYERS, index=default_index(PAYERS, safe_text(row["Πληρωτής"])))
            with c3:
                new_amount = st.number_input("Ποσό (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Ποσό"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
            new_notes = st.text_input("Σημειώσεις", value=safe_text(row["Σημειώσεις"]))
            if st.form_submit_button("Αποθήκευση αλλαγών"):
                updated_df = update_row_by_id(
                    df_exp,
                    selected_id,
                    {
                        "Ημερομηνία": new_date,
                        "Κατηγορία": new_category,
                        "Είδος": new_type,
                        "Ποσό": new_amount,
                        "Πληρωτής": new_payer,
                        "Σημειώσεις": new_notes.strip(),
                    },
                    EXPENSE_COLUMNS,
                )
                if safe_write(SHEET_EXPENSES, updated_df):
                    st.success("Η εγγραφή ενημερώθηκε.")
                    st.rerun()

    if st.button("🗑️ Διαγραφή εξόδου", key="delete_expense_btn"):
        updated_df = delete_row_by_id(df_exp, selected_id)
        if safe_write(SHEET_EXPENSES, updated_df):
            st.success("Η εγγραφή διαγράφηκε.")
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

    st.markdown("### Φίλτρα")
    filtered = filter_tasks(df_task)
    show_table(filtered)

    if filtered.empty:
        return

    task_labels = build_labels(filtered, "_id", lambda row: f"{safe_text(row['Εργασία'])} | {safe_text(row['Κατάσταση'])}")
    task_ids = list(task_labels.keys())
    if not task_ids:
        return

    selected_id = st.selectbox(
        "Επιλογή εργασίας για edit / delete",
        options=task_ids,
        format_func=lambda rid: task_labels.get(rid, "Άγνωστη εργασία"),
    )

    row_df = df_task[df_task["_id"].astype(str) == str(selected_id)]
    if row_df.empty:
        return
    row = row_df.iloc[0]

    with st.expander("✏️ Edit εργασίας"):
        with st.form("task_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_task = st.text_input("Εργασία", value=safe_text(row["Εργασία"]))
                new_status = st.selectbox("Κατάσταση", TASK_STATUSES, index=default_index(TASK_STATUSES, safe_text(row["Κατάσταση"])))
            with c2:
                new_cost = st.number_input("Κόστος (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Κόστος"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
                new_priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES, index=default_index(TASK_PRIORITIES, safe_text(row["Προτεραιότητα"])))
            with c3:
                new_assignee = st.text_input("Ανάθεση", value=safe_text(row["Ανάθεση"]))
            new_notes = st.text_input("Σημειώσεις", value=safe_text(row["Σημειώσεις"]))

            if st.form_submit_button("Αποθήκευση αλλαγών") and new_task.strip():
                updated_df = update_row_by_id(
                    df_task,
                    selected_id,
                    {
                        "Εργασία": new_task.strip(),
                        "Κατάσταση": new_status,
                        "Κόστος": new_cost,
                        "Προτεραιότητα": new_priority,
                        "Ανάθεση": new_assignee.strip(),
                        "Σημειώσεις": new_notes.strip(),
                    },
                    TASK_COLUMNS,
                )
                if safe_write(SHEET_TASKS, updated_df):
                    st.success("Η εργασία ενημερώθηκε.")
                    st.rerun()

    if st.button("🗑️ Διαγραφή εργασίας", key="delete_task_btn"):
        updated_df = delete_row_by_id(df_task, selected_id)
        if safe_write(SHEET_TASKS, updated_df):
            st.success("Η εργασία διαγράφηκε.")
            st.rerun()


def render_offers(df_off: pd.DataFrame):
    st.subheader("💼 Προσφορές")

    st.markdown("### AI / OCR Εισαγωγή από φωτογραφία ή PDF")
    uploaded_offer = st.file_uploader(
        "Ανέβασε φωτογραφία ή PDF προσφοράς",
        type=["png", "jpg", "jpeg", "webp", "pdf"],
        key="offer_ai_upload",
    )

    if uploaded_offer is not None and st.button("🤖 Ανάλυση προσφοράς", key="analyze_offer_ai_btn"):
        try:
            with st.spinner("Γίνεται ανάγνωση της προσφοράς..."):
                parsed_offer, source_mode = extract_offer_with_fallback(uploaded_offer)

            parsed_offer["Σημειώσεις"] = f"[SOURCE={source_mode}] " + parsed_offer.get("Σημειώσεις", "")
            st.session_state["ai_offer_draft"] = parsed_offer

            if source_mode == "AI":
                st.success("Η προσφορά αναγνωρίστηκε με AI.")
            elif source_mode == "FREE_PDF_OCR":
                st.warning("Η προσφορά αναγνωρίστηκε με δωρεάν OCR από PDF. Έλεγξε προσεκτικά τα στοιχεία.")
            else:
                st.warning("Δεν ήταν δυνατή η πλήρης αυτόματη ανάγνωση της εικόνας. Συμπλήρωσε χειροκίνητα τα στοιχεία που λείπουν.")
        except Exception as e:
            st.error(f"Αποτυχία ανάλυσης προσφοράς: {e}")

    if "ai_offer_draft" in st.session_state:
        draft = st.session_state["ai_offer_draft"]
        with st.expander("🧾 Επιβεβαίωση αναγνωρισμένης προσφοράς", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                ai_provider = st.text_input("Πάροχος", value=str(draft.get("Πάροχος", "")), key="ai_provider")
                ai_category = st.selectbox("Κατηγορία", OFFER_CATEGORIES, index=default_index(OFFER_CATEGORIES, str(draft.get("Κατηγορία", "Άλλο"))), key="ai_category")
            with c2:
                ai_description = st.text_input("Περιγραφή", value=str(draft.get("Περιγραφή", "")), key="ai_description")
            with c3:
                ai_amount = st.number_input("Ποσό (€)", min_value=0.0, value=float(draft.get("Ποσό", 0) or 0), step=10.0, key="ai_amount")
            ai_notes = st.text_area("Σημειώσεις", value=str(draft.get("Σημειώσεις", "")), key="ai_notes", height=140)

            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾 Αποθήκευση προσφοράς", key="save_ai_offer_btn"):
                    updated_df = append_row(
                        df_off,
                        {
                            "Πάροχος": ai_provider.strip(),
                            "Περιγραφή": ai_description.strip(),
                            "Ποσό": ai_amount,
                            "Κατηγορία": ai_category,
                            "Σημειώσεις": ai_notes.strip(),
                        },
                        OFFER_COLUMNS,
                    )
                    if safe_write(SHEET_OFFERS, updated_df):
                        del st.session_state["ai_offer_draft"]
                        st.success("Η προσφορά αποθηκεύτηκε.")
                        st.rerun()
            with col_cancel:
                if st.button("❌ Απόρριψη", key="cancel_ai_offer_btn"):
                    del st.session_state["ai_offer_draft"]
                    st.rerun()

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

    st.markdown("### Φίλτρα")
    filtered = filter_offers(df_off)

    if not filtered.empty:
        temp = filtered.copy()
        temp["Ποσό"] = money_series(temp, "Ποσό")
        valid_temp = temp.dropna(subset=["Ποσό"])
        if not valid_temp.empty:
            best = valid_temp.sort_values("Ποσό").iloc[0]
            st.info(f"🏆 Καλύτερη προσφορά: {safe_text(best['Πάροχος'])} ({best['Ποσό']:.2f} €)")

    show_table(filtered)

    if filtered.empty:
        st.info("Χρειάζονται τουλάχιστον 2 προσφορές για σύγκριση.")
        return

    offer_labels = build_labels(filtered, "_id", lambda row: f"{safe_text(row['Πάροχος'])} | {safe_text(row['Περιγραφή'])}")
    offer_ids = list(offer_labels.keys())
    if not offer_ids:
        return

    selected_id = st.selectbox(
        "Επιλογή προσφοράς για edit / delete",
        options=offer_ids,
        format_func=lambda rid: offer_labels.get(rid, "Άγνωστη προσφορά"),
    )

    row_df = df_off[df_off["_id"].astype(str) == str(selected_id)]
    if not row_df.empty:
        row = row_df.iloc[0]

        with st.expander("✏️ Edit προσφοράς"):
            with st.form("offer_edit_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_provider = st.text_input("Πάροχος", value=safe_text(row["Πάροχος"]))
                    new_category = st.selectbox("Κατηγορία", OFFER_CATEGORIES, index=default_index(OFFER_CATEGORIES, safe_text(row["Κατηγορία"])))
                with c2:
                    new_description = st.text_input("Περιγραφή", value=safe_text(row["Περιγραφή"]))
                with c3:
                    new_amount = st.number_input("Ποσό (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Ποσό"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
                new_notes = st.text_input("Σημειώσεις", value=safe_text(row["Σημειώσεις"]))

                if st.form_submit_button("Αποθήκευση αλλαγών") and new_provider.strip():
                    updated_df = update_row_by_id(
                        df_off,
                        selected_id,
                        {
                            "Πάροχος": new_provider.strip(),
                            "Περιγραφή": new_description.strip(),
                            "Ποσό": new_amount,
                            "Κατηγορία": new_category,
                            "Σημειώσεις": new_notes.strip(),
                        },
                        OFFER_COLUMNS,
                    )
                    if safe_write(SHEET_OFFERS, updated_df):
                        st.success("Η προσφορά ενημερώθηκε.")
                        st.rerun()

        if st.button("🗑️ Διαγραφή προσφοράς", key="delete_offer_btn"):
            updated_df = delete_row_by_id(df_off, selected_id)
            if safe_write(SHEET_OFFERS, updated_df):
                st.success("Η προσφορά διαγράφηκε.")
                st.rerun()

    st.markdown("### Σύγκριση προσφορών")
    if len(df_off) >= 2:
        compare_options = build_labels(
            df_off,
            "_id",
            lambda row: f"{safe_text(row['Πάροχος'])} | {safe_text(row['Περιγραφή'])} | {format_currency(pd.to_numeric(pd.Series([row['Ποσό']]), errors='coerce').fillna(0).iloc[0])}",
        )
        compare_ids = list(compare_options.keys())

        col1, col2 = st.columns(2)
        with col1:
            offer_a = st.selectbox("Προσφορά Α", options=compare_ids, format_func=lambda rid: compare_options.get(rid, "Άγνωστη προσφορά"), key="compare_offer_a")
        with col2:
            offer_b = st.selectbox("Προσφορά Β", options=compare_ids, format_func=lambda rid: compare_options.get(rid, "Άγνωστη προσφορά"), key="compare_offer_b")

        if offer_a != offer_b:
            row_a_df = df_off[df_off["_id"].astype(str) == str(offer_a)]
            row_b_df = df_off[df_off["_id"].astype(str) == str(offer_b)]

            if not row_a_df.empty and not row_b_df.empty:
                row_a = row_a_df.iloc[0]
                row_b = row_b_df.iloc[0]

                amount_a = float(pd.to_numeric(pd.Series([row_a["Ποσό"]]), errors="coerce").fillna(0).iloc[0])
                amount_b = float(pd.to_numeric(pd.Series([row_b["Ποσό"]]), errors="coerce").fillna(0).iloc[0])

                diff = abs(amount_a - amount_b)
                cheaper = safe_text(row_a["Πάροχος"]) if amount_a < amount_b else safe_text(row_b["Πάροχος"])
                percent = (diff / max(amount_a, amount_b) * 100) if max(amount_a, amount_b) > 0 else 0

                c1, c2, c3 = st.columns(3)
                c1.metric("Προσφορά Α", format_currency(amount_a))
                c2.metric("Προσφορά Β", format_currency(amount_b))
                c3.metric("Διαφορά", f"{diff:,.2f} € ({percent:.1f}%)")

                st.success(f"Φθηνότερη προσφορά: {cheaper}")

                comparison_df = pd.DataFrame([
                    {"Πεδίο": "Πάροχος", "Προσφορά Α": safe_text(row_a["Πάροχος"]), "Προσφορά Β": safe_text(row_b["Πάροχος"])},
                    {"Πεδίο": "Περιγραφή", "Προσφορά Α": safe_text(row_a["Περιγραφή"]), "Προσφορά Β": safe_text(row_b["Περιγραφή"])},
                    {"Πεδίο": "Κατηγορία", "Προσφορά Α": safe_text(row_a["Κατηγορία"]), "Προσφορά Β": safe_text(row_b["Κατηγορία"])},
                    {"Πεδίο": "Σημειώσεις", "Προσφορά Α": safe_text(row_a["Σημειώσεις"]), "Προσφορά Β": safe_text(row_b["Σημειώσεις"])},
                ])
                st.dataframe(comparison_df, use_container_width=True)
    else:
        st.info("Χρειάζονται τουλάχιστον 2 προσφορές για σύγκριση.")


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

        card_start("Έξοδα ανά Είδος")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Είδος", as_index=False)["Ποσό"].sum()
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_donut_chart(summary, "Είδος", "Ποσό", "Αμοιβή vs Υλικά"), use_container_width=True)
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
    render_dashboard(df_expenses, df_tasks, df_offers)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
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

