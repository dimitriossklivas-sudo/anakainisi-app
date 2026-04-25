import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIG ---
st.set_page_config(page_title="Methana Earth & Fire", layout="wide")

# --- CSS ΓΙΑ ΤΟ DASHBOARD (ΣΧΕΔΙΟ ΣΟΥ) ---
st.markdown("""
    <style>
    .card-container { background: white; padding: 20px; border-radius: 15px; border: 1px solid #e6e6e6; margin-bottom: 20px; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .card-title { color: #4c3826; font-weight: bold; border-bottom: 2px solid #dec18e; margin-bottom: 10px; }
    .label { font-size: 0.85rem; font-weight: bold; }
    .value { float: right; font-weight: normal; }
    </style>
    """, unsafe_allow_html=True)

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Expenses", ttl=0)
    except:
        return pd.DataFrame(columns=["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"])

# --- DASHBOARD RENDERER ---
def render_dashboard(df):
    st.title("🏗️ Dashboard Ανακαίνισης")
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα για εμφάνιση.")
        return

    # Παράδειγμα για "Υδραυλικά" (Όπως το σχέδιο στο χαρτί)
    cat = "Υδραυλικά"
    budget = 2400.0
    
    # Υπολογισμοί
    subset = df[df['Κατηγορία'] == cat]
    paid = pd.to_numeric(subset['Ποσό'], errors='coerce').sum()
    me = pd.to_numeric(subset[subset['Πληρωτής'] == 'Εγώ']['Ποσό'], errors='coerce').sum()
    fat = pd.to_numeric(subset[subset['Πληρωτής'] == 'Πατέρας']['Ποσό'], errors='coerce').sum()

    st.markdown(f'<div class="card-container"><div class="card-title">ΚΑΡΤΕΛΑ {cat.upper()}</div>', unsafe_allow_html=True)
    st.write(f"ΣΥΝΟΛΟ ΚΑΛΥΜΜΕΝΟ: {paid:,.2f}€ / {budget:,.2f}€")
    st.progress(min(paid/budget, 1.0) if budget > 0 else 0)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"ΕΓΩ: {me:,.2f}€")
        st.progress(min(me/(budget/2), 1.0) if budget > 0 else 0)
    with c2:
        st.write(f"ΠΑΤΕΡΑΣ: {fat:,.2f}€")
        st.progress(min(fat/(budget/2), 1.0) if budget > 0 else 0)
    st.markdown('</div>', unsafe_allow_html=True)

# --- EXPENSES FORM ---
def render_expenses(df):
    st.subheader("💰 Καταχώρηση Νέου Εξόδου")
    
    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Ημερομηνία", datetime.now())
            cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Άλλο"])
            etype = st.selectbox("Είδος", ["Αμοιβή", "Υλικά"])
        with col2:
            amt = st.number_input("Ποσό (€)", min_value=0.0, step=10.0, format="%.2f")
            payer = st.selectbox("Πληρωτής", ["Εγώ", "Πατέρας", "Κοινό"])
            notes = st.text_input("Σημειώσεις")
        
        submit = st.form_submit_button("✅ Αποθήκευση Εξόδου")

        if submit:
            if amt <= 0:
                st.error("Παρακαλώ βάλε ένα ποσό μεγαλύτερο από 0.")
            else:
                # Δημιουργία νέας γραμμής
                new_row = {
                    "_id": str(uuid.uuid4())[:8],
                    "Ημερομηνία": d.strftime("%Y-%m-%d"),
                    "Κατηγορία": cat,
                    "Είδος": etype,
                    "Ποσό": amt,
                    "Πληρωτής": payer,
                    "Σημειώσεις": notes
                }
                
                # Προσθήκη και αποστολή στο Google Sheets
                updated_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                conn.update(worksheet="Expenses", data=updated_df)
                st.success("Το έξοδο καταχωρήθηκε επιτυχώς!")
                st.rerun()

    st.divider()
    st.subheader("📊 Ιστορικό Εξόδων")
    st.dataframe(df.sort_values(by="Ημερομηνία", ascending=False), use_container_width=True)

# --- MAIN NAVIGATION ---
def main():
    df = get_data()
    
    menu = st.sidebar.radio("Μενού", ["🏠 Dashboard", "💰 Έξοδα"])
    
    if menu == "🏠 Dashboard":
        render_dashboard(df)
    else:
        render_expenses(df)

if __name__ == "__main__":
    main()
