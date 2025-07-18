import streamlit as st
import pandas as pd
from pathlib import Path

CSV_PATH = "data/rates.csv"

st.set_page_config(page_title="Rates Management", layout="wide")
st.title("💱 Rates Management")


# Helper: linked margin inputs with dynamic calculation
def margin_input(label, official_rate, margin_type, key_prefix=""):
    col1, col2 = st.columns(2)
    
    with col1:
        if margin_type.lower() == "percent":
            # User can input percentage, points will be calculated
            margin_pct = st.number_input(
                f"{label} Margin (%)", 
                value=0.0, 
                format="%.4f", 
                key=f"{key_prefix}_pct"
            )
            # Calculate points based on percentage
            margin_pts = (margin_pct / 100 * official_rate) if official_rate else 0
        else:
            # Points mode - percentage is calculated, so show as disabled
            margin_pct = st.number_input(
                f"{label} Margin (%)", 
                value=(st.session_state.get(f"{key_prefix}_pts", 0) / official_rate * 100) if official_rate else 0,
                format="%.4f", 
                key=f"{key_prefix}_pct_display",
                disabled=True
            )
    
    with col2:
        if margin_type.lower() == "points":
            # User can input points, percentage will be calculated
            margin_pts = st.number_input(
                f"{label} Margin (pts)", 
                value=0.0, 
                format="%.4f", 
                key=f"{key_prefix}_pts"
            )
            # Calculate percentage based on points
            margin_pct = (margin_pts / official_rate * 100) if official_rate else 0
        else:
            # Percentage mode - points is calculated, so show as disabled
            margin_pts = st.number_input(
                f"{label} Margin (pts)", 
                value=(st.session_state.get(f"{key_prefix}_pct", 0) / 100 * official_rate) if official_rate else 0,
                format="%.4f", 
                key=f"{key_prefix}_pts_display",
                disabled=True
            )

    return margin_pct, margin_pts


# Load existing data or create new DataFrame
if Path(CSV_PATH).exists():
    df = pd.read_csv(CSV_PATH)
else:
    df = pd.DataFrame(
        columns=[
            "from_currency",
            "to_currency",
            "mode",
            "official_rate",
            "margin_type",
            "buy_margin_value",
            "sell_margin_value",
            "buy_rate",
            "sell_rate",
            "extra_fees",
        ]
    )

# Initialize session state
if "rate_table" not in st.session_state:
    st.session_state.rate_table = df.copy()

# === Form UI ===
st.subheader("➕ Add New Rate")
from_currency = st.text_input("From Currency", placeholder="e.g. USD")
to_currency = st.text_input("To Currency", placeholder="e.g. LBP")
mode = st.radio(
    "Select Mode", ["Official Rate + Margin", "Direct Buy/Sell Rates"], horizontal=True
)

if mode == "Official Rate + Margin":
    st.markdown("### 📊 Margin-based Calculation")
    official_rate = st.number_input("Official Rate", min_value=0.0, format="%.4f")
    margin_type = st.radio("Margin Type", ["Percent", "Points"], horizontal=True)

    buy_margin_pct, buy_margin_val = margin_input(
        "Buy", official_rate, margin_type, "buy"
    )
    sell_margin_pct, sell_margin_val = margin_input(
        "Sell", official_rate, margin_type, "sell"
    )

    buy_rate = official_rate + buy_margin_val
    sell_rate = official_rate + sell_margin_val

    st.success(f"Buy Rate = {buy_rate:.4f}")
    st.success(f"Sell Rate = {sell_rate:.4f}")

else:
    st.markdown("### ✍️ Direct Entry")
    buy_rate = st.number_input("Buy Rate", min_value=0.0, format="%.4f")
    sell_rate = st.number_input("Sell Rate", min_value=0.0, format="%.4f")
    official_rate = 0.0
    margin_type = ""
    buy_margin_val = 0.0
    sell_margin_val = 0.0

extra_fees = st.number_input("Extra Fees", min_value=0.0, format="%.4f")

if st.button("✅ Add Rate"):
    if not from_currency or not to_currency:
        st.error("Both From Currency and To Currency are required.")
    elif mode == "Official Rate + Margin" and official_rate <= 0:
        st.error("Official rate must be greater than zero.")
    elif mode == "Direct Buy/Sell Rates" and (buy_rate <= 0 or sell_rate <= 0):
        st.error("Buy and Sell rates must be greater than zero.")
    else:
        new_row = {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "mode": mode,
            "official_rate": official_rate,
            "margin_type": margin_type,
            "buy_margin_value": buy_margin_val,
            "sell_margin_value": sell_margin_val,
            "buy_rate": buy_rate,
            "sell_rate": sell_rate,
            "extra_fees": extra_fees,
        }
        df = pd.concat(
            [st.session_state.rate_table, pd.DataFrame([new_row]).dropna(how="all")],
            ignore_index=True,
        )
        df.to_csv(CSV_PATH, index=False)
        st.session_state.rate_table = df.copy()
        st.success(f"✅ Rate for {from_currency}/{to_currency} added successfully!")
        st.rerun()

# === Show Table ===
st.divider()
st.subheader("📄 Existing Rates")

# Update the column names for display
edited_df = st.data_editor(
    st.session_state.rate_table[["from_currency", "to_currency", "mode", "official_rate", "buy_rate", "sell_rate", "extra_fees"]],
    use_container_width=True,
    num_rows="dynamic",
    key="rates_editor",
)

# Save changes made via the editor
if not edited_df.equals(st.session_state.rate_table[["from_currency", "to_currency", "mode", "official_rate", "buy_rate", "sell_rate", "extra_fees"]]):
    st.session_state.rate_table = edited_df.reset_index(drop=True)

if st.button("💾 Save Changes"):
    st.session_state.rate_table.to_csv(CSV_PATH, index=False)
    st.success("Rates saved to Excel !")
            