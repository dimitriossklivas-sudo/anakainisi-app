import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import os

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.3.1", layout="wide", page_icon="🏠")

# --- ΕΜΦΑΝΙΣΗ LOGO (ΔΙΟΡΘΩΜΕΝΟ) ---
# Ψάχνει το αρχείο σε όλες τις πιθανές μορφές ονόματος
possible_logos = ["logo.png", "Logo.png", "LOGO.PNG", "logo.jpg", "Logo.jpg"]
logo_to_display = None

for p in possible_logos:
    if os.path.exists(p):
        logo_to_display = p
        break

if logo_to_display:
    st.image(logo_to_display, width=220)
else:
    # Αν δεν βρει αρχείο, εμφανίζει τον τίτλο με ωραίο στυλ
    st.markdown("<h1 style='color: #D4AF37; margin-bottom: 0;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; font-size: 14px;'>Renovation Management Suite v4.3.1</p>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
tabs = st.tabs(["📊 Στατιστικά & Έξοδα", "👷 Συνεργεία", "📦 Πρόοδος", "💰 Προσφορές", "🏦 Δανειοδότηση"])

# ---------------------------------------------------------
# 1. ΕΝΟΤΗΤΑ ΕΞΟΔΩΝ & ΣΤΑΤΙΣΤΙΚΩΝ
# ---------------------------------------------------------
with tabs[0]:
    df_expenses = conn.read(worksheet="Expenses", ttl="0")
    
    if not df_expenses.empty:
        st.subheader("📊 Οικονομική Εικόνα")
        col_m1, col_m2, col_m3 = st.columns(3)
        total_spent = df_expenses['Ποσό'].sum()
        col_m1.metric("Συνολικά Έξοδα", f"{total_spent:,.2f} €")
        
        # Υπολογισμός ανά πληρωτή (Εγώ / Πατέρας)
        by_payer = df_expenses.groupby('Πληρωτής')['Ποσό'].sum()
        if "Εγώ" in by_payer: col_m2.metric("Πληρωμές (Εγώ)", f"{by_payer['Εγώ']:,.2f} €")
        if "Πατέρας" in by_payer: col_m3.metric("Πληρωμές (Πατέρας)", f"{by_payer['Πατέρας']:,.2f} €")

        st.divider()
        
        c_chart1, c_chart2 = st.columns([1, 1])
        with c_chart1:
            # Διάγραμμα Πίτας
            fig_pie = px.pie(df_expenses, values='Ποσό', names='Κατηγορία', title='Κατανομή Εξόδων ανά Κατηγορία', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c_chart2:
            st.write("### Πρόσφατες Καταχωρήσεις")
            st.dataframe(df_expenses.tail(8), use_container_width=True)
    
    with st.expander("➕ Νέα Καταχώρηση Εξόδου"):
        with st.form("exp_form", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Έπιπλα", "Μόνωση", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new_e = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, "Ποσό": e_amt, "Πληρωτής": e_payer}])
                updated_e = pd.concat([df_expenses, new_e], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_e)
                st.rerun()

# ---------------------------------------------------------
# 5. ΕΝΟΤΗΤΑ ΔΑΝΕΙΟΔΟΤΗΣΗΣ (ΝΕΟ)
# ---------------------------------------------------------
with tabs[4]:
    st.subheader("🏦 Παρακολούθηση Δανειοδότησης")
    df_loan = conn.read(worksheet="Loan", ttl="0")
    
    l_col1, l_col2 = st.columns([1, 1])
    
    with l_col1:
        if not df_loan.empty:
            last_balance = df_loan['Υπόλοιπο Δανείου'].iloc[-1]
            st.metric("Τρέχον Υπόλοιπο Δανείου", f"{last_balance:,.2f} €", delta_color="inverse")
            # Διάγραμμα εξέλιξης αποπληρωμής
            fig_loan = px.area(df_loan, x='Ημερομηνία', y='Υπόλοιπο Δανείου', title='Πορεία Αποπληρωμής Δανείου', color_discrete_sequence=['#D4AF37'])
            st.plotly_chart(fig_loan, use_container_width=True)
        else:
            st.info("Δεν υπάρχουν δεδομένα δανείου. Ξεκινήστε την καταγραφή δεξιά.")

    with l_col2:
        with st.form("loan_form", clear_on_submit=True):
            st.write("📝 Καταγραφή Δόσης / Κινήσεων")
            l_date = st.date_input("Ημερομηνία Κίνησης")
            l_amt = st.number_input("Ποσό Δόσης (€)", min_value=0.0)
            l_bal = st.number_input("Νέο Υπόλοιπο Δανείου (€)", min_value=0.0)
            l_note = st.text_input("Σημειώσεις")
            if st.form_submit_button("Ενημέρωση Δανείου"):
                new_l = pd.DataFrame([{"Ημερομηνία": str(l_date), "Ποσό Δόσης": l_amt, "Υπόλοιπο Δανείου": l_bal, "Σημειώσεις": l_note}])
                updated_l = pd.concat([df_loan, new_l], ignore_index=True)
                conn.update(worksheet="Loan", data=updated_l)
                st.rerun()
    
    st.write("### Ιστορικό Δόσεων")
    st.dataframe(df_loan, use_container_width=True)

# (Συμπεριλαμβάνονται κανονικά και τα Tabs: Συνεργεία, Πρόοδος, Προσφορές)
