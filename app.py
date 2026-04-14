import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.5", layout="wide", page_icon="🏠")

# --- 2. ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ Σφάλμα στα Secrets: {e}")
    st.stop()

# Συναρτήσεις για διαχείριση δεδομένων
def load_data(sheet_name, columns):
    try:
        return conn.read(worksheet=sheet_name, ttl="0")
    except:
        return pd.DataFrame(columns=columns)

# --- 3. LOGO & ΤΙΤΛΟΣ ---
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Renovation Cloud Manager v4.5</p>", unsafe_allow_html=True)

# --- 4. ΚΥΡΙΩΣ ΜΕΝΟΥ (TABS) ---
tabs = st.tabs(["📊 Έξοδα & Dashboard", "👷 Συνεργεία", "💰 Προσφορές"])

# --- ΤΑΒ 1: ΕΞΟΔΑ ---
with tabs[0]:
    df_exp = load_data("Expenses", ["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό", "Πληρωτής"])
    
    with st.sidebar:
        st.header("➕ Νέα Δαπάνη")
        with st.form("expense_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"])
            
            if st.form_submit_button("Αποθήκευση στο Cloud"):
                new_row = pd.DataFrame([{
                    "Ημερομηνία": str(e_date),
                    "Περιγραφή": e_desc,
                    "Κατηγορία": e_cat,
                    "Ποσό": e_amt,
                    "Πληρωτής": e_payer
                }])
                updated_df = pd.concat([df_exp, new_row], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
                st.success("Συγχρονίστηκε!")
                st.rerun()

    if not df_exp.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
            fig = px.pie(df_exp, values='Ποσό', names='Κατηγορία', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(df_exp, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν δεδομένα στο φύλλο 'Expenses'.")

# --- ΤΑΒ 2: ΣΥΝΕΡΓΕΙΑ ---
with tabs[1]:
    st.subheader("👷 Διαχείριση Επαφών")
    df_con = load_data("Contacts", ["Όνομα", "Ειδικότητα", "Τηλέφωνο"])
    
    with st.expander("Προσθήκη Επαφής"):
        with st.form("contact_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                updated_c = pd.concat([df_con, new_c], ignore_index=True)
                conn.update
