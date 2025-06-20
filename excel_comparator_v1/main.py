import pandas as pd

from utils import *


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
