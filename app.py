import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Σκλίβας Δημήτριος | v3.0", layout="wide", page_icon="🏠")

# --- HEADER & LOGO ---
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    # Έλεγχος αν υπάρχει το αρχείο εικόνας
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown(f"<h1 style='text-align: center; color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; font-size: 20px; color: #6B7280; margin-top: -20px;'>Management Suite v3.0</p>", unsafe_allow_html=True)

# Δημιουργία φακέλων αν δεν υπάρχουν
for folder in ["receipts", "documents"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

EXPENSES_FILE = "expenses_v3.csv"
CONTACTS_FILE = "contacts_v3.csv"

# Συναρτήσεις Δεδομένων
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

df_expenses = load_data(EXPENSES_FILE, ["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από", "Αρχείο"])

# --- ΚΥΡΙΟ ΜΕΝΟΥ ---
tab_dash, tab_work, tab_materials, tab_docs = st.tabs([
    "📊 Κέντρο Ελέγχου", 
    "👷 Διαχείριση Συνεργείων", 
    "📦 Υλικά & Πρόοδος", 
    "📄 Αρχείο & Τιμολόγια"
])

# --- TAB: ΚΕΝΤΡΟ ΕΛΕΓΧΟΥ (DASHBOARD) ---
with tab_dash:
    st.sidebar.header("📥 Νέα Εγγραφή v3.0")
    with st.sidebar.form("main_form"):
        date = st.date_input("Ημερομηνία")
        desc = st.text_input("Περιγραφή Εργασίας / Προμηθευτής")
        cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Μπάνιο/Πλακάκια", "Κουζίνα", "Αλουμίνια", "Βάψιμο", "Άλλο"])
        amount = st.number_input("Ποσό (€)", min_value=0.0)
        payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
        doc = st.file_uploader("Ανέβασμα Απόδειξης/Σχεδίου", type=['jpg', 'png', 'pdf'])
        submit = st.form_submit_button("✅ Καταχώρηση")

    if submit and desc and amount > 0:
        file_path = "Δεν υπάρχει"
        if doc:
            file_path = os.path.join("receipts", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{doc.name}")
            with open(file_path, "wb") as f:
                f.write(doc.getbuffer())
        
        new_row = pd.DataFrame([{
            "ID": datetime.now().strftime("%f"),
            "Ημερομηνία": str(date),
            "Περιγραφή": desc,
            "Κατηγορία": cat,
            "Ποσό (€)": amount,
            "Πληρωμή από": payer,
            "Αρχείο": file_path
        }])
        df_expenses = pd.concat([df_expenses, new_row], ignore_index=True)
        df_expenses.to_csv(EXPENSES_FILE, index=False)
        st.sidebar.success("Η εγγραφή αποθηκεύτηκε!")
        st.rerun()

    # Metrics & Charts
    if not df_expenses.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Συνολικά Έξοδα", f"{df_expenses['Ποσό (€)'].sum():,.2f} €")
        c2.metric("Συμμετοχή Δημήτρη", f"{df_expenses[df_expenses['Πληρωμή από']=='Εγώ']['Ποσό (€)'].sum():,.2f} €")
        c3.metric("Συμμετοχή Πατέρα", f"{df_expenses[df_expenses['Πληρωμή από']=='Πατέρας']['Ποσό (€)'].sum():,.2f} €")
        
        st.divider()
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig1 = px.pie(df_expenses, values='Ποσό (€)', names='Κατηγορία', hole=0.4, title="Κόστος ανά Εργασία")
            st.plotly_chart(fig1, use_container_width=True)
        with col_chart2:
            fig2 = px.bar(df_expenses.groupby("Πληρωμή από")["Ποσό (€)"].sum().reset_index(), x='Πληρωμή από', y='Ποσό (€)', title="Σύγκριση Πληρωμών")
            st.plotly_chart(fig2, use_container_width=True)

# --- TAB: ΣΥΝΕΡΓΕΙΑ & ΥΛΙΚΑ (Βάσει του Word) ---
with tab_work:
    st.subheader("👷 Κατάλογος Επαγγελματιών")
    st.info("Εδώ μπορείτε να καταγράφετε τη λίστα συνεργατών και στοιχεία επικοινωνίας.")

with tab_materials:
    st.subheader("📦 Διαχείριση Προμηθειών")
    st.write("Παρακολούθηση αποθεμάτων και checklists εργασιών.")

with tab_docs:
    st.subheader("📑 Ψηφιακό Αρχείο Εγγράφων")
    if not df_expenses.empty:
        st.dataframe(df_expenses.sort_values("Ημερομηνία", ascending=False), use_container_width=True)
