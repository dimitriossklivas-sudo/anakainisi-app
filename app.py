import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Ρύθμιση σελίδας
st.set_page_config(page_title="Καταγραφή Εξόδων Ανακαίνισης", layout="centered")

st.title("🏠 Καταγραφή Εξόδων Ανακαίνισης")

# Σύνδεση με το Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Το URL του Sheet σου σε μορφή εξαγωγής CSV (πιο σταθερό για το 404)
SHEET_ID = "1GTsVsYbY2e5Gw1WN7OpBviq2599SeNI0N3OfFYE6lmo"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Ανάγνωση δεδομένων
try:
    # Δοκιμάζουμε να διαβάσουμε απευθείας το CSV
    df = pd.read_csv(SHEET_URL)
except Exception as e:
    st.error(f"Πρόβλημα σύνδεσης: {e}")
    df = pd.DataFrame(columns=["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])

# Φόρμα εισαγωγής
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
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
            # Ενημέρωση (Χρησιμοποιούμε το αρχικό URL για το update)
            ORIGINAL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"
            try:
                conn.update(spreadsheet=ORIGINAL_URL, data=updated_df)
                st.success("Η καταχώρηση αποθηκεύτηκε!")
                st.rerun()
            except Exception as e:
                st.error("Σφάλμα εγγραφής. Βεβαιωθείτε ότι το Sheet είναι 'Συντάκτης' για όλους.")
        else:
            st.error("Συμπληρώστε τα πεδία.")

# Εμφάνιση δεδομένων
if not df.empty:
    st.metric("Συνολικά Έξοδα", f"{df['Ποσό (€)'].sum():.2f} €")
    st.subheader("Λίστα Εξόδων")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Δεν υπάρχουν ακόμα καταχωρήσεις.")
