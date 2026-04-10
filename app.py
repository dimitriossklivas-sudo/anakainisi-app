import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Ρύθμιση σελίδας
st.set_page_config(page_title="Καταγραφή Εξόδων Ανακαίνισης", layout="centered")

st.title("🏠 Καταγραφή Εξόδων Ανακαίνισης")

# Σύνδεση με το Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# ΤΟ URL ΣΟΥ (Διορθωμένο για να αποφύγουμε το 404)
# Προσοχή: Χρησιμοποιούμε το link με το /gviz/tq για μέγιστη συμβατότητα
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GTsVsYbY2e5Gw1WN7OpBviq2599SeNI0N3OfFYE6lmo/edit#gid=0"

# Ανάγνωση δεδομένων
try:
    df = conn.read(spreadsheet=SHEET_URL, usecols=[0,1,2,3,4])
except Exception as e:
    st.error(f"Πρόβλημα σύνδεσης με το Sheet: {e}")
    df = pd.DataFrame()

# Φόρμα εισαγωγής στο πλάι
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
            
            # Ενοποίηση παλιών και νέων δεδομένων
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Ενημέρωση του Google Sheet
            try:
                conn.update(spreadsheet=SHEET_URL, data=updated_df)
                st.success("Η καταχώρηση αποθηκεύτηκε!")
                st.rerun()
            except Exception as e:
                st.error(f"Σφάλμα κατά την αποθήκευση: {e}")
        else:
            st.error("Παρακαλώ συμπληρώστε Περιγραφή και Ποσό.")

# Εμφάνιση στατιστικών και πίνακα
if not df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Συνολικά Έξοδα", f"{df['Ποσό (€)'].sum():.2f} €")
    with col2:
        mine = df[df['Πληρωμή από'] == 'Εγώ']['Ποσό (€)'].sum()
        st.metric("Πληρωμένα από εμένα", f"{mine:.2f} €")

    st.subheader("Λίστα Εξόδων")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Δεν υπάρχουν ακόμα καταχωρήσεις ή το αρχείο είναι άδειο.")
