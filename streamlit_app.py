import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError
import json

def get_gsheet_client():
    """Authenticate and return a gspread client."""
    service_account_info = json.loads(st.secrets["gcp_service_account"])
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    return gspread.authorize(creds)

def load_sheet(client):
    """Open the worksheet and return it along with its data as a DataFrame."""
    url = st.secrets["spreadsheet"]["url"]
    worksheet_name = st.secrets["spreadsheet"]["worksheet"]
    sheet = client.open_by_url(url).worksheet(worksheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return sheet, df

def test_write_permission(sheet):
    """Check if the service account can write to the sheet."""
    try:
        sheet.append_row(["__TEST_PERMISSION__", 0])
        all_rows = sheet.get_all_values()
        sheet.delete_rows(len(all_rows))
        return True
    except APIError as e:
        st.error(f"❌ Write permission test failed: {e}")
        return False

def add_row_form(df, sheet):
    """Render a dynamic form for adding a new row."""
    st.write("---")
    st.write("📝 Add a new row dynamically:")

    with st.form("add_row_form"):
        new_row = [
            st.number_input(col, value=0) if pd.api.types.is_numeric_dtype(df[col])
            else st.text_input(col, "")
            for col in df.columns
        ]
        submitted = st.form_submit_button("Add row")
        if submitted:
            try:
                sheet.append_row(new_row)
                st.success("✅ Row added successfully!")
                df_updated = pd.DataFrame(sheet.get_all_records())
                st.dataframe(df_updated)
            except Exception as e:
                st.error(f"❌ Could not add row: {e}")

def main():
    client = get_gsheet_client()

    try:
        sheet, df = load_sheet(client)
        st.write("✅ Current data in Google Sheet:")
        st.dataframe(df)

        if test_write_permission(sheet):
            st.success("✅ Service account has write permissions!")
            add_row_form(df, sheet)
        else:
            st.warning("⚠️ Cannot add new rows; check service account permissions.")

    except Exception as e:
        st.error(f"❌ Could not open sheet: {e}")

if __name__ == "__main__":
    main()
