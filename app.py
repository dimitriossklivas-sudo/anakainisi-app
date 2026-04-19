import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ & DESIGN
st.set_page_config(page_title="Σκλίβας Δημήτριος | Pro", layout="wide")

# Custom CSS για ομορφιά και διόρθωση ορατότητας στα Metrics
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 55px;
        background-color: #ffffff;
        border-radius: 10px 10px 0px 0px;
        padding: 10px 15px;
        font-weight: 600;
        color: #495057;
        border: 1px solid #e9ecef;
    }
    .stTabs [aria-selected="true"] {
        background-color: #D4AF37 !important;
        color: white !important;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #D4AF37;
    }
    div[data-testid="stMetricLabel"] > div { color: #495057 !important; font-weight: bold !important; }
    div[data-testid="stMetricValue"] > div { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO & HEADER ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# Σύνδεση & Helper Functions
conn = st.connection("gsheets", type=GSheetsConnection)
def safe_read(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl="0")
    except: return pd.DataFrame()

# 2. ΔΗΜΙΟΥΡΓΙΑ TABS
tabs = st.tabs(["📊 Στατιστικά", "👷 Συνεργεία", "📈 Πρόοδος", "💰 Προσφορές", "🏦 Δάνειο", "📝 Ιστορικό", "📐 Calculator", "📁 Αρχεία"])

# --- TAB 1: ΣΤΑΤΙΣΤΙΚΑ ---
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        m1.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{df_exp[df_exp['Πληρωτής'] == 'Εγώ']['Ποσό'].sum():,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{df_exp[df_exp['Πληρωτής'] == 'Πατέρας']['Ποσό'].sum():,.2f} €")
        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή", hole=0.4), use_container_width=True)
        with c2: st.plotly_chart(px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής', title="Ανά Άτομο"), use_container_width=True)
    with st.expander("➕ Καταχώρηση Εξόδου"):
        with st.form("f_exp", clear_on_submit=True):
            e_d = st.date_input("Ημερομηνία")
            e_c = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
            e_a = st.number_input("Ποσό (€)", min_value=0.0)
            e_p = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new = pd.DataFrame([{"Ημερομηνία": str(e_d), "Κατηγορία": e_c, "Ποσό": e_a, "Πληρωτής": e_p}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new], ignore_index=True))
                st.rerun()
# --- TAB 2: ΣΥΝΕΡΓΕΙΑ (ΕΠΑΝΑΦΟΡΑ) ---
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων & Επαφών")
    
    # 1. Διάβασμα δεδομένων
    df_c = safe_read("Contacts")
    
    # 2. Φόρμα Εισαγωγής Νέας Επαφής
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
        with st.form("form_contact_new", clear_on_submit=True):
            col_name, col_job = st.columns(2)
            with col_name:
                c_name = st.text_input("Ονοματεπώνυμο / Τεχνικός")
            with col_job:
                c_job = st.text_input("Ειδικότητα (π.χ. Ηλεκτρολόγος)")
            
            c_phone = st.text_input("Τηλέφωνο Επικοινωνίας")
            c_notes = st.text_area("Σημειώσεις")
            
            if st.form_submit_button("Αποθήκευση"):
                if c_name:
                    new_contact = pd.DataFrame([{
                        "Όνομα": c_name, 
                        "Ειδικότητα": c_job, 
                        "Τηλέφωνο": c_phone,
                        "Σημειώσεις": c_notes
                    }])
                    conn.update(worksheet="Contacts", data=pd.concat([df_c, new_contact], ignore_index=True))
                    st.toast(f"Η επαφή {c_name} αποθηκεύτηκε!", icon="✅")
                    st.rerun()
                else:
                    st.error("Παρακαλώ συμπληρώστε τουλάχιστον το όνομα.")

    st.divider()

    # 3. Προβολή Λίστας
    if not df_c.empty:
        st.write("### Κατάλογος Επαφών")
        # Χρήση st.data_editor για να μπορείς να σβήνεις ή να αλλάζεις απευθείας (προαιρετικό)
        st.dataframe(df_c, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένες επαφές.")
# --- TAB 3: ΠΡΟΟΔΟΣ ΕΡΓΑΣΙΩΝ ---
with tabs[2]:
    st.subheader("📈 Παρακολούθηση Προόδου & Πληρωμών")
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    
    # Φόρμα για νέα εργασία
    with st.expander("➕ Προσθήκη Νέας Εργασίας/Συμφωνίας"):
        with st.form("new_task_form"):
            nt_name = st.text_input("Όνομα Εργασίας (π.χ. Υδραυλικά)")
            nt_deal = st.number_input("Συμφωνημένη Αμοιβή (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη"):
                new_t = pd.DataFrame([{"Εργασία": nt_name, "Κατάσταση": "Σε εξέλιξη", "Συνολική Αμοιβή": nt_deal}])
                conn.update(worksheet="Progress", data=pd.concat([df_p, new_t], ignore_index=True))
                st.rerun()

    st.divider()

    if not df_p.empty:
        # Καθαρισμός στηλών για σωστή σύγκριση
        if not df_e.empty:
            df_e.columns = df_e.columns.str.strip()
            df_e['Κατηγορία'] = df_e['Κατηγορία'].astype(str).str.strip()
            df_e['Είδος'] = df_e['Είδος'].astype(str).str.strip()

        for i, r in df_p.iterrows():
            t_name = str(r['Εργασία']).strip()
            # Υπολογισμός πληρωμών μόνο για "Αμοιβή" στην αντίστοιχη κατηγορία
            p_done = df_e[(df_e['Κατηγορία'] == t_name) & (df_e['Είδος'].isin(["Αμοιβή", "Αμοιβές"]))]['Ποσό'].sum() if not df_e.empty else 0
            total = r['Συνολική Αμοιβή']
            
            # Υπολογισμός ποσοστού
            perc = (p_done / total) if total > 0 else 0
            
            # Εμφάνιση Μπάρας
            st.write(f"### {t_name}")
            col_bar, col_met = st.columns([3, 1])
            
            with col_bar:
                st.progress(min(perc, 1.0))
                st.write(f"💰 Πληρώθηκαν: **{p_done:,.2f} €** από **{total:,.2f} €**")
            
            with col_met:
                st.metric("Εξόφληση", f"{perc*100:.1f}%")
            st.divider()
    else:
        st.info("Δεν έχουν καταχωρηθεί εργασίες στο φύλλο Progress.")
# --- TAB 4: ΠΡΟΣΦΟΡΕΣ (ΕΠΑΝΑΦΟΡΑ & ΕΝΙΣΧΥΣΗ) ---
with tabs[3]:
    st.subheader("💰 Διαχείριση & Σύγκριση Προσφορών")
    
    df_o = safe_read("Offers")
    
    # Φόρμα Εισαγωγής Νέας Προσφοράς
    with st.expander("➕ Καταχώρηση Νέας Προσφοράς"):
        with st.form("form_offer_new", clear_on_submit=True):
            o_date = st.date_input("Ημερομηνία Προσφοράς")
            o_prov = st.text_input("Πάροχος / Κατάστημα (π.χ. Leroy Merlin, Τοπικός)")
            o_desc = st.text_input("Περιγραφή (π.χ. Πλακάκια Μπάνιου)")
            o_amt = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            o_link = st.text_input("Link Αρχείου (π.χ. Drive PDF)")
            
            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                if o_prov and o_amt > 0:
                    new_offer = pd.DataFrame([{
                        "Ημερομηνία": str(o_date),
                        "Πάροχος": o_prov,
                        "Περιγραφή": o_desc,
                        "Ποσό": o_amt,
                        "Link": o_link
                    }])
                    conn.update(worksheet="Offers", data=pd.concat([df_o, new_offer], ignore_index=True))
                    st.toast("Η προσφορά καταχωρήθηκε επιτυχώς!", icon="💰")
                    st.rerun()
                else:
                    st.warning("Παρακαλώ συμπληρώστε Πάροχο και Ποσό.")

    st.divider()

    # Προβολή Προσφορών
    if not df_o.empty:
        # Υπολογισμός χαμηλότερης προσφοράς για info
        min_offer = df_o['Ποσό'].min()
        st.info(f"💡 Η πιο οικονομική προσφορά μέχρι στιγμής είναι: **{min_offer:,.2f} €**")
        
        st.dataframe(df_o, use_container_width=True)
    else:
        st.info("Δεν έχουν καταχωρηθεί προσφορές ακόμα.")

# --- TAB 5: ΔΑΝΕΙΟ (ΕΠΑΝΑΦΟΡΑ & ΚΑΤΑΧΩΡΗΣΗ) ---
with tabs[4]:
    st.subheader("🏦 Διαχείριση Στεγαστικού Δανείου")
    df_l = safe_read("Loan")
    
    # 1. Metrics Δανείου
    if not df_l.empty:
        # Υποθέτουμε ότι η τελευταία εγγραφή έχει το τρέχον υπόλοιπο
        current_balance = df_l['Υπόλοιπο Δανείου'].iloc[-1]
        st.metric("Τρέχον Υπόλοιπο Δανείου", f"{current_balance:,.2f} €", delta_color="inverse")
    
    # 2. Φόρμα Καταχώρησης Δόσης / Κίνησης
    with st.expander("➕ Καταχώρηση Πληρωμής Δόσης"):
        with st.form("form_loan_new", clear_on_submit=True):
            l_date = st.date_input("Ημερομηνία Πληρωμής")
            l_paid = st.number_input("Ποσό Δόσης (€)", min_value=0.0)
            l_new_bal = st.number_input("Νέο Υπόλοιπο Δανείου (€)", min_value=0.0)
            
            if st.form_submit_button("Ενημέρωση Δανείου"):
                if l_paid > 0:
                    new_loan_entry = pd.DataFrame([{
                        "Ημερομηνία": str(l_date),
                        "Ποσό Δόσης": l_paid,
                        "Υπόλοιπο Δανείου": l_new_bal
                    }])
                    conn.update(worksheet="Loan", data=pd.concat([df_l, new_loan_entry], ignore_index=True))
                    st.toast("Το υπόλοιπο του δανείου ενημερώθηκε!", icon="🏦")
                    st.rerun()

    st.divider()
    if not df_l.empty:
        st.write("### Ιστορικό Πληρωμών Δανείου")
        st.dataframe(df_l, use_container_width=True)

# --- TAB 6: ΙΣΤΟΡΙΚΟ (ΠΛΗΡΗΣ ΛΙΣΤΑ ΕΞΟΔΩΝ) ---
with tabs[5]:
    st.subheader("📝 Αναλυτικό Ιστορικό Εξόδων")
    df_all_exp = safe_read("Expenses")
    
    if not df_all_exp.empty:
        st.write("💡 Χρησιμοποιήστε τα βέλη στις κεφαλίδες για ταξινόμηση (π.χ. ανά ημερομηνία ή ποσό).")
        
        # Προσθήκη φίλτρου γρήγορης αναζήτησης
        search = st.text_input("🔍 Αναζήτηση στο ιστορικό (π.χ. 'Leroy' ή 'Υδραυλικά')")
        if search:
            df_all_exp = df_all_exp[df_all_exp.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        st.dataframe(df_all_exp, use_container_width=True)
        
        # Δυνατότητα λήψης σε CSV
        csv = df_all_exp.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Λήψη Ιστορικού σε Excel/CSV",
            data=csv,
            file_name='sklivas_expenses_history.csv',
            mime='text/csv',
        )
    else:
        st.info("Δεν υπάρχουν δεδομένα εξόδων για εμφάνιση.")
elif mode == "Γεμίσματα":
        area = st.number_input("m² Δαπέδου", value=10.0)
        thick = st.number_input("Πάχος (cm)", value=5.0)
        vol = area * (thick / 100)
        
        # Υπολογισμοί (Αναλογία 1:4)
        cem = vol * 6.5           # ~6.5 σάκοι των 25kg ανά m3
        sand_m3 = vol * 0.9       # ~0.9 m3 άμμος ανά m3 μείγματος
        sand_tons = sand_m3 * 1.6 # 1 m3 άμμου = ~1.6 τόνοι
        
        st.write("### 🏗️ Υλικά για Παραγγελία")
        res1, res2, res3 = st.columns(3)
        res1.metric("Τσιμέντο (25kg)", f"{int(cem)+1} σάκοι")
        res2.metric("Άμμος (m³)", f"{sand_m3:.2f} m³")
        res3.metric("Άμμος (Τόνοι)", f"{sand_tons:.1f} t")
        
        st.info(f"💡 Συμβουλή: Θα χρειαστείτε περίπου {int(sand_m3/0.8)+1} Big Bags άμμου.")
# --- TAB 8: ΑΡΧΕΙΑ ---
with tabs[7]:
    st.subheader("📁 Αρχεία")
    df_f = safe_read("Files")
    st.dataframe(df_f, use_container_width=True)
