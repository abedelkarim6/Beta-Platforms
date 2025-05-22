import re
import pandas as pd
from fuzzywuzzy import fuzz

# ===================================================
# Cleaning Tools
# ===================================================
counter1 = 0
counter2 = 0
counter3 = 0


def split_dataframe(df):
    """
    Splits a DataFrame with 4 columns into two DataFrames each containing
    sender name and amount.
    Assumes columns are ordered as: sender_name_1, amount_1, sender_name_2, amount_2.
    """
    try:
        df = df.dropna(axis=1, how="all")
        df = df.dropna(how="all")

        if len(df.columns) == 4 or len(df.columns) == 5:
            print("Number of columns: ", len(df.columns))
            df = df.iloc[:, :4]
            df.columns = ["name1", "amount1", "name2", "amount2"]
            df.columns = ["sender_name_1", "amount_1", "sender_name_2", "amount_2"]
            df1 = df[["sender_name_1", "amount_1"]].rename(
                columns={"sender_name_1": "sender_name", "amount_1": "amount"}
            )
            df2 = df[["sender_name_2", "amount_2"]].rename(
                columns={"sender_name_2": "sender_name", "amount_2": "amount"}
            )

        elif len(df.columns) == 6:
            print("Number of columns: ", len(df.columns))
            df = df.iloc[:, :6]
            df.columns = [
                "code_type",
                "code_number",
                "sender_name_1",
                "amount_1",
                "sender_name_2",
                "amount_2",
            ]
            df1 = df[["code_type", "code_number", "sender_name_1", "amount_1"]].rename(
                columns={"sender_name_1": "sender_name", "amount_1": "amount"}
            )
            df2 = df[["sender_name_2", "amount_2"]].rename(
                columns={"sender_name_2": "sender_name", "amount_2": "amount"}
            )

        return df1.dropna(axis=0, how="all"), df2.dropna(axis=0, how="all")

    except Exception as e:
        print("The error is probably due to number of columns is neither 4/5/6")
        print("Error in split_dataframe: ", e)
        return None, None


def clean_dataframe(df):
    """
    amount: make it + in case its -
    sender_name: clean it by removing currency symbols, numbers, and splitting on punctuation or whitespace, transforms it to list of tokens
    """
    df.amount = df.amount.abs()

    df["sender_name"] = df["sender_name"].fillna("").astype(str)
    df["sender_name"] = df["sender_name"].str.lower()
    df["sender_name"] = df["sender_name"].apply(extract_clean_name)
    return df


def extract_clean_name(text):
    """
    Cleans and tokenizes a sender name string by removing currency symbols,
    numbers, and splitting on punctuation or whitespace.
    """
    if not isinstance(text, str):
        return []

    text = re.sub(r"(R\$|\$|USD)?\s?\d+(\.\d{1,2})?(Buy@\d+(\.\d{1,2})?)?", "", text)
    tokens = re.split(r"[ \-\+\(\)@,]+", text.lower())
    return [item for item in tokens if item.strip()]


# ===================================================
# Name Matching Tools
# ===================================================


def is_name_match_1(tokens1, tokens2):
    """
    Layer 1: name match function using substring token comparison.
    """
    global counter1

    if all(word in tokens1[:3] for word in tokens2 if len(word) > 2):
        counter1 += 1
        return True
    else:
        return False


def is_name_match_2(tokens1, tokens2):
    """
    Determines if two names are a fuzzy match using token-wise comparison
    and fuzzy ratios.
    """
    global counter2
    global counter3

    if not tokens1 or not tokens2:
        return False

    all_matched = True
    for t2 in tokens2:
        matched = False
        for t1 in tokens1[:3]:
            if (
                fuzz.partial_ratio(t1, t2) >= 80
                # or t1 in t2)
                and len(t1) >= 2
                and len(t2) >= 2
            ):
                counter2 += 1
                matched = True
                break
        if not matched:
            all_matched = False
            break  # if any word doesn't match, we stop
    if all_matched:
        return True

    joined1 = " ".join(tokens1)
    joined2 = " ".join(tokens2)
    # this comparison catches partial matches, even if 1 string has additional messy words
    if fuzz.partial_ratio(joined1, joined2) >= 80:
        counter3 += 1
        return True

    return False


# ===================================================
# Matching Tools
# ===================================================


