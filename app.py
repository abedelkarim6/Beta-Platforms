import magic
import streamlit as st
from utils import main

# Streamlit config
st.set_page_config(page_title="Excel Matcher", layout="wide")
st.title("🔍 Excel Matcher by Name & Amount")


# Short description
st.markdown(
    """
This tool compares two sets of financial transactions to find **matches** based on the **sender's name** and **amount**.

It identifies **unmatched entries** from both sources for manual review. Where each row represents a possible match between two records.

📊 **Expected Excel Format:**

The uploaded Excel file should have **four columns**, structured as:

- `sender_name_1` | `amount_1` | `sender_name_2` | `amount_2`

The names of the columns are not a must, **the order is the only must**.


---
"""
)

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])


@st.cache_data
def load_and_process(uploaded_file, file_type):
    return main(uploaded_file, file_type)


if uploaded_file:
    file_type = magic.from_buffer(uploaded_file.read(1024), mime=True)
    with st.spinner("Processing file..."):
        matched_df1, matched_df2, unmatched_df1, unmatched_df2 = load_and_process(
            uploaded_file, file_type
        )

    # View selection
    view_option = st.radio(
        "Choose what to display:",
        ("Unmatched Entries", "Potential Matches"),
        horizontal=True,
    )

    if view_option == "Unmatched Entries":
        st.subheader("❌ Unmatched Entries")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**First dataset** — {len(unmatched_df1)} rows")
            st.dataframe(unmatched_df1, use_container_width=True)

        with col2:
            st.markdown(f"**Second dataset** — {len(unmatched_df2)} rows")
            st.dataframe(unmatched_df2, use_container_width=True)

    elif view_option == "Potential Matches":
        st.subheader("✅ Potential Matched Rows Based on Name & Amount")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown(f"**First dataset** — {len(matched_df1)} rows")
            st.dataframe(matched_df1, use_container_width=True)

        with col4:
            st.markdown(f"**Second dataset** — {len(matched_df2)} rows")
            st.dataframe(matched_df2, use_container_width=True)
else:
    st.info("📥 Please upload an Excel file to begin.")
