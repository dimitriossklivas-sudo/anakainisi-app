import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. PAGE CONFIG
st.set_page_config(page_title="Σκλίβας Δημήτριος | Dashboard", layout="wide")

# CSS STYLE
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab"] {
        height: 55px; background-color: #ffffff; border-radius: 10px 10px 0px 0px;
        padding: 10px 15px; font-weight: 600; color: #495057;
    }
    .stTabs [aria-selected="true"] { background-color: #D4AF37 !important; color: white !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff !important; padding: 20px; border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.1); border-left: 5px solid #D4AF37;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #D4AF37;'>👑 ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet):
    try: return conn.read(worksheet=sheet, ttl="0")
    except: return pd.DataFrame()

# TABS
tabs = st.tabs(["📊 Στατιστικά", "👷 Συνεργεία", "📈 Πρόοδος", "💰 Προσφορές", "🏦 Δάνειο", "📝 Ιστορικό", "📐 Calculator", "📁 Αρχεία"])

# TAB 1: STATISTICS
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        m1.metric("Συνολικά Έξοδα", f"{df_exp['Ποσό'].sum():,.2f} €")
        m2.metric("Εγώ", f"{df_exp[df_exp['Πληρωτής'] == 'Εγώ']['Ποσό'].sum():,.2f} €")
        m3.metric("Πατέρας", f"{df_exp[df_exp['Πληρωτής'] == 'Πατέρας']['Ποσό'].sum():,.2f} €")
    with st.expander("➕ Νέο Έξοδο"):
        with st.form("f_exp", clear_on_submit=True):
            e_d = st.date_input("Ημερομηνία")
            e_c = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Πλακάκια", "Άλλο"])
            e_a = st.number_input("Ποσό (€)", min_value=0.0)
            e_p = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            e_t = st.radio("Είδος", ["Αμοιβή", "Υλικά"], horizontal=True)
            if st.form_submit_button("Αποθήκευση"):
                new = pd.DataFrame([{"Ημερομηνία": str(e_d), "Κατηγορία": e_c, "Ποσό": e_a, "Πληρωτής": e_p, "Είδος": e_t}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new], ignore_index=True))
                st.rerun()

# TAB 2: CONTACTS
with tabs[1]:
    df_con = safe_read("Contacts")
    with st.expander("➕ Νέα Επαφή"):
        with st.form("f_con", clear_on_submit=True):
            n = st.text_input("Όνομα")
            j = st.text_input("Ειδικότητα")
            p = st.text_input("Τηλέφωνο")
            if st.form_submit_button("Προσθήκη Επαφής"):
                new_c = pd.DataFrame([{"Όνομα": n, "Ειδικότητα": j, "Τηλέφωνο": p}])
                conn.update(worksheet="Contacts", data=pd.concat([df_con, new_c], ignore_index=True))
                st.rerun()
    st.dataframe(df_con, use_container_width=True)

# TAB 3: PROGRESS
with tabs[2]:
    df_pr = safe_read("Progress")
    df_ex = safe_read("Expenses")
    if not df_pr.empty:
        for _, r in df_pr.iterrows():
            t = str(r['Εργασία']).strip()
            paid = df_ex[(df_ex['Κατηγορία'] == t) & (df_ex['Είδος'] == "Αμοιβή")]['Ποσό'].sum() if not df_ex.empty else 0
            total = r['Συνολική Αμοιβή']
            perc = min(paid/total, 1.0) if total > 0 else 0
            st.write(f"**{t}**")
            st.progress(perc)
            st.caption(f"{perc*100:.1f}% ({paid:,.2f} / {total:,.2f} €)")
    with st.expander("➕ Νέα Εργασία"):
        with st.form("f_pr", clear_on_submit=True):
            pr_t = st.text_input("Εργασία")
            pr_a = st.number_input("Ποσό Συμφωνίας (€)", min_value=0.0)
            if st.form_submit_button("Προσθήκη"):
                new_p = pd.DataFrame([{"Εργασία": pr_t, "Συνολική Αμοιβή": pr_a}])
                conn.update(worksheet="Progress", data=pd.concat([df_pr, new_p], ignore_index=True))
                st.rerun()
# TAB 4: OFFERS
with tabs[3]:
    df_off = safe_read("Offers")
    with st.expander("➕ Νέα Προσφορά"):
        with st.form("f_off", clear_on_submit=True):
            o_p = st.text_input("Πάροχος")
            o_d = st.text_input("Περιγραφή")
            o_a = st.number_input("Ποσό (€)", min_value=0.0)
            if st.form_submit_button("OK"):
                new_o = pd.DataFrame([{"Πάροχος": o_p, "Περιγραφή": o_d, "Ποσό": o_a}])
                conn.update(worksheet="Offers", data=pd.concat([df_off, new_o], ignore_index=True))
                st.rerun()
    st.dataframe(df_off, use_container_width=True)

# TAB 5: LOAN
with tabs[4]:
    df_ln = safe_read("Loan")
    if not df_ln.empty: st.metric("Υπόλοιπο Δανείου", f"{df_ln['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
    with st.expander("➕ Ενημέρωση"):
        with st.form("f_ln", clear_on_submit=True):
            l_p = st.number_input("Πληρωμή (€)", min_value=0.0)
            l_u = st.number_input("Νέο Υπόλοιπο (€)", min_value=0.0)
            if st.form_submit_button("Update"):
                new_l = pd.DataFrame([{"Ποσό Δόσης": l_p, "Υπόλοιπο Δανείου": l_u}])
                conn.update(worksheet="Loan", data=pd.concat([df_ln, new_l], ignore_index=True))
                st.rerun()

# TAB 6: HISTORY
with tabs[5]:
    st.dataframe(safe_read("Expenses"), use_container_width=True)

# TAB 7: CALCULATOR
with tabs[6]:
    mode = st.radio("Υπολογισμός για:", ["Πλακάκια", "Γεμίσματα", "Χρώματα"], horizontal=True)
    if mode == "Πλακάκια":
        w = st.number_input("Πλάτος (cm)", value=60.0)
        h = st.number_input("Ύψος (cm)", value=120.0)
        sq = st.number_input("m² Επιφάνειας", value=10.0)
        st.metric("Τεμάχια", int(sq/((w*h)/10000))+1)
    elif mode == "Γεμίσματα":
        a = st.number_input("m²", value=10.0)
        t = st.number_input("cm", value=5.0)
        v = a * (t/100)
        c1, c2, c3 = st.columns(3)
        c1.metric("Τσιμέντα (25kg)", f"{int(v*6.5)+1}")
        c2.metric("Άμμος (m³)", f"{v*0.9:.2f}")
        c3.metric("Άμμος (Τόνοι)", f"{(v*0.9)*1.6:.1f}")
    elif mode == "Χρώματα":
        m2 = st.number_input("m² Τοίχου", value=50.0)
        st.success(f"🎨 Λίτρα (2 χέρια): {(m2*2)/12:.1f} L")

# TAB 8: FILES
with tabs[7]:
    df_fl = safe_read("Files")
    with st.expander("➕ Νέο Link"):
        with st.form("f_fl", clear_on_submit=True):
            f_n = st.text_input("Περιγραφή")
            f_l = st.text_input("Link")
            if st.form_submit_button("Save"):
                new_f = pd.DataFrame([{"Περιγραφή": f_n, "Link": f_l}])
                conn.update(worksheet="Files", data=pd.concat([df_fl, new_f], ignore_index=True))
                st.rerun()
    st.dataframe(df_fl, use_container_width=True)
