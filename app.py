import uuid
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Renovation Manager V3", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(212,175,55,0.10), transparent 25%),
            linear-gradient(180deg, #f7f8fb 0%, #eef2f7 100%);
    }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .hero {
        background: linear-gradient(135deg, #1f2937 0%, #334155 100%);
        color: white;
        padding: 28px;
        border-radius: 22px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    }
    .hero h1 { margin: 0; font-size: 2.4rem; }
    .hero p { margin: 8px 0 0 0; opacity: 0.9; }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 18px;
        padding: 14px;
        border-left: 6px solid #D4AF37;
        box-shadow: 0 6px 18px rgba(15,23,42,0.08);
    }
    .section-card {
        background: rgba(255,255,255,0.9);
        border: 1px solid rgba(15,23,42,0.05);
        border-radius: 18px;
        padding: 14px 16px;
        box-shadow: 0 4px 16px rgba(15,23,42,0.05);
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🏗️ Renovation Manager V3</h1>
        <p>Οργάνωση εξόδων, εργασιών, προσφορών και βασικών οικονομικών του έργου σου.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

SHEET_EXPENSES = "Expenses"
SHEET_TASKS = "Tasks"
SHEET_OFFERS = "Offers"

MENU_OPTIONS = [
    "🏠 Dashboard",
    "💰 Έξοδα",
    "📋 Εργασίες",
    "💼 Προσφορές",
    "📊 Αναλύσεις",
    "🏦 Δάνειο",
    "🧮 Calculator",
]

EXPENSE_COLUMNS = ["_id", "Ημερομηνία", "Κατηγορία", "Είδος", "Ποσό", "Πληρωτής", "Σημειώσεις"]
TASK_COLUMNS = ["_id", "Εργασία", "Κατάσταση", "Κόστος", "Προτεραιότητα", "Ανάθεση", "Σημειώσεις"]
OFFER_COLUMNS = ["_id", "Πάροχος", "Περιγραφή", "Ποσό", "Κατηγορία", "Σημειώσεις"]

EXPENSE_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Κουφώματα", "Άλλο"]
EXPENSE_TYPES = ["Αμοιβή", "Υλικά"]
PAYERS = ["Εγώ", "Πατέρας", "Κοινό", "Άλλο"]

TASK_STATUSES = ["To Do", "Doing", "Done"]
TASK_PRIORITIES = ["Χαμηλή", "Μεσαία", "Υψηλή"]

OFFER_CATEGORIES = ["Υδραυλικά", "Ηλεκτρολογικά", "Πλακάκια", "Κουζίνα", "Βάψιμο", "Άλλο"]


@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)


conn = get_connection()


def empty_df(columns):
    return pd.DataFrame(columns=columns)


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return empty_df(columns)
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def normalize_ids(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "_id" not in df.columns:
        df["_id"] = ""
    df["_id"] = df["_id"].astype(str)
    missing = df["_id"].isin(["", "nan", "None"])
    if missing.any():
        df.loc[missing, "_id"] = [str(uuid.uuid4())[:8] for _ in range(missing.sum())]
    return df


def safe_read(sheet_name: str, columns: list[str]) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=sheet_name, ttl=0)
        if df is None or df.empty:
            return empty_df(columns)
        df = df.dropna(how="all")
        df = ensure_columns(df, columns)
        df = normalize_ids(df)
        return df
    except Exception:
        return empty_df(columns)


def safe_write(sheet_name: str, df: pd.DataFrame) -> bool:
    try:
        conn.update(worksheet=sheet_name, data=df)
        return True
    except Exception as e:
        st.error(f"Σφάλμα αποθήκευσης στο '{sheet_name}': {e}")
        return False


def append_row(df: pd.DataFrame, row_data: dict, columns: list[str]) -> pd.DataFrame:
    row_data["_id"] = str(uuid.uuid4())[:8]
    current = ensure_columns(df, columns)
    new_row = ensure_columns(pd.DataFrame([row_data]), columns)
    return pd.concat([current, new_row], ignore_index=True)


def update_row_by_id(df: pd.DataFrame, row_id: str, new_data: dict, columns: list[str]) -> pd.DataFrame:
    updated = ensure_columns(df, columns).copy()
    mask = updated["_id"].astype(str) == str(row_id)
    if mask.any():
        for key, value in new_data.items():
            updated.loc[mask, key] = value
    return updated


