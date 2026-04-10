import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Ανακαίνιση", layout="wide")
st.title("🏡 Καταγραφή Εξόδων Ανακαίνισης")

conn = st.connection("gsheets", type=GSheetsConnection)
# Επικόλλησε το URL σου ανάμεσα στα εισαγωγικά παρακάτω:
url = "https://docs.google.com/spreadsheets/d/1GTsVsYbY2e5GW1WN70pBviq2599SenI0N3OFfYE6Imo/edit?gid=0#gid=0" 

conn = st.connection("gsheets", type=GSheetsConnection)

# Διάβασμα δεδομένων
try:
    data = conn.read(spreadsheet=url)
    data = data.dropna(how="all")
except:
    data = pd.DataFrame(columns=["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])

with st.sidebar:
    st.header("➕ Νέο Έξοδο")
    date = st.date_input("Ημερομηνία")
    desc = st.text_input("Περιγραφή")
    cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Ηλεκτρολογικά", "Υδραυλικά", "Δάπεδα", "Ξυλουργικά", "Λοιπά"])
    amount = st.number_input("Ποσό (€)", min_value=0.0, step=1.0)
    payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
    
    if st.button("Καταχώρηση"):
        new_row = pd.DataFrame([{
            "Ημερομηνία": str(date),
            "Περιγραφή": desc,
            "Κατηγορία": cat,
            "Ποσό (€)": amount,
            "Πληρωμή από": payer
        }])
        updated_df = pd.concat([data, new_row], ignore_index=True)
                 conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=updated_df)
        st.success("Αποθηκεύτηκε μόνιμα!")
        st.rerun()

# Εμφάνιση συνόλων
if not data.empty:
    total = data["Ποσό (€)"].sum()
    father = data[data["Πληρωμή από"] == "Πατέρας"]["Ποσό (€)"].sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Συνολικό Κόστος", f"{total:.2f} €")
    c2.metric("Πληρωμές Πατέρα", f"{father:.2f} €")
    
    st.markdown("---")
    st.dataframe(data, use_container_width=True)
else:
    st.info("Δεν υπάρχουν ακόμα καταχωρήσεις.")
