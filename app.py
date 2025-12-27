import streamlit as st
import pandas as pd

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Universal Profit Analysis",
    layout="wide"
)

st.title("📊 Universal Sales & Profit Analysis Dashboard")

# =========================
# 🔐 PASSWORD GATE
# =========================
PASSWORD = "michelle123"

entered = st.text_input("🔑 Enter password", type="password")
if entered != PASSWORD:
    st.info("Please enter the password to continue")
    st.stop()

# =========================
# 🧠 SMART COLUMN DETECTOR
# =========================
def find_column(columns, keywords):
    for col in columns:
        for kw in keywords:
            if kw.lower() in col.lower():
                return col
    return None

# =========================
# 📁 FILE UPLOAD
# =========================
file = st.file_uploader(
    "Upload CSV or Excel file",
    type=["csv", "xlsx"]
)

if file is None:
    st.info("Upload a dataset to begin analysis")
    st.stop()

# =========================
# 📥 READ FILE
# =========================
try:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

st.success("File uploaded successfully!")

st.subheader("🔍 Data Preview")
st.dataframe(df.head())

# =========================
# 🧭 COLUMN MAPPING
# =========================
st.subheader("🧭 Map your columns")

columns = df.columns.tolist()

sales_default = find_column(columns, ["sales", "revenue", "amount"])
profit_default = find_column(columns, ["profit", "margin"])
category_default = find_column(columns, ["category", "segment"])
product_default = find_column(columns, ["product", "item", "name"])

sales_col = st.selectbox(
    "Sales column",
    columns,
    index=columns.index(sales_default) if sales_default else 0
)

profit_col = st.selectbox(
    "Profit column",
    columns,
    index=columns.index(profit_default) if profit_default else 0
)

category_col = st.selectbox(
    "Category column",
    columns,
    index=columns.index(category_default) if category_default else 0
)

product_col = st.selectbox(
    "Product column",
    columns,
    index=columns.index(product_default) if product_default else 0
)

# =========================
# 🚫 VALIDATION
# =========================
if len({sales_col, profit_col, category_col, product_col}) < 4:
    st.error("❌ Please select different columns for each field.")
    st.stop()

df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
df[profit_col] = pd.to_numeric(df[profit_col], errors="coerce")

if df[sales_col].isna().all() or df[profit_col].isna().all():
    st.error("❌ Sales or Profit column must contain numeric values.")
    st.stop()

df = df.dropna(subset=[sales_col, profit_col])

st.success("Columns mapped and validated!")

st.divider()

# =========================
# 📊 KPIs
# =========================
total_sales = df[sales_col].sum()
total_profit = df[profit_col].sum()
profit_margin = (total_profit / total_sales) * 100 if total_sales else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"₹{total_sales:,.2f}")
col2.metric("Total Profit", f"₹{total_profit:,.2f}")
col3.metric("Profit Margin", f"{profit_margin:.2f}%")

st.divider()

# =========================
# 📦 PROFIT BY CATEGORY
# =========================
st.subheader("📦 Profit by Category")

category_profit = (
    df.groupby(category_col)[profit_col]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(category_profit)

st.divider()

# =========================
# 🏆 TOP PRODUCTS
# =========================
st.subheader("🏆 Top 5 Products by Profit")

top_products = (
    df.groupby(product_col)[profit_col]
    .sum()
    .sort_values(ascending=False)
    .head(5)
)

st.dataframe(top_products)
