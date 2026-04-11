import streamlit as st
import pandas as pd

st.set_page_config(page_title="Καταγραφή Εξόδων", layout="centered")
st.title("🏠 Καταγραφή Εξόδων Ανακαίνισης")

# Το ID του Sheet σου
SHEET_ID = "1GTsVsYbY2e5Gw1WN7OpBviq2599SeNI0N3OfFYE6lmo"
# Link για διάβασμα (CSV format)
READ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# Link για άνοιγμα του Sheet από τον χρήστη
FORM_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# Ανάγνωση δεδομένων
try:
    df = pd.read_csv(READ_URL)
    st.success("Τα δεδομένα φορτώθηκαν!")
except Exception as e:
    st.error("Δεν ήταν δυνατή η ανάγνωση του Sheet.")
    df = pd.DataFrame()

# Εμφάνιση πίνακα
if not df.empty:
    st.metric("Συνολικά Έξοδα", f"{df.iloc[:, 3].sum():.2f} €") # Υποθέτοντας ότι το ποσό είναι στην 4η στήλη
    st.subheader("Λίστα Εξόδων")
    st.dataframe(df, use_container_width=True)
else:
    st.info("Το αρχείο φαίνεται άδειο.")

# Επειδή η εγγραφή μέσω κώδικα μπλοκάρεται από την Google χωρίς κλειδιά ασφαλείας,
# η πιο σίγουρη λύση για να μην παιδεύεσαι άλλο είναι ένα κουμπί:
st.divider()
st.subheader("📝 Προσθήκη Νέου Εξόδου")
st.write("Λόγω περιορισμών ασφαλείας της Google, παρακαλώ καταχωρήστε το έξοδο απευθείας στο Sheet:")
st.link_button("Άνοιγμα Google Sheet", FORM_URL)
