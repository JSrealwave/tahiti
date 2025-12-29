
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import StringIO

# Custom CSS for modern, minimal style
# Improved Custom CSS for better contrast and modern fonts
st.markdown("""
    <style>
    /* Main app background and text */
    .stApp {
        background-color: #ffffff;  /* Pure white for max contrast */
        color: #1e1e1e;             /* Almost black text */
    }
    
    /* All headings - darker and bolder */
    h1, h2, h3, h4, h5, h6 {
        color: #0a3d62 !important;  /* Deep blue for headings */
        font-weight: 600;
    }
    
    /* Labels (input fields, sliders, etc.) */
    label, .stMarkdown, .stText {
        color: #1e1e1e !important;
        font-weight: 500;
    }
    
    /* Metrics - make values pop */
    .stMetric > div > div {
        color: #1e1e1e !important;
    }
    .stMetric label {
        color: #2c3e50 !important;
        font-weight: 600;
    }
    
    /* Buttons - keep blue but higher contrast */
    .stButton > button {
        background-color: #0066cc;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 6px;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #0052a3;
    }
    
    /* Dataframes - better readability */
    .dataframe {
        font-size: 14px;
    }
    
    /* Block containers (cards) */
    .block-container {
        padding: 24px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 24px;
    }
    
    /* Modern font stack - clean and highly readable */
    body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    .stSidebar .stRadio > div > label {
        color: #1e1e1e !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Personal Finance Dashboard")
st.markdown("Custom tool for rental tracking and retirement planning.")

section = st.sidebar.radio("Select Section", ["Rental Tracker", "Retirement Planner"])

if section == "Rental Tracker":
    st.header("Rental Tracker")
    
    uploaded_file = st.file_uploader("Upload Annual P&L Summary CSV", type="csv")
    
    if uploaded_file is not None:
        # Read as text to handle irregular format
        content = StringIO(uploaded_file.getvalue().decode("utf-8"))
        lines = content.readlines()
        
        data = []
        current_section = None  # "Income" or "Expense"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",", 3)]
            if len(parts) < 4:
                continue
            
            label = parts[1] if len(parts) > 1 else ""
            item = parts[2] if len(parts) > 2 else ""
            amount_str = parts[3].strip('"').replace("$", "").replace(",", "") if len(parts) > 3 else ""
            
            if label == "Income":
                current_section = "Income"
                continue
            elif label == "Expense":
                current_section = "Expense"
                continue
            
            if item and amount_str:
                try:
                    amount = float(amount_str)
                    if current_section == "Expense":
                        amount = -amount  # Make expenses negative for cash flow calc
                    if item not in ["Total Income", "Total Expenses"]:  # Exclude totals to avoid double-counting in breakdowns
                        data.append({"Category": item, "Amount": amount})
                except ValueError:
                    pass
        
        if data:
            df = pd.DataFrame(data)
            
            st.subheader("Property Summary")
            # Extract property info from early lines
            property_name = "Unknown"
            period = "Unknown"
            for line in lines[:10]:
                if "Property:" in line:
                    property_name = line.split(",", 3)[2] if len(line.split(",")) > 2 else "Unknown"
                if "Date:" in line:
                    period = line.split(",", 3)[2] if len(line.split(",")) > 2 else "Unknown"
            st.write(f"**Property:** {property_name}  |  **Period:** {period}")
            
            st.subheader("Category Breakdown")
            st.dataframe(df.style.format({"Amount": "${:,.2f}"}))
            
            # Charts
            col1, col2 = st.columns(2)
            with col1:
                pie = alt.Chart(df).mark_arc().encode(
                    theta="Amount:Q",
                    color="Category:N",
                    tooltip=["Category", "Amount"]
                ).properties(title="Cash Flow by Category", width=300, height=300)
                st.altair_chart(pie)
            
            with col2:
                bar = alt.Chart(df).mark_bar().encode(
                    x="Category:N",
                    y="Amount:Q",
                    color=alt.condition(
                        alt.datum.Amount > 0,
                        alt.value("#28a745"),  # Green for income
                        alt.value("#dc3545")   # Red for expenses
                    ),
                    tooltip=["Category", "Amount"]
                ).properties(title="Amounts by Category", width=400)
                st.altair_chart(bar)
            
            # Calculations
            net_cash_flow = df["Amount"].sum()
            st.subheader("Key Metrics")
            col1, col2, col3 = st.columns(3)
            
            initial_investment = col1.number_input("Initial Capital Investment ($)", min_value=0.0, value=200000.0)
            asset_value = col2.number_input("Depreciable Basis ($)", min_value=0.0, value=150000.0)
            useful_life = col3.number_input("Useful Life (Years)", min_value=1, value=27)
            
            if st.button("Calculate ROI & Depreciation"):
                roi = (net_cash_flow / initial_investment) * 100 if initial_investment > 0 else 0
                annual_depreciation = asset_value / useful_life if useful_life > 0 else 0
                
                st.metric("Net Annual Cash Flow", f"${net_cash_flow:,.2f}")
                st.metric("Cash-on-Cash ROI", f"{roi:.2f}%")
                st.metric("Annual Straight-Line Depreciation", f"${annual_depreciation:,.2f}")
                st.success("Taxable income estimate: Cash Flow - Depreciation = "
                           f"${net_cash_flow - annual_depreciation:,.2f}")

        else:
            st.error("No data parsed. Check CSV format.")

# Retirement Planner section remains the same (copy from previous version)
elif section == "Retirement Planner":
    st.header("Retirement Planner")
    
    current_age = st.number_input("Current Age", min_value=18, max_value=100, value=40)
    retirement_age = st.number_input("Desired Retirement Age", min_value=current_age+1, max_value=100, value=65)
    current_401k = st.number_input("Current 401K/Investments Balance ($)", min_value=0.0, value=100000.0)
    monthly_savings = st.number_input("Current Monthly Savings ($)", min_value=0.0, value=1000.0)
    expected_return = st.number_input("Expected Annual Return (%)", min_value=0.0, value=7.0) / 100
    inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.0, value=3.0) / 100
    desired_monthly_income = st.number_input("Desired Monthly Retirement Income ($)", min_value=0.0, value=5000.0)
    ideal_monthly_savings = st.number_input("Ideal Monthly Savings Target ($)", min_value=0.0, value=1500.0)
    
    if st.button("Run Projections"):
        years = retirement_age - current_age
        
        def project(balance, monthly, ret, inf, y):
            b = balance
            for year in range(y):
                for m in range(12):
                    b += monthly * (1 + inf)**(year + m/12)
                    b *= (1 + ret / 12)
            return b
        
        base = project(current_401k, monthly_savings, expected_return, inflation_rate, years)
        optimistic = project(current_401k, monthly_savings, expected_return + 0.02, inflation_rate - 0.01, years)
        pessimistic = project(current_401k, monthly_savings, expected_return - 0.02, inflation_rate + 0.01, years)
        ideal = project(current_401k, ideal_monthly_savings, expected_return, inflation_rate, years)
        
        scenarios = pd.DataFrame({
            "Scenario": ["Base", "Optimistic", "Pessimistic", "Ideal Savings"],
            "Projected Balance": [base, optimistic, pessimistic, ideal]
        })
        
        st.bar_chart(scenarios.set_index("Scenario"))
        
        # Monte Carlo
        num_sims = 1000
        sims = []
        for _ in range(num_sims):
            annual_rets = np.random.normal(expected_return, 0.05, years)
            b = current_401k
            for y in range(years):
                adj_save = monthly_savings * (1 + inflation_rate)**y
                for m in range(12):
                    b += adj_save / 12
                    b *= (1 + annual_rets[y] / 12)
            sims.append(b)
        
        sim_df = pd.DataFrame({"Projected Balance": sims})
        p10, p50, p90 = np.percentile(sims, [10, 50, 90])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("10th Percentile", f"${p10:,.0f}")
        col2.metric("Median", f"${p50:,.0f}")
        col3.metric("90th Percentile", f"${p90:,.0f}")
        
        hist = alt.Chart(sim_df).mark_bar().encode(
            alt.X("Projected Balance:Q", bin=alt.Bin(maxbins=50)),
            y="count()"
        ).properties(width=700)
        st.altair_chart(hist)
        
        sustainable = (p50 * 0.04) / 12  # 4% safe withdrawal
        st.metric("Estimated Sustainable Monthly Income (Median)", f"${sustainable:,.0f}")
        if sustainable >= desired_monthly_income:
            st.success("On track!")
        else:
            st.warning("May fall short — consider increasing savings or returns.")

