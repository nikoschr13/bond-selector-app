
import streamlit as st
import pandas as pd

# Sample display logic for bond explanation
bond = {
    'Issuer': 'U.S. Treasury',
    'Coupon': 3.5,
    'Price': 98.6,
    'Rating': 'A',
    'Duration': 4.1,
    'Liquidity': 'High'
}

# Corrected f-string
explanation = f"This bond by {bond['Issuer']} offers a {bond['Coupon']}% coupon, priced at {bond['Price']}, rated {bond['Rating']}, with {bond['Duration']} years maturity and {bond['Liquidity']} liquidity."

st.title("AI-Powered Bond Selector")
st.write(explanation)
