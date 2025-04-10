
import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
import os
from datetime import datetime

st.set_page_config(page_title="AI-Powered Bond Selector", layout="wide")

# Sidebar
st.sidebar.header("Client Profile")
password = st.sidebar.text_input("Enter password to access the app:", type="password")
if password != "elxi":
    st.warning("Please enter the correct password to proceed.")
    st.stop()

client_profile = st.sidebar.selectbox("Choose a client profile:", [
    "USD - Income Focused",
    "USD - Capital Gains Focused",
    "EUR - Income Focused",
    "EUR - Capital Gains Focused"
])

uploaded_file = st.sidebar.file_uploader("Upload Bond Data (Excel)", type=["xlsx"])

# Sample scoring logic
def score_bond(bond, profile):
    score = 0
    if profile == "USD - Income Focused":
        if bond["Currency"] == "USD": score += 1
        score += bond["Coupon"] * 2
        score += bond["Liquidity"] * 1.5
        if "well spread" in bond["Coupon_Distribution"].lower(): score += 1
    elif profile == "USD - Capital Gains Focused":
        if bond["Currency"] == "USD": score += 1
        score += max(0, 100 - bond["Price"]) * 1.5
        score += bond["Duration"]
    elif profile == "EUR - Income Focused":
        if bond["Currency"] == "EUR": score += 1
        score += bond["Coupon"] * 2
        score += bond["Liquidity"] * 1.5
        if "well spread" in bond["Coupon_Distribution"].lower(): score += 1
    elif profile == "EUR - Capital Gains Focused":
        if bond["Currency"] == "EUR": score += 1
        score += max(0, 100 - bond["Price"]) * 1.5
        score += bond["Duration"]
    return score

# Portfolio allocation
def optimize_allocation(df, cap=0.3):
    df['Score'] = df['Score'].astype(float)
    total_score = df['Score'].sum()
    df['Weight'] = df['Score'] / total_score
    df['Allocation'] = df['Weight'].apply(lambda w: min(w, cap))
    df['Allocation'] = df['Allocation'] / df['Allocation'].sum()
    return df

# Explanation generator
def generate_explanation(bond):
    explanation = f"This bond by {bond['Issuer']} offers a {bond['Coupon']}% coupon, priced at {bond['Price']}, rated {bond['Rating']}, with {bond['Duration']} years maturity and {bond['Liquidity']} liquidity. Coupon distribution is {bond['Coupon_Distribution']}.
"
    explanation += f"Portfolio Allocation: {bond['Allocation']:.2f} USD ({bond['Weight']*100:.2f}%)"
    return explanation

# Main App
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.markdown("## 📊 Uploaded data:")
    st.dataframe(df)

    # Score and recommend
    df["Score"] = df.apply(lambda row: score_bond(row, client_profile), axis=1)
    df_sorted = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    # Portfolio Optimization
    df_opt = optimize_allocation(df_sorted.copy())
    st.markdown("## 🧠 Top Recommended Bonds")
    st.dataframe(df_opt)

    # Show explanations
    st.markdown("## 📌 Bond Explanations")
    for _, bond in df_opt.iterrows():
        st.markdown(f"**{bond['Issuer']}**: {generate_explanation(bond)}")
