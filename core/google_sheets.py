"""
Google Sheets Integration  TheScienceOfYou
Fetches topics from a Google Sheet.
"""

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Config
# User must provide service_account.json in the project root
creds_file = "service_account.json"
SHEET_NAME = "TheScienceOfYou_Topics"

def get_topics_from_sheet():
    """Fetches topics from Google sheet."""
    if not os.path.exists(creds_file):
        # Fallback to public sheet CSV if no credentials
        print("[Sheets] service_account.json not found. Skipping Google Sheets.")
        return []
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open(SHEET_NAME).sheet1
        records = sheet.get_all_records()
        
        topics = []
        for row in records:
            if row.get("status", "").lower() != "used":
                topics.append({
                    "topic": row.get("topic"),
                    "playlist": row.get("playlist", "body_science"),
                    "row_index": records.index(row) + 2 # For marking as used later
                })
        
        print(f"[Sheets] Found {len(topics)} unused topics in Google Sheet.")
        return topics
        
    except Exception as e:
        print(f"[Sheets] Error: {e}")
        return []

def mark_sheet_topic_used(row_index):
    """Marks a topic as used in the Google Sheet."""
    if not os.path.exists(creds_file): return
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        sheet.update_cell(row_index, 3, "used") # Assuming status is column 3
        print(f"[Sheets] Marked row {row_index} as 'used'.")
    except Exception as e:
        print(f"[Sheets] Mark used error: {e}")
