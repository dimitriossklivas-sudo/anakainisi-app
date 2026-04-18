import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ & DESIGN
st.set_page_config(page_title="Σκλίβας Δημήτριος | Pro", layout="wide")

# Custom CSS για ομορφιά και διόρθωση των Metrics (άσπρες μπάρες)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Στυλ για τα Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background-color: #ffffff;
        border-radius: 12px 12px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #495057;
        border: 1px solid #e9ecef;
    }
    .stTabs [aria-selected="true"] {
        background-color: #D4AF37 !important;
        color: white !important;
    }
    
    /* ΔΙΟΡΘΩΣΗ ΓΙΑ ΤΙΣ ΑΣΠΡΕΣ ΜΠΑΡΕΣ (METRICS) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #D4AF37;
    }
    /* Σκούρο χρώμα στο κείμενο των Metrics για να διαβάζεται στο λευκό */
    div[data-testid="stMetricLabel"] > div {
        color: #495057 !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# Σύνδεση & Helper Functions
conn = st.connection("gsheets", type=GSheetsConnection)
def safe_read(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl="0")
    except: return pd.DataFrame()

# 2. ΔΗΜΙΟΥΡΓΙΑ TABS
tabs = st.tabs([
    "📊 Στατιστικά", "👷 Συνεργεία", "📈 Πρόοδος", "💰 Προσφορές", 
    "🏦 Δάνειο", "📝 Ιστορικό", "📐 Calculator", "📁 Αρχεία"
])

# --- TAB 1: ΣΤΑΤΙΣΤΙΚΑ ---
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        total_val = df_exp['Ποσό'].sum()
        ego_val = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        father_val = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        m1.metric("Συνολικά Έξοδα", f"{total_val:,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{ego_val:,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{father_val:,.2f} €")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή ανά Εργασία", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής', title="Πληρωμές ανά Άτομο", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("new_exp_final", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                e_date = st.date_input("Ημερομηνία")
                e_cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
                e_type = st.radio("Είδος", ["Αμοιβή", "Υλικά"], horizontal=True)
            with f2:
                e_amt = st.number_input("Ποσό (€)", min_value=0.0)
                e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            e_desc = st.text_input("Περιγραφή")
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, "Ποσό": e_amt, "Πληρωτής": e_payer, "Είδος": e_type}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new_row], ignore_index=True))
                st.rerun()

# --- TAB 2: ΣΥΝΕΡΓΕΙΑ ---
with tabs[1]:
    st.subheader("👷 Διαχείριση Συνεργείων")
    df_c = safe_read("Contacts")
    
    # Φόρμα Εισαγωγής Νέας Επαφής
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
        with st.form("new_contact_form", clear_on_submit=True):
            c_name = st.text_input("Ονοματεπώνυμο / Επωνυμία")
            c_job = st.text_input("Ειδικότητα (π.χ. Ηλεκτρολόγος)")
            c_phone = st.text_input("Τηλέφωνο Επικοινωνίας")
            c_note = st.text_area("Σχόλια (π.χ. Διεύθυνση ή Ωράριο)")
            
            if st.form_submit_button("Αποθήκευση Επαφής"):
                if c_name and c_phone:
                    new_contact = pd.DataFrame([{
                        "Όνομα": c_name, 
                        "Ειδικότητα": c_job, 
                        "Τηλέφωνο": c_phone, 
                        "Σημειώσεις": c_note
                    }])
                    conn.update(worksheet="Contacts", data=pd.concat([df_c, new_contact], ignore_index=True))
                    st.toast("Η επαφή αποθηκεύτηκε!", icon="✅")
                    st.rerun()
                else:
                    st.error("Το όνομα και το τηλέφωνο είναι υποχρεωτικά.")

    st.divider()
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)

