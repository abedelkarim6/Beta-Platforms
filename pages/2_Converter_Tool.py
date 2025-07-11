# import streamlit as st
# import pandas as pd

# CSV_PATH = "data/rates.csv"

# st.title("🔄 Converter Tool")

# # Load rates
# df = pd.read_csv(CSV_PATH)
# if df.empty or "pair" not in df.columns:
#     st.warning("No rate data available.")
#     st.stop()

# pairs = df["pair"].dropna().unique()
# selected_pair = st.selectbox("Currency Pair", pairs)

# # Get latest row for the selected pair
# rate_data = df[df["pair"] == selected_pair].iloc[-1]

# # Choose direction
# rate_used = st.radio("Select Rate Type", ["Buy", "Sell"])
# rate_value = rate_data["buy_rate"] if rate_used == "Buy" else rate_data["sell_rate"]

# # Margin calculation
# official_rate = rate_data.get("official_rate", 0)
# margin_type = rate_data.get("margin_type", "")

# if margin_type == "percent" and official_rate > 0:
#     margin_percent = (
#         ((rate_value - official_rate) / official_rate) * 100 if official_rate > 0 else 0
#     )
# elif margin_type == "points" and official_rate > 0:
#     margin_percent = ((rate_value - official_rate) / official_rate) * 100
# else:
#     margin_percent = 0

# # Conversion inputs
# col1, col2 = st.columns(2)
# from_currency, to_currency = selected_pair.split("/")

# with col1:
#     from_amount = st.number_input(f"From {from_currency}", value=0.0, key="from_amt")

# with col2:
#     to_amount = st.number_input(f"To {to_currency}", value=0.0, key="to_amt")

# # Compute missing value
# if from_amount > 0 and to_amount == 0:
#     to_amount = (
#         from_amount / rate_value if rate_used == "Sell" else from_amount * rate_value
#     )
# elif to_amount > 0 and from_amount == 0:
#     from_amount = (
#         to_amount * rate_value if rate_used == "Sell" else to_amount / rate_value
#     )

# # Show rate used and margin
# st.markdown(
#     f"**Rate Used**: {rate_value:.4f} ({rate_used})  \n"
#     f"**Margin %**: {margin_percent:.2f}%"
# )

# # Apply extra fee
# apply_fee = st.checkbox("Include extra fee?")
# extra_fee_pct = (
#     st.number_input("Fee %", min_value=0.0, max_value=100.0, step=0.1)
#     if apply_fee
#     else 0.0
# )

# final_amount = to_amount * (1 - extra_fee_pct / 100)

# # Final result
# st.success(f"✅ Final Converted Amount: {final_amount:.4f}")
import streamlit as st
import pandas as pd

CSV_PATH = "data/rates.csv"

st.set_page_config(layout="wide")
st.title("🔄 Converter Tool")

# Load rates
df = pd.read_csv(CSV_PATH)
pairs = df["pair"].dropna().unique()
selected_pair = st.selectbox("Currency Pair", pairs)

row = df[df["pair"] == selected_pair].iloc[-1]
currency1, currency2 = selected_pair.split("/")

# Rates
rate_forward = row["sell_rate"]  # currency1 -> currency2
rate_backward = row["buy_rate"]  # currency2 -> currency1

# Initialize session state amounts
if "amount1" not in st.session_state:
    st.session_state.amount1 = 1.0
if "amount2" not in st.session_state:
    st.session_state.amount2 = st.session_state.amount1 * rate_forward

# Track which input was last changed
if "last_changed" not in st.session_state:
    st.session_state.last_changed = "amount1"


def on_amount1_change():
    st.session_state.last_changed = "amount1"
    # Convert amount1 to amount2 using forward rate
    st.session_state.amount2 = st.session_state.amount1 * rate_forward


def on_amount2_change():
    st.session_state.last_changed = "amount2"
    # Convert amount2 to amount1 using backward rate
    st.session_state.amount1 = st.session_state.amount2 / rate_backward


col1, col2 = st.columns(2)

with col1:
    st.number_input(
        f"{currency1}",
        key="amount1",
        value=st.session_state.amount1,
        on_change=on_amount1_change,
        format="%.4f",
    )

with col2:
    st.number_input(
        f"{currency2}",
        key="amount2",
        value=st.session_state.amount2,
        on_change=on_amount2_change,
        format="%.4f",
    )

st.markdown(
    f"**Rate Used:** {rate_forward:.4f} ({currency1} → {currency2}) and {rate_backward:.4f} ({currency2} → {currency1})"
)
