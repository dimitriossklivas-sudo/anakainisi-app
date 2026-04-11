import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Ανακαίνιση - Στατιστικά", layout="wide") # wide για καλύτερη προβολή των stats
st.title("🏠 Διαχείριση & Στατιστικά Εξόδων")

FILE_NAME = "expenses.csv"

# Φόρτωση δεδομένων
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
    df["Ποσό (€)"] = pd.to_numeric(df["Ποσό (€)"], errors='coerce')
else:
    df = pd.DataFrame(columns=["Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από"])

# --- SIDEBAR: ΚΑΤΑΧΩΡΗΣΗ ---
with st.sidebar:
    st.header("➕ Νέα Καταχώρηση")
    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Ημερομηνία")
        description = st.text_input("Περιγραφή")
        category = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Οικοδομικά", "Έπιπλα", "Αλουμίνια", "Άλλο"])
        amount = st.number_input("Ποσό (€)", min_value=0.0, format="%.2f")
        payer = st.radio("Πληρωμή από", ["Εγώ", "Πατέρας"])
        submitted = st.form_submit_button("Αποθήκευση")

    if submitted and description and amount > 0:
        new_row = pd.DataFrame([{"Ημερομηνία": str(date), "Περιγραφή": description, "Κατηγορία": category, "Ποσό (€)": amount, "Πληρωμή από": payer}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("Η καταχώρηση έγινε!")
        st.rerun()

# --- ΚΥΡΙΟ ΜΕΡΟΣ: ΣΤΑΤΙΣΤΙΚΑ ---
if not df.empty:
    # 1. Γενικά Σύνολα σε στήλες
    col1, col2, col3 = st.columns(3)
    total_all = df["Ποσό (€)"].sum()
    total_me = df[df["Πληρωμή από"] == "Εγώ"]["Ποσό (€)"].sum()
    total_dad = df[df["Πληρωμή από"] == "Πατέρας"]["Ποσό (€)"].sum()

    col1.metric("Γενικό Σύνολο", f"{total_all:.2f} €")
    col2.metric("Εγώ", f"{total_me:.2f} €", delta_color="normal")
    col3.metric("Πατέρας", f"{total_dad:.2f} €", delta_color="normal")

    st.divider()

    # 2. Στατιστικά ανά Κατηγορία
    st.subheader("📊 Ανάλυση ανά Κατηγορία")
    cat_totals = df.groupby("Κατηγορία")["Ποσό (€)"].sum().sort_values(ascending=False)
    
    # Εμφάνιση γραφήματος
    st.bar_chart(cat_totals)

    # Πίνακας με τα ποσά ανά κατηγορία
    with st.expander("Δείτε τον πίνακα ανά κατηγορία"):
        st.table(cat_totals.apply(lambda x: f"{x:.2f} €"))

    st.divider()

    # 3. Αναλυτική Λίστα
    st.subheader("📋 Όλες οι Καταχωρήσεις")
    st.dataframe(df.sort_values(by="Ημερομηνία", ascending=False), use_container_width=True)
    
    # Κουμπί εξαγωγής
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Εξαγωγή σε CSV για Excel", data=csv, file_name="anakaιnisi_full_report.csv", mime="text/csv")

else:
    st.info("Περιμένω την πρώτη σας καταχώρηση για να εμφανίσω στατιστικά!")
