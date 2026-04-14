import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.8", layout="wide")

# Λειτουργία επιδιόρθωσης κλειδιού
def fix_secrets():
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        # Αντικατάσταση των \n με πραγματικές αλλαγές γραμμής
        raw_key = st.secrets.connections.gsheets.private_key
        fixed_key = raw_key.replace("\\n", "\n")
        return fixed_key
    return None

try:
    # Επιβολή του διορθωμένου κλειδιού
    fixed_key = fix_secrets()
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Διάβασμα δεδομένων
    df = conn.read(worksheet="Expenses", ttl="0")
    st.success("✅ Η σύνδεση πέτυχε!")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Σφάλμα: {e}")
    if "Expenses" in str(e):
        st.info("💡 Σχεδόν έτοιμο! Απλά ονομάστε την καρτέλα στο Google Sheet σας 'Expenses'.")
    else:
        st.info("💡 Βεβαιωθείτε ότι κάνατε Save τα Secrets.")
