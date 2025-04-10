
import streamlit as st
import pandas as pd
import numpy as np

# ========== CONFIG ==========
st.set_page_config(page_title="AI-Powered Bond Selector", layout="wide")

# ========== PASSWORD ==========
password = st.sidebar.text_input("Enter password to access the app:", type="password")
if password != "elxi2025":
    st.warning("Please enter the correct password.")
    st.stop()

# ========== FILE UPLOAD ==========
st.sidebar.header("Client Profile")
profile = st.sidebar.selectbox("Choose a client profile:", ["USD - Income Focused", "EUR - Income Focused", "USD - Capital Gains Focused"])
uploaded_file = st.sidebar.file_uploader("Upload Bond Data (Excel)", type=["xlsx"])

if uploaded_file is None:
    st.info("👈 Please upload an Excel file to begin.")
    st.stop()

# ========== READ DATA ==========
try:
    df = pd.read_excel(uploaded_file)
except Exception as e:
    st.error(f"Failed to read Excel file: {e}")
    st.stop()

# ========== DISPLAY RAW DATA ==========
st.markdown("### ✅ Uploaded data:")
st.dataframe(df)

# ========== FILTERING ==========
st.markdown("### 🔍 Step-by-step Filtering Info")
initial_count = len(df)

filtered_df = df[df['Rating'].str.startswith(('A', 'B'))]  # Investment grade-ish
step1_count = len(filtered_df)

filtered_df = filtered_df[filtered_df['Price'] <= 100]
step2_count = len(filtered_df)

filtered_df = filtered_df[filtered_df['Duration'] <= 5]
step3_count = len(filtered_df)

st.write(f"Original bonds: {initial_count}")
st.write(f"After Investment Grade filter: {step1_count}")
st.write(f"After Price ≤ 100 filter: {step2_count}")
st.write(f"After Duration ≤ 5 filter: {step3_count}")

st.success("✅ Filtered Bonds:")
st.dataframe(filtered_df)

# ========== TOP RECOMMENDED ==========
st.markdown("### 📊 Top Recommended Bonds")
recommended = filtered_df.copy()
recommended = recommended.sort_values(by="Rating").head(10)  # Dummy logic
st.dataframe(recommended)

# ========== EXPLANATION SECTION ==========
st.markdown("### 💬 Bond Explanation")

if not recommended.empty:
    bond = recommended.iloc[0]
    explanation = (
        f"This bond by {bond['Issuer']} offers a {bond['Coupon']}% coupon, "
        f"priced at {bond['Price']}, rated {bond['Rating']}, with "
        f"{bond['Duration']} years maturity and {bond['Liquidity']} liquidity."
    )
    st.write(explanation)
else:
    st.write("No recommended bonds available to generate explanation.")

# ========== PLACEHOLDER: EXPORT ==========
st.markdown("### 📁 Download All Bond Reports")
st.button("Generate ZIP (placeholder)")
