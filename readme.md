# 💱 Currency Exchange Tool – Project Overview

This Streamlit-based app is designed to streamline daily currency exchange operations for a manual exchanger. It includes tools for rate management, real-time conversions, and handling frequent customer-specific deals.

---

## 📄 App Pages

### 1. **Rates Management**
Manage and define buy/sell rates for each currency pair.

**Features:**
- Select currency pair (e.g., USDT/LBP).
- Set **official rate** (pulled from Binance or manually entered).
- Choose **margin type**:  
  - **Points** (e.g., +2,000 LBP)  
  - **Percentage** (e.g., +2%)
- Set margin value (one is user-defined, the other auto-calculated).
- Automatically calculate and display:
  - Final **Buy Rate**
  - Final **Sell Rate**
  - Effective % margin or points

---

### 2. **Converter Tool**
A real-time converter for use by employees to calculate exchange results.

**Features:**
- Select currency pair (e.g., USDT ⇄ LBP)
- Two currency input boxes (editable on both sides)
  - Editing either box updates the other live
- Display:
  - Official rate used
  - Margin details (points and %)
  - Final applied rate (Buy or Sell)
- Optional: Include/exclude **extra fees**
  - Toggle to apply extra fee (flat or %)
- Calculate and display:
  - Final amount after margin + optional fees
  - Breakdown of calculations

---

### 3. **Customers Management**
Manage frequent customers with custom margin rules.

**Features:**
- Define and categorize customers by **visit frequency** (e.g., Regular, VIP, etc.)
- For each customer category:
  - Define **custom margin rules** based on amount ranges:
    - `< 1,000 USDT`
    - `< 10,000 USDT`
    - `< 50,000 USDT`
- When converting, automatically apply customer-specific margin based on:
  - Who the customer is
  - How much they're exchanging

---

## ⚙️ Key Behaviors

- Margins can be defined in **points** or **percent**, and are convertible.
- Both **buy** and **sell** rates are stored and used separately.
- Fees can be **optional** and defined per transaction.
- App is optimized for **internal use** (employee interface).

---

## 🧩 Next Steps

- Define data model and storage (e.g., JSON, SQLite, or simple CSV)
- Integrate Binance API or rate entry panel
- Build Streamlit UI for all 3 pages
- Add logic for margin conversion and customer-specific rates

