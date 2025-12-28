import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO

# =========================
# PAGE CONFIG
# =========================
st.set_page_config("Your Business Report", layout="wide")

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    password BLOB
)
""")
conn.commit()

# =========================
# AUTH FUNCTIONS
# =========================
def create_user(email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        c.execute("INSERT INTO users VALUES (?,?)", (email, hashed))
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    data = c.fetchone()
    if data and bcrypt.checkpw(password.encode(), data[0]):
        return True
    return False

# =========================
# LOGIN / REGISTER
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login / Register")

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
                st.error("Invalid login")

    with t2:
        new_email = st.text_input("New Email")
        new_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            if create_user(new_email, new_password):
                st.success("Account created Successfully. Please login.")
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
# APP HEADER
# =========================
st.title("📊 Business Report ")

# =========================
# SMART COLUMN DETECTOR
# =========================
def find_column(cols, keys):
    for col in cols:
        for k in keys:
            if k.lower() in col.lower():
                return col
    return None

# =========================
# FILE UPLOAD
# =========================
file = st.file_uploader("Upload CSV or Excel file", ["csv", "xlsx"])
if not file:
    st.stop()

df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
st.dataframe(df.head())

cols = df.columns.tolist()

# =========================
# COLUMN MAPPING
# =========================
date_col = st.selectbox("Date Column", cols, index=cols.index(find_column(cols, ["date"])))
sales_col = st.selectbox("Sales Column", cols, index=cols.index(find_column(cols, ["sales", "revenue"])))
profit_col = st.selectbox("Profit Column", cols, index=cols.index(find_column(cols, ["profit"])))
category_col = st.selectbox("Category Column", cols, index=cols.index(find_column(cols, ["category"])))
product_col = st.selectbox("Product Column", cols, index=cols.index(find_column(cols, ["product", "item"])))

# =========================
# DATA CLEANING
# =========================
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce")
df.dropna(subset=[date_col, sales_col, profit_col], inplace=True)

# =========================
# KPIs
# =========================
total_sales = df[sales_col].sum()
total_profit = df[profit_col].sum()
total_loss = df[df[profit_col] < 0][profit_col].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Total Sales", f"₹{total_sales:,.2f}")
c2.metric("Total Profit", f"₹{total_profit:,.2f}")
c3.metric("Total Loss", f"₹{total_loss:,.2f}")

# =========================
# PROFIT / LOSS OVER TIME
# =========================
st.subheader("📉 Profit & Loss Over Time")
daily = df.groupby(df[date_col].dt.date)[profit_col].sum()
st.line_chart(daily)

# =========================
# LOSS ANALYSIS
# =========================
loss_df = df[df[profit_col] < 0]

st.subheader("🔻 Loss Report")
if loss_df.empty:
    st.success("No losses found 🎉")
else:
    st.dataframe(
        loss_df.groupby(product_col)[profit_col]
        .sum()
        .sort_values()
        .head(5)
    )

# =========================
# PDF REPORT GENERATOR
# =========================
def generate_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Profit & Loss Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"Total Sales: ₹{total_sales:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Total Profit: ₹{total_profit:,.2f}", styles["Normal"]))
    elements.append(Paragraph(f"Total Loss: ₹{total_loss:,.2f}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Worst Loss Products", styles["Heading2"]))

    if not loss_df.empty:
        table_data = [["Product", "Loss"]]
        for p, v in (
            loss_df.groupby(product_col)[profit_col]
            .sum()
            .sort_values()
            .head(5)
            .items()
        ):
            table_data.append([p, f"₹{v:,.2f}"])

        elements.append(Table(table_data))
    else:
        elements.append(Paragraph("No losses detected.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================
# DOWNLOAD BUTTON
# =========================
st.divider()
st.subheader("📄 Download Report")

pdf = generate_pdf()
st.download_button(
    "Download Profit & Loss Report (PDF)",
    data=pdf,
    file_name="profit_loss_report.pdf",
    mime="application/pdf"
)
