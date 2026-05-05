import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(
    "./backend/services/service-account.json", scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


def read_sheet(range_name):
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    return result.get("values", [])


def append_row(range_name, values):
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": [values]}
    ).execute()


def update_cell(range_name: str, value) -> None:
    """Update 1 cell cụ thể. VD: update_cell("PRODUCTS!F5", 9)"""
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="RAW",
        body={"values": [[value]]}
    ).execute()