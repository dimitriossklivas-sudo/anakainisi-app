import base64
import io
import uuid
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
from streamlit_gsheets import GSheetsConnection

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #fbf6ee; }
    .hero { background: linear-gradient(135deg, #3f2f22, #7a5a3d); color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; }
    div[data-testid="stMetric"] { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ΣΤΑΘΕΡΕΣ & ΟΝΟΜΑΤΑ SHEETS ---
SHEETS = {
    "EXP": "Expenses", "FEE": "Fees", "CON": "Contacts", 
    "MAT": "Materials", "LOAN": "Loan", "TASK": "Progress", "GAL": "Gallery"
}

# --- ΣΥΝΔΕΣΗ & ΔΕΔΟΜΕΝΑ ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(worksheet=sheet_name, ttl="10m")
        return df.dropna(how="all") if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- UTILS ---
def safe_write(sheet_name, df):
    try:
        conn.update(worksheet=sheet_name, data=df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        return False

# --- RENDERERS ---

def render_materials(df_mat):
    st.subheader("📦 Διαχείριση Υλικών")
    with st.expander("➕ Προσθήκη Υλικού"):
        with st.form("mat_form"):
            name = st.text_input("Όνομα Υλικού")
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Άλλο"])
            price = st.number_input("Τιμή Μονάδας", min_value=0.0)
            qty = st.number_input("Ποσότητα", min_value=1)
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"_id": str(uuid.uuid4())[:8], "Υλικό": name, "Κατηγορία": cat, "Σύνολο": price*qty}])
                updated = pd.concat([df_mat, new_row], ignore_index=True)
                if safe_write(SHEETS["MAT"], updated):
                    st.success("Το υλικό προστέθηκε!")
                    st.rerun()
    st.dataframe(df_mat, use_container_width=True)

def render_timeline(df_tasks):
    st.subheader("🗓️ Timeline Εργασιών")
    if not df_tasks.empty and "Ημερομηνία_Έναρξης" in df_tasks.columns:
        fig = px.timeline(df_tasks, x_start="Ημερομηνία_Έναρξης", x_end="Ημερομηνία_Λήξης", y="Εργασία", color="Κατάσταση")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Δεν υπάρχουν δεδομένα για το Timeline.")

def render_loans(df_loan):
    st.subheader("🏦 Δάνεια & Χρηματοδότηση")
    st.dataframe(df_loan, use_container_width=True)

def render_gallery(df_gal):
    st.subheader("📸 Gallery Φωτογραφιών")
    if df_gal.empty:
        st.info("Η Gallery είναι άδεια.")
    else:
        cols = st.columns(3)
        for idx, row in df_gal.iterrows():
            with cols[idx % 3]:
                if "Image_Data" in row and row["Image_Data"]:
                    st.image(f"data:image/jpeg;base64,{row['Image_Data']}", caption=row.get("Τίτλος", ""))

# --- ΚΥΡΙΩΣ ΕΦΑΡΜΟΓΗ ---
def main():
    # Sidebar Menu
    with st.sidebar:
        st.title("Methana Menu")
        choice = st.radio("Επιλέξτε Tab:", ["🏠 Dashboard", "💰 Έξοδα", "📦 Υλικά", "📞 Επαφές", "🏦 Δάνειο", "🗓️ Timeline", "📸 Gallery"])
        if st.button("🔄 Ανανέωση Δεδομένων"):
            st.cache_data.clear()
            st.rerun()

    # Φόρτωση όλων των δεδομένων (Lazy Loading)
    if choice == "🏠 Dashboard":
        df_exp = load_data(SHEETS["EXP"])
        st.markdown('<div class="hero"><h1>Methana Earth & Fire</h1><p>Dashboard Ανακαίνισης</p></div>', unsafe_allow_html=True)
        st.metric("Συνολικά Έξοδα", f"{pd.to_numeric(df_exp['Ποσό'], errors='coerce').sum():,.2f} €" if not df_exp.empty else "0 €")
    
    elif choice == "💰 Έξοδα":
        df_exp = load_data(SHEETS["EXP"])
        # Εδώ θα έμπαινε η render_expenses που φτιάξαμε πριν
        st.dataframe(df_exp)

    elif choice == "📦 Υλικά":
        df_mat = load_data(SHEETS["MAT"])
        render_materials(df_mat)

    elif choice == "📞 Επαφές":
        df_con = load_data(SHEETS["CON"])
        st.dataframe(df_con)

    elif choice == "🏦 Δάνειο":
        df_loan = load_data(SHEETS["LOAN"])
        render_loans(df_loan)

    elif choice == "🗓️ Timeline":
        df_tasks = load_data(SHEETS["TASK"])
        render_timeline(df_tasks)

    elif choice == "📸 Gallery":
        df_gal = load_data(SHEETS["GAL"])
        render_gallery(df_gal)

if __name__ == "__main__":
    main()

