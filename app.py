import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
import os

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Σκλίβας Δημήτριος | v4.6", layout="wide", page_icon="🏠")

# --- ΕΜΦΑΝΙΣΗ LOGO ---
logo_files = ["logo.png", "Logo.png", "logo.jpg"]
found_logo = False
for f in logo_files:
    if os.path.exists(f):
        st.image(f, width=200)
        found_logo = True
        break
if not found_logo:
    st.markdown("<h1 style='color: #D4AF37;'>ΣΚΛΙΒΑΣ ΔΗΜΗΤΡΙΟΣ</h1>", unsafe_allow_html=True)

# --- ΣΥΝΔΕΣΗ ΜΕ GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Συναρτήση για ασφαλή ανάγνωση
def safe_read(sheet_name):
    try:
        return conn.read(worksheet=sheet_name, ttl="0")
    except:
        return pd.DataFrame()

# Αντικατάστησε τη γραμμή των tabs με αυτή:
tabs = st.tabs([
    "📊 Στατιστικά", 
    "👷 Συνεργεία", 
    "📈 Πρόοδος", 
    "💰 Προσφορές", 
    "🏦 Δάνειο", 
    "📝 Ιστορικό", 
    "📐 Calculator", 
    "📁 Αρχεία"
])

# 1. ΕΞΟΔΑ & ΣΤΑΤΙΣΤΙΚΑ
with tabs[0]:
    df_exp = safe_read("Expenses")
    if not df_exp.empty:
        df_exp.columns = df_exp.columns.str.strip()
        m1, m2, m3 = st.columns(3)
        total_val = df_exp['Ποσό'].sum()
        ego_val = df_exp[df_exp['Πληρωτής'] == "Εγώ"]['Ποσό'].sum()
        father_val = df_exp[df_exp['Πληρωτής'] == "Πατέρας"]['Ποσό'].sum()
        
        m1.metric("Συνολικά Έξοδα", f"{total_val:,.2f} €")
        m2.metric("Πληρωμές (Εγώ)", f"{ego_val:,.2f} €")
        m3.metric("Πληρωμές (Πατέρας)", f"{father_val:,.2f} €")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df_exp, values='Ποσό', names='Κατηγορία', title="Κατανομή ανά Εργασία", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(df_exp, x='Κατηγορία', y='Ποσό', color='Πληρωτής', 
                             title="Πληρωμές ανά Άτομο", barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("➕ Καταχώρηση Νέου Εξόδου"):
        with st.form("new_exp_v55", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                e_date = st.date_input("Ημερομηνία")
                e_cat = st.selectbox("Κατηγορία", ["Υδραυλικά", "Οικοδομικά", "Ηλεκτρολογικά", "Κουζίνα", "Μόνωση", "Άλλο"])
                e_type = st.radio("Είδος", ["Αμοιβή", "Υλικά"], horizontal=True)
            with col_f2:
                e_amt = st.number_input("Ποσό (€)", min_value=0.0)
                e_payer = st.radio("Πληρωτής", ["Εγώ", "Πατέρας"], horizontal=True)
            e_desc = st.text_input("Περιγραφή")
            if st.form_submit_button("Αποθήκευση"):
                new_row = pd.DataFrame([{"Ημερομηνία": str(e_date), "Περιγραφή": e_desc, "Κατηγορία": e_cat, 
                                          "Ποσό": e_amt, "Πληρωτής": e_payer, "Είδος": e_type}])
                conn.update(worksheet="Expenses", data=pd.concat([df_exp, new_row], ignore_index=True))
                st.rerun()

# 2. ΣΥΝΕΡΓΕΙΑ
with tabs[1]:
    df_c = safe_read("Contacts")
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)

# --- 3. ΠΡΟΟΔΟΣ (Προσθήκη Νέων Εργασιών) ---
with tabs[2]:
    st.subheader("📦 Εξέλιξη & Οικονομική Εξόφληση")
    df_p = safe_read("Progress")
    df_e = safe_read("Expenses")
    
    # --- ΦΟΡΜΑ ΠΡΟΣΘΗΚΗΣ ΝΕΑΣ ΕΡΓΑΣΙΑΣ ---
    with st.expander("➕ Προσθήκη Νέας Εργασίας"):
        with st.form("new_task_form", clear_on_submit=True):
            nt_name = st.text_input("Όνομα Εργασίας (π.χ. Πλακάκια)")
            nt_deal = st.number_input("Συνολική Συμφωνημένη Αμοιβή (€)", min_value=0.0)
            nt_status = st.selectbox("Κατάσταση", ["Εκκρεμεί", "Σε εξέλιξη", "Ολοκληρώθηκε"])
            
            if st.form_submit_button("Προσθήκη στο Πρόγραμμα"):
                if nt_name:
                    # Δημιουργία νέας γραμμής
                    new_task = pd.DataFrame([{
                        "Εργασία": nt_name, 
                        "Κατάσταση": nt_status, 
                        "Συνολική Αμοιβή": nt_deal
                    }])
                    # Ενημέρωση Google Sheets
                    updated_p = pd.concat([df_p, new_task], ignore_index=True)
                    conn.update(worksheet="Progress", data=updated_p)
                    st.success(f"Η εργασία '{nt_name}' προστέθηκε με επιτυχία!")
                    st.rerun()
                else:
                    st.error("Παρακαλώ συμπληρώστε το όνομα της εργασίας.")

    st.divider()

    # --- ΕΜΦΑΝΙΣΗ ΥΠΑΡΧΟΥΣΩΝ ΕΡΓΑΣΙΩΝ ---
    if not df_p.empty:
        # Καθαρισμός δεδομένων εξόδων για τη σύνδεση
        if not df_e.empty:
            df_e.columns = df_e.columns.str.strip()
            df_e['Κατηγορία'] = df_e['Κατηγορία'].astype(str).str.strip()
            if 'Είδος' in df_e.columns:
                df_e['Είδος'] = df_e['Είδος'].astype(str).str.strip()

        for i, r in df_p.iterrows():
            t_name = str(r['Εργασία']).strip()
            p_done = 0
            
            # Υπολογισμός πληρωμών αμοιβών
            if not df_e.empty and 'Είδος' in df_e.columns:
                mask = (df_e['Κατηγορία'] == t_name) & (df_e['Είδος'].isin(["Αμοιβή", "Αμοιβές"]))
                p_done = df_e[mask]['Ποσό'].sum()
            
            total_agr = r['Συνολική Αμοιβή'] if 'Συνολική Αμοιβή' in r else 0
            perc = (p_done / total_agr) if total_agr > 0 else 0
            
            # Οπτική απεικόνιση
            st.write(f"### {t_name}")
            col_t, col_m = st.columns([3, 1])
            with col_t:
                st.progress(min(perc, 1.0))
                st.write(f"💰 Πληρώθηκαν: **{p_done:,.2f} €** / Συμφωνία: {total_agr:,.2f} €")
            with col_m:
                st.metric("Εξόφληση", f"{perc*100:.1f}%")
                if r['Κατάσταση'] != "Ολοκληρώθηκε":
                    if st.button("✅ Ολοκλήρωση", key=f"btn_p_{i}"):
                        df_p.at[i, 'Κατάσταση'] = "Ολοκληρώθηκε"
                        conn.update(worksheet="Progress", data=df_p)
                        st.rerun()
                else:
                    st.success("Ολοκληρώθηκε")
            st.divider()
    else:
        st.info("Η λίστα εργασιών είναι κενή.")
# 4. ΠΡΟΣΦΟΡΕΣ
with tabs[3]:
    df_o = safe_read("Offers")
    if not df_o.empty:
        st.dataframe(df_o, use_container_width=True)
    else:
        st.info("Δεν βρέθηκαν δεδομένα στις Προσφορές.")

# 5. ΔΑΝΕΙΟΔΟΤΗΣΗ
with tabs[4]:
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)

