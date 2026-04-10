import streamlit as st
import pandas as pd

# Τίτλος Εφαρμογής
st.set_page_config(page_title="Renovation Tracker", layout="wide")
st.title("🏡 Καταγραφή Εξόδων Ανακαίνισης")

# Αρχικοποίηση δεδομένων (Session State)
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=[
        "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"
    ])

# --- ΦΟΡΜΑ ΚΑΤΑΧΩΡΗΣΗΣ ---
with st.sidebar:
    st.header("➕ Νέο Έξοδο")
    date = st.date_input("Ημερομηνία")
    desc = st.text_input("Περιγραφή")
    cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Ηλεκτρολογικά", "Υδραυλικά", "Δάπεδα", "Ξυλουργικά", "Λοιπά"])
    amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
    payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
    
    if st.button("Καταχώρηση"):
        new_row = pd.DataFrame([[date, desc, cat, amount, payer]], 
                               columns=st.session_state.expenses.columns)
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
        st.success("Το έξοδο καταγράφηκε!")

# --- DASHBOARD & ΣΤΑΤΙΣΤΙΚΑ ---
col1, col2, col3 = st.columns(3)

total_spent = st.session_state.expenses["Ποσό (€)"].sum()
father_spent = st.session_state.expenses[st.session_state.expenses["Πληρωμή από"] == "Πατέρας"]["Ποσό (€)"].sum()
my_spent = total_spent - father_spent

col1.metric("Συνολικά Έξοδα", f"{total_spent:.2f} €")
col2.metric("Πληρωμές Πατέρα", f"{father_spent:.2f} €")
col3.metric("Δικές μου Πληρωμές", f"{my_spent:.2f} €")

st.divider()

# --- ΠΙΝΑΚΑΣ ΔΕΔΟΜΕΝΩΝ ---
st.subheader("📋 Λίστα Εξόδων")
st.dataframe(st.session_state.expenses, use_container_width=True)

# Δυνατότητα εξαγωγής σε Excel
if not st.session_state.expenses.empty:
    csv = st.session_state.expenses.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Λήψη σε Excel (CSV)", csv, "renovation_costs.csv", "text/csv")
