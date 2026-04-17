import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import os

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.2", layout="wide", page_icon="🏠")

# --- ΕΜΦΑΝΙΣΗ LOGO / ΤΙΤΛΟΥ ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=250)
else:
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #6B7280;'>Renovation Management Suite v4.2</p>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
tabs = st.tabs(["📊 Έξοδα", "👷 Συνεργεία", "📦 Πρόοδος Εργασιών", "💰 Προσφορές"])

# ---------------------------------------------------------
# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ
# ---------------------------------------------------------
with tabs[0]:
    st.subheader("📊 Διαχείριση Εξόδων & Πληρωμών")
    df_expenses = conn.read(worksheet="Expenses", ttl="0")
    
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Ημερομηνία")
                desc = st.text_input("Περιγραφή (π.χ. Αγορά ειδών υγιεινής)")
                cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            with col2:
                amt = st.number_input("Ποσό (€)", min_value=0.0)
                payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"], horizontal=True)
            
            if st.form_submit_button("✅ Αποθήκευση"):
                if desc and amt > 0:
                    new_row = pd.DataFrame([{"Ημερομηνία": str(date), "Περιγραφή": desc, "Κατηγορία": cat, "Ποσό": amt, "Πληρωτής": payer}])
                    updated_df = pd.concat([df_expenses, new_row], ignore_index=True)
                    conn.update(worksheet="Expenses", data=updated_df)
                    st.success("Η δαπάνη καταγράφηκε!")
                    st.rerun()

    st.dataframe(df_expenses, use_container_width=True)
    if not df_expenses.empty:
        st.metric("Συνολικό Κόστος", f"{df_expenses['Ποσό'].sum():,.2f} €")

# ---------------------------------------------------------
# 2. ΕΝΟΤΗΤΑ ΣΥΝΕΡΓΕΙΩΝ
# ---------------------------------------------------------
with tabs[1]:
    st.subheader("👷 Λίστα Επαγγελματιών & Επαφών")
    df_contacts = conn.read(worksheet="Contacts", ttl="0")
    
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
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
    st.table(df_contacts)

# ---------------------------------------------------------
# 3. ΕΝΟΤΗΤΑ ΠΡΟΟΔΟΥ ΕΡΓΑΣΙΩΝ
# ---------------------------------------------------------
with tabs[2]:
    st.subheader("📦 Παρακολούθηση Εργασιών")
    df_progress = conn.read(worksheet="Progress", ttl="0")
    
    with st.expander("➕ Προσθήκη Νέας Εργασίας"):
        with st.form("task_form", clear_on_submit=True):
            t_name = st.text_input("Εργασία (π.χ. Τοποθέτηση πλακιδίων)")
            if st.form_submit_button("Προσθήκη"):
                if t_name:
                    new_t = pd.DataFrame([{"Εργασία": t_name, "Κατάσταση": "Εκκρεμεί"}])
                    updated_p = pd.concat([df_progress, new_t], ignore_index=True)
                    conn.update(worksheet="Progress", data=updated_p)
                    st.rerun()

    st.divider()
    if not df_progress.empty:
        for index, row in df_progress.iterrows():
            c1, c2 = st.columns([4, 1])
            is_done = row['Κατάσταση'] == "Ολοκληρώθηκε"
            c1.write(f"{'✅' if is_done else '⏳'} {row['Εργασία']}")
            if c2.button("Αλλαγή", key=f"p_{index}"):
                df_progress.at[index, 'Κατάσταση'] = "Ολοκληρώθηκε" if not is_done else "Εκκρεμεί"
                conn.update(worksheet="Progress", data=df_progress)
                st.rerun()
        
        # Μπάρα Προόδου
        done_count = len(df_progress[df_progress['Κατάσταση'] == "Ολοκληρώθηκε"])
        total_count = len(df_progress)
        st.write(f"**Συνολική Πρόοδος: {done_count}/{total_count}**")
        st.progress(done_count / total_count)

# 4. ΕΝΟΤΗΤΑ ΠΡΟΣΦΟΡΩΝ (Διορθωμένη)
with tabs[3]:
    st.subheader("💰 Διαχείριση & Σύγκριση Προσφορών")
    df_offers = conn.read(worksheet="Offers", ttl="0")
    
    with st.expander("➕ Καταχώρηση Νέας Προσφοράς"):
        with st.form("offer_form", clear_on_submit=True):
            o_vendor = st.text_input("Προμηθευτής / Τεχνικός")
            o_task = st.text_input("Αφορά την εργασία...")
            o_price = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            
            # Πεδίο για φωτογραφία από το κινητό
            uploaded_file = st.file_uploader("📷 Τραβήξτε Φωτογραφία Προσφοράς", type=['png', 'jpg', 'jpeg', 'pdf'])
            
            o_status = st.selectbox("Κατάσταση", ["Σε αναμονή", "Εγκρίθηκε", "Απορρίφθηκε"])
            
            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                # Εδώ διορθώθηκε το όνομα από new_row σε new_o
                new_o = pd.DataFrame([{
                    "Ημερομηνία": str(pd.Timestamp.now().date()), 
                    "Προμηθευτής": o_vendor, 
                    "Εργασία": o_task, 
                    "Ποσό": o_price, 
                    "Κατάσταση": o_status,
                    "Αρχείο": "Ναι" if uploaded_file else "Όχι"
                }])
                updated_o = pd.concat([df_offers, new_o], ignore_index=True)
                conn.update(worksheet="Offers", data=updated_o)
                st.success("Η προσφορά αποθηκεύτηκε στο Google Sheets!")
                st.rerun()

    st.dataframe(df_offers, use_container_width=True)