def delete_row_by_id(df: pd.DataFrame, row_id: str) -> pd.DataFrame:
    if df.empty:
        return df
    updated = df[df["_id"].astype(str) != str(row_id)].copy()
    return updated.reset_index(drop=True)


def money_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def show_table(df: pd.DataFrame, hide_id: bool = True):
    if df.empty:
        st.info("Δεν υπάρχουν δεδομένα.")
        return
    show_df = df.copy()
    if hide_id and "_id" in show_df.columns:
        show_df = show_df.drop(columns=["_id"])
    st.dataframe(show_df, use_container_width=True)


def filter_expenses(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    c1, c2, c3 = st.columns(3)
    with c1:
        cat = st.selectbox("Φίλτρο κατηγορίας", ["Όλες"] + EXPENSE_CATEGORIES, key="exp_filter_cat")
    with c2:
        kind = st.selectbox("Φίλτρο είδους", ["Όλα"] + EXPENSE_TYPES, key="exp_filter_kind")
    with c3:
        payer = st.selectbox("Φίλτρο πληρωτή", ["Όλοι"] + PAYERS, key="exp_filter_payer")
    if cat != "Όλες":
        filtered = filtered[filtered["Κατηγορία"] == cat]
    if kind != "Όλα":
        filtered = filtered[filtered["Είδος"] == kind]
    if payer != "Όλοι":
        filtered = filtered[filtered["Πληρωτής"] == payer]
    return filtered


def filter_tasks(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    c1, c2 = st.columns(2)
    with c1:
        status = st.selectbox("Φίλτρο κατάστασης", ["Όλες"] + TASK_STATUSES, key="task_filter_status")
    with c2:
        priority = st.selectbox("Φίλτρο προτεραιότητας", ["Όλες"] + TASK_PRIORITIES, key="task_filter_priority")
    if status != "Όλες":
        filtered = filtered[filtered["Κατάσταση"] == status]
    if priority != "Όλες":
        filtered = filtered[filtered["Προτεραιότητα"] == priority]
    return filtered


def filter_offers(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    category = st.selectbox("Φίλτρο κατηγορίας προσφοράς", ["Όλες"] + OFFER_CATEGORIES, key="offer_filter_cat")
    if category != "Όλες":
        filtered = filtered[filtered["Κατηγορία"] == category]
    return filtered


def render_dashboard(df_exp: pd.DataFrame, df_tasks: pd.DataFrame, df_off: pd.DataFrame):
    budget = st.number_input("💼 Συνολικό Budget (€)", min_value=0.0, value=30000.0, step=1000.0)
    spent = money_series(df_exp, "Ποσό").sum()
    remaining = budget - spent
    usage = (spent / budget * 100) if budget > 0 else 0.0
    tasks_total = len(df_tasks)
    tasks_done = int((df_tasks["Κατάσταση"] == "Done").sum()) if not df_tasks.empty else 0
    offers_amounts = money_series(df_off, "Ποσό")
    best_offer = offers_amounts.min() if not offers_amounts.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Συνολικά Έξοδα", f"{spent:,.2f} €")
    c2.metric("📉 Υπόλοιπο", f"{remaining:,.2f} €")
    c3.metric("📊 Χρήση Budget", f"{usage:.1f}%")
    c4.metric("✅ Ολοκληρωμένες Εργασίες", f"{tasks_done}/{tasks_total}")

    c5, c6, c7 = st.columns(3)
    c5.metric("🏆 Καλύτερη Προσφορά", f"{best_offer:,.2f} €" if best_offer > 0 else "-")
    c6.metric("🧱 Σύνολο Εργασιών", tasks_total)
    c7.metric("🧾 Σύνολο Προσφορών", len(df_off))

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    a1, a2 = st.columns(2)

    with a1:
        st.subheader("Έξοδα ανά κατηγορία")
        if not df_exp.empty:
            chart = df_exp.copy()
            chart["Ποσό"] = money_series(chart, "Ποσό")
            by_cat = chart.groupby("Κατηγορία", as_index=False)["Ποσό"].sum()
            if not by_cat.empty:
                st.bar_chart(by_cat.set_index("Κατηγορία"))
            else:
                st.info("Δεν υπάρχουν δεδομένα.")
        else:
            st.info("Δεν υπάρχουν έξοδα.")

    with a2:
        st.subheader("Έξοδα ανά είδος")
        if not df_exp.empty:
            chart = df_exp.copy()
            chart["Ποσό"] = money_series(chart, "Ποσό")
            by_kind = chart.groupby("Είδος", as_index=False)["Ποσό"].sum()
            if not by_kind.empty:
                st.bar_chart(by_kind.set_index("Είδος"))
            else:
                st.info("Δεν υπάρχουν δεδομένα.")
        else:
            st.info("Δεν υπάρχουν έξοδα.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_expenses(df_exp: pd.DataFrame):
    st.subheader("💰 Έξοδα")

    with st.expander("➕ Νέο έξοδο", expanded=False):
        with st.form("expense_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                expense_date = st.date_input("Ημερομηνία")
                category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES)
            with c2:
                expense_type = st.selectbox("Είδος", EXPENSE_TYPES)
                payer = st.selectbox("Πληρωτής", PAYERS)
            with c3:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            notes = st.text_input("Σημειώσεις")
            submitted = st.form_submit_button("Αποθήκευση")
            if submitted:
                updated_df = append_row(
                    df_exp,
                    {
                        "Ημερομηνία": str(expense_date),
                        "Κατηγορία": category,
                        "Είδος": expense_type,
                        "Ποσό": amount,
                        "Πληρωτής": payer,
                        "Σημειώσεις": notes.strip(),
                    },
                    EXPENSE_COLUMNS,
                )
                if safe_write(SHEET_EXPENSES, updated_df):
                    st.success("Το έξοδο αποθηκεύτηκε.")
                    st.rerun()

    filtered = filter_expenses(df_exp)
    show_table(filtered)

    if filtered.empty:
        return

    options = filtered["_id"].tolist()
    selected_id = st.selectbox(
        "Επιλογή εξόδου για επεξεργασία / διαγραφή",
        options=options,
        format_func=lambda rid: (
            f"{filtered.loc[filtered['_id'] == rid, 'Ημερομηνία'].iloc[0]} | "
            f"{filtered.loc[filtered['_id'] == rid, 'Κατηγορία'].iloc[0]} | "
            f"{filtered.loc[filtered['_id'] == rid, 'Είδος'].iloc[0]} | "
            f"{float(pd.to_numeric(filtered.loc[filtered['_id'] == rid, 'Ποσό'], errors='coerce').fillna(0).iloc[0]):,.2f} €"
        ),
    )

    row = df_exp[df_exp["_id"] == selected_id].iloc[0]

    with st.expander("✏️ Edit εξόδου", expanded=False):
        with st.form("expense_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_date = st.text_input("Ημερομηνία", value=str(row["Ημερομηνία"]))
                new_category = st.selectbox("Κατηγορία", EXPENSE_CATEGORIES, index=EXPENSE_CATEGORIES.index(row["Κατηγορία"]) if row["Κατηγορία"] in EXPENSE_CATEGORIES else 0)
            with c2:
                new_type = st.selectbox("Είδος", EXPENSE_TYPES, index=EXPENSE_TYPES.index(row["Είδος"]) if row["Είδος"] in EXPENSE_TYPES else 0)
                new_payer = st.selectbox("Πληρωτής", PAYERS, index=PAYERS.index(row["Πληρωτής"]) if row["Πληρωτής"] in PAYERS else 0)
            with c3:
                new_amount = st.number_input("Ποσό (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Ποσό"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
            new_notes = st.text_input("Σημειώσεις", value=str(row["Σημειώσεις"]))
            save_edit = st.form_submit_button("Αποθήκευση αλλαγών")
            if save_edit:
                updated_df = update_row_by_id(
                    df_exp,
                    selected_id,
                    {
                        "Ημερομηνία": new_date,
                        "Κατηγορία": new_category,
                        "Είδος": new_type,
                        "Ποσό": new_amount,
                        "Πληρωτής": new_payer,
                        "Σημειώσεις": new_notes.strip(),
                    },
                    EXPENSE_COLUMNS,
                )
                if safe_write(SHEET_EXPENSES, updated_df):
                    st.success("Το έξοδο ενημερώθηκε.")
                    st.rerun()

    if st.button("🗑️ Διαγραφή επιλεγμένου εξόδου", key="expense_delete_btn"):
        updated_df = delete_row_by_id(df_exp, selected_id)
        if safe_write(SHEET_EXPENSES, updated_df):
            st.success("Το έξοδο διαγράφηκε.")
            st.rerun()


def render_tasks(df_tasks: pd.DataFrame):
    st.subheader("📋 Εργασίες")

    with st.expander("➕ Νέα εργασία", expanded=False):
        with st.form("task_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                task_name = st.text_input("Εργασία")
                status = st.selectbox("Κατάσταση", TASK_STATUSES)
            with c2:
                cost = st.number_input("Κόστος (€)", min_value=0.0, step=10.0)
                priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES)
            with c3:
                assignee = st.text_input("Ανάθεση")
            notes = st.text_input("Σημειώσεις")
            submitted = st.form_submit_button("Αποθήκευση")
            if submitted and task_name.strip():
                updated_df = append_row(
                    df_tasks,
                    {
                        "Εργασία": task_name.strip(),
                        "Κατάσταση": status,
                        "Κόστος": cost,
                        "Προτεραιότητα": priority,
                        "Ανάθεση": assignee.strip(),
                        "Σημειώσεις": notes.strip(),
                    },
                    TASK_COLUMNS,
                )
                if safe_write(SHEET_TASKS, updated_df):
                    st.success("Η εργασία αποθηκεύτηκε.")
                    st.rerun()

    filtered = filter_tasks(df_tasks)
    show_table(filtered)

    if filtered.empty:
        return

    selected_id = st.selectbox(
        "Επιλογή εργασίας για επεξεργασία / διαγραφή",
        options=filtered["_id"].tolist(),
        format_func=lambda rid: f"{filtered.loc[filtered['_id'] == rid, 'Εργασία'].iloc[0]} | {filtered.loc[filtered['_id'] == rid, 'Κατάσταση'].iloc[0]}",
    )

    row = df_tasks[df_tasks["_id"] == selected_id].iloc[0]

    with st.expander("✏️ Edit εργασίας", expanded=False):
        with st.form("task_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_task = st.text_input("Εργασία", value=str(row["Εργασία"]))
                new_status = st.selectbox("Κατάσταση", TASK_STATUSES, index=TASK_STATUSES.index(row["Κατάσταση"]) if row["Κατάσταση"] in TASK_STATUSES else 0)
            with c2:
                new_cost = st.number_input("Κόστος (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Κόστος"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
                new_priority = st.selectbox("Προτεραιότητα", TASK_PRIORITIES, index=TASK_PRIORITIES.index(row["Προτεραιότητα"]) if row["Προτεραιότητα"] in TASK_PRIORITIES else 0)
            with c3:
                new_assignee = st.text_input("Ανάθεση", value=str(row["Ανάθεση"]))
            new_notes = st.text_input("Σημειώσεις", value=str(row["Σημειώσεις"]))
            save_edit = st.form_submit_button("Αποθήκευση αλλαγών")
            if save_edit and new_task.strip():
                updated_df = update_row_by_id(
                    df_tasks,
                    selected_id,
                    {
                        "Εργασία": new_task.strip(),
                        "Κατάσταση": new_status,
                        "Κόστος": new_cost,
                        "Προτεραιότητα": new_priority,
                        "Ανάθεση": new_assignee.strip(),
                        "Σημειώσεις": new_notes.strip(),
                    },
                    TASK_COLUMNS,
                )
                if safe_write(SHEET_TASKS, updated_df):
                    st.success("Η εργασία ενημερώθηκε.")
                    st.rerun()

    if st.button("🗑️ Διαγραφή επιλεγμένης εργασίας", key="task_delete_btn"):
        updated_df = delete_row_by_id(df_tasks, selected_id)
        if safe_write(SHEET_TASKS, updated_df):
            st.success("Η εργασία διαγράφηκε.")
            st.rerun()


def render_offers(df_off: pd.DataFrame):
    st.subheader("💼 Προσφορές")

    with st.expander("➕ Νέα προσφορά", expanded=False):
        with st.form("offer_add_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                provider = st.text_input("Πάροχος")
                category = st.selectbox("Κατηγορία", OFFER_CATEGORIES)
            with c2:
                description = st.text_input("Περιγραφή")
            with c3:
                amount = st.number_input("Ποσό (€)", min_value=0.0, step=10.0)
            notes = st.text_input("Σημειώσεις")
            submitted = st.form_submit_button("Αποθήκευση")
            if submitted and provider.strip():
                updated_df = append_row(
                    df_off,
                    {
                        "Πάροχος": provider.strip(),
                        "Περιγραφή": description.strip(),
                        "Ποσό": amount,
                        "Κατηγορία": category,
                        "Σημειώσεις": notes.strip(),
                    },
                    OFFER_COLUMNS,
                )
                if safe_write(SHEET_OFFERS, updated_df):
                    st.success("Η προσφορά αποθηκεύτηκε.")
                    st.rerun()

    filtered = filter_offers(df_off)

    if not filtered.empty:
        temp = filtered.copy()
        temp["Ποσό"] = money_series(temp, "Ποσό")
        best = temp.sort_values("Ποσό").iloc[0]
        st.info(f"🏆 Καλύτερη προσφορά: {best['Πάροχος']} ({best['Ποσό']:.2f} €)")
    show_table(filtered)

    if filtered.empty:
        return

    selected_id = st.selectbox(
        "Επιλογή προσφοράς για επεξεργασία / διαγραφή",
        options=filtered["_id"].tolist(),
        format_func=lambda rid: f"{filtered.loc[filtered['_id'] == rid, 'Πάροχος'].iloc[0]} | {filtered.loc[filtered['_id'] == rid, 'Περιγραφή'].iloc[0]}",
    )

    row = df_off[df_off["_id"] == selected_id].iloc[0]

    with st.expander("✏️ Edit προσφοράς", expanded=False):
        with st.form("offer_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_provider = st.text_input("Πάροχος", value=str(row["Πάροχος"]))
                new_category = st.selectbox("Κατηγορία", OFFER_CATEGORIES, index=OFFER_CATEGORIES.index(row["Κατηγορία"]) if row["Κατηγορία"] in OFFER_CATEGORIES else 0)
            with c2:
                new_description = st.text_input("Περιγραφή", value=str(row["Περιγραφή"]))
            with c3:
                new_amount = st.number_input("Ποσό (€)", min_value=0.0, value=float(pd.to_numeric(pd.Series([row["Ποσό"]]), errors="coerce").fillna(0).iloc[0]), step=10.0)
            new_notes = st.text_input("Σημειώσεις", value=str(row["Σημειώσεις"]))
            save_edit = st.form_submit_button("Αποθήκευση αλλαγών")
            if save_edit and new_provider.strip():
                updated_df = update_row_by_id(
                    df_off,
                    selected_id,
                    {
                        "Πάροχος": new_provider.strip(),
                        "Περιγραφή": new_description.strip(),
                        "Ποσό": new_amount,
                        "Κατηγορία": new_category,
                        "Σημειώσεις": new_notes.strip(),
                    },
                    OFFER_COLUMNS,
                )
                if safe_write(SHEET_OFFERS, updated_df):
                    st.success("Η προσφορά ενημερώθηκε.")
                    st.rerun()

    if st.button("🗑️ Διαγραφή επιλεγμένης προσφοράς", key="offer_delete_btn"):
        updated_df = delete_row_by_id(df_off, selected_id)
        if safe_write(SHEET_OFFERS, updated_df):
            st.success("Η προσφορά διαγράφηκε.")
            st.rerun()


def render_analytics(df_exp: pd.DataFrame, df_tasks: pd.DataFrame, df_off: pd.DataFrame):
    st.subheader("📊 Αναλύσεις")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Έξοδα ανά κατηγορία")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].sum()
            st.dataframe(summary, use_container_width=True)
            st.bar_chart(summary.set_index("Κατηγορία"))
        else:
            st.info("Δεν υπάρχουν δεδομένα.")

        st.markdown("### Έξοδα ανά είδος")
        if not df_exp.empty:
            temp = df_exp.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Είδος", as_index=False)["Ποσό"].sum()
            st.dataframe(summary, use_container_width=True)
            st.bar_chart(summary.set_index("Είδος"))

    with c2:
        st.markdown("### Εργασίες ανά κατάσταση")
        if not df_tasks.empty:
            summary = df_tasks["Κατάσταση"].value_counts().rename_axis("Κατάσταση").reset_index(name="Πλήθος")
            st.dataframe(summary, use_container_width=True)
            st.bar_chart(summary.set_index("Κατάσταση"))
        else:
            st.info("Δεν υπάρχουν δεδομένα.")

        st.markdown("### Προσφορές ανά κατηγορία")
        if not df_off.empty:
            temp = df_off.copy()
            temp["Ποσό"] = money_series(temp, "Ποσό")
            summary = temp.groupby("Κατηγορία", as_index=False)["Ποσό"].mean()
            summary = summary.rename(columns={"Ποσό": "Μέσο Ποσό"})
            st.dataframe(summary, use_container_width=True)
            st.bar_chart(summary.set_index("Κατηγορία"))
        else:
            st.info("Δεν υπάρχουν δεδομένα.")


def render_loan():
    st.subheader("🏦 Υπολογιστής Δόσης")
    principal = st.number_input("Κεφάλαιο (€)", min_value=0.0, value=10000.0)
    annual_rate = st.number_input("Ετήσιο Επιτόκιο (%)", min_value=0.0, value=4.5)
    months = st.number_input("Μήνες Εξόφλησης", min_value=1, value=60)
    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:
        installment = principal / months
    else:
        installment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)

    total_paid = installment * months
    interest_paid = total_paid - principal

    c1, c2, c3 = st.columns(3)
    c1.metric("Μηνιαία Δόση", f"{installment:.2f} €")
    c2.metric("Συνολικό Πληρωτέο", f"{total_paid:.2f} €")
    c3.metric("Συνολικοί Τόκοι", f"{interest_paid:.2f} €")


def render_calculator():
    st.subheader("🧮 Calculator")
    mode = st.selectbox("Τύπος υπολογισμού", ["Πλακάκια", "Χρώματα"])

    if mode == "Πλακάκια":
        area = st.number_input("m² Επιφάνειας", min_value=0.0, value=10.0)
        w = st.number_input("Πλάτος πλακιδίου (cm)", min_value=0.1, value=60.0)
        h = st.number_input("Ύψος πλακιδίου (cm)", min_value=0.1, value=120.0)
        waste = st.number_input("Ποσοστό φύρας (%)", min_value=0.0, value=10.0)

        tile_area = (w * h) / 10000
        needed = area / tile_area if tile_area > 0 else 0
        needed = int(needed * (1 + waste / 100)) + 1
        st.metric("Τεμάχια που θα χρειαστείς", needed)

    if mode == "Χρώματα":
        wall_area = st.number_input("m² Τοίχου", min_value=0.0, value=50.0)
        coats = st.number_input("Χέρια", min_value=1, value=2)
        coverage = st.number_input("Απόδοση (m²/λίτρο)", min_value=1.0, value=12.0)
        liters = (wall_area * coats) / coverage
        st.metric("Λίτρα χρώματος", f"{liters:.1f} L")


df_expenses = safe_read(SHEET_EXPENSES, EXPENSE_COLUMNS)
df_tasks = safe_read(SHEET_TASKS, TASK_COLUMNS)
df_offers = safe_read(SHEET_OFFERS, OFFER_COLUMNS)

menu = st.sidebar.radio("📂 Μενού", MENU_OPTIONS)

if menu == "🏠 Dashboard":
    render_dashboard(df_expenses, df_tasks, df_offers)
elif menu == "💰 Έξοδα":
    render_expenses(df_expenses)
elif menu == "📋 Εργασίες":
    render_tasks(df_tasks)
elif menu == "💼 Προσφορές":
    render_offers(df_offers)
elif menu == "📊 Αναλύσεις":
    render_analytics(df_expenses, df_tasks, df_offers)
elif menu == "🏦 Δάνειο":
    render_loan()
elif menu == "🧮 Calculator":
    render_calculator()

