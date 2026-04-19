import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ & DESIGN
st.set_page_config(page_title="Σκλίβας Δημήτριος | Pro Dashboard", layout="wide")

# Custom CSS για ομορφιά και διόρθωση ορατότητας
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Στυλ για τα Tabs */
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
        border-color: #D4AF37 !important;
    }
    
    /* ΔΙΟΡΘΩΣΗ ΓΙΑ ΤΙΣ ΚΑΡΤΕΣ METRICS (ΑΣΠΡΕΣ ΜΠΑΡΕΣ) */
    div[data-testid="stMetric"] {
        background-color: #ffffff !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #D4AF37;
    }
    div[data-testid="stMetricLabel"] > div {
        color: #495057 !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricValue"] > div {
        color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO & HEADER ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6c757d; font-size: 16px; margin-top: -10px;'>Premium Σύστημα Διαχείρισης Ανακαίνισης</p>", unsafe_allow_html=True)

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

# --- TAB 1: ΣΤΑΤΙΣΤΙΚΑ & ΕΞΟΔΑ ---
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        total = df_exp['Ποσό'].sum()
        ego = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        father = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        m1.metric("Συνολικά Έξοδα", f"{total:,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{ego:,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{father:,.2f} €")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή ανά Εργασία", hole=0.4), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής', title="Πληρωμές ανά Άτομο", barmode='group'), use_container_width=True)

    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("form_exp", clear_on_submit=True):
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
                new = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, "Ποσό": e_amt, "Πληρωτής": e_payer, "Είδος": e_type}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new], ignore_index=True))
                st.rerun()

# --- TAB 2: ΣΥΝΕΡΓΕΙΑ ---
with tabs[1]:
    st.subheader("👷 Λίστα Συνεργατών")
    df_c = safe_read("Contacts")
    with st.expander("➕ Προσθήκη Νέου Συνεργάτη"):
        with st.form("form_contact", clear_on_submit=True):
            c_n = st.text_input("Όνομα / Τεχνικός")
            c_j = st.text_input("Ειδικότητα")
            c_p = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση"):
                new_c = pd.DataFrame([{"Όνομα": c_n, "Ειδικότητα": c_j, "Τηλέφωνο": c_p}])
                conn.update(worksheet="Contacts", data=pd.concat([df_c, new_c], ignore_index=True))
                st.rerun()
    if not df_c.empty: st.dataframe(df_c, use_container_width=True)

# --- TAB 3: ΠΡΟΟΔΟΣ ---
with tabs[2]:
    st.subheader("📉 Πρόοδος Εργασιών")
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    with st.expander("➕ Νέα Εργασία στο Πρόγραμμα"):
        with st.form("form_prog"):
            nt_n = st.text_input("Όνομα Εργασίας")
            nt_a = st.number_input("Συμφωνημένη Αμοιβή (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη"):
                new_p = pd.DataFrame([{"Εργασία": nt_n, "Κατάσταση": "Εκκρεμεί", "Συνολική Αμοιβή": nt_a}])
                conn.update(worksheet="Progress", data=pd.concat([df_p, new_p], ignore_index=True))
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
            st.write(f"**{t_name}**")
            col_a, col_b = st.columns([4, 1])
            col_a.progress(min(perc, 1.0))
            col_b.metric("Εξόφληση", f"{perc*100:.0f}%")
            st.divider()

# --- TAB 4: ΠΡΟΣΦΟΡΕΣ ---
with tabs[3]:
    st.subheader("💰 Διαχείριση Προσφορών")
    df_o = safe_read("Offers")
    with st.expander("➕ Νέα Προσφορά"):
        with st.form("form_offer"):
            o_p = st.text_input("Πάροχος")
            o_d = st.text_input("Περιγραφή")
            o_a = st.number_input("Ποσό (€)", min_value=0.0)
            if st.form_submit_button("Αποθήκευση"):
                new_o = pd.DataFrame([{"Πάροχος": o_p, "Περιγραφή": o_d, "Ποσό": o_a, "Ημερομηνία": str(st.date_input("Ημ.", key="od"))}])
                conn.update(worksheet="Offers", data=pd.concat([df_o, new_o], ignore_index=True))
                st.rerun()
    if not df_o.empty: st.dataframe(df_o, use_container_width=True)

# --- TAB 5: ΔΑΝΕΙΟ ---
with tabs[4]:
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)

# --- TAB 6: ΙΣΤΟΡΙΚΟ (ΛΙΣΤΑ) ---
with tabs[5]:
    st.subheader("📝 Αναλυτική Λίστα Εξόδων")
    df_list = safe_read("Expenses")
    if not df_list.empty:
        st.write("💡 Κάντε κλικ στις κεφαλίδες για ταξινόμηση")
        st.dataframe(df_list, use_container_width=True)

if "Γέμισμα" in type_mat:
            # Υπολογισμοί για Τσιμεντοκονία (Αναλογία 1:4)
            cement_bags = volume_m3 * 6.5  # ~6.5 τσουβάλια (25kg) ανά κυβικό
            sand_m3 = volume_m3 * 0.9      # ~0.9 m3 άμμος ανά κυβικό μείγματος
            sand_tons = sand_m3 * 1.6      # 1 m3 άμμου είναι περίπου 1.6 τόνοι
            
            res_a, res_b, res_c = st.columns(3)
            with res_a:
                st.metric("Τσιμέντο (25kg)", f"{int(cement_bags) + 1} σάκοι")
            with res_b:
                st.metric("Άμμος (m³)", f"{sand_m3:.2f} m³")
            with res_c:
                st.metric("Άμμος (Τόνοι)", f"{sand_tons:.1f} t")
            
            st.info(f"💡 Συμβουλή: Τα {sand_m3:.2f} m³ άμμου αντιστοιχούν σε περίπου {int(sand_m3 / 0.8) + 1} Big Bag (0.8m³ έκαστο).")
            st.warning(f"⚠️ Συνολικός όγκος προς κάλυψη: {volume_m3:.2f} m³")
# --- TAB 8: ΑΡΧΕΙΑ ---
with tabs[7]:
    st.subheader
