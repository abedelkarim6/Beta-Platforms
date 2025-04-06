import streamlit as st
import pandas as pd

st.set_page_config(page_title="Excel Matcher", layout="centered")
st.title("📊 Excel Sheet Comparator")


# Function to load and prepare the Excel files
def load_and_prepare(file):
    df = pd.read_excel(file)
    df = df[["sender_name", "amount"]]  # Ensure only required columns
    df.dropna(subset=["sender_name", "amount"], inplace=True)
    df["sender_name"] = df["sender_name"].astype(str).str.lower().str.strip()
    return df


# First comparison logic (match and unmatched)
def find_matches(df1, df2):
    matched_indices = set()
    unmatched = []

    for i1, row1 in df1.iterrows():
        name1_words = set(row1["sender_name"].split())
        amount1 = row1["amount"]
        found_match = False

        for i2, row2 in df2.iterrows():
            name2_words = set(row2["sender_name"].split())
            amount2 = row2["amount"]

            if name1_words & name2_words:  # common words
                found_match = True
                if amount1 != amount2:
                    unmatched.append(row1.to_dict())
                break

        if not found_match:
            unmatched.append(row1.to_dict())

    return unmatched


# Second comparison logic (missing and mismatched amounts)
def split_matches(df1, df2):
    missing = []
    mismatched = []

    for _, row1 in df1.iterrows():
        name1_words = set(row1["sender_name"].split())
        amount1 = row1["amount"]
        found_match = False

        for _, row2 in df2.iterrows():
            name2_words = set(row2["sender_name"].split())
            amount2 = row2["amount"]

            if name1_words & name2_words:
                found_match = True
                if amount1 != amount2:
                    mismatched.append(
                        {
                            "sender_name": row1["sender_name"],
                            "amount_file1": amount1,
                            "amount_file2": amount2,
                        }
                    )
                break

        if not found_match:
            missing.append(row1.to_dict())

    return missing, mismatched


# Function to compare two files using the first method (match/unmatched)
def compare_excels_method_1(file1, file2):
    df1 = load_and_prepare(file1)
    df2 = load_and_prepare(file2)

    unmatched1 = find_matches(df1, df2)
    unmatched2 = find_matches(df2, df1)

    return unmatched1, unmatched2


# Function to compare two files using the second method (missing/mismatched)
def compare_excels_method_2(file1, file2):
    df1 = load_and_prepare(file1)
    df2 = load_and_prepare(file2)

    missing1, mismatched1 = split_matches(df1, df2)
    missing2, mismatched2 = split_matches(df2, df1)

    return missing1, mismatched1, missing2, mismatched2


# File upload interface
file1 = st.file_uploader("Upload File 1", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload File 2", type=["xlsx", "xls"])

if file1 and file2:
    # Select method to use
    method = st.radio(
        "Choose comparison method:",
        ("Method 1: Match/Unmatched", "Method 2: Missing/Mismatched"),
    )

    if method == "Method 1: Match/Unmatched":
        with st.spinner("Comparing..."):
            unmatched1, unmatched2 = compare_excels_method_1(file1, file2)

        st.subheader("🔴 Rows in File 1 not matching File 2")
        if unmatched1:
            st.dataframe(pd.DataFrame(unmatched1))
        else:
            st.success("✅ All rows in File 1 matched with File 2.")

        st.subheader("🔵 Rows in File 2 not matching File 1")
        if unmatched2:
            st.dataframe(pd.DataFrame(unmatched2))
        else:
            st.success("✅ All rows in File 2 matched with File 1.")

    elif method == "Method 2: Missing/Mismatched":
        with st.spinner("Comparing..."):
            missing1, mismatched1, missing2, mismatched2 = compare_excels_method_2(
                file1, file2
            )

        st.subheader("🔴 Missing in File 2 (From File 1)")
        if missing1:
            st.dataframe(pd.DataFrame(missing1))
        else:
            st.success("✅ No missing entries from File 1 in File 2.")

        st.subheader("🟠 Amount Mismatches (File 1 vs File 2)")
        if mismatched1:
            st.dataframe(pd.DataFrame(mismatched1))
        else:
            st.success("✅ No amount mismatches from File 1 in File 2.")

        st.markdown("---")

        st.subheader("🔵 Missing in File 1 (From File 2)")
        if missing2:
            st.dataframe(pd.DataFrame(missing2))
        else:
            st.success("✅ No missing entries from File 2 in File 1.")

        st.subheader("🟡 Amount Mismatches (File 2 vs File 1)")
        if mismatched2:
            st.dataframe(pd.DataFrame(mismatched2))
        else:
            st.success("✅ No amount mismatches from File 2 in File 1.")
