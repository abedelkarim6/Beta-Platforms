import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "data/customers.db"
st.set_page_config(layout="wide")
st.title("👥 Customers Management")


# DB connection
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


# Create main and ranges tables
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_ranges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            usdt_range TEXT NOT NULL,
            custom_margin_points REAL DEFAULT 0.0,
            custom_margin_percent REAL DEFAULT 0.0,
            extra_fee_percent REAL DEFAULT 0.0,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """
    )
    conn.commit()
    conn.close()


create_tables()


# Fetch all customers
def fetch_customers():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df


# Fetch range data per customer
# def fetch_customer_ranges(customer_id):
#     conn = get_connection()
#     query = "SELECT * FROM customer_ranges WHERE customer_id = ?"
#     print(f"Executing query: {query} with customer_id={customer_id}")  # Debugging line
#     df = pd.read_sql_query(query, conn, params=(customer_id,))  # Ensure params is a tuple
#     print(f"Fetched {len(df)} rows for customer_id={customer_id}")  # Debugging line
#     conn.close()
#     return df
# Fetch ranges for a specific customer
def fetch_customer_ranges(customer_id):
    conn = get_connection()
    df = pd.read_sql_query(
        """
        SELECT * FROM customer_ranges 
        WHERE customer_id = ?
        """, 
        conn, 
        params=(customer_id,)
    )
    conn.close()
    return df


# Add customer with ranges
def add_customer_with_ranges(name, category, ranges_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (name, category) VALUES (?, ?)", (name, category)
    )
    customer_id = cursor.lastrowid
    for r in ranges_data:
        cursor.execute(
            """
            INSERT INTO customer_ranges (
                customer_id, usdt_range, custom_margin_points,
                custom_margin_percent, extra_fee_percent
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (
                customer_id,
                r,
                ranges_data[r]["points"],
                ranges_data[r]["percent"],
                ranges_data[r]["fee"],
            ),
        )
    conn.commit()
    conn.close()


# Update a range row
def update_customer_range(range_id, points, percent, fee):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE customer_ranges
        SET custom_margin_points = ?, custom_margin_percent = ?, extra_fee_percent = ?
        WHERE id = ?
    """,
        (points, percent, fee, range_id),
    )
    conn.commit()
    conn.close()


# Delete customer and their ranges
def delete_customer_and_ranges(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer_ranges WHERE customer_id = ?", (customer_id,))
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()


# Add new customer form
st.subheader("➕ Add New Customer")
with st.form("add_customer_form"):
    name = st.text_input("Customer Name")
    category = st.selectbox("Category", ["Regular", "VIP", "Partner"])

    usdt_ranges = ["<1k", "<10k", "<50k"]
    ranges_data = {}
    for r in usdt_ranges:
        st.markdown(f"**Range: {r}**")
        col1, col2, col3 = st.columns(3)
        with col1:
            margin_points = st.number_input(
                f"Margin Points ({r})", key=f"mp_{r}", value=0.0, format="%.2f"
            )
        with col2:
            margin_percent = st.number_input(
                f"Margin Percent (%) ({r})", key=f"mper_{r}", value=0.0, format="%.2f"
            )
        with col3:
            fee_percent = st.number_input(
                f"Extra Fee (%) ({r})", key=f"fee_{r}", value=0.0, format="%.2f"
            )
        ranges_data[r] = {
            "points": margin_points,
            "percent": margin_percent,
            "fee": fee_percent,
        }

    submitted = st.form_submit_button("Add Customer")
    if submitted:
        if name.strip():
            add_customer_with_ranges(name.strip(), category, ranges_data)
            st.success(f"✅ Customer '{name}' added with range margins.")
            st.rerun()
        else:
            st.error("Name cannot be empty.")

st.markdown("---")

# Show all customers
st.subheader("📋 All Customers")
df = fetch_customers()
if not df.empty:
    for idx, row in df.iterrows():
        with st.expander(f"{row['name']} (ID: {row['id']})"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input(
                    "Name", value=row["name"], key=f"name_{row['id']}", disabled=True
                )
            with col2:
                new_cat = st.text_input(
                    "Category",
                    value=row["category"],
                    key=f"cat_{row['id']}",
                    disabled=True,
                )

            ranges_df = fetch_customer_ranges(row["id"])
            for _, r in ranges_df.iterrows():
                st.markdown(f"**USDT Range: {r['usdt_range']}**")
                colr1, colr2, colr3, colr4 = st.columns([1.2, 1.2, 1.2, 0.8])
                with colr1:
                    points = st.number_input(
                        "Points", value=r["custom_margin_points"], key=f"rp_{r['id']}"
                    )
                with colr2:
                    percent = st.number_input(
                        "Percent",
                        value=r["custom_margin_percent"],
                        key=f"rper_{r['id']}",
                    )
                with colr3:
                    fee = st.number_input(
                        "Fee %", value=r["extra_fee_percent"], key=f"rf_{r['id']}"
                    )
                with colr4:
                    if st.button("Save", key=f"save_r_{r['id']}"):
                        update_customer_range(r["id"], points, percent, fee)
                        st.success("Range updated.")
                        st.rerun()

            if st.button("🔚 Delete Customer", key=f"del_{row['id']}"):
                delete_customer_and_ranges(row["id"])
                st.warning(f"Deleted {row['name']}")
                st.rerun()
else:
    st.info("No customers found.")
