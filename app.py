import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Pro Renovation Manager", layout="wide", page_icon="🏗️")

# Δημιουργία φακέλων αν δεν υπάρχουν
if not os.path.exists("receipts"):
    os.makedirs("receipts")

FILE_NAME = "expenses_pro.csv"

# Φόρτωση δεδομένων
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    df = pd.DataFrame(columns=["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από", "Αρχείο"])

# --- SIDEBAR: ΕΙΣΑΓΩΓΗ ---
st.sidebar.header("🏗️ Διαχείριση Έργου")
with st.sidebar.form("pro_form", clear_on_submit=True):
    date = st.date_input("Ημερομηνία", datetime.now())
    desc = st.text_input("Τίτλος Εξόδου / Προμηθευτής")
    cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Μπάνιο/Πλακάκια", "Κουζίνα", "Αλουμίνια", "Βάψιμο", "Φωτισμός", "Έπιπλα", "Άλλο"])
    amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
    payer = st.radio("Ποιος πλήρωσε;", ["Εγώ", "Πατέρας"])
    uploaded_file = st.file_uploader("📷 Ανέβασμα Απόδειξης (Image/PDF)", type=['png', 'jpg', 'jpeg', 'pdf'])
    
    submit = st.form_submit_button("✅ Οριστική Καταχώρηση")

if submit and desc and amount > 0:
    file_path = "Δεν υπάρχει"
    if uploaded_file is not None:
        file_path = os.path.join("receipts", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    new_data = pd.DataFrame([{
        "ID": datetime.now().strftime("%H%M%S"),
        "Ημερομηνία": str(date),
        "Περιγραφή": desc,
        "Κατηγορία": cat,
        "Ποσό (€)": amount,
        "Πληρωμή από": payer,
        "Αρχείο": file_path
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    st.sidebar.success("Η καταχώρηση ολοκληρώθηκε!")
    st.rerun()

# --- ΚΥΡΙΟ ΠΑΝΕΛ ---
st.title("🏗️ Pro Renovation Manager")

if not df.empty:
    # KPI Metrics
    c1, c2, c3, c4 = st.columns(4)
    total = df["Ποσό (€)"].sum()
    c1.metric("Συνολικό Κόστος", f"{total:,.2f} €")
    c2.metric("Δικά σου", f"{df[df['Πληρωμή από']=='Εγώ']['Ποσό (€)'].sum():,.2f} €")
    c3.metric("Πατέρα", f"{df[df['Πληρωμή από']=='Πατέρας']['Ποσό (€)'].sum():,.2f} €")
    c4.metric("Εγγραφές", len(df))

    st.divider()

    # Φίλτρα
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search = st.text_input("🔍 Αναζήτηση (π.χ. Τσιμέντα)")
    with col_f2:
        filter_cat = st.multiselect("📂 Φιλτράρισμα Κατηγορίας", options=df["Κατηγορία"].unique())

    # Εφαρμογή φίλτρων
    view_df = df.copy()
    if search:
        view_df = view_df[view_df['Περιγραφή'].str.contains(search, case=False)]
    if filter_cat:
        view_df = view_df[view_df['Κατηγορία'].isin(filter_cat)]

    # Πίνακας Δεδομένων
    st.subheader("📑 Αναλυτική Κατάσταση")
    st.dataframe(view_df.sort_values("Ημερομηνία", ascending=False), use_container_width=True)

    # Προβολή Αποδείξεων
    st.divider()
    st.subheader("🖼️ Αρχείο Αποδείξεων")
    files_with_docs = df[df["Αρχείο"] != "Δεν υπάρχει"]
    if not files_with_docs.empty:
        selected_receipt = st.selectbox("Επιλέξτε έξοδο για προβολή απόδειξης:", files_with_docs["Περιγραφή"] + " (" + files_with_docs["Ημερομηνία"] + ")")
        actual_path = files_with_docs[files_with_docs["Περιγραφή"] + " (" + files_with_docs["Ημερομηνία"] + ")" == selected_receipt]["Αρχείο"].values[0]
        
        if actual_path.endswith('.pdf'):
            st.info(f"Το αρχείο είναι PDF. Μπορείτε να το βρείτε στον φάκελο receipts.")
        else:
            st.image(actual_path, caption=selected_receipt, use_container_width=True)
    else:
        st.write("Δεν έχουν ανέβει ακόμα αποδείξεις.")

else:
    st.info("Ξεκινήστε την πρώτη σας καταχώρηση από το μενού αριστερά!")
