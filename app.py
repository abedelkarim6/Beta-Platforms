import streamlit as st
import pandas as pd

# --- Load session state data ---
if "rate_table" not in st.session_state:
    st.session_state.rate_table = pd.DataFrame(
        columns=[
            "Currency 1",
            "Currency 2",
            "Buy Rate",
            "Sell Rate",
            "Extra Fees",
            "%Buy",
            "%Sell",
        ]
    )

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Select Page", ["Manage Rates", "Converter"])

# --- Page 1: Manage Rates ---
if page == "Manage Rates":
    st.title("Currency Conversion Rate Manager")

    st.subheader("Add New Conversion Rate")
    with st.form("Add Rate Form"):
        col1, col2 = st.columns(2)
        with col1:
            currency1 = st.text_input("Currency 1 (e.g., USDT)")
            buy_rate = st.number_input(
                "Buy Rate", min_value=0.0, step=0.01, format="%.3f"
            )
            buy_points = st.number_input(
                "Buy Points", min_value=0.0, step=0.01, format="%.3f"
            )
            # should be modifided to be calculated automatically
            # percent_buy = st.number_input(
            #     "%Buy", min_value=0.0, step=0.01, format="%.3f"
            # )
            extra_fees = st.number_input(
                "Extra Fees", min_value=0.0, step=0.01, format="%.3f"
            )
        with col2:
            currency2 = st.text_input("Currency 2 (e.g., LBP)")
            sell_rate = st.number_input(
                "Sell Rate", min_value=0.0, step=0.01, format="%.3f"
            )
            sell_points = st.number_input(
                "Sell Points", min_value=0.0, step=0.01, format="%.3f"
            )
            # should be modifided to be calculated automatically
            # percent_sell = st.number_input(
            #     "%Sell", min_value=0.0, step=0.01, format="%.3f"
            # )

        submitted = st.form_submit_button("Add Rate")
        if submitted and currency1 and currency2:
            new_row = {
                "Currency 1": currency1.upper(),
                "Currency 2": currency2.upper(),
                "Buy Rate": buy_rate,
                "Sell Rate": sell_rate,
                "Extra Fees": extra_fees,
                "%Buy": percent_buy,
                "%Sell": percent_sell,
            }
            st.session_state.rate_table = pd.concat(
                [st.session_state.rate_table, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            st.success("Rate added successfully!")

    st.subheader("Current Rates")
    if st.session_state.rate_table.empty:
        st.info("No rates added yet.")
    else:
        # Add a temporary "Delete?" column
        editable_df = st.session_state.rate_table.copy()

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Currency 1": st.column_config.NumberColumn(disabled=True),
                "Currency 2": st.column_config.NumberColumn(disabled=True),
                "Buy Rate": st.column_config.NumberColumn(disabled=True, format="%.3f"),
                "Sell Rate": st.column_config.NumberColumn(
                    disabled=True, format="%.3f"
                ),
                "Extra Fees": st.column_config.NumberColumn(
                    disabled=True, format="%.3f"
                ),
            },
            key="rates_editor",
        )

        # Save changes made via the editor
        if not edited_df.equals(st.session_state.rate_table):
            st.session_state.rate_table = edited_df.reset_index(drop=True)


# --- Page 2: Converter ---
elif page == "Converter":
    st.title("Currency Converter")

    df = st.session_state.rate_table
    if df.empty:
        st.warning("No conversion rates available. Go to 'Manage Rates' to add some.")
    else:
        currency_options = sorted(set(df["Currency 1"]).union(set(df["Currency 2"])))
        currency1 = st.selectbox("Currency 1", currency_options)
        currency2 = st.selectbox("Currency 2", currency_options)
        operation = st.radio("Operation", ["Buy", "Sell"])

        # Filter matching row
        match = df[(df["Currency 1"] == currency1) & (df["Currency 2"] == currency2)]
        if match.empty:
            st.error(
                "No matching rate found. Make sure the pair exists in Manage Rates."
            )
        else:
            rate_row = match.iloc[0]
            rate_used = (
                rate_row["Buy Rate"] if operation == "Buy" else rate_row["Sell Rate"]
            )
            percent_fee = rate_row["%Buy"] if operation == "Buy" else rate_row["%Sell"]

            st.markdown("### Transaction Inputs")
            amount_customer = st.number_input(
                "Amount Paid by Customer", min_value=0.0, step=0.01
            )
            amount_beta = st.number_input(
                "Amount Paid by Beta", min_value=0.0, step=0.01
            )
            custom_rate = st.number_input("Rate Used", value=rate_used, step=0.01)
            extra_fees = st.number_input(
                "Extra Fees", value=rate_row["Extra Fees"], step=0.01
            )

            exclude_fees = st.checkbox("Exclude Extra Fees", value=False)

            st.markdown("### Final Calculation")
            final_rate = custom_rate * (1 + percent_fee / 100)
            if not exclude_fees:
                final_amount = amount_customer * final_rate + extra_fees
            else:
                final_amount = amount_customer * final_rate

            st.write(f"**Final Amount (after fees):** {final_amount:.2f} {currency2}")
