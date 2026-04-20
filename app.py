import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Renovation Manager V2", layout="wide")

st.markdown("""
<style>
.main { background-color: #f4f6f9; }
div[data-testid="stMetric"] {
    background-color: #ffffff;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.1);
    border-left: 5px solid #D4AF37;
}
</style>
""", unsafe_allow_html=True)

st.title("🏗️ Renovation Manager V2")

conn = st.connection("gsheets", type=GSheetsConnection)

def safe_read(sheet):
    try:
        data = conn.read(worksheet=sheet, ttl=0)
        if data is None or data.empty:
            return pd.DataFrame()
        return data.dropna(how="all")
    except Exception:
        return pd.DataFrame()

def safe_write(sheet, df):
    try:
        conn.update(worksheet=sheet, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης: {e}")
        return False

df_exp = safe_read("Expenses")
df_tasks = safe_read("Tasks")
df_off = safe_read("Offers")

options = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "📋 Εργασίες",
    "📊 Αναλύσεις",
    "💼 Προσφορές",
    "🏦 Δάνειο",
    "🧮 Calculator"
]
menu = st.sidebar.radio("📂 Μενού", options)

if menu == "🏠 Dashboard":
    budget = st.number_input("💼 Συνολικό Budget (€)", value=30000.0)

    spent = 0.0
    if not df_exp.empty and "Ποσό" in df_exp.columns:
        spent = pd.to_numeric(df_exp["Ποσό"], errors="coerce").fillna(0).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Έξοδα", f"{spent:,.2f} €")
    c2.metric("📊 Budget %", f"{(spent / budget * 100) if budget > 0 else 0:.1f}%")
    c3.metric("📉 Υπόλοιπο", f"{budget - spent:,.2f} €")

elif menu == "💰 Έξοδα":
    st.subheader("💰 Καταγραφή Εξόδων")
    with st.expander("➕ Νέο Έξοδο"):
        with st.form("f_exp", clear_on_submit=True):
            d = st.date_input("Ημερομηνία")
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Άλλο"])
            amount = st.number_input("Ποσό (€)", min_value=0.0)
            payer = st.selectbox("Πληρωτής", ["Εγώ", "Πατέρας"])

            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{
                    "Ημερομηνία": str(d),
                    "Κατηγορία": cat,
                    "Ποσό": amount,
                    "Πληρωτής": payer
                }])
                df_updated = pd.concat([df_exp, new_row], ignore_index=True)
                if safe_write("Expenses", df_updated):
                    st.success("✔ Αποθηκεύτηκε!")
                    st.rerun()

    if not df_exp.empty:
        st.dataframe(df_exp, use_container_width=True)

elif menu == "📋 Εργασίες":
    st.subheader("📋 Διαχείριση Εργασιών")
    with st.expander("➕ Νέα Εργασία"):
        with st.form("f_task", clear_on_submit=True):
            t = st.text_input("Εργασία")
            status = st.selectbox("Κατάσταση", ["To Do", "Doing", "Done"])
            cost = st.number_input("Εκτιμώμενο Κόστος (€)", min_value=0.0)

            if st.form_submit_button("Προσθήκη"):
                new_row = pd.DataFrame([{
                    "Εργασία": t,
                    "Κατάσταση": status,
                    "Κόστος": cost
                }])
                df_updated = pd.concat([df_tasks, new_row], ignore_index=True)
                if safe_write("Tasks", df_updated):
                    st.success("✔ Προστέθηκε!")
                    st.rerun()

    if not df_tasks.empty:
        st.dataframe(df_tasks, use_container_width=True)

elif menu == "📊 Αναλύσεις":
    st.subheader("📊 Αναλύσεις")

    if not df_exp.empty and "Κατηγορία" in df_exp.columns and "Ποσό" in df_exp.columns:
        df_chart = df_exp.copy()
        df_chart["Ποσό"] = pd.to_numeric(df_chart["Ποσό"], errors="coerce").fillna(0)
        grouped = df_chart.groupby("Κατηγορία", as_index=False)["Ποσό"].sum()
        st.bar_chart(grouped.set_index("Κατηγορία"))
    else:
        st.info("Δεν υπάρχουν ακόμη αρκετά δεδομένα για ανάλυση.")

elif menu == "💼 Προσφορές":
    st.subheader("💼 Προσφορές")

    with st.expander("➕ Νέα Προσφορά"):
        with st.form("f_off", clear_on_submit=True):
            p = st.text_input("Πάροχος")
            d_off = st.text_input("Περιγραφή")
            a_off = st.number_input("Ποσό (€)", min_value=0.0)

            if st.form_submit_button("Αποθήκευση Προσφοράς"):
                new_row = pd.DataFrame([{
                    "Πάροχος": p,
                    "Περιγραφή": d_off,
                    "Ποσό": a_off
                }])
                df_updated = pd.concat([df_off, new_row], ignore_index=True)
                if safe_write("Offers", df_updated):
                    st.success("✔ Η προσφορά αποθηκεύτηκε!")
                    st.rerun()

    if not df_off.empty:
        if "Ποσό" in df_off.columns and "Πάροχος" in df_off.columns:
            df_off_display = df_off.copy()
            df_off_display["Ποσό"] = pd.to_numeric(df_off_display["Ποσό"], errors="coerce")
            df_off_display = df_off_display.dropna(subset=["Ποσό"])

            if not df_off_display.empty:
                best = df_off_display.sort_values("Ποσό", ascending=True).iloc[0]
                st.info(f"🏆 Καλύτερη προσφορά: {best['Πάροχος']} ({best['Ποσό']:.2f}€)")

        st.dataframe(df_off, use_container_width=True)

elif menu == "🧮 Calculator":
    st.subheader("🧮 Υπολογισμοί")
    calc_type = st.selectbox("Τύπος", ["Πλακάκια", "Χρώματα"])

    if calc_type == "Πλακάκια":
        sq = st.number_input("m² Επιφάνειας", value=10.0)
        w = st.number_input("Πλάτος πλακιδίου (cm)", value=60.0)
        h = st.number_input("Ύψος πλακιδίου (cm)", value=120.0)

        if w > 0 and h > 0:
            total = int(sq / ((w * h) / 10000)) + 1
            st.metric("Τεμάχια που θα χρειαστείς", total)

    elif calc_type == "Χρώματα":
        sq_wall = st.number_input("m² Τοίχου", value=50.0)
        liters = (sq_wall * 2) / 12
        st.success(f"🎨 Θα χρειαστείς περίπου {liters:.1f} λίτρα χρώμα.")

elif menu == "🏦 Δάνειο":
    st.subheader("🏦 Υπολογιστής Δόσης")
    p_loan = st.number_input("Κεφάλαιο (€)", value=10000.0)
    r_loan = st.number_input("Ετήσιο Επιτόκιο (%)", value=4.5) / 100 / 12
    n_loan = st.number_input("Μήνες Εξόφλησης", value=60)

    if p_loan > 0 and n_loan > 0:
        if r_loan > 0:
            inst = p_loan * (r_loan * (1 + r_loan) ** n_loan) / ((1 + r_loan) ** n_loan - 1)
        else:
            inst = p_loan / n_loan
        st.metric("Μηνιαία Δόση", f"{inst:.2f} €")
