import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import os

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.6", layout="wide", page_icon="🏠")

# --- ΕΜΦΑΝΙΣΗ LOGO ---
logo_files = ["logo.png", "Logo.png", "logo.jpg"]
found_logo = False
for f in logo_files:
    if os.path.exists(f):
        st.image(f, width=200)
        found_logo = True
        break
if not found_logo:
    st.markdown("<h1 style='color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Συναρτήση για ασφαλή ανάγνωση
def safe_read(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0")
    except:
        return pd.DataFrame()

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
tabs = st.tabs(["📊 Έξοδα & Στατιστικά", "👷 Συνεργεία", "📦 Πρόοδος", "💰 Προσφορές", "🏦 Δανειοδότηση"])

# 1. ΕΞΟΔΑ & ΣΤΑΤΙΣΤΙΚΑ
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        # Συνολικά Ποσά (Metrics)
        m1, m2, m3 = st.columns(3)
        total = df_exp['Ποσό'].sum()
        ego = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        father = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        m1.metric("Συνολικά Έξοδα", f"{total:,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{ego:,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{father:,.2f} €")
        
        st.divider()
        
        # Διαγράμματα
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή ανά Εργασία", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            # Grouped bar chart για να βλέπεις ποιος πλήρωσε τι ανά κατηγορία
            fig_bar = px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής', 
                             title="Πληρωμές ανά Άτομο & Κατηγορία", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

    # Φόρμα Εισαγωγής (v5.1)
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("new_exp_v51", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                e_date = st.date_input("Ημερομηνία")
                e_cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
                e_type = st.radio("Είδος", ["Αμοιβή", "Υλικά"], horizontal=True)
            with f_col2:
                e_amt = st.number_input("Ποσό (€)", min_value=0.0)
                e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            e_desc = st.text_input("Περιγραφή")
            if st.form_submit_button("Αποθήκευση"):
                new_data = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, 
                                          "Ποσό": e_amt, "Πληρωτής": e_payer, "Είδος": e_type}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new_data], ignore_index=True))
                st.success("Το έξοδο αποθηκεύτηκε!")
                st.rerun()

# --- 2. ΣΥΝΕΡΓΕΙΑ ---
with tabs[1]:
    st.subheader("👷 Λίστα Επαφών")
    df_c = safe_read("Contacts")
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)
    else:
        st.warning("Δεν βρέθηκαν δεδομένα στο φύλλο 'Contacts'.")

# --- 3. ΠΡΟΟΔΟΣ (ΔΙΟΡΘΩΜΕΝΟ v5.3) ---
with tabs[2]:
    st.subheader("📦 Εξέλιξη & Οικονομική Εξόφληση")
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    
    if not df_p.empty:
        # Προετοιμασία δεδομένων εξόδων με ασφάλεια
        if not df_e.empty:
            df_e.columns = df_e.columns.str.strip()
            # Μετατροπή στηλών σε κείμενο για να μην χτυπάει το .str.strip()
            df_e['Κατηγορία'] = df_e['Κατηγορία'].astype(str).str.strip()
            if 'Είδος' in df_e.columns:
                df_e['Είδος'] = df_e['Είδος'].astype(str).str.strip()

        for i, r in df_p.iterrows():
            p_done = 0
            # Ασφαλής καθαρισμός ονόματος εργασίας
            task_name = str(r['Εργασία']).strip()
            
            if not df_e.empty and 'Είδος' in df_e.columns:
                # Φιλτράρισμα αμοιβών
                mask = (df_e['Κατηγορία'] == task_name) & \
                       (df_e['Είδος'].isin(["Αμοιβή", "Αμοιβές"]))
                p_done = df_e[mask]['Ποσό'].sum()
            
            total_agr = r['Συνολική Αμοιβή'] if 'Συνολική Αμοιβή' in r else 0
            perc = (p_done / total_agr) if total_agr > 0 else 0
            
            col_t, col_m = st.columns([3, 1])
            with col_t:
                st.write(f"### {task_name}")
                st.progress(min(perc, 1.0))
                st.write(f"💰 Πληρώθηκαν: **{p_done:,.2f} €** / Συμφωνία: {total_agr:,.2f} €")
            with col_m:
                st.metric("Εξόφληση", f"{perc*100:.1f}%")
                if st.button("✅ Ολοκληρώθηκε", key=f"p_btn_v53_{i}"):
                    df_p.at[i, 'Κατάσταση'] = "Ολοκληρώθηκε"
                    conn.update(worksheet="Progress", data=df_p)
                    st.rerun()
            st.divider()
    else:
        st.info("Προσθέστε εργασίες στο φύλλο 'Progress'.")

# --- 4. ΠΡΟΣΦΟΡΕΣ ---
with tabs[3]:
    st.subheader("💰 Διαχείριση Προσφορών")
    df_o = safe_read("Offers")
    if not df_o.empty:
        st.dataframe(df_o, use_container_width=True)
    else:
        st.warning("Δεν βρέθηκαν δεδομένα στο φύλλο 'Offers'.")

# 5. ΔΑΝΕΙΟΔΟΤΗΣΗ
with tabs[4]:
    st.subheader("🏦 Στοιχεία Δανείου")
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)
    st.subheader("🏦 Δανειοδότηση")
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)
