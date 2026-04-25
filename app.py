import base64
import io
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Methana Earth & Fire", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #fbf6ee 0%, #f4ecdf 100%); }
.hero { background: linear-gradient(135deg, #3f2f22 0%, #5a4330 50%, #7a5a3d 100%); color: #fffaf2; padding: 28px 30px; border-radius: 24px; margin-bottom: 18px; }
.hero h1 { margin: 0; font-size: 2.2rem; }
.hero p { margin: 10px 0 0 0; color: rgba(255,250,242,0.88); }
.split-card { background: rgba(255,250,242,0.96); border-radius: 18px; padding: 16px 18px; margin-bottom: 14px; border: 1px solid rgba(90,67,48,0.08); }
.split-title { font-size: 1.04rem; font-weight: 700; color: #4c3826; }
.split-sub { font-size: 0.92rem; color: #7a5a3d; margin-bottom: 10px; }
.split-line { margin-bottom: 10px; }
.split-line-top { display: flex; justify-content: space-between; font-size: 0.92rem; color: #4c3826; margin-bottom: 4px; }
.split-track { height: 14px; border-radius: 999px; background: #eadfce; overflow: hidden; }
.split-fill { height: 100%; border-radius: 999px; }
.split-total { background: linear-gradient(90deg, #c9a96b 0%, #dec18e 100%); }
.split-me { background: linear-gradient(90deg, #3f7d6b 0%, #5fa391 100%); }
.split-father { background: linear-gradient(90deg, #915f35 0%, #b67d4d 100%); }
.split-remaining { background: linear-gradient(90deg, #8a3b3b 0%, #be5a5a 100%); }
.dashboard-block-title { font-size: 1.18rem; font-weight: 800; color: #4c3826; margin: 18px 0 8px 0; }
.dashboard-block-subtitle { color: #7a5a3d; margin-bottom: 12px; }
div[data-testid="stMetric"] { background: rgba(255,250,242,0.98); border-radius: 18px; padding: 14px; border-top: 4px solid #c9a96b; }
.maker { margin-top: 24px; padding: 12px 14px; background: rgba(255,250,242,0.88); border-radius: 14px; color: #5a4330; }
</style>
""", unsafe_allow_html=True)

LOGO_PATH = "assets/logo.png"
header_left, header_right = st.columns([0.85, 5.15])
with header_left:
    try:
        st.image(LOGO_PATH, width=112)
    except Exception:
        pass
with header_right:
    st.markdown('<div class="hero"><h1>Methana Earth & Fire</h1><p>Project dashboard για ανακαίνιση, κόστος, συνεργεία, υλικά και planning.</p></div>', unsafe_allow_html=True)

SHEET_EXPENSES = "Expenses"
SHEET_FEES = "Fees"
SHEET_CONTACTS = "Contacts"
SHEET_MATERIALS = "Materials"
SHEET_LOANS = "Loan"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"

MENU_OPTIONS = ["🏠 Dashboard", "💰 Έξοδα", "💼 Αμοιβές", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📋 Εργασίες", "💼 Προσφορές", "📸 Gallery", "📊 Αναλύσεις", "🧮 Calculator"]

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

@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()

def empty_df(columns):
    return pd.DataFrame(columns=columns)

def ensure_columns(df, columns):
    if df is None or df.empty:
        return empty_df(columns)
    fixed = df.copy()
    for col in columns:
        if col not in fixed.columns:
            fixed[col] = ""
    return fixed[columns]

def normalize_ids(df):
    fixed = df.copy()
    if "_id" not in fixed.columns:
        fixed["_id"] = ""
    fixed["_id"] = fixed["_id"].astype(str)
    missing = fixed["_id"].isin(["", "nan", "None"])
    if missing.any():
        fixed.loc[missing, "_id"] = [str(uuid.uuid4())[:8] for _ in range(missing.sum())]
    return fixed

def safe_read(sheet_name, columns):
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

def safe_write(sheet_name, df):
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης: {e}")
        return False

def append_row(df, row_data, columns):
    row_data["_id"] = str(uuid.uuid4())[:8]
    current = ensure_columns(df, columns)
    new_row = ensure_columns(pd.DataFrame([row_data]), columns)
    return pd.concat([current, new_row], ignore_index=True)

def delete_row_by_id(df, row_id):
    if df.empty:
        return df
    updated = df[df["_id"].astype(str) != str(row_id)].copy()
    return updated.reset_index(drop=True)

def money_series(df, col):
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)

def safe_text(value, fallback=""):
    if pd.isna(value):
        return fallback
    return str(value)

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def format_currency(value):
    try:
        return f"{float(value):,.2f} €"
    except Exception:
        return "0.00 €"

def parse_date(value, fallback=None):
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return fallback
    return parsed.date()

def show_table(df, hide_id=True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return
    display_df = df.copy()
    if hide_id and "_id" in display_df.columns:
        display_df = display_df.drop(columns=["_id"])
    st.dataframe(display_df, use_container_width=True)

def clamp_percent(value, total):
    if total <= 0:
        return 0.0
    return max(0.0, min(100.0, (value / total) * 100))

def render_progress_line(label, value, total, css_class, right_text=None):
    pct = clamp_percent(value, total)
    right = right_text or f"{format_currency(value)} / {format_currency(total)}"
    st.markdown(f'<div class="split-line"><div class="split-line-top"><span>{label}</span><span>{right}</span></div><div class="split-track"><div class="split-fill {css_class}" style="width:{pct:.2f}%"></div></div></div>', unsafe_allow_html=True)

def render_split_card(title, subtitle, total_amount, paid_me, paid_father, target_me=None, target_father=None):
    total_paid = paid_me + paid_father
    remaining = max(total_amount - total_paid, 0)
    st.markdown(f'<div class="split-card"><div class="split-title">{title}</div><div class="split-sub">{subtitle}</div>', unsafe_allow_html=True)
    render_progress_line("Σύνολο καλυμμένο", total_paid, total_amount, "split-total", f"{format_currency(total_paid)} / {format_currency(total_amount)}")
    if target_me and target_me > 0:
        render_progress_line("Εγώ", paid_me, target_me, "split-me", f"{format_currency(paid_me)} από {format_currency(target_me)}")
    else:
        render_progress_line("Εγώ", paid_me, total_amount, "split-me", f"{format_currency(paid_me)}")
    if target_father and target_father > 0:
        render_progress_line("Πατέρας", paid_father, target_father, "split-father", f"{format_currency(paid_father)} από {format_currency(target_father)}")
    else:
        render_progress_line("Πατέρας", paid_father, total_amount, "split-father", f"{format_currency(paid_father)}")
    render_progress_line("Απομένει", remaining, total_amount, "split-remaining", format_currency(remaining))
    st.markdown("</div>", unsafe_allow_html=True)

def make_bar_chart(df, x, y, title):
    fig = px.bar(df, x=x, y=y, title=title, color=x, color_discrete_sequence=["#c9a96b", "#6b4f3a", "#3f7d6b"])
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=55, b=10), height=360)
    return fig

def image_to_base64(uploaded_file, max_size=(1400, 1400), quality=74):
    image = Image.open(uploaded_file).convert("RGB")
    image.thumbnail(max_size)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def calculate_fee_status(df_fee, df_exp):
    if df_fee.empty:
        return pd.DataFrame()
    results = []
    for _, fee in df_fee.iterrows():
        cat = safe_text(fee.get("Κατηγορία", ""))
        if not cat:
            continue
        total = safe_float(fee.get("Ποσό", 0))
        relevant = df_exp[(df_exp["Κατηγορία"] == cat) & (df_exp["Είδος"] == "Αμοιβή")] if not df_exp.empty else pd.DataFrame()
        paid_me = money_series(relevant[relevant["Πληρωτής"] == "Εγώ"], "Ποσό").sum()
        paid_father = money_series(relevant[relevant["Πληρωτής"] == "Πατέρας"], "Ποσό").sum()
        results.append({"Κατηγορία": cat, "Συνολικό Ποσό": total, "Πλήρωσα Εγώ": paid_me, "Πλήρωσε Πατέρας": paid_father, "Στόχος Εγώ": total/2, "Στόχος Πατέρας": total/2, "Περιγραφή": safe_text(fee.get("Περιγραφή"), f"Αμοιβή {cat}")})
    return pd.DataFrame(results)

def calculate_material_split_from_expenses(df_exp):
    if df_exp.empty:
        return pd.DataFrame()
    materials = df_exp[df_exp["Είδος"] == "Υλικά"].copy()
    if materials.empty:
        return pd.DataFrame()
    materials["Ποσό"] = money_series(materials, "Ποσό")
    summary = []
    for category in materials["Κατηγορία"].unique():
        cat_mats = materials[materials["Κατηγορία"] == category]
        total = cat_mats["Ποσό"].sum()
        paid_me = cat_mats[cat_mats["Πληρωτής"] == "Εγώ"]["Ποσό"].sum()
        paid_father = cat_mats[cat_mats["Πληρωτής"] == "Πατέρας"]["Ποσό"].sum()
        summary.append({"Κατηγορία": category, "Σύνολο": total, "Εγώ": paid_me, "Πατέρας": paid_father, "Υπόλοιπο": total - paid_me - paid_father})
    return pd.DataFrame(summary).sort_values("Σύνολο", ascending=False)

def prepare_timeline_df(df_tasks):
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
        rows.append({"Task": task_name, "Start": start, "End": end, "Resource": safe_text(row.get("Κατάσταση", "Εκκρεμεί"))})
    return pd.DataFrame(rows)
    def render_dashboard(df_exp, df_fee, df_material, df_loan, df_task, df_off, df_gal):
    st.markdown('<div class="dashboard-block-title">🏠 Dashboard Ανακαίνισης</div>', unsafe_allow_html=True)
    
    col_budget, col_spent, col_remaining, col_tasks = st.columns(4)
    with col_budget:
        budget = st.number_input("Συνολικό Budget (€)", min_value=0.0, value=30000.0, step=1000.0, key="global_budget")
    with col_spent:
        total_spent = money_series(df_exp, "Ποσό").sum()
        st.metric("Σύνολο Εξόδων", format_currency(total_spent))
    with col_remaining:
        remaining = budget - total_spent
        st.metric("Υπόλοιπο Budget", format_currency(remaining))
    with col_tasks:
        active_tasks = len(df_task[df_task["Κατάσταση"] == "Doing"]) if not df_task.empty else 0
        st.metric("Ενεργές Εργασίες", active_tasks)
    
    st.markdown("---")
    st.markdown('<div class="dashboard-block-title">💰 Αμοιβές Συνεργείων</div>', unsafe_allow_html=True)
    
    fee_cards = calculate_fee_status(df_fee, df_exp)
    if fee_cards.empty:
        st.info("📋 Δεν υπάρχουν αμοιβές συνεργείων.")
    else:
        cols = st.columns(2)
        for idx, (_, card) in enumerate(fee_cards.iterrows()):
            with cols[idx % 2]:
                render_split_card(
                    title=f"👷 {card['Κατηγορία']}",
                    subtitle=card['Περιγραφή'],
                    total_amount=float(card['Συνολικό Ποσό']),
                    paid_me=float(card['Πλήρωσα Εγώ']),
                    paid_father=float(card['Πλήρωσε Πατέρας']),
                    target_me=float(card['Στόχος Εγώ']),
                    target_father=float(card['Στόχος Πατέρας'])
                )
    
    st.markdown("---")
    st.markdown('<div class="dashboard-block-title">📦 Υλικά & Λοιπά Έξοδα</div>', unsafe_allow_html=True)
    
    material_cards = calculate_material_split_from_expenses(df_exp)
    if material_cards.empty:
        st.info("📦 Δεν υπάρχουν υλικά.")
    else:
        cols = st.columns(2)
        for idx, (_, card) in enumerate(material_cards.iterrows()):
            with cols[idx % 2]:
                render_split_card(
                    title=f"🔨 {card['Κατηγορία']}",
                    subtitle="Υλικά και αναλώσιμα",
                    total_amount=float(card['Σύνολο']),
                    paid_me=float(card['Εγώ']),
                    paid_father=float(card['Πατέρας']),
                    target_me=None,
                    target_father=None
                )
    
    st.markdown("---")
    st.markdown('<div class="dashboard-block-title">🗓️ Χρονοδιάγραμμα</div>', unsafe_allow_html=True)
    
    timeline_df = prepare_timeline_df(df_task)
    if timeline_df.empty:
        st.info("📅 Δεν υπάρχουν εργασίες.")
    else:
        gantt = px.timeline(timeline_df, x_start="Start", x_end="End", y="Task", color="Resource", color_discrete_map={"To Do": "#c9a96b", "Doing": "#3f7d6b", "Done": "#915f35"})
        gantt.update_layout(height=400, margin=dict(l=10, r=10, t=50, b=10))
        gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(gantt, use_container_width=True)

def render_expenses(df_exp):
    st.subheader("💰 Έξοδα")
    with st.expander("➕ Νέο έξοδο", expanded=False):
        with st.form("expense_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                date_val = st.date_input("Ημερομηνία")
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
            with col2:
                expense_type = st.selectbox("Είδος", EXPENSE_TYPES)
                payer = st.selectbox("Πληρωτής", PAYERS)
            with col3:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση"):
                new_data = {"Ημερομηνία": str(date_val), "Κατηγορία": category, "Είδος": expense_type, "Ποσό": amount, "Πληρωτής": payer, "Σημειώσεις": notes}
                updated = append_row(df_exp, new_data, EXPENSE_COLUMNS)
                if safe_write(SHEET_EXPENSES, updated):
                    st.success("Το έξοδο αποθηκεύτηκε")
                    st.rerun()
    show_table(df_exp)

def render_fees(df_fee, df_exp):
    st.subheader("💼 Αμοιβές Συνεργείων")
    with st.expander("➕ Νέα αμοιβή", expanded=False):
        with st.form("fee_form"):
            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                total_amount = st.number_input("Συνολικό Ποσό (€)", min_value=0.0, step=100.0)
            with col2:
                description = st.text_input("Περιγραφή εργασίας")
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση"):
                if description.strip():
                    new_data = {"Κατηγορία": category, "Περιγραφή": description, "Ποσό": total_amount, "Σημειώσεις": notes}
                    updated = append_row(df_fee, new_data, FEE_COLUMNS)
                    if safe_write(SHEET_FEES, updated):
                        st.success("Η αμοιβή καταχωρήθηκε")
                        st.rerun()
                else:
                    st.warning("Συμπληρώστε περιγραφή")
    show_table(df_fee)

def render_materials(df_mat):
    st.subheader("📦 Υλικά")
    with st.expander("➕ Νέο υλικό", expanded=False):
        with st.form("material_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                name = st.text_input("Υλικό")
            with col2:
                quantity = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
                unit = st.selectbox("Μονάδα", MATERIAL_UNITS)
            with col3:
                price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
                notes = st.text_input("Σημειώσεις")
            total_val = quantity * price
            st.caption(f"Σύνολο: {format_currency(total_val)}")
            if st.form_submit_button("Αποθήκευση") and name:
                new_data = {"Κατηγορία": category, "Υλικό": name, "Ποσότητα": quantity, "Μονάδα": unit, "Τιμή_Μονάδας": price, "Σύνολο": total_val, "Προμηθευτής": "", "Κατάσταση": "Προς αγορά", "Σημειώσεις": notes}
                updated = append_row(df_mat, new_data, MATERIAL_COLUMNS)
                if safe_write(SHEET_MATERIALS, updated):
                    st.success("Το υλικό αποθηκεύτηκε")
                    st.rerun()
    show_table(df_mat)

def render_contacts(df_contact):
    st.subheader("📞 Επαφές")
    with st.expander("➕ Νέα επαφή", expanded=False):
        with st.form("contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Όνομα")
                role = st.selectbox("Ρόλος", CONTACT_ROLES)
            with col2:
                phone = st.text_input("Τηλέφωνο")
                email = st.text_input("Email")
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and name:
                new_data = {"Όνομα": name, "Ρόλος": role, "Τηλέφωνο": phone, "Email": email, "Περιοχή": "", "Σημειώσεις": notes}
                updated = append_row(df_contact, new_data, CONTACT_COLUMNS)
                if safe_write(SHEET_CONTACTS, updated):
                    st.success("Η επαφή αποθηκεύτηκε")
                    st.rerun()
    show_table(df_contact)

def render_loans(df_loan):
    st.subheader("🏦 Δάνειο")
    with st.expander("➕ Νέο δάνειο", expanded=False):
        with st.form("loan_form"):
            col1, col2 = st.columns(2)
            with col1:
                desc = st.text_input("Περιγραφή")
                principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, step=1000.0)
            with col2:
                rate = st.number_input("Επιτόκιο (%)", min_value=0.0, step=0.1)
                months = st.number_input("Μήνες", min_value=1, step=1)
            monthly_rate = rate / 100 / 12
            if monthly_rate == 0:
                installment = principal / months if months > 0 else 0
            else:
                installment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
            st.metric("Μηνιαία Δόση", format_currency(installment))
            if st.form_submit_button("Αποθήκευση") and desc:
                new_data = {"Περιγραφή": desc, "Κεφάλαιο": principal, "Επιτόκιο": rate, "Μήνες": months, "Μηνιαία_Δόση": installment, "Έναρξη": str(date.today()), "Κατάσταση": "Ενεργό", "Σημειώσεις": ""}
                updated = append_row(df_loan, new_data, LOAN_COLUMNS)
                if safe_write(SHEET_LOANS, updated):
                    st.success("Το δάνειο αποθηκεύτηκε")
                    st.rerun()
    show_table(df_loan)

def render_timeline(df_task):
    st.subheader("🗓️ Timeline")
    with st.expander("➕ Νέα εργασία", expanded=False):
        with st.form("task_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Εργασία")
                room = st.selectbox("Χώρος", ROOMS)
            with col2:
                status = st.selectbox("Κατάσταση", TASK_STATUSES)
                start = st.date_input("Ημερομηνία έναρξης")
            with col3:
                end = st.date_input("Ημερομηνία λήξης")
                assignee = st.text_input("Ανάθεση")
            if st.form_submit_button("Αποθήκευση") and name:
                new_data = {"Εργασία": name, "Χώρος": room, "Κατάσταση": status, "Ημερομηνία_Έναρξης": str(start), "Ημερομηνία_Λήξης": str(end), "Κόστος": 0, "Προτεραιότητα": "Μεσαία", "Ανάθεση": assignee, "Σημειώσεις": ""}
                updated = append_row(df_task, new_data, TASK_COLUMNS)
                if safe_write(SHEET_TASKS, updated):
                    st.success("Η εργασία αποθηκεύτηκε")
                    st.rerun()
    
    timeline_df = prepare_timeline_df(df_task)
    if not timeline_df.empty:
        gantt = px.timeline(timeline_df, x_start="Start", x_end="End", y="Task", color="Resource", color_discrete_map={"To Do": "#c9a96b", "Doing": "#3f7d6b", "Done": "#915f35"})
        gantt.update_layout(height=450, margin=dict(l=10, r=10, t=55, b=10))
        gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(gantt, use_container_width=True)
    show_table(df_task)

def render_tasks(df_task):
    st.subheader("📋 Εργασίες")
    show_table(df_task)

def render_offers(df_off):
    st.subheader("💼 Προσφορές")
    with st.expander("➕ Νέα προσφορά", expanded=False):
        with st.form("offer_form"):
            col1, col2 = st.columns(2)
            with col1:
                provider = st.text_input("Πάροχος")
                category = st.selectbox("Κατηγορία", OFFER_CATEGORIES)
            with col2:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=100.0)
                notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and provider:
                new_data = {"Πάροχος": provider, "Περιγραφή": "", "Ποσό": amount, "Κατηγορία": category, "Σημειώσεις": notes}
                updated = append_row(df_off, new_data, OFFER_COLUMNS)
                if safe_write(SHEET_OFFERS, updated):
                    st.success("Η προσφορά αποθηκεύτηκε")
                    st.rerun()
    show_table(df_off)

def render_gallery(df_gal):
    st.subheader("📸 Gallery")
    with st.expander("➕ Νέα εικόνα", expanded=False):
        with st.form("gallery_form"):
            col1, col2 = st.columns(2)
            with col1:
                room = st.selectbox("Χώρος", ROOMS)
                title = st.text_input("Τίτλος")
            with col2:
                img_type = st.selectbox("Τύπος", IMAGE_TYPES)
            uploaded = st.file_uploader("Ανέβασε εικόνα", type=["jpg", "png", "jpeg", "webp"])
            notes = st.text_input("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση") and uploaded:
                img_data = image_to_base64(uploaded)
                new_data = {"Χώρος": room, "Τίτλος": title, "Τύπος": img_type, "Image_URL": "", "Image_Data": img_data, "Σημειώσεις": notes}
                updated = append_row(df_gal, new_data, GALLERY_COLUMNS)
                if safe_write(SHEET_GALLERY, updated):
                    st.success("Η εικόνα αποθηκεύτηκε")
                    st.rerun()
    if not df_gal.empty:
        preview = df_gal.tail(6)
        cols = st.columns(3)
        for idx, (_, row) in enumerate(preview.iterrows()):
            with cols[idx % 3]:
                if row.get("Image_Data"):
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", use_container_width=True)
                st.caption(f"{safe_text(row['Χώρος'])} | {safe_text(row['Τίτλος'])}")

def render_analytics(df_exp, df_fee, df_material, df_task, df_off):
    st.subheader("📊 Αναλύσεις")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Έξοδα ανά κατηγορία**")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum().sort_values("Ποσό", ascending=False)
            st.dataframe(summary, use_container_width=True)
            st.plotly_chart(make_bar_chart(summary, "Κατηγορία", "Ποσό", "Σύνολο ανά κατηγορία"), use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα")
    with col2:
        st.markdown("**Αμοιβές**")
        fee_status = calculate_fee_status(df_fee, df_exp)
        if not fee_status.empty:
            display_df = fee_status[["Κατηγορία", "Συνολικό Ποσό", "Πλήρωσα Εγώ", "Πλήρωσε Πατέρας"]].copy()
            display_df["Συνολικό Ποσό"] = display_df["Συνολικό Ποσό"].apply(format_currency)
            display_df["Πλήρωσα Εγώ"] = display_df["Πλήρωσα Εγώ"].apply(format_currency)
            display_df["Πλήρωσε Πατέρας"] = display_df["Πλήρωσε Πατέρας"].apply(format_currency)
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν αμοιβές")

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

# MAIN
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)

st.sidebar.markdown("### Πλοήγηση")
menu = st.sidebar.selectbox("Μενού", MENU_OPTIONS, index=0)
st.sidebar.markdown("---")
st.sidebar.caption(f"Τελευταία ενημέρωση: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.caption("Κατασκευαστής: Σκλίβας Δημήτριος")

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

st.markdown('<div class="maker">Κατασκευαστής εφαρμογής: <strong>Σκλίβας Δημήτριος</strong></div>', unsafe_allow_html=True)
