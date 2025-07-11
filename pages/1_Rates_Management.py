import streamlit as st
import pandas as pd
from pathlib import Path

CSV_PATH = "data/rates.csv"

st.set_page_config(page_title="Rates Management", layout="wide")
st.title("💱 Rates Management")


# Helper: linked margin inputs
def margin_input(label, official_rate, margin_type, key_prefix=""):
    col1, col2 = st.columns(2)
    with col1:
        margin_pct = st.number_input(
            f"{label} Margin (%)", value=0.0, format="%.4f", key=f"{key_prefix}_pct"
        )
    with col2:
        margin_pts = st.number_input(
            f"{label} Margin (pts)", value=0.0, format="%.4f", key=f"{key_prefix}_pts"
        )

    if margin_type == "points":
        margin_pct = (margin_pts / official_rate * 100) if official_rate else 0
    else:
        margin_pts = (margin_pct / 100 * official_rate) if official_rate else 0

    return margin_pct, margin_pts


# Load existing data or create new DataFrame
if Path(CSV_PATH).exists():
    df = pd.read_csv(CSV_PATH)
else:
    df = pd.DataFrame(
        columns=[
            "pair",
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
pair = st.text_input("Currency Pair", placeholder="e.g. USDT/LBP")
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
    if not pair:
        st.error("Currency pair is required.")
    elif mode == "Official Rate + Margin" and official_rate <= 0:
        st.error("Official rate must be greater than zero.")
    elif mode == "Direct Buy/Sell Rates" and (buy_rate <= 0 or sell_rate <= 0):
        st.error("Buy and Sell rates must be greater than zero.")
    else:
        new_row = {
            "pair": pair,
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
        st.success(f"✅ Rate for {pair} added successfully!")
        st.rerun()

# === Show Table ===
st.divider()
st.subheader("📄 Existing Rates")

edited_df = st.data_editor(
    st.session_state.rate_table,
    use_container_width=True,
    num_rows="dynamic",
    key="rates_editor",
)

# Save changes made via the editor
if not edited_df.equals(st.session_state.rate_table):
    st.session_state.rate_table = edited_df.reset_index(drop=True)

if st.button("💾 Save Changes"):
    st.session_state.rate_table.to_csv(CSV_PATH, index=False)
    st.success("Rates saved to Excel!")
