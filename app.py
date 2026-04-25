import base64
import io
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

# Φόρτωση δεδομένων από Google Sheets
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()

SHEET_EXPENSES = "Expenses"
SHEET_FEES = "Fees"
SHEET_CONTACTS = "Contacts"
SHEET_MATERIALS = "Materials"
SHEET_LOANS = "Loan"
SHEET_TASKS = "Progress"
SHEET_OFFERS = "Offers"
SHEET_GALLERY = "Gallery"

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
ROOMS = ["Κουζίνα", "Μπάνιο", "Σαλόνι", "Υπνοδωμάτιο", "Μπαλκόνι", "Διάδρομος", "Άλλο"]

def safe_read(sheet_name, columns):
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
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
    except Exception:
        return pd.DataFrame(columns=columns)

def safe_write(sheet_name, df):
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        return False

def append_row(df, row_data, columns):
    row_data["_id"] = str(uuid.uuid4())[:8]
    new_row = pd.DataFrame([row_data])
    for col in columns:
        if col not in new_row.columns:
            new_row[col] = ""
    return pd.concat([df, new_row[columns]], ignore_index=True)

def money_series(df, col):
    if col not in df.columns or df.empty:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)

def format_currency(value):
    try:
        return f"{float(value):,.2f} €"
    except:
        return "0.00 €"

