
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from transformers import pipeline
import os
from fpdf import FPDF
import base64
import zipfile
from allocation_helper import optimize_allocation

# Password protection
password = st.text_input("Enter password to access the app:", type="password")
if password != "elxi2024":
    st.stop()

st.title("AI-Powered Bond Selector")

# Load sentiment model
sentiment_pipeline = pipeline("sentiment-analysis")

# Define client profiles
client_profiles = {
    "USD - Income Focused": {
        "Currency": "USD",
        "Investment Grade Only": True,
        "Max Price": 100,
        "Max Duration": 5,
        "Exclude Perpetuals": True,
    },
    "USD - Capital Gains Focused": {
        "Currency": "USD",
        "Investment Grade Only": True,
        "Max Price": 100,
        "Max Duration": 5,
        "Exclude Perpetuals": True,
    },
    "EUR - Income Focused": {
        "Currency": "EUR",
        "Investment Grade Only": True,
        "Max Price": 100,
        "Max Duration": 5,
        "Exclude Perpetuals": True,
    },
}

# File upload
profile_name = st.selectbox("Choose a client profile:", list(client_profiles.keys()))
uploaded_file = st.file_uploader("Upload Bond Data (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.markdown("✅ Uploaded data:")
    st.dataframe(df)

    # Step-by-step filtering
    profile = client_profiles[profile_name]
    st.subheader("🧪 Filtering Process")

    original_count = len(df)
    st.write(f"Original bonds: {original_count}")

    if profile["Investment Grade Only"]:
        df = df[df["Rating"].str.contains("A|BBB")]
        st.write(f"After Investment Grade filter: {len(df)}")

    df = df[df["Price"] <= profile["Max Price"]]
    st.write(f"After Price ≤ {profile['Max Price']} filter: {len(df)}")

    df = df[df["Duration"] <= profile["Max Duration"]]
    st.write(f"After Duration ≤ {profile['Max Duration']} filter: {len(df)}")

    st.success("🎯 Filtered Bonds:")
    st.dataframe(df)

    # Sentiment analysis
    st.subheader("🧠 AI Sentiment & Scoring")
    sentiment_results = []
    for issuer in df["Issuer"]:
        try:
            result = sentiment_pipeline(issuer)[0]
            score = result["score"] if result["label"] == "POSITIVE" else 1 - result["score"]
            sentiment_results.append((result["label"], score))
        except:
            sentiment_results.append(("UNKNOWN", 0.5))

    df["Sentiment"], df["sentiment_score"] = zip(*sentiment_results)

    # Final score = sentiment only (extend later)
    df["final_score"] = df["sentiment_score"]

    # Allocation step
    st.subheader("💰 Portfolio Optimization")
    capital = st.number_input("Total Capital to Allocate", min_value=1000, value=1000000, step=10000)
    if st.button("Optimize Allocation"):
        df = optimize_allocation(df, total_capital=capital)
        st.success("✅ Allocation optimized")
        st.dataframe(df)

    # Dummy news for placeholder
    df["News"] = [
        "[Dummy headline](https://example.com/news1)",
        "[Dummy headline](https://example.com/news2)",
    ] * (len(df) // 2 + 1)
    df["News"] = df["News"][: len(df)]

    st.subheader("📊 Top Recommended Bonds")
    st.dataframe(df)

    # PDF Report Generator
    def generate_pdf_reports(df, logo_path="logo.jpeg"):
        output_dir = "/tmp/pdf_reports"
        os.makedirs(output_dir, exist_ok=True)
        summary_pdf = FPDF()
        for _, bond in df.iterrows():
            summary_pdf.add_page()
            summary_pdf.set_font("Arial", "B", 16)
            summary_pdf.image(logo_path, x=10, y=8, w=40)
            summary_pdf.set_xy(10, 50)
            summary_pdf.set_font("Arial", size=12)

            explanation = f'This bond by {bond["Issuer"]} offers a {bond["Coupon"]}% coupon, priced at {bond["Price"]}, rated {bond["Rating"]}, with {bond["Duration"]} years maturity and {bond["Liquidity"].lower()} liquidity.'
            if "Allocation" in bond and "Weight" in bond:
                    explanation += f"\n\nPortfolio Allocation: ${bond['Allocation']:.2f} ({bond['Weight']*100:.2f}%)"

Portfolio Allocation: ${bond['Allocation']:.2f} ({bond['Weight']*100:.2f}%)"

            summary_pdf.multi_cell(0, 10, explanation)

            if "News" in bond:
                summary_pdf.ln()
                summary_pdf.multi_cell(0, 10, f"Relevant News:
{bond['News']}")

            report_path = os.path.join(output_dir, f"{bond['ISIN']}.pdf")
            summary_pdf.output(report_path)

        zip_path = "/tmp/bond_reports.zip"
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for pdf_file in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, pdf_file), pdf_file)

        return zip_path

    st.subheader("📥 Download All Bond Reports")
    if st.button("Generate ZIP"):
        try:
            zip_path = generate_pdf_reports(df)
            with open(zip_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/zip;base64,{b64}" download="bond_reports.zip">📁 Download Reports</a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Failed to generate reports: {e}")
