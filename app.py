import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.3", layout="wide", page_icon="🏠")

# --- ΑΣΦΑΛΗΣ ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ Πρόβλημα στα Secrets: {e}")
    st.stop()

def get_data(sheet, columns):
    try:
        return conn.read(worksheet=sheet, ttl="0")
    except:
        return pd.DataFrame(columns=columns)

# --- HEADER ---
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Renovation Manager v4.3 (Cloud Sync)</p>", unsafe_allow_html=True)

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["📊 Έξοδα", "👷 Συνεργεία", "📦 Υλικά", "💰 Προσφορές"])

# --- 📊 ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ ---
with t1:
    df_exp = get_data("Expenses", ["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό", "Πληρωτής"])
    with st.sidebar:
        st.header("➕ Νέα Καταχώρηση")
        with st.form("f1", clear_on_submit=True):
            d = st.date_input("Ημερομηνία")
            desc = st.text_input("Περιγραφή")
            cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            amt = st.number_input("Ποσό (€)", min_value=0.0)
            p = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"])
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"Ημερομηνία": str(d), "Περιγραφή": desc, "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": p}])
                updated = pd.concat([df_exp, new_row], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated)
                st.success("Συγχρονίστηκε!")
                st.rerun()
    
    if not df_exp.empty:
        st.metric("Σύνολο", f"{df_exp['Ποσό'].sum():,.2f} €")
        st.dataframe(df_exp, use_container_width=True)
        st.plotly_chart(px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή Εξόδων"))

# --- 👷 ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ ---
with t2:
    st.subheader("Στοιχεία Επικοινωνίας")
    df_con = get_data("Contacts", ["Όνομα", "Ειδικότητα", "Τηλέφωνο"])
    with st.expander("Προσθήκη Επαφής"):
        with st.form("f2", clear_on_submit=True):
            n = st.text_input("Όνομα")
            s = st.text_input("Ειδικότητα")
            ph = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση Επαφής"):
                new_c = pd.DataFrame([{"Όνομα": n, "Ειδικότητα": s, "Τηλέφωνο": ph}])
                updated_c = pd.concat([df_con, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.rerun()
    st.table(df_con)

# --- 📦 ΕΝΟΤΗΤΑ ΥΛΙΚΩΝ ---
with t3:
    st.subheader("Παραγγελίες Υλικών")
    df_mat = get_data("Materials", ["Υλικό", "Κατάσταση"])
    # Παρόμοια φόρμα καταχώρησης...
    st.dataframe(df_mat, use_container_width=True)

# --- 💰 ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ ---
with t4:
    st.subheader("Σύγκριση Προσφορών")
    df_off = get_data("Offers", ["Προμηθευτής", "Ποσό", "Κατάσταση"])
    # Παρόμοια φόρμα καταχώρησης...
    st.dataframe(df_off, use_container_width=True)
