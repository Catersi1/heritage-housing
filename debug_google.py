import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.title("🕵️ Google Connection Tester")

try:
    # 1. Try to read secrets
    st.info("Attempting to read secrets...")
    # Check if secrets exist
    if "gcp_service_account" not in st.secrets:
        st.error("❌ No secrets found! Did you add them to .streamlit/secrets.toml?")
        st.stop()
        
    creds_dict = dict(st.secrets["gcp_service_account"])
    st.success("✅ Secrets found!")
    
    # 2. Try to Authenticate
    st.info("Attempting to authenticate with Google...")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    st.success("✅ Authentication successful!")

    # 3. Try to Find the Sheet
    target_sheet = "Heritage Leads"
    st.info(f"Looking for sheet named: '{target_sheet}'...")
    sheet = client.open(target_sheet)
    st.balloons()
    st.success(f"🎉 SUCCESS! Found sheet: '{target_sheet}'")
    st.write(f"I can see it has {sheet.sheet1.row_count} rows.")

except Exception as e:
    st.error("❌ CONNECTION FAILED")
    st.warning(f"Error Details: {e}")
    
    if "SpreadsheetNotFound" in str(e):
        st.markdown("### 💡 Fix:")
        st.markdown(f"1. Go to your Google Sheet.")
        st.markdown(f"2. Rename it EXACTLY: **{target_sheet}**")
        st.markdown("3. Click **Share** (top right).")
        st.markdown(f"4. Invite this email: ")
        st.markdown("5. Set it to **Editor**.")
        
    if "InvalidParsable" in str(e):
        st.markdown("### 💡 Fix:")
        st.markdown("The 'Private Key' in your secrets is broken. It likely has missing lines or bad formatting.")

