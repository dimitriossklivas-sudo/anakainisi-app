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

# ---------------------------------------------------------
# 1. ΕΝΟΤΗΤΑ ΣΤΑΤΙΣΤΙΚΩΝ & ΕΞΟΔΩΝ (Επαναφορά & Βελτίωση)
# ---------------------------------------------------------
with tabs[0]:
    df_exp = safe_read("Expenses")
    
    if not df_exp.empty:
        st.subheader("📊 Οικονομική Σύνοψη")
        
        # 1. ΚΕΝΤΡΙΚΑ ΝΟΥΜΕΡΑ (METRICS)
        col_m1, col_m2, col_m3 = st.columns(3)
        total_spent = df_exp['Ποσό'].sum()
        
        # Υπολογισμός ανά πληρωτή
        paid_by_me = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        paid_by_father = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        col_m1.metric("Συνολικά Έξοδα", f"{total_spent:,.2f} €")
        col_m2.metric("Πληρωμές (Εγώ)", f"{paid_by_me:,.2f} €")
        col_m3.metric("Πληρωμές (Πατέρας)", f"{paid_by_father:,.2f} €")
        
        st.divider()

        # 2. ΔΙΑΓΡΑΜΜΑΤΑ (Πίτα & Μπάρες)
        c_chart1, c_chart2 = st.columns([1, 1])
        
        with c_chart1:
            # Πίτα ανά Κατηγορία (Οικοδομικά, Υδραυλικά κλπ)
            fig_pie = px.pie(df_exp, values='Ποσό', names='Κατηγορία', 
                             title="Κατανομή ανά Εργασία", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c_chart2:
            # Μπάρες ανά Κατηγορία και Πληρωτή
            fig_bar = px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής',
                             title="Ποιος πλήρωσε τι ανά Εργασία",
                             barmode='group', # Δίπλα-δίπλα μπάρες για καθαρή εικόνα
                             color_discrete_map={'Εγώ':'#D4AF37', 'Πατέρας':'#4A90E2'})
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.write("### 📝 Ιστορικό Εξόδων")
        st.dataframe(df_exp.tail(15), use_container_width=True)
    
    # ΦΟΡΜΑ ΚΑΤΑΧΩΡΗΣΗΣ (Πλήρης με Είδος)
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("exp_form_final", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                e_date = st.date_input("Ημερομηνία")
                e_cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
                e_type = st.radio("Είδος Εξόδου", ["Αμοιβή", "Υλικά"], horizontal=True)
            with f_col2:
                e_amt = st.number_input("Ποσό (€)", min_value=0.0)
                e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            
            e_desc = st.text_input("Περιγραφή (π.χ. Προκαταβολή ή Αγορά πλακιδίων)")
            
            if st.form_submit_button("Αποθήκευση"):
                new_data = pd.DataFrame([{
                    "Ημερομηνία": str(e_date), 
                    "Περιγραφή": e_desc, 
                    "Κατηγορία": e_cat, 
                    "Είδος": e_type,
                    "Ποσό": e_amt, 
                    "Πληρωτής": e_payer
                }])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new_data], ignore_index=True))
                st.success("Το έξοδο αποθηκεύτηκε!")
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
# 3. ΕΝΟΤΗΤΑ ΠΡΟΟΔΟΥ - ΣΥΝΔΕΣΗ ΜΕ ΟΙΚΟΝΟΜΙΚΑ (v4.8)
# ---------------------------------------------------------
with tabs[2]:
    st.subheader("📦 Εξέλιξη Εργασιών & Έλεγχος Πληρωμών")
    
    # Διαβάζουμε και τα δύο φύλλα για να κάνουμε τη διασταύρωση
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    
    if not df_p.empty:
        # Συνολική πρόοδο έργου (οπτικά)
        total_tasks = len(df_p)
        done_tasks = len(df_p[df_p['Κατάσταση'] == "Ολοκληρώθηκε"])
        st.write(f"**Συνολική Ολοκλήρωση Έργου: {done_tasks}/{total_tasks} Εργασίες**")
        st.progress(done_tasks / total_tasks if total_tasks > 0 else 0)
        st.divider()

        for i, r in df_p.iterrows():
            with st.container():
                # 1. ΥΠΟΛΟΓΙΣΜΟΣ ΠΛΗΡΩΜΩΝ
                # Ψάχνουμε στα έξοδα όπου η Κατηγορία ταυτίζεται με την Εργασία 
                # ΚΑΙ το Είδος είναι "Αμοιβή" (για να μην μετρήσουμε τα υλικά)
                current_payments = 0
                if not df_e.empty and 'Είδος' in df_e.columns:
                    current_payments = df_e[
                        (df_e['Κατηγορία'] == r['Εργασία']) & 
                        (df_e['Είδος'] == "Αμοιβή")
                    ]['Ποσό'].sum()
                
                # 2. ΣΥΝΟΛΙΚΗ ΣΥΜΦΩΝΙΑ
                total_agreement = r['Συνολική Αμοιβή'] if 'Συνολική Αμοιβή' in r else 0
                
                # 3. ΥΠΟΛΟΓΙΣΜΟΣ ΠΟΣΟΣΤΟΥ ΕΞΟΦΛΗΣΗΣ
                pay_ratio = (current_payments / total_agreement) if total_agreement > 0 else 0
                
                # ΕΜΦΑΝΙΣΗ
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"### {r['Εργασία']}")
                    st.caption(f"Κατάσταση: {r['Κατάσταση']}")
                
                with col2:
                    # Μπάρα οικονομικής εξόφλησης
                    st.write(f"💰 **{current_payments:,.2f} €** / {total_agreement:,.2f} €")
                    st.progress(min(pay_ratio, 1.0))
                    st.caption(f"Εξόφληση Αμοιβής: {pay_ratio*100:.1f}%")
                
                with col3:
                    # Κουμπί ολοκλήρωσης εργασίας
                    if r['Κατάσταση'] != "Ολοκληρώθηκε":
                        if st.button("✅ Τέλος", key=f"p_done_{i}"):
                            df_p.at[i, 'Κατάσταση'] = "Ολοκληρώθηκε"
                            conn.update(worksheet="Progress", data=df_p)
                            st.rerun()
                    else:
                        st.success("Ολοκληρώθηκε")
                
                st.write("---") # Διαχωριστική γραμμή ανά εργασία
    else:
        st.info("Η λίστα εργασιών είναι κενή. Προσθέστε εργασίες στο Google Sheets (Φύλλο: Progress).")

    # Φόρμα για προσθήκη νέας εργασίας απευθείας από την εφαρμογή
    with st.expander("➕ Προσθήκη Νέας Εργασίας προς Παρακολούθηση"):
        with st.form("new_task_form", clear_on_submit=True):
            nt_name = st.text_input("Όνομα Εργασίας (π.χ. Υδραυλικά)")
            nt_deal = st.number_input("Συνολική Συμφωνημένη Αμοιβή (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη"):
                if nt_name:
                    new_task = pd.DataFrame([{"Εργασία": nt_name, "Κατάσταση": "Εκκρεμεί", "Συνολική Αμοιβή": nt_deal}])
                    updated_p = pd.concat([df_p, new_task], ignore_index=True)
                    conn.update(worksheet="Progress", data=updated_p)
                    st.success(f"Η εργασία '{nt_name}' προστέθηκε!")
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
