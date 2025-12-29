import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
from datetime import datetime

# =========================
# ADMIN CONFIG
# =========================
ADMIN_EMAIL = "michellemagdalene885@gmail.com"
FREE_USAGE_LIMIT = 3

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="M²SolAnalytics",
    layout="wide",
    page_icon="📊"
)

# =========================
# BRAND HEADER (NO LOGO)
# =========================
st.markdown("""
<h1 style='margin-bottom:0;'>M<sup>2</sup>SolAnalytics</h1>
<h4 style='margin-top:-10px; color:gray;'>MSM.CO</h4>
""", unsafe_allow_html=True)

st.divider()

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password BLOB,
    usage_count INTEGER DEFAULT 0,
    created_at TEXT
)
""")
conn.commit()

# =========================
# AUTH FUNCTIONS
# =========================
def create_user(email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute(
            "INSERT INTO users (email, password, usage_count, created_at) VALUES (?,?,0,?)",
            (email, hashed, datetime.now().isoformat())
        )
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    data = c.fetchone()
    return data and bcrypt.checkpw(password.encode(), data[0])

def increment_usage(email):
    c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email=?", (email,))
    conn.commit()

def get_usage(email):
    c.execute("SELECT usage_count FROM users WHERE email=?", (email,))
    return c.fetchone()[0]

def get_all_users():
    c.execute("SELECT email, usage_count, created_at FROM users")
    return c.fetchall()

# =========================
# SESSION
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =========================
# LOGIN / REGISTER
# =========================
if not st.session_state.logged_in:
    st.subheader("🔐 Client Access")

    t1, t2 = st.tabs(["Login", "Register"])

    with t1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if login_user(email, password):
                st.session_state.logged_in = True
                st.session_state.user = email
                st.rerun()
            else:
                st.error("Invalid credentials")

    with t2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if create_user(new_email, new_password):
                st.success("Account created. Please login.")
            else:
                st.error("User already exists")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.success(f"Logged in as {st.session_state.user}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN PANEL
# =========================
if st.session_state.user == ADMIN_EMAIL:
    st.sidebar.markdown("### 👑 Admin Panel")
    users = get_all_users()
    st.subheader("📊 Registered Users (Admin Only)")
    st.metric("Total Users", len(users))
    st.dataframe(
        pd.DataFrame(users, columns=["Email", "Usage Count", "Registered On"])
    )

st.divider()

# =========================
# USAGE LIMIT CHECK
# =========================
usage = get_usage(st.session_state.user)

if usage >= FREE_USAGE_LIMIT and st.session_state.user != ADMIN_EMAIL:
    st.error("🚫 Free usage limit reached (3 uses)")
    st.info("📧 Contact admin for access: michellemagdalene885@gmail.com")
    st.stop()

# =========================
# FILE UPLOAD
# =========================
file = st.file_uploader("📤 Upload Sales Data (CSV / Excel)", ["csv", "xlsx"])

if not file:
    st.stop()

increment_usage(st.session_state.user)

df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
st.dataframe(df.head())

# =========================
# COLUMN AUTO-DETECT
# =========================
def find_column(cols, keywords):
    for col in cols:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return cols[0]

cols = df.columns.tolist()

date_col = st.selectbox("Date", cols, index=cols.index(find_column(cols, ["date"])))
sales_col = st.selectbox("Sales", cols, index=cols.index(find_column(cols, ["sales", "revenue"])))
profit_col = st.selectbox("Profit", cols, index=cols.index(find_column(cols, ["profit"])))

# =========================
# CLEANING
# =========================
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce")
df.dropna(inplace=True)

# =========================
# KPIs
# =========================
total_sales = df[sales_col].sum()
total_profit = df[profit_col].sum()

c1, c2 = st.columns(2)
c1.metric("💰 Total Sales", f"₹{total_sales:,.2f}")
c2.metric("📈 Total Profit", f"₹{total_profit:,.2f}")

# =========================
# PDF REPORT
# =========================
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("M²SolAnalytics – MSM.CO", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Total Sales: ₹{total_sales:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Total Profit: ₹{total_profit:,.2f}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

st.download_button(
    "📄 Download Report",
    generate_pdf(),
    "M2SolAnalytics_Report.pdf",
    "application/pdf"
)
