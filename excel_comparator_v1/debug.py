from utils import *
import pandas as pd


def filter_rows_by_value(df, column_name, value):
    """
    Returns rows from the DataFrame where the specified column matches the given value.

    Parameters:
    df (pd.DataFrame): The DataFrame to filter.
    column_name (str): The column to check.
    value (any): The value to match in the column.

    Returns:
    pd.DataFrame: Filtered DataFrame with matching rows.
    """
    return df[df[column_name] == value]


excel_path = r"C:\Users\abede\OneDrive\Desktop\aboudi\OnlyTech\SideProjects\TRK_Project\excel-comparator\excel_data\14141477.xls"

file_type = excel_path.split(".")[-1]

if file_type == "xls":
    df = pd.read_excel(excel_path, engine="xlrd")
else:
    df = pd.read_excel(excel_path)

# Split and clean
df1, df2 = split_dataframe(df)
df1 = clean_dataframe(df1)
df2 = clean_dataframe(df2)

###########################################################################
print("df shape: ", df.shape)
print("df1 shape: ", df1.shape)
print("df2 shape: ", df2.shape)
print("---" * 50)
print()
###########################################################################

# Pre-filter unmatched using lightweight comparison
unmatched_df1, unmatched_df2, matched_df1, matched_df2 = find_unmatched_rows(df1, df2)


###########################################################################
print("Layer 1 outputs:")
print("unmatched_df1 shape: ", unmatched_df1.shape)
print("unmatched_df2 shape: ", unmatched_df2.shape)

print("matched_df1 shape: ", matched_df1.shape)
print("matched_df2 shape: ", matched_df2.shape)
print("---" * 50)
print()
###########################################################################

# Run full fuzzy matching
semi_matched_df, unmatched_df1, unmatched_df2 = match_similar_names_on_amount(
    unmatched_df1,
    unmatched_df2,
)


###########################################################################
print("Layer 2 outputs:")
print("unmatched_df1 shape: ", unmatched_df1.shape)
print("unmatched_df2 shape: ", unmatched_df2.shape)
print("semi_matched_df shape: ", semi_matched_df.shape)

print("---" * 50)
print()
###########################################################################


# Clean up fuzzy matched data
semi_matched_df.drop(columns=["df1_index", "df2_index"], errors="ignore", inplace=True)
semi_matched_df1, semi_matched_df2 = split_dataframe(semi_matched_df)
for df in [semi_matched_df2, matched_df1, matched_df2]:
    df.drop(columns=["matched"], errors="ignore", inplace=True)

###########################################################################
print("After cleaning up:")
print("semi_matched_df shape: ", semi_matched_df.shape)
###########################################################################

# Ensure sender_name is consistently formatted
for df in [matched_df1, matched_df2]:
    df["sender_name"] = df["sender_name"].apply(
        lambda x: " ".join(x) if isinstance(x, list) else x
    )
