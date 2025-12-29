
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO
import sqlite3
import hashlib
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth  # Keep your other imports

# --- Authentication with Auto-Hashing ---
credentials = {
    "usernames": {
        "miava": {
            "email": "miavasullivan@hotmail.com",
            "name": "Miava",
            "password": "dogfather"  # Plain text! Library will hash it automatically
        }
    }
}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name="finance_dashboard",
    cookie_key="your-super-long-unique-random-secret-key-abc123xyz789!",  # Strong random string
    cookie_expiry_days=30,
    auto_hash=True  # Explicitly enable auto-hashing (default is True anyway)
)

authenticator.login(location="main")

if st.session_state.get("authentication_status"):
    st.success(f"Welcome, {st.session_state.get('name')}! 👋")
    authenticator.logout("Logout", location="sidebar")

    # === MOVE ALL YOUR DASHBOARD CODE HERE ===
    #st.title("Personal Finance Dashboard")
    #section = st.sidebar.radio("Select Section", ["Rental Tracker", "Retirement Planner"])

    # Your full Rental Tracker and Retirement Planner code (database setup, etc.)

    #conn.close()  # At the very end


    # --- Database Setup (SQLite) ---
    DB_FILE = "finance_data.db"
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()

    # Create tables
    c.execute("""CREATE TABLE IF NOT EXISTS pnl_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property TEXT,
                year TEXT,
                data TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")

    c.execute("""CREATE TABLE IF NOT EXISTS retirement_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                current_age INTEGER,
                retirement_age INTEGER,
                current_balance REAL,
                monthly_savings REAL,
                expected_return REAL,
                inflation_rate REAL,
                desired_income REAL,
                ideal_savings REAL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    conn.commit()

    # --- Custom CSS ---
    st.markdown("""
        <style>
        .stApp { background-color: #ffffff; color: #1e1e1e; }
        h1, h2, h3 { color: #0a3d62 !important; font-weight: 600; }
        label { color: #1e1e1e !important; font-weight: 500; }
        .block-container { padding: 24px; background-color: #ffffff; border-radius: 10px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #e0e0e0; margin-bottom: 24px; }
        .stButton > button { background-color: #0066cc; color: white; border-radius: 6px; }
        section[data-testid="stSidebar"] { background-color: #f8f9fa; }
        </style>
    """, unsafe_allow_html=True)

    st.title("Personal Finance Dashboard")
    #section = st.sidebar.radio("Select Section", ["Rental Tracker", "Retirement Planner"])

    section = st.sidebar.radio(
    "Select Section", 
    ["Rental Tracker", "Retirement Planner"],
    key="main_section_selector"  # Unique key — can be any string
    )

    # =======================
    # RENTAL TRACKER
    # =======================
    if section == "Rental Tracker":
        st.header("Rental Property Tracker")

        uploaded_file = st.file_uploader("Upload Annual P&L CSV", type="csv")
        property_name_input = st.text_input("Property Name (e.g., Chestnut)", value="1406 E. Chestnut Ave.")
        year_input = st.text_input("Year", value="2024")

        if uploaded_file and st.button("Save P&L"):
            content = StringIO(uploaded_file.getvalue().decode("utf-8"))
            c.execute("INSERT INTO pnl_data (property, year, data) VALUES (?, ?, ?)",
                    (property_name_input, year_input, content.getvalue()))
            conn.commit()
            st.success(f"Saved {property_name_input} - {year_input}")

        # Load saved P&Ls
        c.execute("SELECT id, property, year FROM pnl_data ORDER BY year DESC")
        saved_pnls = c.fetchall()

        if saved_pnls:
            st.subheader("Saved P&L Reports")
            selected_pnl_id = st.selectbox("View saved report", [f"{row[1]} ({row[2]})" for row in saved_pnls],
                                        format_func=lambda x: x)

            selected_id = saved_pnls[[f"{r[1]} ({r[2]})" for r in saved_pnls].index(selected_pnl_id)][0]
            c.execute("SELECT data FROM pnl_data WHERE id=?", (selected_id,))
            raw_csv = c.fetchone()[0]

            lines = raw_csv.splitlines()
            data = []
            current_section = None

            for line in lines:
                parts = [p.strip() for p in line.split(",", 3)]
                if len(parts) < 4: continue
                label, item, amount_str = parts[1], parts[2], parts[3].strip('"').replace("$", "").replace(",", "")
                if label in ["Income", "Expense"]:
                    current_section = label
                    continue
                if item and amount_str:
                    try:
                        amount = float(amount_str)
                        if current_section == "Expense": amount = -amount
                        if item not in ["Total Income", "Total Expenses"]:
                            data.append({"Category": item, "Amount": amount})
                    except: pass

            if data:
                df = pd.DataFrame(data)
                st.dataframe(df.style.format({"Amount": "${:,.2f}"}))

                col1, col2 = st.columns(2)
                with col1:
                    st.altair_chart(alt.Chart(df).mark_arc().encode(theta="Amount:Q", color="Category:N").properties(title="Breakdown"))
                with col2:
                    st.altair_chart(alt.Chart(df).mark_bar().encode(
                        x="Category:N", y="Amount:Q",
                        color=alt.condition(alt.datum.Amount > 0, alt.value("#28a745"), alt.value("#dc3545"))
                    ).properties(title="Income vs Expenses"))

                net_cash_flow = df["Amount"].sum()
                initial_investment = st.number_input("Initial Investment ($)", value=200000.0)
                depreciable_basis = st.number_input("Depreciable Basis ($)", value=150000.0)
                useful_life = st.number_input("Useful Life (Years)", value=27)

                if st.button("Calculate"):
                    roi = (net_cash_flow / initial_investment) * 100 if initial_investment else 0
                    dep = depreciable_basis / useful_life
                    st.metric("Net Cash Flow", f"${net_cash_flow:,.2f}")
                    st.metric("Cash-on-Cash ROI", f"{roi:.2f}%")
                    st.metric("Annual Depreciation", f"${dep:,.2f}")

    # =======================
    # RETIREMENT PLANNER
    # =======================
    elif section == "Retirement Planner":
        st.header("Retirement Planner")

        # Inputs
        current_age = st.number_input("Current Age", 18, 100, 40)
        retirement_age = st.number_input("Retirement Age", current_age+1, 100, 65)
        current_balance = st.number_input("Current Balance ($)", 0.0, value=100000.0)
        monthly_savings = st.number_input("Monthly Savings ($)", 0.0, value=1000.0)
        expected_return = st.number_input("Expected Return (%)", 0.0, 15.0, 7.0) / 100
        inflation = st.number_input("Inflation (%)", 0.0, 10.0, 3.0) / 100
        desired_income = st.number_input("Desired Monthly Income ($)", 0.0, value=5000.0)
        ideal_savings = st.number_input("Ideal Monthly Savings ($)", 0.0, value=1500.0)
        scenario_name = st.text_input("Scenario Name (e.g., Base Case)", "My Scenario")

        if st.button("Run & Save Scenario"):
            # Save to DB
            try:
                c.execute("""INSERT INTO retirement_scenarios 
                            (name, current_age, retirement_age, current_balance, monthly_savings,
                            expected_return, inflation_rate, desired_income, ideal_savings)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (scenario_name, current_age, retirement_age, current_balance, monthly_savings,
                        expected_return, inflation, desired_income, ideal_savings))
                conn.commit()
                st.success(f"Saved scenario: {scenario_name}")
            except sqlite3.IntegrityError:
                st.error("Name already exists — choose a unique name.")

        # Load and compare saved scenarios
        c.execute("SELECT name FROM retirement_scenarios")
        saved_names = [row[0] for row in c.fetchall()]

        if saved_names:
            st.subheader("Compare Saved Scenarios")
            selected_names = st.multiselect("Select up to 4 scenarios", saved_names, default=saved_names[:min(4, len(saved_names))])

            if selected_names:
                results = []
                for name in selected_names:
                    c.execute("SELECT * FROM retirement_scenarios WHERE name=?", (name,))
                    row = c.fetchone()
                    years = row[3] - row[2]  # retirement_age - current_age

                    def project(b, m, r, i, y):
                        bal = b
                        for yr in range(y):
                            for mo in range(12):
                                bal += m * (1 + i)**(yr + mo/12)
                                bal *= (1 + r / 12)
                        return bal

                    base = project(row[4], row[5], row[6], row[7], years)
                    ideal = project(row[4], row[9], row[6], row[7], years)

                    results.append({"Scenario": name, "Projected": base, "With Ideal Savings": ideal})

                chart_df = pd.DataFrame(results)
                st.bar_chart(chart_df.set_index("Scenario"))

    # Close DB
    conn.close()

else:
    if st.session_state.get("authentication_status") == False:
        st.error("Username/password is incorrect")
    elif st.session_state.get("authentication_status") is None:
        st.warning("Please enter your username and password")
    st.stop()  # Hides everything until login succeeds