# 6. ΛΙΣΤΑ ΕΞΟΔΩΝ (ΝΕΑ ΚΑΤΗΓΟΡΙΑ)
with tabs[5]:
    st.subheader("📝 Αναλυτικό Ιστορικό Εξόδων")
    df_list = safe_read("Expenses")
    if not df_list.empty:
        # Καθαρισμός στηλών
        df_list.columns = df_list.columns.str.strip()
        
        st.write("💡 *Κάντε κλικ στις επικεφαλίδες των στηλών για ταξινόμηση.*")
        
        # Χρήση st.dataframe για διαδραστικότητα (sorting/filtering)
        st.dataframe(
            df_list, 
            use_container_width=True,
            column_order=("Ημερομηνία", "Κατηγορία", "Είδος", "Περιγραφή", "Ποσό", "Πληρωτής")
        )
    else:
        st.info("Η λίστα είναι κενή.")
    df_l = safe_read("Loan")
    if not df_l.empty:
        st.metric("Υπόλοιπο Δανείου", f"{df_l['Υπόλοιπο Δανείου'].iloc[-1]:,.2f} €")
        st.dataframe(df_l, use_container_width=True)

# --- 7. ΥΠΟΛΟΓΙΣΤΗΣ ΥΛΙΚΩΝ (ΝΕΟ ΤΑΒ) ---
with tabs[6]: # Βεβαιώσου ότι έχεις προσθέσει το όνομα στο st.tabs() παραπάνω
    st.subheader("📐 Έξυπνος Υπολογιστής Υλικών")
    
    calc_type = st.selectbox("Επιλέξτε τι θέλετε να υπολογίσετε:", 
                             ["Πλακάκια & Δάπεδα", "Χρώματα & Βάψιμο", "Υλικά Γεμίσματος (Τσιμέντο/Άμμος)"])
    
    st.divider()
    
    if calc_type == "Πλακάκια & Δάπεδα":
        col1, col2 = st.columns(2)
        with col1:
            area = st.number_input("Επιφάνεια προς κάλυψη (m²)", min_value=0.0, value=20.0)
            waste = st.slider("Ποσοστό Φύρας (για κοψίματα %)", 0, 20, 10)
        with col2:
            box_m2 = st.number_input("Τετραγωνικά ανά κουτί (m²/box)", min_value=0.1, value=1.44)
        
        total_m2 = area * (1 + waste/100)
        boxes_needed = total_m2 / box_m2
        
        st.info(f"📍 Θα χρειαστείτε συνολικά **{total_m2:.2f} m²** υλικού.")
        st.success(f"📦 Παραγγελία: **{int(boxes_needed) + (boxes_needed % 1 > 0)} Κουτιά**")

    elif calc_type == "Χρώματα & Βάψιμο":
        col1, col2 = st.columns(2)
        with col1:
            wall_area = st.number_input("Συνολική επιφάνεια τοίχων (m²)", min_value=0.0, value=50.0)
            hands = st.radio("Πόσα χέρια βάψιμο;", [1, 2, 3], index=1)
        with col2:
            coverage = st.number_input("Απόδοση χρώματος (m²/λίτρο)", min_value=1.0, value=12.0)
        
        total_liters = (wall_area * hands) / coverage
        st.info(f"🎨 Συνολική επιφάνεια προς κάλυψη (με τα χέρια): **{wall_area * hands:.2f} m²**")
        st.success(f"🛢️ Θα χρειαστείτε περίπου **{total_liters:.1f} Λίτρα** χρώματος.")

    elif calc_type == "Υλικά Γεμίσματος (Τσιμέντο/Άμμος)":
        st.write("Υπολογισμός για γέμισμα δαπέδου (αναλογία 1:4)")
        col1, col2 = st.columns(2)
        with col1:
            floor_m2 = st.number_input("Επιφάνεια δαπέδου (m²)", min_value=0.0, value=30.0)
            thickness = st.number_input("Πάχος γεμίσματος (εκατοστά - cm)", min_value=1.0, value=5.0)
        
        volume = floor_m2 * (thickness / 100) # κυβικά μέτρα
        cement_bags = volume * 6 # κατά προσέγγιση 6 τσουβάλια ανά m3 για απλό γέμισμα
        sand_m3 = volume * 0.9
        
        st.info(f"🏗️ Συνολικός όγκος: **{volume:.2f} m³**")
        st.success(f"🧱 Θα χρειαστείτε περίπου **{int(cement_bags)} τσουβάλια τσιμέντο** (25kg) και **{sand_m3:.2f} m³ άμμο**.")
