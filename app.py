import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import math

# PAGE CONFIG
st.set_page_config(page_title="Renovation Manager V2", layout="wide")

# STYLE (mobile friendly)
st.markdown("""
<style>
.main { background-color: #f4f6f9; }

div[data-testid="stMetric"] {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    button {
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
    }
}
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Renovation Manager V2")

# CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data
def safe_read(sheet):
    try:
        return conn.read(worksheet=sheet, ttl=0)
    except:
        return pd.DataFrame()

def safe_write(sheet, df):
    conn.update(worksheet=sheet, data=df)

# LOAD DATA
df_exp = safe_read("Expenses")
df_tasks = safe_read("Tasks")
df_off = safe_read("Offers")
df_ln = safe_read("Loan")

# 🔄 DEVICE MODE TOGGLE
mode = st.sidebar.radio("📱 Mode", ["Desktop", "Mobile"])
is_mobile = mode == "Mobile"

# 🧭 MENU
if is_mobile:
    menu = st.selectbox("📂 Μενού", [
        "🏠 Dashboard",
        "💰 Έξοδα",
        "📋 Εργασίες",
        "📊 Αναλύσεις"
    ])
else:
    menu = st.sidebar.radio("📂 Μενού", [
        "🏠 Dashboard",
        "💰 Έξοδα",
        "📋 Εργασίες",
        "📊 Αναλύσεις"
    ])

# =========================
# 🏠 DASHBOARD
# =========================
if menu == "🏠 Dashboard":

    budget = st.number_input("💼 Συνολικό Budget (€)", value=30000)
    spent = df_exp['Ποσό'].sum() if not df_exp.empty else 0

    if is_mobile:
        st.metric("💰 Έξοδα", f"{spent:,.0f} €")
        st.metric("📊 Budget %", f"{(spent/budget*100) if budget else 0:.1f}%")
        st.metric("📉 Υπόλοιπο", f"{budget-spent:,.0f} €")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Έξοδα", f"{spent:,.0f} €")
        col2.metric("📊 Budget %", f"{(spent/budget*100) if budget else 0:.1f}%")
        col3.metric("📉 Υπόλοιπο", f"{budget-spent:,.0f} €")

    if spent > budget:
        st.error("🚨 Έχεις ξεπεράσει το budget!")

    # ALERT καθυστερήσεων
    if not df_tasks.empty and "Ημερομηνία" in df_tasks:
        overdue = df_tasks[pd.to_datetime(df_tasks["Ημερομηνία"], errors='coerce') < pd.Timestamp.today()]
        if not overdue.empty:
            st.warning("⚠️ Έχεις καθυστερημένες εργασίες!")

# =========================
# 💰 ΕΞΟΔΑ
# =========================
elif menu == "💰 Έξοδα":

    st.subheader("💰 Καταγραφή Εξόδων")

    with st.expander("➕ Νέο Έξοδο"):
        with st.form("f_exp", clear_on_submit=True):
            d = st.date_input("Ημερομηνία")
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά","Ηλεκτρολογικά","Πλακάκια","Κουζίνα","Άλλο"])
            amount = st.number_input("Ποσό (€)", min_value=0.0)
            room = st.selectbox("Χώρος", ["Κουζίνα","Μπάνιο","Σαλόνι","Άλλο"])
            payer = st.selectbox("Πληρωτής", ["Εγώ","Πατέρας"])

            if st.form_submit_button("Αποθήκευση"):
                new = pd.DataFrame([{
                    "Ημερομηνία": str(d),
                    "Κατηγορία": cat,
                    "Ποσό": amount,
                    "Χώρος": room,
                    "Πληρωτής": payer
                }])
                df_exp = pd.concat([df_exp, new], ignore_index=True)
                safe_write("Expenses", df_exp)
                st.success("✔ Αποθηκεύτηκε")
                st.rerun()

    # DISPLAY
    if not df_exp.empty:
        if is_mobile:
            for _, row in df_exp.iterrows():
                st.markdown(f"""
                💰 **{row['Ποσό']}€**
                📂 {row['Κατηγορία']}
                📍 {row['Χώρος']}
                👤 {row['Πληρωτής']}
                """)
                st.divider()
        else:
            st.dataframe(df_exp, use_container_width=True)

# =========================
# 📋 ΕΡΓΑΣΙΕΣ
# =========================
elif menu == "📋 Εργασίες":

    st.subheader("📋 Διαχείριση Εργασιών")

    with st.expander("➕ Νέα Εργασία"):
        with st.form("f_task", clear_on_submit=True):
            t = st.text_input("Εργασία")
            status = st.selectbox("Κατάσταση", ["To Do","Doing","Done"])
            deadline = st.date_input("Προθεσμία")
            cost = st.number_input("Κόστος (€)", min_value=0.0)

            if st.form_submit_button("Προσθήκη"):
                new = pd.DataFrame([{
                    "Εργασία": t,
                    "Κατάσταση": status,
                    "Ημερομηνία": str(deadline),
                    "Κόστος": cost
                }])
                df_tasks = pd.concat([df_tasks, new], ignore_index=True)
                safe_write("Tasks", df_tasks)
                st.success("✔ Προστέθηκε")
                st.rerun()

    if not df_tasks.empty:
        for _, row in df_tasks.iterrows():
            if is_mobile:
                st.markdown(f"""
                🔧 **{row['Εργασία']}**
                📌 {row['Κατάσταση']}
                📅 {row['Ημερομηνία']}
                💰 {row['Κόστος']} €
                """)
                st.divider()
            else:
                st.markdown(f"""
                🔧 **{row['Εργασία']}**
                - Κατάσταση: {row['Κατάσταση']}
                - Προθεσμία: {row['Ημερομηνία']}
                - Κόστος: {row['Κόστος']} €
                """)
# =========================
# 📊 ΑΝΑΛΥΣΕΙΣ
# =========================
elif menu == "📊 Αναλύσεις":

    st.subheader("📊 Αναλύσεις")

    if not df_exp.empty:
        if is_mobile:
            st.bar_chart(df_exp.groupby("Κατηγορία")["Ποσό"].sum())
        else:
            c1, c2 = st.columns(2)
            c1.bar_chart(df_exp.groupby("Κατηγορία")["Ποσό"].sum())

            if "Χώρος" in df_exp:
                c2.bar_chart(df_exp.groupby("Χώρος")["Ποσό"].sum())

# =========================
# ⚙️ EXTRA MENU
# =========================
if is_mobile:
    menu2 = st.selectbox("⚙️ Extra", [
        "💼 Προσφορές",
        "🏦 Δάνειο",
        "🧮 Calculator",
        "📁 Αρχεία"
    ])
else:
    menu2 = st.sidebar.radio("⚙️ Extra", [
        "💼 Προσφορές",
        "🏦 Δάνειο",
        "🧮 Calculator",
        "📁 Αρχεία"
    ])

# =========================
# 💼 ΠΡΟΣΦΟΡΕΣ
# =========================
if menu2 == "💼 Προσφορές":

    st.subheader("💼 Προσφορές")

    with st.expander("➕ Νέα Προσφορά"):
        with st.form("f_off"):
            p = st.text_input("Πάροχος")
            d = st.text_input("Περιγραφή")
            a = st.number_input("Ποσό (€)", min_value=0.0)

            if st.form_submit_button("Αποθήκευση"):
                new = pd.DataFrame([{"Πάροχος": p, "Περιγραφή": d, "Ποσό": a}])
                df_off = pd.concat([df_off, new], ignore_index=True)
                safe_write("Offers", df_off)
                st.success("✔ Αποθηκεύτηκε")
                st.rerun()

    if not df_off.empty:
        best = df_off.sort_values("Ποσό").iloc[0]
        st.success(f"🏆 Καλύτερη προσφορά: {best['Πάροχος']} - {best['Ποσό']}€")

        if is_mobile:
            for _, row in df_off.iterrows():
                st.markdown(f"""
                🏢 **{row['Πάροχος']}**
                💰 {row['Ποσό']} €
                📝 {row['Περιγραφή']}
                """)
                st.divider()
        else:
            st.dataframe(df_off)

# =========================
# 🏦 ΔΑΝΕΙΟ
# =========================
elif menu2 == "🏦 Δάνειο":

    st.subheader("🏦 Υπολογισμός Δανείου")

    P = st.number_input("Ποσό Δανείου (€)")
    r = st.number_input("Επιτόκιο (%)") / 100 / 12
    n = st.number_input("Μήνες")

    if P and r and n:
        installment = P * (r*(1+r)**n)/((1+r)**n - 1)
        st.metric("Μηνιαία δόση", f"{installment:.2f} €")

# =========================
# 🧮 CALCULATOR
# =========================
elif menu2 == "🧮 Calculator":

    st.subheader("🧮 Υπολογισμοί")

    mode_calc = st.selectbox("Επιλογή", ["Πλακάκια","Γεμίσματα","Χρώματα"])

    if mode_calc == "Πλακάκια":
        w = st.number_input("cm πλάτος", value=60.0)
        h = st.number_input("cm ύψος", value=120.0)
        sq = st.number_input("m²", value=10.0)
        st.metric("Τεμάχια", int(sq/((w*h)/10000))+1)

    elif mode_calc == "Γεμίσματα":
        a = st.number_input("m²", value=10.0)
        t = st.number_input("cm", value=5.0)
        v = a * (t/100)
        st.metric("Τσιμέντα", int(v*6.5)+1)

    elif mode_calc == "Χρώματα":
        m2 = st.number_input("m²", value=50.0)
        st.success(f"🎨 {(m2*2)/12:.1f} L")

# =========================
# 📁 ΑΡΧΕΙΑ
# =========================
elif menu2 == "📁 Αρχεία":

    st.subheader("📁 Αρχεία")

    file = st.file_uploader("Ανέβασε αρχείο")

    if file:
        st.success("✔ Το αρχείο ανέβηκε (preview)")
        st.write(file.name)
