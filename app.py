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
# 1. ΕΝΟΤΗΤΑ ΣΤΑΤΙΣΤΙΚΩΝ & ΕΞΟΔΩΝ (Αναβαθμισμένη v4.7)
# ---------------------------------------------------------
with tabs[0]:
    df_exp = safe_read("Expenses")
    
    if not df_exp.empty:
        st.subheader("📊 Λεπτομερής Οικονομική Ανάλυση")
        
        # 1. ΣΥΝΟΛΙΚΑ ΑΝΑ ΠΛΗΡΩΤΗ (Metric Cards)
        col_m1, col_m2, col_m3 = st.columns(3)
        total_spent = df_exp['Ποσό'].sum()
        
        # Υπολογισμός ποσών
        paid_by_me = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        paid_by_father = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        col_m1.metric("Συνολικό Κόστος", f"{total_spent:,.2f} €")
        col_m2.metric("Πληρωμές (Εγώ)", f"{paid_by_me:,.2f} €", delta=f"{(paid_by_me/total_spent)*100:.1f}%")
        col_m3.metric("Πληρωμές (Πατέρας)", f"{paid_by_father:,.2f} €", delta=f"{(paid_by_father/total_spent)*100:.1f}%")
        
        st.divider()

        # 2. ΔΙΑΓΡΑΜΜΑΤΑ
        c_chart1, c_chart2 = st.columns([1, 1])
        
        with c_chart1:
            st.write("### 🍰 Συνολική Συμμετοχή")
            fig_payer_pie = px.pie(df_exp, values='Ποσό', names='Πληρωτής', 
                                  color='Πληρωτής', 
                                  color_discrete_map={'Εγώ':'#D4AF37', 'Πατέρας':'#4A90E2'},
                                  hole=0.4)
            st.plotly_chart(fig_payer_pie, use_container_width=True)

        with c_chart2:
            st.write("### 📊 Ανάλυση ανά Κατηγορία & Πληρωτή")
            # Δημιουργία Stacked Bar Chart
            fig_bar = px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής',
                             title="Ποιος πλήρωσε τι σε κάθε κατηγορία",
                             barmode='stack',
                             color_discrete_map={'Εγώ':'#D4AF37', 'Πατέρας':'#4A90E2'})
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.write("### 📝 Πρόσφατες Καταχωρήσεις")
        st.dataframe(df_exp.tail(10), use_container_width=True)
    
    # Φόρμα εισαγωγής (παραμένει η ίδια αλλά ελέγχουμε τα ονόματα)
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("exp_form_v47", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_desc = st.text_input("Περιγραφή (π.χ. Αμοιβή Υδραυλικού)")
            e_cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new_data = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, "Ποσό": e_amt, "Πληρωτής": e_payer}])
                updated_df = pd.concat([df_exp, new_data], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
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
# 3. ΕΝΟΤΗΤΑ ΠΡΟΟΔΟΥ (Με Οικονομική Ολοκλήρωση)
# ---------------------------------------------------------
with tabs[2]:
    st.subheader("📦 Πρόοδος Εργασιών & Οικονομική Εικόνα")
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    
    if not df_p.empty:
        for i, r in df_p.iterrows():
            with st.container():
                # Υπολογισμός πληρωμών από το φύλλο Expenses για τη συγκεκριμένη εργασία
                # Ψάχνει στην Περιγραφή των εξόδων αν περιέχεται το όνομα της εργασίας
                payments_done = 0
                if not df_e.empty:
                    payments_done = df_e[df_e['Περιγραφή'].str.contains(r['Εργασία'], case=False, na=False)]['Ποσό'].sum()
                
                total_deal = r['Συνολική Αμοιβή'] if 'Συνολική Αμοιβή' in r else 0
                
                # Υπολογισμός ποσοστού πληρωμής
                pay_percent = (payments_done / total_deal) if total_deal > 0 else 0
                
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"### {r['Εργασία']}")
                    st.write(f"**Κατάσταση:** {r['Κατάσταση']}")
                
                with col2:
                    st.write(f"**Πληρωμένο:** {payments_done:,.2f} / {total_deal:,.2f} €")
                    st.progress(min(pay_percent, 1.0))
                    st.caption(f"Οικονομική Εξόφληση: {pay_percent*100:.1f}%")
                
                with col3:
                    if st.button("✅ Ολοκλήρωση", key=f"done_{i}"):
                        df_p.at[i, 'Κατάσταση'] = "Ολοκληρώθηκε"
                        conn.update(worksheet="Progress", data=df_p)
                        st.rerun()
                st.divider()
    else:
        st.info("Δεν βρέθηκαν εργασίες στο φύλλο Progress.")
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
