import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Σκλίβας Δημήτριος | v3.2", layout="wide", page_icon="🏠")

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΜΝΗΜΗΣ (SESSION STATE) ---
# Αυτές οι συναρτήσεις διασφαλίζουν ότι οι καταχωρήσεις ΔΕΝ χάνονται κατά τη χρήση
def initialize_df(key, columns):
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=columns)
    return st.session_state[key]

# Αρχικοποίηση όλων των ενοτήτων βάσει του πλάνου σας
df_expenses = initialize_df('expenses_v3', ["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])
df_contacts = initialize_df('contacts_v3', ["Όνομα", "Ειδικότητα", "Τηλέφωνο", "Σημειώσεις"])
df_offers = initialize_df('offers_v3', ["Ημερομηνία", "Προμηθευτής", "Εργασία", "Ποσό (€)", "Κατάσταση"])
df_materials = initialize_df('materials_v3', ["Υλικό", "Ποσότητα", "Κατάσταση Παραλαβής"])

# --- LOGO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Management Suite v3.2</p>", unsafe_allow_html=True)

# --- TABS ---
tabs = st.tabs(["📊 Έξοδα & Dashboard", "👷 Συνεργεία", "📦 Υλικά & Πρόοδος", "📄 Αρχείο", "💰 Προσφορές"])

# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ
with tabs[0]:
    with st.sidebar:
        st.header("➕ Νέα Δαπάνη")
        with st.form("exp_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
            if st.form_submit_button("Καταχώρηση"):
                new_data = pd.DataFrame([{"ID": datetime.now().strftime("%f"), "Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, "Ποσό (€)": e_amt, "Πληρωμή από": e_payer}])
                st.session_state.expenses_v3 = pd.concat([st.session_state.expenses_v3, new_data], ignore_index=True)
                st.success("Το έξοδο καταγράφηκε!")
                st.rerun()

    if not st.session_state.expenses_v3.empty:
        st.metric("Συνολικό Κόστος", f"{st.session_state.expenses_v3['Ποσό (€)'].sum():,.2f} €")
        fig = px.pie(st.session_state.expenses_v3, values='Ποσό (€)', names='Κατηγορία', hole=0.4)
        st.plotly_chart(fig)

# 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων")
    with st.expander("Προσθήκη Επαφής"):
        with st.form("con_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα")
            c_spec = st.text_input("Ειδικότητα")
            c_phone = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                st.session_state.contacts_v3 = pd.concat([st.session_state.contacts_v3, new_c], ignore_index=True)
                st.rerun()
    st.table(st.session_state.contacts_v3)

# 3. ΕΝΟΤΗΤΑ ΥΛΙΚΩΝ & ΠΡΟΟΔΟΥ
with tabs[2]:
    st.subheader("📦 Παρακολούθηση Υλικών")
    with st.form("mat_form", clear_on_submit=True):
        m_name = st.text_input("Υλικό (π.χ. Πλακάκια)")
        m_qty = st.text_input("Ποσότητα")
        m_status = st.selectbox("Κατάσταση", ["Παραγγέλθηκε", "Παραλήφθηκε"])
        if st.form_submit_button("Ενημέρωση"):
            new_m = pd.DataFrame([{"Υλικό": m_name, "Ποσότητα": m_qty, "Κατάσταση Παραλαβής": m_status}])
            st.session_state.materials_v3 = pd.concat([st.session_state.materials_v3, new_m], ignore_index=True)
            st.rerun()
    st.dataframe(st.session_state.materials_v3, use_container_width=True)

# 4. ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ
with tabs[4]:
    st.subheader("💰 Σύγκριση Προσφορών")
    with st.form("off_form", clear_on_submit=True):
        o_vend = st.text_input("Τεχνικός/Εταιρεία")
        o_price = st.number_input("Ποσό (€)", min_value=0.0)
        o_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Εγκρίθηκε"])
        if st.form_submit_button("Καταχώρηση Προσφοράς"):
            new_o = pd.DataFrame([{"Ημερομηνία": str(datetime.now().date()), "Προμηθευτής": o_vend, "Ποσό (€)": o_price, "Κατάσταση": o_status}])
            st.session_state.offers_v3 = pd.concat([st.session_state.offers_v3, new_o], ignore_index=True)
            st.rerun()
    st.dataframe(st.session_state.offers_v3, use_container_width=True)

# 5. ΑΡΧΕΙΟ (EXPORTS)
with tabs[3]:
    st.subheader("📄 Εξαγωγή Δεδομένων")
    st.info("Επειδή το GitHub είναι 'κλειδωμένο', χρησιμοποιήστε τα παρακάτω κουμπιά για να σώζετε τα δεδομένα σας στον υπολογιστή σας.")
    
    for key, name in [('expenses_v3', 'exoda.csv'), ('contacts_v3', 'synergeia.csv'), ('offers_v3', 'prosfores.csv')]:
        csv = st.session_state[key].to_csv(index=False).encode('utf-8-sig')
        st.download_button(f"📥 Λήψη {name}", csv, name, "text/csv")
