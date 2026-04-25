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


# -----------------------------
# Google Sheets Connection
# -----------------------------
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
    try:
        df = conn.read(worksheet=sheet_name, ttl=ttl_seconds)
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
        st.warning(f"Αδυναμία ανάγνωσης sheet '{sheet_name}': {exc}")
        return pd.DataFrame(columns=columns)


def safe_write(sheet_name, df):
    retries = 3
    for attempt in range(retries):
        try:
            conn.update(worksheet=sheet_name, data=df)
            # Ensure next rerun reads fresh data after a write.
            st.cache_data.clear()
            return True
        except Exception as exc:
            message = str(exc)
            is_rate_limited = "429" in message or "RATE_LIMIT_EXCEEDED" in message or "RESOURCE_EXHAUSTED" in message
            if is_rate_limited and attempt < retries - 1:
                wait_seconds = 1.5 * (attempt + 1)
                st.warning(f"Προσωρινός περιορισμός Google Sheets. Νέα προσπάθεια σε {wait_seconds:.1f}s...")
                time.sleep(wait_seconds)
                continue
            st.error(f"Σφάλμα εγγραφής στο '{sheet_name}': {exc}")
            return False
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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Σύνολο Εξόδων", format_currency(total_spent))
    col2.metric("Έξοδα (Expenses)", len(df_exp))
    col3.metric("Υλικά (Materials)", len(df_material))
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
                updated = append_row(df, new, EXPENSE_COLUMNS)
                if safe_write(SHEET_EXPENSES, updated):
                    st.success("Αποθηκεύτηκε")
                    st.rerun()

    edited = editable_sheet(df, EXPENSE_COLUMNS, "expenses_editor", num_cols=["Ποσό"])
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
        new_df, should_delete = delete_ui(edited, "Επέλεξε _id για διαγραφή", "del_mat")
        if should_delete and safe_write(SHEET_MATERIALS, new_df):
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
                new = {
                    "Περιγραφή": desc,
                    "Κεφάλαιο": principal,
                    "Επιτόκιο": rate,
                    "Μήνες": months,
                    "Μηνιαία_Δόση": installment,
                    "Έναρξη": str(date.today()),
                    "Κατάσταση": "Ενεργό",
                    "Σημειώσεις": "",
                }
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
                if end < start:
                    st.error("Η ημερομηνία λήξης δεν μπορεί να είναι πριν την έναρξη.")
                else:
                    new = {
                        "Εργασία": name,
                        "Χώρος": room,
                        "Κατάσταση": status,
                        "Ημερομηνία_Έναρξης": str(start),
                        "Ημερομηνία_Λήξης": str(end),
                        "Κόστος": 0,
                        "Προτεραιότητα": "Μεσαία",
                        "Ανάθεση": assignee,
                        "Σημειώσεις": "",
                    }
                    updated = append_row(df, new, TASK_COLUMNS)
                    if safe_write(SHEET_TASKS, updated):
                        st.success("Αποθηκεύτηκε")
                        st.rerun()

    timeline = prepare_timeline(df)
    if not timeline.empty:
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


def render_analytics(df_exp, df_material):
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
st.sidebar.markdown("### Πλοήγηση")

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

if menu == "🏠 Dashboard":
    df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
    df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
    df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
    df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
    render_dashboard(df_expenses, df_fees, df_materials, df_tasks)
elif menu == "💰 Έξοδα":
    df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
    render_expenses(df_expenses)
elif menu == "💼 Αμοιβές":
    df_fees = safe_read(SHEET_FEES, FEE_COLUMNS)
    render_fees(df_fees)
elif menu == "📦 Υλικά":
    df_materials = safe_read(SHEET_MATERIALS, MATERIAL_COLUMNS)
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
    render_analytics(df_expenses, df_materials)
elif menu == "🧮 Calculator":
    render_calculator()
