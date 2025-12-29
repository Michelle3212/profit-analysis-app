import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

# =========================
# ADMIN CONFIG
# =========================
ADMIN_EMAIL = "michellemagdalene885@gmail.com"
FREE_LIMIT = 3

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="M²SolAnalytics",
    layout="wide",
    page_icon="📊"
)

# =========================
# BRAND HEADER
# =========================
col1, col2 = st.columns([1, 8])
with col1:
    st.image("logo.png", width=90)
with col2:
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
    usage_count INTEGER DEFAULT 0
)
""")
conn.commit()

# =========================
# AUTH FUNCTIONS
# =========================
def create_user(email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users (email, password, usage_count) VALUES (?,?,0)", (email, hashed))
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    data = c.fetchone()
    return data and bcrypt.checkpw(password.encode(), data[0])

def get_usage(email):
    c.execute("SELECT usage_count FROM users WHERE email=?", (email,))
    return c.fetchone()[0]

def increment_usage(email):
    c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email=?", (email,))
    conn.commit()

def get_all_users():
    c.execute("SELECT email, usage_count FROM users")
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
    st.sidebar.markdown("### 👑 Founder Panel")
    users = get_all_users()
    st.subheader("📊 Client Overview (Admin Only)")
    st.metric("Total Registered Users", len(users))
    st.dataframe(pd.DataFrame(users, columns=["Email", "Usage Count"]))

# =========================
# USAGE LIMIT CHECK
# =========================
usage = get_usage(st.session_state.user)

if usage >= FREE_LIMIT and st.session_state.user != ADMIN_EMAIL:
    st.error("🚫 Free usage limit reached (3/3)")
    st.info("📧 Contact admin to continue access:")
    st.markdown("**michellemagdalene885@gmail.com**")
    st.stop()

st.info(f"🧮 Free Usage: {usage}/{FREE_LIMIT}")

# =========================
# FILE UPLOAD
# =========================
file = st.file_uploader("📤 Upload Sales Data (CSV / Excel)", ["csv", "xlsx"])
if not file:
    st.stop()

increment_usage(st.session_state.user)

df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
st.dataframe(df.head())

cols = df.columns.tolist()

# =========================
# COLUMN MAPPING
# =========================
def find_column(cols, keys):
    for col in cols:
        for k in keys:
            if k.lower() in col.lower():
                return col
    return cols[0]

date_col = st.selectbox("Date", cols, index=cols.index(find_column(cols, ["date"])))
sales_col = st.selectbox("Sales", cols, index=cols.index(find_column(cols, ["sales", "revenue"])))
profit_col = st.selectbox("Profit", cols, index=cols.index(find_column(cols, ["profit"])))

df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce")
df.dropna(inplace=True)

# =========================
# KPIs
# =========================
st.metric("💰 Total Sales", f"₹{df[sales_col].sum():,.2f}")
st.metric("📈 Total Profit", f"₹{df[profit_col].sum():,.2f}")

# =========================
# PDF REPORT
# =========================
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    doc.build([
        Paragraph("M²SolAnalytics – MSM.CO", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Total Sales: ₹{df[sales_col].sum():,.2f}", styles["Normal"]),
        Paragraph(f"Total Profit: ₹{df[profit_col].sum():,.2f}", styles["Normal"])
    ])
    buffer.seek(0)
    return buffer

st.download_button(
    "📄 Download Profit & Loss PDF",
    generate_pdf(),
    "M2SolAnalytics_Report.pdf",
    "application/pdf"
)

st.divider()
st.caption("📧 Contact Admin: michellemagdalene885@gmail.com")
