import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
SHEET_NAME = 'Heritage Leads'
ADMIN_PASSWORD = "heritage"

# CONTACT INFO
NAME_1 = "Miza"
PHONE_1 = "701-441-1388"
NAME_2 = "Eva"
PHONE_2 = "405-268-2502"

# --- GOOGLE SHEETS CONNECTION ---
def get_google_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        return sheet
    except Exception as e:
        st.error(f"⚠️ Error connecting to Google Sheets: {e}")
        return None

def save_lead(data):
    sheet = get_google_sheet()
    if sheet:
        if not sheet.row_values(1):
            sheet.append_row(list(data.keys()))
        sheet.append_row(list(data.values()))

def calculate_score(land_status, utilities, emp_status, total_income, target_payment, savings, credit_est, repo_hist):
    score = 0
    
    # Land Score
    if "Paid Off" in land_status: score += 30
    elif "Financed" in land_status: score += 20
    elif "park" in land_status.lower(): score += 15
    
    # Utilities Score
    if "Yes" in utilities: score += 10
    
    # Employment Score
    if "W2" in emp_status: score += 15
    elif "Fixed" in emp_status: score += 10
    
    # Income Score (Affordability)
    if target_payment > 0:
        if total_income > (target_payment * 2.5): score += 20
        
    # Asset Score
    if savings > 2000: score += 10
    
    # Credit Score
    if "Excellent" in credit_est or "Good" in credit_est: score += 20
    elif "Fair" in credit_est: score += 5
    
    # Negative History
    if "Within last 2 years" in repo_hist: score -= 30
    
    return score

# --- APP SETUP ---
st.set_page_config(page_title="Heritage Housing Pre-Qualifier", page_icon="🏠", layout="centered")

st.image("https://cdn-icons-png.flaticon.com/512/25/25694.png", width=80) 
st.title("Heritage Housing: Eligibility Check")
st.markdown("**Get pre-qualified in minutes. No SSN required.**")
st.divider()

# --- INPUTS ---

st.subheader("1. Contact Info / Información")
# NEW: Language Selector
language = st.selectbox("Preferred Language / Idioma Preferido", ["English", "Español"])

c1, c2 = st.columns(2)
name = c1.text_input("Full Name")
phone = c2.text_input("Phone Number")
email = st.text_input("Email Address")

st.subheader("2. Appointment Request")
want_appt = st.checkbox("I want to schedule a visit.")
appt_text = ""
if want_appt:
    appt_text = st.text_area("Preferred Date/Time & Notes")

st.subheader("3. Property & Utilities")
land_status = st.selectbox("Property Status", [
    "I need to find land", 
    "I have land (Financed)", 
    "I have land (Paid Off)", 
    "Family Land",
    "I'm ok with a mobile home park"
])

c3, c4 = st.columns(2)
land_loc = c3.text_input("Property Location (City/County)")
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

down_payment_src = st.selectbox("Where is the down payment coming from?", ["Savings", "Tax Return", "Family Gift", "Sale of Asset", "Other"])

st.subheader("6. History")
repo_hist = st.selectbox("Any Repossessions?", ["No", "Yes (Within last 2 years)", "Yes (Over 2 years ago)"])

# --- REAL-TIME SCORE CALCULATION ---
current_score = calculate_score(land_status, utilities, emp_status, total_income, target_payment, savings, credit_est, repo_hist)

# Display Real-Time Bar
st.markdown("### 📊 Your Approval Odds")
progress_val = min(max(current_score, 0), 100) / 100.0

if current_score >= 60:
    st.success(f"Approval Odds: High ({current_score} pts)")
    st.progress(progress_val)
elif current_score >= 40:
    st.warning(f"Approval Odds: Moderate ({current_score} pts)")
    st.progress(progress_val)
else:
    st.error(f"Approval Odds: Low ({current_score} pts) - We may need a co-signer.")
    st.progress(progress_val)


# --- SUBMIT BUTTON ---
st.divider()
if st.button("Check My Eligibility", type="primary", use_container_width=True):
    
    if name and phone and total_income > 0:
        final_appt_str = "No"
        if want_appt and appt_text:
            final_appt_str = appt_text

        new_lead = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Language": language,  # Added Language here
            "Name": name, 
            "Phone": phone, 
            "Email": email,
            "Appointment": final_appt_str,
            "Land_Status": land_status, 
            "Land_Loc": land_loc, 
            "Utilities": utilities,
            "Bedrooms": bedrooms, 
            "Target_Pay": target_payment,
            "Income": total_income, 
            "Emp_Type": emp_status, 
            "Credit_Est": credit_est,
            "Down_Pay": savings, 
            "Down_Src": down_payment_src, 
            "Repo": repo_hist,
            "Internal_Score": current_score
        }
        
        save_lead(new_lead)
        
        st.balloons()
        st.success("✅ Info Received!")
        st.write(f"Thank you, {name}! We will review your info and text you at {phone}.")
        
        if want_appt:
            st.info(f"🗓️ Appointment Request: **{final_appt_str}**")

    else:
        st.error("Please fill in Name, Phone, and Income to submit.")

# --- CONTACT BANNER ---
st.info(f"""
**Questions? Call or Text us directly:**
* **{NAME_1}:** {PHONE_1}
* **{NAME_2}:** {PHONE_2}
""")

# --- OWNER LOGIN ---
with st.sidebar:
    st.markdown("---")
    st.caption("Owner Access")
    pwd = st.text_input("Password", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.success("Unlocked")
        sheet = get_google_sheet()
        if sheet:
            st.write(f"Connected to: {SHEET_NAME}")
            if st.button("Refresh Data"):
                st.rerun()

            try:
                all_data = sheet.get_all_values()
                if len(all_data) > 1:
                    df = pd.DataFrame(all_data[1:], columns=all_data[0])
                    st.dataframe(df)
                else:
                    st.info("No leads found yet.")
            except Exception as e:
                st.error(f"Could not read sheet: {e}")
