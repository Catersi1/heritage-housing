import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
FILE_PATH = 'web_leads.csv'
ADMIN_PASSWORD = "heritage"

# CONTACT INFO
NAME_1 = "Miza"
PHONE_1 = "701-441-1388"
NAME_2 = "Eva"
PHONE_2 = "405-268-2502"

def save_lead(data):
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=data.keys())
        df.to_csv(FILE_PATH, index=False)
    else:
        df = pd.read_csv(FILE_PATH)
        for col in data.keys():
            if col not in df.columns:
                df[col] = "" 
    
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)

# --- APP SETUP ---
st.set_page_config(page_title="Heritage Housing Pre-Qualifier", page_icon="🏡", layout="centered")

st.image("https://cdn-icons-png.flaticon.com/512/25/25694.png", width=80) 
st.title("Heritage Housing: Eligibility Check")

# --- CONTACT BANNER (UPDATED) ---
st.info(f"""
**Questions? Call or Text us directly:**
* **{NAME_1}:** {PHONE_1}
* **{NAME_2}:** {PHONE_2}
""")

st.markdown("**Get pre-qualified in minutes. No SSN required.**")
st.divider()

# --- THE FORM ---
with st.form("customer_form", clear_on_submit=True):
    
    st.subheader("1. Contact Info")
    c1, c2 = st.columns(2)
    name = c1.text_input("Full Name")
    phone = c2.text_input("Phone Number")
    email = st.text_input("Email Address (Optional)")
    
    st.subheader("2. Appointment Request")
    want_appt = st.checkbox("I want to schedule a visit to see homes.")
    
    # MANUAL TEXT BOX logic
    appt_text = ""
    if want_appt:
        appt_text = st.text_input("Preferred Date & Time (e.g., Next Tuesday at 2pm)")

    st.subheader("3. Property & Utilities")
    land_status = st.selectbox("Property Status", ["I need to find land", "I have land (Financed)", "I have land (Paid Off)", "Family Land"])
    
    c3, c4 = st.columns(2)
    land_loc = c3.text_input("Property Location (City/County)")
    land_size = c4.text_input("Property Size (e.g. 1 acre)")
    utilities = st.radio("Does the property have utilities?", ["Yes, all utilities", "Partial utilities", "Raw land (No utilities)", "N/A"])

    st.subheader("4. Home Preferences")
    c5, c6 = st.columns(2)
    bedrooms = c5.selectbox("Bedrooms Needed", ["1", "2", "3", "4", "5+"])
    target_payment = c6.number_input("Desired Monthly Payment ($)", step=50, value=1000)

    st.subheader("5. Income & Credit")
    c7, c8 = st.columns(2)
    emp_status = c7.selectbox("Employment Type", ["W2 (Employed)", "1099 (Self-Employed)", "Fixed Income/Retired", "Cash/Other"])
    total_income = c8.number_input("Monthly Household Income ($)", min_value=0, step=100)
    
    c9, c10 = st.columns(2)
    credit_est = c9.selectbox("Estimated Credit Score", ["Excellent (720+)", "Good (640-719)", "Fair (580-639)", "Poor (<580)", "Unknown"])
    savings = c10.number_input("Available for Down Payment ($)", step=500)

    st.subheader("6. History")
    repo_hist = st.selectbox("Any Repossessions?", ["No", "Yes (Within last 2 years)", "Yes (Over 2 years ago)"])

    spam_trap = st.text_input("Ignore this field", label_visibility="hidden")
    
    submitted = st.form_submit_button("Check My Eligibility", use_container_width=True)
    
    if submitted:
        if spam_trap != "": st.stop()
        
        if name and phone and total_income > 0:
            score = 0
            if "Paid Off" in land_status: score += 30
            elif "Financed" in land_status: score += 20
            if "Yes" in utilities: score += 10
            if "W2" in emp_status: score += 15
            elif "Fixed" in emp_status: score += 10
            if total_income > (target_payment * 2.5): score += 20
            if savings > 2000: score += 10
            if "Excellent" in credit_est or "Good" in credit_est: score += 20
            elif "Fair" in credit_est: score += 5
            if "Within last 2 years" in repo_hist: score -= 30
            
            final_appt_str = "No"
            if want_appt and appt_text:
                final_appt_str = appt_text

            new_lead = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Name": name, "Phone": phone, "Email": email,
                "Appointment": final_appt_str,
                "Land_Status": land_status, "Land_Loc": land_loc, "Utilities": utilities,
                "Bedrooms": bedrooms, "Target_Pay": target_payment,
                "Income": total_income, "Emp_Type": emp_status, "Credit_Est": credit_est,
                "Down_Pay": savings, "Repo": repo_hist,
                "Internal_Score": score
            }
            save_lead(new_lead)
            
            st.success("✅ Info Received!")
            if want_appt:
                st.info(f"🗓️ Appointment Request: **{final_appt_str}**")
            
            if score > 0:
                st.write(f"Great news, {name}! We have programs that may work for you. We will text you at {phone}.")
            else:
                st.write(f"Thank you, {name}. A specialist will review your file and contact you shortly.")
        else:
            st.error("Please fill in Name, Phone, and Income.")

with st.sidebar:
    st.markdown("---")
    st.caption("Owner Access")
    pwd = st.text_input("Password", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("Unlocked")
        if os.path.exists(FILE_PATH):
            st.write("### 📋 New Leads")
            df = pd.read_csv(FILE_PATH)
            
            cols = list(df.columns)
            if "Appointment" in cols:
                cols.insert(4, cols.pop(cols.index("Appointment")))
                df = df[cols]
                
            st.dataframe(df.iloc[::-1]) 
            st.download_button("Download CSV", df.to_csv(index=False).encode('utf-8'), 'heritage_leads.csv', 'text/csv')
        else:
            st.info("No leads yet.")
