import streamlit as st

st.set_page_config(page_title="Currency Exchange App", layout="centered")
st.title("💱 Currency Exchange Dashboard")
st.markdown(
    """
Welcome to your custom currency exchange management system.  
Use the sidebar to navigate:
- **Rates Management**: Set and update exchange rates with your margin.
- **Converter Tool**: Real-time currency conversion with optional fees.
- **Customers**: Manage frequent customers and apply personalized rates.
"""
)
