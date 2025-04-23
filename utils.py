import re
import pandas as pd
from fuzzywuzzy import fuzz

# ===================================================
# Cleaning Tools
# ===================================================


def split_dataframe(df):
    """
    Splits a DataFrame with 4 columns into two DataFrames each containing
    sender name and amount.
    Assumes columns are ordered as: sender_name_1, amount_1, sender_name_2, amount_2.
    """
    df = df[df.iloc[:, 0].notna()]
    df = df.dropna(axis=1, how="all")
    if len(df.columns) == 4:
        df.columns = ["sender_name_1", "amount_1", "sender_name_2", "amount_2"]
        df = df.iloc[:, :4]
        df1 = df[["sender_name_1", "amount_1"]].rename(
            columns={"sender_name_1": "sender_name", "amount_1": "amount"}
        )
        df2 = df[["sender_name_2", "amount_2"]].rename(
            columns={"sender_name_2": "sender_name", "amount_2": "amount"}
        )

    elif len(df.columns) == 6:
        df.columns = [
            "code_type",
            "code_number",
            "sender_name_1",
            "amount_1",
            "sender_name_2",
            "amount_2",
        ]
        df = df.iloc[:, :6]
        df1 = df[["code_type", "code_number", "sender_name_1", "amount_1"]].rename(
            columns={"sender_name_1": "sender_name", "amount_1": "amount"}
        )
        df2 = df[["sender_name_2", "amount_2"]].rename(
            columns={"sender_name_2": "sender_name", "amount_2": "amount"}
        )

    return df1, df2


def clean_dataframe(df):
    """
    Cleans a DataFrame by removing NaN columns, converting amount to absolute value,
    and dropping rows where both sender_name and amount are NaN.
    """
    df.amount = df.amount.abs()
    df = df.dropna(axis=1, how="all")
    return df[~(df["sender_name"].isna() & df["amount"].isna())]


def extract_clean_name(text):
    """
    Cleans and tokenizes a sender name string by removing currency symbols,
    numbers, and splitting on punctuation or whitespace.
    """
    if not isinstance(text, str):
        return []

    text = re.sub(r"(R\$|\$|USD)?\s?\d+(\.\d{1,2})?(Buy@\d+(\.\d{1,2})?)?", "", text)
    tokens = re.split(r"[ -+()@,]+", text.lower())
    return [item for item in tokens if item.strip()]


# ===================================================
# Name Matching Tools
# ===================================================


def is_name_match(name1, name2):
    """
    Determines if two names are a fuzzy match using token-wise comparison
    and fuzzy ratios.
    """
    if not isinstance(name1, str) or not isinstance(name2, str):
        return False

    tokens1 = extract_clean_name(name1)
    tokens2 = extract_clean_name(name2)

    if not tokens1 or not tokens2:
        return False

    for t1 in tokens1:
        for t2 in tokens2:
            if (
                fuzz.ratio(t1, t2) >= 75
                or fuzz.partial_ratio(t1, t2) >= 75
                or t1 in t2
                or t2 in t1
            ):
                return True

    joined1 = " ".join(tokens1)
    joined2 = " ".join(tokens2)
    return fuzz.token_set_ratio(joined1, joined2) >= 75


def is_name_match_1(name1, name2):
    """
    Lightweight name match function using substring token comparison.
    """
    tokens1 = extract_clean_name(name1)
    tokens2 = extract_clean_name(name2)
    for t1 in tokens1:
        for t2 in tokens2:
            if t1 in t2 or t2 in t1:
                return True
    return False


# ===================================================
# Matching Tools
# ===================================================


def find_unmatched_rows(df1, df2):
    """
    Compares two DataFrames and returns rows from both that have no matching
    (amount + name) in the other. Uses a lightweight name match.
    """
    unmatched_df1 = []
    unmatched_df2 = []

    for i1, row1 in df1.iterrows():
        matched = False
        for i2, row2 in df2.iterrows():
            if row1["amount"] == row2["amount"] and is_name_match_1(
                row1["sender_name"], row2["sender_name"]
            ):
                matched = True
                df2.at[i2, "matched"] = True
                break
        if not matched:
            unmatched_df1.append(row1)

    for i2, row2 in df2.iterrows():
        if not row2.get("matched", False):
            unmatched_df2.append(row2)

    return pd.DataFrame(unmatched_df1).reset_index(drop=True), pd.DataFrame(
        unmatched_df2
    ).reset_index(drop=True)


def match_names_on_amount(df1, df2):
    """
    Matches rows from two DataFrames based on equal amounts and fuzzy name match.
    Returns matched pairs along with unmatched rows from both DataFrames.
    """
    matched_rows = []
    matched_indices_df1 = set()
    matched_indices_df2 = set()

    for i, row1 in df1.iterrows():
        amount1 = row1["amount"]
        name1 = row1["sender_name"]

        matching_df2 = df2[df2["amount"] == amount1]

        for j, row2 in matching_df2.iterrows():
            name2 = row2["sender_name"]

            if is_name_match(name1, name2):
                matched_rows.append(
                    {
                        "df1_index": i,
                        "df1_name": name1,
                        "df1_amount": amount1,
                        "df2_index": j,
                        "df2_name": name2,
                        "df2_amount": row2["amount"],
                    }
                )
                matched_indices_df1.add(i)
                matched_indices_df2.add(j)
                break  # one-to-one match

    matched_df = pd.DataFrame(matched_rows)
    unmatched_df1 = df1[~df1.index.isin(matched_indices_df1)].copy()
    unmatched_df2 = df2[~df2.index.isin(matched_indices_df2)].copy()

    return matched_df, unmatched_df1, unmatched_df2


# ===================================================
# Main Function
# ===================================================


def main(uploaded, file_type):
    """
    Main function to load, clean, and match transaction data from Excel file.
    Returns:
        matched_df: Matched transactions between df1 and df2.
        unmatched_df1: Transactions from df1 with no match.
        unmatched_df2: Transactions from df2 with no match.
    """
    if file_type == "xls":
        df = pd.read_excel(uploaded, engine="xlrd")
    else:
        df = pd.read_excel(uploaded)

    # Split and clean
    df1, df2 = split_dataframe(df)
    df1 = clean_dataframe(df1)
    df2 = clean_dataframe(df2)

    # Pre-filter unmatched using lightweight comparison
    unmatched_df1, _ = find_unmatched_rows(df1, df2)
    unmatched_df2, _ = find_unmatched_rows(df2, df1)

    # Run full fuzzy matching
    matched_df, unmatched_df1, unmatched_df2 = match_names_on_amount(
        unmatched_df1, unmatched_df2
    )

    # Final cleanup
    matched_df = matched_df.drop(columns=["df1_index", "df2_index"])
    matched_df1, matched_df2 = split_dataframe(matched_df)
    if "matched" in unmatched_df2.columns:
        unmatched_df2 = unmatched_df2.drop("matched", axis=1)

    return matched_df1, matched_df2, unmatched_df1, unmatched_df2
