import streamlit as st
import pandas as pd
import numpy as np
from transformers import pipeline
import matplotlib.pyplot as plt
import requests
import os
from fpdf import FPDF
import zipfile

st.set_page_config(page_title="AI Bond Selector", layout="wide")
password = st.sidebar.text_input("Enter password to access the app:", type="password")
if password != "bondsecure":
    st.warning("Access denied. Please enter the correct password.")
    st.stop()

st.title("AI-Powered Bond Selector")

st.sidebar.header("Client Profile")
profile = st.sidebar.selectbox("Choose a client profile:", [
    "USD - Income Focused",
    "EUR - Income Focused",
    "USD - Capital Gains Focused"
])

uploaded_file = st.sidebar.file_uploader("Upload Bond Data (Excel)", type=["xlsx"])

sentiment_pipeline = pipeline("sentiment-analysis")
FIGI_API_KEY = "bd64546f-c451-4e7f-b72d-441e36a868d8"
NEWS_API_KEY = "590daf1dab92494194236e3aba131e0e"
logo_path = "elxi_logo.jpg"

def fetch_news_sentiment(issuer):
    try:
        url = "https://newsapi.org/v2/everything"
        params = {"q": issuer, "apiKey": NEWS_API_KEY, "language": "en", "sortBy": "relevancy", "pageSize": 3}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            text = " ".join([article['title'] for article in articles])
            sentiment = sentiment_pipeline(text)[0]
            score = sentiment['score'] if sentiment['label'] == 'POSITIVE' else -sentiment['score']
            return score, articles
    except Exception as e:
        st.warning(f"News sentiment failed for {issuer}: {e}")
    return 0.0, []

def generate_pdf_reports(df, logo_path):
    output_dir = "bond_reports_app"
    os.makedirs(output_dir, exist_ok=True)
    pdf_paths = []

    durations = df["Duration"].tolist()
    yields = df["Coupon"].tolist()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 8))
    ax1.hist(durations, bins=5, color='skyblue', edgecolor='black')
    ax1.set_title("Bond Duration Distribution")
    ax1.set_xlabel("Years")
    ax1.set_ylabel("Number of Bonds")
    ax2.hist(yields, bins=5, color='lightgreen', edgecolor='black')
    ax2.set_title("Coupon Yield Distribution")
    ax2.set_xlabel("Coupon %")
    ax2.set_ylabel("Number of Bonds")
    chart_path = os.path.join(output_dir, "portfolio_charts.png")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    summary_pdf = FPDF()
    summary_pdf.add_page()
    summary_pdf.image(logo_path, x=10, y=8, w=40)
    summary_pdf.ln(30)
    summary_pdf.set_font("Arial", "B", 16)
    summary_pdf.cell(200, 10, "Portfolio Summary", ln=True)
    summary_pdf.set_font("Arial", "", 12)
    summary_pdf.ln(10)
    summary_pdf.cell(0, 10, f"Total Bonds: {len(df)}", ln=True)
    summary_pdf.ln(5)
    summary_pdf.set_font("Arial", "B", 12)
    summary_pdf.cell(0, 10, "Included Bonds:", ln=True)
    summary_pdf.set_font("Arial", "", 11)
    for _, row in df.iterrows():
        summary_pdf.cell(0, 10, f"{row['ISIN']} - {row['Issuer']}", ln=True)
    summary_pdf.add_page()
    summary_pdf.set_font("Arial", "B", 14)
    summary_pdf.cell(0, 10, "Portfolio Charts", ln=True)
    summary_pdf.image(chart_path, x=10, w=180)
    summary_path = os.path.join(output_dir, "00_Portfolio_Summary.pdf")
    summary_pdf.output(summary_path)

    for _, bond in df.iterrows():
        pdf = FPDF()
        pdf.add_page()
        pdf.image(logo_path, x=10, y=8, w=40)
        pdf.ln(30)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(200, 10, f"Bond Report: {bond['ISIN']}", ln=True)
        pdf.set_font("Arial", "", 12)
        explanation = f"This bond by {bond['Issuer']} offers a {bond['Coupon']}% coupon, priced at {bond['Price']}, rated {bond['Rating']}, with {bond['Duration']} years maturity and {bond['Liquidity'].lower()} liquidity."
        clean_explanation = explanation.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, 10, clean_explanation)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Recent News:", ln=True)
        pdf.set_font("Arial", "U", 11)
        for line in bond["News"].split("\n"):
            if line.strip().startswith("["):
                title = line[line.find("[")+1:line.find("]")]
                url = line[line.find("(")+1:line.find(")")]
                pdf.set_text_color(0, 0, 255)
                clean_title = title.encode("latin-1", "ignore").decode("latin-1")
        pdf.cell(0, 10, clean_title, ln=True, link=url)
        report_path = os.path.join(output_dir, f"{bond['ISIN']}_report.pdf")
        pdf.output(report_path)
        pdf_paths.append(report_path)

    zip_path = "bond_reports_app.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(summary_path, arcname=os.path.basename(summary_path))
        for path in pdf_paths:
            zipf.write(path, arcname=os.path.basename(path))
    return zip_path

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("✅ Uploaded data:")
    st.dataframe(df)

    df["Duration"] = pd.to_numeric(df["Duration"], errors="coerce")
    def is_investment_grade(r):
        return r in ["AAA", "AA+", "AA", "AA-", "A+", "A", "A-", "BBB+", "BBB", "BBB-"]
    df = df[df["Rating"].apply(is_investment_grade)]
    df = df[df["Price"] <= 100]

    sentiment_scores = []
    news_links = []
    for issuer in df["Issuer"]:
        score, articles = fetch_news_sentiment(issuer)
        sentiment_scores.append(score)
        links = "\n".join([f"[{a['title']}]({a['url']})" for a in articles])
        news_links.append(links)

    df["Sentiment"] = sentiment_scores
    df["sentiment_score"] = (df["Sentiment"] + 1) / 2
    df["News"] = news_links
    df = df[df["Duration"] <= 5]
    df["final_score"] = df["sentiment_score"]
    df = df.sort_values(by="final_score", ascending=False).reset_index(drop=True)

    st.subheader("📊 Top Recommended Bonds")
    st.dataframe(df)

    st.subheader("📥 Download All Bond Reports")
    if st.button("Generate ZIP"):
        zip_path = generate_pdf_reports(df, logo_path)
        with open(zip_path, "rb") as f:
            st.download_button("Download ZIP", f, file_name="bond_reports.zip", mime="application/zip")
else:
    st.info("Please upload a bond dataset in Excel format.")
