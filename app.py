import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fbf6ee; }
    .card-container { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e6e6e6; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .card-title { color: #4c3826; font-weight: bold; border-bottom: 2px solid #dec18e; margin-bottom: 10px; text-transform: uppercase; }
    .label { font-size: 0.9rem; font-weight: bold; margin-top: 10px; color: #5a4330; }
    .value { float: right; font-weight: bold; color: #4c3826; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTION & DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_sheets():
    sheets = {
        "Expenses": ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"],
        "Materials": ["_id", "Κατηγορία", "Υλικό", "Ποσότητα", "Μονάδα", "Τιμή_Μονάδας", "Σύνολο", "Προμηθευτής", "Κατάσταση"],
        "Contacts": ["_id", "Όνομα", "Ρόλος", "Τηλέφωνο", "Email"],
        "Loan": ["_id", "Περιγραφή", "Κεφάλαιο", "Δόση", "Κατάσταση"],
        "Progress": ["_id", "Εργασία", "Χώρος", "Κατάσταση", "Ημερομηνία_Έναρξης", "Ημερομηνία_Λήξης"],
        "Gallery": ["_id", "Χώρος", "Τίτλος", "Image_Data"]
    }
    data = {}
    for s_name, cols in sheets.items():
        try:
            df = conn.read(worksheet=s_name, ttl="5m")
            data[s_name] = df.dropna(how="all") if df is not None else pd.DataFrame(columns=cols)
        except:
            data[s_name] = pd.DataFrame(columns=cols)
    return data

dataframes = load_all_sheets()

# --- 3. RENDER FUNCTIONS ---

def render_dashboard(df_exp):
    st.title("🏗️ Dashboard Ανακαίνισης")
    if df_exp.empty:
        st.info("Δεν υπάρχουν δεδομένα εξόδων.")
        return

    # Λογική για τις κάρτες βάσει του σχεδίου σου
    for cat in ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια"]:
        budget = 2400.0 if cat == "Υδραυλικά" else 1500.0 # Παράδειγμα budget
        subset = df_exp[df_exp['Κατηγορία'] == cat]
        paid = pd.to_numeric(subset['Ποσό'], errors='coerce').sum()
        me = pd.to_numeric(subset[subset['Πληρωτής'] == 'Εγώ']['Ποσό'], errors='coerce').sum()
        fat = pd.to_numeric(subset[subset['Πληρωτής'] == 'Πατέρας']['Ποσό'], errors='coerce').sum()

        st.markdown(f'<div class="card-container"><div class="card-title">ΚΑΡΤΕΛΑ {cat}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="label">ΣΥΝΟΛΟ ΚΑΛΥΜΜΕΝΟ <span class="value">{paid:,.2f}€ / {budget:,.2f}€</span></div>', unsafe_allow_html=True)
        st.progress(min(paid/budget, 1.0) if budget > 0 else 0)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="label">ΕΓΩ <span class="value">{me:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(me/(budget/2), 1.0) if budget > 0 else 0)
        with c2:
            st.markdown(f'<div class="label">ΠΑΤΕΡΑΣ <span class="value">{fat:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(fat/(budget/2), 1.0) if budget > 0 else 0)
        st.markdown('</div>', unsafe_allow_html=True)

def render_expenses(df):
    st.title("💰 Διαχείριση Εξόδων")
    with st.form("exp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Ημερομηνία", datetime.now())
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Άλλο"])
        with c2:
            amt = st.number_input("Ποσό (€)", min_value=0.0)
            payer = st.selectbox("Πληρωτής", ["Εγώ", "Πατέρας", "Κοινό"])
        
        if st.form_submit_button("✅ Αποθήκευση"):
            new_row = {"_id": str(uuid.uuid4())[:8], "Ημερομηνία": d.strftime("%Y-%m-%d"), 
                       "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": payer}
            updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(worksheet="Expenses", data=updated)
            st.success("Καταχωρήθηκε!")
            st.rerun()
    st.dataframe(df, use_container_width=True)

def render_materials(df):
    st.title("📦 Υλικά")
    st.dataframe(df, use_container_width=True)

def render_timeline(df):
    st.title("🗓️ Timeline")
    if not df.empty and "Ημερομηνία_Έναρξης" in df.columns:
        fig = px.timeline(df, x_start="Ημερομηνία_Έναρξης", x_end="Ημερομηνία_Λήξης", y="Εργασία", color="Κατάσταση")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εργασίες στο Progress.")

def render_gallery(df):
    st.title("📸 Gallery")
    if df.empty: st.info("Η Gallery είναι άδεια.")
    else:
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                if row["Image_Data"]:
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", caption=row["Τίτλος"])

# --- 4. MAIN NAVIGATION ---
def main():
    with st.sidebar:
        st.header("Μενού")
        choice = st.radio("Επιλογή:", ["🏠 Dashboard", "💰 Έξοδα", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📸 Gallery"])
        if st.button("🔄 Ανανέωση"):
            st.cache_data.clear()
            st.rerun()

    if choice == "🏠 Dashboard": render_dashboard(dataframes["Expenses"])
    elif choice == "💰 Έξοδα": render_expenses(dataframes["Expenses"])
    elif choice == "📦 Υλικά": render_materials(dataframes["Materials"])
    elif choice == "📞 Επαφές": st.dataframe(dataframes["Contacts"])
    elif choice == "🏦 Δάνειο": st.dataframe(dataframes["Loan"])
    elif choice == "🗓️ Timeline": render_timeline(dataframes["Progress"])
    elif choice == "📸 Gallery": render_gallery(dataframes["Gallery"])

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fbf6ee; }
    .card-container { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e6e6e6; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .card-title { color: #4c3826; font-weight: bold; border-bottom: 2px solid #dec18e; margin-bottom: 10px; text-transform: uppercase; }
    .label { font-size: 0.9rem; font-weight: bold; margin-top: 10px; color: #5a4330; }
    .value { float: right; font-weight: bold; color: #4c3826; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTION & DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_sheets():
    sheets = {
        "Expenses": ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"],
        "Materials": ["_id", "Κατηγορία", "Υλικό", "Ποσότητα", "Μονάδα", "Τιμή_Μονάδας", "Σύνολο", "Προμηθευτής", "Κατάσταση"],
        "Contacts": ["_id", "Όνομα", "Ρόλος", "Τηλέφωνο", "Email"],
        "Loan": ["_id", "Περιγραφή", "Κεφάλαιο", "Δόση", "Κατάσταση"],
        "Progress": ["_id", "Εργασία", "Χώρος", "Κατάσταση", "Ημερομηνία_Έναρξης", "Ημερομηνία_Λήξης"],
        "Gallery": ["_id", "Χώρος", "Τίτλος", "Image_Data"]
    }
    data = {}
    for s_name, cols in sheets.items():
        try:
            df = conn.read(worksheet=s_name, ttl="5m")
            data[s_name] = df.dropna(how="all") if df is not None else pd.DataFrame(columns=cols)
        except:
            data[s_name] = pd.DataFrame(columns=cols)
    return data

dataframes = load_all_sheets()

# --- 3. RENDER FUNCTIONS ---

def render_dashboard(df_exp):
    st.title("🏗️ Dashboard Ανακαίνισης")
    if df_exp.empty:
        st.info("Δεν υπάρχουν δεδομένα εξόδων.")
        return

    # Λογική για τις κάρτες βάσει του σχεδίου σου
    for cat in ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια"]:
        budget = 2400.0 if cat == "Υδραυλικά" else 1500.0 # Παράδειγμα budget
        subset = df_exp[df_exp['Κατηγορία'] == cat]
        paid = pd.to_numeric(subset['Ποσό'], errors='coerce').sum()
        me = pd.to_numeric(subset[subset['Πληρωτής'] == 'Εγώ']['Ποσό'], errors='coerce').sum()
        fat = pd.to_numeric(subset[subset['Πληρωτής'] == 'Πατέρας']['Ποσό'], errors='coerce').sum()

        st.markdown(f'<div class="card-container"><div class="card-title">ΚΑΡΤΕΛΑ {cat}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="label">ΣΥΝΟΛΟ ΚΑΛΥΜΜΕΝΟ <span class="value">{paid:,.2f}€ / {budget:,.2f}€</span></div>', unsafe_allow_html=True)
        st.progress(min(paid/budget, 1.0) if budget > 0 else 0)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="label">ΕΓΩ <span class="value">{me:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(me/(budget/2), 1.0) if budget > 0 else 0)
        with c2:
            st.markdown(f'<div class="label">ΠΑΤΕΡΑΣ <span class="value">{fat:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(fat/(budget/2), 1.0) if budget > 0 else 0)
        st.markdown('</div>', unsafe_allow_html=True)

def render_expenses(df):
    st.title("💰 Διαχείριση Εξόδων")
    with st.form("exp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Ημερομηνία", datetime.now())
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Άλλο"])
        with c2:
            amt = st.number_input("Ποσό (€)", min_value=0.0)
            payer = st.selectbox("Πληρωτής", ["Εγώ", "Πατέρας", "Κοινό"])
        
        if st.form_submit_button("✅ Αποθήκευση"):
            new_row = {"_id": str(uuid.uuid4())[:8], "Ημερομηνία": d.strftime("%Y-%m-%d"), 
                       "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": payer}
            updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(worksheet="Expenses", data=updated)
            st.success("Καταχωρήθηκε!")
            st.rerun()
    st.dataframe(df, use_container_width=True)

def render_materials(df):
    st.title("📦 Υλικά")
    st.dataframe(df, use_container_width=True)

def render_timeline(df):
    st.title("🗓️ Timeline")
    if not df.empty and "Ημερομηνία_Έναρξης" in df.columns:
        fig = px.timeline(df, x_start="Ημερομηνία_Έναρξης", x_end="Ημερομηνία_Λήξης", y="Εργασία", color="Κατάσταση")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εργασίες στο Progress.")

def render_gallery(df):
    st.title("📸 Gallery")
    if df.empty: st.info("Η Gallery είναι άδεια.")
    else:
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                if row["Image_Data"]:
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", caption=row["Τίτλος"])

# --- 4. MAIN NAVIGATION ---
def main():
    with st.sidebar:
        st.header("Μενού")
        choice = st.radio("Επιλογή:", ["🏠 Dashboard", "💰 Έξοδα", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📸 Gallery"])
        if st.button("🔄 Ανανέωση"):
            st.cache_data.clear()
            st.rerun()

    if choice == "🏠 Dashboard": render_dashboard(dataframes["Expenses"])
    elif choice == "💰 Έξοδα": render_expenses(dataframes["Expenses"])
    elif choice == "📦 Υλικά": render_materials(dataframes["Materials"])
    elif choice == "📞 Επαφές": st.dataframe(dataframes["Contacts"])
    elif choice == "🏦 Δάνειο": st.dataframe(dataframes["Loan"])
    elif choice == "🗓️ Timeline": render_timeline(dataframes["Progress"])
    elif choice == "📸 Gallery": render_gallery(dataframes["Gallery"])

if __name__ == "__main__":
    main()
import streamlit as st
import pandas as pd
import uuid
import base64
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIG & STYLE ---
st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fbf6ee; }
    .card-container { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e6e6e6; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .card-title { color: #4c3826; font-weight: bold; border-bottom: 2px solid #dec18e; margin-bottom: 10px; text-transform: uppercase; }
    .label { font-size: 0.9rem; font-weight: bold; margin-top: 10px; color: #5a4330; }
    .value { float: right; font-weight: bold; color: #4c3826; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECTION & DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_sheets():
    sheets = {
        "Expenses": ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"],
        "Materials": ["_id", "Κατηγορία", "Υλικό", "Ποσότητα", "Μονάδα", "Τιμή_Μονάδας", "Σύνολο", "Προμηθευτής", "Κατάσταση"],
        "Contacts": ["_id", "Όνομα", "Ρόλος", "Τηλέφωνο", "Email"],
        "Loan": ["_id", "Περιγραφή", "Κεφάλαιο", "Δόση", "Κατάσταση"],
        "Progress": ["_id", "Εργασία", "Χώρος", "Κατάσταση", "Ημερομηνία_Έναρξης", "Ημερομηνία_Λήξης"],
        "Gallery": ["_id", "Χώρος", "Τίτλος", "Image_Data"]
    }
    data = {}
    for s_name, cols in sheets.items():
        try:
            df = conn.read(worksheet=s_name, ttl="5m")
            data[s_name] = df.dropna(how="all") if df is not None else pd.DataFrame(columns=cols)
        except:
            data[s_name] = pd.DataFrame(columns=cols)
    return data

dataframes = load_all_sheets()

# --- 3. RENDER FUNCTIONS ---

def render_dashboard(df_exp):
    st.title("🏗️ Dashboard Ανακαίνισης")
    if df_exp.empty:
        st.info("Δεν υπάρχουν δεδομένα εξόδων.")
        return

    # Λογική για τις κάρτες βάσει του σχεδίου σου
    for cat in ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια"]:
        budget = 2400.0 if cat == "Υδραυλικά" else 1500.0 # Παράδειγμα budget
        subset = df_exp[df_exp['Κατηγορία'] == cat]
        paid = pd.to_numeric(subset['Ποσό'], errors='coerce').sum()
        me = pd.to_numeric(subset[subset['Πληρωτής'] == 'Εγώ']['Ποσό'], errors='coerce').sum()
        fat = pd.to_numeric(subset[subset['Πληρωτής'] == 'Πατέρας']['Ποσό'], errors='coerce').sum()

        st.markdown(f'<div class="card-container"><div class="card-title">ΚΑΡΤΕΛΑ {cat}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="label">ΣΥΝΟΛΟ ΚΑΛΥΜΜΕΝΟ <span class="value">{paid:,.2f}€ / {budget:,.2f}€</span></div>', unsafe_allow_html=True)
        st.progress(min(paid/budget, 1.0) if budget > 0 else 0)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="label">ΕΓΩ <span class="value">{me:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(me/(budget/2), 1.0) if budget > 0 else 0)
        with c2:
            st.markdown(f'<div class="label">ΠΑΤΕΡΑΣ <span class="value">{fat:,.2f}€</span></div>', unsafe_allow_html=True)
            st.progress(min(fat/(budget/2), 1.0) if budget > 0 else 0)
        st.markdown('</div>', unsafe_allow_html=True)

def render_expenses(df):
    st.title("💰 Διαχείριση Εξόδων")
    with st.form("exp_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            d = st.date_input("Ημερομηνία", datetime.now())
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Άλλο"])
        with c2:
            amt = st.number_input("Ποσό (€)", min_value=0.0)
            payer = st.selectbox("Πληρωτής", ["Εγώ", "Πατέρας", "Κοινό"])
        
        if st.form_submit_button("✅ Αποθήκευση"):
            new_row = {"_id": str(uuid.uuid4())[:8], "Ημερομηνία": d.strftime("%Y-%m-%d"), 
                       "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": payer}
            updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            conn.update(worksheet="Expenses", data=updated)
            st.success("Καταχωρήθηκε!")
            st.rerun()
    st.dataframe(df, use_container_width=True)

def render_materials(df):
    st.title("📦 Υλικά")
    st.dataframe(df, use_container_width=True)

def render_timeline(df):
    st.title("🗓️ Timeline")
    if not df.empty and "Ημερομηνία_Έναρξης" in df.columns:
        fig = px.timeline(df, x_start="Ημερομηνία_Έναρξης", x_end="Ημερομηνία_Λήξης", y="Εργασία", color="Κατάσταση")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν εργασίες στο Progress.")

def render_gallery(df):
    st.title("📸 Gallery")
    if df.empty: st.info("Η Gallery είναι άδεια.")
    else:
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                if row["Image_Data"]:
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", caption=row["Τίτλος"])

# --- 4. MAIN NAVIGATION ---
def main():
    with st.sidebar:
        st.header("Μενού")
        choice = st.radio("Επιλογή:", ["🏠 Dashboard", "💰 Έξοδα", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📸 Gallery"])
        if st.button("🔄 Ανανέωση"):
            st.cache_data.clear()
            st.rerun()

    if choice == "🏠 Dashboard": render_dashboard(dataframes["Expenses"])
    elif choice == "💰 Έξοδα": render_expenses(dataframes["Expenses"])
    elif choice == "📦 Υλικά": render_materials(dataframes["Materials"])
    elif choice == "📞 Επαφές": st.dataframe(dataframes["Contacts"])
    elif choice == "🏦 Δάνειο": st.dataframe(dataframes["Loan"])
    elif choice == "🗓️ Timeline": render_timeline(dataframes["Progress"])
    elif choice == "📸 Gallery": render_gallery(dataframes["Gallery"])

if __name__ == "__main__":
    main()
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


# ✅ FIX Bug 3: Το st.caption τώρα είναι ΜΕΣΑ στο loop αντί στο τέλος του αρχείου
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
