import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.0", layout="wide", page_icon="🏠")

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
# Η σύνδεση αυτή χρησιμοποιεί τα Secrets που ρύθμισες
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ΣΥΝΑΡΤΗΣΗ ΓΙΑ ΑΣΦΑΛΕΣ ΔΙΑΒΑΣΜΑ ---
def fetch_data(sheet_name, columns):
    try:
        data = conn.read(worksheet=sheet_name, ttl="0") # ttl=0 για να ανανεώνεται αμέσως
        return data
    except:
        return pd.DataFrame(columns=columns)

# --- LOGO ---
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Cloud Management Suite v4.0</p>", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["📊 Έξοδα", "👷 Συνεργεία", "📦 Υλικά", "💰 Προσφορές"])

# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ
with tabs[0]:
    df_expenses = fetch_data("Expenses", ["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό", "Πληρωτής"])
    
    with st.sidebar:
        st.header("➕ Νέα Δαπάνη")
        with st.form("exp_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
            
            if st.form_submit_button("✅ Αποθήκευση στο Cloud"):
                new_row = pd.DataFrame([{
                    "Ημερομηνία": str(e_date),
                    "Περιγραφή": e_desc,
                    "Κατηγορία": e_cat,
                    "Ποσό": e_amt,
                    "Πληρωτής": e_payer
                }])
                updated_df = pd.concat([df_expenses, new_row], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
                st.success("Συγχρονίστηκε με το Google Sheets!")
                st.rerun()

    if not df_expenses.empty:
        st.metric("Συνολικά Έξοδα", f"{df_expenses['Ποσό'].sum():,.2f} €")
        st.dataframe(df_expenses, use_container_width=True)
        fig = px.pie(df_expenses, values='Ποσό', names='Κατηγορία', title="Ανάλυση Εξόδων")
        st.plotly_chart(fig)

# 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων")
    df_contacts = fetch_data("Contacts", ["Όνομα", "Ειδικότητα", "Τηλέφωνο"])
    
    with st.expander("Προσθήκη Επαφής"):
        with st.form("con_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση Επαφής"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                updated_c = pd.concat([df_contacts, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.rerun()
    st.dataframe(df_contacts, use_container_width=True)

# 3. ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ
with tabs[3]:
    st.subheader("💰 Σύγκριση Προσφορών")
    df_offers = fetch_data("Offers", ["Ημερομηνία", "Προμηθευτής", "Εργασία", "Ποσό", "Κατάσταση"])
    
    with st.expander("Καταχώρηση Προσφοράς"):
        with st.form("off_form", clear_on_submit=True):
            o_vend = st.text_input("Προμηθευτής")
            o_task = st.text_input("Εργασία")
            o_price = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            o_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Εγκρίθηκε"])
            if st.form_submit_button("Σύγκριση & Αποθήκευση"):
                new_o = pd.DataFrame([{"Ημερομηνία": str(datetime.now().date()), "Προμηθευτής": o_vend, "Εργασία": o_task, "Ποσό": o_price, "Κατάσταση": o_status}])
                updated_o = pd.concat([df_offers, new_o], ignore_index=True)
                conn.update(worksheet="Offers", data=updated_o)
                st.rerun()
    st.dataframe(df_offers, use_container_width=True)
