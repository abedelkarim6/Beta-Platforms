# 💱 Streamlit Currency Converter App

A lightweight 2-page Streamlit web app to manage currency conversion rates and perform quick conversions with fee handling. Designed for small-scale use with up to 50 rates and optional CSV upload/download.

---

## 🚀 Features

### 🔧 Page 1 – Manage Rates
- Add new conversion rates with:
  - Currency 1 → Currency 2
  - Buy Rate, Sell Rate
  - Extra Fees
  - %Buy, %Sell margins
- Edit rates inline using `st.data_editor`
- Delete rows interactively
- Save/load rates using CSV:
  - Download current table as CSV
  - Upload CSV to restore or replace rates

### 🔁 Page 2 – Currency Converter
- Choose currencies and operation (Buy/Sell)
- Enter:
  - Amount paid by customer
  - Amount paid by Beta
  - Custom rate
  - Optional extra fees
- Final amount is automatically calculated based on:
  - Rate used
  - Margin % and fee handling
  - Exclude-fees checkbox

---

## 🛠 How to Run Locally

1. **Clone this repo**
   ```bash
   git clone https://github.com/yourusername/currency-converter-app.git
   ```
   ```bash
   cd currency-converter-app
   ```
