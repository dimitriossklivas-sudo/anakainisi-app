import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Σκλίβας Δημήτριος | v3.1", layout="wide", page_icon="🏠")

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΕΔΟΜΕΝΩΝ ---
def load_data(file_name, columns):
    if file_name not in st.session_state:
        if os.path.exists(file_name):
            st.session_state[file_name] = pd.read_csv(file_name)
        else:
            st.session_state[file_name] = pd.DataFrame(columns=columns)
    return st.session_state[file_name]

def save_and_refresh(df, file_name):
    st.session_state[file_name] = df
    df.to_csv(file_name, index=False)
    st.rerun()

# Αρχεία
EXPENSES_FILE = "expenses_v3.csv"
CONTACTS_FILE = "contacts_v3.csv"
OFFERS_FILE = "offers_v3.csv"

# Φόρτωση
df_expenses = load_data(EXPENSES_FILE, ["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από", "Αρχείο"])
df_contacts = load_data(CONTACTS_FILE, ["Όνομα", "Ειδικότητα", "Τηλέφωνο", "Σημειώσεις"])
df_offers = load_data(OFFERS_FILE, ["Ημερομηνία", "Προμηθευτής", "Εργασία", "Ποσό Προσφοράς (€)", "Κατάσταση"])

# --- LOGO & HEADER ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #6B7280; margin-top: -15px;'>Renovation Management Suite v3.1</p>", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["📊 Dashboard", "👷 Συνεργεία", "📦 Υλικά & Πρόοδος", "📄 Αρχείο & Τιμολόγια", "💰 Προσφορές"])

# 1. DASHBOARD & ΕΞΟΔΑ
with tabs[0]:
    st.sidebar.header("📥 Καταχώρηση Εξόδου")
    with st.sidebar.form("expense_form"):
        # ... (Ο γνωστός κώδικας καταχώρησης εξόδων)
        st.form_submit_button("Αποθήκευση")

# 2. ΔΙΑΧΕΙΡΙΣΗ ΣΥΝΕΡΓΕΙΩΝ (Source 7-12)
with tabs[1]:
    st.subheader("👷 Λίστα Επαγγελματιών")
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
        with st.form("contact_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα / Εταιρεία")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                save_and_refresh(pd.concat([df_contacts, new_c], ignore_index=True), CONTACTS_FILE)

    st.dataframe(df_contacts, use_container_width=True)

# 3. ΥΛΙΚΑ & ΠΡΟΟΔΟΣ (Source 13-22)
with tabs[2]:
    st.subheader("📦 Παρακολούθηση Υλικών & Checklists")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Checklist Εργασιών**")
        st.checkbox("Καθαιρέσεις / Γκρεμίσματα")
        st.checkbox("Ηλεκτρολογική Προεγκατάσταση")
        st.checkbox("Υδραυλική Προεγκατάσταση")
    with col2:
        st.write("**Σημειώσεις ανά Εργασία**")
        st.text_area("Γράψτε εκκρεμότητες εδώ...")

# 4. ΑΡΧΕΙΟ & ΤΙΜΟΛΟΓΙΑ (Source 28-32)
with tabs[3]:
    st.subheader("📄 Ψηφιακό Αρχείο")
    st.dataframe(df_expenses, use_container_width=True)
    # Κουμπί Export για ασφάλεια
    csv = df_expenses.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Λήψη Αρχείου Εξόδων (Excel/CSV)", csv, "expenses_backup.csv", "text/csv")

# 5. ΠΡΟΣΦΟΡΕΣ
