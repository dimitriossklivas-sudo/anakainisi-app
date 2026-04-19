import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# 1. ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ
st.set_page_config(page_title="Σκλίβας Δημήτριος | Pro Dashboard", layout="wide")

# Custom CSS για ομορφιά
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
    st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet_name):
    try: return conn.read(worksheet=sheet_name, ttl="0")
    except: return pd.DataFrame()

# 2. ΔΗΜΙΟΥΡΓΙΑ TABS
tabs = st.tabs(["📊 Στατιστικά", "👷 Συνεργεία", "📈 Πρόοδος", "💰 Προσφορές", "🏦 Δάνειο", "📝 Ιστορικό", "📐 Calculator", "📁 Αρχεία"])

# --- TAB 1: ΣΤΑΤΙΣΤΙΚΑ & ΚΑΤΑΧΩΡΗΣΗ ---
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
    with st.expander("➕ Προσθήκη Επαφής"):
        with st.form("form_c", clear_on_submit=True):
            c_n = st.text_input("Όνομα")
            c_j = st.text_input("Ειδικότητα")
            c_p = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Αποθήκευση Επαφής"):
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
            perc = min(paid/total, 1.0) if total > 0 else 0
            st.write(f"**{t_name}**")
            st.progress(perc)
            st.write(f"{perc*100:.1f}% ({paid:,.2f} € / {total:,.2f} €)")
    with st.expander("➕ Νέα Συμφωνία"):
        with st.form("form_p", clear_on_submit=True):
            p_t = st.text_input("Όνομα Εργασίας")
            p_a = st.number_input("Συνολική Αμοιβή Συμφωνίας (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη Εργασίας"):
                new_p = pd.DataFrame([{"Εργασία": p_t, "Συνολική Αμοιβή": p_a}])
                conn.update(worksheet="Progress", data=pd.concat([df_p, new_p], ignore_index=True))
                st.rerun()

# --- TAB 4: ΠΡΟΣΦΟΡΕΣ ---
with tabs[3]:
    df_o = safe_read("Offers")
    with st.expander("➕ Καταχώρηση Προσφοράς"):
        with st.form("form_o", clear_on_submit=True):
            o_p = st.text_input("Πάροχος/Κατάστημα")
            o_d = st.text_input("Περιγραφή Υλικών")
            o_a = st.number_input("Ποσό Προσφοράς (€)", min_value=0.0)
            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                new_o = pd.DataFrame([{"Πάροχος": o_p, "Περιγραφή": o_d, "Ποσό": o_a}])
                conn.update(worksheet="Offers", data=pd.concat([df_o, new_o], ignore_index=True))
                st.rerun()
    st.dataframe(df_o, use_container_width=True)

# --- TAB 5: ΔΑΝΕΙΟ ---
with tabs[4]:
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
    with st.expander("➕ Ενημέρωση Πληρωμής/Υπολοίπου"):
        with st.form("form_l", clear_on_submit=True):
            l_p = st.number_input("Ποσό Δόσης (€)", min_value=0.0)
            l_u = st.number_input("Νέο Υπόλοιπο Δανείου (€)", min_value=0.0)
            if st.form_submit_button("Ενημέρωση Τράπεζας"):
                new_l = pd.DataFrame([{"Ποσό Δόσης": l_p, "Υπόλοιπο Δανείου": l_u}])
                conn.update(worksheet="Loan", data=pd.concat([df_l, new_l], ignore_index=True))
                st.rerun()
    st.dataframe(df_l, use_container_width=True)

# --- TAB 6: ΙΣΤΟΡΙΚΟ ---
with tabs[5]:
    st.dataframe(safe_read("Expenses"), use_container_width=True)

# --- TAB 7: CALCULATOR ---
with tabs[6]:
    st.subheader("📐 Υπολογιστής Υλικών")
    mode = st.radio("Επιλογή:", ["Πλακάκια", "Γεμίσματα", "Χρώματα"], horizontal=True)
    if mode == "Πλακάκια":
        c1, c2 = st.columns(2)
        with c1:
            pw = st.number_input("Πλάτος (cm)", value=60.0)
            ph = st.number_input("Ύψος (cm)", value=120.0)
        with c2:
            sq = st.number_input("m² Επιφάνειας", value=10.0)
        tile_area = (pw * ph) / 10000
        st.metric("Τεμάχια που χρειάζονται", int(sq/tile_area)+1 if tile_area > 0 else 0)
    elif mode == "Γεμίσματα":
        area = st.number_input("m² Δαπέδου", value=10.0)
        thick = st.number_input("Πάχος (cm)", value=5.0)
        vol = area * (thick / 100)
        cem = vol * 6.5
        sand_m3 = vol * 0.9
        r1, r2, r3 = st.columns(3)
        r1.metric("Τσιμέντο (25kg)", f"{int(cem)+1} σάκοι")
        r2.metric("Άμμος (m³)", f"{sand_m3:.2f} m³")
        r3.metric("Άμμος (Τόνοι)", f"{sand_m3 * 1.6:.1f} t")
        st.info(f"💡 Περίπου {int(sand_m3/0.8)+1} Big Bags άμμου.")
    elif mode == "Χρώματα":
        p_m2 = st.number_input("m² Τοίχου", value=50.0)
        st.success(f"🎨 Χρειάζεστε περίπου: {(p_m2 * 2) / 12:.1f} Λίτρα (για 2 χέρια)")

# --- TAB 8: ΑΡΧΕΙΑ ---
with tabs[7]:
    df_f = safe_read("Files")
    with st.expander("➕ Προσθήκη Link Αρχείου"):
        with st.form("form_f", clear_on_submit=True):
            f_d = st.text_input("Περιγραφή Αρχείου")
            f_l = st.text_input("Link (π.χ. Google Drive)")
            if st.form_submit_button("Αποθήκευση Link"):
                new_f = pd.DataFrame([{"Περιγραφή": f_d, "Link": f_l}])
                conn.update(worksheet