def show_table(df, hide_id=True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα")
        return
    display = df.copy()
    if hide_id and "_id" in display.columns:
        display = display.drop(columns=["_id"])
    st.dataframe(display, use_container_width=True)

def render_progress_line(label, value, total, color):
    pct = (value / total * 100) if total > 0 else 0
    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem;">
            <span>{label}</span>
            <span>{format_currency(value)} / {format_currency(total)}</span>
        </div>
        <div style="background: #e0d5c5; border-radius: 10px; height: 12px; overflow: hidden;">
            <div style="background: {color}; width: {min(100, pct)}%; height: 100%; border-radius: 10px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def calculate_fee_status(df_fee, df_exp):
    if df_fee.empty:
        return pd.DataFrame()
    results = []
    for _, fee in df_fee.iterrows():
        cat = fee.get("Κατηγορία", "")
        if not cat:
            continue
        total = float(fee.get("Ποσό", 0))
        relevant = df_exp[(df_exp["Κατηγορία"] == cat) & (df_exp["Είδος"] == "Αμοιβή")] if not df_exp.empty else pd.DataFrame()
        paid_me = money_series(relevant[relevant["Πληρωτής"] == "Εγώ"], "Ποσό").sum()
        paid_father = money_series(relevant[relevant["Πληρωτής"] == "Πατέρας"], "Ποσό").sum()
        results.append({
            "Κατηγορία": cat,
            "Συνολικό": total,
            "Πλήρωσα Εγώ": paid_me,
            "Πλήρωσε Πατέρας": paid_father,
            "Περιγραφή": fee.get("Περιγραφή", f"Αμοιβή {cat}")
        })
    return pd.DataFrame(results)

def calculate_material_split(df_exp):
    if df_exp.empty:
        return pd.DataFrame()
    mats = df_exp[df_exp["Είδος"] == "Υλικά"].copy()
    if mats.empty:
        return pd.DataFrame()
    mats["Ποσό"] = money_series(mats, "Ποσό")
    summary = []
    for cat in mats["Κατηγορία"].unique():
        sub = mats[mats["Κατηγορία"] == cat]
        summary.append({
            "Κατηγορία": cat,
            "Σύνολο": sub["Ποσό"].sum(),
            "Εγώ": sub[sub["Πληρωτής"] == "Εγώ"]["Ποσό"].sum(),
            "Πατέρας": sub[sub["Πληρωτής"] == "Πατέρας"]["Ποσό"].sum()
        })
    return pd.DataFrame(summary)

def prepare_timeline(df_tasks):
    if df_tasks.empty:
        return pd.DataFrame()
    rows = []
    for _, row in df_tasks.iterrows():
        name = row.get("Εργασία", "")
        if not name:
            continue
        start = pd.to_datetime(row.get("Ημερομηνία_Έναρξης", date.today()))
        end = pd.to_datetime(row.get("Ημερομηνία_Λήξης", start + timedelta(days=1)))
        rows.append({"Task": name, "Start": start, "End": end, "Status": row.get("Κατάσταση", "To Do")})
    return pd.DataFrame(rows)

# Κύριο Dashboard
def render_dashboard(df_exp, df_fee, df_material, df_loan, df_task, df_off, df_gal):
    st.title("🏠 Dashboard Ανακαίνισης")
    
    total_spent = money_series(df_exp, "Ποσό").sum()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Σύνολο Εξόδων", format_currency(total_spent))
    col2.metric("Πλήθος Εγγραφών", len(df_exp))
    col3.metric("Αμοιβές", len(df_fee))
    col4.metric("Εργασίες", len(df_task))
    
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
                st.caption(row['Περιγραφή'])
                render_progress_line("Σύνολο", row['Πλήρωσα Εγώ'] + row['Πλήρωσε Πατέρας'], row['Συνολικό'], "#c9a96b")
                render_progress_line("Εγώ", row['Πλήρωσα Εγώ'], row['Συνολικό'], "#3f7d6b")
                render_progress_line("Πατέρας", row['Πλήρωσε Πατέρας'], row['Συνολικό'], "#915f35")
                st.divider()
    
    st.subheader("📦 Υλικά & Έξοδα")
    materials = calculate_material_split(df_exp)
    if materials.empty:
        st.info("Δεν υπάρχουν υλικά")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(materials.iterrows()):
            with cols[i % 2]:
                st.markdown(f"**🔨 {row['Κατηγορία']}**")
                render_progress_line("Σύνολο", row['Εγώ'] + row['Πατέρας'], row['Σύνολο'], "#c9a96b")
                render_progress_line("Εγώ", row['Εγώ'], row['Σύνολο'], "#3f7d6b")
                render_progress_line("Πατέρας", row['Πατέρας'], row['Σύνολο'], "#915f35")
                st.divider()
    
    st.subheader("🗓️ Χρονοδιάγραμμα")
    timeline = prepare_timeline(df_task)
    if not timeline.empty:
        import plotly.express as px
        fig = px.timeline(timeline, x_start="Start", x_end="End", y="Task", color="Status")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# Σελίδες
def render_expenses(df):
    st.subheader("💰 Έξοδα")
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
                new = {"Ημερομηνία": str(date_val), "Κατηγορία": cat, "Είδος": typ, "Ποσό": amount, "Πληρωτής": payer, "Σημειώσεις": notes}
                updated = append_row(df, new, EXPENSE_COLUMNS)
                if safe_write(SHEET_EXPENSES, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)

def render_fees(df, df_exp):
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
    with st.expander("➕ Νέο υλικό"):
        with st.form("material_form"):
            col1, col2 = st.columns(2)
            with col1:
                cat = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
                name = st.text_input("Υλικό")
                qty = st.number_input("Ποσότητα", min_value=0.0, step=1.0)
            with col2:
                unit = st.selectbox("Μονάδα", ["τεμ", "μέτρα", "m2", "κιλά"])
                price = st.number_input("Τιμή μονάδας (€)", min_value=0.0, step=0.5)
                notes = st.text_input("Σημειώσεις")
            total = qty * price
            st.caption(f"Σύνολο: {format_currency(total)}")
            if st.form_submit_button("Αποθήκευση") and name:
                new = {"Κατηγορία": cat, "Υλικό": name, "Ποσότητα": qty, "Μονάδα": unit, "Τιμή_Μονάδας": price, "Σύνολο": total, "Προμηθευτής": "", "Κατάσταση": "Προς αγορά", "Σημειώσεις": notes}
                updated = append_row(df, new, MATERIAL_COLUMNS)
                if safe_write(SHEET_MATERIALS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)

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
    with st.expander("➕ Νέο δάνειο"):
        with st.form("loan_form"):
            col1, col2 = st.columns(2)
            with col1:
                desc = st.text_input("Περιγραφή")
                principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, step=1000.0)
            with col2:
                rate = st.number_input("Επιτόκιο (%)", min_value=0.0, step=0.1)
                months = st.number_input("Μήνες", min_value=1, step=1)
            if st.form_submit_button("Αποθήκευση") and desc:
                monthly_rate = rate / 100 / 12
                if monthly_rate == 0:
                    installment = principal / months if months > 0 else 0
                else:
                    installment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
                new = {"Περιγραφή": desc, "Κεφάλαιο": principal, "Επιτόκιο": rate, "Μήνες": months, "Μηνιαία_Δόση": installment, "Έναρξη": str(date.today()), "Κατάσταση": "Ενεργό", "Σημειώσεις": ""}
                updated = append_row(df, new, LOAN_COLUMNS)
                if safe_write(SHEET_LOANS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    show_table(df)

def render_timeline_page(df):
    st.subheader("🗓️ Timeline")
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
            if st.form_submit_button("Αποθήκευση") and name:
                new = {"Εργασία": name, "Χώρος": room, "Κατάσταση": status, "Ημερομηνία_Έναρξης": str(start), "Ημερομηνία_Λήξης": str(end), "Κόστος": 0, "Προτεραιότητα": "Μεσαία", "Ανάθεση": assignee, "Σημειώσεις": ""}
                updated = append_row(df, new, TASK_COLUMNS)
                if safe_write(SHEET_TASKS, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()
    
    timeline = prepare_timeline(df)
    if not timeline.empty:
        import plotly.express as px
        fig = px.timeline(timeline, x_start="Start", x_end="End", y="Task", color="Status")
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
    show_table(df)

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
                st.image(f"data:image/jpeg;base64,{row['Image_Data']}", width=200)
                st.caption(f"{row['Χώρος']} - {row['Τίτλος']}")

def render_analytics(df_exp, df_fee, df_material, df_task, df_off):
    st.subheader("📊 Αναλύσεις")
    total = money_series(df_exp, "Ποσό").sum()
    st.metric("Σύνολο Εξόδων", format_currency(total))
    if not df_exp.empty:
        by_cat = df_exp.groupby("Κατηγορία")["Ποσό"].sum().reset_index()
        st.dataframe(by_cat)

def render_calculator():
    st.subheader("🧮 Calculator")
    st.info("Απλός υπολογιστής υλικών - προς υλοποίηση")

# MAIN
df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
df_contacts = safe_read(SHEET_CONTACTS, CONTACT_COLUMNS)
df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
df_loans = safe_read(SHEET_LOANS, LOAN_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)
df_gallery = safe_read(SHEET_GALLERY, GALLERY_COLUMNS)

MENU_OPTIONS = ["🏠 Dashboard", "💰 Έξοδα", "💼 Αμοιβές", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📋 Εργασίες", "💼 Προσφορές", "📸 Gallery", "📊 Αναλύσεις", "🧮 Calculator"]

st.sidebar.markdown("### Πλοήγηση")
menu = st.sidebar.selectbox("Μενού", MENU_OPTIONS)

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
    render_timeline_page(df_tasks)
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

