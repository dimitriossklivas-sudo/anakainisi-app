import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.5", layout="wide")

# 2. ΣΥΝΔΕΣΗ
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"❌ Πρόβλημα στα Secrets: {e}")
    st.stop()

# Συνάρτηση για ασφαλές διάβασμα
def get_data(name, cols):
    try:
        return conn.read(worksheet=name, ttl="0")
    except:
        return pd.DataFrame(columns=cols)

# 3. ΕΜΦΑΝΙΣΗ
st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

tabs = st.tabs(["📊 Έξοδα", "👷 Συνεργεία", "💰 Προσφορές"])

# ΕΞΟΔΑ
with tabs[0]:
    df_exp = get_data("Expenses", ["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό", "Πληρωτής"])
    with st.sidebar.form("exp_form", clear_on_submit=True):
        st.header("Νέο Έξοδο")
        d = st.date_input("Ημερομηνία")
        desc = st.text_input("Περιγραφή")
        cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
        amt = st.number_input("Ποσό", min_value=0.0)
        p = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"])
        if st.form_submit_button("Αποθήκευση"):
            new_row = pd.DataFrame([{"Ημερομηνία": str(d), "Περιγραφή": desc, "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": p}])
            updated = pd.concat([df_exp, new_row], ignore_index=True)
            conn.update(worksheet="Expenses", data=updated)
            st.rerun()
    st.dataframe(df_exp, use_container_width=True)
    if not df_exp.empty:
        st.plotly_chart(px.pie(df_exp, values='Ποσό', names='Κατηγορία'))

# ΣΥΝΕΡΓΕΙΑ
with tabs[1]:
    df_con = get_data("Contacts", ["Όνομα", "Ειδικότητα", "Τηλέφωνο"])
    with st.expander("Προσθήκη Επαφής"):
        with st.form("con_form", clear_on_submit=True):
            n = st.text_input("Όνομα")
            s = st.text_input("Ειδικότητα")
            ph = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": n, "Ειδικότητα": s, "Τηλέφωνο": ph}])
                updated_c = pd.concat([df_con, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.rerun()
    st.dataframe(df_con, use_container_width=True)

# ΠΡΟΣΦΟΡΕΣ
with tabs[2]:
    df_off = get_data("Offers", ["Προμηθευτής", "Ποσό", "Κατάσταση"])
    st.dataframe(df_off, use_container_width=True)
