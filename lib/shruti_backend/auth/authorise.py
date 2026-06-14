from dotenv import load_dotenv
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar","https://www.googleapis.com/auth/gmail.compose"]

def authorise()->Credentials:
    _creds = None
    if os.path.exists("token.json"):
        _creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not _creds or not _creds.valid:
        if _creds and _creds.expired and _creds.refresh_token:
            _creds.refresh(Request())
        else:
            folder = Path("C:\\Users\\Rishav\\Jarvis\\lib\\auth")
            flow = InstalledAppFlow.from_client_secrets_file(
                folder/"credentials1.json", SCOPES
            )
            _creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(_creds.to_json())
    return _creds

my_credentials = authorise()
