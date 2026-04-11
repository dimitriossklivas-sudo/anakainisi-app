import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v3.2", layout="wide", page_icon="🏠")

# --- ΣΥΝΑΡΤΗΣΕΙΣ ΜΝΗΜΗΣ (SESSION STATE) ---
def initialize_df(key, columns):
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=columns)
    return st.session_state[key]

# Αρχικοποίηση όλων των ενοτήτων βάσει του πλάνου σας
df_expenses = initialize_df('expenses_v3', ["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])
df_contacts = initialize_df('contacts_v3', ["Όνομα", "Ειδικότητα", "Τηλέφωνο", "Σημειώσεις"])
df_offers = initialize_df('offers_v3', ["Ημερομηνία", "Προμηθευτής", "Εργασία", "Ποσό (€)", "Κατάσταση"])
df_materials = initialize_df('materials_v3', ["Υλικό", "Ποσότητα", "Κατάσταση Παραλαβής"])

# --- LOGO & BRANDING ---
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 18px;'>Management Suite v3.2</p>", unsafe_allow_html=True)

# --- TABS (ΕΝΟΤΗΤΕΣ) ---
tabs = st.tabs(["📊 Έξοδα & Dashboard", "👷 Συνεργεία", "📦 Υλικά & Πρόοδος", "📄 Αρχείο & Exports", "💰 Προσφορές"])

# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ
with tabs[0]:
    with st.sidebar:
        st.header("➕ Νέα Δαπάνη")
        with st.form("exp_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή (π.χ. Αγορά τσιμέντων)")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Μπάνιο", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            e_payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
            if st.form_submit_button("✅ Καταχώρηση Εξόδου"):
                if e_desc and e_amt > 0:
                    new_entry = pd.DataFrame([{
                        "ID": datetime.now().strftime("%f"),
                        "Ημερομηνία": str(e_date),
                        "Περιγραφή": e_desc,
                        "Κατηγορία": e_cat,
                        "Ποσό (€)": e_amt,
                        "Πληρωμή από": e_payer
                    }])
                    st.session_state.expenses_v3 = pd.concat([st.session_state.expenses_v3, new_entry], ignore_index=True)
                    st.success("Η δαπάνη καταγράφηκε επιτυχώς!")
                    st.rerun()

    if not st.session_state.expenses_v3.empty:
        c1, c2, c3 = st.columns(3)
        total = st.session_state.expenses_v3['Ποσό (€)'].sum()
        c1.metric("Συνολικό Κόστος", f"{total:,.2f} €")
        c2.metric("Εγώ", f"{st.session_state.expenses_v3[st.session_state.expenses_v3['Πληρωμή από']=='Εγώ']['Ποσό (€)'].sum():,.2f} €")
        c3.metric("Πατέρας", f"{st.session_state.expenses_v3[st.session_state.expenses_v3['Πληρωμή από']=='Πατέρας']['Ποσό (€)'].sum():,.2f} €")
        
        st.divider()
        fig = px.pie(st.session_state.expenses_v3, values='Ποσό (€)', names='Κατηγορία', hole=0.4, title="Ανάλυση Εξόδων ανά Κατηγορία")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("👋 Καλώς ορίσατε. Ξεκινήστε προσθέτοντας μια δαπάνη από το μενού αριστερά.")

# 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων & Επαφών")
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
        with st.form("con_form", clear_on_submit=True):
            c_name = st.text_input("Όνομα / Εταιρεία")
            c_spec = st.text_input("Ειδικότητα (π.χ. Ηλεκτρολόγος)")
            c_phone = st.text_input("Τηλέφωνο Επικοινωνίας")
            c_notes = st.text_area("Σημειώσεις")
            if st.form_submit_button("Αποθήκευση"):
                if c_name:
                    new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone, "Σημειώσεις": c_notes}])
                    st.session_state.contacts_v3 = pd.concat([st.session_state.contacts_v3, new_c], ignore_index=True)
                    st.success("Η επαφή αποθηκεύτηκε!")
                    st.rerun()
    st.dataframe(st.session_state.contacts_v3, use_container_width=True)

# 3. ΕΝΟΤΗΤΑ ΥΛΙΚΩΝ & ΠΡΟΟΔΟΥ
with tabs[2]:
    st.subheader("📦 Παρακολούθηση Υλικών & Παραλαβών")
    with st.expander("➕ Καταγραφή Παραγγελίας Υλικού"):
        with st.form("mat_form", clear_on_submit=True):
            m_name = st.text_input("Είδος Υλικού")
            m_qty = st.text_input("Ποσότητα")
            m_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Παραγγέλθηκε", "Παραλήφθηκε"])
            if st.form_submit_button("Ενημέρωση Λίστας"):
                new_m = pd.DataFrame([{"Υλικό": m_name, "Ποσότητα": m_qty, "Κατάσταση Παραλαβής": m_status}])
                st.session_state.materials_v3 = pd.concat([st.session_state.materials_v3, new_m], ignore_index=True)
                st.rerun()
    st.dataframe(st.session_state.materials_v3, use_container_width=True)

# 4. ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ
with tabs[4]:
    st.subheader("💰 Σύγκριση Προσφορών")
    with st.expander("➕ Καταχώρηση Νέας Προσφοράς"):
        with st.form("off_form", clear_on_submit=True):
            o_vend = st.text_input("Τεχνικός / Κατάστημα")
            o_task = st.text_input("Εργασία / Υλικό")
            o_price = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            o_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Εγκρίθηκε", "Απορρίφθηκε"])
            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                new_o = pd.DataFrame([{"Ημερομηνία": str(datetime.now().date()), "Προμηθευτής": o_vend, "Εργασία": o_task, "Ποσό (€)": o_price, "Κατάσταση": o_status}])
                st.session_state.offers_v3 = pd.concat([st.session_state.offers_v3, new_o], ignore_index=True)
                st.rerun()
    st.dataframe(st.session_state.offers_v3, use_container_width=True)

# 5. ΑΡΧΕΙΟ & EXPORTS
with tabs[3]:
    st.subheader("📄 Εξαγωγή Δεδομένων για Ασφάλεια")
    st.warning("⚠️ Σημαντικό: Κατεβάζετε τα αρχεία σας τακτικά για να τα έχετε αποθηκευμένα τοπικά.")
    
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    
    # Export Εξόδων
    csv_exp = st.session_state.expenses_v3.to_csv(index=False).encode('utf-8-sig')
    col_ex1.download_button("📥 Λήψη Εξόδων (CSV)", csv_exp, "exoda_renovation.csv", "text/csv")
    
    # Export Συνεργείων
    csv_con = st.session_state.contacts_v3.to_csv(index=False).encode('utf-8-sig')
    col_ex2.download_button("📥 Λήψη Συνεργείων (CSV)", csv_con, "synergeia_renovation.csv", "text/csv")
    
    # Export Προσφορών
    csv_off = st.session_state.offers_v3.to_csv(index=False).encode('utf-8-sig')
    col_ex3.download_button("📥 Λήψη Προσφορών (CSV)", csv_off, "prosfores_renovation.csv", "text/csv")
