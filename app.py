import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import os

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.5", layout="wide")

# --- ΕΜΦΑΝΙΣΗ LOGO ---
logo_path = "logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=200)
else:
    st.markdown("<h1 style='color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Λειτουργία για ασφαλή ανάγνωση φύλλων
def safe_read(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0")
    except Exception:
        st.warning(f"⚠️ Η καρτέλα '{sheet_name}' δεν βρέθηκε στο Google Sheets. Παρακαλώ δημιουργήστε τη.")
        return pd.DataFrame()

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
tabs = st.tabs(["📊 Στατιστικά", "👷 Συνεργεία", "📦 Πρόοδος", "💰 Προσφορές", "🏦 Δανειοδότηση"])

# 1. ΣΤΑΤΙΣΤΙΚΑ & ΕΞΟΔΑ
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        st.subheader("📊 Οικονομική Εικόνα")
        st.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
        fig = px.pie(df_exp, values='Ποσό', names='Κατηγορία', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df_exp, use_container_width=True)

# 2. ΣΥΝΕΡΓΕΙΑ
with tabs[1]:
    st.subheader("👷 Λίστα Συνεργείων")
    df_con = safe_read("Contacts")
    if not df_con.empty:
        st.dataframe(df_con, use_container_width=True)
    with st.expander("➕ Προσθήκη Επαφής"):
        with st.form("c_form"):
            c_n = st.text_input("Όνομα")
            c_s = st.text_input("Ειδικότητα")
            c_p = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_n, "Ειδικότητα": c_s, "Τηλέφωνο": c_p}])
                updated_c = pd.concat([df_con, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.rerun()

# 3. ΠΡΟΟΔΟΣ
with tabs[2]:
    st.subheader("📦 Πρόοδος Εργασιών")
    df_prog = safe_read("Progress")
    if not df_prog.empty:
        for idx, row in df_prog.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.write(f"{'✅' if row['Κατάσταση'] == 'Ολοκληρώθηκε' else '⏳'} {row['Εργασία']}")
            if col2.button("Αλλαγή", key=f"p_{idx}"):
                df_prog.at[idx, 'Κατάσταση'] = "Ολοκληρώθηκε" if row['Κατάσταση'] != "Ολοκληρώθηκε" else "Εκκρεμεί"
                conn.update(worksheet="Progress", data=df_prog)
                st.rerun()

# 4. ΠΡΟΣΦΟΡΕΣ
with tabs[3]:
    st.subheader("💰 Διαχείριση Προσφορών")
    df_off = safe_read("Offers")
    if not df_off.empty:
        st.dataframe(df_off, use_container_width=True)
    with st.expander("➕ Νέα Προσφορά"):
        with st.form("o_form"):
            o_v = st.text_input("Προμηθευτής")
            o_p = st.number_input("Ποσό (€)", min_value=0.0)
            if st.form_submit_button("Καταχώρηση"):
                new_o = pd.DataFrame([{"Ημερομηνία": str(pd.Timestamp.now().date()), "Προμηθευτής": o_v, "Ποσό": o_p}])
                updated_o = pd.concat([df_off, new_o], ignore_index=True)
                conn.update(worksheet="Offers", data=updated_o)
                st.rerun()

# 5. ΔΑΝΕΙΟΔΟΤΗΣΗ
with tabs[4]:
    st.subheader("🏦 Δανειοδότηση")
    df_loan = safe_read("Loan")
    if not df_loan.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_loan['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_loan, use_container_width=True)
