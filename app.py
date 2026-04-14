import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.1", layout="wide", page_icon="🏠")

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
# Χρησιμοποιεί τα Secrets που έχετε ορίσει στο Streamlit Cloud
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("⚠️ Πρόβλημα σύνδεσης με τα Secrets. Ελέγξτε τη μορφή TOML.")
    st.stop()

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΔΕΔΟΜΕΝΩΝ ---
def load_sheet(sheet_name, cols):
    try:
        # ttl="0" για να διαβάζει πάντα τα τελευταία δεδομένα χωρίς cache
        return conn.read(worksheet=sheet_name, ttl="0")
    except Exception:
        # Αν το φύλλο είναι κενό, επιστρέφει ένα DataFrame με τις σωστές στήλες
        return pd.DataFrame(columns=cols)

# --- LOGO & HEADER ---
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280; font-size: 1.2rem;'>Renovation Cloud Manager v4.1</p>", unsafe_allow_html=True)

# --- ΚΥΡΙΩΣ ΜΕΝΟΥ (TABS) ---
tabs = st.tabs(["📊 Dashboard & Έξοδα", "👷 Συνεργεία", "📦 Υλικά & Πρόοδος", "💰 Προσφορές"])

# --- 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ ---
with tabs[0]:
    df_expenses = load_sheet("Expenses", ["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό", "Πληρωτής"])
    
    with st.sidebar:
        st.header("➕ Νέα Δαπάνη")
        with st.form("exp_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία", datetime.now())
            e_desc = st.text_input("Περιγραφή Εργασίας/Υλικού")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Μπάνιο", "Δάπεδα", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            e_payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
            
            if st.form_submit_button("✅ Αποθήκευση στο Cloud"):
                if e_desc and e_amt > 0:
                    new_data = pd.DataFrame([{
                        "Ημερομηνία": str(e_date),
                        "Περιγραφή": e_desc,
                        "Κατηγορία": e_cat,
                        "Ποσό": e_amt,
                        "Πληρωτής": e_payer
                    }])
                    updated_df = pd.concat([df_expenses, new_data], ignore_index=True)
                    conn.update(worksheet="Expenses", data=updated_df)
                    st.success("Η δαπάνη καταγράφηκε!")
                    st.rerun()
                else:
                    st.warning("Παρακαλώ συμπληρώστε Περιγραφή και Ποσό.")

    # Εμφάνιση Dashboard
    if not df_expenses.empty:
        c1, c2 = st.columns([1, 2])
        with c1:
            total = df_expenses["Ποσό"].sum()
            st.metric("Συνολικό Κόστος", f"{total:,.2f} €")
            # Γράφημα
            fig = px.pie(df_expenses, values='Ποσό', names='Κατηγορία', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(df_expenses.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("Δεν υπάρχουν ακόμα καταχωρημένα έξοδα.")

# --- 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ ---
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων")
    df_contacts = load_sheet("Contacts", ["Όνομα", "Ειδικότητα", "Τηλέφωνο", "Σημειώσεις"])
    
    with st.expander("➕ Προσθήκη Νέας Επαφής"):
        with st.form("con_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα / Εταιρεία")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                updated_c = pd.concat([df_contacts, new_c], ignore_index=True)
                conn.update(worksheet="Contacts", data=updated_c)
                st.rerun()
    st.table(df_contacts)

# --- 3. ΕΝΟΤΗΤΑ ΥΛΙΚΩΝ & ΠΡΟΟΔ
