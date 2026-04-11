import streamlit as st
import pandas as pd

st.set_page_config(page_title="Καταγραφή Εξόδων", layout="centered")
st.title("🏠 Καταγραφή Εξόδων Ανακαίνισης")

# Το ID του Sheet σου
SHEET_ID = "1GTsVsYbY2e5Gw1WN7OpBviq2599SeNI0N3OfFYE6lmo"
# Το πιο απλό link για απευθείας ανάγνωση
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

# Ανάγνωση δεδομένων
try:
    df = pd.read_csv(url)
    if not df.empty:
        st.success("Τα δεδομένα φορτώθηκαν επιτυχώς!")
        # Εμφάνιση στατιστικών αν υπάρχουν στήλες
        if len(df.columns) >= 4:
            total = pd.to_numeric(df.iloc[:, 3], errors='coerce').sum()
            st.metric("Συνολικά Έξοδα", f"{total:.2f} €")
        
        st.subheader("Λίστα Εξόδων")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Το αρχείο είναι άδειο. Ξεκινήστε τις καταχωρήσεις!")
except Exception as e:
    st.error("Η Google μπλοκάρει την αυτόματη ανάγνωση.")
    st.info("Μπορείτε να δείτε και να προσθέσετε έξοδα πατώντας το κουμπί παρακάτω.")

# Κουμπί για απευθείας πρόσβαση
st.divider()
st.subheader("📝 Διαχείριση Εξόδων")
st.link_button("Άνοιγμα Google Sheet για Καταχώρηση", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
