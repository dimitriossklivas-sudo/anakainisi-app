import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Τοπική Καταγραφή Εξόδων", layout="centered")
st.title("🏠 Καταγραφή Εξόδων (Τοπική Αποθήκευση)")

# Όνομα τοπικού αρχείου
FILE_NAME = "expenses.csv"

# Φόρτωση δεδομένων από το αρχείο (αν υπάρχει)
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
else:
    # Δημιουργία κενού πίνακα αν δεν υπάρχει το αρχείο
    df = pd.DataFrame(columns=["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])

# Φόρμα στο sidebar
with st.sidebar:
    st.header("➕ Νέο Έξοδο")
    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Ημερομηνία")
        description = st.text_input("Περιγραφή")
        category = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Οικοδομικά", "Έπιπλα", "Άλλο"])
        amount = st.number_input("Ποσό (€)", min_value=0.0, format="%.2f")
        payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
        submitted = st.form_submit_button("Καταχώρηση")

    if submitted:
        if description and amount > 0:
            new_row = pd.DataFrame([{
                "Ημερομηνία": str(date),
                "Περιγραφή": description,
                "Κατηγορία": category,
                "Ποσό (€)": amount,
                "Πληρωμή από": payer
            }])
            # Προσθήκη και αποθήκευση
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(FILE_NAME, index=False)
            st.success("Αποθηκεύτηκε τοπικά!")
            st.rerun()

# Εμφάνιση αποτελεσμάτων
if not df.empty:
    st.metric("Συνολικά Έξοδα", f"{df['Ποσό (€)'].sum():.2f} €")
    st.dataframe(df, use_container_width=True)
    
    # Κουμπί για να κατεβάσεις το αρχείο στο κινητό/PC σου
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Κατέβασμα αρχείου Excel (CSV)", data=csv, file_name="my_expenses.csv", mime="text/csv")
else:
    st.info("Δεν υπάρχουν ακόμα καταχωρήσεις.")
