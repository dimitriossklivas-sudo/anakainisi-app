import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import hashlib

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Renovation SaaS v8", layout="wide")

# ---------------- HASH ----------------
def blake_hash(text: str) -> str:
    return hashlib.blake2b(text.encode(), digest_size=8).hexdigest()

# ---------------- GOOGLE SHEETS ----------------
conn = st.connection("gsheets", type=GSheetsConnection)

SHEETS = {
    "expenses": "Expenses",
    "tasks": "Tasks",
    "offers": "Offers"
}

def load(sheet):
    try:
        df = conn.read(worksheet=sheet)
        if df is None:
            return pd.DataFrame()
        return df
    except:
        return pd.DataFrame()

def save(sheet, df):
    conn.update(worksheet=sheet, data=df)

df_exp = load(SHEETS["expenses"])
df_tasks = load(SHEETS["tasks"])
df_offers = load(SHEETS["offers"])

# ---------------- HELPERS ----------------
def add(df, row):
    row["id"] = blake_hash(str(datetime.now()))
    return pd.concat([df, pd.DataFrame([row])], ignore_index=True)

def money(x):
    try:
        return f"{float(x):,.2f} €"
    except:
        return "0 €"

# ---------------- THEME ----------------
theme = st.sidebar.toggle("🌙 Dark Mode", value=True)

if theme:
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(180deg,#0f1117,#151922); color:#e6e6e6;}
    .main-card {background:#1c2230;padding:20px;border-radius:16px;box-shadow:0 8px 25px rgba(0,0,0,0.4);margin-bottom:15px;}
    [data-testid="stMetric"] {background:#1c2230;padding:15px;border-radius:12px;border:1px solid rgba(255,255,255,0.05);}
    h1,h2,h3 {color:white;}
    </style>
    """, unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏗 Renovation SaaS v8")
menu = st.sidebar.radio("Menu", ["Dashboard","Expenses","Tasks","Timeline","Offers","Analytics"])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    total = pd.to_numeric(df_exp.get("amount", []), errors="coerce").sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Συνολικά Έξοδα", money(total))
    c2.metric("Καταχωρήσεις", len(df_exp))
    c3.metric("Tasks", len(df_tasks))

    if not df_exp.empty:
        fig = px.pie(df_exp, names="category", values="amount", title="Κατανομή Εξόδων")
        st.plotly_chart(fig, use_container_width=True)

# ---------------- EXPENSES ----------------
elif menu == "Expenses":
    st.title("💰 Expenses")

    with st.form("add_exp"):
        c1,c2,c3 = st.columns(3)
        cat = c1.text_input("Category")
        typ = c2.selectbox("Type", ["Υλικά","Αμοιβή"])
        payer = c3.selectbox("Payer", ["Εγώ","Πατέρας","Κοινό"])
        amount = st.number_input("Amount", 0.0)

        if st.form_submit_button("Add"):
            df_exp = add(df_exp,{
                "category":cat,
                "type":typ,
                "payer":payer,
                "amount":amount,
                "date":str(datetime.now())
            })
            save(SHEETS["expenses"], df_exp)
            st.success("Saved")
            st.rerun()

    st.dataframe(df_exp, use_container_width=True)

# ---------------- TASKS ----------------
elif menu == "Tasks":
    st.title("📋 Tasks")

    with st.form("task"):
        t = st.text_input("Task")
        d = st.date_input("Deadline")

        if st.form_submit_button("Add"):
            df_tasks = add(df_tasks,{
                "task":t,
                "deadline":d,
                "status":"ToDo"
            })
            save(SHEETS["tasks"], df_tasks)
            st.success("Saved")
            st.rerun()

    if not df_tasks.empty:
        df_tasks["overdue"] = pd.to_datetime(df_tasks["deadline"]) < pd.Timestamp.today()
        st.dataframe(df_tasks, use_container_width=True)
    else:
        st.info("No tasks yet")

# ---------------- TIMELINE ----------------
elif menu == "Timeline":
    st.title("📅 Timeline (Gantt)")

    if not df_tasks.empty:
        df_tasks["start"] = pd.to_datetime("today")
        df_tasks["end"] = pd.to_datetime(df_tasks["deadline"])

        fig = px.timeline(
            df_tasks,
            x_start="start",
            x_end="end",
            y="task",
            color="status",
            title="Project Timeline"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks available")

# ---------------- OFFERS ----------------
elif menu == "Offers":
    st.title("💼 Offers")

    with st.form("offer"):
        p = st.text_input("Provider")
        c = st.text_input("Category")
        a = st.number_input("Amount",0.0)

        if st.form_submit_button("Add"):
            df_offers = add(df_offers,{
                "provider":p,
                "category":c,
                "amount":a
            })
            save(SHEETS["offers"], df_offers)
            st.success("Saved")
            st.rerun()

    st.dataframe(df_offers, use_container_width=True)

# ---------------- ANALYTICS ----------------
elif menu == "Analytics":
    st.title("📊 Analytics")

    if not df_exp.empty:
        df_exp["amount"] = pd.to_numeric(df_exp["amount"], errors="coerce")
        summary = df_exp.groupby("category")["amount"].sum().reset_index()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Expenses per Category")
            fig1 = px.bar(summary, x="category", y="amount")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Distribution")
            fig2 = px.pie(summary, names="category", values="amount")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data yet")

# ---------------- FOOTER ----------------
st.markdown("---")
st.caption("Version 8 PRO | Σκλίβας Δημήτριος")
