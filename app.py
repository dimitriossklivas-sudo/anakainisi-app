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
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
            fig = px.pie(df_exp, values='Ποσό', names='Κατηγορία', hole=0.4, title="Ανάλυση Εξόδων")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(df_exp.tail(10), use_container_width=True)
    
    with st.expander("➕ Προσθήκη Νέου Εξόδου"):
        with st.form("new_exp_form", clear_on_submit=True):
            d = st.date_input("Ημερομηνία")
            de = st.text_input("Περιγραφή")
            c = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Άλλο"])
            a = st.number_input("Ποσό (€)", min_value=0.0)
            p = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"Ημερομηνία": str(d), "Περιγραφή": de, "Κατηγορία": c, "Ποσό": a, "Πληρωτής": p}])
                updated_df = pd.concat([df_exp, new_row], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
                st.success("Το έξοδο καταγράφηκε!")
                st.rerun()

# 2. ΣΥΝΕΡΓΕΙΑ
with tabs[1]:
    st.subheader("👷 Λίστα Επαφών")
    df_con = safe_read("Contacts")
    if not df_con.empty: st.table(df_con)
    with st.expander("➕ Νέο Συνεργείο"):
        with st.form("c_form"):
            n = st.text_input("Όνομα")
            s = st.text_input("Ειδικότητα")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": n, "Ειδικότητα": s}])
                conn.update(worksheet="Contacts", data=pd.concat([df_con, new_c], ignore_index=True))
                st.rerun()

# ---------------------------------------------------------
# 3. ΕΝΟΤΗΤΑ ΠΡΟΟΔΟΥ (Με Μπάρες & Ποσοστά)
# ---------------------------------------------------------
with tabs[2]:
    st.subheader("📦 Παρακολούθηση & Εξέλιξη Εργασιών")
    df_p = safe_read("Progress")
    
    if not df_p.empty:
        # Συνολική Πρόοδος Έργου
        total_tasks = len(df_p)
        done_tasks = len(df_p[df_p['Κατάσταση'] == "Ολοκληρώθηκε"])
        total_progress = done_tasks / total_tasks if total_tasks > 0 else 0
        
        st.write(f"### Συνολική Ολοκλήρωση: {total_progress*100:.0f}%")
        st.progress(total_progress)
        st.divider()

        # Λίστα Εργασιών με Μπάρες
        for i, r in df_p.iterrows():
            col_text, col_btn = st.columns([3, 1])
            
            with col_text:
                st.write(f"**{r['Εργασία']}**")
                # Μπάρα για την συγκεκριμένη εργασία
                status_val = 1.0 if r['Κατάσταση'] == "Ολοκληρώθηκε" else 0.0
                st.progress(status_val)
            
            with col_btn:
                # Κουμπί εναλλαγής κατάστασης
                label = "✅ Τέλος" if r['Κατάσταση'] != "Ολοκληρώθηκε" else "🔄 Επαναφορά"
                if st.button(label, key=f"btn_p_{i}"):
                    new_status = "Ολοκληρώθηκε" if r['Κατάσταση'] != "Ολοκληρώθηκε" else "Εκκρεμεί"
                    df_p.at[i, 'Κατάσταση'] = new_status
                    conn.update(worksheet="Progress", data=df_p)
                    st.rerun()
            st.write("") # Κενό ανάμεσα στις εργασίες
    else:
        st.info("Η λίστα εργασιών είναι κενή στο Google Sheets (Φύλλο: Progress).")

    with st.expander("➕ Προσθήκη Νέας Εγκεκριμένης Εργασίας"):
        with st.form("add_task_form", clear_on_submit=True):
            new_t = st.text_input("Περιγραφή Εργασίας")
            if st.form_submit_button("Προσθήκη στη Λίστα"):
                if new_t:
                    new_row = pd.DataFrame([{"Εργασία": new_t, "Κατάσταση": "Εκκρεμεί"}])
                    updated_p = pd.concat([df_p, new_row], ignore_index=True)
                    conn.update(worksheet="Progress", data=updated_p)
                    st.success("Η εργασία προστέθηκε!")
                    st.rerun()

# 4. ΠΡΟΣΦΟΡΕΣ
with tabs[3]:
    st.subheader("💰 Προσφορές")
    df_o = safe_read("Offers")
    if not df_o.empty: st.dataframe(df_o, use_container_width=True)
    with st.expander("➕ Νέα Προσφορά"):
        with st.form("o_form"):
            v = st.text_input("Προμηθευτής")
            pr = st.number_input("Ποσό", min_value=0.0)
            if st.form_submit_button("Καταχώρηση"):
                new_o = pd.DataFrame([{"Ημερομηνία": str(pd.Timestamp.now().date()), "Προμηθευτής": v, "Ποσό": pr}])
                conn.update(worksheet="Offers", data=pd.concat([df_o, new_o], ignore_index=True))
                st.rerun()

# 5. ΔΑΝΕΙΟΔΟΤΗΣΗ
with tabs[4]:
    st.subheader("🏦 Δανειοδότηση")
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)
