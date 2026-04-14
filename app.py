import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Βασικές Ρυθμίσεις
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.6", layout="wide")

# 2. Σύνδεση με το Google Sheets
try:
    # Καθαρισμός του Private Key από τυχόν περίεργους χαρακτήρες
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Δοκιμή ανάγνωσης (Αν δεν υπάρχει το φύλλο, θα βγάλει WorksheetNotFound)
        df = conn.read(worksheet="Expenses", ttl="0")
        st.success("✅ Η σύνδεση με το Cloud πέτυχε!")
except Exception as e:
    st.error(f"❌ Σφάλμα: {e}")
    st.info("Σιγουρευτείτε ότι το Google Sheet έχει φύλλο με όνομα 'Expenses'.")
    st.stop()

# 3. Εμφάνιση Δεδομένων
st.title("📊 Διαχείριση Ανακαίνισης")
st.dataframe(df, use_container_width=True)
