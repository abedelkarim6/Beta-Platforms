from pages.customer import fetch_customers, fetch_customer_ranges
import streamlit as st
import pandas as pd

CSV_PATH = "data/rates.csv"
st.set_page_config(layout="wide")
st.title("🔄 Converter Tool")

# Load rates
df = pd.read_csv(CSV_PATH)

# Fetch customer data
customers_df = fetch_customers()
if customers_df.empty:
    st.warning("No customers available.")
    st.stop()

# Display customer selection
customer_options = {f"{row['name']} (ID: {row['id']})": row['id'] 
                   for _, row in customers_df.iterrows()}

selected_customer = st.selectbox("Select Customer", list(customer_options.keys()))

if selected_customer:
    customer_id = customer_options[selected_customer]
    customer_ranges_df = fetch_customer_ranges(customer_id)

    if customer_ranges_df.empty:
        st.warning(f"No range data available for {selected_customer}.")
        st.info("💡 **Tip**: Go to the Customers page to add range data for this customer.")
        use_customer_margins = False
    else:
        st.markdown(f"### 📊 Ranges for {selected_customer}")
        st.dataframe(customer_ranges_df)
        use_customer_margins = True

# Function to determine which range applies based on amount
def get_customer_range_data(amount, customer_ranges_df):
    """Get the appropriate range data based on the amount"""
    if customer_ranges_df.empty:
        return None
    
    # Convert amount to thousands for comparison
    amount_k = amount / 1000
    
    # Define range order (from smallest to largest)
    range_order = ["<1k", "<10k", "<50k"]
    
    # Find the appropriate range
    if amount_k < 1:
        target_range = "<1k"
    elif amount_k < 10:
        target_range = "<10k"
    elif amount_k < 50:
        target_range = "<50k"
    else:
        target_range = "<50k"  # Use largest range for amounts >= 50k
    
    # Find the range data
    range_data = customer_ranges_df[customer_ranges_df["usdt_range"] == target_range]
    
    if range_data.empty:
        return None
    
    return range_data.iloc[0]

# Function to apply customer margins to rate
def apply_customer_margins(base_rate, amount, customer_ranges_df, official_rate=0):
    """Apply customer-specific margins to the base rate"""
    if customer_ranges_df.empty:
        return base_rate, "No customer margins applied"
    
    range_data = get_customer_range_data(amount, customer_ranges_df)
    
    if range_data is None:
        return base_rate, "No matching range found"
    
    # Apply margins
    margin_points = range_data["custom_margin_points"]
    margin_percent = range_data["custom_margin_percent"]
    extra_fee_percent = range_data["extra_fee_percent"]
    
    # Calculate the adjusted rate
    adjusted_rate = base_rate
    
    # Apply point margin
    if margin_points != 0:
        adjusted_rate += margin_points
    
    # Apply percentage margin
    if margin_percent != 0:
        adjusted_rate = adjusted_rate * (1 + margin_percent / 100)
    
    # Apply extra fee
    if extra_fee_percent != 0:
        adjusted_rate = adjusted_rate * (1 + extra_fee_percent / 100)
    
    # Create description
    description = f"Range: {range_data['usdt_range']}"
    if margin_points != 0:
        description += f" | Points: {margin_points:+.4f}"
    if margin_percent != 0:
        description += f" | Margin: {margin_percent:+.2f}%"
    if extra_fee_percent != 0:
        description += f" | Fee: {extra_fee_percent:+.2f}%"
    
    return adjusted_rate, description

# Extra fees toggle
exclude_fees = st.checkbox("🚫 Exclude Extra Fees", value=False)

# Use two columns for the currency selection side by side
col1, col2 = st.columns(2)

with col1:
    from_currency = st.selectbox("From Currency", df["from_currency"].unique())

with col2:
    to_currency = st.selectbox("To Currency", df["to_currency"].unique())

# Get the rates for selected currencies
rate_data = df[(df["from_currency"] == from_currency) & (df["to_currency"] == to_currency)]

if rate_data.empty:
    st.warning(f"No rate data available for {from_currency} to {to_currency}.")
