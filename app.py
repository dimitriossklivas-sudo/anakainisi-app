import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.7", layout="wide")

# Προσπάθεια σύνδεσης με αυτόματη διόρθωση κλειδιού
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Expenses", ttl="0")
    st.success("✅ Η σύνδεση με το Google Sheets πέτυχε!")
    
    # Εμφάνιση Δεδομένων
    st.title("📊 Διαχείριση Ανακαίνισης")
    st.dataframe(df, use_container_width=True)
    
except Exception as e:
    st.error(f"❌ Σφάλμα Σύνδεσης: {e}")
    if "WorksheetNotFound" in str(e):
        st.info("💡 Λύση: Ονομάστε την καρτέλα στο Google Sheet σας 'Expenses'.")
    else:
        st.info("💡 Λύση: Αντιγράψτε ξανά τα Secrets με τα τριπλά εισαγωγικά.")
