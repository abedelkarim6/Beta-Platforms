import magic
import pandas as pd
import streamlit as st
from utils import main

# Streamlit config
st.set_page_config(page_title="Excel Matcher", layout="wide")
st.title("🔍 Excel Matcher by Name & Amount")


# Short description
st.markdown(
    """
This tool compares two sets of financial transactions to find **matches** based on the **sender's name** and **amount**.

It identifies **unmatched entries** from both sources for manual review.

📊 **Expected Excel Format:**

- The names of the columns are not a must, **the order is the only must**.
- We can have only **4 or 6 columns** (6 in case code name and number is found)

---
"""
)

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls"])


@st.cache_data
def load_and_process(uploaded_file, file_type):
    try:
        return main(uploaded_file, file_type)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        st.error(
            "❌ The uploaded file is not a valid Excel sheet. Please upload a proper .xlsx or .xls file."
        )
        st.stop()


if uploaded_file:
    file_type = magic.from_buffer(uploaded_file.read(1024), mime=True)
    with st.spinner("Processing file..."):
        (
            matched_df1,
            matched_df2,
            semi_matched_df1,
            semi_matched_df2,
            unmatched_df1,
            unmatched_df2,
        ) = load_and_process(uploaded_file, file_type)

    # View selection
    view_option = st.radio(
        "Choose what to display:",
        ("Unmatched Entries", "Potential Matches", "Full Matches"),
        horizontal=True,
    )

    if view_option == "Unmatched Entries":
        st.subheader("❌ Unmatched Entries")

        # col1, col2 = st.columns(2)

        # with col1:
        #     st.markdown(f"**First dataset** — {len(unmatched_df1)} rows")
        #     st.dataframe(unmatched_df1, use_container_width=True, hide_index=True)

        # with col2:
        #     st.markdown(f"**Second dataset** — {len(unmatched_df2)} rows")
        #     st.dataframe(unmatched_df2, use_container_width=True, hide_index=True)

        # Sort the dfs
        unmatched_df1 = unmatched_df1.sort_values(by="amount", ascending=True)
        unmatched_df2 = unmatched_df2.sort_values(by="amount", ascending=True)

        combined_unmatched_df = pd.concat(
            [
                unmatched_df1.reset_index(drop=True),
                unmatched_df2.reset_index(drop=True),
            ],
            axis=1,
        )

        # Optionally rename columns to avoid confusion
        combined_unmatched_df.columns = [
            f"df1_{col}" for col in unmatched_df1.columns
        ] + [f"df2_{col}" for col in unmatched_df2.columns]

        # Display in one block
        st.markdown(f"**Unmatched Rows — {len(combined_unmatched_df)} pairs**")
        st.dataframe(combined_unmatched_df, use_container_width=True, hide_index=True)

    elif view_option == "Potential Matches":
        st.subheader("✅ Potential Matched Rows Based on Name & Amount")

        # Concatenate side-by-side with reset index (to align rows)
        combined_semi_df = pd.concat(
            [
                semi_matched_df1.reset_index(drop=True),
                semi_matched_df2.reset_index(drop=True),
            ],
            axis=1,
        )

        # Optionally rename columns to avoid confusion
        combined_semi_df.columns = [
            f"df1_{col}" for col in semi_matched_df1.columns
        ] + [f"df2_{col}" for col in semi_matched_df2.columns]

        # Display in one block
        st.markdown(f"**Potentially Matched Rows — {len(combined_semi_df)} pairs**")
        st.dataframe(combined_semi_df, use_container_width=True, hide_index=True)

    elif view_option == "Full Matches":
        st.subheader("✅ Full Matched Rows Based on Name & Amount")
        # Sort the dfs
        matched_df1 = matched_df1.sort_values(by="amount", ascending=True)
        matched_df2 = matched_df2.sort_values(by="amount", ascending=True)

        # Concatenate side-by-side with reset index (to align rows)
        combined_df = pd.concat(
            [
                matched_df1.reset_index(drop=True),
                matched_df2.reset_index(drop=True),
            ],
            axis=1,
        )

        # Optionally rename columns to avoid confusion
        combined_df.columns = [f"df1_{col}" for col in matched_df1.columns] + [
            f"df2_{col}" for col in matched_df2.columns
        ]

        # Display in one block
        st.markdown(f"**Matched Rows — {len(combined_df)} pairs**")
        st.dataframe(combined_df, use_container_width=True, hide_index=True)


else:
    st.info("📥 Please upload an Excel file to begin.")
