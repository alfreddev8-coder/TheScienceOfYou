import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes required for YouTube Uploads
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]

def generate_token():
    """Performs OAuth flow to generate token.json."""
    creds = None
    token_path = "token.json"
    client_secrets = "client_secrets.json"

    if not os.path.exists(client_secrets):
        print(f"[Error] {client_secrets} not found! Please make sure it is in the project root.")
        return

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets, SCOPES)
            # Use local server to handle the redirect
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
            print(f"[Success] Token saved to {token_path}")

if __name__ == "__main__":
    generate_token()
