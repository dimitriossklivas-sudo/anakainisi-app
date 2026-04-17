import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.1", layout="wide")

# Logo
if os.path.exists("logo.png"):
    st.image("logo.png", width=200)
else:
    st.markdown("<h1 style='color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- TABS ---
tabs = st.tabs(["📊 Έξοδα", "👷 Συνεργεία", "📦 Υλικά & Πρόοδος", "💰 Προσφορές"])

# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ
with tabs[0]:
    st.subheader("📊 Διαχείριση Εξόδων")
    # Διάβασμα από το Tab "Expenses" του Google Sheet
    df_expenses = conn.read(worksheet="Expenses", ttl="0")
    
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Ημερομηνία")
                desc = st.text_input("Περιγραφή")
            with col2:
                amt = st.number_input("Ποσό (€)", min_value=0.0)
                payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            
            if st.form_submit_button("Αποθήκευση στο Google Sheet"):
                new_data = pd.DataFrame([{"Ημερομηνία": str(date), "Περιγραφή": desc, "Ποσό": amt, "Πληρωτής": payer}])
                updated_df = pd.concat([df_expenses, new_data], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
                st.success("Το έξοδο αποθηκεύτηκε!")
                st.rerun()
    
    st.dataframe(df_expenses, use_container_width=True)

# 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων")
    df_contacts = conn.read(worksheet="Contacts", ttl="0")
    
    with st.expander("➕ Προσθήκη Επαφής"):
        with st.form("contact_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα / Εταιρεία")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση Επαφής"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                updated_c = pd.concat([df_contacts, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.success("Η επαφή αποθηκεύτηκε!")
                st.rerun()
    st.dataframe(df_contacts, use_container_width=True)

# 3. ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ
with tabs[3]:
    st.subheader("💰 Σύγκριση Προσφορών")
    df_offers = conn.read(worksheet="Offers", ttl="0")
    
    with st.expander("➕ Νέα Προσφορά"):
        with st.form("offer_form", clear_on_submit=True):
            o_vendor = st.text_input("Προμηθευτής")
            o_amt = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            o_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Εγκρίθηκε", "Απορρίφθηκε"])
            if st.form_submit_button("Καταχώρηση"):
                new_o = pd.DataFrame([{"Προμηθευτής": o_vendor, "Ποσό": o_amt, "Κατάσταση": o_status}])
                updated_o = pd.concat([df_offers, new_o], ignore_index=True)
                conn.update(worksheet="Offers", data=updated_o)
                st.success("Η προσφορά καταγράφηκε!")
                st.rerun()
    st.dataframe(df_offers, use_container_width=True)