else:
    # Proceed if there is data
    rate_data = rate_data.iloc[-1]  # Get the last matching row
    base_sell_rate = rate_data["sell_rate"]
    base_buy_rate = rate_data["buy_rate"]
    official_rate = rate_data.get("official_rate", 0)
    extra_fees = rate_data.get("extra_fees", 0) if not exclude_fees else 0

    # Initialize session state amounts
    if "amount1" not in st.session_state:
        st.session_state.amount1 = 1000.0  # Default to 1000 to show range effects
    if "amount2" not in st.session_state:
        st.session_state.amount2 = st.session_state.amount1 * base_sell_rate

    # Track which input was last changed
    if "last_changed" not in st.session_state:
        st.session_state.last_changed = "amount1"

    def on_amount1_change():
        st.session_state.last_changed = "amount1"
        # Apply customer margins to sell rate
        if use_customer_margins:
            adjusted_sell_rate, _ = apply_customer_margins(
                base_sell_rate + extra_fees, 
                st.session_state.amount1, 
                customer_ranges_df, 
                official_rate
            )
        else:
            adjusted_sell_rate = base_sell_rate + extra_fees
        
        st.session_state.amount2 = st.session_state.amount1 * adjusted_sell_rate

    def on_amount2_change():
        st.session_state.last_changed = "amount2"
        # Apply customer margins to buy rate
        if use_customer_margins:
            adjusted_buy_rate, _ = apply_customer_margins(
                base_buy_rate + extra_fees, 
                st.session_state.amount2, 
                customer_ranges_df, 
                official_rate
            )
        else:
            adjusted_buy_rate = base_buy_rate + extra_fees
        
        st.session_state.amount1 = st.session_state.amount2 / adjusted_buy_rate

    # Currency input fields
    col1, col2 = st.columns(2)

    with col1:
        st.number_input(
            f"From {from_currency}",
            key="amount1",
            value=st.session_state.amount1,
            on_change=on_amount1_change,
            format="%.4f",
        )

    with col2:
        st.number_input(
            f"To {to_currency}",
            key="amount2",
            value=st.session_state.amount2,
            on_change=on_amount2_change,
            format="%.4f",
        )

    # Calculate current rates with customer margins
    current_amount = st.session_state.amount1 if st.session_state.last_changed == "amount1" else st.session_state.amount2
    
    if use_customer_margins:
        final_sell_rate, sell_description = apply_customer_margins(
            base_sell_rate + extra_fees, 
            current_amount, 
            customer_ranges_df, 
            official_rate
        )
        final_buy_rate, buy_description = apply_customer_margins(
            base_buy_rate + extra_fees, 
            current_amount, 
            customer_ranges_df, 
            official_rate
        )
    else:
        final_sell_rate = base_sell_rate + extra_fees
        final_buy_rate = base_buy_rate + extra_fees
        sell_description = "No customer margins applied"
        buy_description = "No customer margins applied"

    # Display the rate used and margin information
    st.markdown("---")
    st.markdown("### 📊 Rate Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"Sell Rate ({from_currency} → {to_currency})",
            value=f"{final_sell_rate:.4f}",
            delta=f"{final_sell_rate - base_sell_rate:.4f}" if use_customer_margins else None
        )
        if use_customer_margins:
            st.caption(sell_description)
    
    with col2:
        st.metric(
            label=f"Buy Rate ({to_currency} → {from_currency})",
            value=f"{final_buy_rate:.4f}",
            delta=f"{final_buy_rate - base_buy_rate:.4f}" if use_customer_margins else None
        )
        if use_customer_margins:
            st.caption(buy_description)

    # Show detailed breakdown
    st.markdown("---")
    st.markdown("### 💡 Rate Breakdown")
    
    breakdown_col1, breakdown_col2 = st.columns(2)
    
    with breakdown_col1:
        st.write("**Sell Rate Breakdown:**")
        st.write(f"Base Rate: {base_sell_rate:.4f}")
        if extra_fees > 0:
            st.write(f"Extra Fees: {extra_fees:.4f}")
        if use_customer_margins:
            range_data = get_customer_range_data(current_amount, customer_ranges_df)
            if range_data is not None:
                st.write(f"Customer Range: {range_data['usdt_range']}")
                if range_data['custom_margin_points'] != 0:
                    st.write(f"Margin Points: {range_data['custom_margin_points']:+.4f}")
                if range_data['custom_margin_percent'] != 0:
                    st.write(f"Margin Percent: {range_data['custom_margin_percent']:+.2f}%")
                if range_data['extra_fee_percent'] != 0:
                    st.write(f"Customer Fee: {range_data['extra_fee_percent']:+.2f}%")
        st.write(f"**Final Rate: {final_sell_rate:.4f}**")

    with breakdown_col2:
        st.write("**Buy Rate Breakdown:**")
        st.write(f"Base Rate: {base_buy_rate:.4f}")
        if extra_fees > 0:
            st.write(f"Extra Fees: {extra_fees:.4f}")
        if use_customer_margins:
            range_data = get_customer_range_data(current_amount, customer_ranges_df)
            if range_data is not None:
                st.write(f"Customer Range: {range_data['usdt_range']}")
                if range_data['custom_margin_points'] != 0:
                    st.write(f"Margin Points: {range_data['custom_margin_points']:+.4f}")
                if range_data['custom_margin_percent'] != 0:
                    st.write(f"Margin Percent: {range_data['custom_margin_percent']:+.2f}%")
                if range_data['extra_fee_percent'] != 0:
                    st.write(f"Customer Fee: {range_data['extra_fee_percent']:+.2f}%")
        st.write(f"**Final Rate: {final_buy_rate:.4f}**")

    # Show range information
    if use_customer_margins:
        st.markdown("---")
        st.markdown("### 📈 Customer Range Information")
        current_range = get_customer_range_data(current_amount, customer_ranges_df)
        if current_range is not None:
            st.info(f"💰 **Current Amount**: {current_amount:.2f} → **Range**: {current_range['usdt_range']}")
            
            # Show all available ranges
            st.markdown("**All Available Ranges:**")
            for _, range_row in customer_ranges_df.iterrows():
                range_indicator = "🎯" if range_row['usdt_range'] == current_range['usdt_range'] else "⚪"
                st.write(f"{range_indicator} **{range_row['usdt_range']}** - "
                        f"Points: {range_row['custom_margin_points']:+.4f}, "
                        f"Margin: {range_row['custom_margin_percent']:+.2f}%, "
                        f"Fee: {range_row['extra_fee_percent']:+.2f}%")

    # Final conversion result
    st.markdown("---")
    st.success(f"✅ **Final Conversion**: {st.session_state.amount1:.4f} {from_currency} = {st.session_state.amount2:.4f} {to_currency}")
    
    if use_customer_margins:
        st.success(f"🎯 **Customer-specific margins applied for {selected_customer.split(' (')[0]}**")