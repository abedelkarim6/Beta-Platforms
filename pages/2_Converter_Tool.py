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
from pages.Customers import fetch_customers, fetch_customer_ranges
CSV_PATH = "data/rates.csv"
st.set_page_config(layout="wide")
st.title("🔄 Converter Tool")

# Load rates
df = pd.read_csv(CSV_PATH)
pairs = df["pair"].dropna().unique()
selected_pair = st.selectbox("Currency Pair", pairs)
row = df[df["pair"] == selected_pair].iloc[-1]
currency1, currency2 = selected_pair.split("/")

# Fetch customers for display
customers_df = fetch_customers()  # Assuming you have this function in customer.py
if customers_df.empty:
    st.warning("No customers available.")
    st.stop()

# Display customer selection
customer_names = customers_df["name"].unique()  # Assuming 'name' is the customer name column
selected_customer = st.selectbox("Select Customer", customer_names)

# Fetch customer ranges based on selected customer
customer_id = customers_df[customers_df["name"] == selected_customer]["id"].iloc[0]
customer_ranges_df = fetch_customer_ranges(customer_id)

if customer_ranges_df.empty:
    st.warning(f"No range data available for {selected_customer}.")
else:
    st.markdown(f"### Ranges for {selected_customer}")
    st.dataframe(customer_ranges_df)  # Display the customer's range data

# Extra fees toggle
exclude_fees = st.checkbox("🚫 Exclude Extra Fees", value=False)

# Get extra fees
extra_fees = row.get("extra_fees", 0) if not exclude_fees else 0

# Rates (with or without extra fees)
rate_forward = row["sell_rate"] + extra_fees  # currency1 -> currency2
rate_backward = row["buy_rate"] + extra_fees  # currency2 -> currency1

# Get official rate and calculate margin percentages
official_rate = row.get("official_rate", 0)
if official_rate > 0:
    # Calculate margin percentages (including fees if not excluded)
    sell_margin_pct = ((rate_forward - official_rate) / official_rate) * 100
    buy_margin_pct = ((rate_backward - official_rate) / official_rate) * 100
else:
    sell_margin_pct = 0
    buy_margin_pct = 0

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

# Display rates with margin information
st.markdown("---")
st.markdown("### 📊 Rate Information")

col1, col2 = st.columns(2)
with col1:
    st.metric(
        label=f"Sell Rate ({currency1} → {currency2})",
        value=f"{rate_forward:.4f}",
        delta=f"{sell_margin_pct:+.2f}%" if official_rate > 0 else None
    )
with col2:
    st.metric(
        label=f"Buy Rate ({currency2} → {currency1})",
        value=f"{rate_backward:.4f}",
        delta=f"{buy_margin_pct:+.2f}%" if official_rate > 0 else None
    )

# Additional detailed information
if official_rate > 0:
    st.markdown("### 📈 Margin Details")
    margin_col1, margin_col2, margin_col3, margin_col4 = st.columns(4)
    
    with margin_col1:
        st.info(f"**Official Rate:** {official_rate:.4f}")
    
    with margin_col2:
        margin_color = "🟢" if sell_margin_pct >= 0 else "🔴"
        st.info(f"**Sell Margin:** {margin_color} {sell_margin_pct:+.2f}%")
    
    with margin_col3:
        margin_color = "🟢" if buy_margin_pct >= 0 else "🔴"
        st.info(f"**Buy Margin:** {margin_color} {buy_margin_pct:+.2f}%")
    
    with margin_col4:
        fee_status = "❌ Excluded" if exclude_fees else "✅ Included"
        fee_color = "secondary" if exclude_fees else "normal"
        st.info(f"**Extra Fees:** {fee_status}\n\n{row.get('extra_fees', 0):.4f}")

else:
    st.markdown(
        f"**Rate Used:** {rate_forward:.4f} ({currency1} → {currency2}) and {rate_backward:.4f} ({currency2} → {currency1})"
    )
    
    # Show fees status even without official rate
    if row.get("extra_fees", 0) > 0:
        fee_status = "❌ Excluded" if exclude_fees else "✅ Included"
        st.info(f"**Extra Fees ({fee_status}):** {row.get('extra_fees', 0):.4f}")

# Show conversion summary
st.markdown("---")
st.markdown("### 💡 Conversion Summary")
base_sell_rate = row["sell_rate"]
base_buy_rate = row["buy_rate"]
fees = row.get("extra_fees", 0)

summary_col1, summary_col2 = st.columns(2)
with summary_col1:
    st.write("**Sell Rate Breakdown:**")
    st.write(f"Base Rate: {base_sell_rate:.4f}")
    if fees > 0:
        if exclude_fees:
            st.write(f"Extra Fees: {fees:.4f} (❌ Excluded)")
        else:
            st.write(f"Extra Fees: {fees:.4f} (✅ Applied)")
    st.write(f"**Final Rate: {rate_forward:.4f}**")

with summary_col2:
    st.write("**Buy Rate Breakdown:**")
    st.write(f"Base Rate: {base_buy_rate:.4f}")
    if fees > 0:
        if exclude_fees:
            st.write(f"Extra Fees: {fees:.4f} (❌ Excluded)")
        else:
            st.write(f"Extra Fees: {fees:.4f} (✅ Applied)")
    st.write(f"**Final Rate: {rate_backward:.4f}**")
