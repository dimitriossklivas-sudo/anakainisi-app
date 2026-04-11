import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px # Για πιο επαγγελματικά γραφήματα

# Ρυθμίσεις σελίδας
st.set_page_config(page_title="Renovation Pro | Σκλίβας Δημήτριος", layout="wide", page_icon="🏗️")

# Custom CSS για το Logo και την αισθητική
st.markdown("""
    <style>
    .main-title {
        font-size: 40px;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 18px;
        text-align: center;
        color: #6B7280;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

# Logo / Ονοματεπώνυμο
st.markdown('<p class="main-title">ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Project: Διαχείριση Ανακαίνισης v2.0</p>', unsafe_allow_html=True)

# Δημιουργία φακέλων
if not os.path.exists("receipts"):
    os.makedirs("receipts")

FILE_NAME = "expenses_pro_v2.csv"

# Φόρτωση δεδομένων
if os.path.exists(FILE_NAME):
    df = pd.read_csv(FILE_NAME)
    df["Ποσό (€)"] = pd.to_numeric(df["Ποσό (€)"], errors='coerce')
else:
    df = pd.DataFrame(columns=["ID", "Ημερομηνία", "Περιγραφή", "Κατηγορία", "Ποσό (€)", "Πληρωμή από", "Αρχείο"])

# --- SIDEBAR: ΡΥΘΜΙΣΕΙΣ & ΕΙΣΑΓΩΓΗ ---
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις Έργου")
    budget_limit = st.number_input("Συνολικό Όριο Χρημάτων (€)", min_value=1000, value=20000, step=500)
    
    st.divider()
    st.header("➕ Νέα Καταχώρηση")
    with st.form("pro_form", clear_on_submit=True):
        date = st.date_input("Ημερομηνία", datetime.now())
        desc = st.text_input("Περιγραφή / Προμηθευτής")
        cat = st.selectbox("Κατηγορία", ["Οικοδομικά", "Υδραυλικά", "Ηλεκτρολογικά", "Μπάνιο/Πλακάκια", "Κουζίνα", "Αλουμίνια", "Βάψιμο", "Φωτισμός", "Έπιπλα", "Άλλο"])
        amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
        payer = st.radio("Ποιος πλήρωσε;", ["Εγώ", "Πατέρας"])
        uploaded_file = st.file_uploader("📷 Απόδειξη", type=['png', 'jpg', 'jpeg', 'pdf'])
        submit = st.form_submit_button("✅ Αποθήκευση")

if submit and desc and amount > 0:
    file_path = "Δεν υπάρχει"
    if uploaded_file is not None:
        file_path = os.path.join("receipts", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    new_data = pd.DataFrame([{
        "ID": datetime.now().strftime("%H%M%S"),
        "Ημερομηνία": str(date),
        "Περιγραφή": desc,
        "Κατηγορία": cat,
        "Ποσό (€)": amount,
        "Πληρωμή από": payer,
        "Αρχείο": file_path
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    st.rerun()

# --- ΚΕΝΤΡΟ ΕΛΕΓΧΟΥ (DASHBOARD) ---
if not df.empty:
    total_spent = df["Ποσό (€)"].sum()
    remaining = budget_limit - total_spent
    progress = min(total_spent / budget_limit, 1.0)

    # 1. Budget Progress Bar
    st.subheader(f"📊 Πρόοδος Προϋπολογισμού (Όριο: {budget_limit:,.0f}€)")
    col_b1, col_b2 = st.columns([4, 1])
    with col_b1:
        st.progress(progress)
    with col_b2:
        st.write(f"**{progress*100:.1f}%**")
    
    if total_spent > budget_limit:
        st.error(f"⚠️ Έχετε υπερβεί το όριο κατά {total_spent - budget_limit:,.2f} €!")
    else:
        st.info(f"💡 Υπόλοιπο μέχρι το όριο: {remaining:,.2f} €")

    st.divider()

    # 2. Σύγκριση Εγώ vs Πατέρας (Σχεδιαγράμματα)
    st.subheader("⚖️ Κέντρο Ελέγχου Στατιστικών")
    col_stat1, col_stat2 = st.columns(2)

    with col_stat1:
        st.markdown("### Ποιος έχει πληρώσει τι")
        fig_payer = px.pie(df, values='Ποσό (€)', names='Πληρωμή από', hole=0.4,
                           color_discrete_sequence=['#1E3A8A', '#3B82F6'])
        st.plotly_chart(fig_payer, use_container_width=True)

    with col_stat2:
        st.markdown("### Έξοδα ανά Κατηγορία")
        fig_cat = px.bar(df.groupby("Κατηγορία")["Ποσό (€)"].sum().reset_index(), 
                         x='Κατηγορία', y='Ποσό (€)', color='Κατηγορία')
        st.plotly_chart(fig_cat, use_container_width=True)

    st.divider()

    # 3. Φίλτρα & Πίνακας
    st.subheader("📑 Αναλυτικό Αρχείο Εργασιών")
    search_query = st.text_input("🔍 Αναζήτηση στις περιγραφές...")
    
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df['Περιγραφή'].str.contains(search_query, case=False)]
    
    st.dataframe(filtered_df.sort_values("Ημερομηνία", ascending=False), use_container_width=True)

    # 4. Προβολή Αποδείξεων
    st.divider()
    st.subheader("📸 Ψηφιακό Αρχείο Αποδείξεων")
    has_files = df[df["Αρχείο"] != "Δεν υπάρχει"]
    if not has_files.empty:
        selected = st.selectbox("Επιλογή εξόδου για εμφάνιση εγγράφου:", has_files["Περιγραφή"] + " - " + has_files["Ποσό (€)"].astype(str) + "€")
        img_path = has_files[has_files["Περιγραφή"] + " - " + has_files["Ποσό (€)"].astype(str) + "€" == selected]["Αρχείο"].values[0]
        if img_path.endswith('.pdf'):
            st.warning("Το αρχείο είναι PDF και δεν μπορεί να προβληθεί απευθείας. Βρίσκεται αποθηκευμένο στο σύστημα.")
        else:
            st.image(img_path, use_container_width=True)
    
else:
    st.info("👋 Καλώς ορίσατε κ. Σκλίβα. Συμπληρώστε την πρώτη δαπάνη στο μενού αριστερά.")
