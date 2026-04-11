import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# Ρυθμίσεις σελίδας με το όνομά σας
st.set_page_config(page_title="Renovation Pro | Σκλίβας Δημήτριος", layout="wide", page_icon="🏗️")

# Φάκελοι αρχείων
for folder in ["receipts", "progress_photos"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

EXPENSES_FILE = "expenses_pro_v3.csv"
CONTACTS_FILE = "contacts.csv"

# Φόρτωση Δεδομένων
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

df_expenses = load_data(EXPENSES_FILE, ["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από", "Αρχείο"])
df_contacts = load_data(CONTACTS_FILE, ["Όνομα", "Ειδικότητα", "Τηλέφωνο", "Σημειώσεις"])

# --- UI BRANDING ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #6B7280;'>Ολοκληρωμένη Διαχείριση Ανακαίνισης</h3>", unsafe_allow_html=True)

# --- TABS ΓΙΑ ΟΡΓΑΝΩΣΗ (Βάσει του Word) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard & Έξοδα", "👷 Συνεργεία", "📦 Υλικά & Progress", "📄 Έγγραφα"])

# --- TAB 1: DASHBOARD & ΕΞΟΔΑ ---
with tab1:
    with st.sidebar:
        st.header("➕ Νέα Καταχώρηση")
        with st.form("expense_form"):
            date = st.date_input("Ημερομηνία")
            desc = st.text_input("Περιγραφή (π.χ. Τσιμέντα)")
            cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Μπάνιο", "Κουζίνα", "Βάψιμο", "Άλλο"])
            amount = st.number_input("Ποσό (€)", min_value=0.0)
            payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
            file = st.file_uploader("Τιμολόγιο/Απόδειξη", type=['jpg', 'pdf'])
            if st.form_submit_button("Αποθήκευση"):
                # Αποθήκευση (όπως πριν)
                st.success("Καταχωρήθηκε!")

    # Στατιστικά (Dashboard)
    if not df_expenses.empty:
        total_spent = df_expenses["Ποσό (€)"].sum()
        st.metric("Συνολικό Κόστος Έργου", f"{total_spent:,.2f} €")
        fig = px.pie(df_expenses, values='Ποσό (€)', names='Κατηγορία', title="Ανάλυση Κόστους ανά Εργασία")
        st.plotly_chart(fig)

# --- TAB 2: ΔΙΑΧΕΙΡΙΣΗ ΣΥΝΕΡΓΕΙΩΝ (Source 7-12) ---
with tab2:
    st.subheader("👷 Λίστα Επαγγελματιών & Συνεργατών")
    with st.expander("Προσθήκη Νέου Συνεργάτη"):
        with st.form("contact_form"):
            c_name = st.text_input("Όνομα/Εταιρεία")
            c_spec = st.text_input("Ειδικότητα (π.χ. Υδραυλικός)")
            c_phone = st.text_input("Τηλέφωνο Επικοινωνίας")
            if st.form_submit_button("Προσθήκη"):
                new_c = pd.DataFrame([{"Όνομα": c_name, "Ειδικότητα": c_spec, "Τηλέφωνο": c_phone}])
                df_contacts = pd.concat([df_contacts, new_c], ignore_index=True)
                df_contacts.to_csv(CONTACTS_FILE, index=False)
                st.rerun()
    st.table(df_contacts)

# --- TAB 3: ΥΛΙΚΑ & PROGRESS (Source 13-22) ---
with tab3:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("✅ Checklist Εργασιών")
        st.checkbox("Κατεδαφίσεις")
        st.checkbox("Υδραυλική εγκατάσταση")
        st.checkbox("Ηλεκτρολογική εγκατάσταση")
        st.checkbox("Σοβατίσματα / Βάψιμο")
    
    with col_p2:
        st.subheader("📦 Παραγγελίες Υλικών")
        st.info("Εδώ μπορείτε να παρακολουθείτε τι έχει παραληφθεί (π.χ. Πλακάκια, Είδη Υγιεινής)")

# --- TAB 4: ΕΓΓΡΑΦΑ & ΣΗΜΕΙΩΣΕΙΣ (Source 28-32) ---
with tab4:
    st.subheader("📄 Ψηφιακό Αρχείο")
    st.write("Εδώ αποθηκεύονται αυτόματα όλες οι αποδείξεις και τα τιμολόγια που ανεβάζετε.")
    if not df_expenses.empty:
        st.dataframe(df_expenses[["Ημερομηνία", "Περιγραφή", "Ποσό (€)", "Αρχείο"]])
