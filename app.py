import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ & DESIGN
st.set_page_config(page_title="Σκλίβας Δημήτριος | Pro Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 55px; background-color: #ffffff; border-radius: 10px 10px 0px 0px;
        padding: 10px 15px; font-weight: 600; color: #495057; border: 1px solid #e9ecef;
    }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: white !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; padding: 20px; border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1); border-left: 5px solid #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl="0")
    except: return pd.DataFrame()

# 2. ΔΗΜΙΟΥΡΓΙΑ TABS
tabs = st.tabs(["📊 Στατιστικά", "👷 Συνεργεία", "📈 Πρόοδος", "💰 Προσφορές", "🏦 Δάνειο", "📝 Ιστορικό", "📐 Calculator", "📁 Αρχεία"])

# --- TAB 1: ΣΤΑΤΙΣΤΙΚΑ & ΚΑΤΑΧΩΡΗΣΗ ΕΞΟΔΩΝ ---
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        m1.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{df_exp[df_exp['Πληρωτής'] == 'Εγώ']['Ποσό'].sum():,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{df_exp[df_exp['Πληρωτής'] == 'Πατέρας']['Ποσό'].sum():,.2f} €")
    
    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("form_exp", clear_on_submit=True):
            e_date = st.date_input("Ημερομηνία")
            e_cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Πλακάκια", "Άλλο"])
            e_amt = st.number_input("Ποσό (€)", min_value=0.0)
            e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            e_type = st.radio("Είδος", ["Αμοιβή", "Υλικά"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"Ημερομηνία": str(e_date), "Κατηγορία": e_cat, "Ποσό": e_amt, "Πληρωτής": e_payer, "Είδος": e_type}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new_row], ignore_index=True))
                st.rerun()

# --- TAB 2: ΣΥΝΕΡΓΕΙΑ ---
with tabs[1]:
    df_c = safe_read("Contacts")
    with st.expander("➕ Νέος Συνεργάτης"):
        with st.form("form_c"):
            c_n = st.text_input("Όνομα")
            c_j = st.text_input("Ειδικότητα")
            c_p = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Προσθήκη"):
                new_c = pd.DataFrame([{"Όνομα": c_n, "Ειδικότητα": c_j, "Τηλέφωνο": c_p}])
                conn.update(worksheet="Contacts", data=pd.concat([df_c, new_c], ignore_index=True))
                st.rerun()
    st.dataframe(df_c, use_container_width=True)

# --- TAB 3: ΠΡΟΟΔΟΣ ---
with tabs[2]:
    df_p = safe_read("Progress")
    df_ex = safe_read("Expenses")
    if not df_p.empty:
        for i, r in df_p.iterrows():
            t_name = str(r['Εργασία']).strip()
            paid = df_ex[(df_ex['Κατηγορία'] == t_name) & (df_ex['Είδος'] == "Αμοιβή")]['Ποσό'].sum() if not df_ex.empty else 0
            total = r['Συνολική Αμοιβή']
            p_perc = min(paid/total, 1.0) if total > 0 else 0
            st.write(f"**{t_name}** ({p_perc*100:.1f}%)")
            st.progress(p_perc)
    with st.expander("➕ Νέα Συμφωνία"):
        with st.form("form_p"):
            p_t = st.text_input("Εργασία")
            p_a = st.number_input("Συμφωνημένο Ποσό", min_value=0.0)
            if st.form_submit_button("
