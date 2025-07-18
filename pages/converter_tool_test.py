from pages.customer import fetch_customers, fetch_customer_ranges
import streamlit as st
import pandas as pd
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Currency Converter",
    page_icon="💰",
    layout="wide"
)

CSV_PATH = "data/rates.csv"

# Load rates
@st.cache_data
def load_rates():
    try:
        df = pd.read_csv(CSV_PATH)
        return df
    except:
        st.error("❌ Unable to load rates data. Please check if the rates file exists.")
        return pd.DataFrame()

# Function to determine which range applies based on amount
def get_customer_range_data(amount, customer_ranges_df):
    """Get the appropriate range data based on the amount"""
    if customer_ranges_df.empty:
        return None
    
    # Convert amount to thousands for comparison
    amount_k = amount / 1000
    
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

# Main application
def main():
    st.title("💰 Currency Converter")
    st.markdown("Convert between different currencies with customer-specific rates and margins")
    st.markdown("---")
    
    # Load rates
    df = load_rates()
    if df.empty:
        st.stop()
    
    # Customer Selection Section
    st.header("👤 Customer Selection")
    
    # Fetch customer data
    customers_df = fetch_customers()
    if customers_df.empty:
        st.warning("⚠️ No customers available.")
        st.info("💡 Please add customers first to use customer-specific rates.")
        st.stop()
    
    # Display customer selection
    customer_options = {f"{row['name']} (ID: {row['id']})": row['id'] 
                       for _, row in customers_df.iterrows()}
    
    selected_customer = st.selectbox(
        "Select Customer:", 
        list(customer_options.keys()),
        help="Choose a customer to apply their specific rates and margins"
    )
    
    customer_id = customer_options[selected_customer]
    customer_ranges_df = fetch_customer_ranges(customer_id)
    
    if customer_ranges_df.empty:
        st.warning(f"⚠️ No range data available for {selected_customer}.")
        st.info("💡 **Tip**: Go to the Customers page to add range data for this customer.")
        use_customer_margins = False
    else:
        use_customer_margins = True
        
        # Show customer ranges in an expandable section
        with st.expander(f"📊 View Ranges for {selected_customer.split(' (')[0]}", expanded=False):
            st.dataframe(
                customer_ranges_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "usdt_range": st.column_config.TextColumn("Range", width="small"),
                    "custom_margin_points": st.column_config.NumberColumn("Margin Points", format="%.4f"),
                    "custom_margin_percent": st.column_config.NumberColumn("Margin %", format="%.2f%%"),
                    "extra_fee_percent": st.column_config.NumberColumn("Extra Fee %", format="%.2f%%")
                }
            )
    
    st.markdown("---")
    
    # Main converter interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🔄 Currency Conversion")
        
        # Settings
        exclude_fees = st.checkbox("🚫 Exclude Extra Fees", value=False)
        
        # Currency selection
        curr_col1, curr_col2 = st.columns(2)
        
        with curr_col1:
            from_currency = st.selectbox(
                "From Currency:", 
                df["from_currency"].unique(),
                help="Select the source currency"
            )
        
        with curr_col2:
            to_currency = st.selectbox(
                "To Currency:", 
                df["to_currency"].unique(),
                help="Select the target currency"
            )
        
        # Get the rates for selected currencies
        rate_data = df[(df["from_currency"] == from_currency) & (df["to_currency"] == to_currency)]
        
        if rate_data.empty:
            st.error(f"❌ No rate data available for {from_currency} to {to_currency}.")
            st.info("💡 Please add this currency pair in the Rate Management section.")
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
            
            # Currency input fields with better styling
            st.markdown("### 💱 Enter Amount")
            
            input_col1, input_col2 = st.columns(2)
            
            with input_col1:
                st.number_input(
                    f"From {from_currency}",
                    key="amount1",
                    value=st.session_state.amount1,
                    on_change=on_amount1_change,
                    format="%.4f",
                    help=f"Enter the amount in {from_currency}"
                )
            
            with input_col2:
                st.number_input(
                    f"To {to_currency}",
                    key="amount2",
                    value=st.session_state.amount2,
                    on_change=on_amount2_change,
                    format="%.4f",
                    help=f"Converted amount in {to_currency}"
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
            
            # Display conversion result prominently
            st.markdown("---")
            st.success(f"✅ **Conversion Result**: {st.session_state.amount1:.4f} {from_currency} = {st.session_state.amount2:.4f} {to_currency}")
            
            if use_customer_margins:
                st.success(f"🎯 **Customer-specific margins applied for {selected_customer.split(' (')[0]}**")
    
    with col2:
        st.header("📊 Rate Information")
        
        if not rate_data.empty:
            # Current rates display
            rate_col1, rate_col2 = st.columns(1)
            
            with rate_col1:
                st.metric(
                    label=f"Sell Rate",
                    value=f"{final_sell_rate:.4f}",
                    delta=f"{final_sell_rate - base_sell_rate:.4f}" if use_customer_margins else None,
                    help=f"{from_currency} → {to_currency}"
                )
                
                st.metric(
                    label=f"Buy Rate",
                    value=f"{final_buy_rate:.4f}",
                    delta=f"{final_buy_rate - base_buy_rate:.4f}" if use_customer_margins else None,
                    help=f"{to_currency} → {from_currency}"
                )
            
            # Quick amount buttons
            st.markdown("---")
            st.subheader("⚡ Quick Amounts")
            
            quick_amounts = [100, 1000, 5000, 10000, 50000]
            
            for amount in quick_amounts:
                if st.button(f"{amount:,}", key=f"quick_{amount}", use_container_width=True):
                    st.session_state.amount1 = float(amount)
                    st.session_state.last_changed = "amount1"
                    on_amount1_change()
                    st.rerun()
            
            # Customer range information
            if use_customer_margins:
                st.markdown("---")
                st.subheader("📈 Current Range")
                current_range = get_customer_range_data(current_amount, customer_ranges_df)
                if current_range is not None:
                    st.info(f"💰 **Amount**: {current_amount:.2f}")
                    st.info(f"📊 **Range**: {current_range['usdt_range']}")
                    
                    # Show range details
                    if current_range['custom_margin_points'] != 0:
                        st.caption(f"Points: {current_range['custom_margin_points']:+.4f}")
                    if current_range['custom_margin_percent'] != 0:
                        st.caption(f"Margin: {current_range['custom_margin_percent']:+.2f}%")
                    if current_range['extra_fee_percent'] != 0:
                        st.caption(f"Fee: {current_range['extra_fee_percent']:+.2f}%")
    
    # Detailed breakdown section
    if not rate_data.empty:
        st.markdown("---")
        st.header("💡 Detailed Rate Breakdown")
        
        breakdown_col1, breakdown_col2 = st.columns(2)
        
        with breakdown_col1:
            st.subheader("📈 Sell Rate Breakdown")
            st.write(f"**Base Rate**: {base_sell_rate:.4f}")
            if extra_fees > 0:
                st.write(f"**Extra Fees**: {extra_fees:.4f}")
            
            if use_customer_margins:
                range_data = get_customer_range_data(current_amount, customer_ranges_df)
                if range_data is not None:
                    st.write(f"**Customer Range**: {range_data['usdt_range']}")
                    if range_data['custom_margin_points'] != 0:
                        st.write(f"**Margin Points**: {range_data['custom_margin_points']:+.4f}")
                    if range_data['custom_margin_percent'] != 0:
                        st.write(f"**Margin Percent**: {range_data['custom_margin_percent']:+.2f}%")
                    if range_data['extra_fee_percent'] != 0:
                        st.write(f"**Customer Fee**: {range_data['extra_fee_percent']:+.2f}%")
            
            st.markdown(f"**🎯 Final Rate: {final_sell_rate:.4f}**")
        
        with breakdown_col2:
            st.subheader("📉 Buy Rate Breakdown")
            st.write(f"**Base Rate**: {base_buy_rate:.4f}")
            if extra_fees > 0:
                st.write(f"**Extra Fees**: {extra_fees:.4f}")
            
            if use_customer_margins:
                range_data = get_customer_range_data(current_amount, customer_ranges_df)
                if range_data is not None:
                    st.write(f"**Customer Range**: {range_data['usdt_range']}")
                    if range_data['custom_margin_points'] != 0:
                        st.write(f"**Margin Points**: {range_data['custom_margin_points']:+.4f}")
                    if range_data['custom_margin_percent'] != 0:
                        st.write(f"**Margin Percent**: {range_data['custom_margin_percent']:+.2f}%")
                    if range_data['extra_fee_percent'] != 0:
                        st.write(f"**Customer Fee**: {range_data['extra_fee_percent']:+.2f}%")
            
            st.markdown(f"**🎯 Final Rate: {final_buy_rate:.4f}**")
        
        # Customer range overview
        if use_customer_margins:
            st.markdown("---")
            st.subheader("📊 All Customer Ranges")
            
            for _, range_row in customer_ranges_df.iterrows():
                current_range = get_customer_range_data(current_amount, customer_ranges_df)
                range_indicator = "🎯" if current_range is not None and range_row['usdt_range'] == current_range['usdt_range'] else "⚪"
                
                st.write(f"{range_indicator} **{range_row['usdt_range']}** - "
                        f"Points: {range_row['custom_margin_points']:+.4f}, "
                        f"Margin: {range_row['custom_margin_percent']:+.2f}%, "
                        f"Fee: {range_row['extra_fee_percent']:+.2f}%")
    
    # Footer
    st.markdown("---")
    st.markdown("### 💡 Tips:")
    st.markdown("""
    - **Customer Ranges**: Different amounts trigger different margin structures
    - **Quick Amounts**: Use the buttons on the right for common conversion amounts
    - **Exclude Fees**: Toggle to see rates without extra fees
    - **Real-time Updates**: Amounts update automatically when you change the input
    """)

if __name__ == "__main__":
    main()