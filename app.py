import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
FILE_PATH = 'heritage_leads.csv'
STAGES = ["Prospect", "Tentative", "Show Scheduled", "Closed-Won", "Closed-Lost"]
SOURCES = ["FB DM", "Walk-in", "Website", "Referral", "Other"]

# --- SETUP DATA ---
def load_data():
    if not os.path.exists(FILE_PATH):
        cols = [
            "Date", "Customer Name", "Source", "Status", "Home Value", 
            "Probability (%)", "Bedrooms", "Land Status", "Employment", 
            "Total Income", "Rent", "Savings", "Credit Est", "Repo History", "Notes"
        ]
        df = pd.DataFrame(columns=cols)
        df.to_csv(FILE_PATH, index=False)
        return df
    return pd.read_csv(FILE_PATH)

def save_data(df):
    df.to_csv(FILE_PATH, index=False)

# --- LEAD SCORING LOGIC ---
def calculate_score(land, employment, income, rent, savings, credit, repo):
    score = 0
    if land == "Owns Land (Paid Off)": score += 30
    elif land == "Owns Land (Financed)": score += 20
    elif land == "Looking for Land": score += 5
    
    if employment == "W2 (Employed)": score += 15
    elif employment == "1099 (Self-Employed)": score += 5 
    elif employment == "Retired/Fixed Income": score += 10
    
    monthly_income = income / 12
    if monthly_income > (rent * 3): score += 15 
    
    if savings > 5000: score += 10
    elif savings > 1000: score += 5
    
    if credit == "Excellent (720+)": score += 20
    elif credit == "Good (640-719)": score += 15
    elif credit == "Fair (580-639)": score += 5
    
    if repo == "Yes (Last 2 years)": score -= 30
    elif repo == "Yes (Older than 2 years)": score -= 10
    
    return max(0, min(100, score))

# --- APP INTERFACE ---
st.set_page_config(page_title="Heritage Housing Tracker", page_icon="🏠", layout="wide")
st.title("🏠 Heritage Housing Sales & Scoring")
tab1, tab2, tab3 = st.tabs(["➕ Qualifier & Entry", "📋 Pipeline", "📊 Dashboard"])

with tab1:
    st.header("New Lead Qualification")
    with st.form("entry_form", clear_on_submit=True):
        st.subheader("1. Basic Info")
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Customer Name")
        source = c2.selectbox("Source", SOURCES)
        beds = c3.selectbox("Bedrooms Needed", ["2", "3", "4", "5+"])
        
        st.subheader("2. Financial Profile")
        c4, c5 = st.columns(2)
        land_status = c4.selectbox("Property Status", ["No Land", "Looking for Land", "Owns Land (Financed)", "Owns Land (Paid Off)"])
        employment = c5.selectbox("Employment Type", ["W2 (Employed)", "1099 (Self-Employed)", "Retired/Fixed Income", "Unemployed"])
        
        c6, c7, c8 = st.columns(3)
        income_cust = c6.number_input("Customer Annual Income ($)", step=1000)
        income_spouse = c7.number_input("Spouse Annual Income ($)", step=1000)
        total_income = income_cust + income_spouse
        rent = c8.number_input("Current Monthly Rent ($)", step=100)
        
        c9, c10, c11 = st.columns(3)
        savings = c9.number_input("Savings Available ($)", step=500)
        credit = c10.selectbox("Est. Credit Score", ["Unknown", "Poor (<580)", "Fair (580-639)", "Good (640-719)", "Excellent (720+)"])
        repo = c11.selectbox("Repo/Foreclosure History", ["None", "Yes (Older than 2 years)", "Yes (Last 2 years)"])
        
        st.divider()
        calc_score_btn = st.form_submit_button("Calculate Score & Save Lead")
        
        if calc_score_btn and name:
            final_prob = calculate_score(land_status, employment, total_income, rent, savings, credit, repo)
            new_data = {
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Customer Name": name,
                "Source": source,
                "Status": "Prospect",
                "Home Value": 80000,
                "Probability (%)": final_prob,
                "Bedrooms": beds,
                "Land Status": land_status,
                "Employment": employment,
                "Total Income": total_income,
                "Rent": rent,
                "Savings": savings,
                "Credit Est": credit,
                "Repo History": repo,
                "Notes": f"Auto-Scored: {final_prob}%"
            }
            df = load_data()
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            save_data(df)
            if final_prob >= 70: st.success(f"✅ Lead Saved! High Probability: {final_prob}%")
            elif final_prob >= 40: st.warning(f"⚠️ Lead Saved. Medium Probability: {final_prob}%")
            else: st.error(f"🛑 Lead Saved. Low Probability: {final_prob}%")

with tab2:
    st.header("Active Leads")
    df = load_data()
    edited_df = st.data_editor(df, num_rows="dynamic")
    if not df.equals(edited_df): save_data(edited_df)

with tab3:
    st.header("Performance")
    df = load_data()
    if not df.empty:
        df['Weighted Value'] = df['Home Value'] * (df['Probability (%)'] / 100)
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Leads", len(df))
        kpi2.metric("Avg. Lead Score", f"{df['Probability (%)'].mean():.1f}%")
        kpi3.metric("Projected Revenue", f"${df['Weighted Value'].sum():,.0f}")
        st.bar_chart(df, x="Source", y="Probability (%)", color="Source")