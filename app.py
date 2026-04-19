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

# --- TAB 2, 3, 4, 5, 6 (ΣΥΝΟΠΤΙΚΑ) ---
with tabs[1]: 
    df_c = safe_read("Contacts")
    st.dataframe(df_c, use_container_width=True)
with tabs[2]: st.write("Πρόοδος Εργασιών")
with tabs[3]: 
    df_o = safe_read("Offers")
    st.dataframe(df_o, use_container_width=True)
with tabs[4]: 
    df_l = safe_read("Loan")
    st.dataframe(df_l, use_container_width=True)
with tabs[5]: st.dataframe(safe_read("Expenses"), use_container_width=True)

# --- TAB 7: CALCULATOR (ΔΙΟΡΘΩΜΕΝΟ) ---
with tabs[6]:
    st.subheader("📐 Υπολογιστής Υλικών")
    mode = st.radio("Επιλογή:", ["Πλακάκια", "Γεμίσματα", "Χρώματα"], horizontal=True)
    
    if mode == "Πλακάκια":
        w = st.number_input("Πλάτος (cm)", value=60.0)
        h = st.number_input("Ύψος (cm)", value=120.0)
        m2 = st.number_input("m² Επιφάνειας", value=10.0)
        tile_m2 = (w * h) / 10000
        st.metric("Τεμάχια που χρειάζονται", int(m2/tile_m2)+1)
        
    elif mode == "Γεμίσματα":
        area = st.number_input("m² Δαπέδου", value=10.0)
        thick = st.number_input("Πάχος (cm)", value=5.0)
        vol = area * (thick / 100)
        # Υπολογισμός Άμμου & Τσιμέντου
        cem = vol * 6.5
        sand_m3 = vol * 0.9
        res1, res2 = st.columns(2)
        res1.metric("Τσιμέντο (25kg)", f"{int(cem)+1} σάκοι")
        res2.metric("Άμμος (m³)", f"{sand_m3:.2f} m³")
        st.info(f"💡 Περίπου {int(sand_m3/0.8)+1} Big Bags άμμου.")

    elif mode == "Χρώματα":
        p_m2 = st.number_input("m² Τοίχου", value=50.0)
        st.success(f"🎨 Χρειάζεστε περίπου: {(p_m2 * 2) / 12:.1f} Λίτρα")

# --- TAB 8: ΑΡΧΕΙΑ ---
with tabs[7]:
    st.subheader("📁 Αρχεία")
    df_f = safe_read("Files")
    st.dataframe(df_f, use_container_width=True)