# layer 1 of matching
def find_unmatched_rows(df1, df2):
    """
    Compares two DataFrames and returns rows from both that have no matching
    (amount + name) in the other. Uses a lightweight name match.
    """
    unmatched_df1 = []
    unmatched_df2 = []
    matched_df1 = []
    matched_df2 = []
    df1["matched"] = False  # Ensure the column exists and is False by default
    df2["matched"] = False  # Ensure the column exists and is False by default

    # iterate over df1 to find a match with df2, incase not found, add to unmatched_df1
    for i2, row2 in df2.iterrows():
        matched = False

        for i1, row1 in df1.iterrows():
            if not df1.at[i1, "matched"] and not df2.at[i2, "matched"]:
                if row1["amount"] == row2["amount"]:
                    tokens1 = row1["sender_name"]
                    tokens2 = row2["sender_name"]

                    if is_name_match_1(tokens1, tokens2):
                        matched = True
                        df1.at[i1, "matched"] = True
                        df2.at[i2, "matched"] = True
                        break
        if not matched:
            unmatched_df2.append(row2)

        else:
            matched_df2.append(row2)

    # iterate over df1 to fill unmatched_df1 with rows that were not matched
    for i1, row1 in df1.iterrows():
        if not row1["matched"]:
            unmatched_df1.append(row1)
        else:
            matched_df1.append(row1)

    # Transforms list into dataframes
    unmatched_df1, unmatched_df2 = pd.DataFrame(unmatched_df1).reset_index(
        drop=True
    ), pd.DataFrame(unmatched_df2).reset_index(drop=True)
    matched_df1, matched_df2 = pd.DataFrame(matched_df1).reset_index(
        drop=True
    ), pd.DataFrame(matched_df2).reset_index(drop=True)

    # returns 2 dataframes with unmatched rows
    return unmatched_df1, unmatched_df2, matched_df1, matched_df2


# layer 2 of matching
def match_similar_names_on_amount(df1, df2):
    """
    Matches rows from two DataFrames based on equal amounts and fuzzy name match.
    Returns matched pairs along with unmatched rows from both DataFrames.
    """
    matched_rows = []
    matched_indices_df1 = set()
    matched_indices_df2 = set()

    for i, row2 in df2.iterrows():
        amount2 = row2["amount"]
        tokens2 = row2["sender_name"]

        matching_df1 = df1[df1["amount"] == amount2]

        for j, row1 in matching_df1.iterrows():
            if j in matched_indices_df1:
                continue
            tokens1 = row1["sender_name"]
            if is_name_match_2(tokens1, tokens2):
                matched_rows.append(
                    {
                        "df1_index": j,
                        "df1_name": " ".join(tokens1),
                        "df1_amount": row1["amount"],
                        "df2_index": i,
                        "df2_name": " ".join(tokens2),
                        "df2_amount": amount2,
                    }
                )

                matched_indices_df1.add(j)
                matched_indices_df2.add(i)
                break  # one-to-one match

    matched_df = pd.DataFrame(matched_rows)

    unmatched_df1 = df1[~df1.index.isin(matched_indices_df1)].copy()
    unmatched_df2 = df2[~df2.index.isin(matched_indices_df2)].copy()

    # returns tokens into 1 string
    unmatched_df1["sender_name"] = unmatched_df1["sender_name"].apply(
        lambda x: " ".join(x) if isinstance(x, list) else x
    )
    unmatched_df2["sender_name"] = unmatched_df2["sender_name"].apply(
        lambda x: " ".join(x) if isinstance(x, list) else x
    )

    if "matched" in unmatched_df2.columns:
        unmatched_df2 = unmatched_df2.drop("matched", axis=1)
    if "matched" in unmatched_df1.columns:
        unmatched_df1 = unmatched_df1.drop("matched", axis=1)
    return matched_df, unmatched_df1, unmatched_df2


# ===================================================
# Main Function
# ===================================================


def main(uploaded, file_type):
    """
    Loads, cleans, and matches transaction data from an Excel file.

    Returns:
        matched_df1, matched_df2: Matched transactions.
        semi_matched_df1, semi_matched_df2: Fuzzy matched transactions.
        unmatched_df1, unmatched_df2: Unmatched transactions.
    """

    # Load Excel file with appropriate engine
    read_engine = "xlrd" if file_type == "xls" else None
    df = pd.read_excel(uploaded, engine=read_engine, header=None)

    # Clean and split data
    df1, df2 = map(clean_dataframe, split_dataframe(df))

    # Lightweight filtering to find potential matches
    unmatched_df1, unmatched_df2, matched_df1, matched_df2 = find_unmatched_rows(
        df1, df2
    )

    # Fuzzy matching on remaining unmatched data
    semi_matched_df, unmatched_df1, unmatched_df2 = match_similar_names_on_amount(
        unmatched_df1, unmatched_df2
    )

    # Clean up fuzzy matched data
    semi_matched_df.drop(
        columns=["df1_index", "df2_index"], errors="ignore", inplace=True
    )
    semi_matched_df1, semi_matched_df2 = split_dataframe(semi_matched_df)
    for df in [semi_matched_df2, matched_df1, matched_df2]:
        df.drop(columns=["matched"], errors="ignore", inplace=True)

    # Ensure sender_name is consistently formatted
    for df in [matched_df1, matched_df2]:
        df["sender_name"] = df["sender_name"].apply(
            lambda x: " ".join(x) if isinstance(x, list) else x
        )

    return (
        matched_df1,
        matched_df2,
        semi_matched_df1,
        semi_matched_df2,
        unmatched_df1,
        unmatched_df2,
    )
