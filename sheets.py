import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_FILE

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def get_sheet():
    creds  = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(GOOGLE_SHEET_ID).sheet1


def get_all_leads():
    sheet = get_sheet()
    return sheet.get_all_records()


def update_row(row_index, updates: dict):
    """
    Update specific columns in a row by column name.
    row_index is 1-based (row 1 = header, so leads start at row 2).
    """
    sheet   = get_sheet()
    headers = sheet.row_values(1)
    for col_name, value in updates.items():
        if col_name in headers:
            col_index = headers.index(col_name) + 1
            sheet.update_cell(row_index, col_index, str(value))