# --- TAB 3: ΠΡΟΟΔΟΣ ---
with tabs[2]:
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    with st.expander("➕ Προσθήκη Νέας Εργασίας"):
        with st.form("new_task"):
            nt_name = st.text_input("Εργασία")
            nt_deal = st.number_input("Συνολική Αμοιβή (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη"):
                new_t = pd.DataFrame([{"Εργασία": nt_name, "Κατάσταση": "Εκκρεμεί", "Συνολική Αμοιβή": nt_deal}])
                conn.update(worksheet="Progress", data=pd.concat([df_p, new_t], ignore_index=True))
                st.rerun()
    if not df_p.empty:
        if not df_e.empty:
            df_e.columns = df_e.columns.str.strip()
            df_e['Κατηγορία'] = df_e['Κατηγορία'].astype(str).str.strip()
            df_e['Είδος'] = df_e['Είδος'].astype(str).str.strip()
        for i, r in df_p.iterrows():
            t_name = str(r['Εργασία']).strip()
            p_done = df_e[(df_e['Κατηγορία'] == t_name) & (df_e['Είδος'].isin(["Αμοιβή", "Αμοιβές"]))]['Ποσό'].sum() if not df_e.empty else 0
            total = r['Συνολική Αμοιβή']
            perc = (p_done / total) if total > 0 else 0
            st.write(f"### {t_name}")
            c_t, c_m = st.columns([3, 1])
            c_t.progress(min(perc, 1.0))
            c_t.write(f"💰 {p_done:,.2f} € / {total:,.2f} €")
            c_m.metric("Εξόφληση", f"{perc*100:.1f}%")
            st.divider()

# --- TAB 4: ΠΡΟΣΦΟΡΕΣ ---
with tabs[3]:
    st.subheader("💰 Διαχείριση Προσφορών")
    df_o = safe_read("Offers")
    
    # Φόρμα Εισαγωγής Νέας Προσφοράς
    with st.expander("➕ Καταχώρηση Νέας Προσφοράς"):
        with st.form("new_offer_form", clear_on_submit=True):
            o_provider = st.text_input("Πάροχος / Κατάστημα")
            o_desc = st.text_input("Περιγραφή Ειδών (π.χ. Είδη Υγιεινής)")
            o_amt = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            o_date = st.date_input("Ημερομηνία Προσφοράς")
            o_link = st.text_input("Link (Drive/PDF) αν υπάρχει")
            
            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                if o_provider and o_amt > 0:
                    new_offer = pd.DataFrame([{
                        "Ημερομηνία": str(o_date),
                        "Πάροχος": o_provider,
                        "Περιγραφή": o_desc,
                        "Ποσό": o_amt,
                        "Link": o_link
                    }])
                    conn.update(worksheet="Offers", data=pd.concat([df_o, new_offer], ignore_index=True))
                    st.toast("Η προσφορά καταχωρήθηκε!", icon="💰")
                    st.rerun()
                else:
                    st.error("Συμπληρώστε Πάροχο και Ποσό.")

    st.divider()
    if not df_o.empty:
        st.dataframe(df_o, use_container_width=True)

# --- TAB 5: ΔΑΝΕΙΟ ---
with tabs[4]:
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)

# --- TAB 6: ΙΣΤΟΡΙΚΟ ---
with tabs[5]:
    df_list = safe_read("Expenses")
    if not df_list.empty:
        st.dataframe(df_list, use_container_width=True)

# --- TAB 7: CALCULATOR ---
with tabs[6]:
    calc = st.selectbox("Τύπος:", ["Πλακάκια", "Χρώματα"])
    if calc == "Πλακάκια":
        a = st.number_input("m²", value=20.0)
        b = st.number_input("m²/box", value=1.44)
        st.success(f"Κουτιά: {int((a*1.1)/b)+1}")
    else:
        a = st.number_input("m² επιφάνειας", value=50.0)
        st.success(f"Λίτρα (2 χέρια): {(a*2)/12:.1f} L")

# --- TAB 8: ΑΡΧΕΙΑ ---
with tabs[7]:
    st.info("Καταγράψτε links από το Google Drive για αποδείξεις/φωτογραφίες.")
    df_f = safe_read("Files")
    f_desc = st.text_input("Περιγραφή αρχείου")
    f_link = st.text_input("Link (Drive)")
    if st.button("Αποθήκευση Link"):
        new_f = pd.DataFrame([{"Ημερομηνία": "Σήμερα", "Περιγραφή": f_desc, "Link": f_link}])
        conn.update(worksheet="Files", data=pd.concat([df_f, new_f], ignore_index=True))
        st.rerun()
    if not df_f.empty: st.dataframe(df_f, use_container_width=True)
